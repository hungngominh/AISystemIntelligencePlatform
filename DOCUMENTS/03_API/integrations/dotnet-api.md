# Integration Guide - .NET 9 (AIProjectMiddleware)

> **Target**: AIProjectMiddleware (.NET 9 Web API)
> **Status**: Implementation Ready
> **Duration**: 20-30 minutes

---

## Mục lục

1. [Prerequisites](#prerequisites)
2. [Step-by-Step Integration](#step-by-step-integration)
3. [Verification](#verification)
4. [Troubleshooting](#troubleshooting)

---

## Prerequisites

✅ AIProjectMiddleware project must be .NET 9
✅ OTEL stack running: `docker compose up -d`
✅ NuGet access configured
✅ Environment variable support

---

## Step-by-Step Integration

### Step 1: Copy Instrumentation Files

```bash
# Copy from AISystemIntelligencePlatform
cp /d/Work/AISystemIntelligencePlatform/instrumentation/dotnet/*.cs \
   <AIProjectMiddleware-path>/Services/Observability/

# Or copy specific files:
# - ObservabilityExtensions.cs → Services/Observability/
# - PipelineMetrics.cs → Services/Observability/
```

### Step 2: Install NuGet Packages

Add to `.csproj`:

```xml
<ItemGroup>
  <PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.7.0" />
  <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.7.0" />
  <PackageReference Include="OpenTelemetry.Instrumentation.EntityFrameworkCore" Version="1.7.0" />
  <PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.7.0" />
  <PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.7.0" />
  <PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.7.0" />
  <PackageReference Include="prometheus-net.AspNetCore" Version="8.0.0" />
</ItemGroup>
```

Or via CLI:

```bash
dotnet add package OpenTelemetry.Extensions.Hosting
dotnet add package OpenTelemetry.Instrumentation.AspNetCore
dotnet add package OpenTelemetry.Instrumentation.EntityFrameworkCore
dotnet add package OpenTelemetry.Instrumentation.Http
dotnet add package OpenTelemetry.Exporter.OpenTelemetryProtocol
dotnet add package OpenTelemetry.Instrumentation.Runtime
dotnet add package prometheus-net.AspNetCore
```

### Step 3: Update Program.cs

**Before**:
```csharp
var builder = WebApplicationBuilder.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddDbContext<ApplicationDbContext>();

var app = builder.Build();
app.MapControllers();
app.Run();
```

**After**:
```csharp
using AIProjectMiddleware.Services.Observability;

var builder = WebApplicationBuilder.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddDbContext<ApplicationDbContext>();

// Add OpenTelemetry observability
builder.Services.AddObservability(builder.Configuration, "AIProjectMiddleware");

var app = builder.Build();

// Expose /metrics endpoint for Prometheus
app.UseOpenTelemetryPrometheusScrapingEndpoint();

app.MapControllers();
app.Run();
```

### Step 4: Add Environment Variable

Set in local development environment (`.env` or `launchSettings.json`):

```json
{
  "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"
}
```

Or for Docker:

```dockerfile
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### Step 5: Use Pipeline Metrics in Controllers

**Example: Document Processing Endpoint**

```csharp
[ApiController]
[Route("api/[controller]")]
public class DocumentController : ControllerBase
{
    private readonly IOCRService _ocrService;
    private readonly ILogger<DocumentController> _logger;

    public DocumentController(IOCRService ocrService, ILogger<DocumentController> logger)
    {
        _ocrService = ocrService;
        _logger = logger;
    }

    [HttpPost("process")]
    public async Task<IActionResult> ProcessDocument(IFormFile file)
    {
        var documentType = DetectDocumentType(file);
        var clientId = User.FindFirst("client_id")?.Value ?? "unknown";

        try
        {
            // Stage 1: Upload
            using (var activity = PipelineMetrics.StartPipelineStage("upload", documentType))
            {
                var sw = System.Diagnostics.Stopwatch.StartNew();
                var uploadPath = await SaveFile(file);
                sw.Stop();

                PipelineMetrics.PipelineStageDuration.Record(
                    sw.Elapsed.TotalSeconds,
                    new TagList
                    {
                        { "stage", "upload" },
                        { "document_type", documentType },
                        { "status", "success" }
                    }
                );
            }

            // Stage 2: OCR
            using (var activity = PipelineMetrics.StartPipelineStage("ocr", documentType))
            {
                var sw = System.Diagnostics.Stopwatch.StartNew();
                var ocrResult = await _ocrService.ProcessAsync(file.OpenReadStream());
                sw.Stop();

                PipelineMetrics.OcrDuration.Record(
                    sw.Elapsed.TotalSeconds,
                    new TagList
                    {
                        { "document_type", documentType },
                        { "status", "success" }
                    }
                );
            }

            // Stage 3: GPT Extraction
            using (var activity = PipelineMetrics.StartPipelineStage("gpt", documentType))
            {
                var sw = System.Diagnostics.Stopwatch.StartNew();
                var (extractedData, tokens, cost) = await ExtractWithGPT(ocrResult);
                sw.Stop();

                PipelineMetrics.GptDuration.Record(
                    sw.Elapsed.TotalSeconds,
                    new TagList
                    {
                        { "model", "gpt-4" },
                        { "status", "success" }
                    }
                );

                // Record token usage
                PipelineMetrics.AiTokens.Add(
                    tokens.PromptTokens,
                    new TagList
                    {
                        { "model", "gpt-4" },
                        { "token_type", "prompt" },
                        { "service", "AIProjectMiddleware" },
                        { "client_id", clientId }
                    }
                );

                PipelineMetrics.AiTokens.Add(
                    tokens.CompletionTokens,
                    new TagList
                    {
                        { "model", "gpt-4" },
                        { "token_type", "completion" },
                        { "service", "AIProjectMiddleware" },
                        { "client_id", clientId }
                    }
                );

                // Record cost
                PipelineMetrics.AiCost.Add(
                    cost,
                    new TagList
                    {
                        { "model", "gpt-4" },
                        { "service", "AIProjectMiddleware" },
                        { "client_id", clientId }
                    }
                );
            }

            return Ok(new { status = "success", data = extractedData });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Document processing failed");

            // Optional: record failure metrics
            PipelineMetrics.PipelineStageDuration.Record(
                0,
                new TagList
                {
                    { "stage", "error" },
                    { "document_type", documentType },
                    { "status", "error" }
                }
            );

            return BadRequest(new { error = ex.Message });
        }
    }

    private string DetectDocumentType(IFormFile file)
    {
        return file.FileName.EndsWith(".pdf") ? "invoice" : "unknown";
    }

    private async Task<string> SaveFile(IFormFile file)
    {
        var path = Path.Combine(Path.GetTempPath(), file.FileName);
        using (var stream = new FileStream(path, FileMode.Create))
        {
            await file.CopyToAsync(stream);
        }
        return path;
    }

    private async Task<string> ExtractOCR(Stream fileStream)
    {
        // Call OCR service
        return "extracted_text";
    }

    private async Task<(string data, (int PromptTokens, int CompletionTokens) tokens, double cost)>
        ExtractWithGPT(string ocrText)
    {
        // Call GPT API
        return ("extracted_data", (100, 50), 0.003);
    }
}
```

---

## Verification

### Step 1: Verify Metrics Endpoint

```bash
# While application is running
curl http://localhost:5000/metrics

# Should return Prometheus metrics in text format
# Look for lines like:
# api_request_duration_seconds_bucket{...}
# api_requests_total{...}
```

### Step 2: Verify in Prometheus

```bash
# Open Prometheus UI
http://localhost:9090/targets

# Look for:
# - "dotnet-api" job should show "UP"
# - All metrics should be scraping successfully
```

### Step 3: Verify in Grafana

```bash
# Open Grafana
http://localhost:3000

# Navigate to:
# - Application Dashboard
# - Should see api_request_duration_seconds metrics
# - Should see api_requests_total increasing
```

### Step 4: Verify Traces

```bash
# Send a test request
curl -X POST http://localhost:5000/api/document/process \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test-document.pdf"

# Open Tempo UI
http://localhost:3200

# Should see traces for API calls
```

---

## Troubleshooting

### Issue: /metrics endpoint returns 404

**Solution**:
- Verify `UseOpenTelemetryPrometheusScrapingEndpoint()` is called in Program.cs
- Check that it's called AFTER `app = builder.Build()`
- Verify prometheus-net.AspNetCore is installed

```csharp
// CORRECT order
var app = builder.Build();
app.UseOpenTelemetryPrometheusScrapingEndpoint();
app.MapControllers();
```

### Issue: No metrics appearing in Prometheus

**Solution**:
1. Verify OTEL_EXPORTER_OTLP_ENDPOINT is set
2. Check application logs for OTEL errors
3. Verify OTEL Collector is running: `docker logs otel-collector`
4. Verify network connectivity: `docker exec otel-collector ping localhost`

### Issue: Metrics showing but values are 0

**Solution**:
- Ensure code is actually recording metrics
- Verify the tags match your PromQL queries
- Check that histogram is being recorded (not just created)

```csharp
// Make sure to RECORD the metric
PipelineMetrics.OcrDuration.Record(
    duration,
    new TagList { { "document_type", documentType } }
);
```

### Issue: High cardinality warnings in Prometheus

**Solution**:
- Don't use unbounded values (user IDs, file paths) as labels
- Only use fixed values: document_type, stage, status
- Use attributes or context instead of labels for high-cardinality data

---

## Validation Checklist

- [ ] NuGet packages installed
- [ ] Instrumentation files copied to project
- [ ] Program.cs updated with AddObservability()
- [ ] OTEL_EXPORTER_OTLP_ENDPOINT set
- [ ] /metrics endpoint accessible
- [ ] Metrics visible in Prometheus targets
- [ ] Traces visible in Tempo
- [ ] Application Dashboard shows api_* metrics
- [ ] Logs appear in Loki

---

## Next Steps

1. ✅ Integration complete
2. Add custom business logic metrics (queue_backlog_size, async_task_duration)
3. Update alert thresholds based on baseline data
4. Create team-specific dashboards
5. Document SLO targets for your API

---

## References

- [Instrumentation SDK Module](../../02_MODULES/instrumentation-sdk.md)
- [Metrics Contracts](../metrics-contracts.md)
- [Original Architecture Guide](../../docs/architecture.md)

---

*Cập nhật lần cuối: 2026-03-04*
