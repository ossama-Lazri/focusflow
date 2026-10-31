variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "local"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "focusflow"
}
