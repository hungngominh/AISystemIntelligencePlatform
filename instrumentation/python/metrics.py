from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
import time
from contextlib import contextmanager

meter = metrics.get_meter("ai-pipeline")

# Pipeline stage histograms
ocr_duration = meter.create_histogram(
    "ocr_processing_seconds",
    description="OCR processing stage duration",
    unit="s",
)
gpt_duration = meter.create_histogram(
    "gpt_inference_seconds",
    description="GPT API inference duration",
    unit="s",
)
pipeline_duration = meter.create_histogram(
    "pipeline_processing_seconds",
    description="Pipeline stage duration",
    unit="s",
)
ai_tokens = meter.create_counter(
    "ai_tokens_total",
    description="Total AI tokens consumed",
)
ai_cost = meter.create_counter(
    "ai_cost_usd_total",
    description="Total AI cost in USD",
)
queue_size = meter.create_up_down_counter(
    "queue_backlog_size",
    description="Current queue depth",
)

@contextmanager
def measure_pipeline_stage(stage_name: str, attrs: dict):
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
    attrs = {"model": model, "service": service, "client_id": client_id}
    ai_tokens.add(prompt_tokens, attributes={**attrs, "token_type": "prompt"})
    ai_tokens.add(completion_tokens, attributes={**attrs, "token_type": "completion"})
    ai_cost.add(cost_usd, attributes=attrs)
