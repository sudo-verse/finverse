# Deploying Finverse

Finverse is a multi-tenant SaaS: FastAPI backend + background worker + Postgres,
with a static React frontend.

## Architecture

```
              ┌──────────────┐
  browser ───▶│  frontend    │  static build (Vite) → CDN/static host
              │  (React)     │  VITE_API_URL → API base
              └──────┬───────┘
                     │ HTTPS  (Authorization: Bearer <JWT>)
              ┌──────▼───────┐        ┌──────────────┐
              │   api        │───────▶│  Postgres    │
              │ (uvicorn,    │        │  (managed)   │
              │  worker-free)│        └──────▲───────┘
              └──────────────┘               │
              ┌──────────────┐               │
              │   worker     │───────────────┘  news engine + daily ETL + alerts
              │ (1 instance) │
              └──────────────┘
```

- **api** runs worker-free (`BACKEND_ENGINE_ENABLED/ETL_ENABLED/ALERTS_ENABLED=false`)
  so it can scale to N replicas.
- **worker** (exactly one) owns the news engine, daily ETL and alert evaluator.
- **Postgres** is the system of record; schema is owned by **Alembic**.
- The vector store (`chroma_db/`) and source filings (`documents/`) are mounted
  on the API (RAG reads). Use a persistent volume in prod.

## Local production-shaped stack (Docker)

```bash
cp .env.example .env        # fill in secrets (see below)
docker compose up --build
# api → http://localhost:8000 ; migrations run automatically (migrate service)
```

Services: `db` (Postgres) → `migrate` (alembic upgrade head, one-shot) →
`api` + `worker`.

## Migrations

The `migrate` service runs `alembic upgrade head` before api/worker start. For
a non-compose host, run it yourself on each release:

```bash
DATABASE_URL=postgresql+psycopg://… alembic upgrade head
```

After changing a model: `alembic revision --autogenerate -m "…"`, review, commit.

## Frontend

```bash
cd frontend
VITE_API_URL=https://api.finverse.example/api npm run build   # → dist/
```

Serve `frontend/dist/` from any static host/CDN (Vercel, Netlify, Cloudflare,
S3+CloudFront). Point `VITE_API_URL` at the deployed API.

## Required production configuration (env)

| Var | Purpose |
| --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://…` (managed Postgres) |
| `BACKEND_JWT_SECRET` | long random string — sessions depend on it |
| `GEMINI_API_KEY` | AI features (RAG, reports, sentiment news) |
| `BACKEND_STRIPE_SECRET_KEY` | billing |
| `BACKEND_STRIPE_WEBHOOK_SECRET` | **required** to verify Stripe webhooks |
| `BACKEND_CORS_ORIGINS` | the frontend origin(s) |
| `BACKEND_APP_BASE_URL` | where Stripe redirects after checkout |

Set these in the host's secret manager — **not** in a committed file.

## Stripe webhook

Create a webhook endpoint in the Stripe dashboard → `https://api…/api/billing/webhook`,
subscribe to `checkout.session.completed`, `customer.subscription.deleted`,
`customer.subscription.updated`; put its signing secret in
`BACKEND_STRIPE_WEBHOOK_SECRET`. Locally: `stripe listen --forward-to
localhost:8000/api/billing/webhook`.

## Observability

- **Probes:** `GET /health` (liveness — process up) and `GET /readyz` (readiness
  — DB reachable, returns 503 otherwise). Point the orchestrator's liveness at
  `/health` and readiness/traffic-gating at `/readyz`.
- **Request correlation:** every request carries an `X-Request-ID` (inbound or
  generated), echoed in the response header and stamped on every log line —
  `2026-… [<request-id>] finverse.api INFO …`.
- **Errors:** set `BACKEND_SENTRY_DSN` (+ `BACKEND_ENVIRONMENT`) to ship
  exceptions to Sentry; no-op when unset.
- **Rate limiting:** auth endpoints are limited per-IP (brute-force / signup
  spam → 429 + `Retry-After`). Set `BACKEND_REDIS_URL` so the limit is shared
  across API replicas; without it each replica limits in-memory (so set a single
  replica or Redis in prod). A bad `BACKEND_REDIS_URL` falls back to in-memory.

## Go-live checklist

- [ ] `BACKEND_JWT_SECRET` set (strong); **rotate** any keys shared during dev.
- [ ] `BACKEND_STRIPE_WEBHOOK_SECRET` set (webhooks rejected otherwise in prod).
- [ ] `DATABASE_URL` → managed Postgres; `alembic upgrade head` run.
- [ ] `BACKEND_CORS_ORIGINS` / `BACKEND_APP_BASE_URL` → real domains.
- [ ] Persistent volumes for `chroma_db/` and `documents/`.
- [ ] HTTPS/TLS terminated at the proxy/load balancer.
- [ ] **Regulatory:** confirm the SEBI positioning (educational/informational vs
      registered investment advice) before charging.
```
