import os
import pandas as pd

from src import config


def load_raw_violations():
    if not os.path.exists(config.RAW_DATA_PATH):
        raise FileNotFoundError(
            f"raw csv not found at {config.RAW_DATA_PATH}, place the dataset there before running the pipeline"
        )
    df = pd.read_csv(config.RAW_DATA_PATH, low_memory=False)
    return df


def save_parquet(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)


def load_parquet(path):
    return pd.read_parquet(path)