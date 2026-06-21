import streamlit as st


def compute_impact_if_cleared(row):
    base_without_density = (
        row["severity_points"]
        + row["footprint_points"]
        + row["junction_points"]
        + row["chronicity_points"]
        + row["road_context_points"]
        + row["shift_risk_points"]
    )
    if row["cis"] <= 0:
        return 0.0
    drop_pct = (row["cis"] - base_without_density) / row["cis"] * 100
    return max(0.0, drop_pct)


def render_factor_bar(label, points, max_points):
    fraction = 0.0 if max_points == 0 else min(1.0, points / max_points)
    st.write(label)
    st.progress(fraction)
    st.caption(f"{points:.1f} points")


def render_hotspot_detail(priority_df):
    st.subheader("Hotspot Detail")

    sorted_df = priority_df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    options = [
        f"{row['priority_tier']} | {row['dominant_police_station']} | {row['h3_cell']}"
        for _, row in sorted_df.iterrows()
    ]
    selected_label = st.selectbox("Select a hotspot", options)
    selected_index = options.index(selected_label)
    row = sorted_df.iloc[selected_index]

    with st.expander(":material/menu_book: Glossary: What do these terms mean? (Click to expand)"):
        st.markdown("""
        * **Congestion Impact Score (CIS)**: How much this illegal parking slows down traffic (0 to 100). Higher means worse traffic jams.
        * **Enforcement Gap Score (EGS)**: Measures how often violations happen here without any challan (fine) being issued.
        * **Priority Tier**: P0 is the most critical area requiring immediate patrol. P3 is the lowest priority.
        * **Estimated Capacity Loss**: The percentage of the road that is effectively blocked by illegally parked vehicles.
        * **Chronicity**: How often the *same* vehicles repeatedly park illegally in this exact spot.
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Congestion Impact Score", f"{row['cis']:.0f} / 100")
    col2.metric("Enforcement Gap Score", f"{row['egs']:.0f} / 100")
    col3.metric("Priority Tier", row["priority_tier"])
    st.metric("Estimated Capacity Loss", f"{row['estimated_capacity_loss_pct']:.0f}%")

    st.write(f"Station: {row['dominant_police_station']}")
    st.write(f"Junction: {row['dominant_junction_name']}")
    st.write(f"Raw violation count: {int(row['raw_violation_count'])}")
    st.write(f"Violations per device: {row['violations_per_device']:.1f}")

    st.markdown("Why this score, factor breakdown")
    max_points = max(
        row["density_points"],
        row["severity_points"],
        row["footprint_points"],
        row["junction_points"],
        row["chronicity_points"],
        row["road_context_points"],
        row["shift_risk_points"],
        1,
    )
    render_factor_bar("**Density** — True volume of parking violations, adjusted for patrol presence", row["density_points"], max_points)
    render_factor_bar("**Severity** — How dangerous or obstructive the specific parking offenses are here", row["severity_points"], max_points)
    render_factor_bar("**Vehicle Footprint** — How much physical road space the parked vehicles take up (e.g. buses vs bikes)", row["footprint_points"], max_points)
    render_factor_bar("**Junction Proximity** — Extra risk if the illegal parking happens near a busy intersection", row["junction_points"], max_points)
    render_factor_bar("**Chronicity** — How often the exact same vehicles repeatedly park illegally here", row["chronicity_points"], max_points)
    render_factor_bar("**Road Context** — Extra weight if this happens on a major highway or arterial road", row["road_context_points"], max_points)
    render_factor_bar("**Shift Risk** — Increased danger factor depending on poor visibility or time of day", row["shift_risk_points"], max_points)

    impact_pct = compute_impact_if_cleared(row)
    st.success(
        f"**Targeted Impact Estimate:** If illegal parking at this specific location is cleared, "
        f"the AI model estimates the congestion impact score would drop by an impressive **{impact_pct:.0f}%**! \n\n"
        f"*(Note: This is a counterfactual sensitivity estimate based on our formula, not a guarantee).* ",
        icon=":material/trending_down:"
    )

    if bool(row["is_emerging_hotspot"]):
        st.warning(
            "This cell is flagged as an emerging hotspot, recent weeks show violation activity "
            "rising faster than its own historical average."
        )

    st.markdown("Shift distribution")
    import pandas as pd
    
    shift_data = {
        "Shift Window": ["00-06 (Night)", "06-12 (Morning)", "12-18 (Afternoon)", "18-24 (Evening)"],
        "Percentage (%)": [
            round(row['share_00-06'] * 100),
            round(row['share_06-12'] * 100),
            round(row['share_12-18'] * 100),
            round(row['share_18-24'] * 100)
        ]
    }
    shift_df = pd.DataFrame(shift_data)
    
    chart_col, table_col = st.columns([2, 1])
    
    with chart_col:
        st.bar_chart(shift_df.set_index("Shift Window")["Percentage (%)"])
        
    with table_col:
        st.dataframe(shift_df, hide_index=True)
