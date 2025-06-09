import { mastra } from './mastra/index';

async function testTelloAgent() {
  console.log('🚁 Tello制御エージェントのテストを開始します...\n');

  try {
    // Telloエージェントを取得
    const telloAgent = mastra.getAgent('telloAgent');
    
    if (!telloAgent) {
      console.error('❌ Telloエージェントが見つかりません');
      return;
    }

    // テストコマンド例
    const testCommands = [
      'ドローンのステータスを確認して',
      'ドローンを離陸させて',
      '前に50cm進んで',
      '右に90度回転して',
      '上に30cm上昇して',
      '着陸して',
    ];

    console.log('📝 テストコマンド:');
    testCommands.forEach((cmd, i) => {
      console.log(`${i + 1}. ${cmd}`);
    });
    console.log('\n');

    // 各コマンドを順番に実行（実際のテストでは1つずつ実行することを推奨）
    for (let i = 0; i < testCommands.length; i++) {
      const command = testCommands[i];
      console.log(`\n🎯 実行中: "${command}"`);
      console.log('─'.repeat(50));
      
      try {
        const response = await telloAgent.generate(command);
        console.log('✅ 応答:', response.text);
        
        // 安全のため、各コマンド間に少し待機
        if (i < testCommands.length - 1) {
          console.log('⏳ 3秒待機中...');
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
      } catch (error) {
        console.error('❌ エラー:', error);
      }
    }

  } catch (error) {
    console.error('❌ テスト実行エラー:', error);
  }
}

// 単一コマンドテスト用の関数
async function testSingleCommand(command: string) {
  console.log(`🚁 単一コマンドテスト: "${command}"\n`);
  
  try {
    const telloAgent = mastra.getAgent('telloAgent');
    
    if (!telloAgent) {
      console.error('❌ Telloエージェントが見つかりません');
      return;
    }

    const response = await telloAgent.generate(command);
    console.log('✅ 応答:', response.text);
    
  } catch (error) {
    console.error('❌ エラー:', error);
  }
}

// メイン実行部分
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length > 0) {
    // コマンドライン引数がある場合は単一コマンドテスト
    const command = args.join(' ');
    await testSingleCommand(command);
  } else {
    // 引数がない場合は全体テスト
    console.log('⚠️  注意: このテストは実際のTelloドローンに接続を試みます。');
    console.log('⚠️  ドローンが接続されていない場合はエラーが発生します。');
    console.log('⚠️  安全な環境で実行してください。\n');
    
    // 確認プロンプト（実際の使用時はコメントアウトを外してください）
    // const readline = require('readline');
    // const rl = readline.createInterface({
    //   input: process.stdin,
    //   output: process.stdout
    // });
    // 
    // const answer = await new Promise(resolve => {
    //   rl.question('続行しますか？ (y/N): ', resolve);
    // });
    // rl.close();
    // 
    // if (answer !== 'y' && answer !== 'Y') {
    //   console.log('テストをキャンセルしました。');
    //   return;
    // }
    
    await testTelloAgent();
  }
}

// 使用例をコメントで記載
/*
使用方法:

1. 全体テスト実行:
   npx tsx src/test-tello.ts

2. 単一コマンドテスト:
   npx tsx src/test-tello.ts "ドローンのステータスを確認して"
   npx tsx src/test-tello.ts "離陸して"
   npx tsx src/test-tello.ts "前に100cm進んで"
   npx tsx src/test-tello.ts "着陸して"

注意事項:
- 実際のTelloドローンが必要です
- 安全な環境で実行してください
- バッテリー残量を確認してから実行してください
- 障害物のない広いスペースで実行してください
*/

// メイン関数を実行
main().catch(console.error); 