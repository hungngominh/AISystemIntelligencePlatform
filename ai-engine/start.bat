@echo off
REM =============================================================
REM AI Engine - Start Script (Windows)
REM =============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==================================================
echo   AI System Intelligence Platform - AI Engine
echo ==================================================

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python khong tim thay. Cai dat Python 3.10+ tu python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo [OK] Python %PYVER%

REM Kiểm tra .env
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo.
        echo [WARN] File .env chua co - da copy tu .env.example
        echo        Hay dien ANTHROPIC_API_KEY vao file .env truoc khi chay lai
        echo        Mo file: notepad .env
        echo.
        notepad .env
        pause
        exit /b 1
    ) else (
        echo [ERROR] Khong tim thay file .env
        pause
        exit /b 1
    )
)

REM Tạo venv nếu chưa có
if not exist "venv" (
    echo [INFO] Tao virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Cai dat dependencies...
pip install -q -r requirements.txt

REM Tạo thư mục data
if not exist "data" mkdir data

echo.
echo [START] Khoi dong AI Engine...

REM Đọc port từ .env (đơn giản hóa)
set PORT=8765
for /f "tokens=2 delims==" %%i in ('findstr "AI_ENGINE_PORT" .env 2^>nul') do set PORT=%%i

echo        Dashboard: http://localhost:%PORT%
echo        Nhan Ctrl+C de dung
echo.

python main.py

pause
