# Local Deployment

Deep-dive into local and single-machine deployment patterns. Back to [SKILL.md](../SKILL.md).

## Docker Compose Deep-Dive

### Modern Conventions (2026)

- **Filename:** `compose.yaml` (not `docker-compose.yml`)
- **No `version:` field** -- the Compose spec dropped it; start with `services:` directly
- **CLI:** `docker compose` (plugin, not standalone `docker-compose`)

### Networking

Services in the same Compose file share a default network. Reference other services by their service name as hostname:

```yaml
services:
  app:
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@db:5432/app"
      REDIS_URL: "redis://cache:6379"
  db:
    image: postgres:17
  cache:
    image: redis:7-alpine
```

**Port mapping:** `"HOST:CONTAINER"`. Use non-default host ports to avoid conflicts with local installs:

```yaml
ports:
  - "5433:5432"   # PostgreSQL on host port 5433
  - "6380:6379"   # Redis on host port 6380
```

**Custom networks** (when services need isolation):

```yaml
services:
  app:
    networks: [frontend, backend]
  db:
    networks: [backend]
  proxy:
    networks: [frontend]

networks:
  frontend:
  backend:
```

### Volumes and Storage

| Type | Syntax | Use Case |
|------|--------|----------|
| Named volumes | `volumes: [pgdata:/var/lib/postgresql/data]` | Database persistence, model storage |
| Bind mounts | `volumes: [./src:/app/src]` | Development source code sync |
| tmpfs | `tmpfs: /tmp` | Ephemeral data, avoid disk I/O |

Named volumes survive `docker compose down`. They are destroyed with `docker compose down -v` -- warn users before running this.

### Multi-Stage Builds

Use multi-stage Dockerfiles to keep production images small:

```dockerfile
# Build stage
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Production stage
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY ./src ./src
ENV PATH="/app/.venv/bin:$PATH"
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4"]
```

### Health Checks

Every service that other services depend on needs a health check:

```yaml
services:
  db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

`start_period` gives slow-starting services (like databases applying migrations) time before health check failures count.

### Restart Policies

```yaml
services:
  app:
    restart: unless-stopped   # Restart on crash, but not if manually stopped
  db:
    restart: always           # Always restart, even after manual stop
```

For production on a single server, `unless-stopped` is the safest default -- it lets you `docker compose stop` for maintenance without auto-restart fighting you.

### Environment Management

Layer environment configuration:

```yaml
services:
  app:
    env_file:
      - .env              # Defaults (gitignored)
      - .env.local        # Local overrides (gitignored)
    environment:
      - NODE_ENV=development  # Inline overrides (highest priority)
```

Priority (highest wins): inline `environment` > last `env_file` entry > earlier `env_file` entries.

### Compose Profiles for Optional Services

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]

  db:
    image: postgres:17

  # Optional services
  pgadmin:
    image: dpage/pgadmin4
    profiles: ["admin"]
    ports: ["5050:80"]
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin

  mailhog:
    image: mailhog/mailhog
    profiles: ["debug"]
    ports: ["8025:8025", "1025:1025"]

  prometheus:
    image: prom/prometheus
    profiles: ["monitoring"]
    volumes: [./prometheus.yml:/etc/prometheus/prometheus.yml]
```

Run with: `docker compose --profile admin --profile monitoring up`

---

## Process Managers

When Docker is not wanted or not available, process managers run services natively.

### systemd (Linux)

The init system on all modern Linux distributions. Zero overhead, deep OS integration.

```ini
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/app
ExecStart=/opt/app/.venv/bin/gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4
Restart=on-failure
RestartSec=5
MemoryMax=512M
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

Key commands:
- `sudo systemctl enable myapp` -- start on boot
- `sudo systemctl start myapp` -- start now
- `journalctl -u myapp -f` -- stream logs

### launchd (macOS)

Apple's service manager. Uses XML plist files.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.myapp.server</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/app/.venv/bin/gunicorn</string>
    <string>main:app</string>
    <string>-k</string>
    <string>uvicorn.workers.UvicornWorker</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/opt/app</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/var/log/myapp/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/var/log/myapp/stderr.log</string>
</dict>
</plist>
```

Place in `~/Library/LaunchAgents/` (user agents) or `/Library/LaunchDaemons/` (system daemons).

### Procfile (Development)

Simple multi-process runner for development:

```procfile
web: uvicorn main:app --reload --port 8000
worker: celery -A app worker --loglevel=info
scheduler: celery -A app beat --loglevel=info
```

Run with `honcho start` (Python) or `foreman start` (Ruby). Not for production -- no restart on crash, no resource limits, no daemon mode.

### Process Manager Comparison

| Tool | Platform | Resource Limits | Auto-Restart | Production Use |
|------|----------|-----------------|--------------|----------------|
| systemd | Linux | Yes (cgroups) | Yes | Excellent |
| launchd | macOS | Partial | Yes | Excellent (macOS) |
| supervisord | Cross-platform | No | Yes | Good |
| PM2 | Cross-platform | No | Yes | Good (Node.js) |
| Procfile/honcho | Cross-platform | No | No | Development only |

---

## macOS Container Runtimes

| Runtime | Startup | Idle RAM | License | Best For |
|---------|---------|----------|---------|----------|
| **OrbStack** | ~2s | <1 GB | Commercial (free tier) | Fastest UX, recommended for most users |
| **Docker Desktop** | Slow | 2+ GB | Commercial ($5/mo 250+ employees) | Reference implementation, broadest compat |
| **Colima** | Medium | ~400 MB | Open source (MIT) | Terminal-first, scriptable, CI-friendly |
| **Lima** | Medium | Low | Open source (CNCF incubating) | VM-focused, Colima's foundation |

**Recommendation:** OrbStack for daily development on macOS. Colima for CI or when open-source licensing matters.

---

## Container vs Native Process Trade-offs

| Dimension | Containers (Docker Compose) | Native Processes |
|-----------|----------------------------|------------------|
| Isolation | Strong (namespace, cgroup) | Weak (shared filesystem) |
| Reproducibility | High (frozen image) | Depends on host state |
| Resource overhead | Container runtime + VM (macOS) | Near-zero |
| Dev experience | `compose up` starts everything | Per-service setup |
| GPU access | Supported via NVIDIA toolkit | Direct, lower overhead |
| Debugging | `docker exec` or volume mounts | Direct process access |
| Startup time | Seconds | Milliseconds |
| Production parity | High (same image) | Lower (host differences) |

**Default recommendation:** Docker Compose for multi-service apps. Native processes for single-service development or when container overhead is unacceptable (resource-constrained machines, bare-metal GPU performance).

---

## Single-Server Production with Compose

For Level 4 (single-server production), the stack is:

```
Internet --> Caddy (TLS + reverse proxy) --> Docker Compose services --> PostgreSQL
                                                                    --> Redis
```

**systemd manages Compose lifecycle:**

```ini
[Unit]
Description=Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/app
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```

**Production checklist:**
- [ ] Caddy with automatic HTTPS (Let's Encrypt)
- [ ] Health checks on all services
- [ ] Resource limits on all containers
- [ ] `restart: unless-stopped` on all services
- [ ] Named volumes for persistent data
- [ ] Log rotation configured (Docker daemon `json-file` driver with `max-size` and `max-file`)
- [ ] Backup strategy for database volumes
- [ ] Monitoring (at minimum: Caddy access logs + `docker stats`)
- [ ] Firewall: only ports 80, 443, and SSH open
