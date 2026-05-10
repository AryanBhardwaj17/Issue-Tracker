# ── CloudWatch Log Groups ─────────────────────────────────────────────────────

locals {
  log_services = ["auth", "core", "notification", "client"]
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each = toset(local.log_services)

  name              = "/ecs/${var.project_name}/${each.key}"
  retention_in_days = 7

  tags = { Name = "${var.project_name}-${each.key}-logs" }
}
