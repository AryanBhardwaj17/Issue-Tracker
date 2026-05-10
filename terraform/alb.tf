# ── Application Load Balancer ──────────────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = { Name = "${var.project_name}-alb" }
}

# ── Target Groups ─────────────────────────────────────────────────────────────

resource "aws_lb_target_group" "auth" {
  name        = "${var.project_name}-tg-auth"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/api/v1/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200"
  }

  tags = { Name = "${var.project_name}-tg-auth" }
}

resource "aws_lb_target_group" "core" {
  name        = "${var.project_name}-tg-core"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/api/v1/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200"
  }

  tags = { Name = "${var.project_name}-tg-core" }
}

resource "aws_lb_target_group" "notification" {
  name        = "${var.project_name}-tg-notif"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/api/v1/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200"
  }

  tags = { Name = "${var.project_name}-tg-notif" }
}

resource "aws_lb_target_group" "client" {
  name        = "${var.project_name}-tg-client"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200,307"
  }

  tags = { Name = "${var.project_name}-tg-client" }
}

# ── Listener (HTTP :80) ──────────────────────────────────────────────────────

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action: forward to client (catch-all for /*)
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.client.arn
  }
}

# ── Listener Rules (path-based routing — replaces nginx.conf) ────────────────

# Priority 1: /api/v1/auth/* → auth-service
resource "aws_lb_listener_rule" "auth" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.auth.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/auth/*"]
    }
  }
}

# Priority 2: /api/v1/users/* → auth-service
resource "aws_lb_listener_rule" "users" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 2

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.auth.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/users/*"]
    }
  }
}

# Priority 3: /api/v1/notifications/* → notification-service
resource "aws_lb_listener_rule" "notifications" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 3

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.notification.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/notifications/*"]
    }
  }
}

# Priority 4: /uploads/* → core-service
resource "aws_lb_listener_rule" "uploads" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 4

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.core.arn
  }

  condition {
    path_pattern {
      values = ["/uploads/*"]
    }
  }
}

# Priority 5: /api/v1/* → core-service (catch-all API)
resource "aws_lb_listener_rule" "core_api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 5

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.core.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/*"]
    }
  }
}

# Default action (priority 99999): /* → client (set in listener default_action)
