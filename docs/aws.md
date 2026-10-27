# AWS Cloud Architecture & Evolution

## 1. Cloud Architecture Overview

FocusFlow's cloud architecture is modeled after high-availability 12-factor cloud-native applications. During local development, AWS services are fully simulated via LocalStack. When deploying to production, identical interfaces map to native AWS managed services without application code modifications.

```
                                  INTERNET
                                      │
                                      ▼
                            ┌───────────────────┐
                            │  AWS CloudFront   │
                            │      + WAF        │
                            └─────────┬─────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                 │
                     ▼                                 ▼
         ┌───────────────────────┐         ┌───────────────────────┐
         │  S3 Static/Media      │         │ Application Load      │
         │  (Direct Cached)      │         │ Balancer (ALB)        │
         └───────────────────────┘         └───────────┬───────────┘
                                                       │
                                      ┌────────────────┴────────────────┐
                                      ▼ (Private Subnets)
                         ┌─────────────────────────────┐
                         │   Compute Plane             │
                         │   - Dev: LocalStack / Docker│
                         │   - Phase 1: EC2 + ASG      │
                         │   - Phase 2: EKS (Kubernetes│
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
            ┌──────────────────────┐      ┌─────────────────────────┐
            │  RDS PostgreSQL      │      │  ElastiCache Redis      │
            │  (Multi-AZ)          │      │  (Sessions / Throttling)│
            └──────────────────────┘      └─────────────────────────┘
```

---

## 2. Service Matrix: LocalStack vs. AWS Production

| Capability | LocalStack (Development) | AWS Production Target | Architecture Role |
|---|---|---|---|
| **Object Storage** | `s3` (port 4566) | Amazon S3 | Media files, static asset backups, database snapshots |
| **Secrets & Config** | `ssm` (port 4566) | AWS Systems Manager Parameter Store | Dynamic `.env` injection, database credentials, API keys |
| **IAM & Auth** | `iam` / `sts` (mocked) | AWS IAM / IRSA | Fine-grained access control, role assumption |
| **Networking** | Docker bridge network | AWS VPC (Public/Private Subnets, NAT) | Network isolation, security boundaries |
| **Compute** | Docker Compose / Local Host | EC2 ASG ➔ Amazon EKS | Workload scheduling, scaling, container runtime |
| **Database** | Volume-mounted SQLite | Amazon RDS for PostgreSQL | Relational transactional persistence |
| **Caching** | In-memory / SQLite | Amazon ElastiCache (Redis) | High-throughput distributed rate-limiting & session cache |

---

## 3. Storage Architecture (Amazon S3)

### 3.1 Bucket Layout

FocusFlow provisions three isolated buckets via the Terraform `s3` module:

```
s3://
├── focusflow-<env>-media/       # User uploaded content & media assets
│   └── uploads/
├── focusflow-<env>-static/      # Collected static assets for CDN distribution
│   └── staticfiles/
└── focusflow-<env>-backups/     # Periodic database dumps and system artifacts
    └── db-dumps/
```

### 3.2 Security & Lifecycle Enforcement

* **Encryption**: Server-Side Encryption with AWS-managed keys (`AES256`) enforced by default on all buckets.
* **Public Access Block**: `BlockPublicAcls`, `BlockPublicPolicy`, `IgnorePublicAcls`, and `RestrictPublicBuckets` set to `true` on all buckets. Static and media delivery routes through CloudFront Origin Access Control (OAC).
* **Lifecycle Rules**:
  * `focusflow-<env>-backups`: Transition to `STANDARD_IA` after 30 days, expire objects after 90 days.
  * Non-current version expiration: 14 days on versioned buckets.

---

## 4. Identity & Access Management (IAM)

FocusFlow strictly observes the Principle of Least Privilege (PoLP). No root or administrator keys are permitted within workloads.

### 4.1 Policy Separation

1. **`FocusFlowAppS3Policy`**:
   - `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` restricted to `arn:aws:s3:::focusflow-<env>-media/*`.
   - `s3:ListBucket` restricted to `arn:aws:s3:::focusflow-<env>-media`.

2. **`FocusFlowAppSSMPolicy`**:
   - `ssm:GetParameter`, `ssm:GetParameters`, `ssm:GetParametersByPath` scoped specifically to `/focusflow/<env>/*`.
   - `kms:Decrypt` access granted to the SSM default KMS key.

### 4.2 Role Assumption Strategy

* **Local Development**: The application relies on the dummy AWS credentials (`test`/`test`) against the LocalStack mock STS service.
* **Cloud EC2**: Attached via an `aws_iam_instance_profile`. Gunicorn workers access metadata via IMDSv2 (`http://169.254.169.254/latest/meta-data/`).
* **Cloud Kubernetes (EKS)**: Transitions to **IAM Roles for Service Accounts (IRSA)**. A Kubernetes `ServiceAccount` is annotated with the IAM Role ARN via OpenID Connect (OIDC), eliminating credential storage inside the container completely.

---

## 5. Configuration & Secrets Management (AWS SSM)

Application configuration is stored in AWS Systems Manager Parameter Store following a hierarchical naming taxonomy:

```
/focusflow/<environment>/<component>/<parameter_name>
```

### Parameter Schema

| Parameter Key | Type | Description |
|---|---|---|
| `/focusflow/prod/django/SECRET_KEY` | `SecureString` | Production cryptographic signing key |
| `/focusflow/prod/django/ALLOWED_HOSTS` | `StringList` | Comma-delimited list of valid Host headers |
| `/focusflow/prod/django/DATABASE_URL` | `SecureString` | PostgreSQL connection string |
| `/focusflow/prod/django/SECURE_HSTS_SECONDS` | `String` | HSTS header duration (31536000) |
| `/focusflow/prod/django/LOG_LEVEL` | `String` | Logging verbosity threshold |

Ansible and Terraform populate these keys; deployment scripts pull parameters during container instantiation.

---

## 6. Networking Architecture (VPC Design)

For production migration, the network topology is defined as:

* **VPC CIDR**: `10.0.0.0/16`
* **Subnets across 2 Availability Zones**:
  * **Public Subnets** (`10.0.1.0/24`, `10.0.2.0/24`): Internet Gateway (IGW), Application Load Balancers, Bastion/NAT Gateways.
  * **Application Private Subnets** (`10.0.10.0/24`, `10.0.20.0/24`): Compute instances / Kubernetes Worker Nodes. No direct internet ingress. Egress through NAT Gateway.
  * **Data Private Subnets** (`10.0.100.0/24`, `10.0.200.0/24`): RDS PostgreSQL and ElastiCache. Zero internet ingress/egress. Ingress only permitted from Application Subnets on port `5432` and `6379`.

---

## 7. Migration Roadmap to Kubernetes (EKS)

The steps to evolve FocusFlow from single-node container automation to distributed Kubernetes:

```
Phase 1: LocalStack & Compose  ──► Phase 2: EC2 & Ansible  ──► Phase 3: Amazon EKS
(Local Workstation / CI)           (Single Node Cloud VM)      (Production Cluster)
- LocalStack S3/SSM                - Remote S3/SSM             - EKS Control Plane
- Docker Compose                   - Systemd + Docker Engine   - Pods, Deployments
- SQLite file storage              - RDS PostgreSQL (Managed)  - Helm / Kustomize
- Ansible local connection         - Ansible SSH deployment    - ArgoCD / GitOps
```

1. **Database Decoupling**: Transition `config.settings.production` from `sqlite3` engine to `django.db.backends.postgresql` using the `DATABASE_URL` parameter stored in SSM.
2. **Static Asset Externalization**: Configure `django-storages` with `boto3` to offload `collectstatic` artifacts directly into S3, bypassing local disk storage.
3. **Manifest Creation**: Convert `docker-compose.yml` service semantics (ports, environment, volume mounts, healthchecks) into Kubernetes standard manifests (`Deployment`, `Service`, `Ingress`, `ConfigMap`, `SecretProviderClass`).
