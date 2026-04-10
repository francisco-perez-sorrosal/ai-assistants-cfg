# TypeScript/Node.js Observability

OpenTelemetry instrumentation, structured logging, and metrics patterns for TypeScript and Node.js applications. Back to [SKILL.md](../SKILL.md).

## OpenTelemetry Setup

### Installation

```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/api \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

### SDK Initialization

Initialize the SDK **before** any other imports. Use a dedicated `instrumentation.ts` file:

```typescript
// instrumentation.ts -- must be loaded first
import { NodeSDK } from "@opentelemetry/sdk-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { Resource } from "@opentelemetry/resources";
import {
  ATTR_SERVICE_NAME,
  ATTR_SERVICE_VERSION,
} from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: process.env.SERVICE_NAME ?? "my-service",
    [ATTR_SERVICE_VERSION]: process.env.SERVICE_VERSION ?? "0.1.0",
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318/v1/traces",
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318/v1/metrics",
    }),
    exportIntervalMillis: 60_000,
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      "@opentelemetry/instrumentation-fs": { enabled: false },
      "@opentelemetry/instrumentation-dns": { enabled: false },
    }),
  ],
});

sdk.start();

process.on("SIGTERM", () => {
  sdk.shutdown().then(
    () => process.exit(0),
    () => process.exit(1),
  );
});
```

### Loading the Instrumentation

```bash
# Node.js --require flag (CommonJS)
node --require ./instrumentation.js src/index.js

# Node.js --import flag (ESM, Node 18.19+)
node --import ./instrumentation.js src/index.js

# Or via NODE_OPTIONS in package.json
{
  "scripts": {
    "start": "NODE_OPTIONS='--import ./instrumentation.js' node src/index.js"
  }
}
```

### Auto-Instrumentation Coverage

The `auto-instrumentations-node` package covers:

| Library | Instrumented | Spans Created |
|---------|-------------|---------------|
| `http`/`https` | Yes | Client and server spans |
| `express` | Yes | Route handler spans, middleware |
| `fastify` | Yes | Route handler spans |
| `pg` (node-postgres) | Yes | Database query spans |
| `mysql2` | Yes | Database query spans |
| `redis` / `ioredis` | Yes | Cache operation spans |
| `grpc` | Yes | Client and server spans |
| `aws-sdk` | Yes | AWS service call spans |
| `fetch` (undici) | Yes | HTTP client spans |

Disable noisy instrumentations that add low value:

```typescript
getNodeAutoInstrumentations({
  "@opentelemetry/instrumentation-fs": { enabled: false },    // Too noisy
  "@opentelemetry/instrumentation-dns": { enabled: false },   // Low value
  "@opentelemetry/instrumentation-net": { enabled: false },   // Low value
});
```

## Manual Instrumentation

### Creating Spans

```typescript
import { trace, SpanStatusCode } from "@opentelemetry/api";

const tracer = trace.getTracer("my-service", "1.0.0");

async function processOrder(orderId: string): Promise<Order> {
  return tracer.startActiveSpan("process-order", async (span) => {
    try {
      span.setAttribute("order.id", orderId);

      const order = await fetchOrder(orderId);
      span.setAttribute("order.total", order.total);
      span.setAttribute("order.items_count", order.items.length);

      const result = await chargePayment(order);
      span.setAttribute("payment.status", result.status);

      return result;
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(error) });
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

### Span Events

```typescript
span.addEvent("cache-miss", {
  "cache.key": cacheKey,
  "cache.backend": "redis",
});

span.addEvent("retry-attempt", {
  "retry.count": attempt,
  "retry.delay_ms": delayMs,
});
```

### Context Propagation

Context propagates automatically within `startActiveSpan`. For manual propagation across async boundaries:

```typescript
import { context, trace } from "@opentelemetry/api";

// Capture context
const currentContext = context.active();

// Restore in callback (e.g., event handlers, setTimeout)
context.with(currentContext, () => {
  const span = trace.getActiveSpan();
  // span is available here
});
```

## Structured Logging

### pino (Recommended)

```bash
npm install pino pino-pretty
```

```typescript
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  transport: process.env.NODE_ENV === "development"
    ? { target: "pino-pretty", options: { colorize: true } }
    : undefined,
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: process.env.SERVICE_NAME ?? "my-service",
    version: process.env.SERVICE_VERSION ?? "0.1.0",
  },
});
```

### Trace Correlation

Inject trace context into log entries for log-trace correlation:

```typescript
import { trace, context } from "@opentelemetry/api";

function createChildLogger(parentLogger: pino.Logger): pino.Logger {
  const span = trace.getSpan(context.active());
  if (!span) return parentLogger;

  const spanContext = span.spanContext();
  return parentLogger.child({
    trace_id: spanContext.traceId,
    span_id: spanContext.spanId,
    trace_flags: spanContext.traceFlags,
  });
}

// Usage in request handler
app.get("/api/users/:id", (req, res) => {
  const log = createChildLogger(logger);
  log.info({ userId: req.params.id }, "Fetching user");
  // ...
});
```

### winston Alternative

```typescript
import winston from "winston";

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL ?? "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json(),
  ),
  defaultMeta: { service: process.env.SERVICE_NAME },
  transports: [new winston.transports.Console()],
});
```

**pino vs winston**: pino is 5-10x faster in benchmarks due to its sync-first design. Prefer pino for high-throughput services. winston has a richer plugin ecosystem.

## Custom Metrics

```typescript
import { metrics } from "@opentelemetry/api";

const meter = metrics.getMeter("my-service", "1.0.0");

// Counter -- monotonically increasing
const requestCounter = meter.createCounter("http.requests.total", {
  description: "Total HTTP requests processed",
});

// Histogram -- value distribution
const requestDuration = meter.createHistogram("http.request.duration_ms", {
  description: "HTTP request duration in milliseconds",
  unit: "ms",
});

// UpDownCounter -- value that can increase and decrease
const activeConnections = meter.createUpDownCounter("connections.active", {
  description: "Currently active connections",
});

// Usage in middleware
app.use((req, res, next) => {
  const start = performance.now();
  activeConnections.add(1);

  res.on("finish", () => {
    const duration = performance.now() - start;
    requestCounter.add(1, {
      method: req.method,
      route: req.route?.path ?? "unknown",
      status: res.statusCode.toString(),
    });
    requestDuration.record(duration, {
      method: req.method,
      route: req.route?.path ?? "unknown",
    });
    activeConnections.add(-1);
  });

  next();
});
```

## Express/Fastify Middleware

### Error Tracking Middleware

```typescript
import { SpanStatusCode, trace } from "@opentelemetry/api";

// Express error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  const span = trace.getActiveSpan();
  if (span) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
    span.recordException(err);
  }

  logger.error({
    err,
    method: req.method,
    url: req.url,
    statusCode: 500,
  }, "Unhandled error");

  res.status(500).json({ error: "Internal server error" });
});
```

## Gotchas

- **ESM import order matters**: The instrumentation file must be loaded before any library imports. With ESM, use `--import` (not `--require`). Incorrect load order silently produces no traces.
- **Missing `span.end()`**: Forgetting to end a span causes memory leaks and missing trace data. Always use `startActiveSpan` with try/finally to guarantee `span.end()` is called.
- **High-cardinality attributes**: Do not use user IDs, email addresses, or full URLs as span attributes or metric labels. Use route templates (`/users/:id`) and bounded categories.
- **Bundler compatibility**: Webpack and esbuild may break auto-instrumentation monkey-patching. Use `--external` flags to exclude instrumented packages from bundling, or switch to manual instrumentation.
- **pino + OTel log SDK**: The OTel Logs SDK for Node.js is still maturing. For now, correlate via `trace_id`/`span_id` fields injected into pino logs rather than using the OTel Logs API directly.
- **Graceful shutdown**: Always call `sdk.shutdown()` on `SIGTERM`. Without this, the last batch of spans and metrics may be lost.
