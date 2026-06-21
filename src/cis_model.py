import pandas as pd
import numpy as np

from src import config


def compute_severity_component(clean_df, atomic_df):
    id_to_cell = clean_df.set_index("id")["h3_cell"]
    merged = atomic_df.copy()
    merged["h3_cell"] = merged["id"].map(id_to_cell)
    merged["severity_weight"] = merged["offence_code"].map(config.OFFENCE_SEVERITY_WEIGHTS)
    merged["severity_weight"] = merged["severity_weight"].fillna(config.DEFAULT_SEVERITY_WEIGHT)
    merged["weighted_severity"] = merged["severity_weight"] * merged["validation_weight"]
    grouped = merged.groupby("h3_cell").agg(
        severity_sum=("weighted_severity", "sum"),
        severity_weight_sum=("validation_weight", "sum"),
    )
    grouped["severity_sum"] = grouped["severity_sum"].astype(float)
    grouped["severity_weight_sum"] = grouped["severity_weight_sum"].astype(float)
    grouped["severity_component"] = grouped["severity_sum"] / grouped["severity_weight_sum"]
    return grouped["severity_component"]


def compute_footprint_component(clean_df):
    df = clean_df.copy()
    df["pcu_weight"] = df["resolved_vehicle_type"].map(config.VEHICLE_PCU_WEIGHTS)
    df["pcu_weight"] = df["pcu_weight"].fillna(config.DEFAULT_PCU_WEIGHT)
    df["weighted_pcu"] = df["pcu_weight"] * df["validation_weight"]
    grouped = df.groupby("h3_cell").agg(
        pcu_sum=("weighted_pcu", "sum"),
        pcu_weight_sum=("validation_weight", "sum"),
    )
    grouped["pcu_sum"] = grouped["pcu_sum"].astype(float)
    grouped["pcu_weight_sum"] = grouped["pcu_weight_sum"].astype(float)
    grouped["footprint_component"] = grouped["pcu_sum"] / grouped["pcu_weight_sum"]
    return grouped["footprint_component"]


def percentile_rank(series):
    return series.rank(pct=True, method="average") * 100


def clip_series(series, lower, upper):
    return series.astype(float).clip(lower=lower, upper=upper)


def build_observed_impact_proxy(cell_stats, severity_component, footprint_component):
    proxy = pd.DataFrame(index=cell_stats.index)
    proxy["density_raw"] = cell_stats["violations_per_device"].astype(float)
    proxy["severity_raw"] = severity_component.astype(float)
    proxy["footprint_raw"] = footprint_component.astype(float)
    proxy["junction_raw"] = cell_stats["junction_share"].astype(float)
    proxy["road_context_raw"] = cell_stats["mean_road_context_weight"].astype(float)
    proxy["sensitive_raw"] = cell_stats["mean_sensitive_landmark_weight"].astype(float)
    proxy["shift_risk_raw"] = (
        cell_stats["night_share"].astype(float) * cell_stats["mean_shift_friction_weight"].astype(float)
    )
    proxy["observed_congestion_proxy"] = (
        proxy["density_raw"]
        * proxy["severity_raw"]
        * proxy["footprint_raw"]
        * proxy["road_context_raw"]
        * (1.0 + proxy["junction_raw"])
        * proxy["sensitive_raw"]
        * (1.0 + proxy["shift_risk_raw"])
    )
    return proxy["observed_congestion_proxy"]


def build_cis_table(cell_stats, clean_df, atomic_df):
    cell_stats = cell_stats.set_index("h3_cell")

    severity_component = compute_severity_component(clean_df, atomic_df)
    footprint_component = compute_footprint_component(clean_df)

    raw_count = cell_stats["raw_violation_count"].astype(float)
    repeat_count = cell_stats["repeat_vehicle_violations"].astype(float)
    chronicity_component = repeat_count / raw_count

    components = pd.DataFrame(index=cell_stats.index)
    components["density_raw"] = cell_stats["violations_per_device"].astype(float)
    components["severity_raw"] = severity_component
    components["footprint_raw"] = footprint_component
    components["junction_raw"] = cell_stats["junction_share"].astype(float)
    components["chronicity_raw"] = chronicity_component
    components["road_context_raw"] = cell_stats["mean_road_context_weight"].astype(float)
    components["sensitive_raw"] = cell_stats["mean_sensitive_landmark_weight"].astype(float)
    components["shift_risk_raw"] = (
        cell_stats["night_share"].astype(float) * cell_stats["mean_shift_friction_weight"].astype(float)
    )

    fill_values = components.mean(numeric_only=True, skipna=True)
    components = components.fillna(fill_values)

    components["estimated_capacity_loss_pct"] = clip_series(
        (
            components["footprint_raw"]
            * components["road_context_raw"]
            * components["sensitive_raw"]
            * (components["severity_raw"] / 6.0)
            * (1.0 + components["junction_raw"])
            * (1.0 + components["shift_risk_raw"] * 0.5)
            * 11.0
        ),
        5.0,
        95.0,
    )

    components["density_pct"] = percentile_rank(components["density_raw"])
    components["severity_pct"] = percentile_rank(components["severity_raw"])
    components["footprint_pct"] = percentile_rank(components["footprint_raw"])
    components["junction_pct"] = percentile_rank(components["junction_raw"])
    components["chronicity_pct"] = percentile_rank(components["chronicity_raw"])
    components["road_context_pct"] = percentile_rank(components["road_context_raw"] * components["sensitive_raw"])
    components["shift_risk_pct"] = percentile_rank(components["shift_risk_raw"])
    components["capacity_loss_pct_rank"] = percentile_rank(components["estimated_capacity_loss_pct"])

    components["density_points"] = components["density_pct"] * config.ENGINEERING_CIS_WEIGHTS["density"]
    components["severity_points"] = components["severity_pct"] * config.ENGINEERING_CIS_WEIGHTS["severity"]
    components["footprint_points"] = (
        (components["footprint_pct"] * 0.5 + components["capacity_loss_pct_rank"] * 0.5)
        * config.ENGINEERING_CIS_WEIGHTS["footprint"]
    )
    components["junction_points"] = components["junction_pct"] * config.ENGINEERING_CIS_WEIGHTS["junction"]
    components["chronicity_points"] = components["chronicity_pct"] * config.ENGINEERING_CIS_WEIGHTS["chronicity"]
    components["road_context_points"] = components["road_context_pct"] * config.ENGINEERING_CIS_WEIGHTS["road_context"]
    components["shift_risk_points"] = components["shift_risk_pct"] * config.ENGINEERING_CIS_WEIGHTS["shift_risk"]

    components["cis"] = (
        components["density_points"]
        + components["severity_points"]
        + components["footprint_points"]
        + components["junction_points"]
        + components["chronicity_points"]
        + components["road_context_points"]
        + components["shift_risk_points"]
    )

    components["observed_congestion_proxy"] = build_observed_impact_proxy(
        cell_stats, severity_component, footprint_component
    )

    result = cell_stats.join(components)
    result = result.reset_index()
    return result


def attach_location_labels(cis_table, clean_df):
    mode_station = clean_df.groupby("h3_cell")["police_station"].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else None
    )
    mode_junction = clean_df.groupby("h3_cell")["junction_name"].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else None
    )
    cis_table = cis_table.set_index("h3_cell")
    cis_table["dominant_police_station"] = mode_station
    cis_table["dominant_junction_name"] = mode_junction
    cis_table = cis_table.reset_index()
    return cis_table


def run_face_validity_check(cis_table):
    junction_cells = cis_table[cis_table["junction_share"] >= 0.5]
    midblock_cells = cis_table[cis_table["junction_share"] < 0.5]
    return {
        "junction_mean_cis": float(junction_cells["cis"].mean()) if len(junction_cells) else None,
        "midblock_mean_cis": float(midblock_cells["cis"].mean()) if len(midblock_cells) else None,
        "junction_cell_count": int(len(junction_cells)),
        "midblock_cell_count": int(len(midblock_cells)),
    }
