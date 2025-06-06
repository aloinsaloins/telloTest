#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI Tello 簡単な使用例
基本的な飛行パターンのデモンストレーション
"""

from tello_connection import TelloController
import time

def simple_flight_demo():
    """簡単な飛行デモ"""
    tello = TelloController()
    
    try:
        # Telloに接続
        if not tello.connect():
            print("❌ Telloに接続できませんでした")
            return
        
        print("🔋 バッテリー残量:", tello.get_battery(), "%")
        
        # バッテリー残量チェック
        battery = tello.get_battery()
        if battery < 20:
            print("⚠️ バッテリー残量が少ないため、飛行を中止します")
            return
        
        print("3秒後に自動飛行を開始します...")
        time.sleep(3)
        
        # 離陸
        print("🚁 離陸します")
        if not tello.takeoff():
            print("❌ 離陸に失敗しました")
            return
        
        time.sleep(3)
        
        # 簡単な飛行パターン
        print("📐 正方形の飛行パターンを実行します")
        
        # 前進
        print("→ 前進 100cm")
        tello.move_forward(100)
        time.sleep(2)
        
        # 右回転
        print("↻ 右に90度回転")
        tello.rotate_clockwise(90)
        time.sleep(2)
        
        # 前進
        print("→ 前進 100cm")
        tello.move_forward(100)
        time.sleep(2)
        
        # 右回転
        print("↻ 右に90度回転")
        tello.rotate_clockwise(90)
        time.sleep(2)
        
        # 前進
        print("→ 前進 100cm")
        tello.move_forward(100)
        time.sleep(2)
        
        # 右回転
        print("↻ 右に90度回転")
        tello.rotate_clockwise(90)
        time.sleep(2)
        
        # 前進（元の位置に戻る）
        print("→ 前進 100cm（元の位置に戻る）")
        tello.move_forward(100)
        time.sleep(2)
        
        # 右回転（元の向きに戻る）
        print("↻ 右に90度回転（元の向きに戻る）")
        tello.rotate_clockwise(90)
        time.sleep(2)
        
        # 着陸
        print("🛬 着陸します")
        tello.land()
        
        print("✅ 飛行デモ完了!")
        
    except KeyboardInterrupt:
        print("\n🛑 プログラムを中断しています...")
        print("🚨 緊急着陸を実行します")
        tello.emergency()
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("🚨 緊急着陸を実行します")
        tello.emergency()
    
    finally:
        tello.disconnect()

def video_stream_demo():
    """ビデオストリームのデモ"""
    tello = TelloController()
    
    try:
        # Telloに接続
        if not tello.connect():
            print("❌ Telloに接続できませんでした")
            return
        
        print("📹 ビデオストリームを開始します")
        if tello.start_video_stream():
            print("ビデオウィンドウが開きます。'q'キーで終了してください。")
            
            import cv2
            while True:
                frame = tello.get_video_frame()
                if frame is not None:
                    # フレームにテキストを追加
                    cv2.putText(frame, 'DJI Tello Video Stream', (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, 'Press Q to quit', (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    cv2.imshow('Tello Video Stream', frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            cv2.destroyAllWindows()
            tello.stop_video_stream()
        else:
            print("❌ ビデオストリームの開始に失敗しました")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    
    finally:
        tello.disconnect()

def main():
    """メイン関数"""
    print("=== DJI Tello デモプログラム ===")
    print("1. 簡単な飛行デモ")
    print("2. ビデオストリームデモ")
    print("3. 終了")
    
    while True:
        choice = input("\n選択してください (1-3): ").strip()
        
        if choice == '1':
            print("\n⚠️ 注意: ドローンが離陸します。周囲に十分なスペースがあることを確認してください。")
            confirm = input("続行しますか？ (y/N): ").strip().lower()
            if confirm == 'y':
                simple_flight_demo()
            break
        elif choice == '2':
            video_stream_demo()
            break
        elif choice == '3':
            print("プログラムを終了します")
            break
        else:
            print("❌ 無効な選択です。1-3の数字を入力してください。")

if __name__ == "__main__":
    main() 