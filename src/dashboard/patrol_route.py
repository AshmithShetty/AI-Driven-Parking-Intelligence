import streamlit as st

from src import config
from src.dashboard import mappls_client
from src.dashboard import route_optimizer


def render_patrol_route(priority_df):
    st.subheader("Patrol Route Planner")
    
    with st.expander(":material/directions_car: Guide: How to use the Route Planner (Click to expand)"):
        st.markdown("""
        * **What it does**: It automatically plans the fastest driving route for a police patrol car to visit the worst illegal parking spots.
        * **How to use**: Select your police station, choose your patrol shift (e.g., 06-12 means 6 AM to 12 PM), and select how many stops you have time to make.
        * **Result**: You will get a map showing exactly where to drive, in what order, to have the maximum impact on reducing traffic jams.
        """)

    st.caption(
        "Select a police station and shift window to generate a suggested patrol order "
        "through the highest priority cells in that station's jurisdiction during that shift."
    )

    station_options = sorted(priority_df["dominant_police_station"].dropna().unique().tolist())
    station_choice = st.selectbox("Police station", station_options)
    shift_choice = st.selectbox("Shift window (Time of Day)", config.SHIFT_WINDOWS)
    n_stops = st.slider("Number of stops to make", 2, 8, 5)

    station_df = priority_df[priority_df["dominant_police_station"] == station_choice]

    share_col = f"share_{shift_choice}"
    shift_priority_col = f"shift_priority_{shift_choice}"

    ranked = station_df.sort_values(shift_priority_col, ascending=False).head(n_stops)

    if len(ranked) < 2:
        st.warning(
            f"Only {len(ranked)} priority cell found for {station_choice} in this shift "
            f"window, at least 2 are needed to plot a route."
        )
        return

    st.write(f"**Recommended Patrol Route** for {station_choice} during the {shift_choice} shift, ordered by priority:")
    st.dataframe(
        ranked[
            [
                "h3_cell",
                "dominant_junction_name",
                "priority_score",
                share_col,
            ]
        ],
        width="stretch",
    )

    api_key = mappls_client.get_mappls_api_key()
    if not api_key:
        st.info(
            "Mappls route optimization is not active. Set the MAPPLS_API_KEY environment "
            "variable with your Mappls static key to render the route on a map."
        )
        return

    waypoints = []
    for index, (_, row) in enumerate(ranked.iterrows(), start=1):
        junction_name = str(row.get("dominant_junction_name") or row.get("h3_cell") or f"Stop {index}")
        waypoints.append(
            {
                "lat": float(row["mean_latitude"]),
                "lon": float(row["mean_longitude"]),
                "label": f"{index}. {junction_name}",
            }
        )

    optimized_waypoints, distance_km, eta_minutes = route_optimizer.optimize_waypoint_order(waypoints)

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Estimated Driving Distance", f"{distance_km:.1f} km")
    metric_col2.metric("Estimated Driving Time", f"{eta_minutes:.0f} min")

    st.caption(
        "Stops are ordered to minimize driving distance. If live routing is unavailable, "
        "the map will show a straight-line path between the stops."
    )

    html = mappls_client.build_route_map_html(api_key, optimized_waypoints)
    st.iframe(html, height=620)
