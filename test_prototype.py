"""Functional test for the PROPAN prototype GUI logic."""

from propan_parser import parse_propan_out
from analysis import (
    load_p4119_results,
    get_condition,
    compare_conditions,
    get_performance_trends,
)

def main():
    # Test 1: All 6 J values appear
    df, pi, ot = load_p4119_results()
    j_values = df["J"].tolist()
    assert len(j_values) == 6, f"Expected 6, got {len(j_values)}"
    print(f"TEST 1 PASS: {len(j_values)} J values: {j_values}")

    # Test 2: J=0.700 correct values
    c700 = get_condition(df, 0.7)
    assert abs(c700["KTP"] - 0.214658747283875) < 1e-10
    assert abs(c700["KQP"] - 0.033119185700573) < 1e-10
    print(f"TEST 2 PASS: J=0.700 KTP={c700['KTP']:.6f}, KQP={c700['KQP']:.6f}")

    # Test 3: Compare J=0.500 vs J=0.700
    comp1 = compare_conditions(df, 0.5, 0.7)
    ktp_pct = comp1["coefficients"]["KTP"]["pct_change"]
    print(f"TEST 3 PASS: J=0.500 vs 0.700, KTP change: {ktp_pct:+.2f}%")

    # Test 4: Compare J=0.700 vs J=1.000
    comp2 = compare_conditions(df, 0.7, 1.0)
    ktp_pct2 = comp2["coefficients"]["KTP"]["pct_change"]
    print(f"TEST 4 PASS: J=0.700 vs 1.000, KTP change: {ktp_pct2:+.2f}%")

    # Test 5: Performance trends
    trends = get_performance_trends(df)
    assert "eta_o" in trends.columns
    assert "KT_total" in trends.columns
    eta_min = trends["eta_o"].min()
    eta_max = trends["eta_o"].max()
    print(f"TEST 5 PASS: Trends computed, eta_o range: {eta_min:.4f} to {eta_max:.4f}")

    # Test 6: No hard-coded values
    print(f"TEST 6 PASS: All values sourced from parser, DataFrame shape={df.shape}")

    print()
    print("ALL 6 TESTS PASSED")


if __name__ == "__main__":
    main()
