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
- **jobs-worker** (Arq) consumes on-demand background jobs (document ingestion,
  full-universe sentiment refresh) enqueued via `POST /api/jobs/*`; needs Redis.
- **Postgres** is the system of record; schema is owned by **Alembic**.
- The vector store runs as a standalone **chroma** service (set `CHROMA_HOST`);
  API reads and jobs-worker writes share it over HTTP. Source filings
  (`documents/`) and the `parents.json` sidecar are mounted on both. Back the
  Chroma data dir with a persistent volume in prod.

## Local production-shaped stack (Docker)

```bash
cp .env.example .env        # fill in secrets (see below)
docker compose up --build
# api → http://localhost:8000 ; migrations run automatically (migrate service)
```

Services: `db` (Postgres) → `migrate` (alembic upgrade head, one-shot) →
`chroma` (vector store) + `api` + `worker` + `jobs-worker`.

The vector store runs as its own `chroma` service (Chroma in client/server mode):
the `api` reads and the `jobs-worker` writes to it over HTTP via `CHROMA_HOST`,
so there's no shared-filesystem locking. With `CHROMA_HOST` unset the code falls
back to an embedded store under `CHROMA_DIR` (zero-setup local dev).

## Single-EC2 deployment (AWS)

The whole compose stack runs on one EC2 instance — quickest path to a live
backend. Use a managed DB/cache later by pointing `DATABASE_URL` /
`BACKEND_REDIS_URL` at RDS / ElastiCache and removing the `db` / `redis` services.

1. **Instance:** Amazon Linux 2023 / Ubuntu, ≥ `t3.large` (4 GB RAM — torch +
   FinBERT + the cross-encoder need headroom). Install Docker + the compose plugin.
2. **EBS for the vector store:** attach a separate EBS volume so reindexes and
   instance replacement don't lose embeddings (they cost Gemini quota to rebuild):
   ```bash
   sudo mkfs -t xfs /dev/nvme1n1          # first time only
   sudo mkdir -p /mnt/chroma && sudo mount /dev/nvme1n1 /mnt/chroma
   echo '/dev/nvme1n1 /mnt/chroma xfs defaults,nofail 0 2' | sudo tee -a /etc/fstab
   ```
   Then set `CHROMA_DATA_DIR=/mnt/chroma` in `.env` (the `chroma` service binds it).
3. **Secrets:** `cp .env.example .env` and fill it (or pull from SSM/Secrets
   Manager at boot). Set `BACKEND_CORS_ORIGINS` to your Vercel frontend origin.
4. **Run:** `docker compose up -d --build` (the `migrate` service applies
   migrations before `api`/`worker` start).
5. **TLS / domain:** terminate HTTPS in front of `api:8000` — either an ALB +
   ACM cert targeting the instance, or Caddy/nginx on the box. Security group:
   allow 443 inbound; keep 8000 and the Chroma port private.
6. Point the frontend's `VITE_API_URL` at `https://<your-domain>/api`.

> NSE blocks non-Indian IPs — if the engine can't fetch NSE from a US/EU region,
> run the instance in `ap-south-1` (Mumbai) or keep the AWS NSE proxy routing.

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
- [ ] Persistent volume for the `chroma` data dir (`CHROMA_DATA_DIR`) + `documents/`.
- [ ] HTTPS/TLS terminated at the proxy/load balancer.
- [ ] **Regulatory:** confirm the SEBI positioning (educational/informational vs
      registered investment advice) before charging.
```
