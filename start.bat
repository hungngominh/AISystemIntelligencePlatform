@echo off
REM =============================================================
REM AI System Intelligence Platform — Full Stack Start (Windows)
REM =============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   AI System Intelligence Platform v2.0           ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Kiểm tra Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker khong tim thay. Cai dat Docker Desktop truoc.
    pause
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose v2 khong tim thay.
    pause
    exit /b 1
)

echo [OK] Docker da san sang.

REM Kiểm tra .env
if not exist ".env" (
    echo [ERROR] File .env khong tim thay
    pause
    exit /b 1
)

REM Cảnh báo API key
findstr "your-anthropic-api-key-here" .env >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [WARN] ANTHROPIC_API_KEY chua duoc cau hinh!
    echo        Mo file .env de dien API key:
    notepad .env
    echo.
    echo Nhan Enter khi da dien xong API key...
    pause
)

echo.
echo [START] Khoi dong tat ca services...
docker compose up -d --build

echo.
echo [WAIT] Cho services san sang (20s)...
timeout /t 20 /nobreak >nul

echo.
echo [STATUS] Trang thai services:
docker compose ps

echo.
echo ═══════════════════════════════════════════════
echo   [OK] Platform da san sang!
echo.
echo   AI Engine Dashboard:  http://localhost:8765
echo   Grafana:              http://localhost:3000
echo     Username: admin ^| Password: admin123
echo   Prometheus:           http://localhost:9090
echo   AlertManager:         http://localhost:9093
echo ═══════════════════════════════════════════════
echo.
echo   Xem logs AI Engine:  docker compose logs ai-engine -f
echo   Dung tat ca:         docker compose down
echo.

REM Mở browser
start "" "http://localhost:8765"

pause
