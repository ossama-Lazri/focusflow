# Ansible Deployment

## Architecture

Ansible manages the application deployment layer — environment configuration, Docker Compose orchestration, and service health verification. Infrastructure provisioning (IAM, S3) is handled by Terraform; Ansible operates exclusively on the application tier.

```
ansible/
├── ansible.cfg                          # stdout_callback=default, remote_tmp=/tmp/.ansible/tmp
├── inventories/
│   ├── local/
│   │   ├── hosts.yml                    # connection: local, python: auto_silent
│   │   └── group_vars/all.yml           # app_source_method: copy, deploy_become: false
│   └── production/
│       ├── hosts.yml                    # SSH connection to web1.focusflow.io
│       └── group_vars/all.yml           # app_source_method: git, deploy_become: true
├── playbooks/
│   ├── site.yml                         # Full stack: provision + deploy
│   ├── provision.yml                    # OS-level: common + docker roles
│   └── deploy.yml                       # Application: app role only
└── roles/
    ├── common/                          # Base packages, system user
    ├── docker/                          # Docker CE install, daemon config, systemd
    └── app/                             # Application deployment pipeline
```

## Role Structure

### `roles/app`

The `app` role is the core deployment unit. It executes a sequential pipeline:

| Task | Module | Condition |
|---|---|---|
| Create directory hierarchy | `file` | Always |
| Deploy `.env` from template | `template` | Always |
| Deploy `docker-compose.yml` from template | `template` | Always |
| Sync Nginx configuration | `copy` | Always |
| Install git + rsync | `package` | `deploy_become: true` |
| Pull repository via git | `git` | `app_source_method: git` |
| Sync source from local filesystem | `copy` | `app_source_method: copy` |
| Start Docker Compose services | `command` | `not ansible_check_mode` |
| Wait for health endpoint | `uri` | `not ansible_check_mode` |

**Handler:** `Restart FocusFlow` — runs `docker compose up -d --force-recreate` on any notifying task change, skipped in `--check` mode.

### Source Strategy (`app_source_method`)

| Value | Mechanism | Use Case |
|---|---|---|
| `copy` | `ansible.builtin.copy` from `playbook_dir/../..` | Local development — no git required |
| `git` | `ansible.builtin.git` with `depth: 1, force: true` | Production — pull from GitHub |

### Key Variables (`roles/app/defaults/main.yml`)

| Variable | Default | Description |
|---|---|---|
| `app_repo_url` | GitHub URL | Repository to clone in git mode |
| `app_version` | `main` | Branch or tag to deploy |
| `app_source_method` | `git` | Source acquisition strategy |
| `app_dir` | `/opt/focusflow` | Application root on target host |
| `app_port` | `8080` | Port health check polls |
| `healthcheck_retries` | `10` | Max retries for health endpoint |
| `healthcheck_delay` | `3` | Seconds between retries |
| `deploy_become` | (per-inventory) | Whether to use privilege escalation |

## Deployment Workflow

```bash
cd ansible/
export ANSIBLE_CONFIG=./ansible.cfg

# Dry-run
ansible-playbook -i inventories/local/hosts.yml playbooks/deploy.yml --check

# Deploy
ansible-playbook -i inventories/local/hosts.yml playbooks/deploy.yml

# Production
ansible-playbook -i inventories/production/hosts.yml playbooks/deploy.yml
```

All playbooks are idempotent. Re-running against an already-deployed environment produces `changed=0`.

## Operational Workflow

### List hosts
```bash
ansible-inventory -i inventories/local/hosts.yml --list
```

### Ad-hoc commands
```bash
# Check container status on target
ansible localhost -i inventories/local/hosts.yml -m command -a "docker compose ps" --connection=local

# Restart application
ansible localhost -i inventories/local/hosts.yml -m command \
  -a "docker compose -f /tmp/focusflow/docker-compose.yml up -d --force-recreate" --connection=local
```

### Run only specific tasks by tag
```bash
ansible-playbook -i inventories/local/hosts.yml playbooks/deploy.yml --tags "config"
```

### Verbose output
```bash
ansible-playbook -i inventories/local/hosts.yml playbooks/deploy.yml -vvv
```
