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
