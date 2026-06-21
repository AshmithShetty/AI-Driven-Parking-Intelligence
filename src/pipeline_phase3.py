import os

from src import config
from src import data_loader
from src import enforcement_gap
from src import priority_engine
from src import anomaly_detection


def write_phase3_report(merged, thresholds, gap_cells, anomaly_table):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    lines = []
    lines.append("PHASE 3 HOTSPOT DETECTION AND ENFORCEMENT PRIORITIZATION REPORT")
    lines.append("")
    lines.append("priority score weights:")
    for key, value in config.PRIORITY_WEIGHTS.items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    lines.append("enforcement gap score weights:")
    for key, value in config.EGS_WEIGHTS.items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    lines.append("priority tier thresholds (priority score):")
    lines.append(f"  P0 cutoff: {thresholds['p0']:.2f}")
    lines.append(f"  P1 cutoff: {thresholds['p1']:.2f}")
    lines.append(f"  P2 cutoff: {thresholds['p2']:.2f}")
    lines.append("")
    tier_counts = merged["priority_tier"].value_counts()
    lines.append("tier counts:")
    for tier in ["P0", "P1", "P2", "P3"]:
        lines.append(f"  {tier}: {int(tier_counts.get(tier, 0))}")
    lines.append("")

    top15 = merged.sort_values("priority_score", ascending=False).head(15)
    lines.append("top 15 cells by overall priority score:")
    lines.append("")
    for _, row in top15.iterrows():
        lines.append(
            f"cell {row['h3_cell']} | tier {row['priority_tier']} | priority {row['priority_score']:.1f} | "
            f"cis {row['cis']:.1f} | egs {row['egs']:.1f} | capacity_loss {row['estimated_capacity_loss_pct']:.1f} | "
            f"station {row['dominant_police_station']} | "
            f"junction {row['dominant_junction_name']}"
        )
        lines.append(
            f"    shift share -> 00-06 {row['share_00-06']:.2f}, 06-12 {row['share_06-12']:.2f}, "
            f"12-18 {row['share_12-18']:.2f}, 18-24 {row['share_18-24']:.2f}"
        )
    lines.append("")

    lines.append(
        f"evening coverage gap, P0 or P1 cells with under {config.EVENING_GAP_SHARE_THRESHOLD * 100:.0f} percent "
        f"of their violations falling in the 18-24 shift window:"
    )
    lines.append(f"  flagged cell count: {len(gap_cells)}")
    lines.append("")
    for _, row in gap_cells.head(15).iterrows():
        lines.append(
            f"cell {row['h3_cell']} | tier {row['priority_tier']} | priority {row['priority_score']:.1f} | "
            f"station {row['dominant_police_station']} | junction {row['dominant_junction_name']} | "
            f"18-24 share {row['share_18-24']:.3f}"
        )
    lines.append("")

    emerging = anomaly_table[anomaly_table["is_emerging_hotspot"]].sort_values("anomaly_score", ascending=False)
    lines.append(f"emerging hotspots flagged by anomaly detection: {len(emerging)}")
    lines.append("")
    merged_indexed = merged.set_index("h3_cell")
    for _, row in emerging.head(15).iterrows():
        cell_id = row["h3_cell"]
        station = merged_indexed.loc[cell_id, "dominant_police_station"] if cell_id in merged_indexed.index else None
        lines.append(
            f"cell {cell_id} | station {station} | anomaly_score {row['anomaly_score']:.3f} | "
            f"mean_weekly {row['mean_weekly']:.1f} | max_week_jump {row['max_week_jump']:.1f} | "
            f"recent_trend_ratio {row['recent_trend_ratio']:.2f}"
        )

    with open(config.PHASE3_REPORT_PATH, "w") as f:
        f.write("\n".join(lines))


def main():
    clean_df = data_loader.load_parquet(config.CLEAN_RECORDS_PATH)
    hotspot_scores = data_loader.load_parquet(config.HOTSPOT_SCORES_PATH)

    egs_table = enforcement_gap.build_egs_table(hotspot_scores, clean_df)
    priority_table, thresholds = priority_engine.build_priority_table(egs_table)
    merged, shift_rankings = priority_engine.build_shift_rankings(priority_table, clean_df)
    gap_cells = priority_engine.find_evening_gap_cells(merged)
    anomaly_table = anomaly_detection.run_anomaly_detection(clean_df)

    merged = merged.set_index("h3_cell").join(
        anomaly_table.set_index("h3_cell")[["anomaly_score", "is_unusual_pattern", "is_emerging_hotspot"]]
    ).reset_index()

    data_loader.save_parquet(merged, config.PRIORITY_SCORES_PATH)
    merged.sort_values("priority_score", ascending=False).to_csv(config.PRIORITY_RANKING_CSV_PATH, index=False)

    for window, ranked in shift_rankings.items():
        ranked.to_csv(config.SHIFT_RANKING_CSV_PATHS[window], index=False)

    write_phase3_report(merged, thresholds, gap_cells, anomaly_table)

    print("phase 3 complete")
    print(f"priority scores saved to {config.PRIORITY_SCORES_PATH}")
    print(f"priority ranking csv saved to {config.PRIORITY_RANKING_CSV_PATH}")
    for window, path in config.SHIFT_RANKING_CSV_PATHS.items():
        print(f"shift ranking {window} saved to {path}")
    print(f"report saved to {config.PHASE3_REPORT_PATH}")
    print(f"tier counts: {merged['priority_tier'].value_counts().to_dict()}")
    print(f"evening gap cells flagged: {len(gap_cells)}")
    print(f"emerging hotspots flagged: {int(merged['is_emerging_hotspot'].sum())}")


if __name__ == "__main__":
    main()
