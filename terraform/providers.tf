terraform {
    required_providers {
    aws = {
        source  = "hashicorp/aws"
        version = "~> 5.0" # Use a recent version
    }
    random = {
        source  = "hashicorp/random"
        version = "~> 3.1"
    }
    }
    required_version = ">= 1.0"
}

provider "aws" {
    region = var.aws_region # Use the variable
}