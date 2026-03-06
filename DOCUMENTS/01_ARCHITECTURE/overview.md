# Kiến Trúc Tổng Quan - AI System Intelligence Platform

> **Platform**: Observability Stack cho AI Backend Systems
> **Version**: 1.0.0
> **Status**: Production Ready
> **Last Updated**: 2026-03-04

---

## Mục lục

1. [Tổng quan hệ thống](#tổng-quan-hệ-thống)
2. [Các thành phần chính](#các-thành-phần-chính)
3. [Data Flow](#data-flow)
4. [Mục tiêu quan sát](#mục-tiêu-quan-sát)
5. [SLO & Alerts](#slo--alerts)

---

## Tổng quan hệ thống

**AI System Intelligence Platform** là một stack observability containerized, được thiết kế để giám sát hai hệ thống backend:

- **AIProjectMiddleware** (.NET 9 Web API, PostgreSQL, Redis)
- **multiAIAgents** (Python CrewAI agents, GPT inference)

### Mục đích

Cung cấp **full-stack observability** qua:
- **Metrics**: Thời gian thực hiện, tỷ lệ lỗi, chi phí AI
- **Logs**: Tập trung logs từ tất cả services
- **Traces**: Theo dõi request path end-to-end
- **Alerts**: Thông báo tự động khi vi phạm SLO

### Stack công nghệ

| Component | Phiên bản | Mục đích |
|-----------|----------|---------|
| **Prometheus** | v2.50.0 | Time-series metrics database |
| **Grafana** | v10.3.0 | Dashboards & visualization |
| **Loki** | v2.9.0 | Log aggregation with LogQL |
| **Tempo** | v2.4.0 | Distributed traces (TraceQL) |
| **OTEL Collector** | v0.96.0 | Telemetry routing (OTLP) |
| **AlertManager** | v0.26.0 | Alert routing & webhooks |
| **node-exporter** | v1.7.0 | OS metrics collection |
| **postgres-exporter** | v0.15.0 | PostgreSQL metrics |
| **cadvisor** | v0.47.0 | Container resource metrics |

---

## Các thành phần chính

### 1. OTEL Collector (Telemetry Gateway)

**Chức năng**: Nhận OTLP telemetry từ applications, xử lý, và route đến backends

```
Applications (OTLP gRPC/HTTP)
    ↓ :4317, :4318
OTEL Collector
    ↓ (batch, memory_limiter, resource processors)
    ├→ Prometheus (metrics)
    ├→ Tempo (traces)
    └→ Loki (logs)
```

**Config**: `config/otel-collector/otel-collector-config.yaml`

### 2. Prometheus (Metrics Database)

**Chức năng**: Lưu trữ time-series metrics, đánh giá alert rules, phục vụ queries

**Scrape Targets** (từ `config/prometheus/prometheus.yml`):
- `prometheus:9090` - Self-monitoring
- `node-exporter:9100` - OS metrics
- `cadvisor:8080` - Container metrics
- `postgres-exporter:9187` - DB metrics
- `otel-collector:8889` - Application metrics
- `dotnet-api:5000/metrics` - .NET application
- `fastapi:8000/metrics` - Python application

**Data Retention**: 30 days

### 3. Grafana (Visualization)

**Chức năng**: Dashboards, alerts configuration, trace analysis

**Pre-built Dashboards** (auto-provisioned):
- Executive Dashboard (KPIs)
- Application Dashboard (Performance)
- Technical Dashboard (Infrastructure)

**Datasources** (pre-configured):
- Prometheus
- Loki
- Tempo (with trace-to-logs correlation)

### 4. Loki (Log Aggregation)

**Chức năng**: Centralized log storage with LogQL queries

**Data Retention**: 7 days

**Features**:
- Structured log ingestion via OTLP
- LogQL queries
- Trace-to-logs correlation

### 5. Tempo (Distributed Tracing)

**Chức năng**: Stores traces, supports TraceQL queries

**Data Retention**: 2 days

**Integration**:
- Receives traces via OTLP (from OTEL Collector)
- Links to Prometheus metrics
- Links to Loki logs
- Service dependency mapping

---

## Data Flow

```
┌─────────────────────────────────────┐
│  Backend Systems                    │
├─────────────────────────────────────┤
│ • AIProjectMiddleware (.NET 9)      │ :5000/metrics
│ • multiAIAgents (Python CrewAI)     │ :8000/metrics
└──────────────┬──────────────────────┘
               │
        OTLP gRPC (:4317)
        OTLP HTTP (:4318)
               │
        ┌──────▼──────────────┐
        │  OTEL Collector     │
        │  (processors)       │
        └──────┬──────────────┘
               │
     ┌─────────┼─────────┐
     │         │         │
     ▼         ▼         ▼
Prometheus  Tempo      Loki
(metrics)   (traces)   (logs)
     │         │         │
     └─────────┼─────────┘
               │
           Grafana
       (dashboards)
               │
          AlertManager
        (routing/webhooks)
```

---

## Mục tiêu quan sát

### Layers quan sát

| Layer | Metrics | Sources |
|-------|---------|---------|
| **Application** | API latency, errors, costs | OTEL instrumentation |
| **Pipeline** | OCR/GPT/JSON processing | Custom metrics |
| **Infrastructure** | CPU, memory, disk, network | node-exporter, cadvisor |
| **Database** | Connections, locks, transactions | postgres-exporter |
| **Observability Stack** | Collector, Prometheus, Loki health | Self-monitoring |

### Core Metrics (15+)

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `api_request_duration_seconds` | Histogram | endpoint, method, status | API latency analysis |
| `api_requests_total` | Counter | endpoint, method, status | API throughput |
| `pipeline_processing_seconds` | Histogram | stage, document_type | Pipeline latency breakdown |
| `ocr_processing_seconds` | Histogram | document_type | OCR performance |
| `gpt_inference_seconds` | Histogram | model | GPT API latency |
| `ai_tokens_total` | Counter | model, token_type | Token consumption |
| `ai_cost_usd_total` | Counter | model, service | AI cost tracking |
| `queue_backlog_size` | Gauge | queue_name | Queue saturation |
| `async_task_duration_seconds` | Histogram | task_type | Background job performance |
| `pg_locks_count` | Gauge | mode | Database health |

---

## SLO & Alerts

### SLO Targets (5 services)

| Service | Metric | Target | Error Budget/Month |
|---------|--------|--------|---------------------|
| **API** | Availability | 99.9% | 43.2 minutes |
| **API** | p95 Latency | < 2s | 0.1% violation |
| **Pipeline** | Success Rate | > 99% | 1% failure |
| **OCR** | p95 Latency | < 30s | 0.1% violation |
| **GPT** | p95 Inference | < 60s | 0.1% violation |

### Alert Rules (8 configured)

| Alert | Condition | Duration | Severity |
|-------|-----------|----------|----------|
| HighAPILatency | p95 > 2s | 5m | warning |
| HighErrorRate | > 1% | 3m | critical |
| QueueBacklogHigh | > 100 items | 2m | warning |
| GPTCostSpike | > $50/hr | 5m | warning |
| DBLockAnomaly | > 50 locks | 1m | critical |
| ServiceDown | up == 0 | 1m | critical |
| GPTInferenceSlowdown | p95 > 30s | 3m | warning |
| PipelineSuccessRateLow | < 99% | 5m | critical |

---

## Liên kết

- 📁 **Project Structure**: [project-structure.md](./project-structure.md)
- 📊 **Database Design**: [database-design.md](./database-design.md)
- 🚀 **Deployment**: [deployment.md](./deployment.md)
- 📈 **Recording Rules**: config/prometheus/rules/recording_rules.yml
- 🚨 **Alert Rules**: config/prometheus/rules/alert_rules.yml

---

*Cập nhật lần cuối: 2026-03-04*
