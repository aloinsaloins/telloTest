#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tello 接続テストスクリプト
改善されたバイナリデータフィルタリング機能をテストします
"""

import asyncio
import aiohttp
import json
import time

async def test_tello_api():
    """Tello Web API の動作テスト"""
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        print("Tello Web API テスト開始")
        print("=" * 50)
        
        # 1. ヘルスチェック
        print("\n1. ヘルスチェック...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                result = await resp.json()
                print(f"OK サーバー状態: {result['status']}")
        except Exception as e:
            print(f"ERROR ヘルスチェックエラー: {e}")
            return
        
        # 2. Tello接続テスト
        print("\n2. Tello接続テスト...")
        try:
            async with session.post(f"{base_url}/connect") as resp:
                result = await resp.json()
                print(f"接続結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if not result.get('success'):
                    print("ERROR Tello接続に失敗しました。実機が必要です。")
                    print("INFO Webサーバーのログをチェックしてください。")
                    return
                    
        except Exception as e:
            print(f"ERROR 接続テストエラー: {e}")
            return
        
        # 3. バッテリー確認
        print("\n3. バッテリー残量確認...")
        try:
            async with session.get(f"{base_url}/battery") as resp:
                result = await resp.json()
                print(f"バッテリー: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"ERROR バッテリー確認エラー: {e}")
        
        # 4. 状態確認
        print("\n4. ドローン状態確認...")
        try:
            async with session.get(f"{base_url}/status") as resp:
                result = await resp.json()
                print(f"状態: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"ERROR 状態確認エラー: {e}")
        
        # 5. 切断テスト
        print("\n5. 切断テスト...")
        try:
            async with session.post(f"{base_url}/disconnect") as resp:
                result = await resp.json()
                print(f"切断結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"ERROR 切断テストエラー: {e}")
        
        print("\nテスト完了！")

def test_connection_monitoring():
    """接続監視テスト（バイナリデータフィルタリング効果確認）"""
    print("\n接続監視テスト（10秒間）")
    print("このテストでバイナリデータのフィルタリング効果を確認します")
    print("Webサーバーのログを観察してください...")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        remaining = 10 - int(time.time() - start_time)
        print(f"残り {remaining}秒... ", end="\r")
        await asyncio.sleep(1)
    
    print("\nOK 監視テスト完了")
    print("INFO WARNINGレベルのメッセージが大幅に減っているはずです")

async def interactive_test():
    """インタラクティブAPIテスト"""
    base_url = "http://localhost:8080"
    
    print("\nインタラクティブAPIテスト")
    print("=" * 40)
    print("利用可能なコマンド:")
    print("- connect: Tello接続")
    print("- battery: バッテリー確認")
    print("- status: 状態確認")
    print("- takeoff: 離陸")
    print("- land: 着陸")
    print("- emergency: 緊急停止")
    print("- disconnect: 切断")
    print("- quit: 終了")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        while True:
            command = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("\nコマンドを入力 > ").strip().lower()
            )
            
            if command == 'quit':
                break
            
            try:
                if command == 'connect':
                    async with session.post(f"{base_url}/connect") as resp:
                        result = await resp.json()
                elif command == 'battery':
                    async with session.get(f"{base_url}/battery") as resp:
                        result = await resp.json()
                elif command == 'status':
                    async with session.get(f"{base_url}/status") as resp:
                        result = await resp.json()
                elif command == 'takeoff':
                    async with session.post(f"{base_url}/takeoff") as resp:
                        result = await resp.json()
                elif command == 'land':
                    async with session.post(f"{base_url}/land") as resp:
                        result = await resp.json()
                elif command == 'emergency':
                    async with session.post(f"{base_url}/emergency") as resp:
                        result = await resp.json()
                elif command == 'disconnect':
                    async with session.post(f"{base_url}/disconnect") as resp:
                        result = await resp.json()
                else:
                    print("ERROR 不明なコマンドです")
                    continue
                
                print(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
            except Exception as e:
                print(f"ERROR API呼び出しエラー: {e}")

def main():
    """メイン関数"""
    print("Tello 接続改善テスト")
    print("1. 基本APIテスト")
    print("2. 接続監視テスト")
    print("3. インタラクティブテスト")
    
    choice = input("選択してください (1/2/3): ").strip()
    
    if choice == '1':
        print("\n注意: Webサーバー (tello_web_server.py) が起動していることを確認してください")
        input("準備ができたらEnterキーを押してください...")
        asyncio.run(test_tello_api())
    elif choice == '2':
        print("\n注意: Webサーバーを起動してTelloに接続してから実行してください")
        input("準備ができたらEnterキーを押してください...")
        test_connection_monitoring()
    elif choice == '3':
        print("\n注意: Webサーバー (tello_web_server.py) が起動していることを確認してください")
        input("準備ができたらEnterキーを押してください...")
        asyncio.run(interactive_test())
    else:
        print("ERROR 無効な選択です")

if __name__ == "__main__":
    main() 