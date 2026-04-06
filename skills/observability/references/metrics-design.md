# Metrics Design

Metric type selection, naming conventions, cardinality management, and implementation patterns for application and infrastructure metrics. Reference material for the [Observability](../SKILL.md) skill.

## Metric Type Selection

Choose the metric type based on the value's behavior over time.

| Type | Behavior | Suffix Convention | Use When |
|------|----------|-------------------|----------|
| **Counter** | Monotonically increasing | `_total` | Counting events: requests, errors, bytes sent |
| **Gauge** | Goes up and down | (none) | Current values: temperature, queue length, active connections |
| **Histogram** | Samples into buckets | `_seconds`, `_bytes` | Distributions: request duration, response sizes |
| **Summary** | Client-side quantiles | `_seconds` | Pre-calculated percentiles (prefer histogram in most cases) |

**Selection heuristic:**

1. Can this value decrease? **No** -- use a counter.
2. Can this value decrease? **Yes** -- use a gauge.
3. Do you need percentiles or distribution analysis? **Yes** -- use a histogram.
4. Must percentiles be pre-calculated on the client? **Yes** -- use a summary. Otherwise, prefer histogram -- it supports aggregation across instances, while summary does not.

## Prometheus Naming Conventions

Metric names use `snake_case` with a single-word application prefix that identifies the domain or service.

**Rules:**

- Include **base units** (plural) as suffix: `_seconds`, `_bytes`, `_meters`, `_ratio`
- Use **base units**: seconds (not milliseconds), bytes (not kilobytes), ratio 0-1 (not percent)
- Accumulating counts: suffix `_total` (e.g., `http_requests_total`)
- Info metrics: suffix `_info` for metadata pseudo-metrics (e.g., `build_info`)
- Timestamps: suffix `_timestamp_seconds` for recorded timestamps

**Examples:**

```
http_request_duration_seconds        # histogram -- request latency
http_requests_total                  # counter -- total request count
process_resident_memory_bytes        # gauge -- current memory usage
node_cpu_seconds_total               # counter -- CPU time consumed
myapp_cache_hit_ratio                # gauge -- cache hit rate 0-1
myapp_build_info                     # info -- build metadata labels
myapp_last_sync_timestamp_seconds    # gauge -- epoch of last sync
```

## Cardinality Management

### The Cardinality Problem

Each unique combination of label values creates a separate time series in the metrics backend. A metric with three labels, each having 10 values, produces 1,000 time series. Labels with unbounded values -- user IDs, email addresses, IP addresses, full request paths -- cause **cardinality explosion**: millions of time series that overwhelm storage, slow queries, and increase costs.

### Rules for Bounded Labels

- Labels must have **bounded, known value sets**: HTTP methods (`GET`, `POST`, `PUT`, `DELETE`), status code classes (`2xx`, `3xx`, `4xx`, `5xx`), deployment regions
- **Never** use user IDs, email addresses, IP addresses, or session tokens as label values
- Path labels should be **route templates** (`/api/users/{id}`), not actual paths (`/api/users/12345`)
- Limit labels to values with **fewer than 100 unique entries** per label
- Monitor cardinality via the `scrape_series_added` metric in Prometheus

### When Label Cardinality Is Too High

If you need high-cardinality breakdowns (per-user, per-request), use trace attributes or structured log fields instead of metric labels. Metrics are for aggregated trends; traces and logs carry per-event detail.

```
# Wrong -- unbounded label creates millions of series
http_requests_total{user_id="u-abc123", path="/api/users/12345"}

# Right -- bounded labels, high-cardinality data in traces
http_requests_total{method="GET", handler="/api/users/{id}", status="200"}
```

## RED Method Implementation

For each service endpoint, track **R**ate, **E**rrors, and **D**uration. This is the standard methodology for request-driven services (APIs, web servers, microservices).

### Prometheus Metric Examples

```
# Rate -- requests per second (counter, derive rate with PromQL)
http_requests_total{method="GET", handler="/api/users", status="200"}
http_requests_total{method="POST", handler="/api/orders", status="201"}

# Errors -- error responses (same counter, filter by status label)
http_requests_total{method="GET", handler="/api/users", status="500"}
http_requests_total{method="POST", handler="/api/orders", status="422"}

# Duration -- request latency distribution (histogram)
http_request_duration_seconds_bucket{method="GET", handler="/api/users", le="0.1"}
http_request_duration_seconds_bucket{method="GET", handler="/api/users", le="0.5"}
http_request_duration_seconds_bucket{method="GET", handler="/api/users", le="1.0"}
```

### Python Implementation

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "handler", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "handler"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def handle_request(method: str, handler: str) -> None:
    """Example: instrument a request handler with RED metrics."""
    with REQUEST_DURATION.labels(method=method, handler=handler).time():
        status = process_request(method, handler)
    REQUEST_COUNT.labels(method=method, handler=handler, status=str(status)).inc()
```

## USE Method Implementation

For each infrastructure resource, track **U**tilization, **S**aturation, and **E**rrors. This complements RED (which covers services) by covering the resources those services depend on.

### Metric Examples by Resource

**CPU:**

```
node_cpu_utilization_ratio           # gauge -- fraction of CPU time in use (0-1)
node_cpu_runqueue_length             # gauge -- saturation: processes waiting for CPU
node_cpu_errors_total                # counter -- hardware/software CPU errors
```

**Memory:**

```
node_memory_utilization_ratio        # gauge -- fraction of memory in use (0-1)
node_memory_swap_bytes               # gauge -- saturation: swap usage indicates pressure
node_memory_oom_kills_total          # counter -- out-of-memory kill events
```

**Disk:**

```
node_disk_utilization_ratio          # gauge -- fraction of disk capacity used (0-1)
node_disk_io_queue_length            # gauge -- saturation: I/O requests waiting
node_disk_errors_total               # counter -- read/write errors
```

**Network:**

```
node_network_utilization_ratio       # gauge -- fraction of bandwidth in use (0-1)
node_network_receive_queue_length    # gauge -- saturation: receive queue depth
node_network_errors_total            # counter -- transmit/receive errors
```

## SLI-Driven Metric Selection

Choose metrics that directly measure what users experience, not internal system health.

| User Concern | SLI Type | Metric Implementation | SLO Example |
|-------------|----------|----------------------|-------------|
| "Is it available?" | Availability | `successful_requests / total_requests` | 99.9% over 30 days |
| "Is it fast?" | Latency | `p99(http_request_duration_seconds)` | < 200ms at p99 over 30 days |
| "Is it correct?" | Correctness | `correct_responses / total_responses` | 99.99% over 30 days |
| "Is it fresh?" | Freshness | `time_since_last_update_seconds` | < 60s at p99 over 30 days |
| "Can I use it?" | Throughput | Sustained request rate at acceptable latency | 1000 rps at p99 < 200ms |

### Deriving SLO Targets from SLIs

1. **Measure current performance**: collect baseline SLI values over 2-4 weeks
2. **Set targets slightly below baseline**: if current availability is 99.95%, set SLO at 99.9%
3. **Calculate error budget**: `budget = 1 - SLO_target` (e.g., 0.1% = 43.2 minutes/month of allowed downtime)
4. **Define budget policies**: what happens when budget is exhausted (feature freeze, reliability sprint)
5. **Review quarterly**: tighten SLOs as reliability improves, but never tighter than users actually need

## Python Implementation

### prometheus-client Library

The standard Python client for Prometheus exposition.

```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Counter -- monotonically increasing
EVENTS_PROCESSED = Counter(
    "myapp_events_processed_total",
    "Total events processed",
    labelnames=["event_type"],
)

# Gauge -- current value
ACTIVE_CONNECTIONS = Gauge(
    "myapp_active_connections",
    "Number of active connections",
)

# Histogram -- distribution with configurable buckets
PROCESSING_TIME = Histogram(
    "myapp_processing_duration_seconds",
    "Time to process an event",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# Usage
EVENTS_PROCESSED.labels(event_type="order").inc()
ACTIVE_CONNECTIONS.inc()     # connection opened
ACTIVE_CONNECTIONS.dec()     # connection closed

with PROCESSING_TIME.time():
    process_event()

# Expose metrics on port 8000
start_http_server(8000)
```

### OTel Metrics SDK

The OpenTelemetry metrics API provides vendor-neutral instrumentation that can export to Prometheus, OTLP, and other backends.

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Initialize the MeterProvider with an OTLP exporter
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics"),
    export_interval_millis=60000,
)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("myapp")

# Create instruments
request_counter = meter.create_counter(
    name="myapp.requests",
    description="Total requests handled",
    unit="1",
)

active_tasks = meter.create_up_down_counter(
    name="myapp.active_tasks",
    description="Currently active background tasks",
    unit="1",
)

duration_histogram = meter.create_histogram(
    name="myapp.request.duration",
    description="Request processing duration",
    unit="s",
)

# Usage
request_counter.add(1, {"method": "GET", "handler": "/api/users"})
active_tasks.add(1)
active_tasks.add(-1)
duration_histogram.record(0.045, {"method": "GET", "handler": "/api/users"})
```

### When to Use Each

- **prometheus-client**: When Prometheus is your metrics backend and you want native Prometheus exposition format, histogram buckets, and PromQL-optimized metric types
- **OTel Metrics SDK**: When you need vendor-neutral instrumentation, export to multiple backends (OTLP, Prometheus, custom), or already use OTel for tracing and want a unified SDK

## OTel Metrics vs Prometheus

OpenTelemetry and Prometheus address different layers of the metrics stack.

- **OTel** is the **instrumentation API**: vendor-neutral, supports multiple backends, covers metrics + traces + logs in a single SDK. Use OTel when you want portability across observability vendors or a unified instrumentation layer.
- **Prometheus** is a **metrics backend and query language**: pull-based collection, local TSDB storage, PromQL for alerting and dashboards. Prometheus also defines a client library API, but it is Prometheus-specific.

**How they connect**: The OTel SDK can export metrics to Prometheus via the `opentelemetry-exporter-prometheus` package (exposing a Prometheus scrape endpoint) or via the OTel Collector's Prometheus exporter. This means you can instrument with OTel and store/query with Prometheus.

**Practical guidance**: Instrument application code with the OTel metrics API for portability. Use Prometheus for storage, querying, and alerting when it is your metrics backend. The two are complementary, not competing.
