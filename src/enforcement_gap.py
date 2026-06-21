import pandas as pd

from src import config


def compute_rejection_rate(clean_df):
    df = clean_df.copy()
    df["is_rejected"] = (df["validation_status"] == "rejected").astype(int)
    grouped = df.groupby("h3_cell").agg(
        rejected_count=("is_rejected", "sum"),
        total_count=("is_rejected", "count"),
    )
    grouped["rejected_count"] = grouped["rejected_count"].astype(float)
    grouped["total_count"] = grouped["total_count"].astype(float)
    grouped["rejection_rate"] = grouped["rejected_count"] / grouped["total_count"]
    return grouped["rejection_rate"]


def percentile_rank(series):
    return series.rank(pct=True, method="average") * 100


def build_egs_table(hotspot_scores, clean_df):
    rejection_rate = compute_rejection_rate(clean_df)
    table = hotspot_scores.set_index("h3_cell").copy()
    table["rejection_rate"] = rejection_rate

    fill_values = table[["unactioned_rate", "rejection_rate"]].mean(numeric_only=True, skipna=True)
    table[["unactioned_rate", "rejection_rate"]] = table[["unactioned_rate", "rejection_rate"]].fillna(fill_values)

    table["unactioned_pct"] = percentile_rank(table["unactioned_rate"])
    table["rejection_pct"] = percentile_rank(table["rejection_rate"])

    table["egs"] = (
        table["unactioned_pct"] * config.EGS_WEIGHTS["unactioned"]
        + table["rejection_pct"] * config.EGS_WEIGHTS["rejection"]
    )

    table = table.reset_index()
    return table