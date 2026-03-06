#!/bin/bash
# ================================================================
# AI System Intelligence Platform — Server Setup Script
# Chay 1 lan tren server de cai dat tu dau
# ================================================================
set -e

REPO_URL="https://github.com/hungngominh/AISystemIntelligencePlatform.git"
INSTALL_DIR="$HOME/AISystemIntelligencePlatform"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${YELLOW}[INFO]${NC}  $1"; }

echo ""
echo "=================================================="
echo "  AI System Intelligence Platform — Server Setup"
echo "=================================================="
echo ""

# ── 1. Kiem tra / cai Docker ──────────────────────────────────
info "Kiem tra Docker..."
if ! command -v docker &>/dev/null; then
    info "Docker chua co. Dang cai dat..."
    curl -fsSL https://get.docker.com | bash
    sudo usermod -aG docker "$USER"
    ok "Docker da cai. Ban can logout/login lai de dung khong can sudo."
    info "Tiep tuc voi sudo docker..."
    DOCKER_CMD="sudo docker"
else
    ok "Docker: $(docker --version)"
    DOCKER_CMD="docker"
fi

if ! $DOCKER_CMD compose version &>/dev/null 2>&1; then
    err "Docker Compose v2 khong tim thay. Cai dat Docker moi hon (>= 24.0)."
fi
ok "Docker Compose: $($DOCKER_CMD compose version)"

# ── 2. Clone hoac update repo ────────────────────────────────
info "Chuan bi project..."
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Project da ton tai tai $INSTALL_DIR. Dang pull code moi nhat..."
    cd "$INSTALL_DIR"
    git pull origin main
    ok "Code da duoc cap nhat."
else
    info "Dang clone project tu GitHub..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    ok "Clone thanh cong tai $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── 3. Tao file .env neu chua co ─────────────────────────────
if [ -f ".env" ]; then
    ok "File .env da ton tai. Giu nguyen."
else
    info "Tao file .env..."
    cat > .env << 'ENV_EOF'
# ── PostgreSQL (de trong ca 4 dong neu khong dung postgres-exporter) ──
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_DB=your_db_name

# ── AI — chon MOT trong hai cach ─────────────────────────────────
# Cach 1: Proxy Claudible (neu proxy dang chay tai 192.168.0.101:8000)
ANTHROPIC_BASE_URL=http://192.168.0.101:8000

# Cach 2: Anthropic API key truc tiep
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# ── Claude model ──────────────────────────────────────────────────
CLAUDE_MODEL=claude-sonnet-4-6

# ── Dang nhap vao AI Monitor ──────────────────────────────────────
AUTH_USERNAME=admin
AUTH_PASSWORD=@ISystemInt3llig3nc3Platf()rm
AUTH_SECRET_KEY=change-me-in-production-32chars!!
AUTH_SESSION_MAX_AGE=28800

# ── Thong bao Google Chat (de trong neu chua dung) ────────────────
GOOGLE_CHAT_WEBHOOK_URL=

# ── Cai dat ───────────────────────────────────────────────────────
ANALYSIS_INTERVAL_SECONDS=300
LOG_LEVEL=INFO
ENV_EOF
    ok "File .env da tao tai $INSTALL_DIR/.env"
    echo ""
    echo -e "${YELLOW}  QUAN TRONG: Kiem tra file .env truoc khi start!${NC}"
    echo "  nano $INSTALL_DIR/.env"
    echo ""
    echo "  Neu dung proxy Claudible: dam bao ANTHROPIC_BASE_URL dung"
    echo "  Neu dung Anthropic API:   dien ANTHROPIC_API_KEY vao"
    echo ""
    read -rp "  Nhan Enter khi da chinh xua .env xong (hoac Enter de bo qua)... " _
fi

# ── 4. Validate .env ─────────────────────────────────────────
info "Kiem tra cau hinh .env..."
HAS_AI=0
grep -q "^ANTHROPIC_BASE_URL=http" .env 2>/dev/null && HAS_AI=1
grep -q "^ANTHROPIC_API_KEY=sk-" .env 2>/dev/null && HAS_AI=1
if [ "$HAS_AI" -eq 0 ]; then
    echo -e "${RED}[WARN]${NC}  Chua cau hinh AI (ANTHROPIC_BASE_URL hoac ANTHROPIC_API_KEY)"
    echo "        AI Engine se khong phan tich duoc. Chinh sua .env sau khi cai xong."
else
    ok "AI config OK"
fi

# ── 5. Start services ─────────────────────────────────────────
info "Dang khoi dong tat ca services..."
$DOCKER_CMD compose up -d --build

echo ""
info "Cho services san sang (25s)..."
sleep 25

# ── 6. Status check ──────────────────────────────────────────
echo ""
echo "── Trang thai containers ──"
$DOCKER_CMD compose ps

echo ""
echo "── Kiem tra ket noi ──"
check_url() {
    local name=$1 url=$2
    if curl -sf "$url" &>/dev/null; then
        ok "$name: $url"
    else
        echo -e "${RED}[FAIL]${NC}  $name: $url (chua san sang hoac loi)"
    fi
}

sleep 5
check_url "Prometheus"   "http://localhost:9090/-/healthy"
check_url "Loki"         "http://localhost:3100/ready"
check_url "AI Engine"    "http://localhost:33898/health"

# ── 7. Hoan thanh ────────────────────────────────────────────
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "YOUR_SERVER_IP")
echo ""
echo "=================================================="
echo "  Setup hoan tat!"
echo ""
echo "  Truy cap tu trinh duyet:"
echo "  => AI Monitor:  http://$LOCAL_IP:33898"
echo "     Login: admin / @ISystemInt3llig3nc3Platf()rm"
echo ""
echo "  => Grafana:     http://$LOCAL_IP:3000"
echo "     Login: admin / admin123"
echo ""
echo "  => Prometheus:  http://$LOCAL_IP:9090"
echo "=================================================="
echo ""
echo "  Lenh huu ich:"
echo "  Xem log AI Engine:  docker compose logs ai-engine -f"
echo "  Xem tat ca logs:    docker compose logs -f"
echo "  Stop tat ca:        docker compose down"
echo "  Restart AI Engine:  docker compose restart ai-engine"
echo ""
