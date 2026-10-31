#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ANSIBLE_DIR="${ROOT_DIR}/ansible"
TERRAFORM_DIR="${ROOT_DIR}/terraform"

ENVIRONMENT="${ENVIRONMENT:-local}"
ANSIBLE_INVENTORY="inventories/${ENVIRONMENT}/hosts.yml"

log()  { echo "[$(date +%H:%M:%S)] $*"; }
ok()   { echo "[$(date +%H:%M:%S)] ✓ $*"; }
fail() { echo "[$(date +%H:%M:%S)] ✗ $*" >&2; exit 1; }

log "=== FocusFlow Deploy | env=${ENVIRONMENT} ==="

command -v docker    >/dev/null 2>&1 || fail "docker is required"
command -v terraform >/dev/null 2>&1 || fail "terraform is required"
command -v ansible-playbook >/dev/null 2>&1 || fail "ansible-playbook is required"

if [ "${ENVIRONMENT}" = "local" ]; then
    if ! docker ps --format '{{.Names}}' | grep -q "focusflow-localstack"; then
        log "Starting LocalStack..."
        docker compose -f "${ROOT_DIR}/localstack/docker-compose.yml" up -d
        log "Waiting for LocalStack..."
        for i in $(seq 1 30); do
            if curl -sf http://localhost:4566/_localstack/health | grep -q '"s3": "running"'; then
                ok "LocalStack ready"
                break
            fi
            [ "$i" -eq 30 ] && fail "LocalStack did not become ready"
            sleep 2
        done
    else
        ok "LocalStack already running"
    fi
fi

log "Running Terraform (${ENVIRONMENT})..."
cd "${TERRAFORM_DIR}"
terraform init -input=false
terraform validate
terraform apply -auto-approve -input=false
ok "Terraform apply complete"

log "Running Ansible deployment (${ENVIRONMENT})..."
cd "${ANSIBLE_DIR}"
export ANSIBLE_CONFIG="${ANSIBLE_DIR}/ansible.cfg"
ansible-playbook -i "${ANSIBLE_INVENTORY}" playbooks/deploy.yml
ok "Ansible deployment complete"

log "Verifying application health..."
HEALTH_URL="http://localhost:8080/health/"
for i in $(seq 1 15); do
    STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || true)
    if [ "${STATUS}" = "200" ]; then
        ok "Health check passed (HTTP 200)"
        break
    fi
    [ "$i" -eq 15 ] && fail "Health check failed after 30s — got HTTP ${STATUS}"
    sleep 2
done

log "=== Deployment Summary ==="
log "  Environment : ${ENVIRONMENT}"
log "  Web UI      : http://localhost:8080"
log "  Health      : ${HEALTH_URL}"
log "  LocalStack  : http://localhost:4566"
log "========================================"
ok "FocusFlow deployed successfully"
