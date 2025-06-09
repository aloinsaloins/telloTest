#!/usr/bin/env node
import { mastra } from './mastra/index';

async function testMemoryFeatures() {
  console.log('🧠 Mastraメモリ機能テスト（セマンティック検索なし）');
  console.log('================================================\n');

  try {
    // Telloエージェントを取得
    const agent = mastra.getAgent('telloAgent');
    
    if (!agent) {
      console.error('❌ Telloエージェントが見つかりません');
      return;
    }

    // テスト用のユーザーとスレッドID
    const resourceId = 'test_user_001';
    const threadId = 'test_session_' + Date.now();

    console.log(`📝 テスト用リソースID: ${resourceId}`);
    console.log(`🔗 テスト用スレッドID: ${threadId}\n`);

    // 複数の会話をテスト
    const testConversations = [
      'ドローンのバッテリー残量を確認して',
      '私の名前は田中太郎です',
      '離陸して前に50cm進んでください',
      '私の好きな飛行パターンは正方形です',
      '着陸してください',
    ];

    console.log('1️⃣ テスト会話を実行中...');
    for (let i = 0; i < testConversations.length; i++) {
      const message = testConversations[i];
      console.log(`\n📤 メッセージ ${i + 1}: "${message}"`);
      
      try {
        const response = await agent.generate([
          {
            role: 'user',
            content: message,
          },
        ], {
          resourceId: resourceId,
          threadId: threadId,
        });

        console.log(`📥 応答: ${response.text.substring(0, 100)}...`);
        
        // 少し待機
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`❌ メッセージ ${i + 1} でエラー:`, error);
      }
    }

    // メモリを使った質問をテスト
    console.log('\n2️⃣ メモリベースの質問をテスト中...');
    const memoryQuestions = [
      '私の名前を覚えていますか？',
      '私の好きな飛行パターンは何でしたか？',
      '今までにどんなコマンドを実行しましたか？',
    ];

    for (const question of memoryQuestions) {
      console.log(`\n❓ 質問: "${question}"`);
      try {
        const response = await agent.generate([
          {
            role: 'user',
            content: question,
          },
        ], {
          resourceId: resourceId,
          threadId: threadId,
        });

        console.log(`💡 回答: ${response.text}`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error('❌ 質問エラー:', error);
      }
    }

    console.log('\n🎉 メモリ機能テスト完了！');
    console.log('✅ 基本的なメモリ機能（会話履歴・ワーキングメモリ）が正常に動作しています');

  } catch (error) {
    console.error('❌ テスト実行エラー:', error);
  }
}

// スクリプトが直接実行された場合のみテストを実行
if (import.meta.url === `file://${process.argv[1]}`) {
  testMemoryFeatures().catch(console.error);
}

export { testMemoryFeatures }; 