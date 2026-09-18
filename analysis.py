# analysis.py
# Deterministic analysis functions for PROPAN data.
#
# Design decisions:
#   - All calculations are performed deterministically in Python, not by an LLM.
#     This guarantees reproducible, verifiable numerical results.
#   - Functions operate on the pandas DataFrame produced by propan_parser.py.
#   - Comparisons return plain dictionaries so they are easy to display in a GUI
#     or pass to an AI interpretation layer later.

import os
import pandas as pd
from propan_parser import parse_propan_out


def load_p4119_results(data_dir: str = None) -> tuple:
    """
    Load and parse the P4119 PROPAN.OUT file.

    Returns (DataFrame, panel_info dict, operation_time_minutes).
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data", "P4119")
    out_path = os.path.join(data_dir, "PROPAN.OUT")
    return parse_propan_out(out_path)


def get_condition(df: pd.DataFrame, j_value: float) -> dict:
    """
    Retrieve the row for a specific advance ratio J.

    Returns a dictionary of coefficient values.
    Raises ValueError if the J value is not found.
    """
    # Use a small tolerance for floating-point matching
    mask = (df["J"] - j_value).abs() < 1e-6
    rows = df[mask]
    if rows.empty:
        available = df["J"].tolist()
        raise ValueError(
            f"J={j_value} not found. Available J values: {available}"
        )
    return rows.iloc[0].to_dict()


def compare_conditions(df: pd.DataFrame, j1: float, j2: float) -> dict:
    """
    Compare two operating conditions and return absolute and percentage changes.

    The comparison is from j1 → j2 (i.e., j1 is the baseline).

    Returns a dictionary with keys for each coefficient, containing:
      - j1_value: value at j1
      - j2_value: value at j2
      - abs_change: j2_value - j1_value
      - pct_change: percentage change from j1 to j2
    """
    cond1 = get_condition(df, j1)
    cond2 = get_condition(df, j2)

    coeff_cols = ["KTP", "KQP", "KTH", "KQH"]
    comparison = {
        "J_baseline": j1,
        "J_compared": j2,
        "coefficients": {},
    }

    for col in coeff_cols:
        v1 = cond1.get(col)
        v2 = cond2.get(col)
        if v1 is not None and v2 is not None:
            abs_change = v2 - v1
            pct_change = (abs_change / abs(v1) * 100.0) if v1 != 0 else None
            comparison["coefficients"][col] = {
                "j1_value": v1,
                "j2_value": v2,
                "abs_change": abs_change,
                "pct_change": pct_change,
            }

    return comparison


def get_performance_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame suitable for plotting performance trends.

    Includes derived columns:
      - KT_total: KTP + KTH (total thrust coefficient)
      - KQ_total: KQP + KQH (total torque coefficient)
      - eta_o:    open-water efficiency = (J / (2*pi)) * (KT_total / KQ_total)

    These are standard propeller performance metrics.
    """
    import numpy as np

    trends = df.copy()
    trends["KT_total"] = trends["KTP"] + trends["KTH"]
    trends["KQ_total"] = trends["KQP"] + trends["KQH"]

    # Open-water efficiency: eta_o = (J / 2*pi) * (KT / KQ)
    # Only valid where KQ_total != 0
    with np.errstate(divide="ignore", invalid="ignore"):
        trends["eta_o"] = (trends["J"] / (2.0 * np.pi)) * (
            trends["KT_total"] / trends["KQ_total"]
        )
    # Replace infinities with NaN
    trends["eta_o"] = trends["eta_o"].replace([np.inf, -np.inf], np.nan)

    return trends


def format_comparison(comparison: dict) -> str:
    """
    Format a comparison dictionary as a readable text summary.
    """
    lines = []
    j1 = comparison["J_baseline"]
    j2 = comparison["J_compared"]
    lines.append(f"Comparison: J={j1:.3f} -> J={j2:.3f}")
    lines.append("-" * 55)
    lines.append(f"{'Coeff':<6} {'J={:<6.3f}':<14} {'J={:<6.3f}':<14} "
                 f"{'Abs D':<14} {'% D':<10}".format(j1, j2))
    lines.append("-" * 55)

    for col, vals in comparison["coefficients"].items():
        v1 = vals["j1_value"]
        v2 = vals["j2_value"]
        absc = vals["abs_change"]
        pctc = vals["pct_change"]
        pct_str = f"{pctc:+.2f}%" if pctc is not None else "N/A"
        lines.append(
            f"{col:<6} {v1:<+14.6e} {v2:<+14.6e} {absc:<+14.6e} {pct_str}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Analysis Module — Self Test")
    print("=" * 60)

    # Load data
    df, panel_info, op_time = load_p4119_results()
    print(f"\nLoaded {len(df)} operating conditions")
    print(f"J values: {df['J'].tolist()}")

    # Show all coefficient values
    print(f"\nAll coefficients:\n{df[['J', 'KTP', 'KQP', 'KTH', 'KQH']].to_string(index=False)}")

    # Comparison 1: J=0.5 vs J=0.7
    print("\n")
    comp1 = compare_conditions(df, 0.5, 0.7)
    print(format_comparison(comp1))

    # Comparison 2: J=0.7 vs J=1.0
    print("\n")
    comp2 = compare_conditions(df, 0.7, 1.0)
    print(format_comparison(comp2))

    # Performance trends
    print("\n\nPerformance trends:")
    trends = get_performance_trends(df)
    print(trends.to_string(index=False))

    print("\n[Analysis self-test PASSED]")
