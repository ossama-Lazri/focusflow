# Terraform Infrastructure

## Architecture

FocusFlow infrastructure is provisioned via Terraform using a modular structure targeting AWS (production) or LocalStack (local). All resources are tagged with `Environment`, `Project`, and `ManagedBy` via provider-level `default_tags`.

```
terraform/
├── provider.tf           # AWS provider + endpoint configuration
├── variables.tf          # Input variables (environment, region, project_name)
├── main.tf               # Root module — composes all child modules
├── outputs.tf            # Exposes bucket names, ARNs, IAM identifiers
├── terraform.tfvars      # Active variable values (not committed)
├── terraform.tfvars.example
└── modules/
    ├── s3/               # Generic S3 bucket module
    └── iam/              # IAM roles, policies, deployer user
```

## Module Structure

### `modules/s3`

Provisions a single S3 bucket with:

| Resource | Purpose |
|---|---|
| `aws_s3_bucket` | Bucket with configurable `force_destroy` |
| `aws_s3_bucket_versioning` | Enabled/Suspended via `enable_versioning` input |
| `aws_s3_bucket_server_side_encryption_configuration` | AES256 SSE enforced on all buckets |
| `aws_s3_bucket_public_access_block` | Public access fully blocked by default |

Instantiated four times from root:

| Instance | Bucket Name | Versioning |
|---|---|---|
| `s3_media` | `focusflow-{env}-media` | Enabled |
| `s3_static` | `focusflow-{env}-static` | Disabled |
| `s3_backups` | `focusflow-{env}-backups` | Enabled |
| `s3_artifacts` | `focusflow-artifacts` | Enabled |

### `modules/iam`

Provisions the full IAM surface:

| Resource | Name | Purpose |
|---|---|---|
| `aws_iam_role` | `FocusFlowAppRole` | EC2 instance role for application runtime |
| `aws_iam_policy` | `FocusFlowAppRolePolicy` | Scoped S3 + CloudWatch Logs access |
| `aws_iam_role_policy_attachment` | — | Binds policy to role |
| `aws_iam_instance_profile` | `FocusFlowAppRoleInstanceProfile` | EC2 instance profile wrapper |
| `aws_iam_user` | `focusflow-deployer` | CI/CD deploy identity |
| `aws_iam_access_key` | — | Programmatic credentials for deployer |
| `aws_iam_policy` | `focusflow-deployerPolicy` | Least-privilege deploy policy |

Both the app role and deployer user are granted identical scoped permissions: `s3:{Get,Put,Delete,List}` on all FocusFlow buckets and `logs:{CreateLogStream,PutLogEvents,DescribeLogStreams}` on the application log group.

## Deployment Workflow

```bash
cd terraform/

# First-time initialization
terraform init

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply
terraform apply -auto-approve
```

For local development, the provider is pre-configured to route all API calls to LocalStack (`http://localhost:4566`). No credential configuration is required locally.

For production, remove the `endpoints` override and supply real AWS credentials via environment variables or an instance profile.

## Operational Workflow

### Inspect outputs
```bash
terraform output
terraform output -json
terraform output deployment_secret_access_key  # sensitive
```

### Targeted operations
```bash
terraform plan -target=module.s3_media
terraform apply -target=module.iam_app
```

### State management
```bash
terraform state list
terraform state show module.iam_app.aws_iam_role.app
```

### Destroy
```bash
terraform destroy -auto-approve   # local only
# Production: remove -auto-approve, review plan output first
```

> **Note:** `force_destroy = true` is set on all buckets for development convenience. In production, this must be set to `false` and bucket deletion should require explicit state removal after content archival.
