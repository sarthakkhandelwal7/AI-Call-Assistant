resource "aws_ecr_repository" "backend" {
    name                 = "${var.project_name}-backend-${var.environment}"
    image_tag_mutability = "MUTABLE" # Or "IMMUTABLE" for stricter versioning

    image_scanning_configuration {
    scan_on_push = true
    }

    tags = {
    Project     = var.project_name
    Environment = var.environment # Use the variable
    }
}

# Output the repository URLs for use in build scripts or other configurations
output "ecr_backend_repository_url" {
    value = aws_ecr_repository.backend.repository_url
}