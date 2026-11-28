# SmartFreight backend

FastAPI service for shipment delay-risk workflows. The assessment, what-if,
recommendation, history, tracking, and analytics handlers currently return mock
or rule-based data. With `USE_MOCK=true`, each handler loads its response from
`/contracts` and validates it with its Pydantic response model. OpenAPI
descriptions and `simulated` response fields identify mock behavior. The
prediction model and external signal services are not connected yet.

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

Set `GOOGLE_MAPS_SERVER_KEY` only in the local `backend/.env` when a backend
Google Maps integration is added. Do not expose the server key in frontend code.
`ALLOWED_ORIGINS` accepts comma-separated origins; `http://localhost:3000` is
always allowed. `USE_MOCK` defaults to `true`, and `CACHE_TTL_SECONDS` defaults
to `300`.

## Run

From the `backend` directory, start the development server with:

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
| POST | `/assess` | Mock shipment delay assessment |
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
If mock mode is disabled before live services are connected, these endpoints
return HTTP 501.
