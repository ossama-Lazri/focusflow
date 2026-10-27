# FocusFlow Terraform Infrastructure Guide

## Overview

FocusFlow manages all cloud infrastructure as code (IaC) using modular Terraform. The configuration supports zero-cost local execution via LocalStack (AWS simulation) and direct production deployment on AWS.

## Architecture & Modules

```
terraform/
├── main.tf                     # Root module invoking S3 and IAM modules
├── variables.tf                # Input variable definitions
├── outputs.tf                  # Infrastructure outputs (buckets, ARNs, IAM keys)
├── provider.tf                 # AWS provider with optional LocalStack endpoint overrides
├── terraform.tfvars.example    # Example configuration values
├── modules/
│   ├── s3/                     # Reusable S3 bucket module
│   │   ├── main.tf             # Bucket, encryption, versioning, public access block
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/                    # Least-privilege IAM roles and deployment user
│       ├── main.tf             # App role, deployer user, access keys, policy attachments
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── local/                  # LocalStack-targeted environment
    └── production/             # AWS-targeted environment
```

## Provisioned Resources

### 1. S3 Storage Buckets
- `focusflow-artifacts`: CI/CD build artifacts and deployment archives.
- `focusflow-local-media`: User-uploaded assets.
- `focusflow-local-static`: Compiled Django/Nginx static assets.
- `focusflow-local-backups`: Automated SQLite database backups.

Every bucket enforces:
- AES256 server-side encryption.
- S3 bucket versioning.
- Public Access Block (`block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`).

### 2. Identity and Access Management (IAM)
- **Application Role (`FocusFlowAppRole`)**: EC2/Container assume-role with scoped S3 and CloudWatch Logs permissions.
- **Application Instance Profile (`FocusFlowAppRoleInstanceProfile`)**: For EC2 instance attachment.
- **Deployment User (`focusflow-deployer`)**: Programmatic CI/CD deployment user with least-privilege permissions to S3 and CloudWatch.
- **Access Keys**: Programmatic AWS access key pair generated for deployment automation.

## LocalStack vs AWS Execution

### LocalStack Mode (Default)
LocalStack executes on `http://localhost:4566`. `use_localstack = true` redirects all AWS API calls to the local container.

```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

### AWS Production Mode
Set `use_localstack = false` in `terraform.tfvars` or pass `-var="use_localstack=false"` to target real AWS resources with AWS credentials configured via environment variables or IAM role.

## Outputs Reference

| Output Key | Description |
|---|---|
| `artifacts_bucket_name` | Name of the CI/CD artifacts S3 bucket |
| `artifacts_bucket_arn` | ARN of the CI/CD artifacts S3 bucket |
| `media_bucket_name` | Name of the media storage S3 bucket |
| `static_bucket_name` | Name of the static assets S3 bucket |
| `backups_bucket_name` | Name of the backups S3 bucket |
| `app_role_arn` | IAM Role ARN for application runtime |
| `deployment_user_name` | IAM username for deployment pipeline |
| `deployment_access_key_id` | Access key ID for deployer user |
| `deployment_secret_access_key` | Secret access key (sensitive) |
