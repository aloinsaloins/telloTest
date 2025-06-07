import { Tool } from '@mastra/core/tools';
import { z } from 'zod';

// Tello Web APIのベースURL（実際のサーバーのIPアドレスに変更してください）
const TELLO_API_BASE_URL = 'http://localhost:8080';

/**
 * Telloドローンに接続するツール
 */
export const telloConnect = new Tool({
  id: 'tello_connect',
  description: 'DJI Telloドローンに接続します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: `Telloに接続しました。バッテリー残量: ${result.battery}%`,
          data: result,
        };
      } else {
        return {
          success: false,
          message: `接続に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `接続エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンから切断するツール
 */
export const telloDisconnect = new Tool({
  id: 'tello_disconnect',
  description: 'DJI Telloドローンから切断します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      return {
        success: result.success,
        message: result.success
          ? 'Telloから切断しました'
          : `切断に失敗しました: ${result.message}`,
        data: result,
      };
    } catch (error) {
      return {
        success: false,
        message: `切断エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンの状態を取得するツール
 */
export const telloGetStatus = new Tool({
  id: 'tello_get_status',
  description: 'DJI Telloドローンの現在の状態（接続状況、飛行状態、バッテリー残量など）を取得します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/status`);
      const result = await response.json();
      
      const statusMessage = `
接続状態: ${result.connected ? '接続中' : '切断中'}
飛行状態: ${result.flight_status === 'flying' ? '飛行中' : result.flight_status === 'landed' ? '着陸中' : '緊急停止'}
バッテリー残量: ${result.battery}%
      `.trim();
      
      return {
        success: true,
        message: statusMessage,
        data: result,
      };
    } catch (error) {
      return {
        success: false,
        message: `状態取得エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンを離陸させるツール
 */
export const telloTakeoff = new Tool({
  id: 'tello_takeoff',
  description: 'DJI Telloドローンを離陸させます',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/takeoff`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: 'Telloが離陸しました！',
          data: result,
        };
      } else {
        return {
          success: false,
          message: `離陸に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `離陸エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンを着陸させるツール
 */
export const telloLand = new Tool({
  id: 'tello_land',
  description: 'DJI Telloドローンを着陸させます',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/land`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: 'Telloが着陸しました',
          data: result,
        };
      } else {
        return {
          success: false,
          message: `着陸に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `着陸エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンを緊急停止させるツール
 */
export const telloEmergency = new Tool({
  id: 'tello_emergency',
  description: 'DJI Telloドローンを緊急停止させます（危険な状況でのみ使用）',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/emergency`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      return {
        success: true,
        message: 'Telloを緊急停止しました',
        data: result,
      };
    } catch (error) {
      return {
        success: false,
        message: `緊急停止エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンを移動させるツール
 */
export const telloMove = new Tool({
  id: 'tello_move',
  description: 'DJI Telloドローンを指定した方向に指定した距離だけ移動させます',
  inputSchema: z.object({
    direction: z.enum(['up', 'down', 'left', 'right', 'forward', 'back']).describe('移動方向（up: 上昇, down: 下降, left: 左, right: 右, forward: 前進, back: 後退）'),
    distance: z.number().min(20).max(500).describe('移動距離（センチメートル、20-500の範囲）'),
  }),
  execute: async ({ context }) => {
    try {
      const { direction, distance } = context;
      const response = await fetch(`${TELLO_API_BASE_URL}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          direction,
          distance,
        }),
      });
      // …
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: `Telloが${direction}に${distance}cm移動しました`,
          data: result,
        };
      } else {
        return {
          success: false,
          message: `移動に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `移動エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンを回転させるツール
 */
export const telloRotate = new Tool({
  id: 'tello_rotate',
  description: 'DJI Telloドローンを指定した方向に指定した角度だけ回転させます',
  inputSchema: z.object({
    direction: z.enum(['cw', 'ccw']).describe('回転方向（cw: 時計回り, ccw: 反時計回り）'),
    degrees: z.number().min(1).max(360).describe('回転角度（度、1-360の範囲）'),
  }),
  execute: async ({ context }) => {
    try {
      const { direction, degrees } = context;
      const response = await fetch(`${TELLO_API_BASE_URL}/rotate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          direction,
          degrees,
        }),
      });
      
      const result = await response.json();
      
      if (result.success) {
        const directionText = direction === 'cw' ? '時計回り' : '反時計回り';
        return {
          success: true,
          message: `Telloが${directionText}に${degrees}度回転しました`,
          data: result,
        };
      } else {
        return {
          success: false,
          message: `回転に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `回転エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンのバッテリー残量を取得するツール
 */
export const telloGetBattery = new Tool({
  id: 'tello_get_battery',
  description: 'DJI Telloドローンのバッテリー残量を取得します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/battery`);
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: `バッテリー残量: ${result.battery}%`,
          data: result,
        };
      } else {
        return {
          success: false,
          message: `バッテリー情報の取得に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `バッテリー情報取得エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンのビデオストリーミングを開始するツール
 */
export const telloStartVideoStream = new Tool({
  id: 'tello_start_video_stream',
  description: 'DJI Telloドローンのビデオストリーミングを開始します。カメラ映像をリアルタイムで配信開始します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/video/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: 'Telloのビデオストリーミングを開始しました。カメラ映像の配信が始まりました',
          data: result,
        };
      } else {
        return {
          success: false,
          message: `ビデオストリーミング開始に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `ビデオストリーミング開始エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンのビデオストリーミングを停止するツール
 */
export const telloStopVideoStream = new Tool({
  id: 'tello_stop_video_stream',
  description: 'DJI Telloドローンのビデオストリーミングを停止します。カメラ映像の配信を終了します',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/video/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: 'Telloのビデオストリーミングを停止しました。カメラ映像の配信が終了しました',
          data: result,
        };
      } else {
        return {
          success: false,
          message: `ビデオストリーミング停止に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `ビデオストリーミング停止エラー: ${error}`,
        data: null,
      };
    }
  },
});

/**
 * Telloドローンの現在のビデオフレームを取得するツール
 */
export const telloGetVideoFrame = new Tool({
  id: 'tello_get_video_frame',
  description: 'DJI Telloドローンの現在のビデオフレーム（静止画）を取得します。ビデオストリーミングが開始されている必要があります',
  inputSchema: z.object({}),
  execute: async () => {
    try {
      const response = await fetch(`${TELLO_API_BASE_URL}/video/frame`);
      const result = await response.json();
      
      if (result.success) {
        return {
          success: true,
          message: 'ビデオフレームを取得しました',
          data: result,
        };
      } else {
        return {
          success: false,
          message: `ビデオフレーム取得に失敗しました: ${result.message}`,
          data: result,
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `ビデオフレーム取得エラー: ${error}`,
        data: null,
      };
    }
  },
});

// すべてのTelloツールをエクスポート
export const telloTools = [
  telloConnect,
  telloDisconnect,
  telloGetStatus,
  telloTakeoff,
  telloLand,
  telloEmergency,
  telloMove,
  telloRotate,
  telloGetBattery,
  telloStartVideoStream,
  telloStopVideoStream,
  telloGetVideoFrame,
]; 