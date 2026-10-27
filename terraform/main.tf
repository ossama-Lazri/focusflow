module "s3_media" {
  source = "./modules/s3"

  bucket_name       = "${var.project_name}-${var.environment}-media"
  environment       = var.environment
  enable_versioning = true
  force_destroy     = true
}

module "s3_static" {
  source = "./modules/s3"

  bucket_name       = "${var.project_name}-${var.environment}-static"
  environment       = var.environment
  enable_versioning = false
  force_destroy     = true
}

module "s3_backups" {
  source = "./modules/s3"

  bucket_name       = "${var.project_name}-${var.environment}-backups"
  environment       = var.environment
  enable_versioning = true
  force_destroy     = true
}

module "iam_app" {
  source = "./modules/iam"

  role_name   = "FocusFlowAppRole"
  environment = var.environment
  s3_bucket_arns = [
    module.s3_media.bucket_arn,
    module.s3_static.bucket_arn,
    module.s3_backups.bucket_arn
  ]
}
