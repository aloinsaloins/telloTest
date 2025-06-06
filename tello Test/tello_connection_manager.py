#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello 永続接続マネージャー
Telloドローンとの接続を永続化し、複数のコマンドで再利用できるようにします
"""

import json
import sys
import argparse
import atexit
import signal
import os
from tello_connection import TelloController

class TelloConnectionManager:
    """Tello接続を管理するシングルトンクラス"""
    
    _instance = None
    _tello_controller = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """シグナルハンドラーを設定して、プログラム終了時に適切に切断する"""
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナル受信時の処理"""
        self.cleanup()
        sys.exit(0)
    
    def get_controller(self) -> TelloController:
        """Telloコントローラーを取得（必要に応じて接続）"""
        if self._tello_controller is None:
            self._tello_controller = TelloController()
        return self._tello_controller
    
    def connect(self) -> dict:
        """Telloに接続"""
        try:
            controller = self.get_controller()
            
            if controller.is_connected:
                battery = controller.get_battery()
                return {
                    "success": True,
                    "message": "既に接続されています",
                    "data": {
                        "battery": battery,
                        "connected": True
                    }
                }
            
            success = controller.connect()
            if success:
                battery = controller.get_battery()
                return {
                    "success": True,
                    "message": "接続成功",
                    "data": {
                        "battery": battery,
                        "connected": True
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "接続失敗",
                    "data": {
                        "connected": False
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"接続エラー: {str(e)}",
                "data": {
                    "connected": False
                }
            }
    
    def disconnect(self) -> dict:
        """Telloから切断"""
        try:
            if self._tello_controller and self._tello_controller.is_connected:
                self._tello_controller.disconnect()
                return {
                    "success": True,
                    "message": "切断成功",
                    "data": {
                        "connected": False
                    }
                }
            else:
                return {
                    "success": True,
                    "message": "既に切断されています",
                    "data": {
                        "connected": False
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"切断エラー: {str(e)}",
                "data": {
                    "connected": False
                }
            }
    
    def get_status(self) -> dict:
        """接続状態とバッテリー残量を取得"""
        try:
            controller = self.get_controller()
            
            if not controller.is_connected:
                return {
                    "success": True,
                    "message": "未接続",
                    "data": {
                        "battery": 0,
                        "connected": False
                    }
                }
            
            battery = controller.get_battery()
            return {
                "success": True,
                "message": "ステータス確認完了",
                "data": {
                    "battery": battery,
                    "connected": True
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"ステータス確認エラー: {str(e)}",
                "data": {
                    "battery": 0,
                    "connected": False
                }
            }
    
    def execute_command(self, command: str, **kwargs) -> dict:
        """Telloコマンドを実行"""
        try:
            controller = self.get_controller()
            
            # 接続確認
            if not controller.is_connected:
                connect_result = self.connect()
                if not connect_result["success"]:
                    return connect_result
            
            # コマンド実行
            if command == 'takeoff':
                # バッテリーチェック
                battery = controller.get_battery()
                if battery < 20:
                    return {
                        "success": False,
                        "message": f"バッテリー残量が不足しています ({battery}%)",
                        "data": {"battery": battery}
                    }
                
                success = controller.takeoff()
                return {
                    "success": success,
                    "message": "離陸成功" if success else "離陸失敗"
                }
            
            elif command == 'land':
                success = controller.land()
                return {
                    "success": success,
                    "message": "着陸成功" if success else "着陸失敗"
                }
            
            elif command == 'emergency':
                success = controller.emergency()
                return {
                    "success": success,
                    "message": "緊急停止実行" if success else "緊急停止失敗"
                }
            
            elif command in ['up', 'down', 'left', 'right', 'forward', 'back']:
                distance = kwargs.get('distance')
                if not distance or not (20 <= distance <= 500):
                    return {
                        "success": False,
                        "message": "距離は20-500cmの範囲で指定してください"
                    }
                
                method_map = {
                    'up': controller.move_up,
                    'down': controller.move_down,
                    'left': controller.move_left,
                    'right': controller.move_right,
                    'forward': controller.move_forward,
                    'back': controller.move_back
                }
                
                success = method_map[command](distance)
                return {
                    "success": success,
                    "message": f"{command} {distance}cm {'成功' if success else '失敗'}"
                }
            
            elif command in ['cw', 'ccw']:
                degrees = kwargs.get('degrees')
                if not degrees or not (1 <= degrees <= 360):
                    return {
                        "success": False,
                        "message": "角度は1-360度の範囲で指定してください"
                    }
                
                if command == 'cw':
                    success = controller.rotate_clockwise(degrees)
                else:
                    success = controller.rotate_counter_clockwise(degrees)
                
                return {
                    "success": success,
                    "message": f"回転 {degrees}度 {'成功' if success else '失敗'}"
                }
            
            else:
                return {
                    "success": False,
                    "message": f"不明なコマンド: {command}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"コマンド実行エラー: {str(e)}"
            }
    
    def cleanup(self):
        """クリーンアップ処理"""
        if self._tello_controller:
            try:
                self._tello_controller.disconnect()
            except:
                pass


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Tello Connection Manager')
    parser.add_argument('action', choices=['connect', 'disconnect', 'status', 'execute'], 
                       help='実行するアクション')
    parser.add_argument('--command', help='実行するコマンド（executeアクション用）')
    parser.add_argument('--distance', type=int, help='移動距離（cm）')
    parser.add_argument('--degrees', type=int, help='回転角度（度）')
    
    args = parser.parse_args()
    
    manager = TelloConnectionManager()
    result = {}
    
    try:
        if args.action == 'connect':
            result = manager.connect()
        elif args.action == 'disconnect':
            result = manager.disconnect()
        elif args.action == 'status':
            result = manager.get_status()
        elif args.action == 'execute':
            if not args.command:
                result = {
                    "success": False,
                    "message": "executeアクションにはcommandパラメータが必要です"
                }
            else:
                kwargs = {}
                if args.distance is not None:
                    kwargs['distance'] = args.distance
                if args.degrees is not None:
                    kwargs['degrees'] = args.degrees
                
                result = manager.execute_command(args.command, **kwargs)
        
    except Exception as e:
        result = {
            "success": False,
            "message": f"エラー: {str(e)}"
        }
    
    # JSON形式で結果を出力
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main() 