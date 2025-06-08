# 🤖 Mastra AI + DJI Tello 自然言語制御システム

[![Node.js Version](https://img.shields.io/badge/node-%3E%3D20.9.0-brightgreen)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-ISC-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-blue)](https://www.typescriptlang.org/)
[![Mastra](https://img.shields.io/badge/Mastra-0.10.3-purple)](https://mastra.ai/)

DJI Telloドローンを自然言語で制御するAIシステム。Mastra AIフレームワークとGoogle Gemini 1.5 Proを使用し、**メモリ機能**により過去の会話や操作履歴を記憶して、より自然で文脈を理解した対話を実現します。

## ✨ 主な特徴

- 🗣️ **自然言語制御**: 「ドローンを離陸させて」「前に100cm進んで」などの日本語でドローンを操作
- 🧠 **AI エージェント**: Google Gemini 1.5 Proによる高度な言語理解
- 💾 **メモリ機能**: 会話履歴、ユーザー情報、操作パターンを記憶
- 🔄 **ワーキングメモリ**: ユーザーの好みや設定を継続的に記憶
- 🛡️ **安全機能**: バッテリー残量チェック、緊急停止、移動制限
- ⚡ **リアルタイム制御**: Pythonバックエンドとの連携によるリアルタイムドローン制御

## 🎥 デモ

<!-- スクリーンショットやGIFを追加予定 -->
```bash
# 自然言語でのドローン制御例
npm run tello:ai "ドローンを離陸させて"
npm run tello:ai "前に100cm進んで、右に90度回転して"
npm run tello:ai "着陸して"
```

## 🚀 クイックスタート

### 前提条件

- Node.js 20.9.0以上
- Python 3.7以上
- DJI Telloドローン
- Google Gemini API キー

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-username/tello-test.git
cd tello-test

# 依存関係のインストール
npm install
pip install -r requirements.txt

# 環境変数の設定
echo "GOOGLE_GENERATIVE_AI_API_KEY=your-gemini-api-key-here" > .env
```

### Telloドローンとの接続

1. Telloドローンの電源を入れる
2. PCのWi-FiでTELLO-XXXXXXネットワークに接続
3. 安全な飛行環境を確保

### 基本的な使用方法

```bash
# ステータス確認
npm run tello:ai:status

# 離陸
npm run tello:ai:takeoff

# 自然言語コマンド
npm run tello:ai "前に50cm進んで、右に90度回転して"

# 着陸
npm run tello:ai:land
```

## 🧠 メモリ機能

### 記憶される情報
- **ユーザー情報**: 名前、好み、過去の操作履歴
- **Telloドローン情報**: バッテリー残量、飛行時間、よく使用するコマンド
- **会話履歴**: 過去20件の最近のメッセージ
- **安全設定**: ユーザーの安全に関する設定や注意事項

### メモリ機能の活用例

```bash
# ユーザー情報を記憶
npm run tello:ai "私の名前は田中太郎です"
npm run tello:ai "私の好きな飛行パターンは正方形です"

# 後で記憶した情報を参照
npm run tello:ai "私の名前を覚えていますか？"
npm run tello:ai "私の好きな飛行パターンで飛行してください"

# 過去の操作履歴を参照
npm run tello:ai "今までにどんなコマンドを実行しましたか？"
```

## 🎮 対応コマンド

### 基本操作
- 「ドローンを離陸させて」
- 「着陸して」
- 「緊急停止して」
- 「ステータスを確認して」
- 「バッテリー残量を教えて」

### 移動操作
- 「前に[距離]cm進んで」
- 「後ろに[距離]cm下がって」
- 「左に[距離]cm移動して」
- 「右に[距離]cm移動して」
- 「上に[距離]cm上がって」
- 「下に[距離]cm下がって」

### 回転操作
- 「右に[角度]度回転して」
- 「左に[角度]度回転して」
- 「時計回りに[角度]度回って」
- 「反時計回りに[角度]度回って」

### フリップ操作
- 「前フリップして」
- 「後ろフリップして」
- 「左フリップして」
- 「右フリップして」

## 🛠️ 開発

### プロジェクト構造

```
src/
├── mastra/
│   ├── agents/
│   │   └── tello-agent.ts    # Tello制御AIエージェント
│   ├── tools/
│   │   └── tello-tool.ts     # Tello制御ツール
│   └── index.ts              # Mastra設定
├── test-tello.ts             # テストスクリプト
├── tello-natural-language.ts # 自然言語制御メイン
└── ...
```

### 利用可能なスクリプト

```bash
# 開発サーバー起動
npm run dev

# Telloテスト
npm run tello:test

# 定義済みコマンド
npm run tello:ai:status    # ステータス確認
npm run tello:ai:takeoff   # 離陸
npm run tello:ai:land      # 着陸
npm run tello:ai:forward   # 前進
npm run tello:ai:rotate    # 回転

# メモリ機能テスト
npm run memory:test

# Webインターフェース
npm run web:dev
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

<details>
<summary>ドローンに接続できない</summary>

- TelloのWiFiネットワークに接続されているか確認
- ドローンの電源が入っているか確認
- 他のアプリケーションがTelloを使用していないか確認
</details>

<details>
<summary>コマンドが実行されない</summary>

- Google Generative AI APIキーが正しく設定されているか確認
- ドローンのバッテリー残量を確認
- ドローンが平らな場所にあるか確認
</details>

<details>
<summary>応答が遅い</summary>

- WiFi接続の安定性を確認
- Google AI APIの応答時間を確認
- 複数のコマンドを同時に送信していないか確認
</details>

## 📚 技術スタック

- **AI Framework**: [Mastra](https://mastra.ai/) v0.10.3
- **AI Model**: Google Gemini 1.5 Pro
- **Drone SDK**: [tello-drone](https://www.npmjs.com/package/tello-drone) v3.0.6
- **Memory**: LibSQL with @mastra/memory
- **Language**: TypeScript 5.8.3
- **Runtime**: Node.js 20.9.0+

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはISCライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- [Mastra](https://mastra.ai/) - AIエージェントフレームワーク
- [tello-drone](https://www.npmjs.com/package/tello-drone) - Tello制御ライブラリ
- [Google Generative AI](https://ai.google.dev/) - Gemini API

---

⭐ このプロジェクトが役に立った場合は、スターを付けていただけると嬉しいです！ 