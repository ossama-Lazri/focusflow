#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

if command -v awslocal >/dev/null 2>&1; then
    AWS="awslocal"
else
    AWS="aws --endpoint-url=http://localhost:4566 --region=${AWS_REGION}"
fi

# S3
for bucket in focusflow-local-media focusflow-local-static focusflow-local-backups; do
    if ! $AWS s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
        $AWS s3api create-bucket --bucket "$bucket" --region "$AWS_REGION"
    fi
done

# ECR (LocalStack Pro feature; gracefully skip on Community edition)
if $AWS ecr describe-repositories --repository-names focusflow-web >/dev/null 2>&1; then
    :
elif $AWS ecr create-repository --repository-name focusflow-web --image-tag-mutability MUTABLE >/dev/null 2>&1; then
    :
else
    echo "[INFO] ECR emulation requires LocalStack Pro. Skipping local ECR repository creation."
fi

# IAM
ASSUME_ROLE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}'

APP_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::focusflow-local-*",
        "arn:aws:s3:::focusflow-local-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/focusflow/local/*"
    }
  ]
}'

if ! $AWS iam get-role --role-name FocusFlowAppRole >/dev/null 2>&1; then
    $AWS iam create-role \
        --role-name FocusFlowAppRole \
        --assume-role-policy-document "$ASSUME_ROLE_POLICY"
fi

$AWS iam put-role-policy \
    --role-name FocusFlowAppRole \
    --policy-name FocusFlowAppPolicy \
    --policy-document "$APP_POLICY"

# CloudWatch Logs
if ! $AWS logs describe-log-groups --log-group-name-prefix /focusflow/local/web | grep -q "/focusflow/local/web"; then
    $AWS logs create-log-group --log-group-name /focusflow/local/web
fi

$AWS logs create-log-stream \
    --log-group-name /focusflow/local/web \
    --log-stream-name app-stdout >/dev/null 2>&1 || true
