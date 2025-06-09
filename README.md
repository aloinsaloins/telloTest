# 🤖 Mastra AI + DJI Tello 自然言語制御システム

[![Node.js Version](https://img.shields.io/badge/node-%3E%3D20.9.0-brightgreen)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-ISC-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-blue)](https://www.typescriptlang.org/)
[![Mastra](https://img.shields.io/badge/Mastra-0.10.3-purple)](https://mastra.ai/)

DJI Telloドローンを自然言語で制御するAIシステム。Mastra AIフレームワークとGoogle Gemini 1.5 Proを使用し、**メモリ機能**により過去の会話や操作履歴を記憶して、より自然で文脈を理解した対話を実現します。

## ✨ 主な特徴

### 🗣️ 自然言語制御
- **直感的な操作**: 「ドローンを離陸させて」「前に100cm進んで」などの日本語でドローンを操作
- **高度な言語理解**: Google Gemini 1.5 Proによる文脈を理解した自然言語処理
- **包括的なコマンド**: 基本操作から複合操作まで幅広く対応

### 🧠 AI エージェント & メモリ機能
- **Mastra AIフレームワーク**: 最新のAIエージェント技術を活用
- **永続メモリ**: 会話履歴、ユーザー情報、操作パターンを記憶
- **ワーキングメモリ**: ユーザーの好みや設定を継続的に記憶
- **学習機能**: 使用パターンから最適な制御方法を学習

### 🌐 統合インターフェース
- **AG-UIプロトコル**: ドローン制御とAIチャットを一つの画面に統合
- **リアルタイム映像**: ライブビデオストリーミング表示
- **リアルタイム通信**: 非同期イベント処理による応答性の高いUI
- **永続接続管理**: 効率的な接続の再利用とメンテナンス

### 🛡️ 安全機能
- **バッテリー監視**: 残量チェック、緊急停止、移動制限
- **自動安全チェック**: 離陸前の包括的な安全確認
- **緊急停止**: 即座のモーター停止機能
- **自動再接続**: 接続失敗時の自動復旧機能

## 🏗️ システム構成

```
┌─────────────────────────────────────────────────────────────┐
│            React Web Frontend (Port 3000)                  │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │  Video Stream   │  │        AI Chat Interface        │   │
│  │  Component      │  │      (Natural Language)        │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API (/api/copilotkit)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          Python Web Server (Port 8080)                     │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │  Tello Control  │  │     Video Streaming             │   │
│  │  (Persistent)   │  │     (OpenCV + Base64)          │   │
│  │                 │  │                                 │   │
│  │  + API Proxy    │  │     + CORS Handler              │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              │ HTTP API      │ UDP/WiFi      │
              ▼               ▼               │
┌─────────────────────────────────────────────▼─────────────────┐
│           Mastra Server (Port 4111)      DJI Tello Drone     │
│  ┌─────────────────────────────────┐    ┌─────────────────┐   │
│  │  Tello Agent                    │    │    Hardware     │   │
│  │  (Gemini + Memory + Tools)      │    │    Control      │   │
│  │  - 自然言語理解・メモリ機能       │    │                 │   │
│  │  - 安全チェック・学習機能        │    │                 │   │
│  │  - ツール実行・永続接続管理       │    │                 │   │
│  └─────────────────────────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 クイックスタート

### 前提条件

- **Node.js**: v20.9.0以上
- **Python**: 3.7以上
- **DJI Tello**: 充電済みで電源ON
- **Google Gemini API キー**: [こちらから取得](https://ai.google.dev/)

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

1. **Telloドローンの電源を入れる**
2. **WiFi設定**: PCのWi-FiでTELLO-XXXXXXネットワークに接続
3. **接続確認**: `ping 192.168.10.1`でTelloとの通信を確認
4. **安全な飛行環境を確保**

### 使用方法

#### 方法1: コマンドライン（基本）

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

#### 方法2: Webインターフェース（推奨）

```bash
# ターミナル1: Mastra開発サーバー（AIエージェント）
npm run dev

# ターミナル2: Python Webサーバー（Tello制御 + API統合）
python tello_web_server.py

# ターミナル3: React Webアプリケーション（フロントエンド）
npm run web:dev

# ブラウザで http://localhost:3000 にアクセス
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

### 接続管理
- 「ドローンに接続して」
- 「接続状態を確認して」
- 「ドローンから切断して」

### 基本操作
- 「ドローンを離陸させて」
- 「着陸して」
- 「緊急停止して」
- 「ステータスを確認して」
- 「バッテリー残量を教えて」

### 移動操作
- 「前に[距離]cm進んで」（20-500cm）
- 「後ろに[距離]cm下がって」
- 「左に[距離]cm移動して」
- 「右に[距離]cm移動して」
- 「上に[距離]cm上がって」
- 「下に[距離]cm下がって」

### 回転操作
- 「右に[角度]度回転して」（1-360度）
- 「左に[角度]度回転して」
- 「時計回りに[角度]度回って」
- 「反時計回りに[角度]度回って」

### フリップ操作
- 「前フリップして」
- 「後ろフリップして」
- 「左フリップして」
- 「右フリップして」

### 映像制御
- 「ビデオストリーミングを開始して」
- 「映像を停止して」

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
├── tello-natural-language.ts # 自然言語制御メイン
├── test-tello.ts             # テストスクリプト
└── ...

# Python Backend
tello_connection.py             # Tello接続ライブラリ
tello_connection_manager.py     # 永続接続管理
tello_web_server.py            # Webサーバーインターフェース
requirements.txt               # Python依存関係
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

### API仕様

#### Tello制御API

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/connect` | POST | Telloに接続 |
| `/api/disconnect` | POST | Telloから切断 |
| `/api/status` | GET | ドローン状態取得 |
| `/api/battery` | GET | バッテリー残量取得 |
| `/api/takeoff` | POST | 離陸 |
| `/api/land` | POST | 着陸 |
| `/api/emergency` | POST | 緊急停止 |
| `/api/move` | POST | 移動（方向・距離指定） |
| `/api/rotate` | POST | 回転（方向・角度指定） |
| `/api/video/start` | POST | ビデオストリーミング開始 |
| `/api/video/stop` | POST | ビデオストリーミング停止 |
| `/api/video/frame` | GET | 最新フレーム取得 |

#### AG-UI API

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/copilotkit` | POST | Mastraエージェントとの通信 |

## ⚠️ 安全に関する注意事項

### 必須の安全対策
- **広いスペース**: 障害物のない3m×3m以上のスペースで使用
- **バッテリー確認**: 飛行前にバッテリー残量を確認（30%以上推奨）
- **緊急停止**: 問題が発生した場合は即座に緊急停止コマンドを使用
- **屋内飛行**: 初回は屋内の安全な環境でテスト
- **法的遵守**: 航空法等の関連法規を遵守

### 制限事項
- **移動距離**: 20-500cm
- **回転角度**: 1-360度
- **最大飛行時間**: 約13分（バッテリー依存）
- **環境条件**: 屋内または風の少ない屋外環境

### 自動安全機能
- **バッテリー監視**: 30%未満で離陸警告
- **接続監視**: 自動再接続機能
- **タイムアウト処理**: コマンド失敗時の自動復旧
- **緊急停止**: 即座のモーター停止機能

## 🐛 トラブルシューティング

<details>
<summary>ドローンに接続できない</summary>

**解決方法**:
- TelloのWiFiネットワーク（TELLO-XXXXXX）に接続されているか確認
- ドローンの電源が入っているか確認
- `ping 192.168.10.1`で通信確認
- 他のTello制御アプリが動作していないか確認
- ファイアウォールがUDPポート8889, 9000, 11111をブロックしていないか確認
</details>

<details>
<summary>コマンドが実行されない</summary>

**解決方法**:
- Google Generative AI APIキーが正しく設定されているか確認
- ドローンのバッテリー残量を確認（30%以上推奨）
- ドローンが平らな場所にあるか確認
- 接続状態を確認: `npm run tello:ai "接続状態を確認して"`
</details>

<details>
<summary>ビデオが表示されない</summary>

**解決方法**:
- OpenCVが正しくインストールされているか確認
- ストリーミングが開始されているか確認
- UDPポート11111が利用可能か確認
- ブラウザのコンソールでエラーを確認
</details>

<details>
<summary>応答が遅い</summary>

**解決方法**:
- WiFi接続の安定性を確認
- Google AI APIの応答時間を確認
- 複数のコマンドを同時に送信していないか確認
- Telloとの距離が適切か確認（1-3m推奨）
</details>

### ログの確認

```bash
# Python サーバーログ
tail -f tello_web_server.log

# ブラウザコンソール
F12 → Console タブ

# デバッグモード
DEBUG=1 npm run tello:ai "ドローンのステータスを確認して"
```

## 📚 技術スタック

- **AI Framework**: [Mastra](https://mastra.ai/) v0.10.3
- **AI Model**: Google Gemini 1.5 Pro
- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + aiohttp + asyncio
- **Drone SDK**: [tello-drone](https://www.npmjs.com/package/tello-drone) v3.0.6
- **Memory**: LibSQL with @mastra/memory
- **Language**: TypeScript 5.8.3
- **Runtime**: Node.js 20.9.0+

## 🎯 特徴的な機能

### 永続接続管理
- **効率的な接続**: 一度接続すると接続状態を維持
- **自動再接続**: 接続失敗時の自動復旧
- **リソース最適化**: 不要な接続作成を回避

### AG-UIプロトコルの利点
- **統一されたUX**: ドローン制御とAIチャットが一つの画面に統合
- **リアルタイム性**: エージェントからの即座のレスポンス
- **拡張性**: 新しいツールや機能の簡単な追加
- **安全性**: エージェントレベルでの安全チェック

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発時の注意事項

- 新しいツールを追加する場合は`src/mastra/tools/tello-tool.ts`を更新
- エージェントの動作を変更する場合は`src/mastra/agents/tello-agent.ts`を更新
- 安全性を最優先に考慮した実装を心がける

## 📄 ライセンス

このプロジェクトはISCライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- [Mastra](https://mastra.ai/) - AIエージェントフレームワーク
- [tello-drone](https://www.npmjs.com/package/tello-drone) - Tello制御ライブラリ
- [Google Generative AI](https://ai.google.dev/) - Gemini API
- [DJI Tello](https://www.ryzerobotics.com/tello) - ドローンハードウェア

---

⭐ このプロジェクトが役に立った場合は、スターを付けていただけると嬉しいです！ 