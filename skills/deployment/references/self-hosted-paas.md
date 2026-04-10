# Self-Hosted PaaS

PaaS experience on your own servers: Coolify, Dokku, CapRover, and Docker Compose as a PaaS descriptor. Back to [SKILL.md](../SKILL.md).

## When to Self-Host

Self-hosted PaaS makes sense when:

- **Data sovereignty**: Regulations require data to stay on specific hardware or geography
- **Cost at scale**: Cloud PaaS costs exceed a dedicated server at 3+ services running 24/7
- **Existing hardware**: Spare servers, homelab, or on-premises infrastructure available
- **Learning**: Understanding deployment internals without cloud abstraction

Self-hosted PaaS does NOT make sense when:

- Team lacks Linux sysadmin experience (security patches, disk management, networking)
- High availability requirements (multi-region, automated failover)
- Rapid scaling needs (autoscaling on demand)

## Platform Comparison

| Feature | Coolify | Dokku | CapRover |
|---------|---------|-------|----------|
| **Model** | GUI dashboard + API | CLI-first (Heroku-like) | Web dashboard |
| **Deploy from** | GitHub, Docker, Compose | Git push, Docker | Git push, Docker, one-click apps |
| **Multi-server** | Yes (built-in) | No (single server) | Yes (worker nodes) |
| **Database management** | Built-in provisioning | Plugin-based | One-click apps |
| **SSL/TLS** | Automatic (Let's Encrypt) | Plugin (letsencrypt) | Automatic (Let's Encrypt) |
| **Resource isolation** | Docker-based | Docker-based | Docker-based |
| **Install effort** | One script | One script | One script |
| **Maintenance burden** | Low (auto-updates) | Medium (manual updates) | Medium |

## Coolify

The most feature-complete self-hosted PaaS. Recommended default for new self-hosted deployments.

### Installation

```bash
# On a fresh Ubuntu/Debian server (requires root)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Requirements: 2 CPU, 2GB RAM minimum. 4 CPU, 4GB RAM recommended.

### Core Concepts

- **Projects**: Logical groupings (like Railway projects)
- **Resources**: Services, databases, and storage within a project
- **Servers**: Physical/virtual machines managed by Coolify
- **Destinations**: Docker networks on each server

### Deploying a Service

```bash
# Via the web UI (port 8000 by default):
# 1. Create a project
# 2. Add a resource → Application
# 3. Connect GitHub repo or paste Dockerfile
# 4. Configure environment variables
# 5. Deploy
```

Coolify supports `docker-compose.yaml` files directly -- upload your existing Compose file and Coolify manages the lifecycle.

### Database Provisioning

Built-in support for PostgreSQL, MySQL, MariaDB, MongoDB, Redis. One-click creation with automatic backup scheduling.

```
# Backups are stored locally or pushed to S3-compatible storage
# Configure via: Settings → Backup → S3 endpoint
```

### Multi-Server Setup

```
Primary Server (Coolify dashboard)
  └── Worker Server 1 (connected via SSH)
  └── Worker Server 2 (connected via SSH)
```

Add servers via the dashboard: Settings → Servers → Add. Coolify connects over SSH and installs Docker automatically.

### Gotchas

- **Single point of failure**: The Coolify dashboard server is the control plane. If it goes down, deployments cannot be managed (running services continue).
- **Backup responsibility**: Coolify manages database backups, but you must configure offsite storage. Local-only backups are useless if the disk fails.
- **Networking complexity**: Multi-server networking requires proper firewall rules. Services on different servers cannot use Docker DNS.

## Dokku

Heroku-like experience via `git push`. Best for developers comfortable with CLI.

### Installation

```bash
# On Ubuntu 22.04+
wget -NP . https://dokku.com/install/v0.34.x/bootstrap.sh
sudo DOKKU_TAG=v0.34.9 bash bootstrap.sh
```

### Core Workflow

```bash
# On the server
dokku apps:create my-app
dokku postgres:create my-db
dokku postgres:link my-db my-app

# On your workstation
git remote add dokku dokku@server:my-app
git push dokku main
```

### Configuration

```bash
# Environment variables
dokku config:set my-app DATABASE_URL="postgresql://..."

# Domains and SSL
dokku domains:add my-app myapp.example.com
dokku letsencrypt:enable my-app

# Scaling
dokku ps:scale my-app web=2 worker=1

# Resource limits
dokku resource:limit my-app --memory 512 --cpu 50
```

### Buildpacks vs Docker

Dokku supports both Heroku buildpacks (auto-detected) and Dockerfiles:

```bash
# Force Docker deployment
echo "Dockerfile" > .dokku-builder

# Or use a specific buildpack
dokku buildpacks:add my-app https://github.com/heroku/heroku-buildpack-python
```

### Gotchas

- **Single-server only**: No built-in clustering. For multi-server, consider Coolify or manual Docker Swarm.
- **Plugin ecosystem**: Databases, Let's Encrypt, and advanced features require plugins. Most are community-maintained.
- **No web dashboard**: CLI only. Some community dashboards exist but are not official.

## CapRover

Web-based PaaS with a one-click app marketplace.

### Installation

```bash
# On a server with Docker installed
docker run -p 80:80 -p 443:443 -p 3000:3000 \
  -e ACCEPTED_TERMS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v captain-data:/captain \
  caprover/caprover
```

### One-Click Apps

CapRover's marketplace includes 100+ pre-configured apps: PostgreSQL, Redis, WordPress, Gitea, Minio, and more. Deploy via the web dashboard with a single click.

### CLI Deployment

```bash
npm install -g caprover
caprover login
caprover deploy           # Interactive deployment from local directory
```

### Worker Nodes

```bash
# On the worker server
docker swarm join --token <token> <captain-ip>:2377
```

CapRover uses Docker Swarm for multi-node orchestration. Services can be scheduled across nodes.

### Gotchas

- **Docker Swarm dependency**: CapRover relies on Docker Swarm, which has less community momentum than Kubernetes. Swarm is stable but sees fewer updates.
- **Limited auto-scaling**: No built-in autoscaling. Manual replica count adjustment via dashboard.
- **Marketplace quality varies**: One-click apps are community-contributed. Test thoroughly before production use.

## Docker Compose as Self-Hosted PaaS

For teams that do not need a PaaS dashboard, Docker Compose with systemd provides a minimal self-hosted deployment:

### Setup

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/myapp
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose pull && /usr/bin/docker compose up -d --remove-orphans

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable myapp
sudo systemctl start myapp
```

### Update Workflow

```bash
cd /opt/myapp
git pull origin main
sudo systemctl reload myapp   # Pulls new images and recreates changed services
```

### When This Is Enough

- 1-3 services on a single server
- Infrequent deployments (weekly, not hourly)
- Team is comfortable with SSH and systemd
- No need for GitHub-triggered auto-deploy

### When to Upgrade to a PaaS

- Need auto-deploy from GitHub pushes
- Multiple team members deploying
- Managing 4+ applications on the same server
- Need a web dashboard for monitoring and logs

## Security Baseline

All self-hosted PaaS setups must address:

| Concern | Minimum Action |
|---------|---------------|
| **SSH hardening** | Key-only auth, disable root login, non-standard port |
| **Firewall** | Allow only 80, 443, SSH. Block all other inbound traffic |
| **Updates** | Unattended security updates (`unattended-upgrades` on Ubuntu) |
| **TLS** | Let's Encrypt for all public-facing services |
| **Backups** | Automated database backups to offsite storage (S3, B2) |
| **Monitoring** | At minimum: disk space, memory, and service health alerts |
