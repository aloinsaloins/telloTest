# 🤖 Mastra AI + DJI Tello 自然言語制御システム（メモリ機能付き）

このプロジェクトは、Mastra AIフレームワークを使用してDJI Telloドローンを自然言語で制御するシステムです。**メモリ機能**により、過去の会話や操作履歴を記憶し、より自然で文脈を理解した対話が可能です。

## ✨ 特徴

- **自然言語制御**: 「ドローンを離陸させて」「前に100cm進んで」などの自然な日本語でドローンを操作
- **AI エージェント**: Google Gemini 1.5 Proを使用した高度な言語理解
- **メモリ機能**: 会話履歴、ユーザー情報、操作パターンを記憶
- **ワーキングメモリ**: ユーザーの好みや設定を継続的に記憶
- **安全機能**: バッテリー残量チェック、緊急停止、移動制限などの安全機能
- **リアルタイム制御**: Pythonバックエンドとの連携によるリアルタイムドローン制御

## 🧠 メモリ機能

### 記憶される情報
- **ユーザー情報**: 名前、好み、過去の操作履歴
- **Telloドローン情報**: バッテリー残量、飛行時間、よく使用するコマンド
- **会話履歴**: 過去20件の最近のメッセージ
- **安全設定**: ユーザーの安全に関する設定や注意事項

### メモリ設定
```typescript
memory: new Memory({
  storage: new LibSQLStore({
    url: 'file:../mastra.db',
  }),
  options: {
    lastMessages: 20, // 最近のメッセージ数
    workingMemory: {
      enabled: true, // ワーキングメモリ有効
    },
  },
})
```

## 🚀 セットアップ

### 1. 環境要件

- Node.js 20.9.0以上
- Python 3.7以上
- DJI Telloドローン
- Google Gemini API キー

### 2. インストール

```bash
# 依存関係のインストール
npm install

# Python依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env`ファイルにGoogle Gemini APIキーを設定してください：

```bash
GOOGLE_GENERATIVE_AI_API_KEY=your-gemini-api-key-here
```

### 4. Telloドローンとの接続

1. Telloドローンの電源を入れる
2. PCのWi-FiでTELLO-XXXXXXネットワークに接続

## 🎮 使用方法

### 基本的な使用方法（メモリ機能付き）

```bash
# 自然言語でTelloを制御（メモリ機能付き）
npm run tello:ai "ドローンを離陸させて"
npm run tello:ai "前に100cm進んで"
npm run tello:ai "右に90度回転して"
npm run tello:ai "着陸して"

# メモリ機能をテスト
npm run memory:test
```

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
npm run tello:ai "前回のバッテリー残量はどのくらいでしたか？"
```

### 定義済みコマンド

```bash
# ステータス確認
npm run tello:ai:status

# 離陸
npm run tello:ai:takeoff

# 着陸
npm run tello:ai:land

# 前進
npm run tello:ai:forward

# 回転
npm run tello:ai:rotate
```

### カスタムコマンド

```bash
# 任意の自然言語コマンド
npm run tello:ai "上に50cm上がって"
npm run tello:ai "左に30度回転して"
npm run tello:ai "後ろに200cm下がって"
npm run tello:ai "緊急停止して"
```

## 🧠 対応可能な自然言語コマンド

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

### メモリ関連操作
- 「私の名前は[名前]です」
- 「私の好きな[設定]は[値]です」
- 「私の名前を覚えていますか？」
- 「前回の[情報]を教えて」
- 「今までの操作履歴を教えて」

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