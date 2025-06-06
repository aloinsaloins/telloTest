import { createTool } from "@mastra/core";
import { z } from "zod";
import { spawn } from "child_process";

// 永続的なTello接続マネージャーを実行するヘルパー関数
async function executeTelloManager(action: string, options: { command?: string; distance?: number; degrees?: number } = {}): Promise<any> {
  return new Promise((resolve, reject) => {
    const args = ['src/tello_connection_manager.py', action];
    
    if (options.command) {
      args.push('--command', options.command);
    }
    
    if (options.distance !== undefined) {
      args.push('--distance', options.distance.toString());
    }
    
    if (options.degrees !== undefined) {
      args.push('--degrees', options.degrees.toString());
    }

    const pythonProcess = spawn('python', args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          // 出力の最後の行（JSON部分）のみを取得
          const lines = output.trim().split('\n');
          const jsonLine = lines[lines.length - 1];
          const result = JSON.parse(jsonLine);
          resolve(result);
        } catch (parseError) {
          reject(new Error(`JSON parse error: ${output}`));
        }
      } else {
        reject(new Error(`Python Manager failed: ${error}`));
      }
    });
  });
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

// 全ツールをエクスポート
export const telloTools = [
  telloConnectTool,
  telloDisconnectTool,
  telloTakeoffTool,
  telloLandTool,
  telloMoveTool,
  telloRotateTool,
  telloStatusTool,
  telloEmergencyTool,
]; 