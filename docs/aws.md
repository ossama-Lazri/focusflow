# AWS Architecture

## Overview

FocusFlow uses a minimal AWS surface scoped to storage and identity. All services are emulated locally via LocalStack during development and target real AWS in production with zero configuration changes — only the provider endpoint differs.

## Services Used

| Service | Usage |
|---|---|
| S3 | Media uploads, static assets, database backups, CI/CD artifacts |
| IAM | Application runtime role, CI/CD deployer identity |
| CloudWatch Logs | Application stdout log streams |

## S3 Bucket Layout

| Bucket | Purpose | Versioning | Public Access |
|---|---|---|---|
| `focusflow-{env}-media` | User-uploaded media files | Enabled | Blocked |
| `focusflow-{env}-static` | Collected Django static assets | Disabled | Blocked |
| `focusflow-{env}-backups` | Database and configuration backups | Enabled | Blocked |
| `focusflow-artifacts` | CI/CD build artifacts, release bundles | Enabled | Blocked |

All buckets enforce AES256 server-side encryption. The `{env}` suffix isolates resources across environments (`local`, `staging`, `production`).

## IAM Design

```
EC2 Instance
  └── FocusFlowAppRoleInstanceProfile
        └── FocusFlowAppRole
              └── FocusFlowAppRolePolicy
                    ├── s3:{Get,Put,Delete,List} → all focusflow buckets
                    └── logs:{CreateLogStream,PutLogEvents,DescribeLogStreams}

CI/CD Pipeline
  └── focusflow-deployer (IAM User)
        └── focusflow-deployerPolicy
              ├── s3:{Get,Put,Delete,List} → all focusflow buckets
              └── logs:{CreateLogStream,PutLogEvents,DescribeLogStreams}
```

**`FocusFlowAppRole`** — assumed by EC2 instances at runtime via instance profile. No long-lived credentials on the host.

**`focusflow-deployer`** — programmatic IAM user for CI/CD pipelines. Access key ID and secret are output by Terraform and should be stored as encrypted CI/CD secrets (e.g., GitHub Actions secrets). Rotate on a defined schedule.

Both identities are granted least-privilege: access is restricted to FocusFlow-owned bucket ARNs only — no wildcard resource grants.

## Local Development (LocalStack)

The Terraform provider routes all API calls to `http://localhost:4566`. Static credentials (`test`/`test`) are used — no real AWS account is required.

```bash
# Start LocalStack
docker compose -f localstack/docker-compose.yml up -d

# Verify
curl http://localhost:4566/_localstack/health | jq '.services | {s3, iam}'
```

The `init-localstack.sh` script (`scripts/init-localstack.sh`) is a fallback initializer for manual resource creation outside of Terraform.

## Production Considerations

- Replace LocalStack endpoint overrides in `provider.tf` with standard AWS endpoint resolution
- Store deployer credentials in a secrets manager (AWS Secrets Manager or GitHub Actions encrypted secrets)
- Enable S3 access logging for audit trail
- Set `force_destroy = false` on all production buckets
- Apply S3 lifecycle rules for backup retention and cost control
- Enable CloudTrail for IAM and S3 API audit logging
- Use remote Terraform state backend (S3 + DynamoDB lock table)
