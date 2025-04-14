resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend-assets-${var.environment}" # Bucket names must be globally unique

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Block all public access settings for the bucket
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket ownership controls for ACLs if needed (often required for static hosting/CloudFront interactions)
resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Output the bucket name
output "s3_frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}
output "s3_frontend_bucket_regional_domain_name" {
   value = aws_s3_bucket.frontend.bucket_regional_domain_name
}
