"""
patch_propan_for_gfortran.py

Creates a patched copy of the PROPAN source code for gfortran compilation.
Keeps the original external/PROPAN completely untouched.

Changes applied:
1. DISP='DELETE' -> STATUS='SCRATCH' approach (remove named file, use scratch)
   Actually: remove DISP='DELETE' and add STATUS='DELETE' to CLOSE statements
   Simplest correct approach: just remove DISP='DELETE' from OPEN statements
   and add STATUS='DELETE' to corresponding CLOSE statements.
2. CARRIAGECONTROL='FORTRAN' -> removed (gfortran does not support it)
"""
import os
import re
import shutil

SRC = os.path.join("external", "PROPAN", "PROPAN_Source_Code")
DST = os.path.join("build", "src")

def main():
    if not os.path.isdir(SRC):
        print(f"ERROR: Source directory not found: {SRC}")
        return False

    # Clean destination
    if os.path.isdir(DST):
        shutil.rmtree(DST)

    # Copy entire source tree
    shutil.copytree(SRC, DST)
    print(f"Copied source tree to {DST}")

    patches_applied = 0

    # Patch 1: ProPan2025_v1.0.f90 - remove DISP='DELETE' from OPEN statements
    main_prog = os.path.join(DST, "Base", "ProPan2025_v1.0.f90")
    with open(main_prog, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Remove DISP='DELETE', from OPEN statements
    content = content.replace(",DISP='DELETE'", "")

    # Change CLOSE(UNIT=2x) to CLOSE(UNIT=2x,STATUS='DELETE') for units 21-27
    for unit in range(21, 28):
        content = content.replace(
            f"CLOSE(UNIT={unit})",
            f"CLOSE(UNIT={unit},STATUS='DELETE')"
        )

    if content != original:
        with open(main_prog, "w", encoding="utf-8") as f:
            f.write(content)
        patches_applied += 1
        print(f"Patched: {main_prog}")
        print("  - Removed DISP='DELETE' from 7 OPEN statements")
        print("  - Added STATUS='DELETE' to 7 CLOSE statements")

    # Patch 2: progress.f90 - remove CARRIAGECONTROL='FORTRAN'
    progress = os.path.join(DST, "Base", "progress.f90")
    with open(progress, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    content = content.replace(
        "OPEN(UNIT=6,CARRIAGECONTROL='FORTRAN')",
        "! OPEN(UNIT=6,CARRIAGECONTROL='FORTRAN')  ! Removed: gfortran incompatible"
    )

    if content != original:
        with open(progress, "w", encoding="utf-8") as f:
            f.write(content)
        patches_applied += 1
        print(f"Patched: {progress}")
        print("  - Commented out CARRIAGECONTROL='FORTRAN'")

    print(f"\nTotal patches applied: {patches_applied}")
    print("Original source in external/PROPAN is UNTOUCHED.")
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\nSource patching complete. Ready for gfortran build.")
    else:
        print("\nSource patching FAILED.")
