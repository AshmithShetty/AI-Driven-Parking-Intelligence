import pandas as pd

from src import config


def assign_tier(priority_score, thresholds):
    if priority_score >= thresholds["p0"]:
        return "P0"
    if priority_score >= thresholds["p1"]:
        return "P1"
    if priority_score >= thresholds["p2"]:
        return "P2"
    return "P3"


def build_priority_table(egs_table):
    table = egs_table.copy()
    table["priority_score"] = (
        table["cis"] * config.PRIORITY_WEIGHTS["cis"]
        + table["egs"] * config.PRIORITY_WEIGHTS["egs"]
    )

    thresholds = {
        "p0": table["priority_score"].quantile(0.75),
        "p1": table["priority_score"].quantile(0.50),
        "p2": table["priority_score"].quantile(0.25),
    }
    table["priority_tier"] = table["priority_score"].apply(lambda x: assign_tier(x, thresholds))
    return table, thresholds


def compute_shift_share(clean_df):
    pivot = pd.crosstab(clean_df["h3_cell"], clean_df["shift_window"])
    for window in config.SHIFT_WINDOWS:
        if window not in pivot.columns:
            pivot[window] = 0
    pivot = pivot[config.SHIFT_WINDOWS]
    row_totals = pivot.sum(axis=1).astype(float)
    share = pivot.astype(float).div(row_totals.replace(0, pd.NA), axis=0)
    share = share.fillna(0)
    share.columns = [f"share_{c}" for c in share.columns]
    return share


def build_shift_rankings(priority_table, clean_df):
    share = compute_shift_share(clean_df)
    merged = priority_table.set_index("h3_cell").join(share)
    merged = merged.reset_index()

    rankings = {}
    for window in config.SHIFT_WINDOWS:
        share_col = f"share_{window}"
        merged[f"shift_priority_{window}"] = merged["priority_score"] * merged[share_col]
        ranked = merged.sort_values(f"shift_priority_{window}", ascending=False)
        rankings[window] = ranked[
            [
                "h3_cell",
                "dominant_police_station",
                "dominant_junction_name",
                "priority_score",
                "priority_tier",
                "estimated_capacity_loss_pct",
                share_col,
                f"shift_priority_{window}",
            ]
        ].head(20)
    return merged, rankings


def find_evening_gap_cells(merged):
    top_tier = merged[merged["priority_tier"].isin(["P0", "P1"])]
    gap_cells = top_tier[top_tier["share_18-24"] < config.EVENING_GAP_SHARE_THRESHOLD]
    gap_cells = gap_cells.sort_values("priority_score", ascending=False)
    return gap_cells
