import { createTool } from "@mastra/core";
import { z } from "zod";

// 永続的なTello接続マネージャーを実行するヘルパー関数
async function executeTelloManager(action: string, options: { command?: string; distance?: number; degrees?: number } = {}): Promise<any> {
  try {
    let url = '';
    let method = 'GET';
    let body: any = null;

    // アクションに応じてAPIエンドポイントを決定
    switch (action) {
      case 'connect':
        url = 'http://localhost:8080/api/connect';
        method = 'POST';
        break;
      case 'disconnect':
        url = 'http://localhost:8080/api/disconnect';
        method = 'POST';
        break;
      case 'status':
        url = 'http://localhost:8080/api/status';
        method = 'GET';
        break;
      case 'reset_status':
        url = 'http://localhost:8080/api/reset_status';
        method = 'POST';
        break;
      case 'start_video':
        url = 'http://localhost:8080/api/video/start';
        method = 'POST';
        break;
      case 'stop_video':
        url = 'http://localhost:8080/api/video/stop';
        method = 'POST';
        break;
      case 'get_video_frame':
        url = 'http://localhost:8080/api/video/frame';
        method = 'GET';
        break;
      case 'execute':
        if (options.command === 'takeoff') {
          url = 'http://localhost:8080/api/takeoff';
          method = 'POST';
        } else if (options.command === 'land') {
          url = 'http://localhost:8080/api/land';
          method = 'POST';
        } else if (options.command === 'emergency') {
          url = 'http://localhost:8080/api/emergency';
          method = 'POST';
        } else if (['up', 'down', 'left', 'right', 'forward', 'back'].includes(options.command || '')) {
          url = 'http://localhost:8080/api/move';
          method = 'POST';
          body = {
            direction: options.command,
            distance: options.distance
          };
        } else if (['cw', 'ccw'].includes(options.command || '')) {
          url = 'http://localhost:8080/api/rotate';
          method = 'POST';
          body = {
            direction: options.command,
            degrees: options.degrees
          };
        }
        break;
      default:
        throw new Error(`Unknown action: ${action}`);
    }

    // HTTPリクエストを送信
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;

  } catch (error) {
    console.error('executeTelloManager error:', error);
    throw error;
  }
}

// Tello接続ツール（永続接続対応）
export const telloConnectTool = createTool({
  id: "tello_connect",
  description: "Telloドローンに接続します（永続接続）",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      battery: z.number().optional(),
      connected: z.boolean(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('connect');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `接続エラー: ${error instanceof Error ? error.message : String(error)}`,
        data: { connected: false }
      };
    }
  },
});

// Tello切断ツール
export const telloDisconnectTool = createTool({
  id: "tello_disconnect",
  description: "Telloドローンから切断します",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      connected: z.boolean(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('disconnect');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `切断エラー: ${error instanceof Error ? error.message : String(error)}`,
        data: { connected: false }
      };
    }
  },
});

// Tello離陸ツール（自動接続対応）
export const telloTakeoffTool = createTool({
  id: "tello_takeoff",
  description: "Telloドローンを離陸させます（必要に応じて自動接続）",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      battery: z.number().optional(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('execute', { command: 'takeoff' });
      return result;
    } catch (error) {
      return {
        success: false,
        message: `離陸エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Tello着陸ツール（自動接続対応）
export const telloLandTool = createTool({
  id: "tello_land",
  description: "Telloドローンを着陸させます（必要に応じて自動接続）",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('execute', { command: 'land' });
      return result;
    } catch (error) {
      return {
        success: false,
        message: `着陸エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Tello移動ツール（自動接続対応）
export const telloMoveTool = createTool({
  id: "tello_move",
  description: "Telloドローンを指定した方向に移動させます（必要に応じて自動接続）",
  inputSchema: z.object({
    direction: z.enum(["up", "down", "left", "right", "forward", "back"]),
    distance: z.number().min(20).max(500),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async ({ context }) => {
    try {
      const { direction, distance } = context;
      const result = await executeTelloManager('execute', { 
        command: direction, 
        distance 
      });
      return result;
    } catch (error) {
      return {
        success: false,
        message: `移動エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Tello回転ツール（自動接続対応）
export const telloRotateTool = createTool({
  id: "tello_rotate",
  description: "Telloドローンを指定した角度で回転させます（必要に応じて自動接続）",
  inputSchema: z.object({
    direction: z.enum(["clockwise", "counter_clockwise"]),
    degrees: z.number().min(1).max(360),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async ({ context }) => {
    try {
      const { direction, degrees } = context;
      const command = direction === "clockwise" ? "cw" : "ccw";
      const result = await executeTelloManager('execute', { 
        command, 
        degrees 
      });
      return result;
    } catch (error) {
      return {
        success: false,
        message: `回転エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Telloステータス確認ツール（接続状態も含む）
export const telloStatusTool = createTool({
  id: "tello_status",
  description: "Telloドローンのステータス（接続状態、バッテリー残量など）を確認します",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      battery: z.number(),
      connected: z.boolean(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('status');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `ステータス確認エラー: ${error instanceof Error ? error.message : String(error)}`,
        data: { battery: 0, connected: false }
      };
    }
  },
});

// Tello状態リセットツール（デバッグ用）
export const telloResetStatusTool = createTool({
  id: "tello_reset_status",
  description: "Telloドローンの飛行状態をリセットします（「飛行中」エラーが発生した場合のデバッグ用）",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      old_status: z.string().optional(),
      new_status: z.string().optional(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('reset_status');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `状態リセットエラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Tello緊急停止ツール（自動接続対応）
export const telloEmergencyTool = createTool({
  id: "tello_emergency",
  description: "Telloドローンを緊急停止させます（必要に応じて自動接続）",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('execute', { command: 'emergency' });
      return result;
    } catch (error) {
      return {
        success: false,
        message: `緊急停止エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Telloビデオストリーミング開始ツール
export const telloStartVideoTool = createTool({
  id: "tello_start_video",
  description: "Telloドローンのビデオストリーミングを開始します。カメラ映像をリアルタイムで配信開始します",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('start_video');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `ビデオストリーミング開始エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Telloビデオストリーミング停止ツール
export const telloStopVideoTool = createTool({
  id: "tello_stop_video",
  description: "Telloドローンのビデオストリーミングを停止します。カメラ映像の配信を終了します",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('stop_video');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `ビデオストリーミング停止エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// Telloビデオフレーム取得ツール
export const telloGetVideoFrameTool = createTool({
  id: "tello_get_video_frame",
  description: "Telloドローンの現在のビデオフレーム（静止画）を取得します。ビデオストリーミングが開始されている必要があります",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    message: z.string(),
    data: z.object({
      frame_base64: z.string().optional(),
      timestamp: z.string().optional(),
    }).optional(),
  }),
  execute: async () => {
    try {
      const result = await executeTelloManager('get_video_frame');
      return result;
    } catch (error) {
      return {
        success: false,
        message: `ビデオフレーム取得エラー: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
});

// 全ツールをエクスポート
export const telloTools = [
  telloConnectTool,
  telloDisconnectTool,
  telloTakeoffTool,
  telloLandTool,
  telloMoveTool,
  telloRotateTool,
  telloStatusTool,
  telloResetStatusTool,
  telloEmergencyTool,
  telloStartVideoTool,
  telloStopVideoTool,
  telloGetVideoFrameTool,
]; 