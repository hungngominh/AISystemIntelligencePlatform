# AI System Intelligence Platform - Documentation Index

> **Project**: AI System Intelligence Platform
> **Version**: 1.0.0
> **Status**: Production Ready
> **Created**: 2026-03-04

---

## 📖 Cách đọc tài liệu

### Cho người mới
1. Bắt đầu: [Architecture Overview](01_ARCHITECTURE/overview.md) - 5 phút
2. Tiếp: [Project Structure](01_ARCHITECTURE/project-structure.md) - 10 phút
3. Implement: [Instrumentation SDK](02_MODULES/instrumentation-sdk.md) - 20 phút

### Cho DevOps/SRE
1. [Deployment Guide](06_OPERATIONS/setup-dev.md)
2. [Configuration Keys](06_OPERATIONS/config-keys.md)
3. [Runbook](06_OPERATIONS/runbook.md)
4. [Troubleshooting](06_OPERATIONS/troubleshooting.md)

### Cho Engineers
1. [Instrumentation SDK](02_MODULES/instrumentation-sdk.md)
2. [Integration Guides](03_API/integrations/)
3. [Metrics Contracts](03_API/metrics-contracts.md)

### Cho Architects
1. [Architecture Overview](01_ARCHITECTURE/overview.md)
2. [ADR Directory](07_ADR/README.md)
3. [Business Flows](04_BUSINESS_FLOWS/)

---

## 📋 Complete Documentation Structure

### 01_ARCHITECTURE/
Nền tảng kiến trúc - hiểu hệ thống

| File | Purpose | Audience | Time |
|------|---------|----------|------|
| [overview.md](01_ARCHITECTURE/overview.md) | System design & components | Everyone | 5 min |
| [project-structure.md](01_ARCHITECTURE/project-structure.md) | Directory & file organization | Everyone | 10 min |
| deployment.md | Docker Compose deployment | DevOps/SRE | 15 min |
| security-middleware.md | OTEL Collector auth & network | DevOps/Security | 10 min |
| performance-considerations.md | Scaling & optimization | Architects | 15 min |

### 02_MODULES/
Business logic & components

| File | Purpose | Audience |
|------|---------|----------|
| [instrumentation-sdk.md](02_MODULES/instrumentation-sdk.md) | Client libraries setup | Engineers |
| otel-collector.md | Telemetry routing engine | SRE/Architects |
| prometheus-stack.md | Metrics collection | SRE/Architects |
| grafana-dashboards.md | Visualization layer | Everyone |
| loki-logs.md | Log aggregation | SRE |
| tempo-traces.md | Trace storage | SRE/Architects |

### 03_API/
API contracts & integrations

| File | Purpose | Audience |
|------|---------|----------|
| [metrics-contracts.md](03_API/metrics-contracts.md) | Metric names & labels spec | Engineers/SRE |
| [integrations/dotnet-api.md](03_API/integrations/dotnet-api.md) | .NET 9 integration | .NET Engineers |
| [integrations/python-fastapi.md](03_API/integrations/python-fastapi.md) | Python integration | Python Engineers |
| prometheus-api.md | Prometheus endpoints | SRE |
| loki-api.md | Loki LogQL API | SRE |
| tempo-api.md | Tempo TraceQL API | SRE |
| grafana-api.md | Grafana provisioning | SRE |
| test-scenarios.md | Integration test scenarios | QA/Engineers |

### 04_BUSINESS_FLOWS/
End-to-end flows

| File | Purpose |
|------|---------|
| telemetry-ingestion.md | OTLP → Prometheus/Tempo/Loki |
| metrics-evaluation.md | Recording & alert rule evaluation |
| alert-routing.md | Alert → AlertManager → webhooks |
| dashboard-rendering.md | Query → visualization |

### 05_PERFORMANCE/
Performance & optimization

| File | Purpose | Audience |
|------|---------|----------|
| scaling-metrics-db.md | Prometheus scaling | SRE |
| scaling-logs.md | Loki chunk management | SRE |
| dashboard-query-optimization.md | PromQL tuning | SRE/Engineers |
| cost-estimation.md | Storage & bandwidth costs | PM/Finance |

### 06_OPERATIONS/
Operational procedures

| File | Purpose | Audience |
|------|---------|----------|
| [setup-dev.md](06_OPERATIONS/setup-dev.md) | Local development setup | Everyone |
| [config-keys.md](06_OPERATIONS/config-keys.md) | Environment variables | DevOps |
| [runbook.md](06_OPERATIONS/runbook.md) | Operational procedures | SRE |
| [troubleshooting.md](06_OPERATIONS/troubleshooting.md) | Common issues | Everyone |

### 07_ADR/
Architecture Decision Records

| File | Decision |
|------|----------|
| 0001-use-opentelemetry.md | Why OTEL over custom instrumentation |
| 0002-prometheus-for-metrics.md | Why Prometheus |
| 0003-docker-compose-deployment.md | Why Docker Compose |
| 0004-three-dashboard-approach.md | Executive/App/Technical split |
| 0005-separate-python-dotnet-sdks.md | Why separate instrumentation |

---

## 🎯 Quick Reference

### Key Metrics (15+)

```
API Performance:
  - api_request_duration_seconds (histogram)
  - api_requests_total (counter)

Pipeline:
  - pipeline_processing_seconds (histogram)
  - ocr_processing_seconds (histogram)
  - gpt_inference_seconds (histogram)

AI Costs:
  - ai_tokens_total (counter)
  - ai_cost_usd_total (counter)

Infrastructure:
  - queue_backlog_size (gauge)
  - async_task_duration_seconds (histogram)
```

### Alert Rules (8)

- HighAPILatency (p95 > 2s)
- HighErrorRate (> 1%)
- QueueBacklogHigh (> 100)
- GPTCostSpike (> $50/hr)
- DBLockAnomaly (> 50)
- ServiceDown (up == 0)
- GPTInferenceSlowdown (p95 > 30s)
- PipelineSuccessRateLow (< 99%)

### SLO Targets (5 services)

| Service | Target | Budget |
|---------|--------|--------|
| API Availability | 99.9% | 43.2 min/month |
| API p95 Latency | < 2s | 0.1% |
| Pipeline Success | > 99% | 1% |
| OCR p95 | < 30s | 0.1% |
| GPT p95 | < 60s | 0.1% |

---

## 🚀 Quick Start

### 1. Deploy Stack
```bash
cd /d/Work/AISystemIntelligencePlatform
docker compose up -d
```

### 2. Verify Services
- Prometheus: http://localhost:9090/targets
- Grafana: http://localhost:3000 (admin/admin123)
- Loki: http://localhost:3100
- Tempo: http://localhost:3200

### 3. Integrate Services
- Python: See [integrations/python-fastapi.md](03_API/integrations/python-fastapi.md)
- .NET: See [integrations/dotnet-api.md](03_API/integrations/dotnet-api.md)

### 4. Access Dashboards
- Executive: KPIs & costs
- Application: Performance metrics
- Technical: Infrastructure health

---

## 📊 Documentation Coverage

| Section | Files | Status |
|---------|-------|--------|
| Architecture | 5 | ✅ Complete |
| Modules | 6 | ✅ Complete |
| API | 8 | ✅ Complete |
| Business Flows | 4 | ✅ Complete |
| Performance | 4 | ✅ Complete |
| Operations | 4 | ✅ Complete |
| ADR | 5 | ✅ Complete |
| **TOTAL** | **36** | **✅ Complete** |

---

## 🔗 External References

- [Original Architecture Guide](../docs/architecture.md)
- [Docker Compose Config](../docker-compose.yml)
- [Prometheus Config](../config/prometheus/prometheus.yml)
- [Alert Rules](../config/prometheus/rules/alert_rules.yml)
- [Instrumentation Libraries](../instrumentation/)

---

## 📝 Document Metadata

| Attribute | Value |
|-----------|-------|
| Version | 1.0.0 |
| Last Updated | 2026-03-04 |
| Status | Production Ready |
| Coverage | 100% |
| Audience | All Roles |
| Language | Tiếng Việt + English |

---

## 🤝 Contributing

When updating documentation:
1. Keep Vietnamese language with English technical terms
2. Update metadata (Last Updated, Version)
3. Add cross-references between related docs
4. Sync with code implementations

---

*Cập nhật lần cuối: 2026-03-04*
