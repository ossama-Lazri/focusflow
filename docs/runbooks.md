# Site Reliability Engineering Runbooks

## Incident Triage Framework

| Incident Severity | Definition | Response Target | Escalation |
|---|---|---|---|
| **SEV-1** | Total service outage; 100% 5xx errors; active session tracking offline | < 15 minutes | Lead SRE + DevOps on-call |
| **SEV-2** | Partial degradation; elevated latency (> 1s P95); single replica flapping | < 1 hour | Platform Engineer |
| **SEV-3** | Non-critical alert; scrape target down; isolated non-customer bug | Next business day | Team backlog |

---

## Runbook: Pod CrashLoopBackOff & Crash Diagnostics

### Symptoms
- `kubectl get pods` reports `CrashLoopBackOff` or `Error`.
- Grafana alert `Active Pod Replicas` drops below configured threshold.

### Diagnostic Flow
1. **Identify failing pods**:
   ```bash
   kubectl get pods -n focusflow -o wide
   ```
2. **Inspect exit code and termination reason**:
   ```bash
   kubectl describe pod <pod-name> -n focusflow | grep -A 10 "Last State:"
   ```
   - `OOMKilled` (Exit Code 137): Container exceeded `resources.limits.memory`. Increase limits in Helm `values.yaml`.
   - Exit Code 1 / OperationalError: Application initialization failure. Inspect previous logs.
3. **Inspect crashed container logs**:
   ```bash
   kubectl logs <pod-name> -n focusflow --previous --tail=100
   ```
4. **Inspect events**:
   ```bash
   kubectl get events -n focusflow --sort-by='.metadata.creationTimestamp'
   ```

---

## Runbook: Health Probe Failure (Liveness / Readiness)

### Symptoms
- Pods are `Running` but report `0/1 READY`.
- Ingress returns `502 Bad Gateway` or `503 Service Unavailable`.

### Diagnostic Flow
1. **Check probe execution details**:
   ```bash
   kubectl describe pod <pod-name> -n focusflow | grep -E "Liveness|Readiness|Startup|Events"
   ```
2. **Execute direct container probe query**:
   ```bash
   kubectl exec -it <pod-name> -n focusflow -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health/').read())"
   ```
3. **Mitigation**:
   - If migrations or startup tasks block startup: verify `startupProbe.failureThreshold` allows sufficient headroom.
   - If SQLite/database connection locks: check disk volume mounts and permissions (`runAsUser: 1001`).

---

## Runbook: Zero-Downtime Deployment & Rollback

### Rolling Update Verification
```bash
# Rollout deployment update via Helm
helm upgrade focusflow ./helm/focusflow --set image.tag=v0.3.0

# Watch rollout progression
kubectl rollout status deployment/focusflow -n default --timeout=120s
```

### Emergency Rollback
If errors surge or health checks fail immediately post-release:
```bash
# 1. Rollback via Helm
helm rollback focusflow

# 2. Or direct Kubernetes deployment undo
kubectl rollout undo deployment/focusflow

# 3. Confirm target revision running
kubectl rollout status deployment/focusflow
```

---

## Runbook: Scaling & Capacity Adjustment

### Manual Scaling
```bash
# Scale deployment horizontally
kubectl scale deployment/focusflow --replicas=4

# Verify newly scheduled pods
kubectl get pods -l app.kubernetes.io/instance=focusflow -w
```

### Resource Limit Adjustment
Update `helm/focusflow/values.yaml`:
```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```
Apply:
```bash
helm upgrade focusflow ./helm/focusflow
```
