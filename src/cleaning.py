import json
import ast
import pandas as pd

from src import config


def drop_unusable_columns(df):
    columns_to_drop = [c for c in config.NULL_COLUMNS if c in df.columns]
    return df.drop(columns=columns_to_drop)


def parse_list_field(value):
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except Exception:
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            return []


def add_parsed_violation_fields(df):
    df = df.copy()
    df["violation_list"] = df["violation_type"].apply(parse_list_field)
    df["offence_code_list"] = df["offence_code"].apply(parse_list_field)
    df["violation_count"] = df["violation_list"].apply(len)
    return df


def resolve_vehicle_type(df):
    df = df.copy()
    df["resolved_vehicle_type"] = df["updated_vehicle_type"]
    missing_mask = df["resolved_vehicle_type"].isna()
    df.loc[missing_mask, "resolved_vehicle_type"] = df.loc[missing_mask, "vehicle_type"]
    return df


def resolve_junction_flag(df):
    df = df.copy()
    junction_clean = df["junction_name"].astype(str).str.strip().str.lower()
    df["is_junction"] = (~df["junction_name"].isna()) & (junction_clean != "no junction")
    return df


def add_validation_weight(df):
    df = df.copy()
    df["validation_weight"] = df["validation_status"].map(config.VALIDATION_WEIGHTS)
    df["validation_weight"] = df["validation_weight"].fillna(config.DEFAULT_VALIDATION_WEIGHT)
    return df


def summarize_date_range(df):
    parsed_utc = pd.to_datetime(df["created_datetime"], utc=True, errors="coerce")
    parsed_ist = parsed_utc.dt.tz_convert(config.LOCAL_TIMEZONE)
    return parsed_ist.min(), parsed_ist.max()


def build_atomic_violations_table(df):
    records = []
    for row_id, violations, codes, weight in zip(
        df["id"], df["violation_list"], df["offence_code_list"], df["validation_weight"]
    ):
        if not violations:
            continue
        if len(violations) == len(codes):
            pairs = list(zip(violations, codes))
        else:
            pairs = [(v, None) for v in violations]
        for violation_name, code in pairs:
            records.append(
                {
                    "id": row_id,
                    "violation_type": violation_name,
                    "offence_code": code,
                    "violation_label": config.OFFENCE_CODE_MAP.get(code, violation_name),
                    "validation_weight": weight,
                }
            )
    return pd.DataFrame(records)


def run_cleaning_pipeline(df):
    df = drop_unusable_columns(df)
    df = add_parsed_violation_fields(df)
    df = resolve_vehicle_type(df)
    df = resolve_junction_flag(df)
    df = add_validation_weight(df)
    atomic_df = build_atomic_violations_table(df)
    date_min, date_max = summarize_date_range(df)

    corrected_mask = df["updated_vehicle_type"].notna() & (df["updated_vehicle_type"] != df["vehicle_type"])

    notes = {
        "row_count": len(df),
        "date_min": str(date_min),
        "date_max": str(date_max),
        "approved_count": int((df["validation_status"] == "approved").sum()),
        "rejected_count": int((df["validation_status"] == "rejected").sum()),
        "processing_count": int((df["validation_status"] == "processing").sum()),
        "created1_count": int((df["validation_status"] == "created1").sum()),
        "duplicate_count": int((df["validation_status"] == "duplicate").sum()),
        "unvalidated_count": int(df["validation_status"].isna().sum()),
        "junction_violation_count": int(df["is_junction"].sum()),
        "midblock_violation_count": int((~df["is_junction"]).sum()),
        "vehicle_type_corrected_count": int(corrected_mask.sum()),
    }
    return df, atomic_df, notes