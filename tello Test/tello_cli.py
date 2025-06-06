#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello ドローン CLI制御プログラム
コマンドライン引数を受け取ってJSON形式で結果を返します
"""

import sys
import json
import argparse
import os
from tello_connection import TelloController

# 標準出力をUTF-8に設定
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='Tello Drone CLI Controller')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--distance', type=int, help='Distance in cm (20-500)')
    parser.add_argument('--degrees', type=int, help='Rotation degrees (1-360)')
    
    args = parser.parse_args()
    
    tello = TelloController()
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