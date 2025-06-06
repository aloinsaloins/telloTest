# Tello永続接続システム

DJI Telloドローンとの永続的な接続を管理し、自然言語でドローンを制御できるシステムです。

## 🚀 新機能

### 永続接続管理
- **一度接続すると接続状態を維持**: 複数のコマンドで接続を再利用
- **自動接続**: 他のコマンド実行時に自動的に接続確認・再接続
- **効率的な制御**: 毎回新しい接続を作成する必要がなくなりました

### 自然言語制御
- **直感的な操作**: 日本語で自然にドローンを制御
- **安全性重視**: バッテリー残量チェックと安全ガイドライン
- **包括的な機能**: 接続管理から緊急停止まで全ての操作に対応

## 📋 必要な環境

- Python 3.7+
- Node.js 18+
- DJI Tello ドローン
- 必要なPythonパッケージ: `opencv-python`, `numpy`

## 🔧 セットアップ

1. **依存関係のインストール**:
```bash
# Python依存関係
pip install -r requirements.txt

# Node.js依存関係
npm install
```

2. **Telloドローンの準備**:
   - Telloドローンの電源を入れる
   - Wi-FiでTelloのネットワーク（TELLO-XXXXXX）に接続

## 🎮 使用方法

### 基本的な使用方法

```bash
# 自然言語でドローンを制御
tsx src/tello-natural-language.ts "ドローンに接続して"
tsx src/tello-natural-language.ts "ドローンを離陸させて"
tsx src/tello-natural-language.ts "前に100cm進んで"
tsx src/tello-natural-language.ts "着陸して"
```

### 接続管理コマンド

```bash
# 接続
tsx src/tello-natural-language.ts "ドローンに接続して"
tsx src/tello-natural-language.ts "Telloと接続を確立して"

# 接続状態確認
tsx src/tello-natural-language.ts "接続状態を確認して"
tsx src/tello-natural-language.ts "ドローンの状態を教えて"
tsx src/tello-natural-language.ts "バッテリー残量を確認して"

# 切断
tsx src/tello-natural-language.ts "ドローンから切断して"
tsx src/tello-natural-language.ts "接続を終了して"
```

### 飛行制御コマンド（自動接続対応）

```bash
# 離陸・着陸
tsx src/tello-natural-language.ts "ドローンを離陸させて"
tsx src/tello-natural-language.ts "着陸して"

# 移動（20-500cm）
tsx src/tello-natural-language.ts "前に100cm進んで"
tsx src/tello-natural-language.ts "後ろに50cm下がって"
tsx src/tello-natural-language.ts "左に80cm移動して"
tsx src/tello-natural-language.ts "右に120cm移動して"
tsx src/tello-natural-language.ts "上に60cm上がって"
tsx src/tello-natural-language.ts "下に40cm下がって"

# 回転（1-360度）
tsx src/tello-natural-language.ts "右に90度回転して"
tsx src/tello-natural-language.ts "左に180度回転して"
tsx src/tello-natural-language.ts "時計回りに45度回転して"

# 緊急停止
tsx src/tello-natural-language.ts "緊急停止"
tsx src/tello-natural-language.ts "すぐに止めて"
```

## 🔄 システム構成

### 1. 永続接続マネージャー (`tello_connection_manager.py`)
- シングルトンパターンで接続状態を管理
- 自動接続・再接続機能
- 安全な切断処理

### 2. Mastraツール (`src/mastra/tools/tello-tools.ts`)
- 永続接続マネージャーとの連携
- 自動接続対応の各種操作ツール
- JSON形式での結果返却

### 3. Telloエージェント (`src/mastra/agents/tello-agent.ts`)
- 自然言語の理解と解釈
- 安全性チェック
- 適切なツールの選択と実行

### 4. 自然言語インターフェース (`src/tello-natural-language.ts`)
- コマンドライン入力の処理
- エージェントとの連携
- 結果の表示

## 🛡️ 安全機能

- **バッテリー残量チェック**: 離陸前に20%以上の残量を確認
- **移動距離制限**: 20-500cmの範囲内で制限
- **回転角度制限**: 1-360度の範囲内で制限
- **緊急停止機能**: いつでも即座に停止可能
- **自動切断**: プログラム終了時の安全な切断

## 🔍 トラブルシューティング

### 接続できない場合
1. Telloドローンの電源が入っているか確認
2. Wi-FiでTelloのネットワークに接続されているか確認
3. 他のTello制御アプリが動作していないか確認

### コマンドが実行されない場合
1. 接続状態を確認: `tsx src/tello-natural-language.ts "接続状態を確認して"`
2. バッテリー残量を確認: `tsx src/tello-natural-language.ts "バッテリー残量を確認して"`
3. 必要に応じて再接続: `tsx src/tello-natural-language.ts "ドローンに接続して"`

### エラーが発生した場合
1. 緊急停止: `tsx src/tello-natural-language.ts "緊急停止"`
2. 切断して再接続: 
   ```bash
   tsx src/tello-natural-language.ts "切断して"
   tsx src/tello-natural-language.ts "接続して"
   ```

## 📝 使用例

### 基本的な飛行シーケンス
```bash
# 1. 接続確立
tsx src/tello-natural-language.ts "ドローンに接続して"

# 2. ステータス確認
tsx src/tello-natural-language.ts "バッテリー残量を確認して"

# 3. 離陸
tsx src/tello-natural-language.ts "ドローンを離陸させて"

# 4. 簡単な飛行
tsx src/tello-natural-language.ts "前に100cm進んで"
tsx src/tello-natural-language.ts "右に90度回転して"
tsx src/tello-natural-language.ts "上に50cm上がって"

# 5. 着陸
tsx src/tello-natural-language.ts "着陸して"

# 6. 切断（オプション）
tsx src/tello-natural-language.ts "切断して"
```

## 🎯 利点

1. **効率性**: 永続接続により接続時間を短縮
2. **使いやすさ**: 自然言語での直感的な制御
3. **安全性**: 包括的な安全チェック機能
4. **信頼性**: 自動再接続とエラーハンドリング
5. **拡張性**: 新しいコマンドの追加が容易

このシステムにより、Telloドローンを自然言語で効率的かつ安全に制御できるようになりました。 