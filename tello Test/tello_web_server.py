#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello ドローン Web制御サーバー
Mastra AIエージェントからHTTP APIでTelloを制御するためのサーバー

主な機能:
- HTTP API経由でのTello制御
- 非同期処理対応
- コマンド競合対策（asyncio.Lock使用）
- 自動再接続機能
- バイナリデータフィルタリング
"""

import asyncio
import json
import logging
from aiohttp import web
from typing import Dict, Any, Optional
import socket
import threading
import cv2
from datetime import datetime
import contextlib

# ログ設定 - INFOレベル以上を出力（重要な情報のみ）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# WebサーバーのHTTPアクセスログを無効化
logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

class AsyncTelloController:
    """非同期対応のDJI Telloドローン制御クラス"""
    
    def __init__(self):
        # Telloとの通信設定
        self.tello_ip = '192.168.10.1'
        self.tello_port = 8889
        self.local_ip = ''
        self.local_port = 9000
        
        # ビデオストリーム設定
        self.video_port = 11111
        
        # ソケット初期化
        self.socket = None
        self.response_queue = None  # asyncio.Queueに変更
        self.receive_thread = None
        self.running = False
        
        # コマンド実行の直列化用ロック
        self.command_lock = asyncio.Lock()
        
        # イベントループの参照を保持
        self.loop = None
        
        # ビデオキャプチャ
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 接続状態
        self.is_connected = False
        self.last_battery = 0
        self.flight_status = "landed"  # landed, flying, emergency
        
        # 操作ログ
        self.operation_log = []
    
    async def connect(self) -> Dict[str, Any]:
        """Telloに接続します"""
        try:
            logger.debug("Telloに接続中...")
            
            # 現在のイベントループを保存
            self.loop = asyncio.get_running_loop()
            
            # asyncio.Queueを初期化
            self.response_queue = asyncio.Queue()
            
            # ソケット初期化
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.local_ip, self.local_port))
            
            # 応答受信スレッド開始
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_response)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # 少し待機してスレッドが開始されるのを確認
            await asyncio.sleep(0.5)
            
            # SDKモードを有効化（複数回試行）
            for attempt in range(3):
                logger.info(f"Tello接続試行 {attempt + 1}/3")
                response = await self._send_command('command', timeout=10)
                
                if response and 'ok' in response.lower():
                    self.is_connected = True
                    logger.info("Telloに正常に接続されました")
                    
                    # バッテリー残量を確認（接続フラグ設定後に実行）
                    try:
                        battery_response = await self._send_command('battery?', timeout=5)
                        if battery_response.isdigit():
                            self.last_battery = int(battery_response)
                        else:
                            self.last_battery = 0
                            logger.warning(f"バッテリー情報の取得に失敗: {battery_response}")
                    except Exception as e:
                        logger.warning(f"バッテリー情報取得エラー: {e}")
                        self.last_battery = 0
                    
                    self._log_operation("connect", {"status": "success", "battery": self.last_battery})
                    
                    return {
                        "success": True,
                        "message": "Telloに正常に接続されました",
                        "battery": self.last_battery,
                        "timestamp": datetime.now().isoformat()
                    }
                elif response == "timeout":
                    logger.info(f"接続タイムアウト (試行 {attempt + 1})")
                    await asyncio.sleep(1)
                else:
                    # 予期しない応答は詳細をデバッグレベルで記録
                    logger.debug(f"接続試行中の応答: {response}")
                    await asyncio.sleep(1)
            
            self._log_operation("connect", {"status": "failed", "reason": "timeout"})
            return {
                "success": False,
                "message": "Tello接続に失敗しました",
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"接続エラー: {e}")
            self._log_operation("connect", {"status": "error", "error": str(e)})
            return {
                "success": False,
                "message": f"接続エラー: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _send_command(self, command: str, timeout: int = 5, retry_on_timeout: bool = True) -> str:
        """コマンドをTelloに送信し、応答を受信します（直列化対応）"""
        async with self.command_lock:  # コマンド実行を直列化
            try:
                logger.debug(f"送信: {command}")
                
                # キューをクリア
                while not self.response_queue.empty():
                    try:
                        self.response_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                
                # コマンド送信
                self.socket.sendto(command.encode('utf-8'), (self.tello_ip, self.tello_port))
                
                # 応答を待機（非同期）
                try:
                    response = await asyncio.wait_for(self.response_queue.get(), timeout=timeout)
                    logger.debug(f"応答: {response}")
                    return response
                except asyncio.TimeoutError:
                    logger.warning(f"コマンドタイムアウト: {command}")
                    
                    # タイムアウト時の自動再接続（commandコマンド以外で実行）
                    if retry_on_timeout and command != 'command':
                        logger.info("タイムアウトのため自動再接続を試行します...")
                        # 再接続は別のロック取得が必要なので、ここではretry_on_timeout=Falseで再実行
                        # 実際の再接続は呼び出し元で処理
                        return "timeout"
                    
                    return "timeout"
                
            except Exception as e:
                logger.error(f"コマンド送信エラー: {e}")
                return "error"
    
    def _receive_response(self):
        """応答を継続的に受信するスレッド"""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                response, _ = self.socket.recvfrom(1024)
                
                # バイナリデータかどうかを事前にチェック
                if self._is_binary_data(response):
                    # 状態データなどのバイナリデータは無視
                    logger.debug("バイナリ状態データを受信、無視します")
                    continue
                
                # エンコーディング処理
                response_str = None
                for encoding in ['utf-8', 'ascii', 'latin-1']:
                    try:
                        response_str = response.decode(encoding).strip()
                        # 有効なテキストレスポンスかチェック
                        if self._is_valid_tello_response(response_str):
                            break
                        else:
                            response_str = None
                    except UnicodeDecodeError:
                        continue
                
                if response_str is None:
                    # デコードできないまたは無効なデータはデバッグレベルでログ
                    logger.debug(f"無効なデータを受信、スキップします: {response[:20]}...")
                    continue
                
                logger.debug(f"受信: {response_str}")
                # asyncio.Queueにスレッドセーフに追加
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.response_queue.put(response_str), 
                        self.loop
                    )
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"受信エラー: {e}")
                break
    
    def _is_binary_data(self, data: bytes) -> bool:
        """受信データがバイナリデータかどうかを判定"""
        # 非ASCII文字が多い場合はバイナリとみなす
        try:
            data.decode('ascii')
            # ASCII文字のみで構成されていればテキスト
            return False
        except UnicodeDecodeError:
            # ASCIIでデコードできない場合は、印刷可能文字の割合をチェック
            printable_count = sum(1 for b in data if 32 <= b <= 126)
            return printable_count / len(data) < 0.7  # 70%未満が印刷可能文字ならバイナリ
    
    def _is_valid_tello_response(self, text: str) -> bool:
        """Telloの有効なレスポンスかどうかを判定"""
        if not text:
            return False
        
        # 既知のTelloレスポンス
        valid_responses = [
            'ok', 'error', 'timeout', 'out of range', 'ERROR', 'FALSE', 'TRUE'
        ]
        
        # 数値のみ（バッテリー残量など）
        if text.isdigit():
            return True
        
        # 既知のレスポンス
        for valid in valid_responses:
            if valid.lower() in text.lower():
                return True
        
        # 小数点を含む数値（温度など）
        try:
            float(text)
            return True
        except ValueError:
            pass
        
        # その他のパターン（状態文字列など）
        return len(text) <= 50  # 長すぎる文字列は状態データの可能性
    
    async def _auto_reconnect(self) -> bool:
        """自動再接続を試行します（ロック競合回避版）"""
        try:
            logger.info("自動再接続を開始します...")
            
            # 現在の接続をクリーンアップ
            self.is_connected = False
            if self.socket:
                with contextlib.suppress(Exception):
                    self.socket.close()
            
            # 少し待機
            await asyncio.sleep(1)
            
            # ソケット再初期化
            try:
                # 現在のイベントループを保存
                self.loop = asyncio.get_running_loop()
                
                # 新しいasyncio.Queueを作成
                self.response_queue = asyncio.Queue()
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind((self.local_ip, self.local_port))
                
                # 応答受信スレッドが停止していれば再開
                if not self.receive_thread or not self.receive_thread.is_alive():
                    self.running = True
                    self.receive_thread = threading.Thread(target=self._receive_response)
                    self.receive_thread.daemon = True
                    self.receive_thread.start()
                    await asyncio.sleep(0.5)
                
                # SDKモードを有効化（1回のみ試行）
                logger.info("SDK再接続を試行中...")
                response = await self._send_command('command', timeout=10, retry_on_timeout=False)
                
                if response and 'ok' in response.lower():
                    self.is_connected = True
                    logger.info("自動再接続に成功しました")
                    
                    # バッテリー残量を確認
                    try:
                        battery_response = await self._send_command('battery?', timeout=5, retry_on_timeout=False)
                        self.last_battery = int(battery_response) if battery_response.isdigit() else 0
                    except Exception:
                        self.last_battery = 0
                    
                    return True
                else:
                    logger.error(f"SDK再接続に失敗: {response}")
                    return False
                    
            except Exception as e:
                logger.error(f"ソケット再初期化エラー: {e}")
                return False
                
        except Exception as e:
            logger.error(f"自動再接続中にエラーが発生しました: {e}")
            return False
    
    async def get_battery(self) -> Dict[str, Any]:
        """バッテリー残量を取得します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        response = await self._send_command('battery?')
        try:
            battery = int(response)
            self.last_battery = battery
            return {
                "success": True,
                "battery": battery,
                "timestamp": datetime.now().isoformat()
            }
        except ValueError:
            return {
                "success": False,
                "message": "バッテリー情報の取得に失敗しました",
                "raw_response": response
            }
    
    async def takeoff(self) -> Dict[str, Any]:
        """離陸します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        if self.flight_status == "flying":
            return {"success": False, "message": "既に飛行中です"}
        
        logger.debug("離陸中...")
        response = await self._send_command('takeoff', timeout=15)
        
        if 'ok' in response.lower():
            self.flight_status = "flying"
            self._log_operation("takeoff", {"status": "success"})
            return {
                "success": True,
                "message": "離陸に成功しました",
                "flight_status": self.flight_status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            self._log_operation("takeoff", {"status": "failed", "response": response})
            return {
                "success": False,
                "message": f"離陸に失敗しました: {response}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def land(self) -> Dict[str, Any]:
        """着陸します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        if self.flight_status != "flying":
            return {"success": False, "message": "飛行中ではありません"}
        
        logger.debug("着陸中...")
        response = await self._send_command('land', timeout=15)
        
        if 'ok' in response.lower():
            self.flight_status = "landed"
            self._log_operation("land", {"status": "success"})
            return {
                "success": True,
                "message": "着陸に成功しました",
                "flight_status": self.flight_status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            self._log_operation("land", {"status": "failed", "response": response})
            return {
                "success": False,
                "message": f"着陸に失敗しました: {response}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def emergency(self) -> Dict[str, Any]:
        """緊急停止します"""
        logger.debug("緊急停止!")
        response = await self._send_command('emergency')
        
        if 'ok' in response.lower():
            self.flight_status = "emergency"
            self._log_operation("emergency", {"status": "success"})
            return {
                "success": True,
                "message": "緊急停止を実行しました",
                "flight_status": self.flight_status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            self._log_operation("emergency", {"status": "failed", "response": response})
            return {
                "success": False,
                "message": f"緊急停止に失敗しました: {response}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def move(self, direction: str, distance: int) -> Dict[str, Any]:
        """移動します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        if self.flight_status != "flying":
            return {"success": False, "message": "飛行中ではありません"}
        
        # 方向と距離の検証
        valid_directions = ['up', 'down', 'left', 'right', 'forward', 'back']
        if direction not in valid_directions:
            return {"success": False, "message": f"無効な方向です: {direction}"}
        
        if not (20 <= distance <= 500):
            return {"success": False, "message": "距離は20-500cmの範囲で指定してください"}
        
        logger.debug(f"{direction} {distance}cm移動中...")
        response = await self._send_command(f'{direction} {distance}', timeout=10)
        
        if 'ok' in response.lower():
            self._log_operation("move", {"direction": direction, "distance": distance, "status": "success"})
            return {
                "success": True,
                "message": f"{direction}に{distance}cm移動しました",
                "timestamp": datetime.now().isoformat()
            }
        elif response == "timeout":
            self._log_operation("move", {"direction": direction, "distance": distance, "status": "timeout"})
            
            # 自動再接続を試行
            logger.info("移動コマンドタイムアウト、自動再接続を試行します...")
            reconnect_success = await self._auto_reconnect()
            
            if reconnect_success:
                logger.info("再接続成功、移動コマンドを再実行します")
                # 再接続後にコマンドを再実行
                retry_response = await self._send_command(f'{direction} {distance}', timeout=10, retry_on_timeout=False)
                
                if 'ok' in retry_response.lower():
                    self._log_operation("move", {"direction": direction, "distance": distance, "status": "success_after_reconnect"})
                    return {
                        "success": True,
                        "message": f"再接続後に{direction}に{distance}cm移動しました",
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "message": f"再接続後も移動に失敗しました: {retry_response}",
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "success": False,
                    "message": "移動コマンドがタイムアウトし、自動再接続にも失敗しました。ドローンの状態を確認してください。",
                    "reconnected": False,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            self._log_operation("move", {"direction": direction, "distance": distance, "status": "failed", "response": response})
            
            # Auto landエラーの場合は特別な処理
            if "auto land" in response.lower():
                # 飛行状態を着陸に更新
                self.flight_status = "landed"
                
                # バッテリー残量を確認
                battery_info = await self.get_battery()
                current_battery = battery_info.get('battery', 0)
                
                return {
                    "success": False,
                    "message": f"ドローンが自動着陸しました。原因: {response}",
                    "details": {
                        "reason": "auto_land",
                        "battery": current_battery,
                        "flight_status": self.flight_status,
                        "recommendations": [
                            "バッテリー残量を確認してください（推奨: 30%以上）",
                            "ドローンとの距離が遠すぎないか確認してください",
                            "周囲に障害物がないか確認してください",
                            "再度離陸する前に少し待機してください"
                        ]
                    },
                    "raw_response": response,
                    "timestamp": datetime.now().isoformat()
                }
            # Motor stopエラーの場合は特別なメッセージ
            elif "motor stop" in response.lower():
                return {
                    "success": False,
                    "message": "移動に失敗しました: モーターが停止しています。ドローンが着陸しているか、障害物を検知した可能性があります。",
                    "raw_response": response,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"移動に失敗しました: {response}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def rotate(self, direction: str, degrees: int) -> Dict[str, Any]:
        """回転します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        if self.flight_status != "flying":
            return {"success": False, "message": "飛行中ではありません"}
        
        # 回転方向と角度の検証
        if direction not in ['cw', 'ccw']:
            return {"success": False, "message": f"無効な回転方向です: {direction}"}
        
        if not (1 <= degrees <= 360):
            return {"success": False, "message": "角度は1-360度の範囲で指定してください"}
        
        logger.debug(f"{direction} {degrees}度回転中...")
        response = await self._send_command(f'{direction} {degrees}', timeout=10)
        
        if 'ok' in response.lower():
            self._log_operation("rotate", {"direction": direction, "degrees": degrees, "status": "success"})
            return {
                "success": True,
                "message": f"{direction}方向に{degrees}度回転しました",
                "timestamp": datetime.now().isoformat()
            }
        elif response == "timeout":
            self._log_operation("rotate", {"direction": direction, "degrees": degrees, "status": "timeout"})
            
            # 自動再接続を試行
            logger.info("回転コマンドタイムアウト、自動再接続を試行します...")
            reconnect_success = await self._auto_reconnect()
            
            if reconnect_success:
                logger.info("再接続成功、回転コマンドを再実行します")
                # 再接続後にコマンドを再実行
                retry_response = await self._send_command(f'{direction} {degrees}', timeout=10, retry_on_timeout=False)
                
                if 'ok' in retry_response.lower():
                    self._log_operation("rotate", {"direction": direction, "degrees": degrees, "status": "success_after_reconnect"})
                    return {
                        "success": True,
                        "message": f"再接続後に{direction}方向に{degrees}度回転しました",
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "message": f"再接続後も回転に失敗しました: {retry_response}",
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "success": False,
                    "message": "回転コマンドがタイムアウトし、自動再接続にも失敗しました。ドローンの状態を確認してください。",
                    "reconnected": False,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            self._log_operation("rotate", {"direction": direction, "degrees": degrees, "status": "failed", "response": response})
            
            # Auto landエラーの場合は特別な処理
            if "auto land" in response.lower():
                # 飛行状態を着陸に更新
                self.flight_status = "landed"
                
                # バッテリー残量を確認
                battery_info = await self.get_battery()
                current_battery = battery_info.get('battery', 0)
                
                return {
                    "success": False,
                    "message": f"ドローンが自動着陸しました。原因: {response}",
                    "details": {
                        "reason": "auto_land",
                        "battery": current_battery,
                        "flight_status": self.flight_status,
                        "recommendations": [
                            "バッテリー残量を確認してください（推奨: 30%以上）",
                            "ドローンとの距離が遠すぎないか確認してください",
                            "周囲に障害物がないか確認してください",
                            "再度離陸する前に少し待機してください"
                        ]
                    },
                    "raw_response": response,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"回転に失敗しました: {response}",
                    "timestamp": datetime.now().isoformat()
                }
    
    async def get_status(self) -> Dict[str, Any]:
        """ドローンの状態を取得します"""
        return {
            "success": True,
            "connected": self.is_connected,
            "flight_status": self.flight_status,
            "battery": self.last_battery,
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_operation(self, operation: str, details: Dict[str, Any]):
        """操作ログを記録します"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }
        self.operation_log.append(log_entry)
        
        # ログを最新100件に制限
        if len(self.operation_log) > 100:
            self.operation_log = self.operation_log[-100:]
    
    async def disconnect(self):
        """Telloから切断します"""
        try:
            self.running = False
            
            if self.cap:
                self.cap.release()
                self.cap = None
            
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2)
            
            if self.socket:
                self.socket.close()
                
            self.is_connected = False
            self.flight_status = "landed"
            
            logger.debug("Telloから切断されました")
            self._log_operation("disconnect", {"status": "success"})
            
        except Exception as e:
            logger.error(f"切断エラー: {e}")


# グローバルTelloコントローラーインスタンス
tello_controller = AsyncTelloController()

# HTTP APIハンドラー
async def _parse_request_params(request: web.Request, param_names: list) -> dict:
    """Parse parameters from JSON body or query string"""
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    body_text = await request.text()
    logger.info(f"Request body: '{body_text}'")
    
    if body_text.strip() and (request.content_type == 'application/json' or body_text.strip().startswith('{')):
        try:
            data = json.loads(body_text)
            params = {name: data.get(name) for name in param_names}
            logger.info(f"JSON解析成功: {params}")
            return params
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {e}")
            raise web.HTTPBadRequest(
                text=json.dumps({"success": False, "message": f"無効なJSON形式です: {str(e)}"}),
                content_type='application/json'
            )
    else:
        params = {name: request.query.get(name) for name in param_names}
        logger.info(f"クエリパラメータ使用: {params}")
        
        if any(params[name] is None for name in param_names):
            missing = [name for name in param_names if params[name] is None]
            raise web.HTTPBadRequest(
                text=json.dumps({
                    "success": False, 
                    "message": f"必要なパラメータ（{', '.join(missing)}）が不足しています。"
                }),
                content_type='application/json'
            )
        
        return params

async def connect_handler(request: web.Request) -> web.Response:
    """接続エンドポイント"""
    result = await tello_controller.connect()
    return web.json_response(result)

async def disconnect_handler(request: web.Request) -> web.Response:
    """切断エンドポイント"""
    await tello_controller.disconnect()
    return web.json_response({"success": True, "message": "切断しました"})

async def status_handler(request: web.Request) -> web.Response:
    """状態取得エンドポイント"""
    result = await tello_controller.get_status()
    return web.json_response(result)

async def battery_handler(request: web.Request) -> web.Response:
    """バッテリー残量取得エンドポイント"""
    result = await tello_controller.get_battery()
    return web.json_response(result)

async def takeoff_handler(request: web.Request) -> web.Response:
    """離陸エンドポイント"""
    result = await tello_controller.takeoff()
    return web.json_response(result)

async def land_handler(request: web.Request) -> web.Response:
    """着陸エンドポイント"""
    result = await tello_controller.land()
    return web.json_response(result)

async def emergency_handler(request: web.Request) -> web.Response:
    """緊急停止エンドポイント"""
    result = await tello_controller.emergency()
    return web.json_response(result)

async def move_handler(request: web.Request) -> web.Response:
    """移動エンドポイント"""
    try:
        params = await _parse_request_params(request, ['direction', 'distance'])
        
        # Convert distance to int
        distance = int(params['distance'])
        
        result = await tello_controller.move(params['direction'], distance)
        return web.json_response(result)
        
    except web.HTTPBadRequest:
        raise
    except ValueError as e:
        return web.json_response(
            {"success": False, "message": f"distanceは数値で指定してください: {str(e)}"}, 
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"success": False, "message": f"エラー: {e}"}, 
            status=500
        )

async def rotate_handler(request: web.Request) -> web.Response:
    """回転エンドポイント"""
    try:
        params = await _parse_request_params(request, ['direction', 'degrees'])
        
        # Convert degrees to int
        degrees = int(params['degrees'])
        
        result = await tello_controller.rotate(params['direction'], degrees)
        return web.json_response(result)
        
    except web.HTTPBadRequest:
        raise
    except ValueError as e:
        return web.json_response(
            {"success": False, "message": f"degreesは数値で指定してください: {str(e)}"}, 
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"success": False, "message": f"エラー: {e}"}, 
            status=500
        )

async def health_handler(request: web.Request) -> web.Response:
    """ヘルスチェックエンドポイント"""
    return web.json_response({
        "status": "healthy",
        "service": "Tello Web Controller",
        "timestamp": datetime.now().isoformat()
    })

# CORS対応
async def cors_handler(request: web.Request) -> web.Response:
    """CORS preflight対応"""
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',  # 本番環境では特定のドメインに制限することを推奨
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )

def setup_cors(app):
    """CORS設定"""
    @web.middleware
    async def cors_middleware(request, handler):
        # OPTIONSリクエストの場合は直接レスポンスを返す
        if request.method == 'OPTIONS':
            return web.Response(
                headers={
                    'Access-Control-Allow-Origin': '*',  # 本番環境では特定のドメインに制限することを推奨
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                }
            )
        
        try:
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'  # 本番環境では特定のドメインに制限することを推奨
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        except Exception as e:
            logger.error(f"CORS middleware error: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    app.middlewares.append(cors_middleware)

def create_app() -> web.Application:
    """Webアプリケーションを作成します"""
    app = web.Application()
    
    # ルート設定
    app.router.add_get('/health', health_handler)
    app.router.add_post('/connect', connect_handler)
    app.router.add_post('/disconnect', disconnect_handler)
    app.router.add_get('/status', status_handler)
    app.router.add_get('/battery', battery_handler)
    app.router.add_post('/takeoff', takeoff_handler)
    app.router.add_post('/land', land_handler)
    app.router.add_post('/emergency', emergency_handler)
    app.router.add_post('/move', move_handler)
    app.router.add_post('/rotate', rotate_handler)
    
    # OPTIONS用のルート設定
    app.router.add_options('/{path:.*}', cors_handler)
    
    return app

async def main():
    """メイン関数"""
    app = create_app()
    setup_cors(app)  # CORS設定を追加
    
    # サーバー設定
    host = '0.0.0.0'
    port = 8080
    
    logger.info(f"Tello Web Controller started on http://{host}:{port}")
    logger.info("Ready to control Tello drone via HTTP API")
    logger.info("バイナリデータフィルタリング機能が有効です")
    
    # サーバー起動
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    try:
        # サーバーを無限に実行
        await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        logger.info("サーバーを停止中...")
    finally:
        await tello_controller.disconnect()
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main()) 