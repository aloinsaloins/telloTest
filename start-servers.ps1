# Tello AI Controller - Server Startup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Tello AI Controller - Server Startup" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting 3 servers:" -ForegroundColor Yellow
Write-Host "1. Mastra Server (Port 4111)" -ForegroundColor Blue
Write-Host "2. Python Web Server (Port 8080)" -ForegroundColor Green
Write-Host "3. React Web App (Port 3000)" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 新しいPowerShellウィンドウでMastraサーバーを起動
Start-Process powershell -ArgumentList "-Command", "& { Write-Host 'Starting Mastra Server...' -ForegroundColor Blue; npm run dev; Read-Host 'Press Enter to close' }" -WindowStyle Normal

# 3秒待機
Start-Sleep -Seconds 3

# 新しいPowerShellウィンドウでPythonサーバーを起動
Start-Process powershell -ArgumentList "-Command", "& { Write-Host 'Starting Python Web Server...' -ForegroundColor Green; python tello_web_server.py; Read-Host 'Press Enter to close' }" -WindowStyle Normal

# 3秒待機
Start-Sleep -Seconds 3

# 新しいPowerShellウィンドウでReactアプリを起動
Start-Process powershell -ArgumentList "-Command", "& { Write-Host 'Starting React Web App...' -ForegroundColor Magenta; npm run web:dev; Read-Host 'Press Enter to close' }" -WindowStyle Normal

Write-Host ""
Write-Host "All servers are starting..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Mastra Server: http://localhost:4111" -ForegroundColor Blue
Write-Host "Python Server: http://localhost:8080" -ForegroundColor Green  
Write-Host "React Web App: http://localhost:3000" -ForegroundColor Magenta
Write-Host ""
Write-Host "Opening web browser in 10 seconds..." -ForegroundColor Yellow

# 10秒待機してからブラウザを開く
Start-Sleep -Seconds 10
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Done! All servers are running in separate windows." -ForegroundColor Green
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit this window" 