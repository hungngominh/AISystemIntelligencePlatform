#!/bin/bash
# =============================================================
# AI Engine - Start Script (Linux / macOS)
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  AI System Intelligence Platform - AI Engine"
echo "=================================================="

# Kiểm tra Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 không tìm thấy. Cài đặt Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION"

# Kiểm tra .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ""
        echo "⚠️  File .env chưa có — đã copy từ .env.example"
        echo "   Hãy điền ANTHROPIC_API_KEY vào file .env trước khi chạy lại"
        echo ""
        exit 1
    else
        echo "❌ Không tìm thấy file .env"
        exit 1
    fi
fi

# Kiểm tra ANTHROPIC_API_KEY
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  ANTHROPIC_API_KEY chưa được cấu hình trong .env"
    echo "   Chỉnh sửa: nano .env"
fi

# Tạo venv nếu chưa có
if [ ! -d "venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📦 Cài đặt dependencies..."
pip install -q -r requirements.txt

# Tạo thư mục data
mkdir -p data

echo ""
echo "🚀 Khởi động AI Engine..."
echo "   Dashboard: http://localhost:$(grep AI_ENGINE_PORT .env 2>/dev/null | cut -d= -f2 || echo 8765)"
echo "   Nhấn Ctrl+C để dừng"
echo ""

python3 main.py
