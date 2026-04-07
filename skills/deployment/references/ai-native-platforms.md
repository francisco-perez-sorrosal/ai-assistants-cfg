# AI-Native Platforms

Deployment patterns for GPU-first cloud platforms. Back to [SKILL.md](../SKILL.md).

## What Makes AI-Cloud Different

AI-native platforms differ from traditional cloud in structural ways:

1. **GPU as first-class resource** -- GPU type/count is a primary scheduling dimension, not an afterthought
2. **Model lifecycle awareness** -- platforms understand training, fine-tuning, and inference as distinct workload types
3. **Data locality optimization** -- model weights need high-bandwidth storage-to-compute paths
4. **Scale-to-zero** -- GPU idle time is extremely costly; aggressive scale-to-zero is essential
5. **Specialized networking** -- InfiniBand, NVLink for distributed training

## Platform Spectrum

```
More abstraction / Less control                         More control / More complexity
<---------------------------------------------------------------------->
Modal          RunPod         CoreWeave/Nebius          AWS/GCP/Azure
(Python         (Container     (K8s/Slurm +              (Full cloud +
decorators)     pods)          GPU-optimized)             GPU instances)
```

## Modal -- Python-First Serverless

**Best for:** Teams that want the simplest path to GPU workloads in the cloud. Python-native, no YAML, no Dockerfiles required.

### Core Abstractions

```python
import modal

app = modal.App("my-ml-app")

# Environment defined as Python objects
image = modal.Image.debian_slim().pip_install("torch", "transformers", "vllm")

# Serverless function with GPU
@app.function(gpu="A100", image=image, timeout=600)
def train_model(dataset_path: str):
    import torch
    # training code
    return metrics

# Stateful class -- model loaded once, reused across requests
@app.cls(gpu="T4", image=image)
class Predictor:
    @modal.enter()
    def load_model(self):
        self.model = load_checkpoint("s3://models/latest")

    @modal.method()
    def predict(self, input_data):
        return self.model(input_data)

# Web endpoint (auto-generates URL)
@app.function(gpu="T4", image=image)
@modal.web_endpoint()
def api(request):
    return {"result": Predictor().predict.remote(request.json)}

# Scheduled batch job
@app.function(schedule=modal.Cron("0 2 * * *"), gpu="A100")
def nightly_retrain():
    pass
```

### Key Abstractions

| Abstraction | Purpose | Example |
|-------------|---------|---------|
| `@app.function()` | Stateless serverless function | Batch processing, one-off tasks |
| `@app.cls()` | Stateful class (model loaded once) | Inference serving |
| `@modal.web_endpoint()` | HTTP endpoint (auto-URL) | REST APIs |
| `modal.Image` | Container environment (Python-defined) | `.pip_install()`, `.apt_install()` |
| `modal.Volume` | Persistent storage | Model weights, datasets |
| `modal.Secret` | Secret management | API keys, tokens |

### GPU Selection

```python
@app.function(gpu="T4")           # Budget inference
@app.function(gpu="A10G")         # Mid-range inference
@app.function(gpu="A100")         # Training, large model inference
@app.function(gpu="A100-80GB")    # Large models, big batch sizes
@app.function(gpu="H100")         # Maximum throughput
@app.function(gpu="any")          # Any available GPU
```

### Deployment Commands

```bash
modal serve app.py      # Ephemeral deployment for testing (hot-reloads)
modal deploy app.py     # Persistent production deployment
modal run app.py        # One-off execution
```

### Key Characteristics

- **Sub-second cold starts** (claimed) for warm containers
- **Scale-to-zero** -- no cost when idle
- **Container images built remotely** -- no local Docker needed
- **Volume mounts** for caching model weights across invocations
- **OpenAI-compatible** endpoints when using `@modal.web_endpoint()`

### Gotchas

- **Vendor lock-in** -- Modal's Python decorators are proprietary. Migrating requires significant rework
- **No local emulation** -- `modal serve` runs remotely, not locally. Test logic independently before deploying
- **Cold start variability** -- first request after idle can take 5-30s depending on image size and GPU availability
- **Cost awareness** -- GPU time is billed per-second, but forgotten deployments with `min_replicas > 0` accumulate costs

## CoreWeave -- Kubernetes-Native GPU Cloud

**Best for:** Teams with Kubernetes expertise who want GPU-optimized infrastructure without managing bare metal.

### Deployment Model

All workloads are Kubernetes resources. CoreWeave extends K8s with AI-specific CRDs:

| CRD | Purpose |
|-----|---------|
| `InferenceService` | Model serving with autoscaling, traffic splitting |
| `TrainingJob` | Distributed training orchestration |
| `GPUPool` | GPU resource allocation and scheduling |

### Example: InferenceService

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-inference
spec:
  predictor:
    containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
          - "--model=meta-llama/Llama-3.1-70B-Instruct"
          - "--tensor-parallel-size=2"
        resources:
          limits:
            nvidia.com/gpu: 2
          requests:
            nvidia.com/gpu: 2
            memory: "80Gi"
```

### Key Characteristics

- **Bare-metal Kubernetes** optimized for GPU workloads
- **Kueue** for AI workload scheduling (K8s 1.31+)
- **50,000+ GPU clusters** demonstrated
- **If you know K8s, you know CoreWeave** -- extends rather than replaces

### When CoreWeave Over Modal

- Team already has Kubernetes expertise
- Need fine-grained resource control
- Multi-node distributed training
- Existing K8s manifests to port over

## RunPod -- GPU Marketplace

**Best for:** Cost-sensitive GPU workloads, quick experimentation, batch processing.

### Two Deployment Models

**Pods (persistent):**

```bash
runpodctl create pod \
  --name "training-job" \
  --gpu-type "NVIDIA A100 80GB" \
  --gpu-count 1 \
  --image "pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel" \
  --volume-size 100
```

**Serverless (scale-to-zero):**

```python
# handler.py
def handler(event):
    prompt = event["input"]["prompt"]
    # Run inference
    return {"output": result}
```

Deploy with a Docker image containing the handler.

### Pricing Model

- **Secure Cloud:** Fixed pricing, dedicated hardware
- **Community Cloud:** Lower cost, shared infrastructure, spot-like availability
- **Serverless:** Per-second billing, scale-to-zero

### When RunPod Over Modal

- Budget is the primary constraint
- Need SSH access to GPU machines
- Want to run custom Docker images without framework changes
- Training workloads that need persistent GPU access

## Nebius -- AI Training Infrastructure

**Best for:** Large-scale distributed training, organizations needing reserved GPU capacity.

### Service Tiers

| Tier | Model | Best For |
|------|-------|----------|
| **Managed Kubernetes** | Standard K8s + topology-aware GPU scheduling | Teams with K8s experience |
| **Managed Slurm** | HPC-style job scheduling | Research teams, training-heavy |
| **Direct compute** | GPU VMs with pre-installed NVIDIA drivers | Maximum control |

### Key Differentiators

- **Purpose-built for multi-node training** -- InfiniBand networking standard
- **Topology-aware scheduling** -- places related jobs on physically proximate GPUs
- **Capacity Blocks** -- reserved GPU capacity with guaranteed availability
- **Latest hardware** -- GB300, HGX B300, HGX H200 available

### When Nebius

- Distributed training across 100+ GPUs
- Need guaranteed capacity (no spot interruptions)
- InfiniBand networking for training throughput

## GPU Marketplace Comparison

| Platform | Model | Min Cost (A100/hr) | Scale-to-Zero | K8s | SSH | Best For |
|----------|-------|---------------------|----------------|-----|-----|----------|
| **Modal** | Serverless | ~$2.78 | Yes | No | No | Simplest dev experience |
| **RunPod** | Pods + Serverless | ~$1.64 (community) | Serverless only | No | Yes | Cost-sensitive |
| **CoreWeave** | K8s | ~$2.06 | Via HPA | Yes | Via pod | K8s teams |
| **Nebius** | IaaS + K8s + Slurm | Custom | No | Yes | Yes | Large-scale training |
| **Lambda Labs** | Dedicated VMs | ~$1.29 | No | Yes | Yes | Dedicated hardware |
| **Vast.ai** | P2P marketplace | ~$0.80 (auction) | No | No | Yes | Cheapest, experimental |

## Platform Selection Decision Tree

```
Need GPU in the cloud?
├── Simplest experience (no K8s, no YAML) --> Modal
├── Budget is primary concern --> RunPod (or Vast.ai for experimental)
├── Team knows Kubernetes --> CoreWeave
├── Large-scale training (100+ GPUs) --> Nebius or CoreWeave
├── Want dedicated hardware --> Lambda Labs
└── Just need one-off GPU access --> RunPod Pods or Lambda on-demand
```

## Migrating from Local to AI-Cloud

### From Ollama (local) to Modal (cloud)

Local pattern:

```python
# Local: call Ollama API
response = requests.post("http://localhost:11434/api/generate",
    json={"model": "llama3.1:8b", "prompt": prompt})
```

Cloud pattern:

```python
# Cloud: Modal function
@app.cls(gpu="T4", image=vllm_image)
class LLMService:
    @modal.enter()
    def load(self):
        from vllm import LLM
        self.llm = LLM("meta-llama/Llama-3.1-8B-Instruct")

    @modal.method()
    def generate(self, prompt: str):
        return self.llm.generate(prompt)
```

**Key differences:**
- Local uses GGUF quantized models; cloud uses HuggingFace FP16/BF16
- Local is always-on; cloud scales to zero between requests
- Local serves one request at a time (Ollama); cloud handles concurrent requests (vLLM)
- Local costs hardware only; cloud costs per-GPU-second

### From vLLM (local) to vLLM (CoreWeave)

The vLLM configuration translates almost directly to a K8s manifest. The main changes are:
- Container image stays the same
- GPU resources specified as K8s resource requests
- Health checks become readiness/liveness probes
- Environment variables become ConfigMaps/Secrets

This makes vLLM a good choice when you expect to move from local to cloud -- the migration path is well-defined.
