#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo " FocusFlow End-to-End Deployment Pipeline"
echo "=========================================="

# 1. Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "[ERROR] Docker is required but not installed."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "[ERROR] Terraform is required but not installed."; exit 1; }

# 2. Check LocalStack status
if docker ps | grep -q "focusflow-localstack"; then
  echo "[OK] LocalStack container is running."
else
  echo "[INFO] Starting LocalStack..."
  docker compose -f "${ROOT_DIR}/localstack/docker-compose.yml" up -d
  sleep 5
fi

# 3. Apply Terraform Infrastructure
echo "[INFO] Validating and applying Terraform infrastructure..."
cd "${ROOT_DIR}/terraform"
terraform init -upgrade
terraform apply -auto-approve

# 4. Verify deployment targets
echo "[INFO] Verifying FocusFlow containers..."
cd "${ROOT_DIR}"
docker compose ps

echo "=========================================="
echo " FocusFlow Deployment Completed Successfully"
echo " Web UI: http://localhost:8080"
echo " Health: http://localhost:8080/health/"
echo " LocalStack: http://localhost:4566"
echo "=========================================="
