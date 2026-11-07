# Kubernetes Architecture

## Overview

FocusFlow runs on Kubernetes as a resilient, horizontally scalable microservice architecture. Container orchestration provides declarative state management, zero-downtime rolling updates, automated self-healing, and dynamic ingress routing.

```
 Internet / Clients
         │
         ▼
 ┌───────────────────────────────────────┐
 │       Ingress Nginx Controller        │
 └──────────────────┬────────────────────┘
                    │ (TLS Termination / Path Routing)
                    ▼
 ┌───────────────────────────────────────┐
 │     focusflow-service (ClusterIP)     │
 └──────────────────┬────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
 ┌───────────────┐     ┌───────────────┐
 │ FocusFlow Pod │     │ FocusFlow Pod │ (ReplicaSet / Deployment)
 │  - Django App │     │  - Django App │
 │  - Probes     │     │  - Probes     │
 └───────┬───────┘     └───────┬───────┘
         │                     │
         ▼                     ▼
 ┌───────────────────────────────────────┐
 │ PersistentVolumeClaim / Shared Assets │
 └───────────────────────────────────────┘
```

## Request Lifecycle

1. **Ingress Entrypoint**: External HTTP/HTTPS requests hit the `Ingress-Nginx` controller.
2. **Routing & TLS**: Ingress terminates TLS (via cert-manager or provisioned certificates) and matches hostname (`focusflow.local` / `app.focusflow.io`).
3. **ClusterIP Service**: Traffic is balanced across active ready endpoints backing the `focusflow-service`.
4. **Pod Processing**: Django handles application logic, authenticates requests, and queries state.
5. **Static/Media Content**: Static assets and media uploads resolve either via reverse-proxy volume mounts or upstream S3 endpoints.

## Core Kubernetes Primitives

### Namespaces
- `focusflow`: Dedicated namespace isolating application workloads, configs, and secrets.
- `monitoring`: Dedicated namespace hosting Prometheus, Grafana, Loki, and Promtail.
- `ingress-nginx`: Standard ingress controller namespace.

### Workload Specifications
- **Deployment (`focusflow-web`)**:
  - Declarative replicas (`spec.replicas: 2+`).
  - RollingUpdate strategy (`maxSurge: 25%`, `maxUnavailable: 0`).
  - Resource requests and limits defined for predictable scheduling.
- **Probes**:
  - `livenessProbe`: `GET /health/` verifies container process health; failure triggers restart.
  - `readinessProbe`: `GET /health/` checks application readiness to receive traffic; failure removes pod from Service endpoints.
  - `startupProbe`: Guards slow cold-starts during migration executions.
- **Config & Secrets**:
  - `ConfigMap`: Non-sensitive settings (`DJANGO_SETTINGS_MODULE`, `ALLOWED_HOSTS`, `PORT`).
  - `Secret`: Sensitive credentials (`SECRET_KEY`, database credentials, S3 keys).

## Helm Packaging Architecture

The application is packaged as a modular Helm chart located at `helm/focusflow`:

```
helm/focusflow/
├── Chart.yaml             # Chart metadata, apiVersion: v2, version: 0.3.0
├── values.yaml            # Environment defaults
├── values-local.yaml      # Kind / LocalStack overrides
├── values-prod.yaml       # Production-grade configuration
└── templates/
    ├── deployment.yaml    # Workload deployment spec
    ├── service.yaml       # ClusterIP service definition
    ├── ingress.yaml       # Ingress routing rules
    ├── configmap.yaml     # Application configuration
    ├── secret.yaml        # Application secrets template
    ├── serviceaccount.yaml# Pod identity
    └── hpa.yaml           # HorizontalPodAutoscaler spec
```

## Local Cluster Architecture (Kind)

Local development and verification use a multi-node or single-node **Kind (Kubernetes in Docker)** cluster:
- Port mappings forward host `80/443` to the Kind ingress controller.
- Image loaded directly into Kind node cache (`kind load docker-image focusflow-web:latest`).
- Direct integration with LocalStack running alongside the cluster on Docker network bridge.
