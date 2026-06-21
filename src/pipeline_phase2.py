import os

from src import config
from src import data_loader
from src import cis_model


def write_phase2_report(cis_table, validity_check):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    top = cis_table.sort_values("cis", ascending=False).head(15)

    lines = []
    lines.append("PHASE 2 CONGESTION IMPACT SCORING REPORT")
    lines.append("")
    lines.append("engineering scoring weights used:")
    for key, value in config.ENGINEERING_CIS_WEIGHTS.items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    lines.append("face validity check, junction cells vs mid block cells:")
    lines.append(f"  junction cell count: {validity_check['junction_cell_count']}")
    lines.append(f"  junction mean cis: {validity_check['junction_mean_cis']:.2f}")
    lines.append(f"  midblock cell count: {validity_check['midblock_cell_count']}")
    lines.append(f"  midblock mean cis: {validity_check['midblock_mean_cis']:.2f}")
    lines.append("")
    lines.append(f"total cells scored: {len(cis_table)}")
    lines.append(f"cells with null cis: {int(cis_table['cis'].isna().sum())}")
    lines.append(f"cis min: {cis_table['cis'].min():.2f}")
    lines.append(f"cis max: {cis_table['cis'].max():.2f}")
    lines.append("")
    lines.append("top 15 hotspots by congestion impact score:")
    lines.append("")
    for _, row in top.iterrows():
        lines.append(
            f"cell {row['h3_cell']} | cis {row['cis']:.1f} | station {row['dominant_police_station']} | "
            f"junction {row['dominant_junction_name']} | raw_violations {int(row['raw_violation_count'])} | "
            f"violations_per_device {row['violations_per_device']:.1f} | "
            f"estimated_capacity_loss {row['estimated_capacity_loss_pct']:.1f} percent"
        )
        lines.append(
            f"    breakdown -> density {row['density_points']:.1f}, severity {row['severity_points']:.1f}, "
            f"footprint {row['footprint_points']:.1f}, junction {row['junction_points']:.1f}, "
            f"chronicity {row['chronicity_points']:.1f}, road_context {row['road_context_points']:.1f}, "
            f"shift_risk {row['shift_risk_points']:.1f}"
        )

    with open(config.PHASE2_REPORT_PATH, "w") as f:
        f.write("\n".join(lines))


def main():
    clean_df = data_loader.load_parquet(config.CLEAN_RECORDS_PATH)
    atomic_df = data_loader.load_parquet(config.ATOMIC_VIOLATIONS_PATH)
    cell_stats = data_loader.load_parquet(config.H3_CELL_STATS_PATH)

    cis_table = cis_model.build_cis_table(cell_stats, clean_df, atomic_df)
    cis_table = cis_model.attach_location_labels(cis_table, clean_df)

    validity_check = cis_model.run_face_validity_check(cis_table)

    data_loader.save_parquet(cis_table, config.HOTSPOT_SCORES_PATH)
    cis_table.sort_values("cis", ascending=False).to_csv(config.HOTSPOT_RANKING_CSV_PATH, index=False)

    write_phase2_report(cis_table, validity_check)

    print("phase 2 complete")
    print(f"hotspot scores saved to {config.HOTSPOT_SCORES_PATH}")
    print(f"hotspot ranking csv saved to {config.HOTSPOT_RANKING_CSV_PATH}")
    print(f"report saved to {config.PHASE2_REPORT_PATH}")
    print(f"junction mean cis: {validity_check['junction_mean_cis']:.2f}")
    print(f"midblock mean cis: {validity_check['midblock_mean_cis']:.2f}")
    print(f"null cis count: {int(cis_table['cis'].isna().sum())}")


if __name__ == "__main__":
    main()
