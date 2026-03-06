# MODULES - Instrumentation SDK

> **Module**: Client-side OpenTelemetry instrumentation for .NET 9 and Python
> **Status**: Production Ready
> **Version**: 1.0.0

---

## Mục lục

1. [Python FastAPI SDK](#python-fastapi-sdk)
2. [.NET 9 SDK](#net-9-sdk)
3. [Metrics Reference](#metrics-reference)
4. [Integration Examples](#integration-examples)

---

## Python FastAPI SDK

### `instrumentation/python/telemetry.py`

**Chức năng**: Setup OpenTelemetry cho FastAPI application

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app):
    # Traces: Configure BatchSpanProcessor
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics: Configure PeriodicExportingMetricReader
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTEL_ENDPOINT),
        export_interval_millis=15000  # 15s
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Auto-instrument FastAPI + HTTP clients
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(__name__), metrics.get_meter(__name__)
```

**Output**:
- Traces → OTEL Collector :4317 (gRPC) → Tempo
- Metrics → OTEL Collector :4317 (gRPC) → Prometheus

### `instrumentation/python/metrics.py`

**Chức năng**: Custom metric definitions for AI pipeline

```python
from opentelemetry import metrics
import time
from contextlib import contextmanager

meter = metrics.get_meter("ai-pipeline")

# Histograms
ocr_duration = meter.create_histogram(
    "ocr_processing_seconds",
    description="OCR processing stage duration",
    unit="s"
)

gpt_duration = meter.create_histogram(
    "gpt_inference_seconds",
    description="GPT API inference duration",
    unit="s"
)

pipeline_duration = meter.create_histogram(
    "pipeline_processing_seconds",
    description="Pipeline stage duration",
    unit="s"
)

# Counters
ai_tokens = meter.create_counter("ai_tokens_total")
ai_cost = meter.create_counter("ai_cost_usd_total")

# Gauges
queue_size = meter.create_up_down_counter("queue_backlog_size")
```

**Helpers**:

```python
@contextmanager
def measure_pipeline_stage(stage_name: str, attrs: dict):
    """Context manager for measuring pipeline stages"""
    start = time.perf_counter()
    try:
        yield
        pipeline_duration.record(
            time.perf_counter() - start,
            attributes={**attrs, "stage": stage_name, "status": "success"}
        )
    except Exception as e:
        pipeline_duration.record(
            time.perf_counter() - start,
            attributes={**attrs, "stage": stage_name, "status": "error"}
        )
        raise

def record_gpt_usage(model: str, prompt_tokens: int, completion_tokens: int,
                     cost_usd: float, service: str, client_id: str):
    """Record GPT API usage"""
    attrs = {"model": model, "service": service, "client_id": client_id}
    ai_tokens.add(prompt_tokens, attributes={**attrs, "token_type": "prompt"})
    ai_tokens.add(completion_tokens, attributes={**attrs, "token_type": "completion"})
    ai_cost.add(cost_usd, attributes=attrs)
```

---

## .NET 9 SDK

### `instrumentation/dotnet/ObservabilityExtensions.cs`

**Chức năng**: DI extension cho OpenTelemetry setup

```csharp
using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using OpenTelemetry.Resources;

public static class ObservabilityExtensions
{
    public static IServiceCollection AddObservability(
        this IServiceCollection services,
        IConfiguration config,
        string serviceName)
    {
        var otlpEndpoint = config["OTEL_EXPORTER_OTLP_ENDPOINT"] ?? "http://localhost:4317";

        services.AddOpenTelemetry()
            .ConfigureResource(r => r
                .AddService(serviceName)
                .AddAttributes(new Dictionary<string, object>
                {
                    ["environment"] = config["ASPNETCORE_ENVIRONMENT"] ?? "production"
                }))
            .WithTracing(tracing => tracing
                .AddAspNetCoreInstrumentation(opts =>
                {
                    opts.RecordException = true;
                    opts.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health");
                })
                .AddEntityFrameworkCoreInstrumentation(opts =>
                {
                    opts.SetDbStatementForText = true;
                })
                .AddHttpClientInstrumentation()
                .AddSource(PipelineMetrics.ActivitySourceName)
                .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint)))
            .WithMetrics(metrics => metrics
                .AddAspNetCoreInstrumentation()
                .AddHttpClientInstrumentation()
                .AddRuntimeInstrumentation()
                .AddPrometheusExporter()
                .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint)));

        return services;
    }
}
```

**Usage in Program.cs**:
```csharp
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");

// Later in middleware setup
app.UseOpenTelemetryPrometheusScrapingEndpoint();
```

### `instrumentation/dotnet/PipelineMetrics.cs`

**Chức năng**: Metric definitions for .NET

```csharp
using System.Diagnostics;
using System.Diagnostics.Metrics;

public static class PipelineMetrics
{
    public const string ActivitySourceName = "AIProjectMiddleware.Pipeline";

    private static readonly ActivitySource ActivitySource = new(ActivitySourceName);
    private static readonly Meter Meter = new("AIProjectMiddleware.Pipeline", "1.0.0");

    // Histograms
    public static readonly Histogram<double> OcrDuration =
        Meter.CreateHistogram<double>("ocr_processing_seconds", unit: "s");

    public static readonly Histogram<double> GptDuration =
        Meter.CreateHistogram<double>("gpt_inference_seconds", unit: "s");

    public static readonly Histogram<double> PipelineStageDuration =
        Meter.CreateHistogram<double>("pipeline_processing_seconds", unit: "s");

    // Counters
    public static readonly Counter<long> AiTokens =
        Meter.CreateCounter<long>("ai_tokens_total");

    public static readonly Counter<double> AiCost =
        Meter.CreateCounter<double>("ai_cost_usd_total");

    // Gauges
    public static readonly UpDownCounter<long> QueueBacklog =
        Meter.CreateUpDownCounter<long>("queue_backlog_size");

    // Activity helpers
    public static Activity? StartPipelineStage(string stageName, string documentType)
    {
        return ActivitySource.StartActivity(
            $"pipeline.{stageName}",
            ActivityKind.Internal,
            tags: new ActivityTagsCollection
            {
                ["pipeline.stage"] = stageName,
                ["document.type"] = documentType
            });
    }
}
```

**Usage in Controllers**:
```csharp
using (var activity = PipelineMetrics.StartPipelineStage("ocr", "invoice"))
{
    var duration = MeasureOCR();
    PipelineMetrics.OcrDuration.Record(duration,
        new TagList { { "document_type", "invoice" } });
}
```

---

## Metrics Reference

### Metrics được export

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `api_request_duration_seconds` | Histogram | endpoint, method, status, service | FastAPIInstrumentor / AspNetCore |
| `api_requests_total` | Counter | endpoint, method, status, service | Auto-instrumentation |
| `ocr_processing_seconds` | Histogram | document_type, solution, status | Custom (Python/C#) |
| `gpt_inference_seconds` | Histogram | model, prompt_type, status | Custom |
| `pipeline_processing_seconds` | Histogram | stage, document_type, status | Custom |
| `ai_tokens_total` | Counter | model, token_type, service, client_id | Custom |
| `ai_cost_usd_total` | Counter | model, service, client_id | Custom |
| `queue_backlog_size` | Gauge | queue_name, priority | Custom |

---

## Integration Examples

### Python FastAPI Integration

**File**: `main.py` hoặc app entry point

```python
from fastapi import FastAPI
from instrumentation.python.telemetry import setup_telemetry
from instrumentation.python.metrics import measure_pipeline_stage, record_gpt_usage

app = FastAPI()

# Setup telemetry
tracer, meter = setup_telemetry(app)

@app.post("/process-document")
async def process_document(file: UploadFile):
    """Process document through pipeline"""
    with measure_pipeline_stage("upload", {"document_type": "invoice"}):
        # Upload logic
        pass

    with measure_pipeline_stage("ocr", {"document_type": "invoice"}):
        # OCR logic
        result = await ocr_service.process(file)
        pass

    with measure_pipeline_stage("gpt", {"document_type": "invoice"}):
        # GPT extraction
        tokens, cost = await gpt_service.extract(result)
        record_gpt_usage(
            model="gpt-4",
            prompt_tokens=tokens["prompt"],
            completion_tokens=tokens["completion"],
            cost_usd=cost,
            service="ai-agents",
            client_id=client_id
        )
        pass

    return {"status": "success"}

# Expose /metrics for Prometheus scraping
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### .NET 9 Integration

**File**: `Program.cs`

```csharp
var builder = WebApplicationBuilder.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");

var app = builder.Build();

// Middleware
app.UseOpenTelemetryPrometheusScrapingEndpoint();
app.MapControllers();

app.Run();
```

**File**: `Controllers/DocumentController.cs`

```csharp
[ApiController]
[Route("api/[controller]")]
public class DocumentController : ControllerBase
{
    [HttpPost("process")]
    public async Task<IActionResult> ProcessDocument(IFormFile file)
    {
        using var activity = PipelineMetrics.StartPipelineStage("upload", "invoice");

        // Upload logic
        var uploadTime = Measure(() => Upload(file));
        PipelineMetrics.PipelineStageDuration.Record(
            uploadTime,
            new TagList { { "stage", "upload" }, { "status", "success" } }
        );

        // OCR logic
        var ocrTime = Measure(() => OCR(file));
        PipelineMetrics.OcrDuration.Record(
            ocrTime,
            new TagList { { "document_type", "invoice" } }
        );

        // GPT extraction
        var (tokens, cost) = await ExtractWithGPT(file);
        PipelineMetrics.AiTokens.Add(tokens.Prompt,
            new TagList { { "token_type", "prompt" } });
        PipelineMetrics.AiCost.Add(cost,
            new TagList { { "model", "gpt-4" } });

        return Ok();
    }
}
```

---

## Setup Checklist

- [ ] Copy `instrumentation/python/` to Python project
- [ ] Install Python dependencies
- [ ] Call `setup_telemetry(app)` in FastAPI startup
- [ ] Add `/metrics` endpoint
- [ ] Set `OTEL_EXPORTER_OTLP_ENDPOINT` env var
- [ ] Verify metrics at http://localhost:8000/metrics

- [ ] Copy `instrumentation/dotnet/` to .NET project
- [ ] Install NuGet packages
- [ ] Call `.AddObservability()` in Program.cs
- [ ] Add `UseOpenTelemetryPrometheusScrapingEndpoint()` middleware
- [ ] Set `OTEL_EXPORTER_OTLP_ENDPOINT` env var
- [ ] Verify metrics at http://localhost:5000/metrics

---

## Liên kết

- 🔧 [Project Structure](../01_ARCHITECTURE/project-structure.md)
- 📊 [Metrics Contracts](../03_API/metrics-contracts.md)
- 🚀 [Integration Guides](../03_API/integrations/)

---

*Cập nhật lần cuối: 2026-03-04*
