@echo off
setlocal enabledelayedexpansion
chcp 65001 >/dev/null 2>&1

echo.
echo ==================================================
echo   AI System Intelligence Platform - Server Setup
echo   Danh cho Windows 10
echo ==================================================
echo.

cd /d "%~dp0"

REM ── 1. Kiem tra Docker ───────────────────────────────────────
echo [1/5] Kiem tra Docker...
docker --version >/dev/null 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Docker chua duoc cai dat!
    echo.
    echo Vui long cai Docker Desktop truoc:
    echo   1. Tai tai: https://www.docker.com/products/docker-desktop/
    echo   2. Cai dat va khoi dong lai may
    echo   3. Mo Docker Desktop, doi icon tray chuyen sang mau xanh
    echo   4. Chay lai file nay
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('docker --version') do echo [OK] %%v

docker compose version >/dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose v2 khong tim thay. Cap nhat Docker Desktop.
    pause
    exit /b 1
)
echo [OK] Docker Compose OK

REM ── 2. Kiem tra Git ──────────────────────────────────────────
echo.
echo [2/5] Kiem tra Git...
git --version >/dev/null 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Git chua duoc cai dat!
    echo.
    echo Vui long cai Git truoc:
    echo   Tai tai: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('git --version') do echo [OK] %%v

REM ── 3. Clone hoac update repo ────────────────────────────────
echo.
echo [3/5] Chuan bi code...
if exist ".git" (
    echo [INFO] Da co project, dang pull code moi nhat...
    git pull origin main
    if errorlevel 1 (
        echo [WARN] Pull that bai. Tiep tuc voi code hien tai.
    ) else (
        echo [OK] Code da cap nhat.
    )
) else (
    echo [ERROR] Khong tim thay .git. Script nay phai duoc chay tu thu muc project.
    echo.
    echo Hay chay theo cach sau:
    echo   1. Mo Command Prompt hoac PowerShell
    echo   2. git clone https://github.com/hungngominh/AISystemIntelligencePlatform.git
    echo   3. cd AISystemIntelligencePlatform
    echo   4. server-setup.bat
    pause
    exit /b 1
)

REM ── 4. Tao .env neu chua co ──────────────────────────────────
echo.
echo [4/5] Kiem tra cau hinh .env...
if not exist ".env" (
    echo [INFO] Chua co file .env. Dang tao...
    (
        echo # ── PostgreSQL (bo trong neu khong dung postgres-exporter^) ──
        echo POSTGRES_USER=postgres
        echo POSTGRES_PASSWORD=your_db_password
        echo POSTGRES_HOST=localhost
        echo POSTGRES_DB=your_db_name
        echo.
        echo # ── AI - CHINH SUA PHAN NAY ────────────────────────────────
        echo # Cach 1: Proxy Claudible ^(dang su dung^)
        echo ANTHROPIC_BASE_URL=http://192.168.0.101:8000
        echo.
        echo # Cach 2: Anthropic API key truc tiep
        echo # ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
        echo.
        echo # ── Claude model ──────────────────────────────────────────
        echo CLAUDE_MODEL=claude-sonnet-4-6
        echo.
        echo # ── Dang nhap vao AI Monitor ──────────────────────────────
        echo AUTH_USERNAME=admin
        echo AUTH_PASSWORD=@ISystemInt3llig3nc3Platf^(^)rm
        echo AUTH_SECRET_KEY=change-me-in-production-32chars!!
        echo AUTH_SESSION_MAX_AGE=28800
        echo.
        echo # ── Thong bao Google Chat ^(de trong neu chua dung^) ────────
        echo GOOGLE_CHAT_WEBHOOK_URL=
        echo.
        echo # ── Cai dat ───────────────────────────────────────────────
        echo ANALYSIS_INTERVAL_SECONDS=300
        echo LOG_LEVEL=INFO
    ) > .env
    echo [OK] Da tao file .env
    echo.
    echo ============================================
    echo   QUAN TRONG: Kiem tra lai file .env
    echo ============================================
    echo.
    echo Dang mo notepad de ban chinh sua...
    notepad .env
    echo.
    echo Nhan Enter khi da luu xong .env...
    pause
) else (
    echo [OK] File .env da ton tai.
    echo.
    echo Xem lai noi dung .env:
    type .env | findstr /v "^#" | findstr /v "^$"
    echo.
    set /p EDIT_ENV="Muon chinh sua .env khong? (y/N): "
    if /i "!EDIT_ENV!"=="y" (
        notepad .env
        echo Nhan Enter khi da luu xong...
        pause
    )
)

REM ── 5. Start Docker Compose ──────────────────────────────────
echo.
echo [5/5] Khoi dong tat ca services...
echo.
docker compose up -d --build
if errorlevel 1 (
    echo.
    echo [ERROR] docker compose up that bai!
    echo.
    echo Kiem tra:
    echo   1. Docker Desktop co dang chay khong? (icon tray phai mau xanh)
    echo   2. docker compose logs de xem loi chi tiet
    pause
    exit /b 1
)

echo.
echo [INFO] Cho services san sang (30s)...
timeout /t 30 /nobreak >/dev/null

REM ── Ket qua ──────────────────────────────────────────────────
echo.
echo ── Trang thai containers ──
docker compose ps

echo.
echo ── Kiem tra ket noi ──

curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1
if errorlevel 1 (
    echo [WARN] Prometheus: http://localhost:9090 (chua san sang)
) else (
    echo [OK]   Prometheus: http://localhost:9090
)

curl -sf http://localhost:3100/ready >/dev/null 2>&1
if errorlevel 1 (
    echo [WARN] Loki:       http://localhost:3100 (chua san sang)
) else (
    echo [OK]   Loki:       http://localhost:3100
)

curl -sf http://localhost:33898/health >/dev/null 2>&1
if errorlevel 1 (
    echo [WARN] AI Engine:  http://localhost:33898 (chua san sang - doi them 30s)
) else (
    echo [OK]   AI Engine:  http://localhost:33898
)

REM Lay IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /r "IPv4.*192\.168"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP: =!
)

echo.
echo ==================================================
echo   Setup hoan tat!
echo.
echo   Truy cap tu may khac trong cung mang:
echo   =^> AI Monitor:  http://!LOCAL_IP!:33898
echo      Login: admin / @ISystemInt3llig3nc3Platf()rm
echo.
echo   =^> Grafana:     http://!LOCAL_IP!:3000
echo      Login: admin / admin123
echo.
echo   =^> Prometheus:  http://!LOCAL_IP!:9090
echo ==================================================
echo.
echo   Lenh huu ich (chay trong thu muc nay):
echo   Xem log AI:    docker compose logs ai-engine -f
echo   Xem tat ca:    docker compose logs -f
echo   Stop tat ca:   docker compose down
echo   Restart AI:    docker compose restart ai-engine
echo.
echo Nhan Enter de mo AI Monitor trong trinh duyet...
pause
start "" "http://localhost:33898"
