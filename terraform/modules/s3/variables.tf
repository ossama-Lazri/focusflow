variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning for objects in the bucket"
  type        = bool
  default     = true
}

variable "block_public_access" {
  description = "Enable S3 public access block"
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow bucket deletion even if non-empty"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
