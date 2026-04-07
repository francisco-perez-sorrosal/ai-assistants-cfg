# AI/ML Model Serving

Local and single-machine patterns for deploying AI/ML models. Back to [SKILL.md](../SKILL.md).

## Model Serving Engines

| Engine | Primary Use | GPU Management | Concurrency | Status (2026) |
|--------|------------|----------------|-------------|---------------|
| **Ollama** | Local dev, prototyping | Static allocation | Serialized per model | Active, dominant locally |
| **vLLM** | Production serving | PagedAttention (dynamic) | Continuous batching, 3-5x Ollama | Active, dominant in prod |
| **llama.cpp** | Portable inference | Manual | Fixed throughput | Active |
| **TGI** | HF model serving | Advanced | Dynamic batching | **Maintenance mode (Dec 2025)** |

**Do not recommend TGI for new deployments.** HuggingFace recommends vLLM or SGLang as alternatives.

## Ollama

### When to Use

- Local development and prototyping
- Quick model experimentation
- Simple API access (OpenAI-compatible)
- Teams that want `docker compose up` simplicity

### Docker Compose Pattern

```yaml
services:
  ollama:
    image: ollama/ollama:0.6
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ollama_data:/root/.ollama
    ports: ["11434:11434"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # Optional: web UI for chat
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports: ["3000:8080"]
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
    depends_on:
      ollama:
        condition: service_healthy
    volumes:
      - webui_data:/app/backend/data

volumes:
  ollama_data:
  webui_data:
```

### Key Gotchas

- **Pin the image tag** -- `:latest` causes multi-GB re-downloads on updates. Pin to a specific version
- **Volume-mount model storage** -- without the volume, models are re-downloaded on every container restart
- **Serialized requests** -- Ollama processes one request per loaded model at a time. For concurrent load, run multiple instances behind a load balancer
- **macOS GPU** -- Ollama on macOS uses Metal (Apple Silicon) natively. Docker on macOS does NOT have GPU passthrough -- run Ollama as a native binary on macOS for GPU acceleration

### Model Pull on Startup

Ollama doesn't pre-pull models. Add an init container or entrypoint script:

```yaml
services:
  ollama-pull:
    image: ollama/ollama:0.6
    depends_on:
      ollama:
        condition: service_healthy
    entrypoint: ["sh", "-c", "ollama pull llama3.1:8b && ollama pull nomic-embed-text"]
    environment:
      OLLAMA_HOST: ollama:11434
    profiles: ["setup"]
```

Run once with: `docker compose --profile setup up ollama-pull`

## vLLM

### When to Use

- Production inference APIs
- High-concurrency workloads
- Large models (70B+) that need memory optimization
- Continuous batching for throughput

### Docker Compose Pattern

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    command: >
      --model meta-llama/Llama-3.1-8B-Instruct
      --max-model-len 8192
      --gpu-memory-utilization 0.9
      --port 8000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports: ["8000:8000"]
    volumes:
      - hf_cache:/root/.cache/huggingface
    environment:
      HUGGING_FACE_HUB_TOKEN: ${HF_TOKEN}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    restart: unless-stopped

volumes:
  hf_cache:
```

### Key Differences from Ollama

- **PagedAttention** -- manages GPU memory like OS virtual memory, enabling 3-5x more concurrent users on the same hardware
- **Continuous batching** -- processes multiple requests simultaneously instead of serializing
- **Requires NVIDIA GPU with CUDA** -- no CPU fallback, no Apple Silicon support
- **HuggingFace model format** -- uses HF model IDs directly, not GGUF quantized formats
- **Longer startup** -- model loading can take 1-3 minutes for large models (use `start_period` in health checks)

## GPU Memory Requirements

### VRAM Calculator Heuristic

```
VRAM (GB) ≈ (parameters_billions × bytes_per_param) + KV_cache_overhead
```

| Precision | Bytes per Param | 8B Model | 13B Model | 70B Model |
|-----------|----------------|----------|-----------|-----------|
| FP32 | 4 | 32 GB | 52 GB | 280 GB |
| FP16/BF16 | 2 | 16 GB | 26 GB | 140 GB |
| INT8 | 1 | 8 GB | 13 GB | 70 GB |
| INT4 (Q4) | 0.5 | 4 GB | 6.5 GB | 35 GB |

**KV cache overhead** at 32K context: ~4.5 GB for an 8B model at FP16. This grows linearly with context length and batch size.

### What Fits on Consumer GPUs

| GPU | VRAM | Max Model (FP16) | Max Model (Q4) | Notes |
|-----|------|-------------------|-----------------|-------|
| RTX 3060 | 12 GB | ~5B | ~13B | Budget option |
| RTX 4070 | 12 GB | ~5B | ~13B | Better compute, same VRAM |
| RTX 3090 | 24 GB | ~13B | ~30B | Best value for ML |
| RTX 4090 | 24 GB | ~13B | ~30B | Fastest consumer GPU |
| Mac M2 Pro | 16 GB shared | ~8B | ~16B | Shared with system RAM |
| Mac M2 Max | 32 GB shared | ~16B | ~35B | Good for development |
| Mac M2 Ultra | 64-192 GB | ~35B | ~70B+ | Unified memory advantage |

### GPU Sharing Methods

| Method | Isolation | GPU Support | Best For |
|--------|-----------|-------------|----------|
| **Time-slicing** | None | All NVIDIA GPUs | Simple sharing, development |
| **MPS** | Memory isolation | Volta+ (A100, H100) | Multiple lightweight inference |
| **MIG** | Full hardware isolation | A100, H100, B200 | Production multi-tenant |

**For workstations with consumer GPUs:** only time-slicing is available. The practical approach is to run one model server (Ollama or vLLM) that multiplexes access, rather than trying to share the GPU between separate processes.

## Python Environment Isolation for ML

| Tool | Speed | Conda Packages | Best For |
|------|-------|----------------|----------|
| **uv** | Fastest | No | Pure Python projects, web backends |
| **pixi** | Fast | Yes (conda-forge) | ML projects needing CUDA/C libraries |
| **conda/mamba** | Slow/Medium | Yes | Legacy ML projects |

**Guidance:** Use `uv` for FastAPI/web services. Use `pixi` for ML pipelines that need conda-forge packages (CUDA drivers, C libraries). Pixi supports both conda-forge and PyPI -- it's a superset of uv's functionality for ML use cases.

## Jupyter as a Service

For running Jupyter as a persistent service:

**Single user (systemd):**

```ini
[Service]
ExecStart=/opt/jupyter/.venv/bin/jupyter lab --no-browser --port=8888
```

**Multi-user (Docker):**

```yaml
services:
  jupyterhub:
    image: jupyterhub/jupyterhub
    ports: ["8000:8000"]
    volumes:
      - jupyterhub_data:/srv/jupyterhub
```

For 1-100 users on a single server, use [The Littlest JupyterHub (TLJH)](https://tljh.jupyter.org/).

## Combining AI Serving with Application Services

A common local pattern: API backend + database + model server.

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@db:5432/app"
      OLLAMA_URL: "http://ollama:11434"
    depends_on:
      db: { condition: service_healthy }
      ollama: { condition: service_healthy }

  db:
    image: postgres:17
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  ollama:
    image: ollama/ollama:0.6
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes: [ollama_data:/root/.ollama]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  pgdata:
  ollama_data:
```
