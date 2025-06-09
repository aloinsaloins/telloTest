import { telloAgent } from '../mastra/agents/tello-agent';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { messages, threadId, resourceId } = body;

    // エージェントでメッセージを処理
    const result = await telloAgent.generate(messages, {
      threadId,
      resourceId,
      maxSteps: 10,
      temperature: 0.1
    });

    return new Response(JSON.stringify({
      success: true,
      text: result.text,
      toolCalls: result.toolCalls || []
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    });

  } catch (error) {
    console.error('CopilotKit API error:', error);
    
    return new Response(JSON.stringify({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}

export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
} 