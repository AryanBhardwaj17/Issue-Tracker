# ── RDS Subnet Group ──────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = { Name = "${var.project_name}-db-subnets" }
}

# ── RDS Instance (Single-AZ, Free Tier) ──────────────────────────────────────

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t4g.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "postgres" # default DB; we create logical DBs via SQL
  username = "postgres"
  password = var.rds_master_password

  multi_az            = false # Single-AZ — free tier
  publicly_accessible = false
  skip_final_snapshot = true # No snapshot on destroy (demo project)

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 0 # Free tier restriction — no automated backups

  tags = { Name = "${var.project_name}-db" }
}
