import streamlit as st

from src import config
from src import validation_engine


@st.cache_data
def load_validation_results():
    return validation_engine.run_validation_pipeline()


def render_validation_view():
    st.subheader("Model Validation")
    
    with st.expander(":material/fact_check: Guide: How to understand this tab (Click to expand)"):
        st.markdown("""
        * **What is this?** This tab proves that the AI's recommendations are reliable and not just random guesses.
        * **Spearman rank correlation**: A number between 0 and 1. Closer to 1 means the AI is very consistent at identifying bad parking areas over time.
        * **Forward monthly backtest**: We test the AI by asking it to predict *future* hotspots based on past data, and then we check if it was right.
        """)

    st.markdown(
        "The congestion impact score is a rule-based operational model, so the most important "
        "question is whether cells that score high continue to look risky later. This tab shows "
        "two checks: a temporal stability test and a forward monthly backtest."
    )

    with st.spinner("Computing validation checks"):
        stability_result, backtest_df = load_validation_results()

    col1, col2 = st.columns(2)
    col1.metric("Consistency Score (Correlation)", f"{stability_result['correlation']:.3f}")
    col2.metric("Areas compared", stability_result["cells_compared"])
    st.caption(f"Statistical confidence (p-value): {stability_result['p_value']:.6f}")
    st.write(f"First time period: {stability_result['first_half_start']} to {stability_result['first_half_end']}")
    st.write(f"Second time period: {stability_result['second_half_start']} to {stability_result['second_half_end']}")

    st.markdown(
        "A correlation close to 1.0 means a hotspot ranked high in one half of the data is "
        "very likely to also rank high in the other half, evidence that the ranking reflects "
        "a stable underlying pattern rather than noise in any single time window. A weaker "
        "correlation means the ranking should be treated with more caution."
    )
    st.scatter_chart(stability_result["merged_table"], x="cis_first_half", y="cis_second_half")

    st.markdown("Forward monthly backtest")
    if backtest_df.empty:
        st.warning("No monthly backtest results were generated from the processed data.")
        return

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Prediction Accuracy (Proxy)", f"{backtest_df['spearman_future_proxy'].mean():.3f}")
    metric_col2.metric("Prediction Accuracy (Density)", f"{backtest_df['spearman_future_density'].mean():.3f}")
    metric_col3.metric(
        f"Top {config.BACKTEST_TOP_K} Hit Rate",
        f"{backtest_df['precision_at_k'].mean():.3f}",
    )

    st.caption(
        "Prediction Accuracy compares this model's ranking against the next month's actual "
        "observations. Hit Rate measures how many of the top predicted areas actually "
        f"appeared in the next month's top {config.BACKTEST_TOP_K} worst areas."
    )
    st.dataframe(backtest_df, width="stretch", height=260)
