# terraform/vpc.tf

# Define the VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16" # Example CIDR, adjust if needed
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.project_name}-vpc-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Define Availability Zones based on the region
data "aws_availability_zones" "available" {
  state = "available"
}

# Define Private Subnets (for RDS, App Runner)
resource "aws_subnet" "private" {
  # Create one private subnet in each Availability Zone (adjust count as needed)
  count             = 2
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  vpc_id            = aws_vpc.main.id
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.project_name}-private-subnet-${var.environment}-${count.index}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Define Public Subnets (for potential Load Balancer, NAT Gateway)
resource "aws_subnet" "public" {
  count                   = 2
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + length(aws_subnet.private)) # Offset index
  vpc_id                  = aws_vpc.main.id
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true # Instances in public subnet get public IP

  tags = {
    Name        = "${var.project_name}-public-subnet-${var.environment}-${count.index}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Networking for Public Subnets (Internet Access) ---

# Internet Gateway for the VPC
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw-${var.environment}"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0" # Route traffic destined for outside VPC to IGW
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt-${var.environment}"
  }
}

# Associate Public Subnets with the Public Route Table
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- Networking for Private Subnets (NAT Gateway for outbound internet) ---
# Optional but usually needed for containers/functions in private subnets
# to reach external services (e.g., Twilio, OpenAI, ECR)

# --- Remove NAT Gateway EIP ---
# resource "aws_eip" "nat" {
#   domain     = "vpc"
#   depends_on = [aws_internet_gateway.default]
#   tags = merge(var.common_tags, {
#       Name = "${var.project_name}-nat-eip-${var.environment}"
#   })
# }

# --- Remove NAT Gateway Resource ---
# resource "aws_nat_gateway" "default" {
#   allocation_id = aws_eip.nat.id
#   subnet_id     = aws_subnet.public[0].id # Place NAT GW in the first public subnet
#   depends_on    = [aws_internet_gateway.default]
#   tags = merge(var.common_tags, {
#     Name = "${var.project_name}-nat-gw-${var.environment}"
#   })
# }

# Private Route for NAT Gateway (REMOVE THIS ROUTE)
# resource "aws_route" "private_nat_gateway" {
#   route_table_id         = aws_route_table.private.id
#   destination_cidr_block = "0.0.0.0/0"
#   nat_gateway_id         = aws_nat_gateway.default.id
# }

# Route Table for Private Subnets
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  # Remove the route block pointing to the deleted NAT Gateway
  # route {
  #   cidr_block     = "0.0.0.0/0" # Route outbound traffic to NAT Gateway
  #   nat_gateway_id = aws_nat_gateway.nat.id 
  # }

  # You might add routes here later if private subnets need to reach
  # other specific VPC resources (e.g., VPC Endpoints), but no default 
  # internet route via NAT is needed now.

  tags = {
    Name = "${var.project_name}-private-rt-${var.environment}"
  }
}

# Associate Private Subnets with the Private Route Table
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --- Outputs ---
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}
