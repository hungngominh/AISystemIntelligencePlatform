# Deployment Checklist

## ✅ Pre-Deployment Verification

- [x] All 21 files created and organized
- [x] docker-compose.yml valid YAML structure
- [x] All configuration files in proper format
- [x] 3 Grafana dashboards created with PromQL queries
- [x] 4 instrumentation files (2 Python, 2 .NET)
- [x] 10 configuration files (YAML/YML)
- [x] 3 documentation files (README, architecture guide, implementation summary)
- [x] Environment configuration (.env) created
- [x] Recording rules defined (5 pre-computed metrics)
- [x] Alert rules defined (8 alerts with SLO thresholds)

---

## 🚀 Deployment Steps

### Step 1: Initial Setup
```bash
cd /d/Work/AISystemIntelligencePlatform

# Verify directory structure
ls -la docker-compose.yml config/ instrumentation/ docs/

# Check environment file
cat .env
```

**Expected**: 21 files visible, .env contains OTEL endpoints and credentials

---

### Step 2: Start the Observability Stack
```bash
docker compose up -d

# Verify services are running
docker compose ps
```

**Expected**: All 8 services running:
- ✓ otel-collector
- ✓ prometheus
- ✓ grafana
- ✓ loki
- ✓ tempo
- ✓ alertmanager
- ✓ postgres-exporter
- ✓ node-exporter
- ✓ cadvisor

**Wait**: 15-20 seconds for services to fully initialize

---

### Step 3: Verify Core Services
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana health
curl http://localhost:3000/api/health

# Check Loki readiness
curl http://localhost:3100/ready

# Check Tempo readiness
curl http://localhost:3200/ready
```

**Expected**: All endpoints return HTTP 200 OK

---

### Step 4: Access Grafana UI
1. Open http://localhost:3000
2. Login: `admin` / `admin123`
3. Navigate to Dashboards → Browse
4. Verify 3 dashboards are visible:
   - [ ] Executive Dashboard
   - [ ] Application Dashboard
   - [ ] Technical Dashboard

---

### Step 5: Verify Prometheus Scrape Targets
1. Open http://localhost:9090/targets
2. Verify target groups:
   - [ ] prometheus (localhost:9090)
   - [ ] node-exporter (node-exporter:9100)
   - [ ] cadvisor (cadvisor:8080)
   - [ ] postgres-exporter (postgres-exporter:9187)
   - [ ] otel-collector (otel-collector:8889)
   - [ ] dotnet-api (host.docker.internal:5000) — will show DOWN until service starts
   - [ ] fastapi (host.docker.internal:8000) — will show DOWN until service starts

**Note**: .NET and FastAPI targets will show DOWN until those services are instrumented and started. This is normal.

---

### Step 6: Verify Datasources in Grafana
1. Open http://localhost:3000
2. Settings → Data Sources
3. Verify 3 datasources:
   - [ ] Prometheus (http://prometheus:9090)
   - [ ] Loki (http://loki:3100)
   - [ ] Tempo (http://tempo:3200)

All should show green checkmark (✓ Connected)

---

### Step 7: Verify Recording Rules
```bash
curl 'http://localhost:9090/api/v1/rules?type=alert'
```

**Expected**: JSON response with 8 alert rules defined:
- HighAPILatency
- HighErrorRate
- QueueBacklogHigh
- GPTCostSpike
- DBLockAnomaly
- ServiceDown
- GPTInferenceSlowdown
- PipelineSuccessRateLow

---

### Step 8: Test OTLP Collector
```bash
# Send test OTLP trace (gRPC)
grpcurl -plaintext -d '{}' localhost:4317 opentelemetry.proto.collector.trace.v1.TraceService/Export

# Check collector logs
docker logs otel-collector | tail -20
```

**Expected**: No connection errors in logs

---

## 📊 Dashboard Validation Checklist

### Executive Dashboard
- [ ] Service Uptime gauge displays
- [ ] Total Errors (24h) stat displays
- [ ] AI Cost Today stat displays
- [ ] Pipeline Success Rate gauge displays
- [ ] AI Cost Trend (7d) pie chart displays

### Application Dashboard
- [ ] API Request Rate time series displays
- [ ] API Latency (p50/p95/p99) time series displays
- [ ] Queue Backlog stat displays
- [ ] Pipeline Stage Latency bar chart displays
- [ ] Async Task Duration time series displays
- [ ] Active Workers stat displays

### Technical Dashboard
- [ ] CPU Usage time series displays
- [ ] Memory Usage time series displays
- [ ] Disk I/O time series displays
- [ ] Network Traffic time series displays
- [ ] DB Locks stat displays
- [ ] DB Transaction Rate time series displays

**Note**: Dashboards will show "No Data" until metrics are actually being scraped. This is normal for first deployment.

---

## 🔧 Instrumentation Integration Checklist

### For .NET 9 (AIProjectMiddleware)

- [ ] Copy `instrumentation/dotnet/ObservabilityExtensions.cs` → AIProjectMiddleware/Services/
- [ ] Copy `instrumentation/dotnet/PipelineMetrics.cs` → AIProjectMiddleware/Metrics/
- [ ] Add NuGet packages:
  ```
  OpenTelemetry.Extensions.Hosting
  OpenTelemetry.Instrumentation.AspNetCore
  OpenTelemetry.Instrumentation.EntityFrameworkCore
  OpenTelemetry.Instrumentation.Http
  OpenTelemetry.Exporter.OpenTelemetryProtocol
  OpenTelemetry.Instrumentation.Runtime
  prometheus-net.AspNetCore
  ```
- [ ] Update `Program.cs`:
  ```csharp
  builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");
  app.UseOpenTelemetryPrometheusScrapingEndpoint();
  ```
- [ ] Set environment variable:
  ```
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
  ```
- [ ] Restart application
- [ ] Verify in Prometheus: http://localhost:9090/targets → dotnet-api should show UP

### For Python (multiAIAgents)

- [ ] Copy `instrumentation/python/telemetry.py` → multiAIAgents/
- [ ] Copy `instrumentation/python/metrics.py` → multiAIAgents/
- [ ] Install packages:
  ```
  pip install opentelemetry-sdk==1.22.0
  pip install opentelemetry-exporter-otlp-proto-grpc==1.22.0
  pip install opentelemetry-instrumentation-fastapi==0.43b0
  pip install opentelemetry-instrumentation-httpx==0.43b0
  pip install prometheus-client==0.19.0
  ```
- [ ] Update FastAPI app startup:
  ```python
  from instrumentation.python.telemetry import setup_telemetry
  app = FastAPI()
  tracer, meter = setup_telemetry(app)
  ```
- [ ] Set environment variable:
  ```
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
  ```
- [ ] Add /metrics endpoint:
  ```python
  from prometheus_client import make_asgi_app
  metrics_app = make_asgi_app()
  app.mount("/metrics", metrics_app)
  ```
- [ ] Restart application
- [ ] Verify in Prometheus: http://localhost:9090/targets → fastapi should show UP

---

## 🚨 Troubleshooting Quick Reference

| Issue | Check |
|-------|-------|
| Services won't start | `docker compose logs` → check Docker errors |
| Prometheus targets DOWN | Verify AIProjectMiddleware and FastAPI are running on correct ports |
| No metrics in dashboards | Wait 60 seconds for scrape interval, then refresh |
| Grafana won't connect | Check datasource URLs are correct (use service names in docker network) |
| AlertManager not routing | Update `config/alertmanager/alertmanager.yml` with real webhook URLs |
| Traces not appearing in Tempo | Verify OTEL_EXPORTER_OTLP_ENDPOINT is set in service environment |

---

## 📝 Post-Deployment Configuration

### 1. AlertManager Webhooks (Required for Alerts)
Edit `config/alertmanager/alertmanager.yml`:
```yaml
receivers:
  - name: 'critical-channel'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

Then reload:
```bash
curl -X POST http://localhost:9093/-/reload
```

### 2. Custom Dashboard Queries
For team-specific metrics, create custom dashboards in Grafana UI:
1. Dashboard → New Dashboard
2. Add panels with PromQL queries from `docs/architecture.md`
3. Save and share with team

### 3. SLO Tracking
Use AlertManager + recording rules to monitor error budgets:
- Available error budget = (1 - SLO) × 30 days
- Monitor burn rate: `(1 - success_rate) / (1 - SLO)`

---

## 🎯 Success Criteria

✅ **Deployment is successful when**:

1. All 8 Docker services are running
2. Prometheus scrapes at least node-exporter, postgres-exporter, cadvisor
3. Grafana UI is accessible with 3 dashboards visible
4. Tempo and Loki datasources are connected in Grafana
5. No critical errors in service logs

✅ **Full observability is active when**:

6. AIProjectMiddleware and FastAPI are instrumented and running
7. Prometheus shows their scrape targets as UP
8. Metrics appear in dashboard panels
9. Traces appear in Tempo
10. Logs appear in Loki

---

## 📞 Support

- Check `docs/architecture.md` for detailed troubleshooting
- Review service logs: `docker compose logs SERVICE_NAME`
- Prometheus UI for metric validation: http://localhost:9090
- Grafana alerts: Settings → Alert Rules

---

**Last Updated**: 2026-03-04
**Platform Version**: 1.0
**Status**: Ready for Deployment
