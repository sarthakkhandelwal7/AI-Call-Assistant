# terraform/rds.tf

# Need random password generation if not providing one
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?" # Define allowed special characters
}

# Store the generated password securely in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}-rds-credentials-${var.environment}"
  description = "Credentials for the RDS database"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id     = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "dbadmin" # Or your preferred master username
    password = random_password.db_password.result
  })
}

# Subnet Group for RDS (needs at least two AZs for high availability)
resource "aws_db_subnet_group" "default" {
  name       = "${var.project_name}-rds-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private[*].id # Use the private subnets from vpc.tf

  tags = {
    Name        = "${var.project_name}-rds-subnet-group-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# RDS PostgreSQL Instance (Free Tier Settings)
resource "aws_db_instance" "default" {
  identifier             = "${var.project_name}-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "15" # Choose a recent supported version
  instance_class         = "db.t3.micro" # Free tier eligible instance class
  allocated_storage      = 20            # Free tier eligible storage (GB)
  storage_type           = "gp2"         # CHANGE TO GP2 for Free Tier eligibility

  # Ensure db_name is alphanumeric
  db_name                = "${replace(var.project_name, "-", "_")}${var.environment}"
  # Fetch username/password from Secrets Manager
  username               = jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string).username
  password               = jsondecode(aws_secretsmanager_secret_version.db_credentials.secret_string).password

  db_subnet_group_name   = aws_db_subnet_group.default.name
  vpc_security_group_ids = [aws_security_group.rds.id] # Use the RDS SG from security_groups.tf

  # Availability / Backup
  multi_az               = false # Keep as false for lower cost/simplicity unless HA needed
  skip_final_snapshot    = true  # Set to false for production if you want a final backup
  backup_retention_period = 0    # Set higher (e.g., 7 days) for production backups

  # Networking
  publicly_accessible = false # Set to false now that we use Bastion/Tunnel for access

  # Other Settings
  storage_encrypted   = true
  deletion_protection = false # Set to true for production safety

  tags = {
    Name        = "${var.project_name}-rds-instance-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }

  # Ensure subnet group is created first
  depends_on = [aws_db_subnet_group.default]
}

# --- Outputs ---
output "rds_instance_endpoint" {
  value = aws_db_instance.default.endpoint
}
output "rds_instance_port" {
  value = aws_db_instance.default.port
}
output "rds_db_name" {
  value = aws_db_instance.default.db_name
}
output "rds_credentials_secret_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}
