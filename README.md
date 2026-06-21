# Gridlock

Gridlock is a Streamlit prototype for Bengaluru parking enforcement intelligence. It converts historical violation records into H3-cell hotspot rankings, congestion impact estimates, enforcement gap scores, shift-wise patrol priorities, anomaly flags, and a patrol route view.

## What the app does

- Cleans and parses the provided violation dataset
- Corrects for enforcement-intensity bias with `violations_per_device`
- Builds an engineering-style Congestion Impact Score
- Produces enforcement gap and overall priority scores
- Generates shift-specific hotspot rankings
- Runs temporal stability and monthly forward backtests
- Shows historical hotspot maps, live traffic context, hotspot detail, validation, and patrol routing

## Project structure

- `app.py`: Streamlit entrypoint
- `src/pipeline.py`: phase 1 cleaning and feature build
- `src/pipeline_phase2.py`: congestion impact scoring
- `src/pipeline_phase3.py`: prioritization and anomaly detection
- `src/validation_engine.py`: temporal stability and forward backtest
- `src/dashboard/`: UI and patrol routing modules

## Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Place the provided dataset at `data/raw/violations.csv`.
4. Set `MAPPLS_API_KEY` if you want Mappls live traffic and browser-side route rendering.
5. Run `streamlit run app.py`.

## Data artifacts

The app auto-builds missing or stale derived artifacts on startup:

- cleaned records
- atomic violation table
- H3 cell statistics
- hotspot scores
- priority scores
- validation summaries

## Validation outputs

- `reports/phase1_data_quality_report.txt`
- `reports/phase2_hotspot_report.txt`
- `reports/phase3_priority_report.txt`
- `reports/validation_summary.txt`

## Notes

- The patrol route is stop-order optimized locally before Mappls draws the route.
- If Mappls browser-side routing is unavailable, the app falls back to a straight-line route in optimized stop order.
- The model uses only the provided dataset and derived features from it.
