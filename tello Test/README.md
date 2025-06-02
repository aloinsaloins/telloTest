# DJI Tello 自然言語制御システム

このプロジェクトは、MastraとAIを使用してDJI Telloドローンを自然言語で制御するシステムです。

## 🚁 機能

- **自然言語制御**: 日本語でドローンに指示を出せます
- **安全機能**: 緊急停止、バッテリー監視、安全な移動範囲制限
- **豊富なコマンド**: 離陸、着陸、移動、回転、フリップなど
- **リアルタイムステータス**: バッテリー残量、速度、飛行時間の確認

## 📋 必要なもの

- DJI Telloドローン
- Node.js 20.9.0以上
- Google Generative AI APIキー
- WiFi接続（TelloのWiFiネットワークに接続）

## 🛠️ セットアップ

### 1. 依存関係のインストール

```bash
pnpm install
```

### 2. 環境変数の設定

`.env`ファイルを作成し、Google Generative AI APIキーを設定：

```bash
GOOGLE_GENERATIVE_AI_API_KEY=your_google_api_key_here
```

### 3. Telloドローンの準備

1. Telloドローンの電源を入れる
2. コンピューターをTelloのWiFiネットワーク（TELLO-XXXXXX）に接続
3. ドローンが安全な環境にあることを確認

## 🎮 使用方法

### 基本的な使用方法

```bash
# 単一コマンドの実行
npx tsx src/test-tello.ts "ドローンのステータスを確認して"

# 複数のコマンドを順次実行
npx tsx src/test-tello.ts

# package.jsonのスクリプトを使用
pnpm run tello:status
pnpm run tello:takeoff
pnpm run tello:land
```

### 利用可能なコマンド例

#### 基本操作
- `"ドローンを離陸させて"`
- `"着陸して"`
- `"緊急停止"`
- `"ドローンのステータスを確認して"`

#### 移動コマンド
- `"前に50cm進んで"`
- `"後ろに30cm下がって"`
- `"左に40cm移動して"`
- `"右に60cm移動して"`
- `"上に20cm上昇して"`
- `"下に25cm下降して"`

#### 回転コマンド
- `"右に90度回転して"`
- `"左に45度回転して"`
- `"時計回りに180度回転して"`

#### フリップコマンド
- `"前フリップして"`
- `"後ろフリップして"`
- `"左フリップして"`
- `"右フリップして"`

## 🔧 開発

### プロジェクト構造

```
src/
├── mastra/
│   ├── agents/
│   │   ├── tello-agent.ts    # Tello制御AIエージェント
│   │   └── weather-agent.ts  # 既存の天気エージェント
│   ├── tools/
│   │   ├── tello-tool.ts     # Tello制御ツール
│   │   └── weather-tool.ts   # 既存の天気ツール
│   └── index.ts              # Mastra設定
├── test-tello.ts             # テストスクリプト
└── ...
```

### カスタムコマンドの追加

新しいTelloコマンドを追加するには：

1. `src/mastra/tools/tello-tool.ts`に新しいツールを追加
2. `src/mastra/agents/tello-agent.ts`のinstructionsを更新
3. 新しいツールをエージェントのtoolsに追加

## ⚠️ 安全に関する注意事項

### 必須の安全対策
- **広いスペース**: 障害物のない3m×3m以上のスペースで使用
- **バッテリー確認**: 飛行前にバッテリー残量を確認
- **緊急停止**: 問題が発生した場合は即座に緊急停止コマンドを使用
- **屋内飛行**: 初回は屋内の安全な環境でテスト

### 制限事項
- 移動距離: 20-500cm
- 回転角度: 1-360度
- 最大飛行時間: 約13分（バッテリー依存）

## 🐛 トラブルシューティング

### よくある問題

#### 1. ドローンに接続できない
```
解決方法:
- TelloのWiFiネットワークに接続されているか確認
- ドローンの電源が入っているか確認
- 他のアプリケーションがTelloを使用していないか確認
```

#### 2. コマンドが実行されない
```
解決方法:
- Google Generative AI APIキーが正しく設定されているか確認
- ドローンのバッテリー残量を確認
- ドローンが平らな場所にあるか確認
```

#### 3. 応答が遅い
```
解決方法:
- WiFi接続の安定性を確認
- Google AI APIの応答時間を確認
- 複数のコマンドを同時に送信していないか確認
```

## 📚 API リファレンス

### Telloツール

- `telloBasicCommands`: 離陸、着陸、緊急停止
- `telloMovementCommands`: 6方向の移動
- `telloRotationCommands`: 時計回り・反時計回りの回転
- `telloFlipCommands`: 4方向のフリップ
- `telloStatusTool`: ステータス情報の取得
- `telloDisconnect`: 接続の終了

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。新機能の提案や改善案がありましたら、お気軽にお知らせください。

## 📄 ライセンス

ISC License

## 🙏 謝辞

- [Mastra](https://mastra.ai/) - AIエージェントフレームワーク
- [tello-drone](https://www.npmjs.com/package/tello-drone) - Tello制御ライブラリ
- [Google Generative AI](https://ai.google.dev/) - Gemini API 