# ── Amazon MQ (Managed RabbitMQ) ──────────────────────────────────────────────

resource "aws_security_group" "mq" {
  name_prefix = "${var.project_name}-mq-"
  description = "Amazon MQ - only ECS tasks can connect on 5671"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "AMQPS from ECS tasks"
    from_port       = 5671
    to_port         = 5671
    protocol        = "tcp"
    security_groups = [aws_security_group.tasks.id]
  }

  ingress {
    description     = "HTTPS management UI from ECS tasks"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.tasks.id]
  }

  tags = { Name = "${var.project_name}-sg-mq" }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_mq_broker" "rabbitmq" {
  broker_name = "${var.project_name}-mq"

  engine_type        = "RabbitMQ"
  engine_version     = "3.13"
  host_instance_type = "mq.m7g.medium"
  deployment_mode    = "SINGLE_INSTANCE"

  publicly_accessible = false
  auto_minor_version_upgrade = true

  user {
    username = "rabbit_user"
    password = var.rabbitmq_password
  }

  subnet_ids         = [aws_subnet.private_a.id]
  security_groups    = [aws_security_group.mq.id]

  logs {
    general = true
  }

  tags = { Name = "${var.project_name}-mq" }
}
