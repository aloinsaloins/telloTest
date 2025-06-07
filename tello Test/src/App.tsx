import React, { useState, useEffect } from 'react';
import { TelloVideoStream } from './components/TelloVideoStream';
import { AGUIChat } from './components/AGUIChat';

interface TelloStatus {
  connected: boolean;
  flight_status: string;
  battery: number;
}

function App() {
  const [isVideoStreaming, setIsVideoStreaming] = useState(false);
  const [telloStatus, setTelloStatus] = useState<TelloStatus>({
    connected: false,
    flight_status: 'landed',
    battery: 0
  });
  const [isConnecting, setIsConnecting] = useState(false);

  // Telloの状態を定期的に更新
  useEffect(() => {
    const updateStatus = async () => {
      try {
        const response = await fetch('/api/status');
        const data = await response.json();
        if (data.success) {
          setTelloStatus({
            connected: data.connected,
            flight_status: data.flight_status,
            battery: data.battery
          });
        }
      } catch (error) {
        console.error('Status update error:', error);
      }
    };

    // 初回実行
    updateStatus();
    
    // 5秒間隔で状態を更新
    const interval = setInterval(updateStatus, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const response = await fetch('/api/connect', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        setTelloStatus(prev => ({ ...prev, connected: true, battery: data.battery }));
      } else {
        alert(`接続に失敗しました: ${data.message}`);
      }
    } catch (error) {
      alert('接続中にエラーが発生しました');
      console.error('Connection error:', error);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/disconnect', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        setTelloStatus(prev => ({ ...prev, connected: false }));
        setIsVideoStreaming(false);
      }
    } catch (error) {
      console.error('Disconnect error:', error);
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 50) return '#4CAF50';
    if (battery > 20) return '#FF9800';
    return '#f44336';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flying': return '#2196F3';
      case 'landed': return '#4CAF50';
      case 'emergency': return '#f44336';
      default: return '#757575';
    }
  };

  return (
    <div className="app">
        <header className="app-header">
          <h1>🚁 Tello AI Controller</h1>
          <p>AG-UIプロトコルを使用したTelloドローン制御システム</p>
        </header>

        <div className="main-content">
          {/* 左側: ドローン制御パネル */}
          <div className="control-panel">
            {/* 接続状態 */}
            <div className="status-card">
              <h3>ドローン状態</h3>
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-label">接続状態:</span>
                  <span className={`status-value ${telloStatus.connected ? 'connected' : 'disconnected'}`}>
                    {telloStatus.connected ? '✅ 接続中' : '❌ 未接続'}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">飛行状態:</span>
                  <span 
                    className="status-value"
                    style={{ color: getStatusColor(telloStatus.flight_status) }}
                  >
                    {telloStatus.flight_status === 'flying' ? '🛫 飛行中' : 
                     telloStatus.flight_status === 'landed' ? '🛬 着陸中' : 
                     telloStatus.flight_status === 'emergency' ? '🚨 緊急停止' : '❓ 不明'}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">バッテリー:</span>
                  <span 
                    className="status-value"
                    style={{ color: getBatteryColor(telloStatus.battery) }}
                  >
                    🔋 {telloStatus.battery}%
                  </span>
                </div>
              </div>
              
              <div className="connection-controls">
                {!telloStatus.connected ? (
                  <button 
                    onClick={handleConnect}
                    disabled={isConnecting}
                    className="connect-btn"
                  >
                    {isConnecting ? '接続中...' : 'Telloに接続'}
                  </button>
                ) : (
                  <button 
                    onClick={handleDisconnect}
                    className="disconnect-btn"
                  >
                    切断
                  </button>
                )}
              </div>
            </div>

            {/* ビデオストリーミング */}
            <TelloVideoStream 
              isStreaming={isVideoStreaming}
              onStreamToggle={setIsVideoStreaming}
            />

            {/* 安全注意事項 */}
            <div className="safety-card">
              <h3>⚠️ 安全注意事項</h3>
              <ul>
                <li>離陸前にバッテリー残量を確認してください（推奨: 30%以上）</li>
                <li>屋内での飛行時は障害物に注意してください</li>
                <li>緊急時は即座に「緊急停止」を実行してください</li>
                <li>移動距離は20-500cmの範囲で指定してください</li>
              </ul>
            </div>
          </div>

          {/* 右側: AIチャット */}
          <div className="chat-panel">
            <AGUIChat />
          </div>
        </div>

        <style jsx>{`
          .app {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          }
          
          .app-header {
            text-align: center;
            padding: 20px;
            color: white;
          }
          
          .app-header h1 {
            margin: 0 0 8px 0;
            font-size: 2.5rem;
            font-weight: bold;
          }
          
          .app-header p {
            margin: 0;
            font-size: 1.1rem;
            opacity: 0.9;
          }
          
          .main-content {
            display: flex;
            gap: 20px;
            padding: 0 20px 20px 20px;
            max-width: 1400px;
            margin: 0 auto;
          }
          
          .control-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
          }
          
          .chat-panel {
            flex: 1;
            min-height: 600px;
          }
          
          .status-card, .safety-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
          
          .status-card h3, .safety-card h3 {
            margin: 0 0 16px 0;
            color: #333;
            font-size: 1.3rem;
          }
          
          .status-grid {
            display: grid;
            gap: 12px;
            margin-bottom: 20px;
          }
          
          .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
          }
          
          .status-label {
            font-weight: 500;
            color: #666;
          }
          
          .status-value {
            font-weight: bold;
          }
          
          .status-value.connected {
            color: #4CAF50;
          }
          
          .status-value.disconnected {
            color: #f44336;
          }
          
          .connection-controls {
            display: flex;
            gap: 10px;
          }
          
          .connect-btn, .disconnect-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s;
          }
          
          .connect-btn {
            background-color: #4CAF50;
            color: white;
          }
          
          .connect-btn:hover:not(:disabled) {
            background-color: #45a049;
          }
          
          .connect-btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
          }
          
          .disconnect-btn {
            background-color: #f44336;
            color: white;
          }
          
          .disconnect-btn:hover {
            background-color: #da190b;
          }
          
          .safety-card ul {
            margin: 0;
            padding-left: 20px;
            color: #666;
          }
          
          .safety-card li {
            margin-bottom: 8px;
            line-height: 1.4;
          }
          
          @media (max-width: 768px) {
            .main-content {
              flex-direction: column;
            }
            
            .app-header h1 {
              font-size: 2rem;
            }
          }
        `}</style>
      </div>
  );
}

export default App; 