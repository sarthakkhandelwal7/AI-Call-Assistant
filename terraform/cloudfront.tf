# terraform/cloudfront.tf

# Create CloudFront Origin Access Control (OAC)
resource "aws_cloudfront_origin_access_control" "frontend_oac" {
  name                              = "${var.project_name}-frontend-oac-${var.environment}"
  description                       = "Origin Access Control for Frontend S3 Bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Create CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend_distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Frontend distribution for ${var.project_name}"
  default_root_object = "index.html"

  # Define the S3 origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name # Use regional domain name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend_oac.id
    origin_id                = "S3-${aws_s3_bucket.frontend.bucket}" # A unique identifier for the origin
  }

  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend.bucket}" # Must match origin_id above

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600 # Cache for 1 hour by default
    max_ttl                = 86400 # Cache for 1 day maximum
  }

  # Price class (Use lowest cost for free tier focus)
  price_class = "PriceClass_100" # US, Canada, Europe

  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none" # No geographic restrictions
    }
  }

  # Viewer certificate (Using default CloudFront certificate)
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Define S3 Bucket Policy allowing CloudFront access via OAC
data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"] # Allow access to all objects in the bucket

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    # Condition to ensure access is only through *this* distribution
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend_distribution.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.s3_policy.json

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}


# --- Outputs ---
output "cloudfront_distribution_domain_name" {
  description = "Domain name of the CloudFront distribution for the frontend"
  value       = aws_cloudfront_distribution.frontend_distribution.domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend_distribution.id
}
