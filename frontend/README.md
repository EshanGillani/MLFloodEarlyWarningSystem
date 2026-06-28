# Frontend — Karachi Flood Early Warning System

Optional Next.js (App Router) dashboard that visualizes predictions from the FastAPI
backend in [`../backend`](../backend).

> Most users don't need this. To just get flood predictions, run the standalone Python
> script in [`../src/package`](../src/package) — see the root [README](../README.md).

## Run the dashboard

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL if backend isn't on http://localhost:8000
npm run dev
```

Open http://localhost:3000.

| Variable              | Default                 | Description                          |
| --------------------- | ----------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the backend API (build-time). |
