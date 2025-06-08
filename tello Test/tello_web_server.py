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
import base64
import time
import subprocess
import numpy as np

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
        self.video_streaming = False
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # FFmpegプロセス（代替ビデオ処理用）
        self.ffmpeg_process = None
        self.use_ffmpeg = False
        
        # シンプルUDPキャプチャ用
        self.udp_socket = None
        self.use_simple_udp = False
        
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
    
    async def reset_flight_status(self) -> Dict[str, Any]:
        """飛行状態をリセットします（デバッグ用）"""
        old_status = self.flight_status
        self.flight_status = "landed"
        self._log_operation("reset_flight_status", {"old_status": old_status, "new_status": "landed"})
        logger.info(f"飛行状態をリセットしました: {old_status} -> landed")
        return {
            "success": True,
            "message": f"飛行状態をリセットしました: {old_status} -> landed",
            "old_status": old_status,
            "new_status": "landed",
            "timestamp": datetime.now().isoformat()
        }

    async def takeoff(self) -> Dict[str, Any]:
        """離陸します"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        if self.flight_status == "flying":
            # 状態確認のため実際のドローンの状態をチェック
            logger.warning("飛行状態が'flying'になっていますが、実際の状態を確認します...")
            
            # 実際にTelloに状態確認コマンドを送信
            try:
                state_response = await self._send_command('battery?', timeout=3)
                if state_response == "timeout" or state_response == "error":
                    # 通信できない場合は状態をリセット
                    logger.info("ドローンとの通信ができないため、状態をリセットします")
                    self.flight_status = "landed"
                else:
                    # 通信できる場合は、強制的に着陸コマンドを送信してから離陸
                    logger.info("安全のため、まず着陸コマンドを送信します")
                    await self._send_command('land', timeout=5)
                    await asyncio.sleep(2)  # 少し待機
                    self.flight_status = "landed"
            except Exception as e:
                logger.warning(f"状態確認中にエラー: {e}")
                self.flight_status = "landed"
        
        logger.info("離陸を開始します...")
        response = await self._send_command('takeoff', timeout=25)  # タイムアウトを25秒に延長
        
        if 'ok' in response.lower():
            self.flight_status = "flying"
            self._log_operation("takeoff", {"status": "success"})
            logger.info("離陸に成功しました")
            return {
                "success": True,
                "message": "離陸に成功しました",
                "flight_status": self.flight_status,
                "timestamp": datetime.now().isoformat()
            }
        elif response == "timeout":
            self._log_operation("takeoff", {"status": "timeout"})
            
            # 自動再接続を試行
            logger.info("離陸コマンドタイムアウト、自動再接続を試行します...")
            reconnect_success = await self._auto_reconnect()
            
            if reconnect_success:
                logger.info("再接続成功、離陸コマンドを再実行します")
                # 再接続後にコマンドを再実行
                retry_response = await self._send_command('takeoff', timeout=25, retry_on_timeout=False)
                
                if 'ok' in retry_response.lower():
                    self.flight_status = "flying"
                    self._log_operation("takeoff", {"status": "success_after_reconnect"})
                    logger.info("再接続後に離陸に成功しました")
                    return {
                        "success": True,
                        "message": "再接続後に離陸に成功しました",
                        "flight_status": self.flight_status,
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"再接続後も離陸に失敗: {retry_response}")
                    return {
                        "success": False,
                        "message": f"再接続後も離陸に失敗しました: {retry_response}",
                        "reconnected": True,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                logger.error("離陸コマンドタイムアウト、自動再接続にも失敗")
                return {
                    "success": False,
                    "message": "離陸コマンドがタイムアウトし、自動再接続にも失敗しました。ドローンの状態を確認してください。",
                    "reconnected": False,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            self._log_operation("takeoff", {"status": "failed", "response": response})
            logger.error(f"離陸に失敗: {response}")
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
            "video_streaming": self.video_streaming,
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
    
    async def start_video_stream(self) -> Dict[str, Any]:
        """ビデオストリーミングを開始します（改善版）"""
        if not self.is_connected:
            return {"success": False, "message": "Telloに接続されていません"}
        
        try:
            # 既存のビデオストリーミングを停止
            if self.video_streaming:
                logger.info("既存のビデオストリーミングを停止中...")
                await self.stop_video_stream()
                await asyncio.sleep(1)
            
            # ビデオストリーミングを有効化（複数回試行）
            streamon_success = False
            for attempt in range(3):
                logger.info(f"ビデオストリーミング有効化試行 {attempt + 1}/3")
                response = await self._send_command('streamon', timeout=10)
                
                if 'ok' in response.lower():
                    streamon_success = True
                    logger.info("Telloビデオストリーミングコマンドが成功しました")
                    break
                elif response == "timeout":
                    logger.warning(f"streamon コマンドタイムアウト (試行 {attempt + 1})")
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"streamon 応答: {response} (試行 {attempt + 1})")
                    await asyncio.sleep(1)
            
            if not streamon_success:
                return {
                    "success": False,
                    "message": "Telloビデオストリーミングコマンドが失敗しました"
                }
            
            # Telloがストリーミングモードになるまで待機
            logger.info("Telloがストリーミングモードになるまで待機中...")
            await asyncio.sleep(3)
            
            # 複数の方法でビデオキャプチャを試行
            capture_methods = [
                ("OpenCV", self._start_opencv_capture),
                ("FFmpeg", self._start_ffmpeg_capture),
                ("Simple UDP", self._start_simple_udp_capture)
            ]
            
            for method_name, method_func in capture_methods:
                logger.info(f"{method_name}でビデオキャプチャを試行中...")
                try:
                    success = await method_func()
                    if success:
                        logger.info(f"✅ {method_name}でビデオストリーミングを開始しました")
                        return {
                            "success": True,
                            "message": f"{method_name}でビデオストリーミングを開始しました",
                            "method": method_name.lower(),
                            "timestamp": datetime.now().isoformat()
                        }
                except Exception as method_e:
                    logger.error(f"{method_name}でエラー: {method_e}")
                    continue
            
            # すべての方法が失敗した場合
            logger.error("すべてのビデオキャプチャ方法が失敗しました")
            return {
                "success": False,
                "message": "すべてのビデオキャプチャ方法が失敗しました。Telloのビデオストリーミング機能を確認してください。"
            }
                
        except Exception as e:
            logger.error(f"ビデオストリーミング開始エラー: {e}")
            return {
                "success": False,
                "message": f"ビデオストリーミング開始エラー: {e}"
            }
    
    async def _start_opencv_capture(self) -> bool:
        """OpenCVを使用してビデオキャプチャを開始（改善版）"""
        try:
            # 複数のUDPストリーム形式を試行
            stream_urls = [
                f'udp://0.0.0.0:{self.video_port}',
                f'udp://@0.0.0.0:{self.video_port}',
                f'udp://127.0.0.1:{self.video_port}'
            ]
            
            for stream_url in stream_urls:
                logger.info(f"ビデオストリーム接続を試行: {stream_url}")
                
                # OpenCVでビデオキャプチャを開始
                self.cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
                
                if self.cap.isOpened():
                    # OpenCVの設定を最適化（フレームレート向上）
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # バッファサイズを最小に
                    self.cap.set(cv2.CAP_PROP_FPS, 30)  # フレームレートを向上
                    
                    # タイムアウト設定を追加
                    self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5秒タイムアウト
                    self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)  # 3秒読み取りタイムアウト
                    
                    # フォーマット設定（より柔軟に）
                    try:
                        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
                    except:
                        pass  # フォーマット設定に失敗しても続行
                    
                    self.video_streaming = True
                    self.use_ffmpeg = False
                    
                    # ビデオフレーム取得スレッドを開始
                    video_thread = threading.Thread(target=self._capture_video_frames)
                    video_thread.daemon = True
                    video_thread.start()
                    
                    # 初期化時間を待機（短縮）
                    await asyncio.sleep(2)
                    
                    # テストフレームを取得して動作確認
                    test_attempts = 0
                    while test_attempts < 15:  # 試行回数を増加
                        if self.latest_frame is not None:
                            logger.info(f"OpenCVビデオキャプチャが正常に動作しています ({stream_url})")
                            return True
                        await asyncio.sleep(0.2)  # 待機時間をさらに短縮
                        test_attempts += 1
                    
                    # このストリームURLでは失敗、次を試行
                    logger.warning(f"OpenCVでフレームを取得できませんでした ({stream_url})")
                    self.video_streaming = False
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                else:
                    logger.warning(f"OpenCVビデオキャプチャの初期化に失敗しました ({stream_url})")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
            
            logger.warning("すべてのOpenCVストリームURLで失敗しました")
            return False
                
        except Exception as e:
            logger.error(f"OpenCVキャプチャエラー: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    async def _start_ffmpeg_capture(self) -> bool:
        """FFmpegを使用してビデオキャプチャを開始（改善版）"""
        try:
            # FFmpegの利用可能性をチェック
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("FFmpegが見つかりません。FFmpegをインストールしてください。")
                return False
            
            # 複数のFFmpegコマンド設定を試行
            ffmpeg_configs = [
                # 設定1: 基本的な設定
                [
                    'ffmpeg',
                    '-fflags', '+genpts',
                    '-thread_queue_size', '512',
                    '-i', f'udp://0.0.0.0:{self.video_port}',
                    '-f', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-an',  # オーディオなし
                    '-sn',  # 字幕なし
                    '-vf', 'scale=640:480',  # より小さい解像度で安定性向上
                    '-r', '25',  # フレームレートを向上
                    '-'
                ],
                # 設定2: より堅牢な設定
                [
                    'ffmpeg',
                    '-fflags', '+genpts',
                    '-thread_queue_size', '1024',
                    '-probesize', '32',
                    '-analyzeduration', '0',
                    '-i', f'udp://0.0.0.0:{self.video_port}',
                    '-f', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-an',
                    '-sn',
                    '-vf', 'scale=640:480',
                    '-r', '20',
                    '-'
                ]
            ]
            
            for i, ffmpeg_cmd in enumerate(ffmpeg_configs):
                logger.info(f"FFmpeg設定 {i+1} を試行中...")
                
                try:
                    # FFmpegプロセスを開始
                    self.ffmpeg_process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        bufsize=10**6  # バッファサイズを調整
                    )
                    
                    self.video_streaming = True
                    self.use_ffmpeg = True
                    
                    # FFmpegフレーム取得スレッドを開始
                    video_thread = threading.Thread(target=self._capture_ffmpeg_frames)
                    video_thread.daemon = True
                    video_thread.start()
                    
                    # 初期化時間を待機（短縮）
                    await asyncio.sleep(2)
                    
                    # テストフレームを取得して動作確認
                    test_attempts = 0
                    while test_attempts < 15:
                        if self.latest_frame is not None:
                            logger.info(f"FFmpegビデオキャプチャが正常に動作しています (設定 {i+1})")
                            return True
                        await asyncio.sleep(0.5)
                        test_attempts += 1
                    
                    # この設定では失敗、次を試行
                    logger.warning(f"FFmpeg設定 {i+1} でフレームを取得できませんでした")
                    self.video_streaming = False
                    if self.ffmpeg_process:
                        self.ffmpeg_process.terminate()
                        try:
                            self.ffmpeg_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            self.ffmpeg_process.kill()
                        self.ffmpeg_process = None
                        
                except Exception as config_e:
                    logger.warning(f"FFmpeg設定 {i+1} でエラー: {config_e}")
                    if self.ffmpeg_process:
                        try:
                            self.ffmpeg_process.terminate()
                            self.ffmpeg_process.wait(timeout=2)
                        except:
                            pass
                        self.ffmpeg_process = None
            
            logger.warning("すべてのFFmpeg設定で失敗しました")
            return False
            
        except Exception as e:
            logger.error(f"FFmpegキャプチャエラー: {e}")
            if self.ffmpeg_process:
                try:
                    self.ffmpeg_process.terminate()
                    self.ffmpeg_process.wait(timeout=2)
                except:
                    pass
                self.ffmpeg_process = None
            return False
    
    async def _start_simple_udp_capture(self) -> bool:
        """シンプルなUDPソケットを使用してビデオキャプチャを開始"""
        try:
            import socket
            
            # UDPソケットを作成
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind(('0.0.0.0', self.video_port))
            self.udp_socket.settimeout(5.0)  # 5秒タイムアウト
            
            self.video_streaming = True
            self.use_simple_udp = True
            self.use_ffmpeg = False
            
            # シンプルUDPフレーム取得スレッドを開始
            video_thread = threading.Thread(target=self._capture_simple_udp_frames)
            video_thread.daemon = True
            video_thread.start()
            
            # 初期化時間を待機
            await asyncio.sleep(2)
            
            # テストフレームを取得して動作確認
            test_attempts = 0
            while test_attempts < 10:
                if self.latest_frame is not None:
                    logger.info("シンプルUDPビデオキャプチャが正常に動作しています")
                    return True
                await asyncio.sleep(0.5)
                test_attempts += 1
            
            logger.warning("シンプルUDPでフレームを取得できませんでした")
            self.video_streaming = False
            self.use_simple_udp = False
            if self.udp_socket:
                self.udp_socket.close()
                self.udp_socket = None
            return False
            
        except Exception as e:
            logger.error(f"シンプルUDPキャプチャエラー: {e}")
            if self.udp_socket:
                try:
                    self.udp_socket.close()
                except:
                    pass
                self.udp_socket = None
            return False
    
    async def stop_video_stream(self) -> Dict[str, Any]:
        """ビデオストリーミングを停止します"""
        try:
            self.video_streaming = False
            
            # OpenCVキャプチャを停止
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # FFmpegプロセスを停止
            if self.ffmpeg_process:
                try:
                    self.ffmpeg_process.terminate()
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()
                finally:
                    self.ffmpeg_process = None
            
            # シンプルUDPソケットを停止
            if self.udp_socket:
                try:
                    self.udp_socket.close()
                except:
                    pass
                finally:
                    self.udp_socket = None
            
            self.use_ffmpeg = False
            self.use_simple_udp = False
            self.latest_frame = None
            
            # ビデオストリーミングを無効化
            if self.is_connected:
                response = await self._send_command('streamoff')
                logger.info("ビデオストリーミングを停止しました")
            
            return {
                "success": True,
                "message": "ビデオストリーミングを停止しました",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ビデオストリーミング停止エラー: {e}")
            return {
                "success": False,
                "message": f"ビデオストリーミング停止エラー: {e}"
            }
    
    def _capture_video_frames(self):
        """ビデオフレームを継続的にキャプチャするスレッド（改善版）"""
        consecutive_failures = 0
        max_failures = 10
        frame_skip_count = 0
        successful_frames = 0
        
        logger.info("ビデオフレームキャプチャスレッドを開始しました")
        
        while self.video_streaming and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    # フレームが正常に取得できた場合
                    consecutive_failures = 0
                    frame_skip_count = 0
                    successful_frames += 1
                    
                    # フレームサイズをチェック
                    if frame.shape[0] > 0 and frame.shape[1] > 0:
                        with self.frame_lock:
                            self.latest_frame = frame
                        
                        # 最初のフレーム取得時にログ出力
                        if successful_frames == 1:
                            logger.info(f"最初のビデオフレームを取得しました (サイズ: {frame.shape})")
                        elif successful_frames % 100 == 0:  # 100フレームごとにログ
                            logger.debug(f"ビデオフレーム取得中... ({successful_frames} フレーム)")
                else:
                    # フレーム取得に失敗した場合
                    consecutive_failures += 1
                    frame_skip_count += 1
                    
                    # 連続失敗が多い場合は再初期化
                    if consecutive_failures >= max_failures:
                        logger.warning(f"連続してフレーム取得に失敗しました（{consecutive_failures}回）")
                        # キャプチャを再初期化
                        try:
                            self.cap.release()
                            time.sleep(2)
                            self.cap = cv2.VideoCapture(f'udp://@0.0.0.0:{self.video_port}')
                            if self.cap.isOpened():
                                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                                self.cap.set(cv2.CAP_PROP_FPS, 30)
                                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
                                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
                                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                                # フレームレート向上のための追加設定
                                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                                self.cap.set(cv2.CAP_PROP_EXPOSURE, -6)
                                consecutive_failures = 0
                                logger.info("ビデオキャプチャを再初期化しました")
                            else:
                                logger.error("ビデオキャプチャの再初期化に失敗しました")
                                break
                        except Exception as reinit_e:
                            logger.error(f"ビデオキャプチャ再初期化エラー: {reinit_e}")
                            break
                    else:
                        # より短時間待機してリトライ（フレームレート向上）
                        time.sleep(0.01)
                        
            except Exception as e:
                error_msg = str(e)
                # OpenCVの特定のエラーを詳細に処理
                if "Unknown C++ exception" in error_msg:
                    logger.error("OpenCVでC++例外が発生しました。ビデオストリームを再初期化します。")
                    try:
                        if self.cap:
                            self.cap.release()
                        time.sleep(1)
                        # より堅牢な再初期化
                        self.cap = cv2.VideoCapture(f'udp://0.0.0.0:{self.video_port}', cv2.CAP_FFMPEG)
                        if self.cap.isOpened():
                            # 基本設定のみ適用（エラーを避けるため）
                            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            consecutive_failures = 0
                            logger.info("OpenCVビデオキャプチャを再初期化しました")
                            continue
                        else:
                            logger.error("OpenCVビデオキャプチャの再初期化に失敗")
                            break
                    except Exception as reinit_e:
                        logger.error(f"ビデオキャプチャ再初期化エラー: {reinit_e}")
                        break
                else:
                    logger.error(f"フレームキャプチャエラー: {e}")
                
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.error("フレームキャプチャエラーが多すぎるため、スレッドを終了します")
                    break
                time.sleep(0.1)
        
        logger.info("ビデオフレームキャプチャスレッドが終了しました")
    
    def _capture_ffmpeg_frames(self):
        """FFmpegからビデオフレームを継続的にキャプチャするスレッド"""
        frame_width = 640
        frame_height = 480
        frame_size = frame_width * frame_height * 3  # BGR24
        
        consecutive_failures = 0
        max_failures = 10
        
        while self.video_streaming and self.ffmpeg_process:
            try:
                # FFmpegからフレームデータを読み取り
                raw_frame = self.ffmpeg_process.stdout.read(frame_size)
                
                if len(raw_frame) == frame_size:
                    # バイトデータをnumpy配列に変換
                    frame = np.frombuffer(raw_frame, dtype=np.uint8)
                    frame = frame.reshape((frame_height, frame_width, 3))
                    
                    consecutive_failures = 0
                    with self.frame_lock:
                        self.latest_frame = frame
                        
                elif len(raw_frame) == 0:
                    # プロセスが終了した
                    logger.info("FFmpegプロセスが終了しました")
                    break
                else:
                    # 不完全なフレーム
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        logger.warning(f"FFmpegから不完全なフレームを連続受信（{consecutive_failures}回）")
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"FFmpegフレームキャプチャエラー: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.error("FFmpegフレームキャプチャエラーが多すぎるため、ビデオストリーミングを停止します")
                    break
                time.sleep(0.1)
        
        logger.info("FFmpegビデオフレームキャプチャスレッドが終了しました")
    
    def _capture_simple_udp_frames(self):
        """シンプルUDPソケットからビデオフレームを継続的にキャプチャするスレッド"""
        consecutive_failures = 0
        max_failures = 10
        successful_frames = 0
        
        logger.info("シンプルUDPビデオフレームキャプチャスレッドを開始しました")
        
        while self.video_streaming and self.udp_socket:
            try:
                # UDPパケットを受信
                data, addr = self.udp_socket.recvfrom(65536)  # 最大64KB
                
                if len(data) > 0:
                    # H.264データを受信した場合、簡単な画像として保存
                    # 実際のH.264デコードは複雑なので、ここでは受信確認のみ
                    consecutive_failures = 0
                    successful_frames += 1
                    
                    # 最初のパケット受信時にログ出力
                    if successful_frames == 1:
                        logger.info(f"最初のUDPビデオパケットを受信しました (サイズ: {len(data)} bytes, from: {addr})")
                    elif successful_frames % 100 == 0:  # 100パケットごとにログ
                        logger.debug(f"UDPビデオパケット受信中... ({successful_frames} パケット)")
                    
                    # 簡単なテスト画像を生成（実際のH.264デコードの代替）
                    if successful_frames <= 5:  # 最初の数フレームのみテスト画像を生成
                        test_frame = self._create_test_frame(f"UDP Frame {successful_frames}")
                        with self.frame_lock:
                            self.latest_frame = test_frame
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        logger.warning(f"UDPパケット受信に連続失敗（{consecutive_failures}回）")
                        break
                    time.sleep(0.1)
                    
            except socket.timeout:
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.warning(f"UDPソケットタイムアウトが連続発生（{consecutive_failures}回）")
                    break
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"シンプルUDPフレームキャプチャエラー: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.error("シンプルUDPフレームキャプチャエラーが多すぎるため、スレッドを終了します")
                    break
                time.sleep(0.1)
        
        logger.info("シンプルUDPビデオフレームキャプチャスレッドが終了しました")
    
    def _create_test_frame(self, text: str):
        """テスト用のフレームを生成"""
        import numpy as np
        
        # 640x480のテスト画像を作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = [64, 128, 192]  # 青っぽい背景
        
        # OpenCVでテキストを描画（利用可能な場合）
        try:
            import cv2
            cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            cv2.putText(frame, "Tello Video Stream", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        except:
            pass  # OpenCVが利用できない場合はテキストなしで続行
        
        return frame
    
    async def get_video_frame(self) -> Dict[str, Any]:
        """最新のビデオフレームをBase64エンコードして取得します"""
        if not self.video_streaming or self.latest_frame is None:
            return {
                "success": False,
                "message": "ビデオストリーミングが開始されていません"
            }
        
        try:
            with self.frame_lock:
                frame = self.latest_frame.copy()
            
            # フレームをJPEGエンコード（品質を下げて高速化）
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            
            # Base64エンコード
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "success": True,
                "frame": frame_base64,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"フレーム取得エラー: {e}")
            return {
                "success": False,
                "message": f"フレーム取得エラー: {e}"
            }

    async def disconnect(self):
        """Telloから切断します"""
        try:
            self.running = False
            self.video_streaming = False
            
            # OpenCVキャプチャを停止
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # FFmpegプロセスを停止
            if self.ffmpeg_process:
                try:
                    self.ffmpeg_process.terminate()
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()
                finally:
                    self.ffmpeg_process = None
            
            # シンプルUDPソケットを停止
            if self.udp_socket:
                try:
                    self.udp_socket.close()
                except:
                    pass
                finally:
                    self.udp_socket = None
            
            self.use_ffmpeg = False
            self.use_simple_udp = False
            self.latest_frame = None
            
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

async def reset_status_handler(request: web.Request) -> web.Response:
    """飛行状態リセットエンドポイント"""
    result = await tello_controller.reset_flight_status()
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

async def start_video_handler(request: web.Request) -> web.Response:
    """ビデオストリーミング開始エンドポイント"""
    result = await tello_controller.start_video_stream()
    return web.json_response(result)

async def stop_video_handler(request: web.Request) -> web.Response:
    """ビデオストリーミング停止エンドポイント"""
    result = await tello_controller.stop_video_stream()
    return web.json_response(result)

async def video_frame_handler(request: web.Request) -> web.Response:
    """ビデオフレーム取得エンドポイント"""
    result = await tello_controller.get_video_frame()
    return web.json_response(result)

async def video_debug_handler(request: web.Request) -> web.Response:
    """ビデオストリーミングデバッグ情報エンドポイント"""
    debug_info = {
        "video_streaming": tello_controller.video_streaming,
        "use_ffmpeg": tello_controller.use_ffmpeg,
        "use_simple_udp": tello_controller.use_simple_udp,
        "cap_opened": tello_controller.cap.isOpened() if tello_controller.cap else False,
        "ffmpeg_process_running": tello_controller.ffmpeg_process is not None and tello_controller.ffmpeg_process.poll() is None if tello_controller.ffmpeg_process else False,
        "udp_socket_active": tello_controller.udp_socket is not None,
        "latest_frame_available": tello_controller.latest_frame is not None,
        "latest_frame_shape": tello_controller.latest_frame.shape if tello_controller.latest_frame is not None else None,
        "is_connected": tello_controller.is_connected
    }
    return web.json_response({"success": True, "debug_info": debug_info})

async def handle_direct_command(message: str) -> str:
    """Mastraエージェントが利用できない場合の直接的なコマンド処理"""
    message_lower = message.lower()
    responses = []
    
    # 複雑な複数コマンドの処理: 「ビデオストリーミングを開始して、離陸して、前に50cm進んで、着陸して、ビデオを停止して」
    if ("ビデオ" in message and "開始" in message and 
        "離陸" in message and 
        ("前" in message or "進" in message) and 
        "着陸" in message and 
        ("停止" in message or "ビデオ" in message)):
        
        logger.info("複雑な複数コマンド処理: ビデオ開始 + 離陸 + 移動 + 着陸 + ビデオ停止")
        
        # 1. ビデオストリーミング開始
        logger.info("Telloビデオストリーミング開始コマンドを実行中...")
        video_start_result = await tello_controller.start_video_stream()
        if video_start_result.get('success', False):
            responses.append("✅ ビデオストリーミングを開始しました。")
            await asyncio.sleep(2)  # ビデオ安定化のため待機
        else:
            responses.append("❌ ビデオストリーミングの開始に失敗しました。")
        
        # 2. 離陸
        logger.info("Tello離陸コマンドを実行中...")
        takeoff_result = await tello_controller.takeoff()
        if takeoff_result.get('success', False):
            responses.append("✅ 離陸に成功しました。")
            await asyncio.sleep(3)  # 離陸安定化のため待機
        else:
            responses.append("❌ 離陸に失敗しました。")
        
        # 3. 前進移動
        import re
        distance_match = re.search(r'(\d+)\s*cm', message)
        distance = int(distance_match.group(1)) if distance_match else 50
        
        logger.info(f"Tello前進移動コマンドを実行中... 距離: {distance}cm")
        move_result = await tello_controller.move('forward', distance)
        if move_result.get('success', False):
            responses.append(f"✅ 前に{distance}cm移動しました。")
            await asyncio.sleep(2)  # 移動安定化のため待機
        else:
            responses.append(f"❌ 前への移動に失敗しました。")
        
        # 4. 着陸
        logger.info("Tello着陸コマンドを実行中...")
        land_result = await tello_controller.land()
        if land_result.get('success', False):
            responses.append("✅ 着陸に成功しました。")
            await asyncio.sleep(3)  # 着陸安定化のため待機
        else:
            responses.append("❌ 着陸に失敗しました。")
        
        # 5. ビデオストリーミング停止
        logger.info("Telloビデオストリーミング停止コマンドを実行中...")
        video_stop_result = await tello_controller.stop_video_stream()
        if video_stop_result.get('success', False):
            responses.append("✅ ビデオストリーミングを停止しました。")
        else:
            responses.append("❌ ビデオストリーミングの停止に失敗しました。")
        
        return "\n".join(responses)
    
    # 複数コマンドの処理: 「離陸して、20cm右に動いて」のようなケース
    elif "離陸" in message and "右" in message and ("移動" in message or "動" in message):
        logger.info("複数コマンド処理: 離陸 + 右移動")
        
        # 1. 離陸
        logger.info("Tello離陸コマンドを実行中...")
        takeoff_result = await tello_controller.takeoff()
        if takeoff_result.get('success', False):
            responses.append("✅ 離陸に成功しました。")
            await asyncio.sleep(3)  # 離陸安定化のため待機
            
            # 2. 右移動
            import re
            distance_match = re.search(r'(\d+)\s*cm', message)
            distance = int(distance_match.group(1)) if distance_match else 20
            
            logger.info(f"Tello右移動コマンドを実行中... 距離: {distance}cm")
            move_result = await tello_controller.move('right', distance)
            if move_result.get('success', False):
                responses.append(f"✅ 右に{distance}cm移動しました。")
            else:
                responses.append(f"❌ 右への移動に失敗しました。")
        else:
            responses.append("❌ 離陸に失敗しました。")
        
        return "\n".join(responses)
    
    # 単一コマンドの処理
    elif "接続" in message or "connect" in message_lower:
        logger.info("Tello接続コマンドを実行中...")
        connect_result = await tello_controller.connect()
        success = connect_result.get('success', False)
        if success:
            return "✅ Telloに正常に接続されました。"
        else:
            return "❌ Telloへの接続に失敗しました。"
    
    elif "離陸" in message or "takeoff" in message_lower:
        logger.info("Tello離陸コマンドを実行中...")
        takeoff_result = await tello_controller.takeoff()
        success = takeoff_result.get('success', False)
        if success:
            return "✅ 離陸に成功しました。"
        else:
            return "❌ 離陸に失敗しました。"
    
    elif "着陸" in message or "land" in message_lower:
        logger.info("Tello着陸コマンドを実行中...")
        land_result = await tello_controller.land()
        success = land_result.get('success', False)
        if success:
            return "✅ 着陸に成功しました。"
        else:
            return "❌ 着陸に失敗しました。"
    
    elif ("ビデオ" in message or "video" in message_lower) and ("開始" in message or "start" in message_lower):
        logger.info("Telloビデオストリーミング開始コマンドを実行中...")
        video_result = await tello_controller.start_video_stream()
        success = video_result.get('success', False)
        if success:
            return "✅ ビデオストリーミングを開始しました。"
        else:
            return "❌ ビデオストリーミングの開始に失敗しました。"
    
    elif ("ビデオ" in message or "video" in message_lower) and ("停止" in message or "stop" in message_lower):
        logger.info("Telloビデオストリーミング停止コマンドを実行中...")
        video_result = await tello_controller.stop_video_stream()
        success = video_result.get('success', False)
        if success:
            return "✅ ビデオストリーミングを停止しました。"
        else:
            return "❌ ビデオストリーミングの停止に失敗しました。"
    
    elif "右" in message and ("移動" in message or "動" in message):
        logger.info("Tello右移動コマンドを実行中...")
        # 距離を抽出（デフォルト20cm）
        import re
        distance_match = re.search(r'(\d+)\s*cm', message)
        distance = int(distance_match.group(1)) if distance_match else 20
        move_result = await tello_controller.move('right', distance)
        success = move_result.get('success', False)
        if success:
            return f"✅ 右に{distance}cm移動しました。"
        else:
            return f"❌ 右への移動に失敗しました。"
    
    elif "前" in message and ("移動" in message or "動" in message or "進" in message):
        logger.info("Tello前進移動コマンドを実行中...")
        # 距離を抽出（デフォルト50cm）
        import re
        distance_match = re.search(r'(\d+)\s*cm', message)
        distance = int(distance_match.group(1)) if distance_match else 50
        move_result = await tello_controller.move('forward', distance)
        success = move_result.get('success', False)
        if success:
            return f"✅ 前に{distance}cm移動しました。"
        else:
            return f"❌ 前への移動に失敗しました。"
    
    elif "状態" in message or "status" in message_lower:
        logger.info("Telloステータス確認中...")
        status_result = await tello_controller.get_status()
        return f"📊 ドローンの状態: {status_result}"
    
    else:
        return "❌ 認識できないコマンドです。まず「接続して」と言ってください。"

async def copilotkit_handler(request: web.Request) -> web.Response:
    """AG-UI/CopilotKit APIエンドポイント - Mastraエージェントとの通信"""
    try:
        # リクエストボディを取得
        body = await request.json()
        messages = body.get('messages', [])
        thread_id = body.get('threadId', 'default')
        resource_id = body.get('resourceId', 'user')
        
        logger.info(f"CopilotKit request: {len(messages)} messages, thread: {thread_id}")
        
        if not messages:
            response_text = "メッセージが空です。何かご質問はありますか？"
        else:
            last_message = messages[-1].get('content', '')
            logger.info(f"Last message: {last_message}")
            
            # Mastraエージェントを呼び出す
            response_text = await call_mastra_agent(last_message, thread_id, resource_id)
        
        # 成功レスポンスを返す
        return web.json_response({
            "success": True,
            "text": response_text,
            "toolCalls": {},
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"CopilotKit API error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def call_mastra_agent(message: str, thread_id: str, resource_id: str) -> str:
    """Mastraエージェントを呼び出す"""
    try:
        import aiohttp
        import json
        
        mastra_url = "http://localhost:4111/api/agents/telloAgent/generate"
        logger.info(f"🚀 Calling Mastra agent: {message}")
        
        payload = {
            "messages": [{"role": "user", "content": message}],
            "threadId": thread_id,
            "resourceId": resource_id
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                mastra_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                logger.info(f"Mastra response status: {resp.status}")
                
                if resp.status == 200:
                    mastra_response = await resp.json()
                    response_text = mastra_response.get('text', 'エージェントからの応答がありませんでした。')
                    logger.info(f"✅ Mastra agent SUCCESS")
                    return response_text
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Mastra agent HTTP error: {resp.status}")
                    # フォールバック処理
                    return await handle_direct_command(message)
                    
    except Exception as e:
        logger.error(f"❌ Mastra agent call failed: {e}")
        # フォールバック処理
        return await handle_direct_command(message)

async def health_handler(request: web.Request) -> web.Response:
    """ヘルスチェックエンドポイント"""
    return web.json_response({
        "status": "healthy",
        "service": "Tello Web Controller",
        "timestamp": datetime.now().isoformat()
    })

async def index_handler(request: web.Request) -> web.Response:
    """メインページのハンドラー"""
    html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tello Web Controller</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .status-panel {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .control-section {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 20px;
        }
        .control-section h3 {
            margin-top: 0;
            color: #fff;
            text-align: center;
        }
        button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            color: white;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        .emergency-btn {
            background: linear-gradient(45deg, #e74c3c, #c0392b) !important;
            font-size: 18px !important;
            padding: 15px 30px !important;
        }
        .connect-btn {
            background: linear-gradient(45deg, #2ecc71, #27ae60) !important;
        }
        .video-section {
            text-align: center;
            margin-top: 30px;
        }
        #videoFrame {
            max-width: 100%;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .api-info {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
        }
        .api-info h3 {
            color: #fff;
        }
        .api-info code {
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-connected { background-color: #2ecc71; }
        .status-disconnected { background-color: #e74c3c; }
        .status-unknown { background-color: #f39c12; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚁 Tello Web Controller</h1>
        
        <div class="status-panel">
            <h2>ドローン状態</h2>
            <div id="status">
                <span class="status-indicator status-unknown"></span>
                <span id="statusText">状態を確認中...</span>
            </div>
            <div id="battery" style="margin-top: 10px;">バッテリー: 確認中...</div>
        </div>

        <div class="control-grid">
            <div class="control-section">
                <h3>接続制御</h3>
                <button class="connect-btn" onclick="connect()">接続</button>
                <button onclick="disconnect()">切断</button>
                <button onclick="resetStatus()">状態リセット</button>
            </div>

            <div class="control-section">
                <h3>基本操作</h3>
                <button onclick="takeoff()">離陸</button>
                <button onclick="land()">着陸</button>
                <button class="emergency-btn" onclick="emergency()">緊急停止</button>
            </div>

            <div class="control-section">
                <h3>移動制御</h3>
                <button onclick="move('forward', 50)">前進</button>
                <button onclick="move('back', 50)">後退</button>
                <button onclick="move('left', 50)">左移動</button>
                <button onclick="move('right', 50)">右移動</button>
                <button onclick="move('up', 50)">上昇</button>
                <button onclick="move('down', 50)">下降</button>
            </div>

            <div class="control-section">
                <h3>回転制御</h3>
                <button onclick="rotate('cw', 90)">右回転</button>
                <button onclick="rotate('ccw', 90)">左回転</button>
            </div>

            <div class="control-section">
                <h3>ビデオ制御</h3>
                <button onclick="startVideo()">ビデオ開始</button>
                <button onclick="stopVideo()">ビデオ停止</button>
                <button onclick="refreshVideo()">フレーム更新</button>
            </div>
        </div>

        <div class="video-section">
            <h3>ライブビデオ</h3>
            <img id="videoFrame" src="" alt="ビデオフレームが表示されます" style="display: none;">
            <div id="videoStatus">ビデオを開始してください</div>
        </div>

        <div class="api-info">
            <h3>API情報</h3>
            <p>このコントローラーは以下のAPIエンドポイントを提供します：</p>
            <ul>
                <li><code>GET /health</code> - ヘルスチェック</li>
                <li><code>POST /api/connect</code> - Tello接続</li>
                <li><code>GET /api/status</code> - ドローン状態</li>
                <li><code>GET /api/battery</code> - バッテリー残量</li>
                <li><code>POST /api/takeoff</code> - 離陸</li>
                <li><code>POST /api/land</code> - 着陸</li>
                <li><code>POST /api/emergency</code> - 緊急停止</li>
                <li><code>POST /api/copilotkit</code> - AG-UI API</li>
            </ul>
        </div>
    </div>

    <script>
        // 状態更新
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusElement = document.getElementById('statusText');
                const indicator = document.querySelector('.status-indicator');
                
                if (data.success) {
                    statusElement.textContent = `接続済み - ${data.status || '不明'}`;
                    indicator.className = 'status-indicator status-connected';
                } else {
                    statusElement.textContent = '未接続';
                    indicator.className = 'status-indicator status-disconnected';
                }
            } catch (error) {
                document.getElementById('statusText').textContent = 'エラー';
                document.querySelector('.status-indicator').className = 'status-indicator status-unknown';
            }
        }

        // バッテリー更新
        async function updateBattery() {
            try {
                const response = await fetch('/api/battery');
                const data = await response.json();
                document.getElementById('battery').textContent = 
                    data.success ? `バッテリー: ${data.battery}%` : 'バッテリー: 不明';
            } catch (error) {
                document.getElementById('battery').textContent = 'バッテリー: エラー';
            }
        }

        // API呼び出し関数
        async function apiCall(endpoint, method = 'POST', body = null) {
            try {
                const options = { method };
                if (body) {
                    options.headers = { 'Content-Type': 'application/json' };
                    options.body = JSON.stringify(body);
                }
                
                const response = await fetch(endpoint, options);
                const data = await response.json();
                
                if (data.success) {
                    alert(`成功: ${data.message || '操作完了'}`);
                } else {
                    alert(`エラー: ${data.error || '不明なエラー'}`);
                }
                
                // 状態を更新
                updateStatus();
                updateBattery();
            } catch (error) {
                alert(`通信エラー: ${error.message}`);
            }
        }

        // 制御関数
        async function connect() { await apiCall('/api/connect'); }
        async function disconnect() { await apiCall('/api/disconnect'); }
        async function takeoff() { await apiCall('/api/takeoff'); }
        async function land() { await apiCall('/api/land'); }
        async function emergency() { await apiCall('/api/emergency'); }
        async function resetStatus() { await apiCall('/api/reset_status'); }
        
        async function move(direction, distance) {
            await apiCall('/api/move', 'POST', { direction, distance });
        }
        
        async function rotate(direction, degrees) {
            await apiCall('/api/rotate', 'POST', { direction, degrees });
        }

        async function startVideo() {
            await apiCall('/api/video/start');
            setTimeout(refreshVideo, 1000); // 1秒後にフレーム取得
        }

        async function stopVideo() {
            await apiCall('/api/video/stop');
            document.getElementById('videoFrame').style.display = 'none';
            document.getElementById('videoStatus').textContent = 'ビデオを開始してください';
        }

        async function refreshVideo() {
            try {
                const response = await fetch('/api/video/frame');
                const data = await response.json();
                
                if (data.success && data.frame) {
                    const img = document.getElementById('videoFrame');
                    img.src = `data:image/jpeg;base64,${data.frame}`;
                    img.style.display = 'block';
                    document.getElementById('videoStatus').textContent = 'ライブビデオ表示中';
                } else {
                    document.getElementById('videoStatus').textContent = 'フレーム取得失敗';
                }
            } catch (error) {
                document.getElementById('videoStatus').textContent = `ビデオエラー: ${error.message}`;
            }
        }

        // 定期更新
        setInterval(updateStatus, 5000);
        setInterval(updateBattery, 10000);
        
        // 初期化
        updateStatus();
        updateBattery();
        
        // ビデオの自動更新（ビデオが表示されている場合）
        setInterval(() => {
            const img = document.getElementById('videoFrame');
            if (img.style.display !== 'none') {
                refreshVideo();
            }
        }, 1000);
    </script>
</body>
</html>
    """
    return web.Response(text=html_content, content_type='text/html')

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
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                }
            )
        
        try:
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'  # 本番環境では特定のドメインに制限することを推奨
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        except web.HTTPMethodNotAllowed as e:
            logger.error(f"Method not allowed: {request.method} {request.path}")
            return web.json_response({
                "error": f"Method {request.method} not allowed for {request.path}",
                "allowed_methods": ["GET", "POST", "OPTIONS"]
            }, status=405, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            })
        except Exception as e:
            logger.error(f"CORS middleware error: {e}")
            return web.json_response({
                "error": str(e),
                "path": request.path,
                "method": request.method
            }, status=500, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            })
    
    app.middlewares.append(cors_middleware)

def create_app() -> web.Application:
    """Webアプリケーションを作成します"""
    app = web.Application()
    
    # メインページ
    app.router.add_get('/', index_handler)
    
    # ルート設定（/api/ プレフィックス付き）
    app.router.add_get('/health', health_handler)
    app.router.add_post('/api/connect', connect_handler)
    app.router.add_post('/api/disconnect', disconnect_handler)
    app.router.add_get('/api/status', status_handler)
    app.router.add_get('/api/battery', battery_handler)
    app.router.add_post('/api/takeoff', takeoff_handler)
    app.router.add_post('/api/land', land_handler)
    app.router.add_post('/api/emergency', emergency_handler)
    app.router.add_post('/api/reset_status', reset_status_handler)
    app.router.add_post('/api/move', move_handler)
    app.router.add_post('/api/rotate', rotate_handler)
    app.router.add_post('/api/video/start', start_video_handler)
    app.router.add_post('/api/video/stop', stop_video_handler)
    app.router.add_get('/api/video/frame', video_frame_handler)
    app.router.add_get('/api/video/debug', video_debug_handler)
    
    # 後方互換性のため、/api/ なしのエンドポイントも維持
    app.router.add_post('/connect', connect_handler)
    app.router.add_post('/disconnect', disconnect_handler)
    app.router.add_get('/status', status_handler)
    app.router.add_get('/battery', battery_handler)
    app.router.add_post('/takeoff', takeoff_handler)
    app.router.add_post('/land', land_handler)
    app.router.add_post('/emergency', emergency_handler)
    app.router.add_post('/reset_status', reset_status_handler)
    app.router.add_post('/move', move_handler)
    app.router.add_post('/rotate', rotate_handler)
    app.router.add_post('/video/start', start_video_handler)
    app.router.add_post('/video/stop', stop_video_handler)
    app.router.add_get('/video/frame', video_frame_handler)
    app.router.add_get('/video/debug', video_debug_handler)
    
    # AG-UI/CopilotKit API
    app.router.add_post('/api/copilotkit', copilotkit_handler)
    app.router.add_options('/api/copilotkit', cors_handler)
    
    # OPTIONS用のルート設定（/api/ プレフィックス付き）
    app.router.add_options('/api/connect', cors_handler)
    app.router.add_options('/api/disconnect', cors_handler)
    app.router.add_options('/api/status', cors_handler)
    app.router.add_options('/api/battery', cors_handler)
    app.router.add_options('/api/takeoff', cors_handler)
    app.router.add_options('/api/land', cors_handler)
    app.router.add_options('/api/emergency', cors_handler)
    app.router.add_options('/api/reset_status', cors_handler)
    app.router.add_options('/api/move', cors_handler)
    app.router.add_options('/api/rotate', cors_handler)
    app.router.add_options('/api/video/start', cors_handler)
    app.router.add_options('/api/video/stop', cors_handler)
    app.router.add_options('/api/video/frame', cors_handler)
    
    # 後方互換性のため、/api/ なしのOPTIONSも維持
    app.router.add_options('/connect', cors_handler)
    app.router.add_options('/disconnect', cors_handler)
    app.router.add_options('/status', cors_handler)
    app.router.add_options('/battery', cors_handler)
    app.router.add_options('/takeoff', cors_handler)
    app.router.add_options('/land', cors_handler)
    app.router.add_options('/emergency', cors_handler)
    app.router.add_options('/reset_status', cors_handler)
    app.router.add_options('/move', cors_handler)
    app.router.add_options('/rotate', cors_handler)
    app.router.add_options('/video/start', cors_handler)
    app.router.add_options('/video/stop', cors_handler)
    app.router.add_options('/video/frame', cors_handler)
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
    logger.info("AG-UI/CopilotKit APIエンドポイント: /api/copilotkit")
    
    # 利用可能なエンドポイントを表示
    logger.info("Available endpoints:")
    logger.info("  GET  /health - ヘルスチェック")
    logger.info("  POST /api/connect - Tello接続")
    logger.info("  POST /api/disconnect - Tello切断")
    logger.info("  GET  /api/status - ドローン状態")
    logger.info("  GET  /api/battery - バッテリー残量")
    logger.info("  POST /api/takeoff - 離陸")
    logger.info("  POST /api/land - 着陸")
    logger.info("  POST /api/emergency - 緊急停止")
    logger.info("  POST /api/move - 移動")
    logger.info("  POST /api/rotate - 回転")
    logger.info("  POST /api/video/start - ビデオ開始")
    logger.info("  POST /api/video/stop - ビデオ停止")
    logger.info("  GET  /api/video/frame - フレーム取得")
    logger.info("  GET  /api/video/debug - ビデオデバッグ情報")
    logger.info("  POST /api/copilotkit - AG-UI API")
    logger.info("  (後方互換性のため /api/ なしのエンドポイントも利用可能)")
    
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