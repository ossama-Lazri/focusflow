# Monitoring Architecture & Operational Guide

## System Topology

FocusFlow telemetry follows a pull-based metrics model orchestrated via Prometheus in the `monitoring` namespace. Scrape targets are dynamically discovered through Kubernetes API annotations and node cAdvisor proxies, visualized via Grafana.

```
┌────────────────────────────────────────────────────────┐
│                   Grafana (Port 3000)                  │
│    - FocusFlow / Production Overview Dashboard         │
└───────────────────────────┬────────────────────────────┘
                            │ PromQL Queries
                            ▼
┌────────────────────────────────────────────────────────┐
│                 Prometheus (Port 9090)                 │
│    - TSDB Retention: 15 days                           │
│    - Scrape Interval: 15s                              │
└──────┬────────────────────┬────────────────────┬───────┘
       │                    │                    │
       ▼ (Node Proxy)       ▼ (Pod Discovery)    ▼ (Self)
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   cAdvisor   │     │  FocusFlow   │     │  Prometheus  │
│ (CPU/Memory) │     │   /metrics   │     │   Internal   │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Key Telemetry & Metrics (RED Method)

### Rate (Throughput)
- **Application Request Rate**:
  ```promql
  sum(rate(http_requests_total[1m])) or rate(focusflow_uptime_seconds[1m])
  ```
- **Active Focus Sessions**:
  ```promql
  max(focusflow_sessions_active)
  ```

### Errors (Failure Ratio)
- **Application Availability**:
  ```promql
  max(focusflow_up)  # 1 = Healthy, 0 = Down
  ```
- **Target Down Ratio**:
  ```promql
  count(up{job="kubernetes-pods"} == 0) / count(up{job="kubernetes-pods"})
  ```

### Duration (Latency)
- **Scrape & Response Latency (P95)**:
  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) or avg(scrape_duration_seconds{job="kubernetes-pods"})
  ```

### Saturation & Compute
- **Per-Pod CPU Utilization**:
  ```promql
  sum(rate(container_cpu_usage_seconds_total{container=~"focusflow|web"}[2m])) by (pod)
  ```
- **Per-Pod Memory Working Set**:
  ```promql
  sum(container_memory_working_set_bytes{container=~"focusflow|web"}) by (pod)
  ```

## Operational Dashboards

Grafana is provisioned with declarative dashboards via `monitoring/grafana/dashboard-provider.yaml`:
- **`FocusFlow / Production Overview` (`focusflow-overview`)**:
  - Top stat cards: Application Health (healthy/down), Active Replicas, Active Sessions, Total Sessions.
  - Middle graphs: Request Rate (req/s), P95 Response Latency.
  - Bottom graphs: Per-pod CPU saturation (percent cores) and Memory working set (MB/GB).

## Monitoring Verification & CLI Workflow

```bash
# Verify Prometheus scrape targets state
kubectl exec -n monitoring deploy/prometheus -- wget -qO- http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, endpoint: .scrapeUrl}'

# Port-forward interfaces
kubectl port-forward svc/prometheus -n monitoring 9090:9090
kubectl port-forward svc/grafana -n monitoring 3000:3000
```
