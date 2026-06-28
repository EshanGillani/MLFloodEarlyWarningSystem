# Karachi Flood Early Warning System

**Live Flood-Risk Prediction Using Machine Learning and the Open-Meteo API**
*A project developed for the Youth Innovation Challenge: Code for Climate at the IPN Summit (Houston, 2025).*

Predicts **live flood-risk levels** in Karachi using a trained **Random Forest** model. It analyzes
atmospheric pressure, precipitation, relative humidity, and short-term pressure trends from hourly
[Open-Meteo](https://open-meteo.com/) weather data plus historical Karachi flooding data, and classifies risk into:

- 🟢 **NORMAL**
- 🟡 **FLOOD WATCH**
- 🔴 **EMERGENCY WARNING**

## Live demo

A hosted instance is available: https://ml-flood-early-warning-system.vercel.app/

> ⚠️ The hosted demo depends on a backend deployed on Railway. If the cards show as
> permanent loading placeholders, the **hosted backend is down** — the code itself is fine.
> Run it locally with the steps below (it works out of the box) or deploy your own backend.

When the demo is up, **don't toggle Demo Mode** if you want live data — it auto-refreshes every ~15s.

---

## Repository layout

```
MLFloodEarlyWarningSystem/
├── backend/        FastAPI service — model training, Open-Meteo ingestion, prediction API
├── frontend/       Next.js dashboard (App Router) that consumes the backend API
├── src/package/    Standalone Python package version of the model
├── pyproject.toml  Packaging for the standalone src/ package
└── README.md
```

The two pieces you run are **`backend/`** (the API) and **`frontend/`** (the dashboard).

---

## Prerequisites

- **Python 3.11** (see `backend/runtime.txt`)
- **Node.js 18+** and npm (Next.js 16)
- *(Optional)* a **PostgreSQL** database for persistent history — not required to run

---

## Quick start (local)

The frontend defaults to `http://localhost:8000` and the backend defaults to that same port,
so the two connect with **no configuration**. Open two terminals:

### 1. Backend (terminal 1)

```bash
cd backend
python -m venv .venv

# Activate the virtualenv:
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS/Linux:           source .venv/bin/activate

pip install -r requirements.txt

# (optional) copy the env template if you want to override defaults / add a DB
cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

The API is now at **http://localhost:8000**. Quick checks:

- Health: http://localhost:8000/health
- Interactive docs: http://localhost:8000/docs
- A live prediction: http://localhost:8000/api/predict

On first start with no database, it trains the model from the bundled legacy data
and runs entirely in memory — that's expected.

### 2. Frontend (terminal 2)

```bash
cd frontend
npm install

# Optional — only needed if your backend is NOT on http://localhost:8000
cp .env.example .env.local

npm run dev
```

Open **http://localhost:3000**. The dashboard will populate from your local backend.

---

## Configuration

### Frontend — `frontend/.env.local`

| Variable              | Default                 | Description                                                                 |
| --------------------- | ----------------------- | --------------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the backend API. **Must be set at build time** (see Vercel note). |

### Backend — `backend/.env`

Every value has a default in `app/config.py`, so a `.env` file is optional. Most relevant:

| Variable       | Default                | Description                                                                       |
| -------------- | ---------------------- | --------------------------------------------------------------------------------- |
| `DATABASE_URL` | *(empty)*              | PostgreSQL DSN for persistent history. Empty = in-memory, no persistence.          |
| `CORS_ORIGINS` | localhost + `*.vercel.app` | Origins allowed to call the API. Add your frontend origin if it differs.        |
| `LATITUDE` / `LONGITUDE` | Karachi          | Target location for predictions.                                                  |

See `backend/.env.example` for the full list. The Open-Meteo API requires **no key**.

---

## Deployment

The hosted demo uses **Railway (backend) + Vercel (frontend)**, but any host works.

### Backend (Railway / Render / Docker)

`backend/` ships with `Dockerfile`, `Procfile`, `nixpacks.toml`, and `render.yaml`.

1. Create a service from the `backend/` directory.
2. *(Optional)* add a PostgreSQL plugin and set `DATABASE_URL` for persistent history.
3. Start command (if not auto-detected):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Verify `https://<your-backend>/health` returns `{"status": "ok"}`.

### Frontend (Vercel)

1. Import the repo and set the **Root Directory** to `frontend`.
2. Add an environment variable **`NEXT_PUBLIC_API_URL`** = your deployed backend URL
   (e.g. `https://your-backend.up.railway.app`).
3. Deploy. If you change the variable later, **redeploy** — `NEXT_PUBLIC_*` values are
   baked in at build time, not read at runtime.

> If the deployed dashboard hangs on loading skeletons, it almost always means
> `NEXT_PUBLIC_API_URL` is wrong/unset or the backend is unreachable. Confirm the
> backend `/health` endpoint responds and that CORS allows your Vercel origin.

---

## Standalone Python package

`src/package/` contains a self-contained version of the model (no web server). It is packaged
via `pyproject.toml`:

```bash
pip install -e .
```

---

## How it works

1. Fetches **live hourly weather data** from Open-Meteo.
2. Extracts features: surface pressure, precipitation, relative humidity.
3. Computes a **pressure trend** from recent hours.
4. The Random Forest model classifies the current flood risk.
5. Returns the risk label (and the dashboard renders it with a map of the area).

## Contributing

Pull requests are welcome — improve model accuracy, add features (rainfall intensity, wind speed),
expand to other cities, or improve docs and tests.
