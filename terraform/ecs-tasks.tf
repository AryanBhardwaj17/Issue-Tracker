# ── Task Definitions ──────────────────────────────────────────────────────────

# Auth Service
resource "aws_ecs_task_definition" "auth" {
  family                   = "${var.project_name}-auth"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "auth"
      image     = "${aws_ecr_repository.services["auth"].repository_url}:latest"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp", name = "http" },
        { containerPort = 50051, protocol = "tcp", name = "grpc" }
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.auth_db_url.arn },
        { name = "RSA_PRIVATE_KEY", valueFrom = aws_secretsmanager_secret.rsa_private_key.arn },
        { name = "RSA_PUBLIC_KEY", valueFrom = aws_secretsmanager_secret.rsa_public_key.arn },
        { name = "INTERNAL_API_KEY", valueFrom = aws_secretsmanager_secret.internal_api_key.arn }
      ]

      environment = [
        { name = "GRPC_PORT", value = "50051" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "COOKIE_SECURE", value = "false" }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}/auth"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Core Service
resource "aws_ecs_task_definition" "core" {
  family                   = "${var.project_name}-core"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "core"
      image     = "${aws_ecr_repository.services["core"].repository_url}:latest"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp", name = "http" }
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.core_db_url.arn },
        { name = "RSA_PUBLIC_KEY", valueFrom = aws_secretsmanager_secret.rsa_public_key.arn },
        { name = "INTERNAL_API_KEY", valueFrom = aws_secretsmanager_secret.internal_api_key.arn },
        { name = "RABBITMQ_URL", valueFrom = aws_secretsmanager_secret.rabbitmq_url.arn }
      ]

      environment = [
        { name = "AUTH_SERVICE_GRPC_HOST", value = "auth-service.${var.project_name}.local:50051" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "LOG_FORMAT", value = "json" },
        { name = "USE_S3", value = "true" },
        { name = "S3_BUCKET", value = aws_s3_bucket.uploads.bucket },
        { name = "S3_REGION", value = var.aws_region }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}/core"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Notification Service
resource "aws_ecs_task_definition" "notification" {
  family                   = "${var.project_name}-notification"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "notification"
      image     = "${aws_ecr_repository.services["notification"].repository_url}:latest"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp", name = "http" }
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.notif_db_url.arn },
        { name = "RSA_PUBLIC_KEY", valueFrom = aws_secretsmanager_secret.rsa_public_key.arn },
        { name = "RABBITMQ_URL", valueFrom = aws_secretsmanager_secret.rabbitmq_url.arn }
      ]

      environment = [
        { name = "SMTP_HOST", value = "localhost" },
        { name = "SMTP_PORT", value = "1025" },
        { name = "SMTP_USE_TLS", value = "false" },
        { name = "SMTP_FROM", value = "noreply@issuetracker.dev" },
        { name = "FRONTEND_URL", value = "http://${aws_lb.main.dns_name}" },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "LOG_FORMAT", value = "json" }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}/notification"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Client (Next.js)
resource "aws_ecs_task_definition" "client" {
  family                   = "${var.project_name}-client"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "client"
      image     = "${aws_ecr_repository.services["client"].repository_url}:latest"
      essential = true

      portMappings = [
        { containerPort = 3000, protocol = "tcp", name = "http" }
      ]

      environment = [
        { name = "NODE_ENV", value = "production" },
        { name = "HOSTNAME", value = "0.0.0.0" }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "wget -q --spider http://localhost:3000/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}/client"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

