# ClaimSphere Copilot — Frontend

React + TypeScript + Fluent UI v9 dashboard for the ClaimSphere Copilot claims
processing platform. Dark-first, glassmorphic, Microsoft-accented.

## Stack

- **React 18 + TypeScript + Vite**
- **Fluent UI v9** (`@fluentui/react-components`, `@fluentui/react-icons`) — base components + custom dark theme
- **Framer Motion** — entrance / hover animations
- **Recharts** — area, donut, and bar charts
- **TanStack Table** — sortable claims table
- **TanStack Query** — data fetching, caching, polling
- **Zustand** — lightweight global state (backend/online, data source, selection)
- **Axios** — typed API client
- **React Router** — page routing

## Getting started

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api/*` to the FastAPI backend. Start the backend first:

```bash
# from repo root
uvicorn backend.main:app --reload --port 8000
```

Then visit http://localhost:5173.

## Data behavior

The dashboard calls the real backend (`GET /claims/`, `GET /health`). Because the
backend keeps claims in memory and starts empty, the UI falls back to a
deterministic **50-claim synthetic dataset** when the backend is unreachable or
returns no claims. The sidebar + top bar show whether data is **Live** or **Demo**.

Set `VITE_FORCE_DEMO=true` (see `.env.example`) to always use synthetic data.
Point `VITE_BACKEND_ORIGIN` at a deployed API for production builds.

## Structure

```
src/
  api/         Typed client, types mirroring backend models, synthetic data
  components/
    common/    GlassCard, StatusBadge, SectionHeader, Skeleton, FraudMeter
    layout/    Sidebar, TopBar, AppLayout, nav config
    dashboard/ KPI cards, charts (Recharts), claims table (TanStack)
  hooks/       useClaimsData, useBackendHealth (TanStack Query)
  pages/       Dashboard (complete), placeholders for the other 5 views
  store/       Zustand app store
  theme/       Design tokens + Fluent dark theme
  styles/      Global CSS (glass, gradients, skeleton/pulse animations)
  utils/       Formatting helpers
```

## Status

- **Dashboard** — complete, wired to the live backend with synthetic fallback.
- **Intake, Claims, Claim Detail, Agent Monitor, Policy Search, Review Queue** —
  scaffolded with polished placeholders describing the planned build.
