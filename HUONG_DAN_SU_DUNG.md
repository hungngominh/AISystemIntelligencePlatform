# AI System Intelligence Platform — Hướng dẫn sử dụng chi tiết

> **Phiên bản**: 2.0.0 | **Cập nhật**: 2026-03-06

---

## Hiểu nhanh hệ thống

Hệ thống gồm **2 phần**, **đều chạy trên cùng một server** bằng Docker:

```
[Server 192.168.0.39]                    [Trình duyệt của bạn]
  docker compose up -d
  ├── prometheus    :9090   <──────────>  http://192.168.0.39:33898
  ├── loki          :3100                 (AI Monitor Dashboard)
  ├── grafana       :3000
  ├── alertmanager  :9093
  ├── node-exporter :9100                 http://192.168.0.39:3000
  ├── cadvisor      :8080                 (Grafana)
  └── ai-engine     :33898
```

**Nguyên lý:**
- `prometheus` + `loki` thu thập metrics/logs của chính server đó
- `ai-engine` đọc data từ prometheus/loki nội bộ → gửi Claude phân tích → hiển thị Web UI
- Bạn mở browser trên **bất kỳ máy nào trong cùng mạng** để xem dashboard

---

## PHẦN 1 — CÀI ĐẶT TRÊN SERVER (192.168.0.39)

> Làm **một lần duy nhất**. Sau đó chỉ cần `docker compose up -d` mỗi khi restart server.

### Bước 1.1 — Yêu cầu server

| Yêu cầu | Lệnh kiểm tra | Tối thiểu |
|---------|--------------|-----------|
| OS | `cat /etc/os-release` | Ubuntu 20.04+ / Debian 11+ |
| Docker Engine | `docker --version` | 24.0+ |
| Docker Compose v2 | `docker compose version` | 2.20+ |
| RAM | `free -h` | 4 GB |
| Disk trống | `df -h /` | 20 GB |

**Cài Docker nếu chưa có (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
newgrp docker
docker --version       # Kết quả: Docker version 24.x.x
docker compose version # Kết quả: Docker Compose version v2.x.x
```

### Bước 1.2 — Clone project lên server

```bash
# SSH vào server
ssh user@192.168.0.39

# Clone project (lần đầu)
git clone https://github.com/hungngominh/AISystemIntelligencePlatform.git
cd AISystemIntelligencePlatform
```

Nếu đã có project rồi, pull code mới nhất:
```bash
cd AISystemIntelligencePlatform
git pull origin main
```

### Bước 1.3 — Tạo file .env trên server

File `.env` phải nằm ở **thư mục gốc** (cùng cấp với `docker-compose.yml`):

```bash
nano .env
```

Dán nội dung sau, **chỉnh sửa các giá trị theo thực tế**:

```env
# ── PostgreSQL (để trống cả 4 dòng nếu không dùng postgres-exporter) ──
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=192.168.0.39
POSTGRES_DB=your_db_name

# ── AI — chọn MỘT trong hai cách ──────────────────────────────────────
# Cách 1: Proxy Claudible (nếu proxy đang chạy tại 192.168.0.101:8000)
ANTHROPIC_BASE_URL=http://192.168.0.101:8000

# Cách 2: Anthropic API key trực tiếp
# (xoá dòng ANTHROPIC_BASE_URL trên, bỏ comment dòng dưới)
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx

# ── Model Claude ────────────────────────────────────────────────────────
CLAUDE_MODEL=claude-sonnet-4-6

# ── Đăng nhập vào AI Monitor ────────────────────────────────────────────
AUTH_USERNAME=admin
AUTH_PASSWORD=@ISystemInt3llig3nc3Platf()rm
AUTH_SECRET_KEY=change-me-in-production-32chars!!
AUTH_SESSION_MAX_AGE=28800

# ── Thông báo Google Chat (để trống nếu chưa dùng) ──────────────────────
GOOGLE_CHAT_WEBHOOK_URL=

# ── Cài đặt khác ────────────────────────────────────────────────────────
ANALYSIS_INTERVAL_SECONDS=300
LOG_LEVEL=INFO
```

Lưu: `Ctrl+O` → `Enter` → `Ctrl+X`

### Bước 1.4 — Khởi động tất cả services

```bash
# Phải đứng trong thư mục AISystemIntelligencePlatform
docker compose up -d --build
```

Lần đầu mất **3–5 phút** pull Docker images. Các lần sau chỉ vài giây.

Kiểm tra sau khi start:
```bash
docker compose ps
```

Kết quả mong đợi — tất cả `STATUS` phải là `Up`:
```
NAME                STATUS
prometheus          Up
loki                Up
grafana             Up
alertmanager        Up
otel-collector      Up
node-exporter       Up
cadvisor            Up
ai-engine           Up
```

> **`postgres-exporter` bị Exit** nếu chưa cấu hình PostgreSQL — **không sao**, các service khác không bị ảnh hưởng.

### Bước 1.5 — Xác nhận hoạt động

Chạy ngay trên server:
```bash
curl http://localhost:9090/-/healthy   # Prometheus
curl http://localhost:3100/ready       # Loki
curl http://localhost:33898/health     # AI Engine
```

Chạy từ máy bạn (cùng mạng LAN):
```bash
curl http://192.168.0.39:9090/-/healthy
curl http://192.168.0.39:33898/health
```

Kết quả mong đợi:
- Prometheus → `Prometheus Server is Healthy.`
- Loki → `ready`
- AI Engine → `{"status":"ok","timestamp":"..."}`

### Bước 1.6 — Theo dõi log AI Engine

```bash
docker compose logs ai-engine -f
```

Log khởi động bình thường:
```
INFO  AI System Intelligence Platform starting...
INFO     Prometheus: http://prometheus:9090
INFO     Loki:       http://loki:3100
INFO     Port:       8765
INFO     Model:      claude-sonnet-4-6
INFO  Analyzer: dùng OpenAI-compatible proxy → http://192.168.0.101:8000
INFO  DB initialized. Default Server seeded.
INFO  Scheduler started. Sync interval: 60s
INFO  Added job for server_id=1 (Default Server)
```

Log phân tích định kỳ (mỗi 5 phút):
```
INFO  [server_id=1] Collecting metrics from prometheus...
INFO  [server_id=1] Analysis done: status=ok tokens=854
```

Khi thấy `Analysis done` → **hệ thống đang hoạt động đúng**.

---

## PHẦN 2 — TRUY CẬP WEB UI

Sau khi server đã start, mở trình duyệt:

```
http://192.168.0.39:33898
```

Đăng nhập:
- **Username**: `admin`
- **Password**: `@ISystemInt3llig3nc3Platf()rm`

### Tất cả URL hữu ích

| Service | URL | Tài khoản |
|---------|-----|-----------|
| **AI Monitor** (dùng hàng ngày) | `http://192.168.0.39:33898` | admin / @ISystemInt3llig3nc3Platf()rm |
| Grafana (đồ thị chi tiết) | `http://192.168.0.39:3000` | admin / admin123 |
| Prometheus (query trực tiếp) | `http://192.168.0.39:9090` | Không cần login |
| Prometheus Targets | `http://192.168.0.39:9090/targets` | Xem trạng thái scrape |
| AlertManager | `http://192.168.0.39:9093` | Không cần login |
| cAdvisor (container metrics) | `http://192.168.0.39:8080` | Không cần login |

---

## PHẦN 3 — CHẠY AI ENGINE TRÊN MÁY CỦA BẠN (tùy chọn)

> Dùng khi: dev/debug, hoặc muốn chạy AI Engine riêng trỏ đến server.
> **Server vẫn phải chạy Prometheus + Loki.**

### Bước 3.1 — Yêu cầu

| Yêu cầu | Kiểm tra |
|---------|---------|
| Python 3.10+ | `python --version` |
| Kết nối đến server | `curl http://192.168.0.39:9090/-/healthy` |

### Bước 3.2 — Cấu hình ai-engine/.env

```env
ANTHROPIC_BASE_URL=http://192.168.0.101:8000
CLAUDE_MODEL=claude-sonnet-4-6
PROMETHEUS_URL=http://192.168.0.39:9090
LOKI_URL=http://192.168.0.39:3100
ALERTMANAGER_URL=http://192.168.0.39:9093
AI_ENGINE_HOST=0.0.0.0
AI_ENGINE_PORT=8765
ANALYSIS_INTERVAL_SECONDS=300
DB_PATH=./data/ai_engine.db
AUTH_USERNAME=admin
AUTH_PASSWORD=@ISystemInt3llig3nc3Platf()rm
AUTH_SECRET_KEY=change-me-in-production-32chars!!
AUTH_SESSION_MAX_AGE=28800
GOOGLE_CHAT_WEBHOOK_URL=
LOG_LEVEL=INFO
```

### Bước 3.3 — Khởi động

**Windows:**
```cmd
cd D:\Work\AISystemIntelligencePlatform\ai-engine
start.bat
```

**Linux/macOS:**
```bash
cd /path/to/AISystemIntelligencePlatform/ai-engine
chmod +x start.sh
./start.sh
```

Script tự động: tạo venv → cài packages → khởi động tại port 8765.

Mở trình duyệt: **`http://localhost:8765`**

---

## PHẦN 4 — SỬ DỤNG HÀNG NGÀY

### Dashboard chính

Sau khi đăng nhập bạn thấy:

```
🤖 AI Monitor  [Dashboard] [Servers] [Chat]          [▶ Phân tích ngay] [⏻]

  🟢 Production VPS   🟡 Staging Server   ⚫ Dev Server

  ┌─────────────────────────────────────────────────────────┐
  │  Production VPS                                          │
  │  ✅ HỆ THỐNG BÌNH THƯỜNG                                │
  │  "CPU 45%, Memory 62%, không có alert, 0 lỗi logs"     │
  │  2026-03-06 10:30:00 UTC                    [💬 Hỏi AI] │
  ├──────────┬──────────┬──────────┬──────────             │
  │    30    │    25    │    4     │    1                   │
  │   Tổng   │    OK    │  Warning │  Critical              │
  └─────────────────────────────────────────────────────────┘
```

**Màu dots trên tabs:**
- 🟢 Xanh = OK
- 🟡 Vàng = Warning, cần chú ý
- 🔴 Đỏ = Critical, cần xử lý ngay
- ⚫ Đen = Chưa có dữ liệu

**Thao tác:**
| Nút/hành động | Kết quả |
|---------------|---------|
| Click tab server | Chuyển xem server khác |
| `▶ Phân tích ngay` | Kích hoạt phân tích ngay lập tức |
| Click dòng trong bảng | Xem báo cáo AI chi tiết |
| `💬 Hỏi AI` | Mở chat về server đang xem |
| Dashboard tự refresh | Mỗi 30 giây |

### Thêm server mới để monitor

1. Vào **Servers** (menu trên)
2. Nhấn **"+ Thêm server"**
3. Điền thông tin:
   - **Tên**: tên hiển thị, ví dụ `Production VPS`
   - **Prometheus URL**: `http://IP_SERVER:9090`
   - **Loki URL**: `http://IP_SERVER:3100`
4. Nhấn **"🔍 Ping"** để kiểm tra kết nối
5. Nhấn **Lưu**

→ AI Engine tự động bắt đầu phân tích server mới trong vòng 60 giây.

> **Lưu ý:** Prometheus và Loki trên server đó phải **mở port ra ngoài** để AI Engine truy cập được.

### Chat với AI

Vào **Chat** → chọn server → đặt câu hỏi bằng tiếng Việt:

```
Bạn: "CPU đang như thế nào?"
AI:  "CPU đang ở mức 45.2%, bình thường.
      Memory 62%, disk 34%..."

Bạn: "Có vấn đề gì cần chú ý không?"
AI:  "Phát hiện queue backlog tăng lên 85 items
      trong 15 phút qua, nên theo dõi..."
```

AI có dữ liệu metrics thực tế của server nên trả lời chính xác.

### Đọc báo cáo chi tiết

Click vào bất kỳ dòng phân tích nào → trang chi tiết:

- **Tab "Báo cáo AI"**: Phân tích đầy đủ bằng Markdown, gồm:
  - Tổng quan status
  - Vấn đề phát hiện (nếu có)
  - Đề xuất hành động cụ thể
- **Tab "Raw Metrics"**: Dữ liệu JSON gốc thu thập được

---

## PHẦN 5 — NHẬN THÔNG BÁO GOOGLE CHAT

Khi AI phát hiện WARNING hoặc CRITICAL → tự động gửi vào Google Chat.

### Tạo Webhook

1. Google Chat → Space (nhóm) muốn nhận thông báo
2. Click tên Space → **Apps & integrations** → **Webhooks**
3. **Add webhook** → tên `AI Monitor` → **Save** → Copy URL

### Cấu hình

Điền vào `.env` (trên server):
```env
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/XXXXX/messages?key=...&token=...
```

Restart AI Engine:
```bash
docker compose restart ai-engine
```

Test gửi thông báo:
```bash
curl -X POST http://192.168.0.39:33898/api/notifications/test
```

---

## PHẦN 6 — THAY ĐỔI CẤU HÌNH

Sau mỗi thay đổi `.env` trên server, restart AI Engine:
```bash
docker compose restart ai-engine
```

### Đổi mật khẩu đăng nhập

```env
AUTH_USERNAME=admin
AUTH_PASSWORD=mật_khẩu_mới
```

### Đổi tần suất phân tích

```env
ANALYSIS_INTERVAL_SECONDS=60    # 1 phút — debug, tốn nhiều token
ANALYSIS_INTERVAL_SECONDS=300   # 5 phút — mặc định, khuyên dùng
ANALYSIS_INTERVAL_SECONDS=900   # 15 phút — tiết kiệm token
```

### Đổi model Claude

```env
CLAUDE_MODEL=claude-haiku-4-5-20251001   # Nhanh, ít token, kém chính xác hơn
CLAUDE_MODEL=claude-sonnet-4-6           # Cân bằng (mặc định)
CLAUDE_MODEL=claude-opus-4-6             # Chất lượng cao nhất, nhiều token nhất
```

---

## PHẦN 7 — XỬ LÝ SỰ CỐ

### Vấn đề 1: "Không có dữ liệu" / UNKNOWN

**90% nguyên nhân: server chưa start docker-compose.**

Kiểm tra kết nối từ máy bạn:
```bash
curl http://192.168.0.39:9090/-/healthy
```
- Không phản hồi → SSH vào server, start lại docker-compose
- Phản hồi OK → xem tiếp log AI Engine

SSH vào server kiểm tra:
```bash
ssh user@192.168.0.39
cd AISystemIntelligencePlatform

docker compose ps                    # Xem service nào Down
docker compose up -d                 # Start service bị Down
docker compose logs ai-engine --tail=50  # Tìm lỗi cụ thể
```

Prometheus đang chạy nhưng không có data:
- Mở `http://192.168.0.39:9090/targets` trong browser
- Target màu đỏ (DOWN) → exporter đó chưa chạy

### Vấn đề 2: AI Engine log lỗi kết nối

```bash
docker compose logs ai-engine 2>&1 | grep -iE "error|fail|refuse"
```

| Lỗi trong log | Nguyên nhân | Cách fix |
|--------------|------------|---------|
| `Connection refused prometheus:9090` | Prometheus chưa chạy | `docker compose restart prometheus` |
| `Connection refused loki:3100` | Loki chưa chạy | `docker compose restart loki` |
| `Claude API error: Connection refused` | Proxy Claudible chưa start | Start proxy tại máy 192.168.0.101 |
| `Invalid API key` | Claudible từ chối source IP | Kiểm tra `http://192.168.0.101:8000/__dashboard__` |

### Vấn đề 3: AI Engine không start — lỗi config

```bash
docker compose logs ai-engine | head -30
```

| Lỗi | Nguyên nhân | Cách fix |
|-----|------------|---------|
| `Phải cấu hình ít nhất một trong hai...` | Thiếu ANTHROPIC_BASE_URL/API_KEY | Thêm vào `.env` |
| `EnvSettingsError` | Ký tự lạ trong `.env` | Tạo lại file `.env` từ đầu |
| `Port already in use` | Port 8765 bị chiếm | Đổi `AI_ENGINE_PORT` trong `.env` |

### Vấn đề 4: Proxy Claudible lỗi

Proxy tại `192.168.0.101:8000` xác thực bằng **source IP**.

```bash
# Kiểm tra proxy còn sống
curl http://192.168.0.101:8000/__stats__

# Nếu không phản hồi → vào máy 192.168.0.101:
# cd D:\Work\ClaudeTokenTracker && start_proxy.bat
```

### Vấn đề 5: Web UI trắng, lỗi JS

1. `F12` → tab **Console** → xem lỗi đỏ
2. Xóa cache: `Ctrl+Shift+Delete` → Clear All → Reload

### Restart toàn bộ từ đầu

```bash
ssh user@192.168.0.39
cd AISystemIntelligencePlatform
docker compose down
docker compose up -d --build
docker compose logs -f
```

---

## Tóm tắt ports

| Service | Port | URL | Mục đích |
|---------|------|-----|---------|
| **AI Monitor** | **33898** | `http://192.168.0.39:33898` | **Dashboard AI — dùng hàng ngày** |
| Prometheus | 9090 | `http://192.168.0.39:9090` | Query metrics, xem targets |
| Grafana | 3000 | `http://192.168.0.39:3000` | Đồ thị chi tiết (admin/admin123) |
| Loki | 3100 | `http://192.168.0.39:3100` | Query logs |
| AlertManager | 9093 | `http://192.168.0.39:9093` | Xem và quản lý alerts |
| OTEL Collector | 4317/4318 | — | Nhận telemetry từ ứng dụng |
| Node Exporter | 9100 | — | Metrics CPU/RAM/Disk server |
| cAdvisor | 8080 | `http://192.168.0.39:8080` | Metrics Docker containers |

---

## Luồng hoạt động

```
Mỗi 5 phút (cấu hình được):

  AI Engine (Docker, cùng server)
    ├─► prometheus:9090  →  CPU, RAM, Disk, API latency, error rate, queue
    ├─► loki:3100        →  Logs lỗi 15 phút gần nhất
    └─► Claude AI        →  STATUS: OK / WARNING / CRITICAL + phân tích
         ├─► Lưu vào SQLite DB
         └─► Nếu WARNING/CRITICAL → Gửi Google Chat

Khi AlertManager firing:
  AlertManager → webhook → AI Engine /api/webhooks/alertmanager
    └─► Phân tích ngay → Gửi Google Chat kèm runbook

Người dùng:
  Browser → http://192.168.0.39:33898 → Xem dashboard, chat với AI
```

---

*AI System Intelligence Platform v2.0 — https://github.com/hungngominh/AISystemIntelligencePlatform*
