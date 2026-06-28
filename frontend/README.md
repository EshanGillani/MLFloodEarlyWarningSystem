# Frontend — Karachi Flood Early Warning System

Next.js (App Router) dashboard that consumes the FastAPI backend in [`../backend`](../backend).

## Setup

See the **root [README](../README.md)** for full local-setup and deployment instructions.

Quick version:

```bash
npm install
cp .env.example .env.local   # optional — only if backend isn't on http://localhost:8000
npm run dev
```

Open http://localhost:3000.

### Environment

| Variable              | Default                 | Description                          |
| --------------------- | ----------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the backend API (build-time). |
