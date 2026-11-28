# SmartFreight backend

FastAPI service for shipment delay-risk workflows. With `USE_MOCK=true`,
`POST /assess` returns its contract example. With `USE_MOCK=false`, it uses the
Google Routes API with OSRM fallback, Open-Meteo route weather, and a clearly
marked deterministic model STUB that will be replaced by the XGBoost model.
What-if, recommendation, history, tracking, and analytics still use contract
fixtures in mock mode.

## Setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the virtual environment with
`.venv\\Scripts\\Activate.ps1`.

Environment variables are read from `backend/.env`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `USE_MOCK` | Use contract fixtures for `/assess` (`true`) or live route/weather services and the model STUB (`false`) | `true` |
| `GOOGLE_MAPS_SERVER_KEY` | Server key for Google Routes; route lookup falls back to public OSRM if absent or if Google fails | empty |
| `ALLOWED_ORIGINS` | Comma-separated browser origins; localhost:3000 is always allowed | `http://localhost:3000` |
| `CACHE_TTL_SECONDS` | Route and weather cache lifetime | `300` |

Keep the Google server key in the local `.env`; do not expose it in frontend
code. Open-Meteo does not require a key for this forecast request.

## Run

From the `backend` directory, set `USE_MOCK=true` in `.env` for fixture mode.
For real assessment mode, set `USE_MOCK=false` and configure
`GOOGLE_MAPS_SERVER_KEY` (OSRM remains the fallback). Restart the server after
changing settings. Then start the development server with:

```bash
uvicorn app.main:app --reload
```

The health check is at <http://127.0.0.1:8000/health> and interactive API docs
are at <http://127.0.0.1:8000/docs>. The OpenAPI document is at
<http://127.0.0.1:8000/openapi.json>.

Run tests from this directory with:

```bash
python -m pytest
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Process health check |
| POST | `/assess` | Mock fixture or real route/weather assessment with model STUB |
| POST | `/whatif` | Mock scenario analysis |
| POST | `/recommend` | Mock recommendations |
| GET | `/history` | Mock assessment history |
| GET | `/track/{id}` | Mock shipment tracking |
| GET | `/analytics/threshold` | Mock threshold metrics |
| GET | `/analytics/impact` | Mock impact estimates |
| GET | `/analytics/lanes` | Mock lane metrics |
| GET | `/analytics/shap` | Mock feature impacts |
| GET | `/analytics/calibration` | Mock calibration metrics |

Request and response examples live in the repository-level `contracts/` folder.
With mock mode disabled, the other fixture-backed endpoints return HTTP 501
until their live services are connected.
