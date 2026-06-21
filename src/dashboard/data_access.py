import pandas as pd
import streamlit as st

from src import config


@st.cache_data
def load_priority_scores_with_vehicle_type():
    priority_df = pd.read_parquet(config.PRIORITY_SCORES_PATH)
    clean_df = pd.read_parquet(config.CLEAN_RECORDS_PATH)
    mode_vehicle = clean_df.groupby("h3_cell")["resolved_vehicle_type"].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else None
    )
    priority_df = priority_df.set_index("h3_cell")
    priority_df["dominant_vehicle_type"] = mode_vehicle
    priority_df = priority_df.reset_index()
    return priority_df


@st.cache_data
def load_shift_ranking(window):
    return pd.read_csv(config.SHIFT_RANKING_CSV_PATHS[window])