# Centralized Logging Architecture & Guide

## Architecture Overview

FocusFlow utilizes an agent-aggregator log architecture leveraging **Grafana Loki** as the log store and **Promtail** as the node-level collection daemon. Logs are shipped without full-text indexing, dramatically reducing ingestion overhead while retaining rich label query capabilities.

```
 FocusFlow Pod (stdout/stderr)
            │
            ▼
 Container Runtime Log Engine (/var/log/pods/*.log)
            │
            ▼
 Promtail DaemonSet (HostMount /var/log/pods)
   - CRI Parser
   - JSON Field Extraction (level, time, logger)
   - Kubernetes Label Enrichment (namespace, pod, container, app)
            │
            ▼ (HTTP Push: /loki/api/v1/push)
 Loki Single-Binary (TSDB v13 Schema)
            │
            ▼ (LogQL)
 Grafana Logs Dashboard & Explore UI
```

## Log Pipeline & Parser Specification

Promtail ingests container streams and executes pipeline processing:
1. **CRI Pipeline**: Strips CRI container engine metadata and reassembles multiline log segments.
2. **JSON Parser**: Extracts structured Django payload attributes (`time`, `level`, `logger`, `message`).
3. **Relabeling**:
   - `app`: Extracts standard `app.kubernetes.io/name` or controller prefixes.
   - `pod`: Populated from `__meta_kubernetes_pod_name`.
   - `namespace`: Populated from `__meta_kubernetes_namespace`.
   - `container`: Populated from `__meta_kubernetes_pod_container_name`.

## LogQL Investigation Runbook

### Application Logs
```logql
# Stream all FocusFlow application logs
{app=~"focusflow.*"}

# Filter by HTTP endpoint
{app=~"focusflow.*"} |= "GET /dashboard/"

# Real-time Gunicorn request rate
sum(rate({app=~"focusflow.*"} [1m])) by (pod)
```

### Error Triage
```logql
# Case-insensitive error and exception search
{app=~"focusflow.*"} |=~ "(?i)error|exception|fail|traceback"

# 5xx HTTP response status detection
{app=~"focusflow.*"} |=~ "HTTP/1.[01]\" 5[0-9]{2}"
```

### Infrastructure & Cluster Logs
```logql
# Ingress and control plane audit stream
{namespace=~"ingress-nginx|kube-system"}

# Monitor Loki ingestion health
{namespace="monitoring", container="loki"}
```

## CLI Log Inspection

```bash
# Direct pod tailing across all deployment replicas
kubectl logs -n focusflow -l app.kubernetes.io/name=focusflow -f --tail=100

# Inspect previous container instance before restart
kubectl logs -n focusflow -l app.kubernetes.io/name=focusflow --previous --tail=100

# Check Promtail collector status
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=50
```
