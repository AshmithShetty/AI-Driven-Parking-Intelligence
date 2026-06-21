import os

import pandas as pd
from scipy.stats import spearmanr

from src import cis_model
from src import config
from src import data_loader
from src import feature_engineering


def prepare_atomic_subset(atomic_df, ids):
    return atomic_df[atomic_df["id"].isin(set(ids))].copy()


def compute_temporal_stability(clean_df, atomic_df):
    midpoint = clean_df["event_datetime"].quantile(0.5)

    first_half = clean_df[clean_df["event_datetime"] < midpoint].copy()
    second_half = clean_df[clean_df["event_datetime"] >= midpoint].copy()

    atomic_first = prepare_atomic_subset(atomic_df, first_half["id"])
    atomic_second = prepare_atomic_subset(atomic_df, second_half["id"])

    cell_stats_first = feature_engineering.compute_h3_cell_stats(first_half)
    cell_stats_second = feature_engineering.compute_h3_cell_stats(second_half)

    cis_first = cis_model.build_cis_table(cell_stats_first, first_half, atomic_first)
    cis_second = cis_model.build_cis_table(cell_stats_second, second_half, atomic_second)

    merged = cis_first[["h3_cell", "cis"]].merge(
        cis_second[["h3_cell", "cis"]], on="h3_cell", suffixes=("_first_half", "_second_half")
    )

    correlation, p_value = spearmanr(merged["cis_first_half"], merged["cis_second_half"])

    return {
        "correlation": float(correlation),
        "p_value": float(p_value),
        "cells_compared": int(len(merged)),
        "first_half_start": str(first_half["event_datetime"].min()),
        "first_half_end": str(first_half["event_datetime"].max()),
        "second_half_start": str(second_half["event_datetime"].min()),
        "second_half_end": str(second_half["event_datetime"].max()),
        "merged_table": merged,
    }


def compute_top_k_precision(predicted, observed, top_k):
    predicted_top = set(predicted.sort_values("cis", ascending=False).head(top_k)["h3_cell"])
    observed_top = set(
        observed.sort_values("observed_congestion_proxy", ascending=False).head(top_k)["h3_cell"]
    )
    if not predicted_top:
        return 0.0
    return len(predicted_top & observed_top) / len(predicted_top)


def run_monthly_backtest(clean_df, atomic_df):
    month_period = clean_df["event_datetime"].dt.tz_localize(None).dt.to_period("M")
    months = month_period.sort_values().drop_duplicates().tolist()
    rows = []

    for target_month in months[2:]:
        train_df = clean_df[month_period < target_month].copy()
        test_df = clean_df[month_period == target_month].copy()

        if train_df.empty or test_df.empty:
            continue

        atomic_train = prepare_atomic_subset(atomic_df, train_df["id"])
        atomic_test = prepare_atomic_subset(atomic_df, test_df["id"])

        train_cell_stats = feature_engineering.compute_h3_cell_stats(train_df)
        test_cell_stats = feature_engineering.compute_h3_cell_stats(test_df)

        predicted = cis_model.build_cis_table(train_cell_stats, train_df, atomic_train)
        observed = cis_model.build_cis_table(test_cell_stats, test_df, atomic_test)

        merged = predicted[["h3_cell", "cis"]].merge(
            observed[["h3_cell", "observed_congestion_proxy", "violations_per_device"]],
            on="h3_cell",
            how="inner",
        )
        merged = merged.dropna(subset=["cis", "observed_congestion_proxy", "violations_per_device"])

        if merged.empty:
            continue

        spearman_proxy, proxy_p = spearmanr(merged["cis"], merged["observed_congestion_proxy"])
        spearman_density, density_p = spearmanr(merged["cis"], merged["violations_per_device"])
        precision_at_k = compute_top_k_precision(predicted, observed, config.BACKTEST_TOP_K)

        rows.append(
            {
                "target_month": str(target_month),
                "train_start": str(train_df["event_datetime"].min()),
                "train_end": str(train_df["event_datetime"].max()),
                "test_start": str(test_df["event_datetime"].min()),
                "test_end": str(test_df["event_datetime"].max()),
                "cells_compared": int(len(merged)),
                "spearman_future_proxy": float(spearman_proxy),
                "spearman_future_proxy_p_value": float(proxy_p),
                "spearman_future_density": float(spearman_density),
                "spearman_future_density_p_value": float(density_p),
                "precision_at_k": float(precision_at_k),
            }
        )

    return pd.DataFrame(rows)


def write_validation_summary(stability_result, backtest_df):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    lines = []
    lines.append("VALIDATION SUMMARY")
    lines.append("")
    lines.append("temporal stability")
    lines.append(f"  spearman: {stability_result['correlation']:.3f}")
    lines.append(f"  p_value: {stability_result['p_value']:.6f}")
    lines.append(f"  cells_compared: {stability_result['cells_compared']}")
    lines.append("")
    lines.append("monthly forward backtest")
    if backtest_df.empty:
        lines.append("  no backtest rows generated")
    else:
        lines.append(
            f"  mean future proxy spearman: {backtest_df['spearman_future_proxy'].mean():.3f}"
        )
        lines.append(
            f"  mean future density spearman: {backtest_df['spearman_future_density'].mean():.3f}"
        )
        lines.append(f"  mean precision@{config.BACKTEST_TOP_K}: {backtest_df['precision_at_k'].mean():.3f}")
        lines.append("")
        for _, row in backtest_df.iterrows():
            lines.append(
                f"  {row['target_month']} | cells {row['cells_compared']} | "
                f"proxy_spearman {row['spearman_future_proxy']:.3f} | "
                f"density_spearman {row['spearman_future_density']:.3f} | "
                f"precision@{config.BACKTEST_TOP_K} {row['precision_at_k']:.3f}"
            )

    with open(config.VALIDATION_SUMMARY_PATH, "w") as handle:
        handle.write("\n".join(lines))


def run_validation_pipeline():
    clean_df = data_loader.load_parquet(config.CLEAN_RECORDS_PATH)
    atomic_df = data_loader.load_parquet(config.ATOMIC_VIOLATIONS_PATH)
    stability_result = compute_temporal_stability(clean_df, atomic_df)
    backtest_df = run_monthly_backtest(clean_df, atomic_df)
    if not backtest_df.empty:
        data_loader.save_parquet(backtest_df, config.VALIDATION_BACKTEST_PATH)
    write_validation_summary(stability_result, backtest_df)
    return stability_result, backtest_df
