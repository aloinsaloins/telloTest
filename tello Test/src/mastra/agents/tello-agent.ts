import { Agent } from '@mastra/core/agent';
import { createTool } from '@mastra/core/tools';
import { google } from '@ai-sdk/google';
import { z } from 'zod';

// Telloツールを作成
const connectTello = createTool({
  id: 'connect_tello',
  description: 'Telloドローンに接続します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/connect', { method: 'POST' });
    return await response.json();
  }
});

const disconnectTello = createTool({
  id: 'disconnect_tello',
  description: 'Telloドローンから切断します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/disconnect', { method: 'POST' });
    return await response.json();
  }
});

const getTelloStatus = createTool({
  id: 'get_tello_status',
  description: 'Telloドローンの状態を取得します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/status');
    return await response.json();
  }
});

const getBattery = createTool({
  id: 'get_battery',
  description: 'Telloドローンのバッテリー残量を取得します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/battery');
    return await response.json();
  }
});

const takeoff = createTool({
  id: 'takeoff',
  description: 'Telloドローンを離陸させます',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/takeoff', { method: 'POST' });
    return await response.json();
  }
});

const land = createTool({
  id: 'land',
  description: 'Telloドローンを着陸させます',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/land', { method: 'POST' });
    return await response.json();
  }
});

const emergencyStop = createTool({
  id: 'emergency_stop',
  description: 'Telloドローンを緊急停止させます',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/emergency', { method: 'POST' });
    return await response.json();
  }
});

const moveDrone = createTool({
  id: 'move_drone',
  description: 'Telloドローンを指定した方向に移動させます',
  inputSchema: z.object({
    direction: z.enum(['up', 'down', 'left', 'right', 'forward', 'back']),
    distance: z.number().min(20).max(500)
  }),
  execute: async ({ context }) => {
    const response = await fetch('/api/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction: context.direction, distance: context.distance })
    });
    return await response.json();
  }
});

const rotateDrone = createTool({
  id: 'rotate_drone',
  description: 'Telloドローンを指定した方向に回転させます',
  inputSchema: z.object({
    direction: z.enum(['cw', 'ccw']),
    degrees: z.number().min(1).max(360)
  }),
  execute: async ({ context }) => {
    const response = await fetch('/api/rotate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction: context.direction, degrees: context.degrees })
    });
    return await response.json();
  }
});

const startVideoStream = createTool({
  id: 'start_video_stream',
  description: 'Telloドローンのビデオストリーミングを開始します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/video/start', { method: 'POST' });
    return await response.json();
  }
});

const stopVideoStream = createTool({
  id: 'stop_video_stream',
  description: 'Telloドローンのビデオストリーミングを停止します',
  inputSchema: z.object({}),
  execute: async () => {
    const response = await fetch('/api/video/stop', { method: 'POST' });
    return await response.json();
  }
});

export const telloAgent = new Agent({
  name: 'TelloAgent',
  instructions: `
あなたはDJI Telloドローンを制御するAIアシスタントです。

主な機能:
- ドローンの接続・切断
- 離陸・着陸
- 移動（前後左右上下）
- 回転（時計回り・反時計回り）
- バッテリー残量確認
- ビデオストリーミング制御
- 緊急停止

安全に関する重要な注意事項:
1. 離陸前に必ずバッテリー残量を確認してください（推奨: 30%以上）
2. 屋内での飛行時は障害物に注意してください
3. 緊急時は即座に緊急停止を実行してください
4. 移動距離は20-500cmの範囲で指定してください
5. 回転角度は1-360度の範囲で指定してください

ユーザーの指示に従って、安全にドローンを制御してください。
`,
  model: google('gemini-1.5-flash'),
  tools: {
    connectTello,
    disconnectTello,
    getTelloStatus,
    getBattery,
    takeoff,
    land,
    emergencyStop,
    moveDrone,
    rotateDrone,
    startVideoStream,
    stopVideoStream
  }
}); 