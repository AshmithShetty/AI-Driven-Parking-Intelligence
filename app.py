import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

from src import bootstrap
from src.dashboard import data_access
from src.dashboard import map_view
from src.dashboard import hotspot_detail
from src.dashboard import priority_table
from src.dashboard import validation_view
from src.dashboard import patrol_route


st.set_page_config(page_title="Gridlock Parking Intelligence", layout="wide")

st.title("AI Driven Parking Intelligence")
st.caption(
    "Bengaluru Traffic Police violation data, Nov 2023 to Apr 2024, "
    "scored and prioritized for targeted enforcement."
)

with st.spinner("Preparing processed data and validation artifacts"):
    bootstrap_status = bootstrap.ensure_artifacts()

if bootstrap_status["rebuilt"]:
    st.info("Derived data artifacts were rebuilt for this session so the dashboard reflects the latest available raw dataset.")

priority_df = data_access.load_priority_scores_with_vehicle_type()

tab_map, tab_detail, tab_table, tab_validation, tab_route = st.tabs(
    ["Hotspot Map", "Hotspot Detail", "Priority Ranking", "Model Validation", "Patrol Route"]
)

with tab_map:
    map_view.render_map_view(priority_df)

with tab_detail:
    hotspot_detail.render_hotspot_detail(priority_df)

with tab_table:
    priority_table.render_priority_table(priority_df)

with tab_validation:
    validation_view.render_validation_view()

with tab_route:
    patrol_route.render_patrol_route(priority_df)
