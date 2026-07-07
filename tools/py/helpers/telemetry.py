"""Telemetry initialization and helper utilities for OpenTelemetry and Arize Phoenix."""

import os
from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import StatusCode


def init_telemetry() -> None:
    """Initialize OpenTelemetry tracer provider with OTLP exporter pointing to Arize Phoenix."""
    # Check if telemetry is enabled via env (or default to local Phoenix)
    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "http://localhost:6006/v1/traces"

    try:
        # Avoid duplicate initialization
        current_provider = trace.get_tracer_provider()
        if isinstance(current_provider, TracerProvider):
            return

        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        logger.info(f"OpenTelemetry tracing initialized. Exporting to Phoenix at {endpoint}")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}")



# Initialize telemetry immediately on module import
init_telemetry()


def get_tracer(name: str) -> trace.Tracer:
    """Get or create an OpenTelemetry tracer with the specified name."""
    return trace.get_tracer(name)
