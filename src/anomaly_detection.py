import pandas as pd
from sklearn.ensemble import IsolationForest

from src import config


def build_weekly_matrix(clean_df):
    df = clean_df.copy()
    naive_datetime = df["event_datetime"].dt.tz_localize(None)
    df["week_start"] = naive_datetime.dt.to_period("W").dt.start_time
    pivot = pd.pivot_table(
        df,
        index="h3_cell",
        columns="week_start",
        values="id",
        aggfunc="count",
        fill_value=0,
    )
    pivot = pivot.sort_index(axis=1)
    return pivot


def compute_anomaly_features(weekly_matrix):
    values = weekly_matrix.values.astype(float)
    week_over_week = pd.DataFrame(
        values, index=weekly_matrix.index, columns=weekly_matrix.columns
    ).diff(axis=1)

    features = pd.DataFrame(index=weekly_matrix.index)
    features["mean_weekly"] = values.mean(axis=1)
    features["std_weekly"] = values.std(axis=1)
    features["max_week_jump"] = week_over_week.max(axis=1)
    features["max_week_jump"] = features["max_week_jump"].fillna(0)

    n_weeks = values.shape[1]
    recent_n = max(1, n_weeks // 4)
    recent_avg = values[:, -recent_n:].mean(axis=1)
    overall_avg = values.mean(axis=1)
    features["recent_trend_ratio"] = recent_avg / overall_avg.clip(min=0.01)

    return features


def run_anomaly_detection(clean_df):
    weekly_matrix = build_weekly_matrix(clean_df)
    features = compute_anomaly_features(weekly_matrix)

    feature_cols = ["mean_weekly", "std_weekly", "max_week_jump", "recent_trend_ratio"]

    model = IsolationForest(
        n_estimators=200,
        contamination=config.ANOMALY_CONTAMINATION,
        random_state=42,
    )
    model.fit(features[feature_cols])

    features["anomaly_score"] = -model.decision_function(features[feature_cols])
    features["is_unusual_pattern"] = model.predict(features[feature_cols]) == -1
    features["is_emerging_hotspot"] = features["is_unusual_pattern"] & (features["recent_trend_ratio"] > 1.1)
    features = features.reset_index()
    features = features.rename(columns={features.columns[0]: "h3_cell"})
    return features[
        [
            "h3_cell",
            "mean_weekly",
            "std_weekly",
            "max_week_jump",
            "recent_trend_ratio",
            "anomaly_score",
            "is_unusual_pattern",
            "is_emerging_hotspot",
        ]
    ]