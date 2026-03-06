#!/bin/bash
# =============================================================
# AI System Intelligence Platform — Full Stack Start (Linux/macOS)
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   AI System Intelligence Platform v2.0           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Kiểm tra Docker
if ! command -v docker &>/dev/null; then
    echo "❌ Docker không tìm thấy. Cài đặt Docker Desktop trước."
    exit 1
fi

if ! docker compose version &>/dev/null 2>&1; then
    echo "❌ Docker Compose v2 không tìm thấy."
    exit 1
fi

echo "✅ Docker: $(docker --version)"

# Kiểm tra .env
if [ ! -f ".env" ]; then
    echo "❌ File .env không tìm thấy"
    exit 1
fi

# Cảnh báo nếu chưa set API key
if grep -q "your-anthropic-api-key-here" .env; then
    echo ""
    echo "⚠️  ANTHROPIC_API_KEY chưa được cấu hình!"
    echo "   Chỉnh sửa file .env:"
    echo "   nano .env"
    echo ""
    read -p "   Tiếp tục anyway? (y/N): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Khởi động tất cả services..."
docker compose up -d --build

echo ""
echo "⏳ Chờ services sẵn sàng (20s)..."
sleep 20

echo ""
echo "📊 Trạng thái services:"
docker compose ps

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Platform đã sẵn sàng!"
echo ""
echo "  🤖 AI Engine Dashboard:  http://localhost:8765"
echo "  📊 Grafana:              http://localhost:3000"
echo "     Username: admin | Password: admin123"
echo "  📈 Prometheus:           http://localhost:9090"
echo "  🚨 AlertManager:         http://localhost:9093"
echo "═══════════════════════════════════════════════"
echo ""
echo "  Xem logs AI Engine:  docker compose logs ai-engine -f"
echo "  Dừng tất cả:         docker compose down"
echo ""
