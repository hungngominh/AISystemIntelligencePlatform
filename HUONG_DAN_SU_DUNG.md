# AI System Intelligence Platform — Hướng dẫn sử dụng

> **Phiên bản**: 2.0.0 | **Cập nhật**: 2026-03-06

---

## Hiểu nhanh: Hệ thống gồm 2 phần

```
┌─────────────────────────┐        ┌──────────────────────────┐
│   SERVER CẦN MONITOR    │        │      MÁY CỦA BẠN         │
│  (222.253.80.38)        │◄──────►│  (máy tính cá nhân)      │
│                         │        │                          │
│  • Prometheus :9090     │        │  • AI Engine chạy ở đây  │
│  • Loki :3100           │        │  • Mở browser xem UI     │
│  • Grafana :3000        │        │  • http://localhost:33898 │
│  • Ứng dụng của bạn     │        │                          │
└─────────────────────────┘        └──────────────────────────┘
         ↑ Thu thập metrics                  ↑ Phân tích AI
```

**Nguyên lý hoạt động:**
- **Server** chạy Prometheus/Loki để thu thập metrics và logs từ ứng dụng
- **AI Engine** (chạy cùng server hoặc máy khác) đọc data từ Prometheus/Loki → gửi cho Claude phân tích → hiển thị kết quả lên Web UI

---

## PHẦN 1 — SERVER CẦN LÀM GÌ?

Server của bạn cần chạy **Observability Stack** (Prometheus, Loki, Grafana...) để thu thập dữ liệu.

### Bước 1.1 — Yêu cầu

| Yêu cầu | Kiểm tra |
|---------|---------|
| Docker + Docker Compose | `docker --version` |
| Port 9090 (Prometheus) mở | Firewall hoặc VPS panel |
| Port 3100 (Loki) mở | Firewall hoặc VPS panel |
| Ứng dụng đang chạy | `.NET API` hoặc `Python FastAPI` |

### Bước 1.2 — Deploy Observability Stack lên server

```bash
# SSH vào server
ssh user@222.253.80.38 -p 33898

# Clone/copy project lên server
git clone <your-repo> AISystemIntelligencePlatform
cd AISystemIntelligencePlatform

# Chỉnh sửa .env (điền thông tin PostgreSQL của bạn)
nano .env
```

Nội dung `.env` trên server — **chỉ cần phần này**, không cần ANTHROPIC_API_KEY:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=host.docker.internal
POSTGRES_DB=your_db_name
```

```bash
# Khởi động stack (KHÔNG bao gồm ai-engine)
docker compose up -d prometheus grafana loki tempo alertmanager \
    otel-collector node-exporter postgres-exporter cadvisor

# Kiểm tra đã chạy chưa
docker compose ps
```

### Bước 1.3 — Kiểm tra server sẵn sàng

Truy cập từ trình duyệt (hoặc dùng curl):

```bash
# Prometheus đang chạy?
curl http://222.253.80.38:9090/-/healthy
# Kết quả mong đợi: "Prometheus Server is Healthy."

# Loki đang chạy?
curl http://222.253.80.38:3100/ready
# Kết quả mong đợi: "ready"
```

> ✅ Nếu trả về kết quả trên → **Server đã sẵn sàng**

### Bước 1.4 — Instrument ứng dụng của bạn (để có metrics)

Nếu ứng dụng chưa gửi metrics thì Prometheus chỉ monitor được infrastructure (CPU, RAM, Disk). Để monitor ứng dụng sâu hơn, thêm OTEL:

**Python (FastAPI):**
```python
# Xem file: instrumentation/python/telemetry.py
from instrumentation.python.telemetry import setup_telemetry
tracer, meter = setup_telemetry(app)
```

**.NET 9:**
```csharp
// Xem file: instrumentation/dotnet/ObservabilityExtensions.cs
builder.Services.AddObservability(builder.Configuration, "YourAppName");
```

> ⚠️ **Nếu bỏ qua bước này:** AI vẫn phân tích được CPU, RAM, Disk, Logs cơ bản — nhưng không có metrics ứng dụng (API latency, error rate, queue...).

---

## PHẦN 2 — MÁY CỦA BẠN CẦN LÀM GÌ?

Máy của bạn chạy **AI Engine** — đây là phần duy nhất cần Anthropic API / proxy URL.

### Bước 2.1 — Yêu cầu

| Yêu cầu | Kiểm tra |
|---------|---------|
| Python 3.10+ | `python --version` |
| Kết nối được đến server | `curl http://222.253.80.38:9090/-/healthy` |
| Proxy URL hoặc Anthropic API Key | Xem mục cấu hình |

### Bước 2.2 — Cấu hình

Mở file `ai-engine/.env` (copy từ `ai-engine/.env.example` nếu chưa có):

```env
# ── Chọn MỘT trong hai cách kết nối AI ──────────────────────

# CÁCH 1: Dùng proxy URL của bạn (đang cấu hình)
ANTHROPIC_BASE_URL=http://192.168.0.101:8000

# CÁCH 2: Dùng Anthropic API trực tiếp
# ANTHROPIC_API_KEY=sk-ant-...

# ── Server mặc định (server đầu tiên trong DB) ───────────────
PROMETHEUS_URL=http://222.253.80.38:9090
LOKI_URL=http://222.253.80.38:3100

# ── Cài đặt khác ─────────────────────────────────────────────
CLAUDE_MODEL=claude-sonnet-4-6
ANALYSIS_INTERVAL_SECONDS=300
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/...
AUTH_USERNAME=admin
AUTH_PASSWORD=@ISystemInt3llig3nc3Platf()rm
AUTH_SECRET_KEY=change-me-in-production-32chars!!
```

### Bước 2.3 — Khởi động AI Engine

**Windows:**
```cmd
cd D:\Work\AISystemIntelligencePlatform\ai-engine
start.bat
```

**Linux / macOS:**
```bash
cd /path/to/AISystemIntelligencePlatform/ai-engine
chmod +x start.sh
./start.sh
```

Script tự động:
1. Kiểm tra Python
2. Tạo virtual environment
3. Cài đặt dependencies
4. Khởi động server tại port 8765

### Bước 2.4 — Mở giao diện

Mở trình duyệt: **http://localhost:33898**

Đăng nhập:
- Username: `admin`
- Password: `@ISystemInt3llig3nc3Platf()rm`

---

## PHẦN 3 — SỬ DỤNG HÀNG NGÀY

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

## PHẦN 4 — NHẬN THÔNG BÁO GOOGLE CHAT

Khi có WARNING hoặc CRITICAL, hệ thống tự gửi thông báo vào Google Chat.

### Tạo webhook

1. Mở **Google Chat** → vào Space nhóm của bạn
2. Click tên Space → **Manage webhooks**
3. Click **Add webhook** → đặt tên `AI Monitor` → **Save**
4. Copy URL (dạng `https://chat.googleapis.com/v1/spaces/...`)

### Cấu hình

Điền vào `ai-engine/.env`:
```env
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/XXX/messages?key=...
```

Khởi động lại AI Engine. Test thử:
```bash
curl -X POST http://localhost:33898/api/notifications/test
```

---

## PHẦN 5 — THAY ĐỔI CẤU HÌNH

### Đổi mật khẩu đăng nhập

Sửa `ai-engine/.env`:
```env
AUTH_USERNAME=admin
AUTH_PASSWORD=mật_khẩu_mới
```
Khởi động lại AI Engine.

### Đổi tần suất phân tích

```env
ANALYSIS_INTERVAL_SECONDS=300   # 5 phút (mặc định)
ANALYSIS_INTERVAL_SECONDS=600   # 10 phút
ANALYSIS_INTERVAL_SECONDS=60    # 1 phút (tốn nhiều API token hơn)
```

### Đổi model Claude

```env
CLAUDE_MODEL=claude-haiku-4-5-20251001   # Nhanh, rẻ
CLAUDE_MODEL=claude-sonnet-4-6           # Cân bằng (mặc định)
CLAUDE_MODEL=claude-opus-4-6             # Chất lượng cao nhất
```

---

## PHẦN 6 — XỬ LÝ SỰ CỐ

### AI Engine không kết nối được server

```bash
# Kiểm tra từ máy của bạn
curl http://222.253.80.38:9090/-/healthy
# Nếu không trả về → port 9090 chưa mở trên server

# Mở port trên server (Ubuntu/Debian)
sudo ufw allow 9090
sudo ufw allow 3100
```

### AI trả lời "không có dữ liệu"

Nguyên nhân: Prometheus chưa scrape được ứng dụng.

```bash
# Kiểm tra Prometheus targets
curl http://222.253.80.38:9090/api/v1/targets

# Tìm targets có "health": "down"
# → Kiểm tra ứng dụng có expose /metrics chưa
```

### AI Engine không start

```bash
# Xem lỗi chi tiết
python main.py

# Lỗi thường gặp:
# "Phải cấu hình ít nhất một trong hai..."
#   → Chưa set ANTHROPIC_BASE_URL hoặc ANTHROPIC_API_KEY trong .env

# "Connection refused"
#   → PROMETHEUS_URL sai hoặc server chưa chạy
```

### Xem logs chi tiết

```bash
# Nếu chạy bằng script
# Log in ra terminal trực tiếp

# Nếu chạy bằng Docker
docker compose logs ai-engine -f
```

---

## Tóm tắt ports cần biết

| Service | Port | Chạy ở đâu | Dùng để |
|---------|------|-----------|---------|
| **AI Engine UI** | **33898** | **Máy bạn** | **Xem dashboard** |
| Prometheus | 9090 | Server | Thu thập metrics |
| Loki | 3100 | Server | Thu thập logs |
| Grafana | 3000 | Server | Dashboard thô |
| AlertManager | 9093 | Server | Quản lý alerts |
| OTEL Collector | 4317/4318 | Server | Nhận telemetry từ app |

---

*AI System Intelligence Platform v2.0*
