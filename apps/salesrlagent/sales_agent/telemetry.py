"""Content-free JSON logs, correlated spans, OTLP traces and metrics."""
import json
import logging
import os
import time
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


class JsonFormatter(logging.Formatter):
    def format(self, record):
        context = trace.get_current_span().get_span_context()
        return json.dumps({'timestamp': time.time(), 'level': record.levelname,
                           'event': record.getMessage(), 'trace_id': format(context.trace_id, '032x'),
                           **getattr(record, 'fields', {})})


def configure():
    logger = logging.getLogger('sales_agent')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    resource = Resource.create({'service.name': 'salesrlagent', 'service.version': '0.1.0'})
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    readers = []
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip('/') + '/v1/traces')))
        readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint.rstrip('/') + '/v1/metrics'), export_interval_millis=10000))
    trace.set_tracer_provider(provider)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=readers))
    return logger


logger = configure()
tracer = trace.get_tracer('sales_agent')
meter = metrics.get_meter('sales_agent')
turns = meter.create_counter('sales.turns')
latency = meter.create_histogram('sales.turn.duration', unit='ms')
feedback = meter.create_counter('sales.feedback')
