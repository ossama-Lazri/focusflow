output "s3_artifacts_bucket_name" {
  description = "FocusFlow artifacts S3 bucket name"
  value       = module.s3_artifacts.bucket_name
}

output "s3_artifacts_bucket_arn" {
  description = "FocusFlow artifacts S3 bucket ARN"
  value       = module.s3_artifacts.bucket_arn
}

output "s3_media_bucket_name" {
  description = "FocusFlow media S3 bucket name"
  value       = module.s3_media.bucket_id
}

output "s3_media_bucket_arn" {
  description = "FocusFlow media S3 bucket ARN"
  value       = module.s3_media.bucket_arn
}

output "s3_static_bucket_name" {
  description = "FocusFlow static S3 bucket name"
  value       = module.s3_static.bucket_id
}

output "s3_static_bucket_arn" {
  description = "FocusFlow static S3 bucket ARN"
  value       = module.s3_static.bucket_arn
}

output "s3_backups_bucket_name" {
  description = "FocusFlow backups S3 bucket name"
  value       = module.s3_backups.bucket_id
}

output "s3_backups_bucket_arn" {
  description = "FocusFlow backups S3 bucket ARN"
  value       = module.s3_backups.bucket_arn
}

output "iam_role_arn" {
  description = "FocusFlow application IAM role ARN"
  value       = module.iam_app.role_arn
}

output "iam_instance_profile_name" {
  description = "FocusFlow IAM instance profile name"
  value       = module.iam_app.instance_profile_name
}

output "deployment_user_name" {
  description = "FocusFlow deployment IAM user name"
  value       = module.iam_app.deployment_user_name
}

output "deployment_access_key_id" {
  description = "FocusFlow deployment IAM access key ID"
  value       = module.iam_app.deployment_access_key_id
}

output "deployment_secret_access_key" {
  description = "FocusFlow deployment IAM secret access key"
  value       = module.iam_app.deployment_secret_access_key
  sensitive   = true
}
