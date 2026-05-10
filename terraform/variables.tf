# ── General ────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "issue-tracker"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

# ── RDS ───────────────────────────────────────────────────────────────────────

variable "rds_master_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "auth_db_password" {
  description = "Password for auth_user in RDS"
  type        = string
  sensitive   = true
}

variable "core_db_password" {
  description = "Password for core_user in RDS"
  type        = string
  sensitive   = true
}

variable "notif_db_password" {
  description = "Password for notification_user in RDS"
  type        = string
  sensitive   = true
}

# ── Secrets ───────────────────────────────────────────────────────────────────

variable "internal_api_key" {
  description = "Shared secret for gRPC auth between services"
  type        = string
  sensitive   = true
}

variable "rabbitmq_password" {
  description = "RabbitMQ default user password"
  type        = string
  sensitive   = true
}

variable "rsa_private_key_path" {
  description = "Path to RSA private key PEM file"
  type        = string
}

variable "rsa_public_key_path" {
  description = "Path to RSA public key PEM file"
  type        = string
}

# ── GitLab CI ─────────────────────────────────────────────────────────────────

variable "gitlab_project_path" {
  description = "GitLab project path for OIDC trust (e.g. group/project)"
  type        = string
}
