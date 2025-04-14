variable "aws_region" {
    description = "The AWS region to deploy resources in."
    type        = string
    default     = "us-east-1" # Or your preferred default
}

variable "environment" {
    description = "The deployment environment (e.g., dev, staging, prod)."
    type        = string
    default     = "dev"
    validation {
    # Optional: Ensure environment is one of the allowed values
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
    }
}

variable "project_name" {
    description = "A short name for the project, used in naming resources."
    type        = string
    default     = "ai-call-assistant"
}

variable "backend_api_url" {
    description = "The base URL for the backend API."
    type        = string
    default     = "" # Default empty, will be set during apply
}