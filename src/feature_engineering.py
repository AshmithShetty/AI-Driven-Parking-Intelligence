import pandas as pd
import h3

from src import config


def assign_shift_window(hour):
    if 0 <= hour < 6:
        return "00-06"
    if 6 <= hour < 12:
        return "06-12"
    if 12 <= hour < 18:
        return "12-18"
    return "18-24"


def add_temporal_features(df):
    df = df.copy()
    parsed_utc = pd.to_datetime(df["created_datetime"], utc=True, errors="coerce")
    parsed_ist = parsed_utc.dt.tz_convert(config.LOCAL_TIMEZONE)
    df["event_datetime"] = parsed_ist
    df["event_hour"] = parsed_ist.dt.hour
    df["event_day_of_week"] = parsed_ist.dt.dayofweek
    df["event_month"] = parsed_ist.dt.month
    df["event_year"] = parsed_ist.dt.year
    df["shift_window"] = df["event_hour"].apply(
        lambda h: assign_shift_window(h) if pd.notna(h) else None
    )
    return df


def infer_road_context(location, junction_name):
    text = f"{location or ''} {junction_name or ''}".strip().lower()
    for context, keywords in config.ROAD_CONTEXT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return context
    return config.DEFAULT_ROAD_CONTEXT


def infer_sensitive_landmark_weight(location, junction_name):
    text = f"{location or ''} {junction_name or ''}".strip().lower()
    matched = [
        weight
        for keyword, weight in config.SENSITIVE_LANDMARK_WEIGHTS.items()
        if keyword in text
    ]
    if not matched:
        return config.DEFAULT_SENSITIVE_LANDMARK_WEIGHT
    return max(matched)


def add_context_features(df):
    df = df.copy()
    df["road_context"] = [
        infer_road_context(location, junction_name)
        for location, junction_name in zip(df["location"], df["junction_name"])
    ]
    df["road_context_weight"] = df["road_context"].map(config.ROAD_CONTEXT_WEIGHTS)
    df["road_context_weight"] = df["road_context_weight"].fillna(
        config.ROAD_CONTEXT_WEIGHTS[config.DEFAULT_ROAD_CONTEXT]
    )
    df["sensitive_landmark_weight"] = [
        infer_sensitive_landmark_weight(location, junction_name)
        for location, junction_name in zip(df["location"], df["junction_name"])
    ]
    df["weekend_flag"] = df["event_day_of_week"].isin([5, 6]).astype(int)
    df["night_flag"] = df["shift_window"].isin(["00-06", "18-24"]).astype(int)
    df["shift_friction_weight"] = df["shift_window"].map(config.SHIFT_FRICTION_WEIGHTS)
    df["shift_friction_weight"] = df["shift_friction_weight"].fillna(1.0)
    return df


def add_h3_cell(df):
    df = df.copy()
    cells = []
    for lat, lon in zip(df["latitude"], df["longitude"]):
        if pd.isna(lat) or pd.isna(lon):
            cells.append(None)
        else:
            cells.append(h3.latlng_to_cell(lat, lon, config.H3_RESOLUTION))
    df["h3_cell"] = cells
    return df


def compute_h3_cell_stats(df):
    grouped = df.groupby("h3_cell")
    stats = grouped.agg(
        raw_violation_count=("id", "count"),
        weighted_violation_count=("validation_weight", "sum"),
        unique_devices=("device_id", "nunique"),
        unique_officers=("created_by_id", "nunique"),
        junction_violation_count=("is_junction", "sum"),
        multi_violation_count=("violation_count", lambda x: (x >= 2).sum()),
        repeat_vehicle_violations=("vehicle_number", lambda x: x.duplicated(keep=False).sum()),
        unactioned_count=("data_sent_to_scita", lambda x: (~x.astype(bool)).sum()),
        mean_latitude=("latitude", "mean"),
        mean_longitude=("longitude", "mean"),
        mean_road_context_weight=("road_context_weight", "mean"),
        mean_sensitive_landmark_weight=("sensitive_landmark_weight", "mean"),
        mean_shift_friction_weight=("shift_friction_weight", "mean"),
        night_violation_count=("night_flag", "sum"),
        weekend_violation_count=("weekend_flag", "sum"),
    ).reset_index()

    stats["violations_per_device"] = stats["weighted_violation_count"] / stats["unique_devices"].clip(lower=1)
    stats["junction_share"] = stats["junction_violation_count"] / stats["raw_violation_count"]
    stats["multi_violation_rate"] = stats["multi_violation_count"] / stats["raw_violation_count"]
    stats["unactioned_rate"] = stats["unactioned_count"] / stats["raw_violation_count"]
    stats["night_share"] = stats["night_violation_count"] / stats["raw_violation_count"]
    stats["weekend_share"] = stats["weekend_violation_count"] / stats["raw_violation_count"]

    return stats


def summarize_shift_distribution(df):
    counts = df["shift_window"].value_counts()
    return {window: int(counts.get(window, 0)) for window in config.SHIFT_WINDOWS}


def run_feature_pipeline(df):
    df = add_temporal_features(df)
    df = add_context_features(df)
    df = add_h3_cell(df)
    cell_stats = compute_h3_cell_stats(df)
    shift_distribution = summarize_shift_distribution(df)
    return df, cell_stats, shift_distribution
