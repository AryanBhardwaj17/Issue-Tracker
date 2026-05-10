# ── ECS Services ──────────────────────────────────────────────────────────────

# Auth Service (desired=2)
resource "aws_ecs_service" "auth" {
  name            = "svc-auth"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.auth.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  enable_execute_command = true

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.auth.arn
    container_name   = "auth"
    container_port   = 8000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.main.arn

    service {
      port_name      = "http"
      discovery_name = "auth-service"
      client_alias {
        port     = 8000
        dns_name = "auth-service.${var.project_name}.local"
      }
    }

    service {
      port_name      = "grpc"
      discovery_name = "auth-service-grpc"
      client_alias {
        port     = 50051
        dns_name = "auth-service.${var.project_name}.local"
      }
    }
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]
}

# Core Service (desired=2)
resource "aws_ecs_service" "core" {
  name            = "svc-core"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.core.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  enable_execute_command = true

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.core.arn
    container_name   = "core"
    container_port   = 8000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.main.arn

    service {
      port_name      = "http"
      discovery_name = "core-service"
      client_alias {
        port     = 8000
        dns_name = "core-service.${var.project_name}.local"
      }
    }
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http, aws_ecs_service.auth, aws_mq_broker.rabbitmq]
}

# Notification Service (desired=2)
resource "aws_ecs_service" "notification" {
  name            = "svc-notification"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.notification.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  enable_execute_command = true

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.notification.arn
    container_name   = "notification"
    container_port   = 8000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.main.arn

    service {
      port_name      = "http"
      discovery_name = "notification-service"
      client_alias {
        port     = 8000
        dns_name = "notification-service.${var.project_name}.local"
      }
    }
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http, aws_mq_broker.rabbitmq]
}

# Client Service (desired=2)
resource "aws_ecs_service" "client" {
  name            = "svc-client"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.client.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  enable_execute_command = true

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.client.arn
    container_name   = "client"
    container_port   = 3000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.main.arn

    service {
      port_name      = "http"
      discovery_name = "client"
      client_alias {
        port     = 3000
        dns_name = "client.${var.project_name}.local"
      }
    }
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]
}


