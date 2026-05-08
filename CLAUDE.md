# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Five containerised services communicating over a shared Docker network (`issue-tracker-net`):

```
Browser → Nginx Gateway (:80)
  ├── /api/v1/auth/*  /api/v1/users/*   → Auth Service        (:8000 HTTP, :50051 gRPC)
  ├── /api/v1/notifications/*            → Notification Service (:8000)
  ├── /api/v1/*  /uploads/*             → Core Service         (:8000)
  └── /                                 → Next.js Client       (:3000)

Core ──gRPC──► Auth           (user-lookup, protected by INTERNAL_API_KEY)
Core ──RabbitMQ──► Notification  (topic exchange "domain-events", queue "notification-service")
Notification ──SMTP──► Email provider
```

**Three independent PostgreSQL databases** (one per backend service — they never share a DB).

**JWT RS256**: Auth signs tokens with `RSA_PRIVATE_KEY`. Core and Notification only hold `RSA_PUBLIC_KEY` and verify — they never sign.

**CORS is nginx-only.** Do not add `CORSMiddleware` to any FastAPI service; it would produce duplicate headers.

**RabbitMQ events are fire-and-forget** from Core (`publisher.py` swallows failures to protect the caller's DB transaction). The Notification consumer retries a message once on handler failure, then acks to avoid infinite loops.

**gRPC server in Auth starts only when `INTERNAL_API_KEY` is non-empty.** In dev/test flows with no key set, it silently skips.

**`shared/`** is a local Python library (`shared/jwt.py`, `shared/schemas.py`, `shared/exceptions.py`) installed as a package dependency in each backend service via `pyproject.toml`.

**File uploads**: Core serves `/uploads/<filename>` as static files from `UPLOADS_DIR` (default `/app/uploads`), backed by a named Docker volume.

---

## Development

### Run everything

```bash
# Production-like (uses pre-built images from env vars IMAGE_AUTH, IMAGE_CORE, etc.)
docker compose up --build

# Development — hot reload, exposes DBs on host ports 5433/5434/5435, gateway on :8080
docker compose -f docker-compose.dev.yml up --build
```

Dev compose uses per-service `.env` files (`services/auth/.env`, `services/core/.env`, `services/notification/.env`) and includes MailHog (SMTP :1025, web UI :8025) instead of a real SMTP server.

### Backend (per service)

Each service is an independent Python project. Run commands from within the service directory.

```bash
cd services/core        # or auth / notification

# Install (once)
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file or test
pytest tests/test_project_service.py
pytest tests/test_project_service.py::test_create_project_success

# Lint
ruff check .
ruff format .
```

Tests use **SQLite in-memory** (via `aiosqlite`) — no Docker required. `conftest.py` stubs all required env vars before importing any app module.

### Database migrations

```bash
cd services/<name>
alembic upgrade head      # apply all pending migrations
alembic revision --autogenerate -m "description"   # generate a new migration
```

> **Production note**: Auth and Core do **not** auto-run Alembic in their Docker CMD (`create_all` only fires when `DEBUG=True`). Migrations must be applied as a separate init step before deploying. Notification's Dockerfile CMD runs `alembic upgrade head` automatically.

### gRPC stubs (proto regeneration)

```bash
make proto-gen
```

Requires `grpcio-tools` installed. Regenerates Python stubs in `services/auth/app/generated/` and `services/core/app/generated/` from `proto/user_lookup.proto`.

### Frontend

```bash
cd client
npm install

npm run dev          # Next.js dev server on :3000
npm run build        # production build (outputs standalone bundle)
npm test             # Vitest unit tests (jsdom)
npm run test:watch
npm run lint
```

> The `client/AGENTS.md` note: this repo uses **Next.js 16** which has breaking changes from earlier versions. Read `node_modules/next/dist/docs/` before assuming App Router conventions from training data.

The frontend is a Next.js SPA using the App Router. All API calls go through an Axios instance (`src/lib/interceptor.ts`) that auto-attaches the access token and handles 401 → token refresh. Server state is managed via React Query (hooks in `src/hooks/`); auth state lives in a Zustand store (`src/stores/authStore.ts`). The Axios `baseURL` points to the Nginx gateway's `/api/v1` path.

---

## Environment Variables

All settings use `pydantic-settings` and fail at startup if required vars are missing.

### Auth Service (required)
| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `RSA_PRIVATE_KEY` | Full PEM, newlines as `\n` |
| `RSA_PUBLIC_KEY` | Full PEM, newlines as `\n` |
| `INTERNAL_API_KEY` | Shared secret for gRPC auth; empty = gRPC disabled |
| `GRPC_PORT` | Default `50051` |
| `LOG_LEVEL` | Default `INFO` |

### Core Service (required)
| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `RSA_PUBLIC_KEY` | Verify-only |
| `AUTH_SERVICE_GRPC_HOST` | Default `auth-service:50051` |
| `INTERNAL_API_KEY` | Sent as metadata on every gRPC call |
| `RABBITMQ_URL` | `amqp://...` |
| `LOG_LEVEL` / `LOG_FORMAT` | `LOG_FORMAT=json` for production |

### Notification Service (required)
| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `RSA_PUBLIC_KEY` | Verify-only |
| `RABBITMQ_URL` | `amqp://...` |
| `SMTP_HOST` / `SMTP_PORT` | Email delivery |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Optional credentials |
| `SMTP_FROM` | Default `noreply@issuetracker.local` |
| `SMTP_USE_TLS` | Default `true` |
| `FRONTEND_URL` | Used to build links inside emails |
| `LOG_LEVEL` / `LOG_FORMAT` | `LOG_FORMAT=json` for production |

---

## Service Entry Points

| Service | Start command | Ports |
|---|---|---|
| Auth | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | 8000 (HTTP), 50051 (gRPC) |
| Core | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | 8000 |
| Notification | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` | 8000 |
| Gateway | nginx | 80 |
| Client | `node server.js` (Next.js standalone output) | 3000 |

Health endpoints: `GET /api/v1/health` on Auth and Core; `GET /health` on the Nginx gateway.
