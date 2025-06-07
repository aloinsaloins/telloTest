import React, { useState, useEffect, useRef } from 'react';

interface TelloVideoStreamProps {
  isStreaming: boolean;
  onStreamToggle: (streaming: boolean) => void;
}

export const TelloVideoStream: React.FC<TelloVideoStreamProps> = ({
  isStreaming,
  onStreamToggle
}) => {
  const [frame, setFrame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // ビデオフレームを定期的に取得
  useEffect(() => {
    if (isStreaming) {
      const fetchFrame = async () => {
        try {
          const response = await fetch('/api/video/frame');
          const data = await response.json();
          
          if (data.success && data.frame) {
            setFrame(data.frame);
            setError(null);
          } else {
            setError(data.message || 'フレームの取得に失敗しました');
          }
        } catch (err) {
          setError('ビデオフレームの取得中にエラーが発生しました');
          console.error('Video frame fetch error:', err);
        }
      };

      // 100ms間隔でフレームを取得（10 FPS）
      intervalRef.current = setInterval(fetchFrame, 100);
      
      // 初回実行
      fetchFrame();
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setFrame(null);
      setError(null);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isStreaming]);

  const handleStreamToggle = async () => {
    try {
      if (isStreaming) {
        // ストリーミング停止
        const response = await fetch('/api/video/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
          onStreamToggle(false);
        } else {
          setError(data.message || 'ストリーミングの停止に失敗しました');
        }
      } else {
        // ストリーミング開始
        const response = await fetch('/api/video/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
          onStreamToggle(true);
        } else {
          setError(data.message || 'ストリーミングの開始に失敗しました');
        }
      }
    } catch (err) {
      setError('ストリーミング制御中にエラーが発生しました');
      console.error('Stream toggle error:', err);
    }
  };

  return (
    <div className="tello-video-stream">
      <div className="video-header">
        <h3>Tello ライブ映像</h3>
        <button
          onClick={handleStreamToggle}
          className={`stream-toggle-btn ${isStreaming ? 'stop' : 'start'}`}
          disabled={false}
        >
          {isStreaming ? 'ストリーミング停止' : 'ストリーミング開始'}
        </button>
      </div>
      
      <div className="video-container">
        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}
        
        {isStreaming && frame ? (
          <img
            src={`data:image/jpeg;base64,${frame}`}
            alt="Tello Live Stream"
            className="video-frame"
          />
        ) : (
          <div className="no-video">
            <div className="placeholder">
              {isStreaming ? (
                <p>📹 ビデオフレームを読み込み中...</p>
              ) : (
                <p>📷 ビデオストリーミングが停止中</p>
              )}
            </div>
          </div>
        )}
      </div>
      
      <style jsx>{`
        .tello-video-stream {
          background: #f5f5f5;
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .video-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .video-header h3 {
          margin: 0;
          color: #333;
          font-size: 18px;
        }
        
        .stream-toggle-btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: bold;
          transition: background-color 0.2s;
        }
        
        .stream-toggle-btn.start {
          background-color: #4CAF50;
          color: white;
        }
        
        .stream-toggle-btn.start:hover {
          background-color: #45a049;
        }
        
        .stream-toggle-btn.stop {
          background-color: #f44336;
          color: white;
        }
        
        .stream-toggle-btn.stop:hover {
          background-color: #da190b;
        }
        
        .stream-toggle-btn:disabled {
          background-color: #cccccc;
          cursor: not-allowed;
        }
        
        .video-container {
          position: relative;
          width: 100%;
          height: 300px;
          background: #000;
          border-radius: 4px;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .video-frame {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }
        
        .no-video {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100%;
        }
        
        .placeholder {
          text-align: center;
          color: #888;
        }
        
        .placeholder p {
          margin: 0;
          font-size: 16px;
        }
        
        .error-message {
          position: absolute;
          top: 8px;
          left: 8px;
          right: 8px;
          background: rgba(244, 67, 54, 0.9);
          color: white;
          padding: 8px;
          border-radius: 4px;
          z-index: 10;
        }
        
        .error-message p {
          margin: 0;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}; 