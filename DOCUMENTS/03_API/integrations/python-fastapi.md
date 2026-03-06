# Integration Guide - Python FastAPI (multiAIAgents)

> **Target**: multiAIAgents (Python CrewAI + FastAPI)
> **Status**: Implementation Ready
> **Duration**: 15-20 minutes

---

## Mục lục

1. [Prerequisites](#prerequisites)
2. [Step-by-Step Integration](#step-by-step-integration)
3. [Verification](#verification)
4. [Troubleshooting](#troubleshooting)

---

## Prerequisites

✅ FastAPI application running
✅ OTEL stack running: `docker compose up -d`
✅ Python 3.9+ with pip
✅ Environment variable support

---

## Step-by-Step Integration

### Step 1: Copy Instrumentation Files

```bash
# Copy from AISystemIntelligencePlatform
cp -r /d/Work/AISystemIntelligencePlatform/instrumentation/python/* \
      <multiAIAgents-path>/instrumentation/

# Or copy specific files:
# - telemetry.py → instrumentation/
# - metrics.py → instrumentation/
```

### Step 2: Install Python Dependencies

Create `requirements-observability.txt`:

```txt
opentelemetry-sdk==1.22.0
opentelemetry-exporter-otlp-proto-grpc==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
prometheus-client==0.19.0
```

Install:

```bash
pip install -r requirements-observability.txt
```

Or individually:

```bash
pip install opentelemetry-sdk==1.22.0
pip install opentelemetry-exporter-otlp-proto-grpc==1.22.0
pip install opentelemetry-instrumentation-fastapi==0.43b0
pip install opentelemetry-instrumentation-httpx==0.43b0
pip install prometheus-client==0.19.0
```

### Step 3: Update Application Startup

**Before**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/process")
async def process():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**After**:
```python
from fastapi import FastAPI
from instrumentation.telemetry import setup_telemetry
from prometheus_client import make_asgi_app

# Create app
app = FastAPI()

# Setup telemetry (must be early)
tracer, meter = setup_telemetry(app)

# Setup Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.post("/process")
async def process():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Add Environment Variable

Set in `.env` or environment:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

For Docker:

```dockerfile
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### Step 5: Use Metrics in Endpoint Handlers

**Example: Document Processing with Pipeline Stages**

```python
from fastapi import FastAPI, UploadFile
from instrumentation.telemetry import setup_telemetry
from instrumentation.metrics import (
    measure_pipeline_stage,
    record_gpt_usage,
    ocr_duration,
    pipeline_duration,
    queue_size
)
import time

app = FastAPI()
tracer, meter = setup_telemetry(app)

@app.post("/api/documents/process")
async def process_document(file: UploadFile):
    """
    Process document through AI pipeline.

    Stages:
    1. Upload - save file
    2. OCR - extract text
    3. GPT - extract structured data
    4. Validate - validate output
    5. Store - save to database
    """

    document_type = detect_document_type(file.filename)
    client_id = request.headers.get("X-Client-Id", "unknown")

    try:
        # Stage 1: Upload
        with measure_pipeline_stage("upload", {"document_type": document_type}):
            start = time.perf_counter()
            file_path = await save_file(file)
            duration = time.perf_counter() - start
            pipeline_duration.record(
                duration,
                attributes={"stage": "upload", "status": "success"}
            )

        # Stage 2: OCR
        with measure_pipeline_stage("ocr", {"document_type": document_type}):
            start = time.perf_counter()
            ocr_text = await call_ocr_service(file_path)
            duration = time.perf_counter() - start

            ocr_duration.record(
                duration,
                attributes={"document_type": document_type, "status": "success"}
            )

        # Stage 3: GPT Extraction
        with measure_pipeline_stage("gpt", {"document_type": document_type}):
            start = time.perf_counter()

            # Call GPT API
            extracted_data, tokens_used, cost_usd = await extract_with_gpt(
                ocr_text,
                document_type
            )

            duration = time.perf_counter() - start
            pipeline_duration.record(
                duration,
                attributes={"stage": "gpt", "status": "success"}
            )

            # Record GPT usage
            record_gpt_usage(
                model="gpt-4",
                prompt_tokens=tokens_used["prompt"],
                completion_tokens=tokens_used["completion"],
                cost_usd=cost_usd,
                service="multiAIAgents",
                client_id=client_id
            )

        # Stage 4: Validate
        with measure_pipeline_stage("validate", {"document_type": document_type}):
            start = time.perf_counter()
            is_valid = validate_extraction(extracted_data, document_type)
            duration = time.perf_counter() - start

            if not is_valid:
                raise ValueError("Extracted data validation failed")

            pipeline_duration.record(
                duration,
                attributes={"stage": "validate", "status": "success"}
            )

        # Stage 5: Store
        with measure_pipeline_stage("store", {"document_type": document_type}):
            start = time.perf_counter()
            result_id = await save_to_database(extracted_data)
            duration = time.perf_counter() - start

            pipeline_duration.record(
                duration,
                attributes={"stage": "store", "status": "success"}
            )

        return {
            "status": "success",
            "document_type": document_type,
            "result_id": result_id,
            "data": extracted_data
        }

    except Exception as e:
        # Log error
        import logging
        logging.error(f"Pipeline error: {e}", exc_info=True)

        # Record failure metric
        pipeline_duration.record(
            0,
            attributes={"stage": "error", "status": "error"}
        )

        raise


@app.get("/api/queue/status")
async def queue_status():
    """Get current queue status"""
    pending_count = await get_pending_queue_count()
    max_capacity = 1000

    # Update gauge
    queue_size.add(pending_count, attributes={"queue_name": "document_processing"})

    return {
        "queue_name": "document_processing",
        "pending": pending_count,
        "capacity": max_capacity,
        "saturation": pending_count / max_capacity
    }


# Helper functions (implement according to your logic)
async def save_file(file: UploadFile) -> str:
    """Save uploaded file and return path"""
    pass

async def call_ocr_service(file_path: str) -> str:
    """Extract text from document"""
    pass

async def extract_with_gpt(text: str, doc_type: str) -> tuple:
    """Extract structured data using GPT"""
    # Returns: (extracted_data, tokens_used, cost_usd)
    pass

def detect_document_type(filename: str) -> str:
    """Detect document type from filename"""
    if filename.endswith(".pdf"):
        return "invoice"
    return "unknown"

def validate_extraction(data: dict, doc_type: str) -> bool:
    """Validate extracted data"""
    return True

async def save_to_database(data: dict) -> str:
    """Save to database and return ID"""
    pass

async def get_pending_queue_count() -> int:
    """Get current queue depth"""
    return 0
```

### Step 6: Expose /metrics Endpoint

Already done in Step 3 with:

```python
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

## Verification

### Step 1: Verify Metrics Endpoint

```bash
# While application is running
curl http://localhost:8000/metrics

# Should return Prometheus metrics
# Look for:
# opentelemetry_instrumentation_fastapi_* metrics
```

### Step 2: Send Test Request

```bash
# Upload a test document
curl -X POST http://localhost:8000/api/documents/process \
  -H "X-Client-Id: test-client-001" \
  -F "file=@sample-invoice.pdf"
```

### Step 3: Verify in Prometheus

```bash
# Open Prometheus UI
http://localhost:9090/targets

# Check:
# - fastapi job should show "UP"
# - Scraping should succeed
```

### Step 4: Verify Metrics in Grafana

```bash
# Open Grafana
http://localhost:3000/d/application-dashboard

# Should see:
# - api_request_duration_seconds histogram
# - api_requests_total counter increasing
# - pipeline_processing_seconds for each stage
# - ai_cost_usd_total accumulating
```

### Step 5: Verify Traces in Tempo

```bash
# Open Tempo UI
http://localhost:3200

# Should see traces for:
# - POST /api/documents/process
# - All HTTP calls made by the handler
```

---

## Troubleshooting

### Issue: /metrics endpoint returns 404

**Solution**:
```python
# Make sure you mount AFTER creating app
app = FastAPI()
tracer, meter = setup_telemetry(app)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)  # This line!
```

### Issue: No traces appearing

**Solution**:
1. Verify OTEL_EXPORTER_OTLP_ENDPOINT is set
2. Check application logs for OTEL errors
3. Test connectivity: `python -c "import httpx; httpx.get('http://localhost:4317')"`

### Issue: Metrics showing but context managers aren't recording

**Solution**:
Ensure you're using the context manager correctly:

```python
# CORRECT
with measure_pipeline_stage("ocr", {"document_type": "invoice"}):
    # Your code here
    pass

# WRONG (missing with)
measure_pipeline_stage("ocr", {"document_type": "invoice"})
```

### Issue: ImportError for instrumentation modules

**Solution**:
Ensure the path is correct:

```python
# If instrumentation/ is in project root
from instrumentation.telemetry import setup_telemetry

# If copied to different location, adjust import
import sys
sys.path.insert(0, '/path/to/instrumentation')
from telemetry import setup_telemetry
```

---

## Testing Example

```python
# test_integration.py
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_document_processing():
    """Test document processing with metrics"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test upload
        with open("test-invoice.pdf", "rb") as f:
            response = await client.post(
                "/api/documents/process",
                files={"file": f},
                headers={"X-Client-Id": "test-001"}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_metrics_endpoint():
    """Verify metrics are being recorded"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get metrics
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert "pipeline_processing_seconds" in response.text
```

---

## Validation Checklist

- [ ] Python dependencies installed
- [ ] Instrumentation files copied to project
- [ ] setup_telemetry() called in app startup
- [ ] /metrics endpoint mounted
- [ ] OTEL_EXPORTER_OTLP_ENDPOINT set
- [ ] /metrics returns Prometheus format
- [ ] Metrics visible in Prometheus targets
- [ ] Traces visible in Tempo
- [ ] Application Dashboard shows api_* metrics
- [ ] Custom metrics (pipeline, queue, cost) being recorded

---

## Next Steps

1. ✅ Integration complete
2. Add more custom metrics (task_type specific metrics)
3. Update dashboards for Python-specific metrics
4. Set up alerts based on pipeline latency
5. Monitor token usage and costs in real-time

---

## References

- [Instrumentation SDK Module](../../02_MODULES/instrumentation-sdk.md)
- [Metrics Contracts](../metrics-contracts.md)
- [Original Architecture Guide](../../docs/architecture.md)

---

*Cập nhật lần cuối: 2026-03-04*
