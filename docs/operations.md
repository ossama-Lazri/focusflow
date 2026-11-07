# Operations Guide

## Operational Overview

This runbook covers operational lifecycle procedures for FocusFlow on Kubernetes, including cluster bootstrapping, deployment execution, scaling, health triage, incident response, and rollback.

## Deployment Workflows

### 1. Local Cluster Bootstrapping (Kind)
```bash
# Provision Kind cluster with ingress host port mappings
kind create cluster --name focusflow --config kubernetes/kind-config.yaml

# Install Ingress Nginx Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### 2. Helm Deployment
```bash
# Package application container image
docker build -t focusflow-web:latest .
kind load docker-image focusflow-web:latest --name focusflow

# Install or upgrade FocusFlow release
helm upgrade --install focusflow helm/focusflow \
  --namespace focusflow \
  --create-namespace \
  -f helm/focusflow/values-local.yaml
```

### 3. Observability Stack Bootstrap
```bash
# Deploy Prometheus, Loki, Promtail, and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install monitoring stack
helm upgrade --install loki-stack grafana/loki-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true,promtail.enabled=true
```

## Scaling & Capacity Management

### Manual Scaling
```bash
# Scale application deployment directly
kubectl scale deployment/focusflow-web --replicas=4 -n focusflow
```

### Horizontal Pod Autoscaling (HPA)
HPA automatically adjusts replica count based on CPU and memory utilization thresholds:
```bash
kubectl get hpa -n focusflow
```

## Health Verification & Troubleshooting

### Probe & Pod Status
```bash
# Check pod lifecycle status
kubectl get pods -n focusflow -o wide

# Inspect pod lifecycle events, probes, and conditions
kubectl describe pod -l app.kubernetes.io/name=focusflow -n focusflow
```

### Application Logs
```bash
# Stream aggregate container logs
kubectl logs -l app.kubernetes.io/name=focusflow -n focusflow -f --tail=100

# Inspect previous crashed container logs
kubectl logs -l app.kubernetes.io/name=focusflow -n focusflow --previous
```

### Ingress & Network Triage
```bash
# Verify ingress endpoints and backend routing
kubectl get ingress -n focusflow
kubectl describe ingress focusflow-ingress -n focusflow

# Check active service endpoints
kubectl get endpoints focusflow-service -n focusflow
```

## Rollback & Disaster Recovery

### Rollout Inspection
```bash
# View deployment revision history
kubectl rollout history deployment/focusflow-web -n focusflow

# Rollback to immediate preceding revision
kubectl rollout undo deployment/focusflow-web -n focusflow

# Rollback via Helm
helm rollback focusflow -n focusflow
```

### Database & Storage Operations
- Persistent SQLite / PostgreSQL volumes managed via StatefulSet or persistent storage classes.
- Media and static backups synchronized to S3/LocalStack buckets via cron-triggered Kubernetes Jobs.
