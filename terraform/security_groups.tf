# terraform/security_groups.tf

# Security Group for the RDS Database
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg-${var.environment}"
  description = "Allow PostgreSQL traffic from App Runner"
  vpc_id      = aws_vpc.main.id # Reference the VPC created in vpc.tf

  # Ingress Rule: Allow PostgreSQL from App Runner (placeholder for now)
  # We'll add a specific rule once the App Runner SG is defined

  # Egress Rule: Allow all outbound (typical for RDS)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # All protocols
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-rds-sg-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Security Group for App Runner (Placeholder - App Runner often manages its own default)
# We might define specific egress rules here later if needed
resource "aws_security_group" "app_runner" {
  name        = "${var.project_name}-apprunner-sg-${var.environment}"
  description = "Security group for App Runner service"
  vpc_id      = aws_vpc.main.id

  # Ingress rules might be managed by App Runner itself or Load Balancer
  # Egress rule to allow outbound traffic (e.g., to NAT Gateway for internet)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Or restrict further if needed
  }

  tags = {
    Name        = "${var.project_name}-apprunner-sg-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Add rule to allow App Runner SG access to RDS SG on PostgreSQL port
resource "aws_security_group_rule" "allow_apprunner_to_rds" {
  type                     = "ingress"
  from_port                = 5432 # PostgreSQL port
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app_runner.id # App Runner SG ID
  security_group_id        = aws_security_group.rds.id        # RDS SG ID
  description              = "Allow App Runner to connect to RDS"
}

# --- Outputs ---
output "rds_security_group_id" {
  value = aws_security_group.rds.id
}

output "app_runner_security_group_id" {
  value = aws_security_group.app_runner.id
}
