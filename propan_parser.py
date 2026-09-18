# propan_parser.py
# Parses PROPAN input (.INP) and output (.OUT) files into structured data.
#
# Design decisions:
#   - Regex-based line parsing is used because PROPAN.OUT is a Fortran free-form
#     text output, not a CSV or fixed-width table.
#   - Scientific notation like 4.210E-002 is handled natively by Python's float().
#   - The parser returns pandas DataFrames so the rest of the prototype can work
#     with clean, typed, labelled data.
#   - No values are invented. If a field is missing from the file, it is NaN.

import re
import os
import pandas as pd


def parse_propan_out(filepath: str) -> pd.DataFrame:
    """
    Parse a PROPAN.OUT file and return a DataFrame with one row per
    operating condition (advance ratio J).

    Columns: J, KTP, KQP, KTH, KQH, ERRK_final, kutta_iterations

    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if no operating conditions can be parsed.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PROPAN.OUT not found at: {filepath}")

    with open(filepath, "r") as f:
        text = f.read()

    # --- Parse panel information from the header ---
    panel_info = {}
    panel_patterns = {
        "NRP": r"NRP=\s*([\d]+)",
        "NCP": r"NCP=\s*([\d]+)",
        "NPPAN": r"NPPAN=\s*([\d]+)",
        "NRW": r"NRW=\s*([\d]+)",
        "NPW": r"NPW=\s*([\d]+)",
        "NPWPAN": r"NPWPAN=\s*([\d]+)",
        "NHTP": r"NHTP=\s*([\d]+)",
        "NHX": r"NHX=\s*([\d]+)",
        "NHPAN": r"NHPAN=\s*([\d]+)",
        "NPAN": r"Total number of body panels NPAN=\s*([\d]+)",
        "NWPAN": r"Total number of wake panels NWPAN=\s*([\d]+)",
    }
    for key, pattern in panel_patterns.items():
        m = re.search(pattern, text)
        if m:
            panel_info[key] = int(m.group(1))

    # --- Parse operation time ---
    time_match = re.search(r"Operation time\s*=\s*([\d.]+)\s*minutes", text)
    operation_time_min = float(time_match.group(1)) if time_match else None

    # --- Split file into per-J blocks ---
    # Each block starts with "  J= <value>" and runs until the next J= or EOF.
    j_pattern = re.compile(r"^\s*J=\s*(.+)$", re.MULTILINE)
    j_matches = list(j_pattern.finditer(text))

    if not j_matches:
        raise ValueError(
            f"No operating conditions (J=...) found in {filepath}"
        )

    records = []
    for i, jm in enumerate(j_matches):
        # Extract the text block for this J condition
        start = jm.start()
        end = j_matches[i + 1].start() if i + 1 < len(j_matches) else len(text)
        block = text[start:end]

        j_val = float(jm.group(1).strip())

        # Parse final coefficients (last KTP/KQP/KTH/KQH lines in the block)
        ktp = _last_match(r"KTP=\s*([^\s]+)", block)
        kqp = _last_match(r"KQP=\s*([^\s]+)", block)
        kth = _last_match(r"KTH=\s*([^\s]+)", block)
        kqh = _last_match(r"KQH=\s*([^\s]+)", block)

        # Parse Kutta condition iterations
        errk_matches = re.findall(r"ERRK=\s*([^\s]+)", block)
        kutta_iters = len(errk_matches)
        errk_final = float(errk_matches[-1]) if errk_matches else None

        records.append({
            "J": j_val,
            "KTP": ktp,
            "KQP": kqp,
            "KTH": kth,
            "KQH": kqh,
            "ERRK_final": errk_final,
            "kutta_iterations": kutta_iters,
        })

    df = pd.DataFrame(records)

    # --- Validate ---
    _validate_dataframe(df, filepath)

    return df, panel_info, operation_time_min


def parse_propan_inp(filepath: str) -> dict:
    """
    Parse a PROPAN.INP file and return a dictionary of key parameters.

    This is a simplified parser for the Fortran namelist format used by PROPAN.
    It extracts the most relevant parameters for the prototype.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PROPAN.INP not found at: {filepath}")

    with open(filepath, "r") as f:
        text = f.read()

    params = {}

    # Comment lines
    comment_match = re.search(
        r"COMMENT\s*=\s*(.+?)(?=\n\s*!|\n\s*[A-Z])", text, re.DOTALL
    )
    if comment_match:
        raw = comment_match.group(1)
        parts = re.findall(r"'([^']*)'", raw)
        params["COMMENT"] = [p for p in parts if p.strip() and p.strip() != "-"]

    # Scalar integer parameters
    for key in ["IP", "IN", "IH", "NB", "JI", "JF", "IROTOR", "NU",
                "NKIT", "MKIT", "IK", "NWA", "NGAP", "NCAV", "NREV",
                "IPAN", "INTE", "MMAX", "IFARP", "ISTRIP", "ISOLVER",
                "IFIELD", "ICP"]:
        m = re.search(rf"{key}\s*=\s*([\d]+)", text)
        if m:
            params[key] = int(m.group(1))

    # UU array (advance ratios)
    uu_match = re.search(r"UU\s*=\s*(.+)", text)
    if uu_match:
        params["UU"] = [float(v.strip()) for v in uu_match.group(1).split(",")]

    # IDENTU array (file identifiers)
    identu_match = re.search(r"IDENTU\s*=\s*(.+)", text)
    if identu_match:
        params["IDENTU"] = re.findall(r"'(\d+)'", identu_match.group(1))

    # Tolerance values
    for key in ["TOLK", "TOLS"]:
        m = re.search(rf"{key}\s*=\s*([^\s,]+)", text)
        if m:
            # Handle Fortran D notation: 1.D-3 -> 1.E-3
            params[key] = float(m.group(1).replace("D", "E").replace("d", "e"))

    # BETA
    m = re.search(r"BETA\s*=\s*([^\s,]+)", text)
    if m:
        params["BETA"] = float(m.group(1))

    return params


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _last_match(pattern: str, block: str):
    """Return the last regex match as a float, or None if not found."""
    matches = re.findall(pattern, block)
    if matches:
        return float(matches[-1])
    return None


def _validate_dataframe(df: pd.DataFrame, filepath: str):
    """Validate the parsed DataFrame for data integrity."""
    if df.empty:
        raise ValueError(f"Parsed DataFrame is empty from {filepath}")

    # Check J values are numeric and reasonable
    if not pd.api.types.is_numeric_dtype(df["J"]):
        raise ValueError("J column is not numeric")

    # Check coefficient columns are numeric
    for col in ["KTP", "KQP", "KTH", "KQH"]:
        if col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0 and not pd.api.types.is_numeric_dtype(non_null):
                raise ValueError(f"{col} column contains non-numeric values")

    # Report parsing summary
    n = len(df)
    j_vals = df["J"].tolist()
    print(f"[Parser] Successfully parsed {n} operating conditions from {filepath}")
    print(f"[Parser] J values: {j_vals}")


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    data_dir = os.path.join(os.path.dirname(__file__), "data", "P4119")
    out_path = os.path.join(data_dir, "PROPAN.OUT")
    inp_path = os.path.join(data_dir, "PROPAN.INP")

    print("=" * 60)
    print("PROPAN Parser — Self Test")
    print("=" * 60)

    # Parse .OUT
    print(f"\nParsing: {out_path}")
    df, panel_info, op_time = parse_propan_out(out_path)
    print(f"\nPanel info: {panel_info}")
    print(f"Operation time: {op_time} minutes")
    print(f"\nParsed DataFrame:\n{df.to_string(index=False)}")

    # Parse .INP
    print(f"\nParsing: {inp_path}")
    params = parse_propan_inp(inp_path)
    for k, v in params.items():
        print(f"  {k}: {v}")

    print("\n[Parser self-test PASSED]")
