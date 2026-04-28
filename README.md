# Issue Tracker

A microservices-based project management web application for organizing work into projects, epics, user stories, tasks, and comments with a Kanban board view and email/in-app notifications.

---

## Architecture

```
Browser (Next.js SPA)
        │
        ▼
Nginx (API Gateway)          — TLS termination, path-based routing
 ├── /api/v1/auth/*     →    Auth Service     (FastAPI)  →  user_db (Postgres)
 ├── /api/v1/*          →    Core Service     (FastAPI)  →  core_db (Postgres)
 ├── /api/v1/notif-*    →    Notification Svc (FastAPI)  →  notification_db (Postgres)
 └── /uploads/*         →    Core Service (static files)
                                    │
                                    ▼
                              RabbitMQ (domain events)
                                    │
                                    ▼
                         Notification Service consumer
                                    │
                                    ▼
                               SMTP (email)
```

**Services:**

| Service | Port | Responsibility |
|---|---|---|
| Auth Service | 8001 | Registration, login, JWT access tokens, refresh token rotation |
| Core Service | 8002 | Projects, epics, user stories, tasks, comments |
| Notification Service | 8003 | In-app notifications, email delivery via RabbitMQ events |
| Nginx Gateway | 80/443 | Reverse proxy, CORS, routing |
| Frontend | 3000 | Next.js SPA |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, zustand, dnd-kit |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic |
| Databases | PostgreSQL (one per service) |
| Message bus | RabbitMQ |
| Gateway | Nginx |
| Containers | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Run (production-like)

```bash
docker compose up --build
```

### Run (development — with hot reload)

```bash
docker compose -f docker-compose.dev.yml up --build
```

The frontend is available at `http://localhost:3000`.  
The API gateway is at `http://localhost:80`.

---

## Project Structure

```
├── client/               # Next.js frontend
├── gateway/              # Nginx configuration
├── services/
│   ├── auth/             # Auth Service (FastAPI)
│   ├── core/             # Core Service (FastAPI)
│   └── notification/     # Notification Service (FastAPI)
├── shared/               # Shared Python library (JWT helpers, schemas)
├── docs/                 # HLD, LLD, DB schema, requirements
├── docker-compose.yml
└── docker-compose.dev.yml
```

---

## Database Schema

See [docs/database.txt](docs/database.txt) for the full schema.  
See [docs/HLD.md](docs/HLD.md) and [docs/LLD.md](docs/LLD.md) for architecture details.

---

## Key Features

- **JWT auth** — short-lived access tokens (in-memory on client), httpOnly refresh token cookie with rotation
- **Projects & Members** — OWNER / MEMBER roles, project-scoped permissions
- **Epics & User Stories** — 7-status Kanban workflow, Fibonacci story points, priority levels
- **Tasks & Subtasks** — 2-level task hierarchy per story
- **Comments** — with optional image attachments
- **Notifications** — in-app inbox + email delivery via RabbitMQ events
