#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${ROOT_DIR}/terraform"

ENVIRONMENT="${ENVIRONMENT:-local}"

log()  { echo "[$(date +%H:%M:%S)] $*"; }
ok()   { echo "[$(date +%H:%M:%S)] ✓ $*"; }
warn() { echo "[$(date +%H:%M:%S)] ! $*"; }
fail() { echo "[$(date +%H:%M:%S)] ✗ $*" >&2; exit 1; }

log "=== FocusFlow Destroy | env=${ENVIRONMENT} ==="

if [ "${ENVIRONMENT}" = "production" ]; then
    warn "You are about to destroy the PRODUCTION environment."
    read -r -p "Type 'destroy-production' to confirm: " CONFIRM
    [ "${CONFIRM}" = "destroy-production" ] || fail "Aborted"
fi

log "Stopping application containers..."
if docker compose -f "${ROOT_DIR}/docker-compose.yml" ps --quiet 2>/dev/null | grep -q .; then
    docker compose -f "${ROOT_DIR}/docker-compose.yml" down --remove-orphans
    ok "Application containers stopped"
else
    warn "No application containers running"
fi

log "Destroying Terraform infrastructure (${ENVIRONMENT})..."
cd "${TERRAFORM_DIR}"
terraform init -input=false
terraform destroy -auto-approve -input=false
ok "Terraform infrastructure destroyed"

if [ "${ENVIRONMENT}" = "local" ]; then
    log "Stopping LocalStack..."
    if docker compose -f "${ROOT_DIR}/localstack/docker-compose.yml" ps --quiet 2>/dev/null | grep -q .; then
        docker compose -f "${ROOT_DIR}/localstack/docker-compose.yml" down --remove-orphans
        ok "LocalStack stopped"
    else
        warn "LocalStack was not running"
    fi
fi

log "Cleaning up temporary deployment artifacts..."
rm -rf /tmp/focusflow 2>/dev/null && ok "Cleaned /tmp/focusflow" || true

log "=== Destroy Summary ==="
log "  Environment : ${ENVIRONMENT}"
log "  Infrastructure destroyed"
log "  Containers stopped"
log "========================================"
ok "FocusFlow environment destroyed"
