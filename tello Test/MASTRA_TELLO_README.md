# 🤖 Mastra AI + DJI Tello 自然言語制御システム

このプロジェクトは、Mastra AIフレームワークを使用してDJI Telloドローンを自然言語で制御するシステムです。

## ✨ 特徴

- **自然言語制御**: 「ドローンを離陸させて」「前に100cm進んで」などの自然な日本語でドローンを操作
- **AI エージェント**: Google Gemini 1.5 Proを使用した高度な言語理解
- **安全機能**: バッテリー残量チェック、緊急停止、移動制限などの安全機能
- **リアルタイム制御**: Pythonバックエンドとの連携によるリアルタイムドローン制御

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

### 基本的な使用方法

```bash
# 自然言語でTelloを制御
npm run tello:ai "ドローンを離陸させて"
npm run tello:ai "前に100cm進んで"
npm run tello:ai "右に90度回転して"
npm run tello:ai "着陸して"
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

## 🔧 システム構成

### ファイル構成

```
src/
├── mastra/
│   ├── agents/
│   │   └── tello-agent.ts      # Tello制御エージェント
│   ├── tools/
│   │   └── tello-tools.ts      # Telloツール定義
│   └── index.ts                # Mastra設定
├── tello-natural-language.ts   # 自然言語制御メイン
└── test-tello.ts              # テスト用ファイル

# Python バックエンド
tello_connection.py             # Tello接続ライブラリ
tello_example.py               # 使用例
requirements.txt               # Python依存関係
```

### アーキテクチャ

```
自然言語入力 → Mastra AI Agent → Tello Tools → Python Backend → DJI Tello
```

1. **自然言語入力**: ユーザーが日本語でコマンドを入力
2. **Mastra AI Agent**: Google Gemini 1.5 Proがコマンドを解析し、適切なツールを選択
3. **Tello Tools**: TypeScriptツールがPythonスクリプトを実行
4. **Python Backend**: Tello接続ライブラリがドローンと通信
5. **DJI Tello**: 実際のドローン制御

## 🛡️ 安全機能

- **バッテリーチェック**: 離陸前に自動でバッテリー残量を確認
- **移動制限**: 移動距離を20-500cmに制限
- **回転制限**: 回転角度を1-360度に制限
- **緊急停止**: 危険な状況での即座の停止機能
- **接続確認**: コマンド実行前の接続状態確認

## 🔍 トラブルシューティング

### よくある問題

1. **「Telloに接続できません」**
   - TelloのWi-Fiネットワークに接続されているか確認
   - Telloドローンの電源が入っているか確認

2. **「Gemini APIエラー」**
   - `.env`ファイルのAPIキーが正しく設定されているか確認
   - APIキーの使用制限に達していないか確認

3. **「Pythonスクリプトエラー」**
   - Python依存関係がインストールされているか確認
   - `pip install -r requirements.txt`を実行

### デバッグモード

```bash
# 詳細なログ出力
DEBUG=1 npm run tello:ai "ドローンのステータスを確認して"
```

## 📚 開発者向け情報

### 新しいツールの追加

`src/mastra/tools/tello-tools.ts`に新しいツールを追加できます：

```typescript
export const newTelloTool = createTool({
  id: "new_tello_command",
  description: "新しいTelloコマンドの説明",
  inputSchema: z.object({
    // パラメータ定義
  }),
  outputSchema: z.object({
    // 出力定義
  }),
  execute: async (params) => {
    // 実装
  },
});
```

### エージェントの設定変更

`src/mastra/agents/tello-agent.ts`でエージェントの動作を調整できます。

## 🤝 貢献

バグ報告や機能追加の提案は、GitHubのIssueまでお願いします。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🙏 謝辞

- [Mastra AI](https://mastra.ai/) - AIエージェントフレームワーク
- [DJI Tello](https://www.ryzerobotics.com/tello) - ドローンハードウェア
- [Google Gemini](https://ai.google.dev/) - Gemini 1.5 Pro言語モデル 