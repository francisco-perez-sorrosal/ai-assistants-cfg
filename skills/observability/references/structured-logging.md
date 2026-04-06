# Structured Logging

Best practices for machine-readable logging: field conventions, correlation patterns, Python library selection, and OTel integration. Reference material for the [Observability](../SKILL.md) skill.

## Core Principles

- Emit logs as **machine-readable key-value pairs** (typically JSON), not free-form text
- Each field is independently queryable -- enables aggregation, filtering, and correlation across services
- Consistent field names across all services in an organization eliminate ambiguity during incident response
- Separate log *structure* from log *rendering* -- a single log event should support JSON for production, human-readable console output for development
- Treat the logging schema as a contract: additions are safe, renames and removals are breaking changes

## Essential Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `timestamp` | When the event occurred (ISO 8601, UTC) | `2026-04-06T14:30:00.123Z` |
| `level` | Severity classification | `info`, `warn`, `error` |
| `message` | Human-readable event description | `User login succeeded` |
| `service` | Origin service name | `auth-service` |
| `trace_id` | Distributed trace correlation | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `span_id` | Current span within the trace | `00f067aa0ba902b7` |
| `request_id` | Request-scoped correlation ID | `req-abc-123` |
| `error.type` | Exception class (on error events) | `ValueError` |
| `error.message` | Error detail (on error events) | `Invalid email format` |

`trace_id` and `span_id` are injected automatically by the OTel log SDK when a trace is active -- no manual effort per log call.

## Log Level Semantics

| Level | When to Use | Examples |
|-------|-------------|---------|
| `TRACE` / `DEBUG` | Development diagnostics; **never enable in production** | SQL queries, internal state dumps, variable snapshots |
| `INFO` | Normal operation milestones worth recording | Service started, request completed, scheduled job finished |
| `WARN` | Degraded but functional state; action may be needed soon | Retry succeeded after transient failure, cache miss fallback, approaching quota limit |
| `ERROR` | Request or operation failure; requires investigation | Unhandled exception, external service timeout, data validation failure |
| `FATAL` / `CRITICAL` | System cannot continue; immediate attention required | Database connection pool exhausted, invalid configuration at startup, out-of-memory |

**Guidelines**:
- Default production log level: `INFO`. Use `WARN` and above for alerting pipelines.
- Avoid `DEBUG` in production -- it generates orders of magnitude more data and can expose sensitive internal state.
- When in doubt between `WARN` and `ERROR`, ask: "Did a user-visible operation fail?" If yes, `ERROR`. If the system self-recovered, `WARN`.

## Correlation ID Patterns

**Goal**: Link every log entry in a request's lifecycle across all services it touches.

1. **Generate at entry**: Create a unique ID at the system boundary (API gateway, load balancer, or first service). Use the OTel trace ID when tracing is active -- it already satisfies uniqueness and propagation.
2. **Propagate across boundaries**: Pass the correlation ID in HTTP headers (`X-Request-ID` or W3C `traceparent`), message queue metadata, and gRPC metadata.
3. **Bind to logger context**: Attach the ID once at request entry using the logger's context binding mechanism. All subsequent log calls within that request automatically include it.
4. **OTel automatic injection**: When the OTel log SDK is configured, `trace_id` and `span_id` are injected into every log record produced while a span is active -- zero per-log-call effort.

```python
# structlog context binding example
import structlog

logger = structlog.get_logger()

def handle_request(request_id: str) -> None:
    log = logger.bind(request_id=request_id)
    log.info("processing_started")
    # ... all subsequent log.info/warn/error calls include request_id
    log.info("processing_complete", items_processed=42)
```

**Tip**: When using both `request_id` and OTel `trace_id`, keep both. The `request_id` may originate from an upstream system that does not use OTel.

For async Python services using `contextvars`, structlog's `merge_contextvars` processor automatically propagates bound context across `await` boundaries without manual threading:

```python
# Async-safe context binding with structlog contextvars
import structlog

structlog.contextvars.bind_contextvars(request_id="req-abc-123", user_id="u-42")
# All logs in this async context now include request_id and user_id
# Works across await boundaries without explicit passing
```

## What NOT to Log

| Category | Examples | Why | Alternative |
|----------|----------|-----|-------------|
| **PII** | Names, emails, phone numbers, SSNs, addresses | Privacy regulations (GDPR, CCPA); breach liability | Log anonymized identifiers or hashed values |
| **Secrets** | API keys, tokens, passwords, connection strings | Credential exposure in log aggregation systems | Never log; mask if unavoidable (`sk-...XXXX`) |
| **Unbounded data** | Full request/response bodies, large payloads | Storage explosion; may contain embedded PII | Log a SHA-256 hash or truncated preview (first 200 chars) |
| **Health check noise** | Routine liveness/readiness probe responses | Drowns real signals in high-frequency noise | Exclude from logging or sample at 1% |

**Redaction strategy**: Apply redaction at the logger processor level, not at individual log call sites. A centralized processor ensures no field slips through.

```python
# structlog processor for PII redaction
import re

REDACT_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

def redact_pii(
    logger: object, method_name: str, event_dict: dict[str, object]
) -> dict[str, object]:
    """Replace known PII patterns with [REDACTED] in all string values."""
    for key, value in event_dict.items():
        if isinstance(value, str):
            for pattern in REDACT_PATTERNS.values():
                value = pattern.sub("[REDACTED]", value)
            event_dict[key] = value
    return event_dict
```

Add `redact_pii` to the structlog processor chain (before the renderer) to automatically scrub PII from all log output.

## Python Library Comparison

| Criterion | structlog | stdlib `logging` | loguru |
|-----------|-----------|-------------------|--------|
| **Structured output** | Native JSON/logfmt | Requires custom formatter | Built-in JSON support |
| **Context binding** | First-class `bind()` | Manual via `LoggerAdapter` or filters | Via `contextualize()` |
| **OTel integration** | Direct via processor | OTel logging SDK handler | Requires custom adapter |
| **Stdlib compatibility** | Wraps or replaces stdlib | Is the stdlib | Separate API, not compatible |
| **Library-safe** | Yes (no global state mutation) | Yes (hierarchical loggers) | No (replaces global handler) |
| **Setup complexity** | Medium (processor pipeline) | High (handlers + formatters + filters) | Low (one-liner) |

## Recommended Stack

- **Production services**: `structlog` -- structured output + context binding + OTel correlation in a composable processor pipeline. The de facto standard for Python services that need machine-readable logs.
- **Libraries**: stdlib `logging` -- zero dependencies, universally compatible. Libraries must never force a logging framework on their consumers.
- **Prototyping and CLI tools**: `loguru` -- beautiful console output, zero configuration, file rotation built in. Swap to structlog when the prototype becomes a service.

## structlog Configuration Pattern

A production-ready processor pipeline with JSON output and OTel correlation:

```python
import logging
import sys

import structlog


def configure_logging(*, json_output: bool = True, log_level: str = "INFO") -> None:
    """Configure structlog with OTel-aware JSON output for production."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
```

**Usage**:

```python
configure_logging(json_output=True)
logger = structlog.get_logger()

logger.info("server_started", port=8080, env="production")
# {"event": "server_started", "port": 8080, "env": "production",
#  "level": "info", "logger": "...", "timestamp": "2026-04-06T14:30:00Z"}
```

**Development mode**: Call `configure_logging(json_output=False)` for colored, human-readable console output using the same processor pipeline.

## OTel Log SDK Integration

When OpenTelemetry tracing is active, the OTel logging SDK bridges Python's stdlib logging to the OTel log pipeline and automatically injects `trace_id` and `span_id` into every log record.

```python
from opentelemetry import trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter

# Set up OTel log export (replace ConsoleLogExporter with OTLPLogExporter for production)
logger_provider = LoggerProvider()
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(ConsoleLogExporter())
)

# Attach to stdlib logging
otel_handler = LoggingHandler(logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)

# Now any log emitted while a span is active includes trace_id and span_id
with trace.get_tracer(__name__).start_as_current_span("my-operation"):
    logging.getLogger(__name__).info("This log is correlated with the active span")
```

**Key points**:
- The OTel handler is additive -- it does not replace structlog or other handlers
- `trace_id` and `span_id` injection is automatic; no per-log-call code changes
- In production, replace `ConsoleLogExporter` with `OTLPLogExporter` to send logs to your collector
- structlog and OTel compose cleanly: structlog handles structure and context binding, OTel handles trace correlation and export
