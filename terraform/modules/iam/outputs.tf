output "role_arn" {
  description = "The ARN of the IAM role"
  value       = aws_iam_role.app.arn
}

output "role_name" {
  description = "The name of the IAM role"
  value       = aws_iam_role.app.name
}

output "policy_arn" {
  description = "The ARN of the scoped policy"
  value       = aws_iam_policy.app.arn
}

output "instance_profile_name" {
  description = "The name of the IAM instance profile"
  value       = aws_iam_instance_profile.app.name
}

output "instance_profile_arn" {
  description = "The ARN of the IAM instance profile"
  value       = aws_iam_instance_profile.app.arn
}

output "deployment_user_name" {
  description = "Name of the deployment IAM user"
  value       = aws_iam_user.deployer.name
}

output "deployment_access_key_id" {
  description = "Access key ID for the deployment user"
  value       = aws_iam_access_key.deployer.id
}

output "deployment_secret_access_key" {
  description = "Secret access key for the deployment user"
  value       = aws_iam_access_key.deployer.secret
  sensitive   = true
}
