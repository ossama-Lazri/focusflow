variable "role_name" {
  description = "Name of the IAM role"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs the role has access to"
  type        = list(string)
}

variable "log_group_arn" {
  description = "CloudWatch log group ARN"
  type        = string
  default     = "*"
}

variable "deployer_user_name" {
  description = "Name of the CI/CD deployment IAM user"
  type        = string
  default     = "focusflow-deployer"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
