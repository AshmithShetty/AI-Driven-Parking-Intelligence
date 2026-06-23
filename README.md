# AI Driven Parking Intelligence powered by Bengaluru Traffic Police violation data, scored and prioritized for targeted enforcement.

## Theme

Poor Visibility on Parking-Induced Congestion


A Streamlit application for Bengaluru parking enforcement intelligence. It converts historical violation records into H3-cell hotspot rankings, congestion impact estimates, enforcement gap scores, shift-wise patrol priorities, anomaly flags, and a patrol route view.

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

1. Create and activate a virtual environment `python -m venv venv` and `.\venv\Scripts\Activate`. 
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

## Tab Descriptions

1. **Hotspot Map**
   Renders a geospatial map view of ranked parking enforcement hotspots with multiple functional layers.
   - **Map Layers Available**:
     - *Violation Density (Historical)*: An interactive H3 hex-cell map colored by priority score based on 2023-24 data.
     - *Live Traffic*: Real-time traffic map via Mappls API, pinning the highest priority cells for current context.
     - *Decision Support View*: A side-by-side comparison of historical density and live traffic.
   - **Key Metrics Displayed**: Counts of P0 (Critical) cells, high capacity-loss cells, and emerging hotspots, alongside a tabular list of top action candidates.

2. **Hotspot Detail**
   Provides a comprehensive drill-down for a specifically selected hotspot (chosen by tier, station, and cell ID).
   - **Core Metrics**: Congestion Impact Score (CIS), Enforcement Gap Score (EGS), Priority Tier, and Estimated Capacity Loss.
   - **Factor Breakdown**: Visual progress bars showing the exact point contribution of Density, Severity, Footprint, Junction Proximity, Chronicity, Road Context, and Shift Risk.
   - **Targeted Impact Estimate**: Calculates a counterfactual percentage drop in CIS if the hotspot were fully cleared.
   - **Shift Distribution**: A bar chart and data table breaking down historical violation activity across four daily shift windows.

3. **Priority Ranking**
   Displays an interactive, filtered tabular view of all hotspots sorted by overall operational priority.
   - **Interactive Filters**: Filter by priority tier, police station, dominant vehicle type, specific shift relevance, and minimum score threshold.
   - **Data Displayed**: Includes cell ID, priority tier, CIS, EGS, capacity loss, location details, vehicle type, and shift breakdown percentages.
   - **Export Capability**: Allows users to download the filtered current ranking directly as a CSV for offline use.

4. **Model Validation**
   Proves the reliability and robustness of the underlying rule-based scoring model.
   - **Temporal Stability Test**: Displays a consistency score (Spearman rank correlation) and a scatter plot comparing hotspot severity between two halves of the dataset to prove the pattern isn't random noise.
   - **Forward Monthly Backtest**: Shows how accurately past data predicted future hotspots, displaying prediction accuracy metrics and the hit rate for the top worst areas.

5. **Patrol Route Planner**
   Generates an actionable driving itinerary targeting the highest priority hotspots for a specific shift and station.
   - **User Inputs**: Select the target police station, the specific patrol shift window, and the maximum number of stops to make.
   - **Optimization**: Integrates a local algorithm to determine the most efficient stop order (minimizing travel distance).
   - **Route Visualization**: Outputs estimated driving distance and time, and optionally renders the turn-by-turn route on an interactive Mappls map.

## Notes

- The patrol route is stop-order optimized locally before Mappls draws the route.
- If Mappls browser-side routing is unavailable, the app falls back to a straight-line route in optimized stop order.
- The model uses only the provided dataset and derived features from it.
