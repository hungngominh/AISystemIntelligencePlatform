# Cấu Trúc Dự Án

> **Component**: Project Structure & Directory Organization
> **Status**: Complete
> **Last Updated**: 2026-03-04

---

## Mục lục

1. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
2. [Mô tả từng folder](#mô-tả-từng-folder)
3. [File configuration chính](#file-configuration-chính)
4. [Instrumentation packages](#instrumentation-packages)

---

## Cấu trúc thư mục

```
AISystemIntelligencePlatform/
├── docker-compose.yml                    # Container orchestration
├── .env                                  # Environment variables
│
├── config/                               # Service configurations
│   ├── otel-collector/
│   │   └── otel-collector-config.yaml   # OTLP receiver, processors, exporters
│   │
│   ├── prometheus/
│   │   ├── prometheus.yml               # Scrape targets & global config
│   │   └── rules/
│   │       ├── recording_rules.yml      # Pre-computed metrics
│   │       └── alert_rules.yml          # Alert conditions (8 rules)
│   │
│   ├── alertmanager/
│   │   └── alertmanager.yml             # Alert routing & webhook config
│   │
│   ├── loki/
│   │   └── loki-config.yaml             # Log storage & retention
│   │
│   ├── tempo/
│   │   └── tempo-config.yaml            # Trace backend config
│   │
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/datasources.yaml   # Auto-provision Prometheus, Loki, Tempo
│       │   └── dashboards/dashboards.yaml     # Auto-provision 3 dashboards
│       │
│       └── dashboards/
│           ├── executive.json                # Dashboard 1: KPIs
│           ├── application.json              # Dashboard 2: Performance
│           └── technical.json                # Dashboard 3: Infrastructure
│
├── instrumentation/                      # Client instrumentation libraries
│   ├── python/
│   │   ├── telemetry.py                 # OpenTelemetry setup for FastAPI
│   │   └── metrics.py                   # Metric definitions & helpers
│   │
│   └── dotnet/
│       ├── ObservabilityExtensions.cs   # DI extension for .NET 9
│       └── PipelineMetrics.cs           # Metric definitions for .NET
│
├── docs/                                 # Original documentation
│   └── architecture.md                  # Technical reference (600+ lines)
│
└── DOCUMENTS/                            # Formal documentation (this section)
    ├── README.md                        # Index & reading guide
    ├── SYSTEM_MAP.md                    # Method contracts & code-gen companion
    ├── CHANGE_TRACKING.md               # Doc-vs-code alignment
    ├── llms.txt                         # LLM-oriented overview
    │
    ├── 01_ARCHITECTURE/
    │   ├── overview.md                  # You are here
    │   ├── project-structure.md         # This file
    │   ├── database-design.md           # None (stateless stack)
    │   ├── deployment.md                # Docker Compose & operations
    │   ├── security-middleware.md       # OTEL Collector auth & network
    │   └── performance-considerations.md # Scaling & optimization
    │
    ├── 02_MODULES/
    │   ├── otel-collector.md           # Telemetry routing engine
    │   ├── prometheus-stack.md         # Metrics collection & evaluation
    │   ├── grafana-dashboards.md       # Visualization layer
    │   ├── loki-logs.md                # Log aggregation
    │   ├── tempo-traces.md             # Trace storage & analysis
    │   └── instrumentation-sdk.md      # Client libraries (Python + .NET)
    │
    ├── 03_API/
    │   ├── _template.md
    │   ├── prometheus-api.md           # Prometheus API endpoints
    │   ├── loki-api.md                 # Loki LogQL API
    │   ├── tempo-api.md                # Tempo TraceQL API
    │   ├── grafana-api.md              # Grafana provisioning API
    │   ├── metrics-contracts.md        # Metric names & labels contract
    │   ├── integrations/
    │   │   ├── dotnet-api.md          # .NET 9 integration guide
    │   │   └── python-fastapi.md      # Python FastAPI integration guide
    │   └── test-scenarios.md           # Integration test scenarios
    │
    ├── 04_BUSINESS_FLOWS/
    │   ├── telemetry-ingestion.md      # OTLP → Prometheus/Tempo/Loki flow
    │   ├── metrics-evaluation.md        # Recording & alert rule evaluation
    │   ├── alert-routing.md            # Alert generation → AlertManager → webhooks
    │   └── dashboard-rendering.md      # Query execution → visualization
    │
    ├── 05_PERFORMANCE/
    │   ├── scaling-metrics-db.md       # Prometheus scaling & retention
    │   ├── scaling-logs.md             # Loki chunk management
    │   ├── dashboard-query-optimization.md # PromQL performance
    │   └── cost-estimation.md          # Storage & bandwidth costs
    │
    ├── 06_OPERATIONS/
    │   ├── setup-dev.md                # Local development setup
    │   ├── config-keys.md              # Environment variables reference
    │   ├── runbook.md                  # Operational procedures
    │   └── troubleshooting.md          # Common issues & resolutions
    │
    └── 07_ADR/
        ├── README.md
        ├── template.md
        ├── 0001-use-opentelemetry.md   # Why OTEL over custom instrumentation
        ├── 0002-prometheus-for-metrics.md # Why Prometheus
        ├── 0003-docker-compose-deployment.md # Why Docker Compose
        ├── 0004-three-dashboard-approach.md # Executive/App/Technical split
        └── 0005-separate-python-dotnet-sdks.md # Why separate instrumentation
```

---

## Mô tả từng folder

### `docker-compose.yml` - Container Orchestration

Định nghĩa 9 services:

| Service | Port | Purpose | Retention |
|---------|------|---------|-----------|
| otel-collector | 4317, 4318 | Telemetry ingestion | N/A |
| prometheus | 9090 | Metrics DB | 30 days |
| grafana | 3000 | Dashboards | Config |
| loki | 3100 | Logs | 7 days |
| tempo | 3200, 9411 | Traces | 2 days |
| alertmanager | 9093 | Alert routing | N/A |
| node-exporter | 9100 | OS metrics | N/A |
| postgres-exporter | 9187 | DB metrics | N/A |
| cadvisor | 8080 | Container metrics | N/A |

**Volumes**:
- `prometheus_data:/prometheus` - Metrics storage
- `loki_data:/loki` - Log storage
- `tempo_data:/tmp/tempo` - Trace storage
- `grafana_data:/var/lib/grafana` - Dashboards & settings

---

### `config/` - Service Configurations

#### `otel-collector-config.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc: :4317
      http: :4318
processors:
  - batch
  - memory_limiter
  - resource (add environment label)
exporters:
  - prometheus (for Prometheus scraping)
  - loki (for log aggregation)
  - otlp/tempo (for distributed tracing)
```

**Flow**: OTLP → Batch/MemLimit → Prometheus/Loki/Tempo

#### `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  external_labels:
    cluster: ai-platform
    environment: production

scrape_configs:
  - job_name: prometheus (self)
  - job_name: node-exporter
  - job_name: cadvisor
  - job_name: postgres-exporter
  - job_name: otel-collector
  - job_name: dotnet-api (host.docker.internal:5000)
  - job_name: fastapi (host.docker.internal:8000)

rule_files:
  - recording_rules.yml
  - alert_rules.yml
```

#### `recording_rules.yml`

5 pre-computed metrics:
1. `job:api_request_duration_seconds:p95` - p95 API latency
2. `job:pipeline_processing_seconds:p99` - p99 pipeline duration
3. `job:api_error_rate:rate5m` - error rate per endpoint
4. `job:ai_cost_usd:daily` - daily AI costs
5. `job:queue_saturation:ratio` - queue saturation ratio

#### `alert_rules.yml`

8 alert rules với thresholds dựa trên SLO (xem [overview.md](./overview.md#slo--alerts))

---

### `instrumentation/` - Client Libraries

#### `python/telemetry.py`

```python
def setup_telemetry(app):
    # Traces: BatchSpanProcessor → OTLPSpanExporter
    # Metrics: PeriodicExportingMetricReader → OTLPMetricExporter
    # Auto-instrument: FastAPIInstrumentor, HTTPXClientInstrumentor
```

**Usage**:
```python
from instrumentation.python.telemetry import setup_telemetry
app = FastAPI()
tracer, meter = setup_telemetry(app)
```

#### `python/metrics.py`

Predefined metrics:
- `ocr_duration` - OCR processing histogram
- `gpt_duration` - GPT inference histogram
- `pipeline_duration` - Pipeline stage histogram
- `ai_tokens` - Token counter
- `ai_cost` - Cost counter
- `queue_size` - Queue gauge

#### `dotnet/ObservabilityExtensions.cs`

```csharp
public static IServiceCollection AddObservability(
    this IServiceCollection services,
    IConfiguration config,
    string serviceName)
{
    // Traces: AspNetCore, EntityFramework, HttpClient instrumentation
    // Metrics: AspNetCore, HttpClient, Runtime instrumentation
    // Exporters: OtlpExporter, PrometheusExporter
}
```

**Usage**:
```csharp
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");
app.UseOpenTelemetryPrometheusScrapingEndpoint();
```

---

## File configuration chính

### Environment variables (`.env`)

```bash
# OTEL
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

### Config Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| docker-compose.yml | 85 | 9 services definition |
| prometheus.yml | 50 | Scrape config |
| otel-collector-config.yaml | 35 | Telemetry routing |
| alert_rules.yml | 65 | 8 alert conditions |
| recording_rules.yml | 30 | 5 pre-computed metrics |
| grafana provisioning | 25 | Auto datasources & dashboards |

---

## Instrumentation packages

### Python Dependencies

```
opentelemetry-sdk==1.22.0
opentelemetry-exporter-otlp-proto-grpc==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
prometheus-client==0.19.0
```

### .NET Dependencies

```
OpenTelemetry.Extensions.Hosting
OpenTelemetry.Instrumentation.AspNetCore
OpenTelemetry.Instrumentation.EntityFrameworkCore
OpenTelemetry.Instrumentation.Http
OpenTelemetry.Exporter.OpenTelemetryProtocol
OpenTelemetry.Instrumentation.Runtime
prometheus-net.AspNetCore
```

---

## Key Design Decisions

✅ **Docker Compose** - Single `docker-compose.yml` defines entire stack
✅ **Stateless services** - No application database (observability only)
✅ **Volume mounts** - Config as YAML, data in volumes
✅ **Auto-provisioning** - Grafana datasources & dashboards auto-loaded
✅ **Separate SDKs** - Independent Python & .NET instrumentation libraries

---

## Liên kết

- 📊 [Architecture Overview](./overview.md)
- 🚀 [Deployment Guide](./deployment.md)
- 📈 [Recording & Alert Rules](../../config/prometheus/rules/)
- 🔧 [Instrumentation SDK](../02_MODULES/instrumentation-sdk.md)

---

*Cập nhật lần cuối: 2026-03-04*
