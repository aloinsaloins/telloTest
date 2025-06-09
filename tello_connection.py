#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello ドローン接続プログラム
Telloドローンとの基本的な接続と制御を行います
"""

import socket
import threading
import time
import cv2
import numpy as np
from typing import Optional
import queue

class TelloController:
    """DJI Telloドローンを制御するクラス"""
    
    def __init__(self):
        # Telloとの通信設定
        self.tello_ip = '192.168.10.1'
        self.tello_port = 8889
        self.local_ip = ''
        self.local_port = 9000
        
        # ビデオストリーム設定
        self.video_port = 11111
        
        # ソケット初期化
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.local_ip, self.local_port))
        
        # 応答キュー
        self.response_queue = queue.Queue()
        
        # 応答受信用スレッド
        self.receive_thread = threading.Thread(target=self._receive_response)
        self.receive_thread.daemon = True
        self.running = True
        
        # ビデオキャプチャ
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 接続状態
        self.is_connected = False
        
    def connect(self) -> bool:
        """Telloに接続します"""
        try:
            print("Telloに接続中...")
            
            # 応答受信スレッド開始
            self.receive_thread.start()
            
            # 少し待機してスレッドが開始されるのを確認
            time.sleep(0.5)
            
            # SDKモードを有効化（複数回試行）
            for attempt in range(3):
                print(f"接続試行 {attempt + 1}/3")
                response = self.send_command('command', timeout=10)
                
                if 'ok' in response.lower():
                    self.is_connected = True
                    print("Telloに正常に接続されました")
                    
                    # バッテリー残量を確認
                    battery = self.get_battery()
                    print(f"バッテリー残量: {battery}%")
                    
                    return True
                elif response == "timeout":
                    print(f"接続タイムアウト (試行 {attempt + 1})")
                    time.sleep(1)  # 1秒待機してから再試行
                else:
                    print(f"予期しない応答: {response}")
                    time.sleep(1)
            
            print("Tello接続に失敗しました")
            return False
                
        except Exception as e:
            print(f"接続エラー: {e}")
            return False
    
    def send_command(self, command: str, timeout: int = 5) -> str:
        """コマンドをTelloに送信し、応答を受信します"""
        try:
            print(f"送信: {command}")
            
            # キューをクリア
            while not self.response_queue.empty():
                try:
                    self.response_queue.get_nowait()
                except queue.Empty:
                    break
            
            # コマンド送信
            self.socket.sendto(command.encode('utf-8'), (self.tello_ip, self.tello_port))
            
            # 応答を待機
            try:
                response = self.response_queue.get(timeout=timeout)
                print(f"応答: {response}")
                return response
            except queue.Empty:
                print("コマンドタイムアウト")
                return "timeout"
            
        except Exception as e:
            print(f"コマンド送信エラー: {e}")
            return "error"
    
    def _receive_response(self):
        """応答を継続的に受信するスレッド"""
        while self.running:
            try:
                self.socket.settimeout(1.0)  # 1秒のタイムアウトを設定
                response, _ = self.socket.recvfrom(1024)
                
                # 複数のエンコーディングを試行
                response_str = None
                for encoding in ['utf-8', 'ascii', 'latin-1']:
                    try:
                        response_str = response.decode(encoding).strip()
                        break
                    except UnicodeDecodeError:
                        continue
                
                # すべてのエンコーディングが失敗した場合
                if response_str is None:
                    # バイナリデータとして処理し、印刷可能文字のみ抽出
                    response_str = ''.join(chr(b) for b in response if 32 <= b <= 126)
                    if not response_str:
                        # 完全にバイナリの場合はスキップ
                        continue
                
                print(f"受信: {response_str}")
                
                # 応答をキューに追加
                self.response_queue.put(response_str)
                
            except socket.timeout:
                # タイムアウトは正常（ループを継続）
                continue
            except Exception as e:
                if self.running:  # 正常な切断でない場合のみエラー表示
                    print(f"受信エラー: {e}")
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
            print("Telloに接続されていません")
            return False
            
        print("離陸中...")
        response = self.send_command('takeoff')
        return 'ok' in response.lower()
    
    def land(self) -> bool:
        """着陸します"""
        if not self.is_connected:
            print("Telloに接続されていません")
            return False
            
        print("着陸中...")
        response = self.send_command('land')
        return 'ok' in response.lower()
    
    def emergency(self) -> bool:
        """緊急停止します"""
        print("緊急停止!")
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
    
    def start_video_stream(self) -> bool:
        """ビデオストリームを開始します"""
        try:
            response = self.send_command('streamon')
            if 'ok' in response.lower():
                # OpenCVでビデオキャプチャを初期化
                self.cap = cv2.VideoCapture(f'udp://@0.0.0.0:{self.video_port}')
                print("ビデオストリーム開始")
                return True
            return False
        except Exception as e:
            print(f"ビデオストリーム開始エラー: {e}")
            return False
    
    def stop_video_stream(self) -> bool:
        """ビデオストリームを停止します"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            response = self.send_command('streamoff')
            print("ビデオストリーム停止")
            return 'ok' in response.lower()
        except Exception as e:
            print(f"ビデオストリーム停止エラー: {e}")
            return False
    
    def get_video_frame(self) -> Optional[np.ndarray]:
        """ビデオフレームを取得します"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def disconnect(self):
        """Telloから切断します"""
        try:
            self.running = False  # 受信スレッドを停止
            
            if self.cap:
                self.stop_video_stream()
            
            # スレッドの終了を待機
            if self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2)
            
            self.socket.close()
            self.is_connected = False
            print("Telloから切断されました")
        except Exception as e:
            print(f"切断エラー: {e}")


def main():
    """メイン関数 - 基本的な使用例"""
    tello = TelloController()
    
    try:
        # Telloに接続
        if not tello.connect():
            return
        
        # 基本情報を取得
        print(f"🔋 バッテリー: {tello.get_battery()}%")
        
        # ユーザー入力待ち
        print("\n=== Tello制御コマンド ===")
        print("takeoff - 離陸")
        print("land - 着陸")
        print("up/down/left/right/forward/back [距離] - 移動")
        print("cw/ccw [角度] - 回転")
        print("video - ビデオストリーム開始")
        print("emergency - 緊急停止")
        print("quit - 終了")
        print("========================\n")
        
        while True:
            command = input("コマンドを入力してください: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'takeoff':
                tello.takeoff()
            elif command == 'land':
                tello.land()
            elif command == 'emergency':
                tello.emergency()
            elif command == 'video':
                if tello.start_video_stream():
                    print("ビデオウィンドウを開きます。'q'キーで終了してください。")
                    while True:
                        frame = tello.get_video_frame()
                        if frame is not None:
                            cv2.imshow('Tello Video', frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
                    cv2.destroyAllWindows()
                    tello.stop_video_stream()
            elif command.startswith(('up', 'down', 'left', 'right', 'forward', 'back')):
                parts = command.split()
                if len(parts) == 2:
                    try:
                        distance = int(parts[1])
                        direction = parts[0]
                        if direction == 'up':
                            tello.move_up(distance)
                        elif direction == 'down':
                            tello.move_down(distance)
                        elif direction == 'left':
                            tello.move_left(distance)
                        elif direction == 'right':
                            tello.move_right(distance)
                        elif direction == 'forward':
                            tello.move_forward(distance)
                        elif direction == 'back':
                            tello.move_back(distance)
                    except ValueError:
                        print("距離は数値で入力してください")
                else:
                    print("使用法: [方向] [距離(cm)]")
            elif command.startswith(('cw', 'ccw')):
                parts = command.split()
                if len(parts) == 2:
                    try:
                        degrees = int(parts[1])
                        if parts[0] == 'cw':
                            tello.rotate_clockwise(degrees)
                        else:
                            tello.rotate_counter_clockwise(degrees)
                    except ValueError:
                        print("角度は数値で入力してください")
                else:
                    print("使用法: [cw/ccw] [角度(度)]")
            else:
                print("不明なコマンドです")
    
    except KeyboardInterrupt:
        print("\n🛑 プログラムを中断しています...")
    
    finally:
        tello.disconnect()


if __name__ == "__main__":
    main() 