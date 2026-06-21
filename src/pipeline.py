import os

from src import config
from src import data_loader
from src import cleaning
from src import feature_engineering
from src import confound_analysis


def write_report(notes, correlation, r_squared, cell_stats, shift_distribution):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    lines = []
    lines.append("PHASE 1 DATA QUALITY REPORT")
    lines.append("")
    lines.append(f"total rows loaded: {notes['row_count']}")
    lines.append(f"date range found (IST): {notes['date_min']} to {notes['date_max']}")
    lines.append(f"filename label says: {config.EXPECTED_DATE_RANGE_LABEL}, actual range differs from this label")
    lines.append("")
    lines.append(f"approved: {notes['approved_count']}")
    lines.append(f"rejected: {notes['rejected_count']}")
    lines.append(f"processing: {notes['processing_count']}")
    lines.append(f"created1: {notes['created1_count']}")
    lines.append(f"duplicate: {notes['duplicate_count']}")
    lines.append(f"unvalidated (nan): {notes['unvalidated_count']}")
    lines.append("")
    lines.append(f"junction violations: {notes['junction_violation_count']}")
    lines.append(f"mid block violations: {notes['midblock_violation_count']}")
    lines.append(f"vehicle type corrected rows: {notes['vehicle_type_corrected_count']}")
    lines.append("")
    lines.append("shift window distribution (IST):")
    for window, count in shift_distribution.items():
        lines.append(f"  {window}: {count}")
    lines.append("")
    lines.append(f"h3 cells generated: {len(cell_stats)}")
    lines.append(f"enforcement effort confound correlation r: {correlation:.4f}")
    lines.append(f"enforcement effort confound r squared: {r_squared:.4f}")
    lines.append("")
    lines.append("interpretation: high r squared means violation density is significantly")
    lines.append("explained by patrol device count rather than true illegal parking rate")
    lines.append("all downstream density features must use violations_per_device, not raw counts")

    with open(config.PHASE1_REPORT_PATH, "w") as f:
        f.write("\n".join(lines))


def main():
    raw_df = data_loader.load_raw_violations()
    clean_df, atomic_df, notes = cleaning.run_cleaning_pipeline(raw_df)
    clean_df, cell_stats, shift_distribution = feature_engineering.run_feature_pipeline(clean_df)
    correlation, r_squared = confound_analysis.run_confound_check(cell_stats)

    data_loader.save_parquet(clean_df, config.CLEAN_RECORDS_PATH)
    data_loader.save_parquet(atomic_df, config.ATOMIC_VIOLATIONS_PATH)
    data_loader.save_parquet(cell_stats, config.H3_CELL_STATS_PATH)

    write_report(notes, correlation, r_squared, cell_stats, shift_distribution)

    print("phase 1 complete")
    print(f"clean records saved to {config.CLEAN_RECORDS_PATH}")
    print(f"atomic violations saved to {config.ATOMIC_VIOLATIONS_PATH}")
    print(f"h3 cell stats saved to {config.H3_CELL_STATS_PATH}")
    print(f"report saved to {config.PHASE1_REPORT_PATH}")
    print(f"confound chart saved to {config.CONFOUND_CHART_PATH}")
    print(f"enforcement confound r squared: {r_squared:.4f}")
    print(f"shift window distribution: {shift_distribution}")


if __name__ == "__main__":
    main()