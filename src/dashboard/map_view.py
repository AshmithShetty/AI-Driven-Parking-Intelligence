import pydeck as pdk
import streamlit as st

from src.dashboard import mappls_client


def compute_fill_color(priority_score):
    score = max(0.0, min(100.0, float(priority_score)))
    red = int(255 * (score / 100))
    green = int(255 * (1 - score / 100))
    return [red, green, 60, 180]


def render_historical_layer(priority_df):
    df = priority_df.copy()
    df["fill_color"] = df["priority_score"].apply(compute_fill_color)

    layer = pdk.Layer(
        "H3HexagonLayer",
        df,
        get_hexagon="h3_cell",
        get_fill_color="fill_color",
        get_line_color=[80, 80, 80],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        extruded=False,
    )
    view_state = pdk.ViewState(
        latitude=float(df["mean_latitude"].mean()),
        longitude=float(df["mean_longitude"].mean()),
        zoom=10,
        pitch=0,
    )
    tooltip = {
        "html": "<b>{dominant_police_station}</b><br/>priority {priority_score}<br/>tier {priority_tier}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None,
    )
    return deck


def render_live_traffic_layer(priority_df, top_n=20):
    api_key = mappls_client.get_mappls_api_key()
    center_lat = float(priority_df["mean_latitude"].mean())
    center_lon = float(priority_df["mean_longitude"].mean())

    if not api_key:
        st.info(
            "Mappls live traffic layer is not active. Set the MAPPLS_API_KEY environment "
            "variable with your Mappls static key to enable this layer."
        )
        return

    top_cells = priority_df.sort_values("priority_score", ascending=False).head(top_n)
    markers = [
        {
            "lat": float(row["mean_latitude"]),
            "lon": float(row["mean_longitude"]),
            "label": f"{row['dominant_police_station']} priority {row['priority_score']:.0f}",
        }
        for _, row in top_cells.iterrows()
    ]
    html = mappls_client.build_traffic_map_html(api_key, center_lat, center_lon, 11, markers)
    st.iframe(html, height=580)


def render_decision_support(priority_df):
    top_cells = priority_df.sort_values("priority_score", ascending=False).head(10).copy()

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("P0 cells", int((priority_df["priority_tier"] == "P0").sum()))
    metric_col2.metric(
        "High capacity-loss cells",
        int((priority_df["estimated_capacity_loss_pct"] >= 60).sum()),
    )
    metric_col3.metric(
        "Emerging hotspots",
        int(priority_df["is_emerging_hotspot"].fillna(False).astype(bool).sum()),
    )

    col1, col2 = st.columns([1.1, 0.9])
    with col1:
        st.caption(
            "Historical priority surface from the violation dataset. Use this to identify the "
            "cells that repeatedly create obstruction risk."
        )
        st.pydeck_chart(render_historical_layer(top_cells))
    with col2:
        st.caption(
            "Current Mappls live traffic with top predicted cells pinned for visual corroboration."
        )
        render_live_traffic_layer(top_cells, top_n=10)

    st.markdown("Top action candidates")
    st.dataframe(
        top_cells[
            [
                "h3_cell",
                "priority_tier",
                "priority_score",
                "estimated_capacity_loss_pct",
                "dominant_police_station",
                "dominant_junction_name",
                "share_18-24",
                "is_emerging_hotspot",
            ]
        ],
        width="stretch",
        height=260,
    )


def render_map_view(priority_df):
    st.subheader("Hotspot Map")
    
    with st.expander(":material/map: Guide: How to use this map (Click to expand)"):
        st.markdown("""
        * **Violation Density**: Shows areas with a high history of illegal parking. Red areas require the most attention.
        * **Live Traffic**: Shows current real-time traffic conditions.
        * **Decision Support View**: Puts historical data and live traffic side-by-side to help you decide where to send patrols right now.
        """)
        
    layer_choice = st.radio(
        "Map layer",
        [
            "Violation Density (2023-24, historical)",
            "Live Traffic (today, Mappls)",
            "Decision Support View",
        ],
        horizontal=True,
    )
    if layer_choice == "Violation Density (2023-24, historical)":
        st.caption("Source: BTP violation dataset, Nov 2023 to Apr 2024. Color scales with priority score, red is higher priority.")
        deck = render_historical_layer(priority_df)
        st.pydeck_chart(deck)
    elif layer_choice == "Live Traffic (today, Mappls)":
        st.caption("Source: Mappls live traffic API, reflects current conditions, not historical data.")
        render_live_traffic_layer(priority_df)
    else:
        st.caption(
            "This view pairs the historical hotspot surface with current live traffic so officers can "
            "sanity-check where persistent illegal parking risk overlaps today's pressure."
        )
        render_decision_support(priority_df)
