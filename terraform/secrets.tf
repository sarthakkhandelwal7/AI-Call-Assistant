# Define the container for application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-app-secrets-${var.environment}"
  description = "Application secrets (API Keys, JWT Secret, etc.)"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Generate a random string for the JWT Secret Key
resource "random_password" "jwt_secret" {
  length           = 64 # Use a strong length
  special          = false # Avoid special chars if JWT library has issues
  override_special = ""
}

# Create the initial version of the secret with the JSON content
resource "aws_secretsmanager_secret_version" "app_secrets_initial" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id

  # Store multiple secrets as key-value pairs in a single Secret Manager entry
  secret_string = jsonencode({
    TWILIO_ACCOUNT_SID      = "YOUR_PROD_TWILIO_SID_PLACEHOLDER"         # Replace with actual SID if non-sensitive, or keep placeholder
    TWILIO_AUTH_TOKEN       = "YOUR_PROD_TWILIO_TOKEN_PLACEHOLDER"       # Keep placeholder
    TWILIO_VERIFY_SERVICE_SID = "YOUR_PROD_TWILIO_VERIFY_SID_PLACEHOLDER" # Replace with actual SID if non-sensitive, or keep placeholder
    OPENAI_API_KEY          = "YOUR_PROD_OPENAI_KEY_PLACEHOLDER"         # Keep placeholder
    JWT_SECRET_KEY          = random_password.jwt_secret.result        # Use a randomly generated secret
    GOOGLE_CLIENT_ID        = "YOUR_GOOGLE_CLIENT_ID_PLACEHOLDER"      # Replace with actual ID (often non-sensitive)
    GOOGLE_CLIENT_SECRET    = "YOUR_PROD_GOOGLE_SECRET_PLACEHOLDER"    # Keep placeholder
  })

  # Add lifecycle rule to prevent accidental deletion if desired
  # lifecycle {
  #   prevent_destroy = true
  # }
}

# --- Outputs ---
output "app_secrets_arn" {
  description = "ARN of the application secrets stored in Secrets Manager"
  value       = aws_secretsmanager_secret.app_secrets.arn
}
