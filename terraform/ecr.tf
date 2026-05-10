# ── ECR Repositories ──────────────────────────────────────────────────────────

locals {
  ecr_services = ["auth", "core", "notification", "client"]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(local.ecr_services)

  name                 = "${var.project_name}/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Allow terraform destroy to delete repos with images

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "${var.project_name}-${each.key}" }
}

# ── Lifecycle policy: keep only last 10 images per repo ───────────────────────

resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
