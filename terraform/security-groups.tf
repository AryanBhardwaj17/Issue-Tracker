# ── ALB Security Group ─────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  description = "ALB - allow HTTP from internet"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg-alb" }

  lifecycle {
    create_before_destroy = true
  }
}

# ── ECS Tasks Security Group ──────────────────────────────────────────────────

resource "aws_security_group" "tasks" {
  name_prefix = "${var.project_name}-tasks-"
  description = "ECS tasks - ALB inbound, inter-service, NAT outbound"
  vpc_id      = aws_vpc.main.id

  # ALB → backend services (port 8000)
  ingress {
    description     = "ALB to backend services"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # ALB → client (port 3000)
  ingress {
    description     = "ALB to client"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Inter-service: all traffic within this SG (gRPC :50051, AMQP :5672, etc.)
  ingress {
    description = "Inter-service communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Outbound: all (NAT → ECR, CloudWatch, Secrets Manager)
  egress {
    description = "All outbound via NAT"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg-tasks" }

  lifecycle {
    create_before_destroy = true
  }
}

# ── RDS Security Group ────────────────────────────────────────────────────────

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "RDS - only ECS tasks can connect on 5432"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.tasks.id]
  }

  tags = { Name = "${var.project_name}-sg-rds" }

  lifecycle {
    create_before_destroy = true
  }
}
