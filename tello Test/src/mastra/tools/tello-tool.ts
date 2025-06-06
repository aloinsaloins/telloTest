import { createTool } from '@mastra/core';
import { z } from 'zod';
import Tello from 'tello-drone';

// Telloドローンのインスタンス
let tello: any = null;
let isConnected = false;

// より包括的なログ抑制機能
const suppressLogs = () => {
  const originalLog = console.log;
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalInfo = console.info;
  const originalDebug = console.debug;
  
  // 標準出力も抑制
  const originalStdoutWrite = process.stdout.write;
  const originalStderrWrite = process.stderr.write;
  
  console.log = () => {};
  console.error = () => {};
  console.warn = () => {};
  console.info = () => {};
  console.debug = () => {};
  
  // stdout/stderrの書き込みも抑制
  process.stdout.write = () => true;
  process.stderr.write = () => true;
  
  return () => {
    console.log = originalLog;
    console.error = originalError;
    console.warn = originalWarn;
    console.info = originalInfo;
    console.debug = originalDebug;
    process.stdout.write = originalStdoutWrite;
    process.stderr.write = originalStderrWrite;
  };
};

// Telloに接続
const connectTello = async () => {
  if (!tello || !isConnected) {
    const restoreLogs = suppressLogs();
    try {
      tello = new Tello();
      
      // 接続処理
      await tello.connect();
      isConnected = true;
      
      // 接続確認のため簡単なコマンドを送信
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1秒待機
      
      restoreLogs();
      console.log('Telloに接続しました');
      
    } catch (error) {
      restoreLogs();
      console.error('Tello接続エラー:', error);
      isConnected = false;
      throw error;
    }
  }
  return tello;
};

// 安全にコマンドを実行するヘルパー関数
const executeCommand = async (commandFn: () => Promise<any>, commandName: string) => {
  const restoreLogs = suppressLogs();
  try {
    const result = await commandFn();
    restoreLogs();
    return { success: true, result };
  } catch (error) {
    restoreLogs();
    console.error(`${commandName}エラー:`, error);
    // 接続が切れた場合はフラグをリセット
    const errorStr = error instanceof Error ? error.message : String(error);
    if (errorStr.includes('connection') || errorStr.includes('timeout')) {
      isConnected = false;
      tello = null;
    }
    throw error;
  }
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
      
      let result;
      switch (command) {
        case 'takeoff':
          result = await executeCommand(() => drone.takeoff(), '離陸');
          return { success: true, message: 'ドローンが離陸しました' };
        case 'land':
          result = await executeCommand(() => drone.land(), '着陸');
          return { success: true, message: 'ドローンが着陸しました' };
        case 'emergency':
          result = await executeCommand(() => drone.emergency(), '緊急停止');
          return { success: true, message: '緊急停止を実行しました' };
        default:
          return { success: false, message: '不明なコマンドです' };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { success: false, message: `エラーが発生しました: ${errorMessage}` };
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
      
      const commandMap = {
        'forward': () => drone.forward(distance),
        'backward': () => drone.backward(distance),
        'left': () => drone.left(distance),
        'right': () => drone.right(distance),
        'up': () => drone.up(distance),
        'down': () => drone.down(distance),
      };
      
      await executeCommand(commandMap[direction], `${direction}移動`);
      return { success: true, message: `${direction}方向に${distance}cm移動しました` };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { success: false, message: `移動エラー: ${errorMessage}` };
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
      
      const commandFn = direction === 'clockwise' 
        ? () => drone.clockwise(degrees)
        : () => drone.counterClockwise(degrees);
      
      await executeCommand(commandFn, `${direction}回転`);
      return { success: true, message: `${direction}方向に${degrees}度回転しました` };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { success: false, message: `回転エラー: ${errorMessage}` };
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
      
      const flipMap = {
        'forward': 'f',
        'backward': 'b',
        'left': 'l',
        'right': 'r',
      };
      
      await executeCommand(() => drone.flip(flipMap[direction]), `${direction}フリップ`);
      return { success: true, message: `${direction}方向にフリップしました` };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { success: false, message: `フリップエラー: ${errorMessage}` };
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
      
      // 各ステータスを個別に取得し、エラーハンドリングを行う
      let battery, speed, time;
      
      try {
        const batteryResult = await executeCommand(() => drone.getBattery(), 'バッテリー取得');
        battery = batteryResult.result;
      } catch (error) {
        battery = 'N/A';
      }
      
      try {
        const speedResult = await executeCommand(() => drone.getSpeed(), '速度取得');
        speed = speedResult.result;
      } catch (error) {
        speed = 'N/A';
      }
      
      try {
        const timeResult = await executeCommand(() => drone.getTime(), '飛行時間取得');
        time = timeResult.result;
      } catch (error) {
        time = 'N/A';
      }
      
      return {
        success: true,
        status: {
          battery: battery !== 'N/A' ? `${battery}%` : battery,
          speed: speed !== 'N/A' ? `${speed}cm/s` : speed,
          flightTime: time !== 'N/A' ? `${time}秒` : time,
          connected: isConnected,
        },
        message: `バッテリー: ${battery !== 'N/A' ? battery + '%' : battery}, 速度: ${speed !== 'N/A' ? speed + 'cm/s' : speed}, 飛行時間: ${time !== 'N/A' ? time + '秒' : time}`
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { 
        success: false, 
        message: `ステータス取得エラー: ${errorMessage}`,
        status: { connected: false }
      };
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
      if (tello && isConnected) {
        const restoreLogs = suppressLogs();
        try {
          await tello.disconnect();
          restoreLogs();
        } catch (error) {
          restoreLogs();
          throw error;
        }
        tello = null;
        isConnected = false;
        return { success: true, message: 'Telloとの接続を終了しました' };
      }
      return { success: true, message: 'Telloは既に切断されています' };
    } catch (error) {
      // エラーが発生してもフラグはリセット
      tello = null;
      isConnected = false;
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { success: false, message: `切断エラー: ${errorMessage}` };
    }
  },
}); 