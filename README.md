# ClimaTwin-IN

Hackathon MVP for an AI-powered climate digital twin of India. The initial pilot is configurable and defaults to Madhya Pradesh.

## Phase 1 status

Phase 1 provides the Python project scaffold and a minimal Flask service. Phase 2 adds safe, inactive MOSDAC/IMD adapter boundaries and local-file discovery. No external request is made by the application, and no weather observations, predictions, or climate claims are included yet.

## Windows PowerShell setup

```powershell
cd "D:\0815(1)\23\ClimaTwin-IN"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m backend.app
```

## Frontend development server (port 3000)

Run the Flask API on port 5000, then in a second VS Code terminal run:

```powershell
npm install
npm run dev
```

Open `http://127.0.0.1:3000/`. Vite serves the `frontend/` directory and
proxies `/api/*` to the Flask backend at `http://127.0.0.1:5000`, so the
dashboard can be developed directly with hot reload while keeping the
existing backend and SQLite services unchanged.

Open `http://127.0.0.1:5000/api/health` for the application check, and `http://127.0.0.1:5000/api/data/status` for source readiness. The starter configuration uses `DATA_MODE=LOCAL`.

To run the Phase 1 test:

```powershell
python -m pytest
```

## Configuration

Copy `.env.example` to `.env`, then set the pilot state, data mode, host, and port there. Keep credentials out of Git; MOSDAC and IMD values are deliberately empty placeholders for future official integrations.

## Local data (Phase 2)

Put real, developer-provided CSV, JSON, or GeoJSON files under `data/raw/mosdac/` or `data/raw/imd/`. The current local loader only discovers and reads these files; cleaning, validation, and normalization begin in Phase 3. It never generates weather observations.

## Local processing (Phase 3)

Place a real local dataset below `data/raw/` and run this in Windows PowerShell:

```powershell
python scripts/process_data.py --file data/raw/local/climate.csv --source LOCAL
```

The pipeline maps known headers, records unsafe/unknown mappings, validates and cleans explicit invalidities, normalizes timestamps, preserves unit uncertainty, and writes a processed CSV to `data/processed/` plus an audit report in `data/reports/`. It only accepts files below the configured raw-data directory and does not call MOSDAC or IMD.

## SQLite storage (Phase 4)

Initialize the idempotent local database, then import a Phase 3 CSV:

```powershell
python scripts/init_database.py
python scripts/import_processed_data.py --file data/processed/processed_climate_<timestamp>.csv
```

Stored records are always labelled `observed`. Read-only APIs are `/api/database/status`, `/api/locations`, `/api/observations/latest`, and `/api/observations/history?location_id=<id>&limit=100`. The predictions and scenario tables are schema preparation only; this phase creates no AI output.

## Interactive map and history (Phase 5)

Start Flask with `python -m backend.app`, then open `http://127.0.0.1:5000/`. The dashboard uses the Flask APIs only, Leaflet/OpenStreetMap for observed point locations, and Chart.js for history. `/api/map-data` returns observed GeoJSON; sparse observations are not interpolated into a synthetic surface.

## Random Forest climate AI (Phase 6)

Inspect and train from the actual SQLite observations:

```powershell
python scripts/inspect_training_data.py
python scripts/train_models.py
python scripts/evaluate_models.py
```

Training is chronological and uses shifted/lagged features to prevent future leakage. Temperature and rainfall models are trained separately only when the real data passes the sufficiency check. Metrics are written to `reports/ml/`, models to `models/<target>/`, and prediction requests use `POST /api/predict`. With insufficient data, the system returns `INSUFFICIENT TRAINING DATA` and leaves the model unavailable; it never fabricates rows, metrics, or confidence values.

## What-If scenarios (Phase 9)

Run the experimental scenario lab through `POST /api/scenarios/run` with a `location_id` and supported changes: `temperature_delta` (-5 to +5 °C), `rainfall_change_percent` (-50 to +50%), and `humidity_delta` (-30 to +30 percentage points). These are software/UX bounds, not scientific climate limits. Outputs are stored separately in `scenario_runs`, labelled `experimental_scenario`, and never overwrite observed data.

## Final integrated dashboard (Phase 10)

The single dashboard at `http://127.0.0.1:5000/` combines observed climate, map/history, AI model status, Digital Twin state, What-If Climate Lab, and system status. Aggregated APIs are `/api/dashboard/<location_id>` and `/api/system/status`. LOCAL mode is always shown as local/historical data; MOSDAC and IMD remain `NOT_CONFIGURED` until official adapters are configured.

## API integration slots (Phase 11)

MOSDAC and IMD are deliberately disabled. `.env.example` contains empty
placeholders for each provider's future URL, credentials, and dataset ID;
`.env` is ignored by Git and must never contain committed secrets. With the
default `DATA_MODE=LOCAL`, the application reads only developer-provided local
files and continues through processing, SQLite, prediction, digital-twin, and
scenario layers without making external requests. `/api/data/status` and
`/api/system/status` report both providers as `NOT_CONFIGURED` (or
`CONFIGURED_NOT_ACTIVATED` if all placeholders are filled, while requests
remain disabled). Future integration is isolated to the provider adapters:
official authentication, request construction, dataset selection, response
mapping, and error handling can be added there without rewriting the existing
DataManager or downstream phases.
