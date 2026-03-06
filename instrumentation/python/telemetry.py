from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import os

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ai-fastapi-service")

def setup_telemetry(app):
    # Traces
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT))
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTEL_ENDPOINT), export_interval_millis=15000
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Auto-instrument FastAPI + HTTPX
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(SERVICE_NAME), metrics.get_meter(SERVICE_NAME)
