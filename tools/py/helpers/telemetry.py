"""Telemetry initialization and helper utilities for OpenTelemetry and Arize Phoenix."""

import os
import socket
from urllib.parse import urlparse

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_CONNECT_TIMEOUT_SECONDS = 0.5


def _is_endpoint_reachable(endpoint: str) -> bool:
    """Check whether the OTLP collector endpoint is accepting connections."""
    host = urlparse(endpoint).hostname
    port = urlparse(endpoint).port or (443 if endpoint.startswith("https://") else 80)
    if not host:
        return False

    try:
        with socket.create_connection((host, port), timeout=_CONNECT_TIMEOUT_SECONDS):
            return True
    except OSError:
        return False


def init_telemetry() -> None:
    """Initialize OpenTelemetry tracer provider with OTLP exporter pointing to Arize Phoenix."""
    # Check if telemetry is enabled via env (or default to local Phoenix)
    endpoint = (
        os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or "http://localhost:6006/v1/traces"
    )

    if not _is_endpoint_reachable(endpoint):
        logger.debug(f"OTLP collector at {endpoint} is not reachable; skipping telemetry initialization.")
        return

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
