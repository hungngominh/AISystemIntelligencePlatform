# AI System Intelligence Platform — Observability Architecture

## Overview

The **AISystemIntelligencePlatform** provides a next-generation monitoring and observability stack for two existing backend systems:

- **AIProjectMiddleware** (.NET 9 Web API, PostgreSQL, Redis)
- **multiAIAgents** (Python CrewAI agents, GPT inference via langchain-openai)

This platform is built on industry-standard technologies: Prometheus, Grafana, Loki, Tempo, OpenTelemetry, and AlertManager — all containerized via Docker Compose for easy deployment.

---

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- AIProjectMiddleware running on `localhost:5000` (or configure in `.env`)
- multiAIAgents/FastAPI running on `localhost:8000` (or configure in `.env`)

### 2. Start the Stack

```bash
cd /d/Work/AISystemIntelligencePlatform
docker compose up -d
```

### 3. Verify Services

| Service | URL | Purpose |
|---------|-----|---------|
| Grafana | http://localhost:3000 | Dashboards (admin/admin123) |
| Prometheus | http://localhost:9090 | Metrics database |
| Loki | http://localhost:3100 | Log aggregation |
| Tempo | http://localhost:3200 | Trace storage |
| AlertManager | http://localhost:9093 | Alert routing |
| OTEL Collector | :4317/:4318 | Telemetry ingestion (gRPC/HTTP) |

---

## Architecture

### Data Flow

```
Services (FastAPI / .NET)
        │
        │  OTLP (gRPC :4317)
        ▼
  OTEL Collector
  ┌─────────────┐
  │ Receivers   │◄── OTLP traces, metrics, logs
  │ Processors  │   (batch, memory_limiter, resource)
  │ Exporters   │
  └──────┬──────┘
         │
    ┌────┴─────────────┐
    │                  │
    ▼                  ▼                  ▼
Prometheus          Tempo              Loki
(metrics)          (traces)           (logs)
    │                  │                  │
    └──────────────────┼──────────────────┘
                       │
                   Grafana
              (unified UI layer)
                       │
                  AlertManager
              (routing + notifications)

node-exporter ──► Prometheus (OS metrics)
postgres-exporter ► Prometheus (DB metrics)
cadvisor ──────► Prometheus (container metrics)
```

---

## Instrumentation

### .NET 9 Integration

Add to your `Program.cs`:

```csharp
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");

// Then expose /metrics endpoint
app.UseOpenTelemetryPrometheusScrapingEndpoint();
```

See `instrumentation/dotnet/ObservabilityExtensions.cs` for full implementation.

### Python FastAPI Integration

In your FastAPI application:

```python
from instrumentation.python.telemetry import setup_telemetry

app = FastAPI()
tracer, meter = setup_telemetry(app)
```

Then use metrics in your handlers:

```python
from instrumentation.python.metrics import measure_pipeline_stage, record_gpt_usage

# Pipeline processing
with measure_pipeline_stage("ocr", {"document_type": "invoice"}):
    # OCR logic here
    pass

# GPT usage
record_gpt_usage(
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=50,
    cost_usd=0.003,
    service="ai-agents",
    client_id="client-123"
)
```

---

## Key Metrics

### API & HTTP

| Metric | Type | Labels |
|--------|------|--------|
| `api_request_duration_seconds` | Histogram | endpoint, method, status, service |
| `api_requests_total` | Counter | endpoint, method, status, service |

### Pipeline & AI

| Metric | Type | Labels |
|--------|------|--------|
| `pipeline_processing_seconds` | Histogram | stage, document_type, status |
| `pipeline_completed_total` | Counter | status, document_type |
| `ocr_processing_seconds` | Histogram | document_type, solution, status |
| `gpt_inference_seconds` | Histogram | model, prompt_type, status |
| `ai_tokens_total` | Counter | model, token_type, service, client_id |
| `ai_cost_usd_total` | Counter | model, service, client_id |

### Async & Queueing

| Metric | Type | Labels |
|--------|------|--------|
| `queue_backlog_size` | Gauge | queue_name, priority |
| `queue_capacity_total` | Gauge | queue_name |
| `async_task_duration_seconds` | Histogram | task_type, worker_id, status |

### Database

| Metric | Type | Labels |
|--------|------|--------|
| `db_query_duration_seconds` | Histogram | operation, table, status |
| `pg_locks_count` | Gauge | mode |
| `pg_stat_database_xact_*` | Counter | (DB transaction stats) |

---

## Dashboards

### Executive Dashboard
**Location:** http://localhost:3000/d/executive-dashboard

Metrics:
- Service uptime (gauge)
- Total errors (24h) — big number
- AI cost today — big number with USD unit
- Pipeline success rate (gauge)
- AI cost trend (7d) by service — pie chart

**Audience:** Leadership, Product Managers

---

### Application Dashboard
**Location:** http://localhost:3000/d/application-dashboard

Metrics:
- API request rate by endpoint (time series)
- API latency: p50/p95/p99 by endpoint (time series)
- Error rate by endpoint (heatmap-ready)
- Queue backlog (stat + time series)
- Pipeline stage latency breakdown (p95) — bar chart
- Async task duration (p95) by task_type (time series)
- Active workers (stat)

**Audience:** Platform Engineers, Oncall Engineers

---

### Technical Dashboard
**Location:** http://localhost:3000/d/technical-dashboard

Metrics:
- CPU usage (time series)
- Memory usage (time series)
- Disk I/O (time series, read/write)
- Network traffic (time series, in/out)
- DB locks (stat + by mode)
- DB transaction rate (commits/rollbacks)
- Thread pool queue depth (dotnet)
- GC pause time (dotnet)

**Audience:** Infrastructure Engineers, SREs

---

## SLO Definitions

| Service | Metric | SLO Target | Error Budget (30d) |
|---------|--------|------------|---------------------|
| API Availability | `up` | 99.9% | 43.2 min/month |
| API p95 Latency | `api_request_duration_seconds` p95 | < 2s | 0.1% violation |
| Pipeline Success Rate | `pipeline_completed_total{status="success"}` | > 99% | 1% failure rate |
| OCR p95 Latency | `ocr_processing_seconds` p95 | < 30s | 0.1% violation |
| GPT Inference p95 | `gpt_inference_seconds` p95 | < 60s | 0.1% violation |

---

## PromQL Query Examples

### API Performance
```promql
# p95 latency by endpoint
histogram_quantile(0.95,
  sum(rate(api_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# Error rate
sum(rate(api_requests_total{status=~"5.."}[5m])) by (endpoint)
/ sum(rate(api_requests_total[5m])) by (endpoint)

# SLO compliance: % requests under 2s
sum(rate(api_request_duration_seconds_bucket{le="2"}[1h]))
/ sum(rate(api_request_duration_seconds_count[1h]))
```

### Pipeline & AI
```promql
# Pipeline stage breakdown (p95)
histogram_quantile(0.95,
  sum(rate(pipeline_processing_seconds_bucket[5m])) by (le, stage)
)

# AI cost per day by service
sum(increase(ai_cost_usd_total[24h])) by (service)

# GPT token burn rate
sum(rate(ai_tokens_total{model=~"gpt.*"}[1h])) by (service) * 3600

# Error budget burn rate (30-day SLO: 99.9%)
(1 - (
  sum(rate(api_requests_total{status!~"5.."}[1h])) /
  sum(rate(api_requests_total[1h]))
)) / (1 - 0.999)
```

### Infrastructure
```promql
# Queue saturation
queue_backlog_size / queue_capacity_total > 0.8

# DB lock anomaly
pg_locks_count > avg_over_time(pg_locks_count[1h]) * 3

# Memory pressure
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.2
```

---

## LogQL Examples (Loki)

```logql
# All errors in last 1h
{service="ai-api"} |= "ERROR" | json | line_format "{{.message}}"

# Slow GPT requests (> 30s)
{service="ai-pipeline"} | json | duration > 30s | logfmt

# Correlate logs with trace
{service="ai-api"} | json | traceID = "abc123xyz"

# Pipeline errors by document type
{job="document-processor"} |= "pipeline_error" | json | document_type != ""
  | stats by (document_type) count() as error_count
```

---

## Alert Rules

### Critical Alerts
- **HighErrorRate**: Error rate > 1% for 3 minutes
- **ServiceDown**: Service up==0 for 1 minute
- **DBLockAnomaly**: Lock count > 50 for 1 minute
- **PipelineSuccessRateLow**: Success rate < 99% for 5 minutes

### Warning Alerts
- **HighAPILatency**: p95 latency > 2s for 5 minutes
- **QueueBacklogHigh**: Queue depth > 100 for 2 minutes
- **GPTCostSpike**: Cost > $50/hour for 5 minutes
- **GPTInferenceSlowdown**: p95 > 30s for 3 minutes

---

## Configuration

### `.env` Environment Variables

```bash
# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=ai-platform

# Grafana
GF_SECURITY_ADMIN_PASSWORD=admin123
GF_FEATURE_TOGGLES_ENABLE=traceqlEditor

# PostgreSQL (for postgres-exporter)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=host.docker.internal
POSTGRES_DB=aiprojmiddleware
```

### Prometheus Config Updates

To scrape your services, ensure they expose metrics:

- **.NET 9 API** → `http://localhost:5000/metrics` (prometheus-net)
- **FastAPI** → `http://localhost:8000/metrics` (prometheus-client)

Both are pre-configured in `config/prometheus/prometheus.yml`.

---

## Alerting Webhooks

Edit `config/alertmanager/alertmanager.yml` to configure webhook destinations:

```yaml
receivers:
  - name: 'critical-channel'
    webhook_configs:
      - url: 'http://your-slack-webhook-url'

  - name: 'ai-team-channel'
    webhook_configs:
      - url: 'http://your-pagerduty-webhook-url'
```

---

## Troubleshooting

### No metrics appearing in Prometheus

1. Verify services are running and exposing `/metrics` endpoints
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify scrape config in `config/prometheus/prometheus.yml`
4. Check service logs for export errors

### No traces in Tempo

1. Verify OTEL_EXPORTER_OTLP_ENDPOINT is set in service environment
2. Check OTEL Collector logs: `docker logs otel-collector`
3. Verify services are sending OTLP (port 4317 for gRPC, 4318 for HTTP)

### Dashboard panels showing "No data"

1. Verify metric names match exactly (case-sensitive)
2. Check PromQL expressions in Prometheus UI first
3. Ensure time range covers when metrics were emitted

---

## Retention & Storage

| Component | Retention | Storage |
|-----------|-----------|---------|
| Prometheus | 30 days | `prometheus_data` volume |
| Loki | 168 hours (7d) | `loki_data` volume |
| Tempo | 48 hours | `tempo_data` volume |
| Grafana | N/A (config-driven) | `grafana_data` volume |

To change retention, modify `docker-compose.yml` volume declarations or service command flags.

---

## Next Steps

1. **Instrument services** → Add OTEL SDKs to .NET and Python applications
2. **Configure alerts** → Update AlertManager webhook URLs for your team
3. **Create custom dashboards** → Use Grafana UI to build team-specific views
4. **Set SLOs** → Define error budgets and monitor compliance
5. **Integrate with on-call** → Link AlertManager to PagerDuty/Opsgenie

---

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/instrumentation/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Loki Query Language (LogQL)](https://grafana.com/docs/loki/latest/logql/)
- [Tempo Trace Query (TraceQL)](https://grafana.com/docs/tempo/latest/traceql/)
