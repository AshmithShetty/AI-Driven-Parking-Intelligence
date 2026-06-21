import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "violations.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

CLEAN_RECORDS_PATH = os.path.join(PROCESSED_DIR, "violations_clean.parquet")
ATOMIC_VIOLATIONS_PATH = os.path.join(PROCESSED_DIR, "violations_atomic.parquet")
H3_CELL_STATS_PATH = os.path.join(PROCESSED_DIR, "h3_cell_stats.parquet")
PHASE1_REPORT_PATH = os.path.join(REPORTS_DIR, "phase1_data_quality_report.txt")
CONFOUND_CHART_PATH = os.path.join(REPORTS_DIR, "enforcement_confound.png")

HOTSPOT_SCORES_PATH = os.path.join(PROCESSED_DIR, "hotspot_scores.parquet")
HOTSPOT_RANKING_CSV_PATH = os.path.join(PROCESSED_DIR, "hotspot_ranking.csv")
PHASE2_REPORT_PATH = os.path.join(REPORTS_DIR, "phase2_hotspot_report.txt")

H3_RESOLUTION = 8
LOCAL_TIMEZONE = "Asia/Kolkata"

NULL_COLUMNS = ["description", "closed_datetime", "action_taken_timestamp"]

OFFENCE_CODE_MAP = {
    104: "PARKING NEAR ROAD CROSSING",
    105: "PARKING ON FOOTPATH",
    106: "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSSING",
    107: "PARKING IN A MAIN ROAD",
    108: "PARKING OPPOSITE PARKED VEHICLE",
    109: "DOUBLE PARKING",
    111: "PARKING NEAR BUS STOP SCHOOL OR HOSPITAL",
    112: "WRONG PARKING",
    113: "NO PARKING",
    116: "DEFECTIVE NUMBER PLATE",
    124: "REFUSE TO GO FOR HIRE",
    130: "VIOLATING LANE DISCIPLINE",
    135: "AGAINST ONE WAY OR NO ENTRY",
    139: "PARKING OTHER THAN BUS STOP",
}

VALIDATION_WEIGHTS = {
    "approved": 1.0,
    "processing": 0.5,
    "created1": 0.5,
    "rejected": 0.0,
    "duplicate": 0.0,
}
DEFAULT_VALIDATION_WEIGHT = 0.5

EXPECTED_DATE_RANGE_LABEL = "Jan to May"

SHIFT_WINDOWS = ["00-06", "06-12", "12-18", "18-24"]

VEHICLE_PCU_WEIGHTS = {
    "SCOOTER": 0.5,
    "MOTOR CYCLE": 0.5,
    "MOPED": 0.5,
    "PASSENGER AUTO": 1.2,
    "GOODS AUTO": 1.2,
    "CAR": 1.0,
    "JEEP": 1.0,
    "VAN": 1.0,
    "OTHERS": 1.0,
    "LGV": 1.5,
    "TEMPO": 1.5,
    "MAXI-CAB": 1.5,
    "MINI LORRY": 1.5,
    "HGV": 3.0,
    "LORRY/GOODS VEHICLE": 3.0,
    "TANKER": 3.0,
    "PRIVATE BUS": 3.0,
    "BUS (BMTC/KSRTC)": 3.0,
    "TOURIST BUS": 3.0,
    "SCHOOL VEHICLE": 3.0,
    "FACTORY BUS": 3.0,
    "TRACTOR": 4.0,
}
DEFAULT_PCU_WEIGHT = 1.0

OFFENCE_SEVERITY_WEIGHTS = {
    104: 8,
    105: 4,
    106: 10,
    107: 9,
    108: 7,
    109: 8,
    111: 8,
    112: 5,
    113: 5,
    116: 1,
    124: 1,
    130: 6,
    135: 7,
    139: 5,
}
DEFAULT_SEVERITY_WEIGHT = 4

CIS_WEIGHTS = {
    "density": 0.30,
    "severity": 0.25,
    "footprint": 0.20,
    "junction": 0.15,
    "chronicity": 0.10,
}

EGS_WEIGHTS = {
    "unactioned": 0.6,
    "rejection": 0.4,
}

PRIORITY_WEIGHTS = {
    "cis": 0.6,
    "egs": 0.4,
}

ANOMALY_CONTAMINATION = 0.05
EVENING_GAP_SHARE_THRESHOLD = 0.05

PRIORITY_SCORES_PATH = os.path.join(PROCESSED_DIR, "priority_scores.parquet")
PRIORITY_RANKING_CSV_PATH = os.path.join(PROCESSED_DIR, "priority_ranking.csv")
PHASE3_REPORT_PATH = os.path.join(REPORTS_DIR, "phase3_priority_report.txt")
VALIDATION_SUMMARY_PATH = os.path.join(REPORTS_DIR, "validation_summary.txt")
VALIDATION_BACKTEST_PATH = os.path.join(PROCESSED_DIR, "validation_backtest.parquet")

SHIFT_RANKING_CSV_PATHS = {
    "00-06": os.path.join(PROCESSED_DIR, "shift_ranking_00_06.csv"),
    "06-12": os.path.join(PROCESSED_DIR, "shift_ranking_06_12.csv"),
    "12-18": os.path.join(PROCESSED_DIR, "shift_ranking_12_18.csv"),
    "18-24": os.path.join(PROCESSED_DIR, "shift_ranking_18_24.csv"),
}

ROAD_CONTEXT_WEIGHTS = {
    "expressway": 1.45,
    "arterial": 1.30,
    "collector": 1.15,
    "local": 1.00,
}
DEFAULT_ROAD_CONTEXT = "local"

ROAD_CONTEXT_KEYWORDS = {
    "expressway": ["outer ring road", "ring road", "expressway", "flyover", "underpass", "highway"],
    "arterial": ["main road", "signal", "junction", "crossing", "market", "metro", "station", "circle"],
    "collector": ["cross road", "cross", "layout", "avenue", "road"],
}

SENSITIVE_LANDMARK_WEIGHTS = {
    "metro": 1.25,
    "station": 1.20,
    "market": 1.20,
    "mall": 1.15,
    "hospital": 1.20,
    "school": 1.20,
    "theatre": 1.15,
    "bus stop": 1.15,
    "commercial": 1.10,
}
DEFAULT_SENSITIVE_LANDMARK_WEIGHT = 1.0

SHIFT_FRICTION_WEIGHTS = {
    "00-06": 1.15,
    "06-12": 0.95,
    "12-18": 0.90,
    "18-24": 1.10,
}

ENGINEERING_CIS_WEIGHTS = {
    "density": 0.20,
    "severity": 0.12,
    "footprint": 0.18,
    "junction": 0.12,
    "chronicity": 0.10,
    "road_context": 0.13,
    "shift_risk": 0.15,
}

BACKTEST_TOP_K = 20

ROUTE_SPEED_KMPH = 22.0
