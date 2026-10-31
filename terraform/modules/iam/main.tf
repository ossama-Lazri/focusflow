data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = merge(
    var.tags,
    {
      Name        = var.role_name
      Environment = var.environment
    }
  )
}

data "aws_iam_policy_document" "app" {
  statement {
    sid    = "S3Access"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = concat(
      var.s3_bucket_arns,
      [for arn in var.s3_bucket_arns : "${arn}/*"]
    )
  }

  statement {
    sid    = "CloudWatchLogsAccess"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = [var.log_group_arn]
  }
}

resource "aws_iam_policy" "app" {
  name        = "${var.role_name}Policy"
  description = "Scoped policy for FocusFlow application services"
  policy      = data.aws_iam_policy_document.app.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "app" {
  role       = aws_iam_role.app.name
  policy_arn = aws_iam_policy.app.arn
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.role_name}InstanceProfile"
  role = aws_iam_role.app.name
}

resource "aws_iam_user" "deployer" {
  name = var.deployer_user_name

  tags = merge(
    var.tags,
    {
      Name        = var.deployer_user_name
      Environment = var.environment
      Role        = "CI/CD Deployer"
    }
  )
}

resource "aws_iam_access_key" "deployer" {
  user = aws_iam_user.deployer.name
}

data "aws_iam_policy_document" "deployer" {
  statement {
    sid    = "S3DeploymentArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = concat(
      var.s3_bucket_arns,
      [for arn in var.s3_bucket_arns : "${arn}/*"]
    )
  }

  statement {
    sid    = "CloudWatchDeployLogging"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = [var.log_group_arn]
  }
}

resource "aws_iam_policy" "deployer" {
  name        = "${var.deployer_user_name}Policy"
  description = "Least-privilege deployment policy for FocusFlow CI/CD"
  policy      = data.aws_iam_policy_document.deployer.json

  tags = var.tags
}

resource "aws_iam_user_policy_attachment" "deployer" {
  user       = aws_iam_user.deployer.name
  policy_arn = aws_iam_policy.deployer.arn
}
