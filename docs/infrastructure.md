# Infrastructure Architecture & Automation

## 1. High-Level Architecture Overview

FocusFlow utilizes a modular Infrastructure as Code (IaC) and Configuration Management pattern designed for complete local execution via LocalStack, with zero friction migration to real AWS infrastructure and Kubernetes (EKS).

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Local Developer Node                          │
│                                                                        │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│   │  Terraform   │────►│  LocalStack  │     │   Ansible Engine     │   │
│   │  (IaC Core)  │     │  (AWS Mock)  │     │ (Host / Config Mgmt) │   │
│   └──────┬───────┘     └──────┬───────┘     └──────────┬───────────┘   │
│          │                    │                        │               │
│          ▼                    ▼                        ▼               │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│   │ State Files  │     │  S3 / IAM /  │     │ Docker Engine Host   │   │
│   │ (Local/S3)   │     │  SSM / VPC   │     │ (App, Nginx, DB)     │   │
│   └──────────────┘     └──────────────┘     └──────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                         Target Evolution (Cloud)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         AWS Production (Target)                        │
│   VPC Multi-AZ ──► EKS Cluster / RDS Aurora ──► S3 / CloudFront / WAF  │
└────────────────────────────────────────────────────────────────────────┘
```

The design enforces environment parity: Terraform code written against LocalStack endpoints is identical to production AWS definitions, separated strictly by provider endpoint injection and environment variables.

---

## 2. Directory & Component Topology

```
focusflow/
├── terraform/
│   ├── environments/
│   │   ├── local/              # LocalStack target environment
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── provider.tf     # Configures endpoint overrides for LocalStack
│   │   └── prod/               # AWS production target environment
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       ├── outputs.tf
│   │       └── backend.tf      # S3 backend + DynamoDB state locking
│   ├── modules/
│   │   ├── s3/                 # Buckets: media, static, backups
│   │   ├── iam/                # Scoped service policies and roles
│   │   ├── ssm/                # Parameter Store secret orchestration
│   │   └── networking/         # VPC, Subnets, Routing, Security Groups
│   ├── versions.tf             # Core Terraform & provider version pins
│   └── outputs.tf
│
├── ansible/
│   ├── ansible.cfg             # Control node configuration & pipelining
│   ├── inventories/
│   │   ├── local/
│   │   │   └── hosts.yml       # Local Docker daemon & localhost targets
│   │   └── production/
│   │       └── hosts.yml       # Dynamic EC2/Bastion target inventory
│   ├── playbooks/
│   │   ├── site.yml            # Master orchestration entrypoint
│   │   ├── provision.yml       # Host dependency baseline
│   │   └── deploy.yml          # Container release & health verification
│   └── roles/
│       ├── common/             # OS hardening, baseline packages, users
│       ├── docker/             # Docker engine, compose plugin, daemon config
│       ├── localstack/         # LocalStack container verification & init
│       └── app/                # FocusFlow compose lifecycle, env, migrations
│
├── localstack/
│   └── docker-compose.yml      # LocalStack service definition
│
├── scripts/
│   ├── init-localstack.sh      # LocalStack readiness hook & mock seeding
│   ├── terraform.sh            # Environment-switching IaC wrapper
│   └── deploy.sh               # Single-command provisioning & deploy pipeline
│
└── docs/
    ├── infrastructure.md       # Core infrastructure topology & lifecycle
    └── aws.md                  # AWS service mapping & cloud evolution
```

---

## 3. Terraform Module Architecture

### 3.1 Module Decoupling Strategy

All infrastructure resources are isolated into reusable modules under `terraform/modules/`. No module directly references provider configurations or environment-specific naming conventions.

| Module | Core Resources | Input Contract | Outputs |
|---|---|---|---|
| `networking` | `aws_vpc`, `aws_subnet`, `aws_security_group` | CIDR blocks, AZ list, environment tag | `vpc_id`, `subnet_ids`, `sg_ids` |
| `s3` | `aws_s3_bucket`, `aws_s3_bucket_versioning`, `aws_s3_bucket_server_side_encryption_configuration` | Bucket prefix, ACLs, lifecycle rules | `bucket_arn`, `bucket_id`, `domain_name` |
| `iam` | `aws_iam_role`, `aws_iam_policy`, `aws_iam_instance_profile` | Service principals, S3 ARNs, SSM ARNs | `role_arn`, `instance_profile_name` |
| `ssm` | `aws_ssm_parameter` | Key-value pairs, parameter tiers | `parameter_arns` |

### 3.2 Provider Abstraction Pattern

The provider definition controls routing between LocalStack and real AWS.

```hcl
# terraform/environments/local/provider.tf
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3     = "http://localhost:4566"
    iam    = "http://localhost:4566"
    ssm    = "http://localhost:4566"
    ec2    = "http://localhost:4566"
    sts    = "http://localhost:4566"
  }
}
```

In `terraform/environments/prod/provider.tf`, endpoint blocks are omitted, allowing the official AWS SDK to resolve real credentials via IAM role authentication or standard environment credentials.

---

## 4. Ansible Configuration Management

Ansible operates as the configuration and deployment layer. It targets the runtime environment regardless of whether it is running on a local host via Docker socket or remote virtual instances.

### 4.1 Role Breakdown

* **`common`**: Manages system packages, non-root system users (`appuser`), file permissions, and directory structures (`/opt/focusflow/data`, `/opt/focusflow/static`).
* **`docker`**: Installs Docker CE, sets storage driver (`overlay2`), configures log rotation (`json-file`, max 10MB x 3), and starts systemd service.
* **`localstack`**: Validates LocalStack container health via `http://localhost:4566/_localstack/health` before running downstream automation.
* **`app`**: Renders production `.env` from SSM/encrypted variables, syncs `docker-compose.yml`, executes `docker compose pull`, triggers migrations, runs `collectstatic`, and verifies `/health/`.

---

## 5. LocalStack Structure & Runtime Topology

LocalStack runs as a standalone infrastructure support container alongside the main FocusFlow compose stack:

* **Endpoint**: Single edge proxy on port `4566`.
* **Services Emulated**: `s3`, `iam`, `ssm`, `sts`.
* **Persistence**: LocalStack state persists to `.localstack/` directory volume mount.
* **Init Hooks**: Shell scripts mounted to `/etc/localstack/init/ready.d/` automatically provision base buckets and mock parameters on container boot before Terraform execution.

---

## 6. End-to-End Deployment Workflow

The deployment follows a strictly decoupled 3-stage lifecycle:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 1. Infrastructure│     │ 2. Configuration │     │ 3. Application   │
│    (Terraform)   ├────►│     (Ansible)    ├────►│    (Compose)     │
│                  │     │                  │     │                  │
│  - Provision S3  │     │  - Provision OS  │     │  - Up Containers │
│  - Provision IAM │     │  - Pull Secrets  │     │  - DB Migration  │
│  - Populate SSM  │     │  - Config Engine │     │  - Health Probe  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

1. **Infrastructure Phase**:
   - `terraform -chdir=terraform/environments/local init`
   - `terraform -chdir=terraform/environments/local apply -auto-approve`
   - Outputs infrastructure IDs (S3 Bucket names, SSM paths).

2. **Configuration Phase**:
   - `ansible-playbook -i ansible/inventories/local/hosts.yml ansible/playbooks/site.yml`
   - Configures runtime dependencies, system limits, and deployment directories.

3. **Application Lifecycle Phase**:
   - Environment variables derived from step 1 and 2 are injected.
   - Blue/Green or in-place container recreation executes.
   - Database migrations run inside container context.
   - Zero-downtime healthcheck verification against `/health/`.

---

## 7. Developer Workflow

### 7.1 Daily Local Iteration

```bash

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# 1. Start LocalStack
docker compose -f localstack/docker-compose.yml up -d

# 2. Provision Local Infrastructure
./scripts/terraform.sh local apply

# 3. Run Configuration & App Orchestration
./scripts/deploy.sh local

# 4. Verify Local Emulation
aws --endpoint-url=http://localhost:4566 s3 ls
```

### 7.2 Validation & Drift Detection

* **IaC Syntax & Formatting**: `terraform fmt -check -recursive` and `tflint`.
* **Ansible Linting**: `ansible-lint ansible/`.
* **State Drift**: `terraform plan -detailed-exitcode` detects discrepancies between Terraform state and LocalStack.

---

## 8. Target Evolution: AWS & Kubernetes (EKS)

The architecture contains zero architectural dead-ends. The progression to Kubernetes is predefined:

1. **State Migration**: Local state (`terraform.tfstate`) is swapped for an S3 remote backend with DynamoDB locking by switching to `environments/prod`.
2. **Compute Transition**:
   - Stage 1: Single-node Docker deployment managed via Ansible (current design).
   - Stage 2: AWS ASG (Auto Scaling Group) running EC2 nodes managed via Ansible.
   - Stage 3: AWS EKS cluster provisioned via a new Terraform module (`modules/eks`), where Docker containers transition to Kubernetes Pods, Deployments, and Ingresses.
3. **Storage & Database Transition**:
   - S3 module remains completely unchanged (identical API contract).
   - SQLite volume transitions to AWS RDS PostgreSQL via the `modules/rds` Terraform module.
