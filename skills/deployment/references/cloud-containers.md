# Cloud Container Services

Managed container deployment on Cloud Run (GCP), ECS/Fargate (AWS), and Azure Container Apps. Back to [SKILL.md](../SKILL.md).

## When Cloud Containers Over PaaS

| Signal | PaaS Sufficient | Cloud Containers Needed |
|--------|----------------|------------------------|
| Services | 1-3 | 4+ or complex networking |
| Scaling | Moderate, predictable | Burst traffic, scale-to-zero |
| Compliance | Standard | VPC isolation, audit logs, HIPAA/SOC2 |
| Budget | Under $200/month | Enterprise cloud spend |
| Team | No cloud expertise | Cloud-native team |
| Networking | Public endpoints only | Private services, VPC peering |

## Google Cloud Run

### Why Start Here

Cloud Run is the simplest cloud container service. Deploy a Docker container and get a managed HTTPS endpoint with automatic scaling, including scale-to-zero. No cluster management, no node pools, no load balancer configuration.

### Deployment

```bash
# Build and push to Artifact Registry
gcloud artifacts repositories create my-repo \
  --repository-format=docker --location=us-central1

docker build -t us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:latest .
docker push us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:latest

# Deploy
gcloud run deploy my-app \
  --image us-central1-docker.pkg.dev/PROJECT/my-repo/my-app:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

### Configuration (`service.yaml`)

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: us-central1-docker.pkg.dev/PROJECT/my-repo/my-app
          ports:
            - containerPort: 8000
          resources:
            limits:
              cpu: "1"
              memory: 512Mi
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-url
                  key: latest
          startupProbe:
            httpGet:
              path: /health
            initialDelaySeconds: 5
            periodSeconds: 5
```

### Key Features

| Feature | Configuration |
|---------|--------------|
| **Scale-to-zero** | `min-instances 0` (default) |
| **Always-on** | `min-instances 1+` |
| **CPU allocation** | `cpu-throttling: false` for always-allocated CPU |
| **Secrets** | Secret Manager integration via `--set-secrets` |
| **VPC access** | `--vpc-connector` for private networking |
| **Custom domains** | `gcloud run domain-mappings create` |
| **Jobs** | `gcloud run jobs create` for batch/cron workloads |

### Cloud SQL Integration

```bash
gcloud run deploy my-app \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE \
  --set-env-vars "DATABASE_URL=postgresql+asyncpg://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE"
```

### Gotchas

- **Cold start latency**: Scale-to-zero instances take 2-10 seconds to start. Use `min-instances 1` for latency-sensitive services.
- **Request timeout**: Default 5 minutes, max 60 minutes. Not suitable for very long-running tasks (use Cloud Run Jobs instead).
- **No persistent disk**: Filesystem is ephemeral. Use Cloud Storage or Cloud SQL for persistence.
- **Concurrency model**: Each instance handles multiple concurrent requests (default 80). CPU-bound workloads may need lower concurrency.

## AWS ECS/Fargate

### Architecture

```
ECS Cluster
  └── Service (desired count, load balancer config)
       └── Task Definition (container specs, resources)
            └── Container (image, ports, env vars)
```

**Fargate** = serverless compute for ECS (no EC2 instances to manage). **EC2 launch type** = bring your own instances (more control, potentially cheaper at scale).

### Task Definition

```json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "portMappings": [
        { "containerPort": 8000, "protocol": "tcp" }
      ],
      "environment": [
        { "name": "ENV", "value": "production" }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:db-url"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "app"
        }
      }
    }
  ]
}
```

### Service Configuration

```bash
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-app \
  --task-definition my-app:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-abc],securityGroups=[sg-xyz],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=app,containerPort=8000"
```

### Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-app \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 --max-capacity 10

# Target tracking policy (scale on CPU)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-app \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    "TargetValue=70,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}"
```

### Gotchas

- **Complexity**: ECS requires ALB, target groups, security groups, VPC, subnets, IAM roles. Plan 2-4 hours for initial setup.
- **No scale-to-zero on Fargate**: Minimum 1 task. Use Lambda for scale-to-zero workloads.
- **ECR costs**: Container image storage in ECR has transfer costs. Clean up old images.
- **Networking**: `awsvpc` mode assigns an ENI per task. There is a per-subnet ENI limit (~250 for most instance types).

## Azure Container Apps

### Overview

Azure Container Apps is Microsoft's managed container platform built on Kubernetes (but fully abstracted). Closest to Cloud Run in simplicity.

### Deployment

```bash
# Create environment
az containerapp env create \
  --name my-env --resource-group my-rg --location eastus

# Deploy container
az containerapp create \
  --name my-app \
  --resource-group my-rg \
  --environment my-env \
  --image myregistry.azurecr.io/my-app:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10 \
  --cpu 0.5 --memory 1.0Gi
```

### Key Features

| Feature | Notes |
|---------|-------|
| **Scale-to-zero** | Supported (like Cloud Run) |
| **Dapr integration** | Built-in service-to-service communication, pub/sub, state management |
| **Revisions** | Traffic splitting across container versions for canary deployments |
| **Jobs** | Event-driven and scheduled container jobs |
| **Custom domains** | Via `az containerapp hostname` |

### Gotchas

- **Dapr overhead**: Dapr sidecar adds latency and resource usage. Disable if not using Dapr features.
- **Limited GPU support**: GPU workloads are preview/limited. Use Azure ML or AKS for GPU needs.
- **Logs**: Application logs go to Azure Monitor / Log Analytics. Query language (KQL) has a learning curve.

## Cross-Platform Comparison

| Aspect | Cloud Run | ECS/Fargate | Container Apps |
|--------|-----------|-------------|---------------|
| **Simplicity** | Highest | Lowest | High |
| **Scale-to-zero** | Yes | No (Fargate) | Yes |
| **Networking** | VPC connectors | Full VPC | VNET integration |
| **GPU** | No | Yes (EC2 type) | Preview |
| **Cost model** | Per-request + CPU/memory | Per-task-hour | Per-request + CPU/memory |
| **IAM/Identity** | Google IAM | AWS IAM (complex) | Azure RBAC |
| **Best for** | Simple services, GCP shops | AWS shops, complex networking | Azure shops, Dapr users |
