#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello ドローン CLI制御プログラム（静音版）
コマンドライン引数を受け取ってJSON形式で結果を返します
print文を使わずにエラーメッセージもJSONに含めます
"""

import sys
import json
import argparse
import socket
import threading
import time
from typing import Optional

class SilentTelloController:
    """DJI Telloドローンを制御するクラス（静音版）"""
    
    def __init__(self):
        # Telloとの通信設定
        self.tello_ip = '192.168.10.1'
        self.tello_port = 8889
        self.local_ip = ''
        self.local_port = 9000
        
        # ソケット初期化
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.local_ip, self.local_port))
        
        # 応答受信用スレッド
        self.receive_thread = threading.Thread(target=self._receive_response)
        self.receive_thread.daemon = True
        
        # 接続状態
        self.is_connected = False
        
    def connect(self) -> bool:
        """Telloに接続します"""
        try:
            # 応答受信スレッド開始
            self.receive_thread.start()
            
            # SDKモードを有効化
            response = self.send_command('command')
            if 'ok' in response.lower():
                self.is_connected = True
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def send_command(self, command: str, timeout: int = 5) -> str:
        """コマンドをTelloに送信し、応答を受信します"""
        try:
            self.socket.sendto(command.encode('utf-8'), (self.tello_ip, self.tello_port))
            
            # 応答を待機
            self.socket.settimeout(timeout)
            response, _ = self.socket.recvfrom(1024)
            response_str = response.decode('utf-8').strip()
            
            return response_str
            
        except socket.timeout:
            return "timeout"
        except Exception as e:
            return "error"
    
    def _receive_response(self):
        """応答を継続的に受信するスレッド"""
        while True:
            try:
                response, _ = self.socket.recvfrom(1024)
            except Exception as e:
                break
    
    def get_battery(self) -> int:
        """バッテリー残量を取得します"""
        response = self.send_command('battery?')
        try:
            return int(response)
        except ValueError:
            return 0
    
    def takeoff(self) -> bool:
        """離陸します"""
        if not self.is_connected:
            return False
            
        response = self.send_command('takeoff')
        return 'ok' in response.lower()
    
    def land(self) -> bool:
        """着陸します"""
        if not self.is_connected:
            return False
            
        response = self.send_command('land')
        return 'ok' in response.lower()
    
    def emergency(self) -> bool:
        """緊急停止します"""
        response = self.send_command('emergency')
        return 'ok' in response.lower()
    
    def move_up(self, distance: int) -> bool:
        """上昇します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'up {distance}')
            return 'ok' in response.lower()
        return False
    
    def move_down(self, distance: int) -> bool:
        """下降します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'down {distance}')
            return 'ok' in response.lower()
        return False
    
    def move_left(self, distance: int) -> bool:
        """左に移動します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'left {distance}')
            return 'ok' in response.lower()
        return False
    
    def move_right(self, distance: int) -> bool:
        """右に移動します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'right {distance}')
            return 'ok' in response.lower()
        return False
    
    def move_forward(self, distance: int) -> bool:
        """前進します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'forward {distance}')
            return 'ok' in response.lower()
        return False
    
    def move_back(self, distance: int) -> bool:
        """後退します (20-500cm)"""
        if 20 <= distance <= 500:
            response = self.send_command(f'back {distance}')
            return 'ok' in response.lower()
        return False
    
    def rotate_clockwise(self, degrees: int) -> bool:
        """時計回りに回転します (1-360度)"""
        if 1 <= degrees <= 360:
            response = self.send_command(f'cw {degrees}')
            return 'ok' in response.lower()
        return False
    
    def rotate_counter_clockwise(self, degrees: int) -> bool:
        """反時計回りに回転します (1-360度)"""
        if 1 <= degrees <= 360:
            response = self.send_command(f'ccw {degrees}')
            return 'ok' in response.lower()
        return False
    
    def disconnect(self):
        """Telloから切断します"""
        try:
            self.socket.close()
            self.is_connected = False
        except Exception as e:
            pass

def main():
    parser = argparse.ArgumentParser(description='Tello Drone CLI Controller (Silent)')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--distance', type=int, help='Distance in cm (20-500)')
    parser.add_argument('--degrees', type=int, help='Rotation degrees (1-360)')
    
    args = parser.parse_args()
    
    tello = SilentTelloController()
    result = {
        "success": False,
        "message": "",
        "data": {}
    }
    
    try:
        # コマンドに応じて処理を実行
        if args.command == 'connect':
            success = tello.connect()
            result["success"] = success
            result["message"] = "接続成功" if success else "接続失敗"
            
        elif args.command == 'status':
            if tello.connect():
                battery = tello.get_battery()
                result["success"] = True
                result["message"] = f"ステータス確認完了"
                result["data"] = {
                    "battery": battery,
                    "connected": tello.is_connected
                }
            else:
                result["message"] = "接続失敗"
                
        elif args.command == 'takeoff':
            if tello.connect():
                # バッテリーチェック
                battery = tello.get_battery()
                if battery < 20:
                    result["message"] = f"バッテリー残量が不足しています ({battery}%)"
                else:
                    success = tello.takeoff()
                    result["success"] = success
                    result["message"] = "離陸成功" if success else "離陸失敗"
            else:
                result["message"] = "接続失敗"
                
        elif args.command == 'land':
            if tello.connect():
                success = tello.land()
                result["success"] = success
                result["message"] = "着陸成功" if success else "着陸失敗"
            else:
                result["message"] = "接続失敗"
                
        elif args.command == 'emergency':
            if tello.connect():
                success = tello.emergency()
                result["success"] = success
                result["message"] = "緊急停止実行" if success else "緊急停止失敗"
            else:
                result["message"] = "接続失敗"
                
        elif args.command in ['up', 'down', 'left', 'right', 'forward', 'back']:
            if not args.distance:
                result["message"] = "距離パラメータが必要です"
            elif not (20 <= args.distance <= 500):
                result["message"] = "距離は20-500cmの範囲で指定してください"
            elif tello.connect():
                success = False
                if args.command == 'up':
                    success = tello.move_up(args.distance)
                elif args.command == 'down':
                    success = tello.move_down(args.distance)
                elif args.command == 'left':
                    success = tello.move_left(args.distance)
                elif args.command == 'right':
                    success = tello.move_right(args.distance)
                elif args.command == 'forward':
                    success = tello.move_forward(args.distance)
                elif args.command == 'back':
                    success = tello.move_back(args.distance)
                
                result["success"] = success
                result["message"] = f"{args.command} {args.distance}cm {'成功' if success else '失敗'}"
            else:
                result["message"] = "接続失敗"
                
        elif args.command in ['cw', 'ccw']:
            if not args.degrees:
                result["message"] = "角度パラメータが必要です"
            elif not (1 <= args.degrees <= 360):
                result["message"] = "角度は1-360度の範囲で指定してください"
            elif tello.connect():
                success = False
                if args.command == 'cw':
                    success = tello.rotate_clockwise(args.degrees)
                elif args.command == 'ccw':
                    success = tello.rotate_counter_clockwise(args.degrees)
                
                result["success"] = success
                result["message"] = f"回転 {args.degrees}度 {'成功' if success else '失敗'}"
            else:
                result["message"] = "接続失敗"
                
        else:
            result["message"] = f"不明なコマンド: {args.command}"
            
    except Exception as e:
        result["success"] = False
        result["message"] = f"エラー: {str(e)}"
    
    finally:
        try:
            tello.disconnect()
        except:
            pass
    
    # JSON形式で結果を出力
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main() 