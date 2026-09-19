import os
import shutil
import subprocess
import time
from pathlib import Path
import pandas as pd
from propan_parser import parse_propan_out
from analysis import get_performance_trends

PROJECT_ROOT = Path(__file__).resolve().parent
SOLVER_EXE = PROJECT_ROOT / "propan_solver" / "propan.exe"
BASE_DATA_DIR = PROJECT_ROOT / "data" / "P4119"

def run_propan_custom_j(j_value: float, timeout_sec: int = 120) -> pd.DataFrame:
    """
    Executes the official compiled PROPAN Fortran solver for a custom advance coefficient J.
    Returns a parsed pandas DataFrame with KT_total, 10KQ_total, eta calculated.
    """
    if not SOLVER_EXE.exists():
        raise FileNotFoundError(f"PROPAN solver executable not found at {SOLVER_EXE}")

    # Format J tag and directory
    j_str = f"{j_value:.4f}".replace('.', '_')
    run_dir = PROJECT_ROOT / "propan_solver" / "runs" / f"run_j_{j_str}_{int(time.time())}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Copy template geometry files
    shutil.copy(BASE_DATA_DIR / "PROPANEL.DAT", run_dir / "PROPANEL.DAT")
    shutil.copy(BASE_DATA_DIR / "WAKE.INP", run_dir / "WAKE.INP")

    # Read base PROPAN.INP template
    with open(BASE_DATA_DIR / "PROPAN.INP", "r") as f:
        inp_content = f.read()

    ident_tag = f"J{int(j_value * 1000):04d}"[:8]

    lines = inp_content.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("NU"):
            new_lines.append("NU         = 1")
        elif line.strip().startswith("IDENTU"):
            new_lines.append(f"IDENTU     = '{ident_tag}'")
        elif line.strip().startswith("UU"):
            new_lines.append(f"UU         = {j_value:.6f}")
        else:
            new_lines.append(line)

    new_inp = "\n".join(new_lines) + "\n"
    with open(run_dir / "PROPAN.INP", "w") as f:
        f.write(new_inp)

    # Set environment for MinGW DLLs (if specified in env or exists locally)
    env = os.environ.copy()
    mingw_bin = os.environ.get("MINGW_BIN")
    if not mingw_bin and Path(r"D:\mingw64\bin").exists():
        mingw_bin = r"D:\mingw64\bin"
        
    if mingw_bin:
        env["PATH"] = str(mingw_bin) + ";" + env.get("PATH", "")


    # Execute PROPAN solver
    res = subprocess.run(
        [str(SOLVER_EXE)],
        cwd=run_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec
    )

    out_file = run_dir / "PROPAN.OUT"
    if not out_file.exists():
        raise RuntimeError(
            f"PROPAN.exe exited with code {res.returncode} but did not produce PROPAN.OUT.\n"
            f"Stdout: {res.stdout}\nStderr: {res.stderr}"
        )

    df, panel_info, op_time = parse_propan_out(out_file)
    df_calc = get_performance_trends(df)
    return df_calc

if __name__ == "__main__":
    for test_j in [0.651, 0.712, 0.781, 0.7137]:
        print(f"\nTesting propan_runner with arbitrary custom J = {test_j}...")
        df_result = run_propan_custom_j(test_j)
        print(f"Calculated performance result for custom J = {test_j}:")
        print(df_result.to_string(index=False))

