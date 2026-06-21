import os

from src import config
from src import pipeline
from src import pipeline_phase2
from src import pipeline_phase3
from src import validation_engine


REQUIRED_OUTPUTS = [
    config.CLEAN_RECORDS_PATH,
    config.ATOMIC_VIOLATIONS_PATH,
    config.H3_CELL_STATS_PATH,
    config.HOTSPOT_SCORES_PATH,
    config.PRIORITY_SCORES_PATH,
    config.PRIORITY_RANKING_CSV_PATH,
    config.PHASE1_REPORT_PATH,
    config.PHASE2_REPORT_PATH,
    config.PHASE3_REPORT_PATH,
    config.VALIDATION_SUMMARY_PATH,
]


def outputs_missing():
    return [path for path in REQUIRED_OUTPUTS if not os.path.exists(path)]


def outputs_stale():
    if not os.path.exists(config.RAW_DATA_PATH):
        return False
    raw_mtime = os.path.getmtime(config.RAW_DATA_PATH)
    existing_outputs = [path for path in REQUIRED_OUTPUTS if os.path.exists(path)]
    if not existing_outputs:
        return False
    oldest_output = min(os.path.getmtime(path) for path in existing_outputs)
    return raw_mtime > oldest_output


def build_all_artifacts():
    pipeline.main()
    pipeline_phase2.main()
    pipeline_phase3.main()
    validation_engine.run_validation_pipeline()


def ensure_artifacts():
    missing = outputs_missing()
    stale = outputs_stale()
    if missing or stale:
        build_all_artifacts()
    remaining_missing = outputs_missing()
    return {
        "rebuilt": bool(missing or stale),
        "missing_outputs": remaining_missing,
        "stale": stale,
    }
