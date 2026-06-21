import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config


def compute_confound_correlation(cell_stats):
    valid = cell_stats.dropna(subset=["raw_violation_count", "unique_devices"])
    valid = valid[valid["unique_devices"] > 0]
    correlation = np.corrcoef(valid["unique_devices"], valid["raw_violation_count"])[0, 1]
    r_squared = correlation ** 2
    return correlation, r_squared, valid


def plot_confound_chart(valid, correlation):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(valid["unique_devices"], valid["raw_violation_count"], alpha=0.5, s=20)
    ax.set_yscale("log")
    ax.set_xlabel("unique enforcement devices active in cell")
    ax.set_ylabel("violation count in cell (log scale)")
    ax.set_title(f"enforcement effort vs violation count, r={correlation:.3f}")
    fig.tight_layout()
    fig.savefig(config.CONFOUND_CHART_PATH, dpi=150)
    plt.close(fig)


def run_confound_check(cell_stats):
    correlation, r_squared, valid = compute_confound_correlation(cell_stats)
    plot_confound_chart(valid, correlation)
    return correlation, r_squared