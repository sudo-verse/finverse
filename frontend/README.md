# Finverse — Frontend

Modern React frontend for the **Finverse** NSE AI Stock Intelligence Platform. A
fintech-terminal UI (Bloomberg / TradingView / Kite inspired) with a dark
glassmorphism theme.

## Stack

| Concern        | Library                                  |
| -------------- | ---------------------------------------- |
| Framework      | React 19 + Vite 7 + TypeScript           |
| Styling        | Tailwind CSS v4 (+ custom glass theme)   |
| Components     | Shadcn-style primitives on Radix UI      |
| Routing        | React Router v7                          |
| Data fetching  | TanStack Query v5 + Axios                |
| Charts         | Recharts v3                              |
| Animation      | Framer Motion                            |
| Icons          | Lucide React                             |
| Toasts         | Sonner                                   |
| Command palette| cmdk (`Ctrl+K`)                          |

## Getting started

```bash
npm install
npm run dev        # http://localhost:5173 (expects the API on :8000)
```

Other scripts:

```bash
npm run build      # type-check + production build → dist/
npm run preview    # serve the production build
npm run typecheck  # tsc --noEmit
npm run lint       # eslint
```

## Connecting the backend

The app talks **directly to the live Finverse API** (`backend/`). In dev,
`/api` is proxied to `http://localhost:8000` (see `vite.config.ts`), so just
run both:

```bash
python -m uvicorn backend.main:app --reload --port 8000   # from the repo root
npm run dev                                               # from frontend/
```

For production builds, set `VITE_API_URL` to the deployed API base URL.

Expected endpoints:

```
GET  /api/dashboard
GET  /api/signals
GET  /api/stocks
GET  /api/stocks/:symbol
GET  /api/competitors/:symbol
GET  /api/portfolio
POST /api/report
POST /api/chat
```

The expected response shapes are the TypeScript interfaces in
`src/types/index.ts`.

## Project structure

```
src/
├── api/            # axios client + typed service layer (live API)
├── components/
│   ├── ui/         # shadcn-style primitives (button, card, dialog, …)
│   ├── layout/     # sidebar, topbar, command palette, app shell
│   └── shared/     # metric cards, signal badges, chart theme, stock search
├── hooks/          # TanStack Query hooks, useDebounce
├── lib/            # cn(), INR/percent/date formatters
├── pages/          # dashboard, signals, stock-analysis, competitors,
│                   # portfolio, assistant, settings
└── types/          # shared TypeScript interfaces
```

## Pages

- **Dashboard** — KPI metrics, signal distribution donut, industry bars, 14-day
  signal trend, latest signals & news feeds
- **Signals** — searchable/filterable signal cards (type, source, sentiment)
  with confidence bars and pagination
- **Stock Analysis** — quote header, AI recommendation, price chart with
  SMA 20/50/200, volume, fundamentals grid, AI investment report, peer snapshot
- **Competitors** — industry ranking, quality radar, ROE/growth comparisons,
  peer table
- **Portfolio** — value/P&L/return/Sharpe metrics, allocation & sector charts,
  growth curve, holdings table
- **AI Assistant** — chat UI with typing indicator, markdown rendering, source
  chips (wire to the RAG backend via `POST /api/chat`)
- **Settings** — theme, notification and API configuration

## Notes

- Vite is pinned to v7 (Rollup): the rolldown bundler in Vite 8.0.x emits
  self-referencing CJS interop vars for recharts' `es-toolkit` dependency,
  which crashes the competitor radar chart in production builds.
