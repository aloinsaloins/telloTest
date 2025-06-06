#!/usr/bin/env node
import { mastra } from './mastra/index';

async function main() {
  const args = process.argv.slice(2);
  const userInput = args.join(' ') || 'ドローンのステータスを確認して';

  console.log('🤖 Tello自然言語制御システム（永続接続対応）');
  console.log('================================================');
  console.log(`📝 入力: "${userInput}"`);
  console.log('🔄 処理中...\n');

  try {
    // Telloエージェントを取得
    const agent = mastra.getAgent('telloAgent');
    
    if (!agent) {
      console.error('❌ Telloエージェントが見つかりません');
      return;
    }

    // 自然言語の指示をエージェントに送信
    const response = await agent.generate([
      {
        role: 'user',
        content: userInput,
      },
    ]);

    console.log('🤖 エージェントの応答:');
    console.log('========================');
    console.log(response.text);
    
    if (response.toolCalls && response.toolCalls.length > 0) {
      console.log('\n🔧 実行されたツール:');
      response.toolCalls.forEach((toolCall, index) => {
        console.log(`${index + 1}. ${toolCall.toolName}`);
        if (toolCall.args && Object.keys(toolCall.args).length > 0) {
          console.log(`   引数: ${JSON.stringify(toolCall.args, null, 2)}`);
        }
      });
    }

  } catch (error) {
    console.error('❌ エラーが発生しました:', error);
  }
}

// コマンドライン引数の例を表示
if (process.argv.length === 2) {
  console.log('\n📖 使用例（永続接続システム）:');
  console.log('=====================================');
  console.log('\n🔗 接続管理:');
  console.log('tsx src/tello-natural-language.ts "ドローンに接続して"');
  console.log('tsx src/tello-natural-language.ts "接続状態を確認して"');
  console.log('tsx src/tello-natural-language.ts "ドローンから切断して"');
  
  console.log('\n✈️ 基本操作（自動接続）:');
  console.log('tsx src/tello-natural-language.ts "ドローンを離陸させて"');
  console.log('tsx src/tello-natural-language.ts "前に100cm進んで"');
  console.log('tsx src/tello-natural-language.ts "右に90度回転して"');
  console.log('tsx src/tello-natural-language.ts "上に50cm上がって"');
  console.log('tsx src/tello-natural-language.ts "着陸して"');
  
  console.log('\n🔋 ステータス確認:');
  console.log('tsx src/tello-natural-language.ts "バッテリー残量を確認して"');
  console.log('tsx src/tello-natural-language.ts "ドローンの状態を教えて"');
  
  console.log('\n🚨 緊急時:');
  console.log('tsx src/tello-natural-language.ts "緊急停止"');
  console.log('tsx src/tello-natural-language.ts "すぐに止めて"');
  
  console.log('\n💡 特徴:');
  console.log('- 一度接続すると、他のコマンドで自動的に接続を再利用');
  console.log('- 接続が切れた場合は自動的に再接続を試行');
  console.log('- 明示的に切断するまで接続状態を維持');
  console.log('- 自然言語で直感的にドローンを制御可能');
  console.log('\n');
}

main().catch(console.error); 