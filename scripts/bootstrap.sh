#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

log()  { echo "[$(date +%H:%M:%S)] $*"; }
ok()   { echo "[$(date +%H:%M:%S)] ✓ $*"; }
fail() { echo "[$(date +%H:%M:%S)] ✗ $*" >&2; exit 1; }

log "=== FocusFlow Bootstrap ==="

command -v docker    >/dev/null 2>&1 || fail "docker is required"
command -v terraform >/dev/null 2>&1 || fail "terraform is required"
command -v ansible   >/dev/null 2>&1 || fail "ansible is required"
command -v python3   >/dev/null 2>&1 || fail "python3 is required"
ok "Prerequisites satisfied"

if [ ! -f "${ROOT_DIR}/.env" ]; then
    cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
    log ".env created from .env.example — review and update secrets before deploying"
fi

if docker ps --format '{{.Names}}' | grep -q "focusflow-localstack"; then
    ok "LocalStack already running"
else
    log "Starting LocalStack..."
    docker compose -f "${ROOT_DIR}/localstack/docker-compose.yml" up -d
    log "Waiting for LocalStack to be ready..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:4566/_localstack/health | grep -q '"s3": "running"'; then
            ok "LocalStack is ready"
            break
        fi
        [ "$i" -eq 30 ] && fail "LocalStack did not become ready in time"
        sleep 2
    done
fi

log "Initializing Terraform..."
cd "${ROOT_DIR}/terraform"
terraform init -input=false -upgrade
ok "Terraform initialized"

log "Bootstrap complete — run scripts/deploy.sh to deploy"
