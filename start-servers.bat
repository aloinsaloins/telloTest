@echo off
echo ========================================
echo  Tello AI Controller - Server Startup
echo ========================================
echo.
echo Starting 3 servers:
echo 1. Mastra Server (Port 4111)
echo 2. Python Web Server (Port 8080) 
echo 3. React Web App (Port 3000)
echo.
echo Press Ctrl+C to stop all servers
echo ========================================
echo.

REM 新しいコマンドプロンプトウィンドウでMastraサーバーを起動
start "Mastra Server (Port 4111)" cmd /c "npm run dev"

REM 少し待機してからPythonサーバーを起動
timeout /t 3 /nobreak >nul
start "Python Web Server (Port 8080)" cmd /c "python tello_web_server.py"

REM 少し待機してからReactアプリを起動
timeout /t 3 /nobreak >nul
start "React Web App (Port 3000)" cmd /c "npm run web:dev"

echo.
echo All servers are starting...
echo.
echo Mastra Server: http://localhost:4111
echo Python Server: http://localhost:8080
echo React Web App: http://localhost:3000
echo.
echo Opening web browser in 10 seconds...

REM 10秒待機してからブラウザを開く
timeout /t 10 /nobreak >nul
start http://localhost:3000

echo.
echo Done! All servers are running in separate windows.
echo Close those windows or press Ctrl+C to stop the servers.
pause 