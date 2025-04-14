# terraform/apprunner.tf

# --- IAM FOR APPRUNNER --- 

# 1. Access Role (For App Runner Service to access ECR during deployment)
resource "aws_iam_role" "apprunner_access_role" {
  name = "${var.project_name}-apprunner-access-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{ 
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { 
        Service = "build.apprunner.amazonaws.com" # Principal for App Runner build/deployment service
      }
    }]
  })
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Attach ECR policy to the Access Role
resource "aws_iam_role_policy_attachment" "apprunner_access_ecr" {
  role       = aws_iam_role.apprunner_access_role.name
  policy_arn = aws_iam_policy.apprunner_ecr_policy.arn # Reuse the ECR policy
}

# 2. Instance Role (For the running container/task to access Secrets Manager)
resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.project_name}-apprunner-instance-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "tasks.apprunner.amazonaws.com" # Principal for App Runner instance tasks
      }
    }]
  })
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Policy to allow reading ECR images (Used by BOTH Roles now)
resource "aws_iam_policy" "apprunner_ecr_policy" {
  name        = "${var.project_name}-apprunner-ecr-policy-${var.environment}"
  description = "Allow App Runner to pull images from ECR"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:GetAuthorizationToken"
        ],
        Resource = "*" # Restrict further if needed, e.g., to specific repo ARNs
      }
    ]
  })
}

# Policy to allow reading secrets from Secrets Manager (Used by Instance Role)
resource "aws_iam_policy" "apprunner_secrets_policy" {
  name        = "${var.project_name}-apprunner-secrets-policy-${var.environment}"
  description = "Allow App Runner to read specific secrets"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
          ],
        # Grant access ONLY to the specific secrets needed
        Resource = [
          aws_secretsmanager_secret.db_credentials.arn,
          aws_secretsmanager_secret.app_secrets.arn
        ]
      }
    ]
  })
}

# Attach policies to the Instance Role
resource "aws_iam_role_policy_attachment" "apprunner_instance_ecr" { # Attach ECR policy also to instance role if needed (e.g., for debugging/logging?) - can be debated
  role       = aws_iam_role.apprunner_instance_role.name
  policy_arn = aws_iam_policy.apprunner_ecr_policy.arn
}

resource "aws_iam_role_policy_attachment" "apprunner_instance_secrets" { 
  role       = aws_iam_role.apprunner_instance_role.name
  policy_arn = aws_iam_policy.apprunner_secrets_policy.arn
}

# --- APPRUNNER SERVICE --- 

# Define the App Runner Service
resource "aws_apprunner_service" "backend" {
  service_name = "${var.project_name}-backend-${var.environment}"

  source_configuration {
    authentication_configuration {
      # Provide the ARN of the Access Role created above
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }
    image_repository {
      image_identifier       = "${aws_ecr_repository.backend.repository_url}:v1.0.0" # Use the specific image tag
      image_repository_type = "ECR"
      image_configuration {
        port = "8000" # Port the backend container listens on

        # === SECTION 1: runtime_environment_secrets ===
        # These correctly fetch LIVE values from specific keys in Secrets Manager
        runtime_environment_secrets = {
          TWILIO_AUTH_TOKEN     = "${aws_secretsmanager_secret.app_secrets.arn}:TWILIO_AUTH_TOKEN::", 
          OPENAI_API_KEY        = "${aws_secretsmanager_secret.app_secrets.arn}:OPENAI_API_KEY::",
          JWT_SECRET_KEY        = "${aws_secretsmanager_secret.app_secrets.arn}:JWT_SECRET_KEY::",
          GOOGLE_CLIENT_SECRET  = "${aws_secretsmanager_secret.app_secrets.arn}:GOOGLE_CLIENT_SECRET::",
          GOOGLE_CLIENT_ID      = "${aws_secretsmanager_secret.app_secrets.arn}:GOOGLE_CLIENT_ID::",
          TWILIO_ACCOUNT_SID    = "${aws_secretsmanager_secret.app_secrets.arn}:TWILIO_ACCOUNT_SID::",
          TWILIO_VERIFY_SERVICE_SID = "${aws_secretsmanager_secret.app_secrets.arn}:TWILIO_VERIFY_SERVICE_SID::"
        }

        # === SECTION 2: runtime_environment_variables ===
        # These variables get values determined DURING terraform apply
        runtime_environment_variables = {
          APP_ENV = var.environment
          LOG_LEVEL = "info"
          FRONTEND_URL = "https://${aws_cloudfront_distribution.frontend_distribution.domain_name}"
          DATABASE_URL = "postgresql+asyncpg://${jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string).username}:${jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string).password}@${aws_db_instance.default.endpoint}/${aws_db_instance.default.db_name}",
          # Removed: GOOGLE_CLIENT_ID, TWILIO_ACCOUNT_SID, TWILIO_VERIFY_SERVICE_SID
        }
      }
    }
    auto_deployments_enabled = false # Disable auto-deploy on image push for now
  }

  network_configuration {
    egress_configuration {
      egress_type = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.default.arn
    }
    # App Runner doesn't directly configure inbound, it's public by default
    # or uses a VPC endpoint if ingress_type = "VPC" (more complex)
  }

  instance_configuration {
    cpu    = "1024" # 1 vCPU
    memory = "2048" # 2 GB (Free tier eligible values)
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn # Assign the INSTANCE role here
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }

  # Allow time for role/policy attachments
  depends_on = [
     # Depend on attachments for *both* roles
     aws_iam_role_policy_attachment.apprunner_access_ecr, # Attachment to Access Role
     aws_iam_role_policy_attachment.apprunner_instance_ecr, # Attachment to Instance Role
     aws_iam_role_policy_attachment.apprunner_instance_secrets # Attachment to Instance Role
  ]
}

# VPC Connector required for App Runner to access resources in a VPC (like RDS)
resource "aws_apprunner_vpc_connector" "default" {
  vpc_connector_name = "${var.project_name}-vpc-connector-${var.environment}"
  subnets            = aws_subnet.private[*].id # Use private subnets
  security_groups    = [aws_security_group.app_runner.id] # Use App Runner SG

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}


# --- Outputs ---
output "apprunner_backend_service_url" {
  description = "URL of the deployed App Runner backend service"
  value       = aws_apprunner_service.backend.service_url
}
output "apprunner_backend_service_arn" {
   description = "ARN of the deployed App Runner backend service"
   value       = aws_apprunner_service.backend.arn
}
