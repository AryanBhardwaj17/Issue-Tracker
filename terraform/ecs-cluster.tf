# ── ECS Cluster ───────────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "main" {
  name = var.project_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = var.project_name }
}

# ── Cloud Map Namespace for Service Connect ──────────────────────────────────

resource "aws_service_discovery_http_namespace" "main" {
  name        = "${var.project_name}.local"
  description = "Service Connect namespace for ${var.project_name}"

  tags = { Name = "${var.project_name}-namespace" }
}
