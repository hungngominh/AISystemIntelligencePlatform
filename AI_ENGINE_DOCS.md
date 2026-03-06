# AI System Intelligence Platform — Tài liệu đầy đủ

> **Phiên bản**: 2.0.0
> **Cập nhật**: 2026-03-05
> **Tác giả**: AI Engine Team

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Các thành phần](#3-các-thành-phần)
4. [Hướng dẫn cài đặt](#4-hướng-dẫn-cài-đặt)
5. [Cấu hình](#5-cấu-hình)
6. [Hướng dẫn sử dụng](#6-hướng-dẫn-sử-dụng)
7. [API Reference](#7-api-reference)
8. [Google Chat Integration](#8-google-chat-integration)
9. [Troubleshooting](#9-troubleshooting)
10. [Phát triển thêm](#10-phát-triển-thêm)

---

## 1. Tổng quan

**AI System Intelligence Platform** là hệ thống giám sát server thông minh, tích hợp AI (Claude) để tự động phân tích trạng thái hệ thống, phát hiện sự cố và đề xuất giải pháp.

### Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| **Phân tích tự động** | AI phân tích metrics + logs mỗi 5 phút (cấu hình được) |
| **Alert Analysis** | Khi có alert → AI giải thích nguyên nhân + runbook |
| **Chat interface** | Hỏi AI về bất kỳ vấn đề server nào |
| **Google Chat notify** | Gửi cảnh báo qua Google Chat khi WARNING/CRITICAL |
| **Web Dashboard** | Giao diện xem lịch sử phân tích |
| **Cross-platform** | Chạy trên Windows và Linux/macOS |

### Stack công nghệ

**Observability Stack** (đã có từ v1.0):
- Prometheus, Grafana, Loki, Tempo, AlertManager, OTEL Collector

**AI Engine** (mới trong v2.0):
- Python 3.10+, FastAPI, APScheduler, SQLite, Anthropic Claude API

---

## 2. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│  Backend Systems (applications bạn monitor)          │
│  • AIProjectMiddleware (.NET 9) :5000/metrics        │
│  • multiAIAgents (Python)       :8000/metrics        │
└────────────────────┬────────────────────────────────┘
                     │ OTLP (gRPC :4317 / HTTP :4318)
                     ▼
            ┌─────────────────┐
            │  OTEL Collector │
            └────┬────┬───────┘
                 │    │
       ┌─────────┘    └────────┐
       ▼                       ▼
  Prometheus              Loki (logs)
  (metrics)          ┌────────────────┐
       │             │  Tempo (traces) │
       │             └────────────────┘
       │
  AlertManager ──────┐
       │             │ webhook
       ▼             ▼
   Grafana    ┌──────────────────────────────┐
  (dashboards)│       AI ENGINE (mới)        │
              │                              │
              │  ┌──────────────────────┐    │
              │  │ Scheduler (5 phút)   │    │
              │  │  ↓ collect metrics   │    │
              │  │  ↓ call Claude API   │    │
              │  │  ↓ save to SQLite    │    │
              │  │  ↓ notify if needed  │    │
              │  └──────────────────────┘    │
              │                              │
              │  ┌──────────────────────┐    │
              │  │ Web UI (:8765)       │    │
              │  │  • Dashboard         │    │
              │  │  • Chat with AI      │    │
              │  │  • Alert details     │    │
              │  └──────────────────────┘    │
              │                              │
              │  Claude API ←→ AI Engine     │
              └──────────────────────────────┘
                           │
                           ▼
                    Google Chat
                   (notifications)
```

### Luồng dữ liệu chi tiết

#### Luồng 1: Phân tích định kỳ
```
1. APScheduler kích hoạt mỗi N giây (mặc định 300s)
2. Collector gọi Prometheus HTTP API (instant queries)
3. Collector gọi Loki HTTP API (recent errors)
4. Data được format thành text dễ đọc
5. Gửi đến Claude API với system prompt SRE expert
6. Claude trả về Markdown report + status (OK/WARNING/CRITICAL)
7. Lưu vào SQLite
8. Nếu status != OK → gửi Google Chat notification
```

#### Luồng 2: Alert webhook
```
1. Prometheus phát hiện rule violation
2. AlertManager nhận alert
3. AlertManager POST đến /api/webhooks/alertmanager
4. AI Engine thu thập metrics tại thời điểm alert
5. Claude phân tích nguyên nhân + đề xuất runbook
6. Lưu DB + gửi Google Chat
```

#### Luồng 3: Chat
```
1. User gõ câu hỏi trên web UI
2. API lấy chat history từ SQLite
3. Lấy metrics snapshot gần nhất (cached)
4. Gửi đến Claude với context đầy đủ
5. Trả về response, lưu history
```

---

## 3. Các thành phần

### 3.1 AI Engine (`ai-engine/`)

```
ai-engine/
├── main.py              # Entry point, uvicorn server
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build
├── .env.example         # Template cấu hình
├── start.sh             # Start script (Linux/macOS)
├── start.bat            # Start script (Windows)
├── data/                # SQLite database (auto-created)
│   └── ai_engine.db
└── src/
    ├── config.py        # Pydantic settings từ .env
    ├── database.py      # SQLite operations (sqlite-utils)
    ├── collector.py     # Thu thập metrics từ Prometheus + Loki
    ├── analyzer.py      # Gọi Claude API để phân tích
    ├── scheduler.py     # APScheduler định kỳ
    ├── notifier.py      # Gửi Google Chat notification
    ├── api.py           # FastAPI routes
    └── ui.py            # HTML Web UI
```

### 3.2 Database Schema

**Bảng `analyses`**:
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER | Primary key, auto-increment |
| created_at | TEXT | ISO8601 UTC timestamp |
| analysis_type | TEXT | `periodic` / `alert` / `chat` |
| status | TEXT | `ok` / `warning` / `critical` / `error` |
| summary | TEXT | Tóm tắt 1 dòng |
| full_report | TEXT | Markdown report đầy đủ |
| raw_metrics | TEXT | JSON metrics đã thu thập |
| alert_name | TEXT | Tên alert (nếu là alert analysis) |
| tokens_used | INTEGER | Số token Claude đã dùng |

**Bảng `chat_messages`**:
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER | Primary key |
| session_id | TEXT | UUID session |
| role | TEXT | `user` / `assistant` |
| content | TEXT | Nội dung message |
| created_at | TEXT | ISO8601 UTC timestamp |

### 3.3 Metrics thu thập

AI Engine thu thập 17 nhóm metrics song song:

| Nhóm | Metrics | Nguồn |
|------|---------|-------|
| Infrastructure | CPU%, Memory%, Disk% | Prometheus/node-exporter |
| API | p95 latency, error rate, RPS | Prometheus/OTEL |
| Queue | Backlog size by queue name | Prometheus |
| AI Costs | Cost/hour, tokens/hour, GPT latency | Prometheus |
| Database | Lock counts by mode | Prometheus/pg-exporter |
| Targets | Health của tất cả scrape targets | Prometheus targets API |
| Active Alerts | Alerts đang firing | Prometheus alerts API |
| Recent Errors | Error logs 15 phút qua | Loki |
| Containers | CPU + Memory per container | Prometheus/cadvisor |

---

## 4. Hướng dẫn cài đặt

### Yêu cầu

| Component | Phiên bản tối thiểu |
|-----------|---------------------|
| Docker + Docker Compose | Docker 24.0+, Compose v2 |
| Python (chạy ngoài Docker) | 3.10+ |
| Anthropic API Key | Bắt buộc |

### Cài đặt với Docker (khuyến nghị)

#### Bước 1: Cấu hình `.env`
```bash
# Mở file .env ở root project
# Điền giá trị thực:
ANTHROPIC_API_KEY=sk-ant-...   # Bắt buộc
GOOGLE_CHAT_WEBHOOK_URL=...    # Tùy chọn, để nhận thông báo
```

#### Bước 2: Khởi động toàn bộ stack
```bash
# Từ thư mục gốc (D:\Work\AISystemIntelligencePlatform)
docker compose up -d
```

#### Bước 3: Kiểm tra
```bash
docker compose ps
# Tất cả services phải có status "Up"

# Kiểm tra AI Engine logs
docker compose logs ai-engine -f
```

#### Bước 4: Truy cập

| Service | URL | Thông tin |
|---------|-----|-----------|
| **AI Engine Dashboard** | http://localhost:8765 | Username/Password không cần |
| **Grafana** | http://localhost:3000 | admin / admin123 |
| **Prometheus** | http://localhost:9090 | - |
| **AlertManager** | http://localhost:9093 | - |

---

### Cài đặt chỉ AI Engine (không Docker)

#### Windows
```cmd
cd D:\Work\AISystemIntelligencePlatform\ai-engine
start.bat
```
Script sẽ tự động:
1. Tạo file `.env` từ `.env.example` nếu chưa có
2. Mở Notepad để điền config
3. Tạo Python virtual environment
4. Cài dependencies
5. Khởi động server

#### Linux / macOS
```bash
cd /path/to/AISystemIntelligencePlatform/ai-engine
chmod +x start.sh
./start.sh
```

---

## 5. Cấu hình

### Biến môi trường AI Engine

| Biến | Mặc định | Mô tả |
|------|---------|-------|
| `ANTHROPIC_API_KEY` | *bắt buộc* | API key từ console.anthropic.com |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Model Claude dùng để phân tích |
| `PROMETHEUS_URL` | `http://localhost:9090` | URL Prometheus |
| `LOKI_URL` | `http://localhost:3100` | URL Loki |
| `ALERTMANAGER_URL` | `http://localhost:9093` | URL AlertManager |
| `AI_ENGINE_HOST` | `0.0.0.0` | Bind host |
| `AI_ENGINE_PORT` | `8765` | Port Web UI + API |
| `ANALYSIS_INTERVAL_SECONDS` | `300` | Tần suất phân tích (giây) |
| `GOOGLE_CHAT_WEBHOOK_URL` | *(trống)* | Webhook URL Google Chat |
| `LOG_LEVEL` | `INFO` | Level logging |
| `DB_PATH` | `./data/ai_engine.db` | Đường dẫn SQLite |

### Điều chỉnh tần suất phân tích

Để phân tích mỗi 10 phút thay vì 5 phút:
```env
ANALYSIS_INTERVAL_SECONDS=600
```

Để phân tích mỗi 1 phút (chú ý chi phí API):
```env
ANALYSIS_INTERVAL_SECONDS=60
```

### Chọn model Claude

| Model | Tốc độ | Chất lượng | Chi phí |
|-------|--------|-----------|---------|
| `claude-haiku-4-5-20251001` | Nhanh nhất | Tốt | Thấp nhất |
| `claude-sonnet-4-6` | Cân bằng | Rất tốt | Trung bình |
| `claude-opus-4-6` | Chậm hơn | Tốt nhất | Cao nhất |

---

## 6. Hướng dẫn sử dụng

### Dashboard chính (http://localhost:8765)

```
┌─────────────────────────────────────────────────┐
│  🤖 AI Monitor    [Dashboard] [Chat]   [▶ Phân tích ngay]  │
├─────────────────────────────────────────────────┤
│  ✅ HỆ THỐNG BÌNH THƯỜNG                         │
│  "Tất cả metrics trong ngưỡng bình thường..."   │
│  2026-03-05 10:30:00 UTC          [💬 Hỏi AI]   │
├──────┬──────┬──────┬──────────────────────────  │
│ 30   │ 25   │  4   │  1                          │
│ Tổng │ OK   │ Warn │ Critical                    │
├─────────────────────────────────────────────────┤
│  Lịch sử phân tích                               │
│  #30  ✅ OK   "Bình thường"   Định kỳ  10:30     │
│  #29  ⚠️ WARN  "Queue cao"    Định kỳ  10:25     │
│  #28  🚨 CRIT  "DB locks"     Alert    10:20     │
│  ...                                             │
└─────────────────────────────────────────────────┘
```

**Các thao tác**:
- Click vào dòng trong bảng → xem báo cáo chi tiết
- Nhấn "Phân tích ngay" → kích hoạt phân tích tức thì
- Dashboard tự refresh mỗi 30 giây

### Xem chi tiết phân tích

Click vào bất kỳ dòng nào → trang chi tiết:
- **Tab "Báo cáo AI"**: Markdown report từ Claude, format rõ ràng
- **Tab "Raw Metrics"**: JSON data đã thu thập để debug

### Chat với AI (http://localhost:8765/chat)

Các câu hỏi gợi ý:
- "Tóm tắt trạng thái server"
- "CPU và memory đang như thế nào?"
- "Có alert nào đang active không?"
- "Chi phí AI trong 1 giờ qua là bao nhiêu?"
- "Có lỗi nào trong logs gần đây không?"
- "Tại sao CPU spike lên 90%?"
- "Queue backlog đang bao nhiêu?"

AI có đầy đủ context về metrics hiện tại để trả lời chính xác.

### Kích hoạt phân tích thủ công

Qua UI: Nhấn nút "▶ Phân tích ngay" trên navbar

Qua API:
```bash
curl -X POST http://localhost:8765/api/analyses/trigger
```

### Kiểm tra webhook Google Chat

```bash
curl -X POST http://localhost:8765/api/notifications/test
```

---

## 7. API Reference

### GET `/health`
Kiểm tra AI Engine còn sống.
```json
{"status": "ok", "timestamp": "2026-03-05T10:30:00+00:00"}
```

### GET `/api/analyses?limit=20&type=periodic`
Lấy danh sách phân tích.
- `limit`: số lượng (mặc định 20)
- `type`: `periodic` | `alert` | `chat` (tùy chọn)

### GET `/api/analyses/{id}`
Chi tiết một phân tích.

### POST `/api/analyses/trigger`
Kích hoạt phân tích ngay lập tức (chạy background).

### GET `/api/metrics/snapshot`
Metrics snapshot được cache từ lần thu thập gần nhất.

### POST `/api/metrics/collect`
Thu thập metrics ngay (không phân tích AI).

### POST `/api/webhooks/alertmanager`
Webhook nhận alerts từ AlertManager. Payload format: AlertManager webhook v1.

### POST `/api/chat`
Chat với AI.
```json
// Request
{"message": "CPU đang như thế nào?", "session_id": "abc123"}

// Response
{"session_id": "abc123", "response": "...", "tokens_used": 350}
```

### POST `/api/notifications/test`
Gửi thông báo test.

---

## 8. Google Chat Integration

### Bước 1: Tạo Webhook trong Google Chat

1. Mở Google Chat, vào Space (nhóm) muốn nhận thông báo
2. Click tên Space → **Manage webhooks**
3. Click **Add webhook**
4. Đặt tên: "AI Monitor" → **Save**
5. Copy URL webhook (dạng `https://chat.googleapis.com/v1/spaces/...`)

### Bước 2: Cấu hình

```env
# Trong file .env
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/XXXX/messages?key=...
```

### Bước 3: Test

```bash
curl -X POST http://localhost:8765/api/notifications/test
```

### Format thông báo

Thông báo Google Chat dùng **Card v2 format** với:
- Header: emoji status + tên alert/report
- Section "Summary": tóm tắt 1 dòng
- Section "AI Analysis": nội dung đầy đủ (có thể collapse)
- Button "Xem chi tiết": link đến AI Engine dashboard

**Ví dụ thông báo WARNING**:
```
⚠️ AI Server Report — WARNING
AI System Intelligence Platform

📋 Summary
Queue backlog cao: 150 items trong queue "invoice-processing"

📊 AI Analysis (thu gọn)
## Vấn đề phát hiện
- Queue backlog: 150 items (ngưỡng: 100)
- OCR processing chậm: p95 = 45s
...

[Xem chi tiết]
```

---

## 9. Troubleshooting

### AI Engine không start

```bash
# Kiểm tra logs
docker compose logs ai-engine

# Lỗi thường gặp:
# "ANTHROPIC_API_KEY not set" → Điền API key vào .env
# "Connection refused to prometheus:9090" → Start Prometheus trước
```

### Không nhận được thông báo Google Chat

1. Kiểm tra webhook URL đúng trong `.env`
2. Test thủ công: `curl -X POST http://localhost:8765/api/notifications/test`
3. Xem logs: `docker compose logs ai-engine | grep "Google Chat"`

### AI phân tích không chính xác

AI chỉ phân tích được khi có dữ liệu từ Prometheus và Loki. Nếu applications chưa được instrument:
- Metrics sẽ là `null` → AI sẽ ghi "không có dữ liệu"
- Thêm OTEL instrumentation vào app (xem `instrumentation/` folder)

### Metrics null tất cả

```bash
# Kiểm tra Prometheus scrape targets
curl http://localhost:9090/api/v1/targets | python -m json.tool

# Nếu tất cả "down" → services chưa expose /metrics
```

### Lỗi "Too many tokens"

Giảm số lỗi logs gửi đến AI (trong `collector.py`, dòng `limit=30`):
```python
loki.query_recent_errors(minutes=15, limit=10)  # giảm xuống 10
```

---

## 10. Phát triển thêm

### Thêm kênh thông báo mới (Slack, Email, etc.)

Thêm vào `src/notifier.py`:
```python
async def _send_slack(status, summary, report, ...):
    payload = {"text": f"*{status.upper()}* {summary}\n{report[:500]}"}
    async with httpx.AsyncClient() as client:
        await client.post(settings.slack_webhook_url, json=payload)
```

Thêm vào `send_notification()`:
```python
if settings.slack_webhook_url:
    tasks.append(_send_slack(...))
```

### Thêm metrics mới vào phân tích

Thêm query vào `src/collector.py` trong `collect_all_metrics()`:
```python
prom.query("your_custom_metric_name"),
```

Thêm vào `_format_metrics_for_prompt()` trong `src/analyzer.py`:
```python
lines.append(f"- Custom metric: {metrics['custom']['value']}")
```

### Lên lịch phân tích theo giờ cao điểm

Sửa `src/scheduler.py`:
```python
from apscheduler.triggers.cron import CronTrigger

# Phân tích mỗi 1 phút trong giờ cao điểm (8-18h)
scheduler.add_job(run_periodic_analysis, CronTrigger(
    minute="*/1", hour="8-18"
))
# Phân tích mỗi 10 phút ngoài giờ
scheduler.add_job(run_periodic_analysis, CronTrigger(
    minute="*/10", hour="0-7,19-23"
))
```

---

## Tóm tắt ports

| Port | Service | URL |
|------|---------|-----|
| **8765** | **AI Engine** | **http://localhost:8765** |
| 3000 | Grafana | http://localhost:3000 |
| 9090 | Prometheus | http://localhost:9090 |
| 9093 | AlertManager | http://localhost:9093 |
| 3100 | Loki | http://localhost:3100 |
| 3200 | Tempo | http://localhost:3200 |
| 4317 | OTEL gRPC | - |
| 4318 | OTEL HTTP | - |
| 9100 | node-exporter | - |
| 9187 | postgres-exporter | - |
| 8080 | cadvisor | - |

---

*AI System Intelligence Platform v2.0 — Built with Claude AI*
