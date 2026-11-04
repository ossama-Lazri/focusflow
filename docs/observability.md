# Observability Architecture

## Overview

FocusFlow observability implements the three pillars of telemetry—metrics, logs, and traces/health state—providing unified operational insight across cluster and application layers.

```
                  ┌──────────────────────────────┐
                  │       Grafana Unified UI     │
                  └──────┬────────────────┬──────┘
                         │                │
            Query Metrics│                │Query Logs
                         ▼                ▼
                ┌────────────┐      ┌────────────┐
                │ Prometheus │      │    Loki    │
                └──────▲─────┘      └─────▲──────┘
                       │Scrape            │Push
                       │                  │
         ┌─────────────┴────────┐         │
         │                      │         │
  ┌──────────────┐      ┌──────────────┐  │
  │ kube-state-  │      │ FocusFlow Pod│  │
  │   metrics    │      │ (stdout/err) │──┘
  └──────────────┘      └──────┬───────┘
                               │ Stream
                               ▼
                        ┌──────────────┐
                        │   Promtail   │ (DaemonSet)
                        └──────────────┘
```

## Metrics Architecture

### Scrape Targets
1. **Application Runtime**: Pod scrape annotations (`prometheus.io/scrape: "true"`, `prometheus.io/port: "8000"`, `prometheus.io/path: "/metrics"`).
2. **Cluster & Workload State**: `kube-state-metrics` exports deployment, replica, node, and pod health status.
3. **Ingress Controller**: Ingress Nginx exposes request rate, response latency, and HTTP status code metrics.

### Key Performance Indicators (RED Method)
- **Rate**: Requests processed per second (`sum(rate(http_requests_total[5m]))`).
- **Errors**: Percentage of 5xx HTTP responses (`rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`).
- **Duration**: P95 and P99 application response latency percentiles (`histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`).

## Logging Architecture

### Ingestion Flow
1. **Container Output**: FocusFlow outputs structured JSON logs to standard output (`stdout`/`stderr`).
2. **Collection (Promtail)**: Runs as a cluster-wide `DaemonSet`, mounting node container log directories (`/var/log/pods`).
3. **Enrichment**: Promtail labels log lines with Kubernetes metadata (`namespace`, `pod`, `container`, `app`).
4. **Storage (Loki)**: Ingests compressed log chunks, indexing only labels for cost efficiency and high throughput.
5. **Visualization**: Grafana queries Loki using LogQL for log correlation with metric anomalies.

## Monitoring & Alerting Strategy

### Alerting Rules
- **PodRestartLoop**: Fires if pod restart rate exceeds threshold (`rate(kube_pod_container_status_restarts_total[15m]) > 0`).
- **ServiceUnavailable**: Fires if readiness probes fail or ready endpoints drop to zero.
- **HighErrorRate**: Fires if 5xx HTTP rate exceeds 1% of total traffic over a 5-minute window.
- **LatencySpike**: Fires if P95 latency exceeds 500ms for over 5 minutes.

### Grafana Dashboards
- **Cluster & Node Overview**: CPU, memory, filesystem saturation.
- **FocusFlow Operations**: Active focus sessions, HTTP throughput, response status codes, P95/P99 latency.
- **Unified Log Explorer**: LogQL queries correlated with deployment rollout timestamps.
