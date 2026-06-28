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
> Run the backend locally with the steps below or deploy your own.

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

This README covers running the **`backend/`** API. The `frontend/` dashboard is deployed
separately — use the [live demo](#live-demo) to view it.

---

## Prerequisites

- **Python 3.11** (see `backend/runtime.txt`)
- *(Optional)* a **PostgreSQL** database for persistent history — not required to run

---

## Quick start (local)

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

---

## Configuration

### Backend — `backend/.env`

Every value has a default in `app/config.py`, so a `.env` file is optional. Most relevant:

| Variable       | Default                | Description                                                                       |
| -------------- | ---------------------- | --------------------------------------------------------------------------------- |
| `DATABASE_URL` | *(empty)*              | PostgreSQL DSN for persistent history. Empty = in-memory, no persistence.          |
| `CORS_ORIGINS` | localhost + `*.vercel.app` | Origins allowed to call the API. Add your frontend origin if it differs.        |
| `LATITUDE` / `LONGITUDE` | Karachi          | Target location for predictions.                                                  |

See `backend/.env.example` for the full list. The Open-Meteo API requires **no key**.

---

## Deployment (backend)

The hosted demo runs the backend on **Railway**, but any host works.
`backend/` ships with `Dockerfile`, `Procfile`, `nixpacks.toml`, and `render.yaml`.

1. Create a service from the `backend/` directory.
2. *(Optional)* add a PostgreSQL plugin and set `DATABASE_URL` for persistent history.
3. Start command (if not auto-detected):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Verify `https://<your-backend>/health` returns `{"status": "ok"}`.
5. Make sure `CORS_ORIGINS` allows the origin that will call this API.

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
