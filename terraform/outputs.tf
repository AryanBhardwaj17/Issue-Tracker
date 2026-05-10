output "alb_dns_name" {
  description = "ALB DNS name — use this as your app URL"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "ecr_registry" {
  description = "ECR registry URL"
  value       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "ecr_repo_auth" {
  description = "ECR repo URI for auth service"
  value       = aws_ecr_repository.services["auth"].repository_url
}

output "ecr_repo_core" {
  description = "ECR repo URI for core service"
  value       = aws_ecr_repository.services["core"].repository_url
}

output "ecr_repo_notification" {
  description = "ECR repo URI for notification service"
  value       = aws_ecr_repository.services["notification"].repository_url
}

output "ecr_repo_client" {
  description = "ECR repo URI for client"
  value       = aws_ecr_repository.services["client"].repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_connect_namespace" {
  description = "Cloud Map namespace for Service Connect"
  value       = aws_service_discovery_http_namespace.main.name
}
