# FocusFlow Ansible Automation Guide

## Overview

FocusFlow utilizes Ansible for automated host configuration, Docker environment provisioning, and reproducible application deployment across local, staging, and production environments.

## Directory Layout

```
ansible/
├── ansible.cfg                    # Core Ansible runtime configuration
├── inventories/
│   ├── local/
│   │   ├── hosts.yml              # Localhost connection target
│   │   └── group_vars/
│   │       └── all.yml            # Local environment variables
│   └── production/
│       ├── hosts.yml              # Production server inventory
│       └── group_vars/
│           └── all.yml            # Production variables (templated / vaulted)
├── playbooks/
│   ├── site.yml                   # Master orchestration playbook
│   ├── provision.yml              # Host provisioning (OS, users, Docker)
│   └── deploy.yml                 # App deployment & health verification
└── roles/
    ├── common/                    # Baseline OS dependencies & app user
    ├── docker/                    # Docker CE engine & Compose installation
    └── app/                       # FocusFlow compose setup, env, and healthcheck
```

## Roles Specification

### 1. `common`
- Updates apt package cache.
- Installs prerequisite utilities (`curl`, `ca-certificates`, `gnupg`, `git`, `rsync`, `htop`).
- Creates system group `appuser` and non-root system user `appuser`.

### 2. `docker`
- Adds official Docker GPG key and APT repository.
- Installs `docker-ce`, `docker-ce-cli`, `containerd.io`, and `docker-compose-plugin`.
- Configures `/etc/docker/daemon.json` with log rotation (`max-size: 20m`, `max-file: 5`).
- Enables and starts systemd service `docker`.
- Adds `appuser` to the `docker` group.

### 3. `app`
- Creates application directories: `/opt/focusflow`, `/opt/focusflow/data`, `/opt/focusflow/logs`.
- Deploys environment file (`.env`) from template with database, secret key, and host configurations.
- Deploys production `docker-compose.yml`.
- Synchronizes Nginx configuration and application build context.
- Starts containers with `docker compose up -d --build`.
- Verifies endpoint health via HTTP probe to `http://127.0.0.1:{{ app_port }}/health/`.

## Running Playbooks

### Syntax Verification
```bash
cd ansible
export ANSIBLE_CONFIG=./ansible.cfg
ansible-playbook --syntax-check -i inventories/local/hosts.yml playbooks/site.yml
```

### Inspect Tasks
```bash
ansible-playbook -i inventories/local/hosts.yml playbooks/site.yml --list-tasks
```

### Dry Run (Check Mode)
```bash
ansible-playbook -i inventories/local/hosts.yml playbooks/site.yml --check
```

### Execute Deployment Only
```bash
ansible-playbook -i inventories/local/hosts.yml playbooks/deploy.yml
```

### Production Deployment
```bash
ansible-playbook -i inventories/production/hosts.yml playbooks/site.yml --ask-vault-pass
```
