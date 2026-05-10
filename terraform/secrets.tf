# ── Secrets Manager ────────────────────────────────────────────────────────────

# Auth service DATABASE_URL
resource "aws_secretsmanager_secret" "auth_db_url" {
  name                    = "${var.project_name}/auth/database-url"
  recovery_window_in_days = 0 # Immediate delete on terraform destroy
}

resource "aws_secretsmanager_secret_version" "auth_db_url" {
  secret_id = aws_secretsmanager_secret.auth_db_url.id
  secret_string = "postgresql+asyncpg://auth_user:${var.auth_db_password}@${aws_db_instance.main.endpoint}/auth_db"
}

# Core service DATABASE_URL
resource "aws_secretsmanager_secret" "core_db_url" {
  name                    = "${var.project_name}/core/database-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "core_db_url" {
  secret_id = aws_secretsmanager_secret.core_db_url.id
  secret_string = "postgresql+asyncpg://core_user:${var.core_db_password}@${aws_db_instance.main.endpoint}/core_db"
}

# Notification service DATABASE_URL
resource "aws_secretsmanager_secret" "notif_db_url" {
  name                    = "${var.project_name}/notification/database-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "notif_db_url" {
  secret_id = aws_secretsmanager_secret.notif_db_url.id
  secret_string = "postgresql+asyncpg://notification_user:${var.notif_db_password}@${aws_db_instance.main.endpoint}/notification_db"
}

# RSA Private Key (auth only)
resource "aws_secretsmanager_secret" "rsa_private_key" {
  name                    = "${var.project_name}/auth/rsa-private-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rsa_private_key" {
  secret_id     = aws_secretsmanager_secret.rsa_private_key.id
  secret_string = file(var.rsa_private_key_path)
}

# RSA Public Key (shared by auth, core, notification)
resource "aws_secretsmanager_secret" "rsa_public_key" {
  name                    = "${var.project_name}/rsa-public-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rsa_public_key" {
  secret_id     = aws_secretsmanager_secret.rsa_public_key.id
  secret_string = file(var.rsa_public_key_path)
}

# Internal API Key (auth + core)
resource "aws_secretsmanager_secret" "internal_api_key" {
  name                    = "${var.project_name}/internal-api-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "internal_api_key" {
  secret_id     = aws_secretsmanager_secret.internal_api_key.id
  secret_string = var.internal_api_key
}

# RabbitMQ URL (core + notification) — points to Amazon MQ
resource "aws_secretsmanager_secret" "rabbitmq_url" {
  name                    = "${var.project_name}/rabbitmq-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "rabbitmq_url" {
  secret_id     = aws_secretsmanager_secret.rabbitmq_url.id
  secret_string = "amqps://rabbit_user:${var.rabbitmq_password}@${replace(aws_mq_broker.rabbitmq.instances[0].endpoints[0], "amqps://", "")}/"
}
