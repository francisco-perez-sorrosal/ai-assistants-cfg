# Kubernetes Patterns

When Kubernetes is warranted, essential patterns, and managed K8s comparison. Back to [SKILL.md](../SKILL.md).

## When Kubernetes Is Warranted

Kubernetes adds significant operational complexity. Use it only when the benefits outweigh that cost.

### Use K8s When

- **5+ services** with complex inter-service networking (service mesh, mTLS, traffic policies)
- **Multi-team ownership** where teams deploy independently to shared infrastructure
- **Complex scaling requirements** beyond simple horizontal autoscaling (custom metrics, KEDA event-driven scaling)
- **Stateful workloads** requiring operator patterns (databases, message queues with specific lifecycle management)
- **Compliance requirements** demanding namespace isolation, network policies, RBAC at the workload level
- **Team has K8s expertise** -- the operational tax is real; do not adopt K8s as a learning exercise for production systems

### Do NOT Use K8s When

- Fewer than 5 services (Cloud Run, ECS, or PaaS handles this with less overhead)
- Single team deploying everything (no multi-tenancy benefit)
- Budget-constrained (managed K8s control planes cost $70-150/month before any workloads)
- No one on the team has operated K8s in production before

## Essential Resources

### Pod

The smallest deployable unit. Usually wraps a single container plus optional sidecars.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  containers:
    - name: app
      image: my-app:1.0.0
      ports:
        - containerPort: 8000
      resources:
        requests:
          cpu: 250m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
      readinessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 15
        periodSeconds: 20
```

**Never deploy bare Pods.** Always use a Deployment (or StatefulSet) to manage Pod lifecycle.

### Deployment

Manages a set of identical Pods with rolling updates.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:1.0.0
          # ... same as Pod spec above
```

### Service

Exposes Pods internally or externally.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP    # Internal only (default)
  # type: LoadBalancer  # External with cloud LB
  # type: NodePort      # External on node ports
```

### Ingress

Routes external HTTP traffic to Services.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts: [myapp.example.com]
      secretName: myapp-tls
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

### ConfigMap and Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@db:5432/app"
```

Reference in Pod spec:

```yaml
envFrom:
  - configMapRef:
      name: app-config
  - secretRef:
      name: app-secrets
```

## Deployment Patterns

### Rolling Update (Default)

Gradually replaces old Pods with new ones. Zero-downtime when health checks are configured.

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 25%
    maxSurge: 25%
```

### Blue-Green

Run two complete environments. Switch traffic atomically via Service selector update.

```bash
# Deploy green alongside blue
kubectl apply -f deployment-green.yaml

# Verify green is healthy
kubectl rollout status deployment/my-app-green

# Switch traffic
kubectl patch service my-app -p '{"spec":{"selector":{"version":"green"}}}'

# Remove blue after validation
kubectl delete deployment my-app-blue
```

### Canary

Route a percentage of traffic to the new version. Requires a service mesh (Istio, Linkerd) or ingress controller with traffic splitting.

```yaml
# Istio VirtualService for 90/10 split
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts: [my-app]
  http:
    - route:
        - destination:
            host: my-app
            subset: stable
          weight: 90
        - destination:
            host: my-app
            subset: canary
          weight: 10
```

## Autoscaling

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### KEDA (Event-Driven Scaling)

Scale based on external metrics: queue depth, HTTP request rate, cron schedules, database connections.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: my-app
spec:
  scaleTargetRef:
    name: my-app
  minReplicaCount: 0    # Scale to zero
  maxReplicaCount: 50
  triggers:
    - type: rabbitmq
      metadata:
        queueName: tasks
        host: amqp://rabbitmq:5672
        queueLength: "10"
```

## Managed K8s Comparison

| Feature | GKE Autopilot | EKS | AKS |
|---------|---------------|-----|-----|
| **Control plane cost** | Free | $73/month | Free |
| **Node management** | Fully managed | Self-managed or Fargate | Managed node pools |
| **Simplest option** | GKE Autopilot | EKS + Fargate | AKS with auto-mode |
| **GPU support** | Yes (T4, A100, H100) | Yes (extensive) | Yes (N-series) |
| **Networking** | VPC-native (default) | VPC CNI | Azure CNI / kubenet |
| **Ingress** | GKE Gateway | AWS ALB Controller | AGIC |
| **Best for** | Lowest operational burden | AWS-native teams | Azure-native teams |

### GKE Autopilot

Recommended for teams new to K8s. Google manages nodes, scaling, and security. You only define workloads.

```bash
gcloud container clusters create-auto my-cluster \
  --region us-central1 \
  --release-channel regular
```

### EKS with Fargate

Serverless Pods on AWS -- no node management.

```bash
eksctl create cluster --name my-cluster --region us-east-1 --fargate
```

## Gotchas

- **YAML sprawl**: A single service requires Deployment + Service + Ingress + ConfigMap + Secret + HPA = 6 files minimum. Use Helm charts or Kustomize to manage this.
- **Resource requests matter**: Without CPU/memory requests, the scheduler cannot make intelligent placement decisions. Always set requests; set limits for memory (to prevent OOM) but consider omitting CPU limits (throttling causes latency spikes).
- **Namespace isolation is not security isolation**: Namespaces are organizational, not security boundaries. Use Network Policies for actual traffic isolation.
- **etcd size limits**: ConfigMaps and Secrets have a 1MB size limit. Large configs need mounted volumes.
- **Ingress controller is required**: K8s does not include an ingress controller by default. Install nginx-ingress, Traefik, or use cloud-native options (GKE Gateway, AWS ALB).
- **Persistent volumes are zone-bound**: A PV in `us-central1-a` cannot be used by a Pod in `us-central1-b`. Plan storage topology with scheduling constraints.
