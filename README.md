# PROPAN AI Prototype

An end-to-end GUI prototype built around the official PROPAN propeller analysis solver and workflow.

## What is PROPAN?

PROPAN is a **panel method solver** for marine propeller hydrodynamics analysis,
developed at IST (Instituto Superior Técnico, Lisbon). It solves potential
flow around a propeller using a boundary element (panel) method, computing thrust
and torque coefficients at specified advance ratios.

This prototype includes:
1. **Official Compiled Fortran Solver** (`propan.exe`) compiled with GFortran (MinGW-w64).
2. **Deterministic Python Analysis & Parsing Layer** (`propan_parser.py`, `analysis.py`, `propan_runner.py`).
3. **Interactive Streamlit GUI Dashboard** (`app.py`).
4. **AI Interpretation Assistant** (`ai_assistant.py`).

## Features & Capabilities

- **Real-Time Fortran Solver Execution** — Enter any custom advance ratio $J$ in the GUI to execute the official Fortran solver in real-time.
- **P4119 Standard Benchmark** — Includes pre-calculated P4119 benchmark operating conditions ($J = 0.5$ to $1.0$).
- **No Mock or Simulated Data** — All numerical values displayed come directly from actual `PROPAN.OUT` solver outputs.
- **Data Integrity** — The cloned PROPAN repository in `external/PROPAN/` is kept **read-only and untouched**.

## Architecture

```
User Input (J) / Pre-calculated P4119 Data
        |
        v
PROPAN Fortran Solver (propan.exe)
        |
        v
PROPAN.OUT Output File
        |
        v
Python Parser (propan_parser.py)
        |
        v
Deterministic Analysis (analysis.py)
        |
        v
Plotly Visualization & Interactive Dashboard (app.py)
        |
        v
AI Interpretation Layer (ai_assistant.py)
```

## Project Structure

```
PROPAN_AI_Prototype/
    .venv/                  # Python virtual environment
    data/
        P4119/              # P4119 reference input & output files
    external/
        PROPAN/             # Original PROPAN repository (read-only)
    propan_solver/
        compile_propan.py   # Automated Fortran compiler script
        propan.exe          # Compiled official Fortran solver executable
        stubs/              # Fortran routine stubs
    app.py                  # Streamlit GUI dashboard
    propan_runner.py        # Solver runner module for custom J inputs
    analysis.py             # Deterministic analysis functions
    propan_parser.py        # PROPAN output & input file parser
    ai_assistant.py         # AI interpretation layer (OpenAI API integration)
    test_prototype.py       # Deterministic analysis test suite
    test_ai_assistant.py    # AI assistant test suite
    test_propan_runner.py   # Fortran solver runner test suite
    requirements.txt        # Python dependencies
    README.md               # Project documentation
```

## Setup & Running

```bash
# Activate Virtual Environment
.venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run Streamlit GUI Application
python -m streamlit run app.py
```

The application will launch at `http://localhost:8501`.

## Optional AI Assistant Configuration

To enable the AI engineering assistant, set your Gemini API key before starting Streamlit:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

## Automated Testing

```bash
python propan_parser.py     # Parser self-test
python analysis.py          # Analysis self-test
python test_prototype.py    # Functional analysis test suite
python test_ai_assistant.py # AI assistant test suite
python test_propan_runner.py # Fortran solver integration test suite
```
