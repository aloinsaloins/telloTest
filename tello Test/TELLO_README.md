# DJI Tello ドローン接続プログラム

このプログラムは、DJI Telloドローンとの接続と基本的な制御を行うPythonライブラリです。

## 📋 必要な環境

- Python 3.7以上
- DJI Telloドローン
- Wi-Fi接続

## 🚀 セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. Telloドローンとの接続

1. Telloドローンの電源を入れます
2. PCのWi-Fi設定で「TELLO-XXXXXX」ネットワークに接続します
3. パスワードは不要です

## 📁 ファイル構成

- `tello_connection.py` - メインのTello制御クラス
- `tello_example.py` - 使用例とデモプログラム
- `requirements.txt` - 必要なPythonライブラリ
- `TELLO_README.md` - このファイル

## 🎮 基本的な使用方法

### インタラクティブモード

```bash
python tello_connection.py
```

利用可能なコマンド:
- `takeoff` - 離陸
- `land` - 着陸
- `up [距離]` - 上昇 (20-500cm)
- `down [距離]` - 下降 (20-500cm)
- `left [距離]` - 左移動 (20-500cm)
- `right [距離]` - 右移動 (20-500cm)
- `forward [距離]` - 前進 (20-500cm)
- `back [距離]` - 後退 (20-500cm)
- `cw [角度]` - 時計回り回転 (1-360度)
- `ccw [角度]` - 反時計回り回転 (1-360度)
- `video` - ビデオストリーム開始
- `emergency` - 緊急停止
- `quit` - 終了

### デモプログラム

```bash
python tello_example.py
```

## 💻 プログラムでの使用例

```python
from tello_connection import TelloController

# Telloコントローラーを初期化
tello = TelloController()

try:
    # 接続
    if tello.connect():
        print("接続成功!")
        
        # バッテリー残量確認
        battery = tello.get_battery()
        print(f"バッテリー: {battery}%")
        
        # 離陸
        tello.takeoff()
        
        # 前進100cm
        tello.move_forward(100)
        
        # 右に90度回転
        tello.rotate_clockwise(90)
        
        # 着陸
        tello.land()
        
finally:
    # 切断
    tello.disconnect()
```

## 📹 ビデオストリーム

```python
# ビデオストリーム開始
if tello.start_video_stream():
    while True:
        frame = tello.get_video_frame()
        if frame is not None:
            cv2.imshow('Tello Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cv2.destroyAllWindows()
    tello.stop_video_stream()
```

## ⚠️ 安全上の注意

1. **飛行前の確認**
   - 周囲に十分なスペース（最低3m×3m）があることを確認
   - 人や障害物がないことを確認
   - バッテリー残量が20%以上あることを確認

2. **緊急時の対応**
   - 何か問題が発生した場合は、すぐに`emergency`コマンドを実行
   - Ctrl+Cでプログラムを中断すると自動的に緊急停止

3. **法的な注意**
   - 日本国内でドローンを飛行させる場合は、航空法等の関連法規を遵守してください
   - 人口集中地区での飛行には許可が必要です

## 🔧 トラブルシューティング

### 接続できない場合

1. TelloのWi-Fiネットワークに正しく接続されているか確認
2. ファイアウォールがUDPポート8889, 9000, 11111をブロックしていないか確認
3. Telloドローンが十分に充電されているか確認

### ビデオストリームが表示されない場合

1. OpenCVが正しくインストールされているか確認
2. UDPポート11111が利用可能か確認
3. 他のアプリケーションがカメラを使用していないか確認

### コマンドが応答しない場合

1. Telloとの距離が近すぎる場合があります（最低1m離れる）
2. バッテリー残量が少ない場合は一部のコマンドが無効になります
3. 前のコマンドが完了するまで待ってから次のコマンドを送信

## 📚 参考資料

- [DJI Tello SDK 2.0 User Guide](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)
- [Tello SDK Commands](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)

## 🤝 貢献

バグ報告や機能追加の提案は、GitHubのIssueまでお願いします。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 