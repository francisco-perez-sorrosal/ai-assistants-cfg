# Reverse Proxy and TLS

Patterns for reverse proxies and HTTPS configuration. Back to [SKILL.md](../SKILL.md).

## Choosing a Reverse Proxy

| Proxy | Config Complexity | Auto HTTPS | Docker Integration | Recommended For |
|-------|------------------|------------|-------------------|-----------------|
| **Caddy** | Minimal (3-5 lines) | Built-in (mkcert local, Let's Encrypt prod) | Via Caddyfile or API | **Default recommendation** -- simplest path |
| **nginx** | Moderate (15+ lines) | Manual (certbot) | Via conf files | High-traffic production, complex routing |
| **Traefik** | Low (Docker labels) | Built-in (Let's Encrypt) | Native Docker auto-discovery | Dynamic container environments |

**Default recommendation: Caddy.** It handles HTTPS automatically in both local (via mkcert) and production (via Let's Encrypt) with minimal configuration.

## Caddy

### Local Development (with mkcert TLS)

First, install mkcert and create a local CA:

```bash
# macOS
brew install mkcert nss
mkcert -install

# Generate certs for local domains
mkcert localhost 127.0.0.1 ::1 myapp.local
# Creates: localhost+3.pem and localhost+3-key.pem
```

**Caddyfile for local development:**

```caddyfile
myapp.local {
    tls ./localhost+3.pem ./localhost+3-key.pem

    handle /api/* {
        reverse_proxy app:8000
    }

    handle {
        reverse_proxy frontend:3000
    }
}
```

Add `127.0.0.1 myapp.local` to `/etc/hosts`.

### Production (automatic HTTPS)

```caddyfile
myapp.example.com {
    # TLS is automatic -- Caddy obtains and renews Let's Encrypt certs

    handle /api/* {
        reverse_proxy app:8000
    }

    handle {
        reverse_proxy frontend:3000
    }

    log {
        output file /var/log/caddy/access.log
        format json
    }
}
```

That's it. No certbot, no cron jobs, no manual renewal.

### Docker Compose Integration

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data        # TLS certificates
      - caddy_config:/config    # Caddy configuration
    restart: unless-stopped

  app:
    build: .
    # No port mapping needed -- Caddy reaches app via Docker network
    expose: ["8000"]

volumes:
  caddy_data:
  caddy_config:
```

**Key pattern:** Services behind Caddy use `expose` (no host port mapping), not `ports`. Caddy handles all external traffic on ports 80 and 443.

### Caddy Gotchas

- **HTTPS by default** -- Caddy enables HTTPS even for `localhost`. Use `http://localhost` explicitly if you want plain HTTP
- **Port 80 and 443 must be free** -- Caddy binds to both for HTTP->HTTPS redirect and ACME challenges
- **`caddy_data` volume is critical** -- contains TLS certificates. Losing this volume forces re-issuance (rate-limited by Let's Encrypt)

## nginx

### When nginx Over Caddy

- Need maximum raw throughput (nginx is slightly faster for static files and high-concurrency scenarios)
- Complex routing rules (regex-based location matching, request rewriting)
- Team already has nginx expertise
- Need modules like ModSecurity (WAF) or RTMP (streaming)

### Basic Reverse Proxy

```nginx
server {
    listen 80;
    server_name myapp.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name myapp.example.com;

    ssl_certificate /etc/letsencrypt/live/myapp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myapp.example.com/privkey.pem;

    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
    }
}
```

### Docker Compose with certbot

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot

  certbot:
    image: certbot/certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    entrypoint: >
      sh -c "certbot certonly --webroot -w /var/www/certbot
      --email admin@example.com -d myapp.example.com --agree-tos --non-interactive
      && sleep 12h && certbot renew"

volumes:
  certbot_certs:
  certbot_www:
```

## Traefik

### When Traefik Over Caddy

- Dynamic container environments where services come and go
- Need dashboard for route visualization
- Complex middleware chains (rate limiting, circuit breakers, retries)
- Multiple domains with different TLS configurations

### Docker Compose with Auto-Discovery

```yaml
services:
  traefik:
    image: traefik:v3.3
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports: ["80:80", "443:443"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_acme:/acme

  app:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`myapp.example.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.app.tls.certresolver=letsencrypt"
      - "traefik.http.services.app.loadbalancer.server.port=8000"

volumes:
  traefik_acme:
```

**Key pattern:** Traefik discovers services via Docker labels. No separate configuration file needed -- routing rules are co-located with the service definition.

## Decision Summary

| Scenario | Use | Why |
|----------|-----|-----|
| Getting started, most projects | Caddy | Simplest HTTPS, minimal config |
| High-traffic production, static files | nginx | Maximum throughput |
| Dynamic microservices, frequent deploys | Traefik | Auto-discovery via Docker labels |
| Local development HTTPS | Caddy + mkcert | One-time setup, trusted local certs |
