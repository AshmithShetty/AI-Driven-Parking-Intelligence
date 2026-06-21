import streamlit as st

from src import config


def render_priority_table(priority_df):
    st.subheader("Priority Ranking")

    with st.expander(":material/view_column: Glossary: Table Columns Explained (Click to expand)"):
        st.markdown("""
        * **h3_cell**: The unique ID for the specific map area (hexagon).
        * **priority_tier**: **P0** (Critical) to **P3** (Low Priority).
        * **priority_score**: Overall score combining congestion and lack of enforcement (0-100).
        * **cis (Congestion Impact Score)**: Traffic slowdown caused by illegal parking here.
        * **egs (Enforcement Gap Score)**: How often people park illegally here without getting fined.
        * **estimated_capacity_loss_pct**: % of road blocked.
        * **is_emerging_hotspot**: 'True' means illegal parking is rapidly getting worse here.
        """)

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    tier_filter = row1_col1.multiselect("Tier", ["P0", "P1", "P2", "P3"], default=["P0", "P1"])
    station_options = sorted(priority_df["dominant_police_station"].dropna().unique().tolist())
    station_filter = row1_col2.multiselect("Police station", station_options)
    vehicle_options = sorted(priority_df["dominant_vehicle_type"].dropna().unique().tolist())
    vehicle_filter = row1_col3.multiselect("Dominant vehicle type", vehicle_options)

    row2_col1, row2_col2 = st.columns(2)
    shift_filter = row2_col1.selectbox("Sort by shift relevance", ["overall"] + config.SHIFT_WINDOWS)
    min_priority = row2_col2.slider("Minimum priority score", 0, 100, 0)

    filtered = priority_df.copy()
    if tier_filter:
        filtered = filtered[filtered["priority_tier"].isin(tier_filter)]
    if station_filter:
        filtered = filtered[filtered["dominant_police_station"].isin(station_filter)]
    if vehicle_filter:
        filtered = filtered[filtered["dominant_vehicle_type"].isin(vehicle_filter)]
    filtered = filtered[filtered["priority_score"] >= min_priority]

    if shift_filter == "overall":
        filtered = filtered.sort_values("priority_score", ascending=False)
    else:
        sort_col = f"shift_priority_{shift_filter}"
        filtered = filtered.sort_values(sort_col, ascending=False)

    display_cols = [
        "h3_cell",
        "priority_tier",
        "priority_score",
        "cis",
        "egs",
        "estimated_capacity_loss_pct",
        "dominant_police_station",
        "dominant_junction_name",
        "dominant_vehicle_type",
        "raw_violation_count",
        "share_00-06",
        "share_06-12",
        "share_12-18",
        "share_18-24",
        "is_emerging_hotspot",
    ]
    st.dataframe(filtered[display_cols], width="stretch", height=420)
    st.caption(f"{len(filtered)} cells match the current filters")

    csv_data = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered ranking as CSV",
        data=csv_data,
        file_name="priority_ranking_filtered.csv",
        mime="text/csv",
    )
