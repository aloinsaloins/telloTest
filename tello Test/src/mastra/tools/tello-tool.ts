import { createTool } from '@mastra/core';
import { z } from 'zod';
import Tello from 'tello-drone';

// Telloドローンのインスタンス
let tello: any = null;

// Telloに接続
const connectTello = async () => {
  if (!tello) {
    tello = new Tello();
    await tello.connect();
    console.log('Telloに接続しました');
  }
  return tello;
};

// 基本的な飛行コマンドツール
export const telloBasicCommands = createTool({
  id: 'tello-basic-commands',
  inputSchema: z.object({
    command: z.enum(['takeoff', 'land', 'emergency']).describe('基本コマンド: takeoff(離陸), land(着陸), emergency(緊急停止)'),
  }),
  description: 'Telloドローンの基本的な飛行コマンドを実行します',
  execute: async ({ context }) => {
    const { command } = context;
    try {
      const drone = await connectTello();
      
      switch (command) {
        case 'takeoff':
          await drone.takeoff();
          return { success: true, message: 'ドローンが離陸しました' };
        case 'land':
          await drone.land();
          return { success: true, message: 'ドローンが着陸しました' };
        case 'emergency':
          await drone.emergency();
          return { success: true, message: '緊急停止を実行しました' };
        default:
          return { success: false, message: '不明なコマンドです' };
      }
    } catch (error) {
      return { success: false, message: `エラーが発生しました: ${error}` };
    }
  },
});

// 移動コマンドツール
export const telloMovementCommands = createTool({
  id: 'tello-movement-commands',
  inputSchema: z.object({
    direction: z.enum(['forward', 'backward', 'left', 'right', 'up', 'down']).describe('移動方向'),
    distance: z.number().min(20).max(500).describe('移動距離（cm）20-500の範囲'),
  }),
  description: 'Telloドローンを指定した方向に移動させます',
  execute: async ({ context }) => {
    const { direction, distance } = context;
    try {
      const drone = await connectTello();
      
      switch (direction) {
        case 'forward':
          await drone.forward(distance);
          break;
        case 'backward':
          await drone.backward(distance);
          break;
        case 'left':
          await drone.left(distance);
          break;
        case 'right':
          await drone.right(distance);
          break;
        case 'up':
          await drone.up(distance);
          break;
        case 'down':
          await drone.down(distance);
          break;
      }
      
      return { success: true, message: `${direction}方向に${distance}cm移動しました` };
    } catch (error) {
      return { success: false, message: `移動エラー: ${error}` };
    }
  },
});

// 回転コマンドツール
export const telloRotationCommands = createTool({
  id: 'tello-rotation-commands',
  inputSchema: z.object({
    direction: z.enum(['clockwise', 'counterclockwise']).describe('回転方向: clockwise(時計回り), counterclockwise(反時計回り)'),
    degrees: z.number().min(1).max(360).describe('回転角度（度）1-360の範囲'),
  }),
  description: 'Telloドローンを指定した角度で回転させます',
  execute: async ({ context }) => {
    const { direction, degrees } = context;
    try {
      const drone = await connectTello();
      
      if (direction === 'clockwise') {
        await drone.clockwise(degrees);
      } else {
        await drone.counterClockwise(degrees);
      }
      
      return { success: true, message: `${direction}方向に${degrees}度回転しました` };
    } catch (error) {
      return { success: false, message: `回転エラー: ${error}` };
    }
  },
});

// フリップコマンドツール
export const telloFlipCommands = createTool({
  id: 'tello-flip-commands',
  inputSchema: z.object({
    direction: z.enum(['forward', 'backward', 'left', 'right']).describe('フリップ方向'),
  }),
  description: 'Telloドローンを指定した方向にフリップさせます',
  execute: async ({ context }) => {
    const { direction } = context;
    try {
      const drone = await connectTello();
      
      switch (direction) {
        case 'forward':
          await drone.flip('f');
          break;
        case 'backward':
          await drone.flip('b');
          break;
        case 'left':
          await drone.flip('l');
          break;
        case 'right':
          await drone.flip('r');
          break;
      }
      
      return { success: true, message: `${direction}方向にフリップしました` };
    } catch (error) {
      return { success: false, message: `フリップエラー: ${error}` };
    }
  },
});

// ステータス取得ツール
export const telloStatusTool = createTool({
  id: 'tello-status',
  inputSchema: z.object({}),
  description: 'Telloドローンの現在のステータスを取得します',
  execute: async ({ context }) => {
    try {
      const drone = await connectTello();
      const battery = await drone.getBattery();
      const speed = await drone.getSpeed();
      const time = await drone.getTime();
      
      return {
        success: true,
        status: {
          battery: `${battery}%`,
          speed: `${speed}cm/s`,
          flightTime: `${time}秒`,
        },
        message: `バッテリー: ${battery}%, 速度: ${speed}cm/s, 飛行時間: ${time}秒`
      };
    } catch (error) {
      return { success: false, message: `ステータス取得エラー: ${error}` };
    }
  },
});

// 接続終了ツール
export const telloDisconnect = createTool({
  id: 'tello-disconnect',
  inputSchema: z.object({}),
  description: 'Telloドローンとの接続を終了します',
  execute: async ({ context }) => {
    try {
      if (tello) {
        await tello.disconnect();
        tello = null;
        return { success: true, message: 'Telloとの接続を終了しました' };
      }
      return { success: true, message: 'Telloは既に切断されています' };
    } catch (error) {
      return { success: false, message: `切断エラー: ${error}` };
    }
  },
}); 