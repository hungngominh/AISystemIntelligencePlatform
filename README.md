# AI System Intelligence Platform — Observability Stack

Complete, production-ready observability platform for monitoring AIProjectMiddleware (.NET 9) and multiAIAgents (Python) systems.

## 📦 What's Included

- **Docker Compose Stack** — 8 containerized services (Prometheus, Grafana, Loki, Tempo, AlertManager, OTEL Collector, exporters)
- **3 Grafana Dashboards** — Executive, Application, and Technical views
- **Instrumentation Libraries** — Ready-to-use Python and .NET wrappers for OpenTelemetry
- **Alert Rules** — 8 pre-configured alerts for API, pipeline, and infrastructure metrics
- **PromQL & LogQL Examples** — Common queries for performance analysis and debugging
- **Complete Documentation** — Architecture guide, SLO definitions, troubleshooting

## 🚀 Quick Start

```bash
# 1. Start the stack
docker compose up -d

# 2. Open Grafana
# http://localhost:3000 (admin/admin123)

# 3. Verify services
# Prometheus: http://localhost:9090/targets
# Loki: http://localhost:3100
# Tempo: http://localhost:3200
```

## 📊 Dashboards

| Dashboard | Purpose | Audience |
|-----------|---------|----------|
| **Executive** | Uptime, costs, pipeline success | Leadership, PMs |
| **Application** | Request rates, latency, errors, queue depth | Platform/Oncall Engineers |
| **Technical** | CPU, memory, disk, DB, transactions | SREs, Infrastructure |

## 📐 Metrics Architecture

### Core Metrics (All Services)

```
API Performance
├── api_request_duration_seconds (histogram)
├── api_requests_total (counter)
└── api_error_rate (recorded)

Pipeline & AI
├── pipeline_processing_seconds (histogram, per-stage)
├── pipeline_completed_total (counter)
├── ocr_processing_seconds (histogram)
├── gpt_inference_seconds (histogram)
├── ai_tokens_total (counter)
└── ai_cost_usd_total (counter)

Infrastructure
├── queue_backlog_size (gauge)
├── async_task_duration_seconds (histogram)
├── node_cpu/memory/disk (from node-exporter)
├── pg_locks_count, pg_stat_database_xact_* (from postgres-exporter)
└── container metrics (from cadvisor)
```

## 🔧 Instrumentation

### .NET 9 (AIProjectMiddleware)

```csharp
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");

// In your pipeline handlers:
using var activity = PipelineMetrics.StartPipelineStage("ocr", "invoice");
// ... OCR logic
PipelineMetrics.OcrDuration.Record(duration, new { document_type = "invoice" });
```

See: `instrumentation/dotnet/ObservabilityExtensions.cs` and `PipelineMetrics.cs`

### Python FastAPI (multiAIAgents)

```python
from instrumentation.python.telemetry import setup_telemetry
from instrumentation.python.metrics import measure_pipeline_stage, record_gpt_usage

app = FastAPI()
tracer, meter = setup_telemetry(app)

@app.post("/process")
async def process():
    with measure_pipeline_stage("ocr", {"document_type": "invoice"}):
        # OCR logic
        pass

    record_gpt_usage("gpt-4", prompt_tokens=100, completion_tokens=50, ...)
```

See: `instrumentation/python/telemetry.py` and `metrics.py`

## 🎯 SLO Targets

| Service | Metric | Target | Error Budget (30d) |
|---------|--------|--------|---------------------|
| API | Availability | 99.9% | 43.2 min |
| API | p95 Latency | < 2s | 0.1% violation |
| Pipeline | Success Rate | > 99% | 1% failure rate |
| OCR | p95 Latency | < 30s | 0.1% violation |
| GPT | p95 Inference | < 60s | 0.1% violation |

## 🚨 Alert Rules

8 pre-configured alerts:

- **HighAPILatency** — p95 > 2s (warning)
- **HighErrorRate** — > 1% (critical)
- **QueueBacklogHigh** — > 100 items (warning)
- **GPTCostSpike** — > $50/hr (warning)
- **DBLockAnomaly** — > 50 locks (critical)
- **ServiceDown** — up==0 (critical)
- **GPTInferenceSlowdown** — p95 > 30s (warning)
- **PipelineSuccessRateLow** — < 99% (critical)

Configure webhook URLs in `config/alertmanager/alertmanager.yml`.

## 📁 Directory Structure

```
.
├── docker-compose.yml              # Full stack definition
├── .env                            # Environment variables
├── config/
│   ├── otel-collector/            # OTLP collector configuration
│   ├── prometheus/                # Prometheus + alert/recording rules
│   ├── alertmanager/              # Alert routing
│   ├── loki/                      # Log storage
│   ├── tempo/                     # Trace storage
│   └── grafana/                   # Provisioning & dashboards
├── instrumentation/
│   ├── dotnet/                    # .NET 9 OTEL wrapper
│   └── python/                    # Python/FastAPI OTEL wrapper
└── docs/
    └── architecture.md            # Full documentation
```

## 🔌 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Grafana | 3000 | UI dashboards |
| Prometheus | 9090 | Metrics API |
| Loki | 3100 | Log API |
| Tempo | 3200 | Trace API |
| AlertManager | 9093 | Alert API |
| OTEL gRPC | 4317 | Telemetry ingestion |
| OTEL HTTP | 4318 | Telemetry ingestion |
| node-exporter | 9100 | OS metrics |
| postgres-exporter | 9187 | DB metrics |
| cadvisor | 8080 | Container metrics |

## 📖 Documentation

See `docs/architecture.md` for:
- Detailed data flow architecture
- PromQL query examples
- LogQL query examples
- Troubleshooting guide
- Configuration reference
- Retention policies
- Integration patterns

## 🔄 Data Retention

| Component | Retention |
|-----------|-----------|
| Prometheus | 30 days |
| Loki | 7 days |
| Tempo | 2 days |
| Grafana | Config-driven |

## ✅ Verification Steps

After `docker compose up -d`:

1. ✓ Grafana accessible at http://localhost:3000
2. ✓ All scrape targets UP in Prometheus http://localhost:9090/targets
3. ✓ Datasources connected in Grafana (Prometheus, Loki, Tempo)
4. ✓ Send test request → verify trace in Tempo
5. ✓ Verify metrics in Prometheus for `api_request_duration_seconds`
6. ✓ Trigger alert threshold → verify AlertManager notification
7. ✓ Executive dashboard shows cost, uptime, pipeline data

## 🛠️ Next Steps

1. **Add OTEL SDKs** to your .NET and Python services (see `instrumentation/` examples)
2. **Configure AlertManager webhooks** (Slack, PagerDuty, email, etc.)
3. **Create custom dashboards** for team-specific metrics
4. **Set up SLO tracking** and error budget calculations
5. **Integrate with on-call** system for alert routing

## 📚 References

- [OpenTelemetry](https://opentelemetry.io/)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [Loki](https://grafana.com/oss/loki/)
- [Tempo](https://grafana.com/oss/tempo/)

---

**Built for AIProjectMiddleware + multiAIAgents observability. Customize and deploy!** 🚀
