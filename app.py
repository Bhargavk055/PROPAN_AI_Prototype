# app.py
# Streamlit GUI for the PROPAN P4119 Propeller Performance Prototype.
#
# This GUI loads real PROPAN output data via propan_parser.py,
# performs all calculations via analysis.py, and displays results
# using Plotly charts and Streamlit layout components.
#
# No numerical values are hard-coded. Everything comes from PROPAN.OUT or actual Fortran solver runs.

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from propan_parser import parse_propan_out, parse_propan_inp
from analysis import (
    load_p4119_results,
    get_condition,
    compare_conditions,
    get_performance_trends,
)
from ai_assistant import is_ai_configured, build_analysis_context, ask_ai
from propan_runner import run_propan_custom_j

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PROPAN AI Prototype",
    page_icon="⚓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Load data (cached so it only runs once)
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    """Load and parse P4119 data. Returns (df, panel_info, op_time)."""
    return load_p4119_results()

@st.cache_data
def load_input_params():
    """Load and parse PROPAN.INP parameters."""
    import os
    inp_path = os.path.join(os.path.dirname(__file__), "data", "P4119", "PROPAN.INP")
    return parse_propan_inp(inp_path)

try:
    df, panel_info, op_time = load_data()
    inp_params = load_input_params()
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}")
    st.stop()
except ValueError as e:
    st.error(f"Data parsing error: {e}")
    st.stop()

# Initialize session state for custom simulation results
if "custom_runs" not in st.session_state:
    st.session_state["custom_runs"] = []

# Merge custom simulation results with base DataFrame if any exist
combined_df = df.copy()
if st.session_state["custom_runs"]:
    for custom_df in st.session_state["custom_runs"]:
        combined_df = pd.concat([combined_df, custom_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["J"]).sort_values("J").reset_index(drop=True)

trends = get_performance_trends(combined_df)
j_values = combined_df["J"].tolist()
j_labels = [f"{j:.4f}".rstrip('0').rstrip('.') for j in j_values]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("PROPAN P4119")
    st.markdown("---")

    st.markdown("**Data**")
    st.write("P4119 Propeller Case")

    st.markdown("**Available J values**")
    st.write(", ".join(j_labels))

    st.markdown("**Data source**")
    st.write("Official PROPAN Solver Output")

    st.markdown("**Solver status**")
    st.success("Fortran Solver Executable Ready")

    if op_time is not None:
        st.markdown("**Base run time**")
        st.write(f"{op_time:.0f} minutes")

    st.markdown("---")
    st.caption("All values computed from official PROPAN solver runs.")

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("PROPAN AI Prototype")
st.subheader("P4119 Propeller Performance Analysis & Custom Solver")

# ---------------------------------------------------------------------------
# Section 1 -- Case Overview
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Case Overview")

col_case1, col_case2, col_case3, col_case4 = st.columns(4)
col_case1.metric("Case", "P4119")
col_case2.metric("Data source", "PROPAN.OUT")
col_case3.metric("Operating conditions", str(len(combined_df)))
col_case4.metric("Fortran Solver", "Active (gfortran)")

if inp_params.get("COMMENT"):
    st.caption("Configuration: " + " / ".join(inp_params["COMMENT"]))

# ---------------------------------------------------------------------------
# Section 2 -- Run Custom PROPAN Solver
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Run Custom PROPAN Solver Simulation")
st.write("Enter any custom advance ratio $J$ to execute the compiled Fortran PROPAN solver in real-time.")

sim_col1, sim_col2 = st.columns([2, 1])
with sim_col1:
    custom_j_val = st.number_input(
        "Custom Advance Ratio (J)",
        min_value=0.010,
        max_value=5.000,
        value=0.7137,
        step=0.001,
        format="%.4f"
    )
with sim_col2:
    st.write("")
    st.write("")
    run_btn = st.button("🚀 Run PROPAN Fortran Solver", use_container_width=True)

if run_btn:
    with st.spinner(f"Running official Fortran PROPAN solver for J = {custom_j_val:.4f}..."):
        try:
            custom_res_df = run_propan_custom_j(custom_j_val)
            st.session_state["custom_runs"].append(custom_res_df)
            st.success(f"✅ PROPAN Fortran solver completed successfully for J = {custom_j_val:.4f}!")
            st.rerun()
        except Exception as err:
            st.error(f"Solver execution error: {err}")

# ---------------------------------------------------------------------------
# Section 3 -- Operating Condition Selector & Current Result
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Current Result")

selected_j = st.selectbox(
    "Select Operating condition (Advance Ratio J)",
    options=j_values,
    format_func=lambda x: f"J = {x:.4f}".rstrip('0').rstrip('.') + (" (Custom Run)" if any(abs(x - c_df["J"].iloc[0]) < 1e-5 for c_df in st.session_state["custom_runs"]) else ""),
    index=min(2, len(j_values) - 1),
)

cond = get_condition(combined_df, selected_j)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("J", f"{cond['J']:.4f}".rstrip('0').rstrip('.'))
col2.metric("KTP (Blade Thrust)", f"{cond['KTP']:.6f}")
col3.metric("KQP (Blade Torque)", f"{cond['KQP']:.6f}")
col4.metric("KTH (Hub Thrust)", f"{cond['KTH']:.6f}")
col5.metric("KQH (Hub Torque)", f"{cond['KQH']:.2e}")

# Show convergence info for the selected condition
kutta_val = cond.get("kutta_iterations")
errk_val = cond.get("ERRK_final")
kutta_str = f"{int(kutta_val)}" if (kutta_val is not None and pd.notna(kutta_val)) else "N/A"
errk_str = f"{errk_val:.2e}" if (errk_val is not None and pd.notna(errk_val)) else "N/A"

conv_col1, conv_col2 = st.columns(2)
conv_col1.caption(
    f"Kutta iterations: {kutta_str} | Final ERRK: {errk_str}"
)

# ---------------------------------------------------------------------------
# Section 4 -- Performance Trend Charts
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Performance Trends")

chart_col1, chart_col2 = st.columns(2)

# Chart 1: Blade coefficients (KTP, KQP)
with chart_col1:
    fig_blade = go.Figure()

    fig_blade.add_trace(go.Scatter(
        x=trends["J"], y=trends["KTP"],
        mode="lines+markers",
        name="KTP (Blade Thrust)",
        line=dict(color="#2563eb", width=2),
        marker=dict(size=8),
    ))
    fig_blade.add_trace(go.Scatter(
        x=trends["J"], y=trends["KQP"],
        mode="lines+markers",
        name="KQP (Blade Torque)",
        line=dict(color="#dc2626", width=2),
        marker=dict(size=8),
    ))

    # Highlight selected J
    sel_row = trends[trends["J"] == selected_j]
    if not sel_row.empty:
        fig_blade.add_trace(go.Scatter(
            x=[selected_j], y=[sel_row["KTP"].iloc[0]],
            mode="markers",
            name=f"Selected (J={selected_j:.3f})",
            marker=dict(size=14, color="#2563eb", symbol="star",
                        line=dict(width=2, color="white")),
            showlegend=False,
        ))
        fig_blade.add_trace(go.Scatter(
            x=[selected_j], y=[sel_row["KQP"].iloc[0]],
            mode="markers",
            marker=dict(size=14, color="#dc2626", symbol="star",
                        line=dict(width=2, color="white")),
            showlegend=False,
        ))

    fig_blade.update_layout(
        title="Blade Coefficients vs Advance Ratio",
        xaxis_title="J (Advance Ratio)",
        yaxis_title="Coefficient",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_blade, use_container_width=True)

# Chart 2: Hub coefficients (KTH, KQH)
with chart_col2:
    fig_hub = go.Figure()

    fig_hub.add_trace(go.Scatter(
        x=trends["J"], y=trends["KTH"],
        mode="lines+markers",
        name="KTH (Hub Thrust)",
        line=dict(color="#059669", width=2),
        marker=dict(size=8),
    ))
    fig_hub.add_trace(go.Scatter(
        x=trends["J"], y=trends["KQH"],
        mode="lines+markers",
        name="KQH (Hub Torque)",
        line=dict(color="#d97706", width=2),
        marker=dict(size=8),
        yaxis="y2",
    ))

    # Highlight selected J
    if not sel_row.empty:
        fig_hub.add_trace(go.Scatter(
            x=[selected_j], y=[sel_row["KTH"].iloc[0]],
            mode="markers",
            marker=dict(size=14, color="#059669", symbol="star",
                        line=dict(width=2, color="white")),
            showlegend=False,
        ))
        fig_hub.add_trace(go.Scatter(
            x=[selected_j], y=[sel_row["KQH"].iloc[0]],
            mode="markers",
            marker=dict(size=14, color="#d97706", symbol="star",
                        line=dict(width=2, color="white")),
            showlegend=False,
            yaxis="y2",
        ))

    fig_hub.update_layout(
        title="Hub Coefficients vs Advance Ratio",
        xaxis_title="J (Advance Ratio)",
        yaxis_title="KTH",
        yaxis2=dict(title="KQH", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_hub, use_container_width=True)

# Chart 3: Open-water efficiency
st.markdown("#### Open-Water Efficiency")
fig_eta = go.Figure()
fig_eta.add_trace(go.Scatter(
    x=trends["J"], y=trends["eta_o"],
    mode="lines+markers",
    name="eta_o",
    line=dict(color="#7c3aed", width=2),
    marker=dict(size=8),
))
if not sel_row.empty:
    fig_eta.add_trace(go.Scatter(
        x=[selected_j], y=[sel_row["eta_o"].iloc[0]],
        mode="markers",
        marker=dict(size=14, color="#7c3aed", symbol="star",
                    line=dict(width=2, color="white")),
        showlegend=False,
    ))
fig_eta.update_layout(
    title="Open-Water Efficiency (eta_o = J/(2*pi) * KT_total/KQ_total)",
    xaxis_title="J (Advance Ratio)",
    yaxis_title="eta_o",
    height=350,
    margin=dict(t=60, b=40),
)
st.plotly_chart(fig_eta, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 5 -- Compare Conditions
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Compare Conditions")

comp_col_a, comp_col_b = st.columns(2)

with comp_col_a:
    j_a = st.selectbox(
        "Condition A (baseline)",
        options=j_values,
        format_func=lambda x: f"J = {x:.3f}",
        index=0,
        key="comp_a",
    )

with comp_col_b:
    default_b = min(2, len(j_values) - 1)
    j_b = st.selectbox(
        "Condition B (compared)",
        options=j_values,
        format_func=lambda x: f"J = {x:.3f}",
        index=default_b,
        key="comp_b",
    )

# Display both conditions side by side
cond_a = get_condition(combined_df, j_a)
cond_b = get_condition(combined_df, j_b)

result_col_a, result_col_b = st.columns(2)

with result_col_a:
    st.markdown(f"**Condition A: J = {j_a:.3f}**")
    st.write(f"KTP = {cond_a['KTP']:.6f}")
    st.write(f"KQP = {cond_a['KQP']:.6f}")
    st.write(f"KTH = {cond_a['KTH']:.6f}")
    st.write(f"KQH = {cond_a['KQH']:.2e}")

with result_col_b:
    st.markdown(f"**Condition B: J = {j_b:.3f}**")
    st.write(f"KTP = {cond_b['KTP']:.6f}")
    st.write(f"KQP = {cond_b['KQP']:.6f}")
    st.write(f"KTH = {cond_b['KTH']:.6f}")
    st.write(f"KQH = {cond_b['KQH']:.2e}")

# Comparison table
if j_a != j_b:
    comp = compare_conditions(combined_df, j_a, j_b)

    st.markdown(f"**Changes: J = {j_a:.3f} -> J = {j_b:.3f}**")

    change_cols = st.columns(4)
    coeff_names = {"KTP": "Blade Thrust", "KQP": "Blade Torque",
                   "KTH": "Hub Thrust", "KQH": "Hub Torque"}

    for i, (coeff, label) in enumerate(coeff_names.items()):
        vals = comp["coefficients"].get(coeff, {})
        if vals:
            abs_c = vals["abs_change"]
            pct_c = vals["pct_change"]
            pct_str = f"{pct_c:+.2f}%" if pct_c is not None else "N/A"
            change_cols[i].metric(
                label=f"{coeff} ({label})",
                value=f"{vals['j2_value']:.6f}",
                delta=pct_str,
            )
else:
    st.info("Select two different conditions to see a comparison.")

# ---------------------------------------------------------------------------
# Section 6 -- Data Table
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Complete Data Table")
st.caption("Values parsed from official PROPAN solver output.")

display_df = combined_df[["J", "KTP", "KQP", "KTH", "KQH",
                          "ERRK_final", "kutta_iterations"]].copy()
display_df.columns = ["J", "KTP", "KQP", "KTH", "KQH",
                       "Final ERRK", "Kutta Iterations"]
st.dataframe(display_df, use_container_width=True, hide_index=True)

# Performance trends table
st.markdown("#### Derived Performance Metrics")
st.caption("KT_total = KTP + KTH, KQ_total = KQP + KQH, "
           "eta_o = (J / 2*pi) * (KT_total / KQ_total)")

display_trends = trends[["J", "KT_total", "KQ_total", "eta_o"]].copy()
display_trends.columns = ["J", "KT Total", "KQ Total", "Open-Water Efficiency"]
st.dataframe(display_trends, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Section 7 -- AI Engineering Assistant
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### AI ENGINEERING ASSISTANT")

if not is_ai_configured():
    st.info("💡 **AI assistant is not configured.** Set the `GEMINI_API_KEY` (or `OPENAI_API_KEY`) environment variable to enable AI interpretation.")
else:
    st.markdown("Ask the AI to interpret the current PROPAN performance data.")
    
    # Suggested questions
    suggested_q = st.selectbox(
        "Suggested questions:",
        [
            "Analyze the current performance trend",
            "Compare the selected conditions",
            "What changes as J increases?",
            "Explain KTP and KQP trends",
            "Custom question..."
        ]
    )
    
    user_q = ""
    if suggested_q == "Custom question...":
        user_q = st.text_input("Enter your question:")
    else:
        user_q = suggested_q
        
    if st.button("Ask AI"):
        if not user_q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing data..."):
                # Build context
                comparison_data = comp if ('comp' in locals() and j_a != j_b) else None
                context = build_analysis_context(
                    df=combined_df,
                    current_j=selected_j,
                    current_condition=cond,
                    comparison=comparison_data
                )
                
                # Ask AI
                response = ask_ai(user_q, context)
                
                st.markdown("#### AI Interpretation")
                st.write(response)
