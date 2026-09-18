import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GFORTRAN = os.environ.get("GFORTRAN", "gfortran")
SRC_ROOT = PROJECT_ROOT / "external" / "PROPAN" / "PROPAN_Source_Code"
BUILD_DIR = PROJECT_ROOT / "propan_solver" / "build"
PATCH_DIR = PROJECT_ROOT / "propan_solver" / "patched_src"
OUT_EXE = PROJECT_ROOT / "propan_solver" / "propan.exe"

BUILD_DIR.mkdir(parents=True, exist_ok=True)
PATCH_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = [
    # Base
    "Base/propan_mod.f90",
    "Base/ProPan2025_v1.0.f90",
    "Base/progress.f90",
    "Base/input.f90",
    "Base/inivars.f90",
    "Base/delvars.f90",
    "Base/counters.f90",
    "Base/output.f90",
    # Geom
    "Geom/bladegeom.f90",
    "Geom/bladewakegeom.f90",
    "Geom/nozzlegeom.f90",
    "Geom/nozzlewakegeom.f90",
    "Geom/hubgeom.f90",
    "Geom/panel.f90",
    "Geom/pancoor.f90",
    # Numdif
    "Numdif/numdifblade.f90",
    "Numdif/numdifbladewake.f90",
    "Numdif/numdifnozzle.f90",
    "Numdif/numdifhub.f90",
    # InfCoef
    "InfCoef/InfCoefMatrixStd.f90",
    "InfCoef/InfCoefMatrixUnStd.f90",
    # PotCoef
    "InfCoef/PotCoef/bladecoef.f90",
    "InfCoef/PotCoef/bladewakecoef.f90",
    "InfCoef/PotCoef/nozzlecoef.f90",
    "InfCoef/PotCoef/nozzlewakecoef.f90",
    "InfCoef/PotCoef/hubcoef.f90",
    "InfCoef/PotCoef/potpan.f90",
    "InfCoef/PotCoef/potpan_num.f90",
    "InfCoef/PotCoef/potlinsub.f90",
    # VelCoef
    "InfCoef/VelCoef/bladevelo.f90",
    "InfCoef/VelCoef/bladewakevelo.f90",
    "InfCoef/VelCoef/nozzlevelo.f90",
    "InfCoef/VelCoef/nozzlewakevelo.f90",
    "InfCoef/VelCoef/hubvelo.f90",
    "InfCoef/VelCoef/imagehubvelo.f90",
    "InfCoef/VelCoef/velpan.f90",
    "InfCoef/VelCoef/gaussvel.f90",
    # Solve
    "Solve/SolveRhsWet.f90",
    "Solve/SolveRhsCav.f90",
    "Solve/SolveRhsCavRed.f90",
    "Solve/SolveLkWet.f90",
    "Solve/SolveLkCav.f90",
    "Solve/SolveIpkcWet.f90",
    "Solve/SolveIpkcCav.f90",
    "Solve/SolveWake.f90",
    # WakeAlign
    "WakeAlign/wakealign1.f90",
    r"D:\PROPAN_AI_Prototype\propan_solver\stubs\wakealign2.f90",  # stub
    "WakeAlign/nozzledef.f90",
    "WakeAlign/geoduct37.f90",
    "WakeAlign/bladewakedisp.f90",
    "WakeAlign/nozzledisp.f90",
    "WakeAlign/nozzlewakedisp.f90",
    "WakeAlign/ff.f90",
    # Cav
    "Cav/cavcheck.f90",
    "Cav/cavprop.f90",
    "Cav/caverrc.f90",
    "Cav/cavpotp.f90",
    "Cav/cavpots.f90",
    "Cav/cavthickp.f90",
    "Cav/cavthicks.f90",
    "Cav/cavrecover.f90",
    # VtCp
    "VtCp/velp.f90",
    "VtCp/velpw.f90",
    "VtCp/presp.f90",
    "VtCp/veln.f90",
    "VtCp/presn.f90",
    "VtCp/presnte.f90",
    "VtCp/velh.f90",
    "VtCp/presh.f90",
    # Wake
    "Calc/Wake/vwake.f90",
    "Calc/Wake/fourier_coef.f90",
    "Calc/Wake/fourier_function.f90",
    # Grids
    "Grids/hubgrid.f90",
    "Grids/nozzlegrid.f90",
    "Grids/nozzlewakegrid.f90",
    # Grape
    "Grids/Grape/angri.f90",
    "Grids/Grape/bord.f90",
    "Grids/Grape/calcb.f90",
    "Grids/Grape/calphi.f90",
    "Grids/Grape/coef.f90",
    "Grids/Grape/grape.f90",
    "Grids/Grape/guessa.f90",
    "Grids/Grape/rhs.f90",
    "Grids/Grape/sip.f90",
    "Grids/Grape/splin.f90",
    # Field
    "Field/bladecoeff.f90",
    "Field/bladewakecoeff.f90",
    "Field/hubcoeff.f90",
    "Field/nozzlecoeff.f90",
    "Field/nozzlewakecoeff.f90",
    "Field/velfStd.f90",
    "Field/velfUnStd.f90",
    "Field/presfStd.f90",
    "Field/presfUnStd.f90",
    # Calc
    "Calc/JacobianWet.f90",
    "Calc/JacobianCav.f90",
    "Calc/linint.f90",
    "Calc/intk1.f90",
    "Calc/splint.f90",
    "Calc/spline.f90",
    "Calc/ispline.f90",
    "Calc/gaussint.f90",
    "Calc/bisof.f",
    "Calc/CtCq.f90",
    "Calc/gaperrg.f90",
    "Calc/periodicflow.f90",
    "Calc/velinf.f90",
    "Calc/stret2.f90",
    "Calc/sxx.f90",
    "Calc/shxx.f90",
    "Calc/sdiv.f90",
    "Calc/frame.f90",
    # Linpack
    "Linpack/cubspl.f",
    "Linpack/daxpy.f",
    "Linpack/dcopy.f",
    "Linpack/ddot.f",
    "Linpack/dgedi.f",
    "Linpack/dgefa.f",
    "Linpack/dgemm.f",
    "Linpack/dger.f",
    "Linpack/dgesl.f",
    "Linpack/drotm.f",
    "Linpack/drotmg.f",
    "Linpack/dscal.f",
    "Linpack/dsort.f",
    "Linpack/dswap.f",
    "Linpack/dtrsv.f",
    "Linpack/fdump.f",
    "Linpack/i1mach.f",
    "Linpack/idamax.f",
    "Linpack/interv.f",
    "Linpack/j4save.f",
    "Linpack/lsame.f",
    "Linpack/ppvalu.f",
    "Linpack/xerbla.f",
    "Linpack/xercnt.f",
    "Linpack/xerhlt.f",
    "Linpack/xermsg.f",
    "Linpack/xerprn.f",
    "Linpack/xersve.f",
    "Linpack/xgetua.f",
    # IMSL
    "IMSL/c1dim.f",
    "IMSL/c1iarg.f",
    "IMSL/c1ind.f",
    "IMSL/c1tci.f",
    "IMSL/c1tic.f",
    "IMSL/c12ile.f",
    "IMSL/da1ot.f",
    "IMSL/dc1r.f",
    "IMSL/dc1trg.f",
    "IMSL/dc1wfr.f",
    "IMSL/dcsfrg.f",
    "IMSL/df2lsq.f",
    "IMSL/dfnlsq.f",
    "IMSL/dgirts.f",
    "IMSL/difnan.f",
    "IMSL/dmach.f",
    "IMSL/dr2ivn.f",
    "IMSL/dr3ivn.f",
    "IMSL/dset.f",
    "IMSL/dxyz.f",
    "IMSL/e1init.f",
    "IMSL/e1inpl.f",
    "IMSL/e1mes.f",
    "IMSL/e1pop.f",
    "IMSL/e1pos.f",
    "IMSL/e1prt.f",
    "IMSL/e1psh.f",
    "IMSL/e1std.f",
    "IMSL/e1sti.f",
    "IMSL/e1stl.f",
    "IMSL/e1ucs.f",
    "IMSL/e1usr.f",
    "IMSL/e3prt.f",
    "IMSL/i1cstr.f",
    "IMSL/i1dx.f",
    "IMSL/i1erif.f",
    "IMSL/i1kgt.f",
    "IMSL/i1kqu.f",
    "IMSL/i1krl.f",
    "IMSL/i1kst.f",
    "IMSL/i1x.f",
    "IMSL/iachar.f",
    "IMSL/icase.f",
    "IMSL/idanan.f",
    "IMSL/imach.f",
    "IMSL/iwkin.f",
    "IMSL/m1ve.f",
    "IMSL/m1vech.f",
    "IMSL/n1rcd.f",
    "IMSL/n1rgb.f",
    "IMSL/n1rty.f",
    "IMSL/s1anum.f",
    "IMSL/umach.f",
]

def get_patched_file(src_path: Path) -> Path:
    with open(src_path, "r", encoding="latin-1") as f:
        content = f.read()

    patched = False
    if "DISP='DELETE'" in content:
        content = content.replace(",DISP='DELETE',STATUS='NEW'", ",STATUS='REPLACE'")
        content = content.replace(",DISP='DELETE'", "")
        patched = True
    if "CARRIAGECONTROL='FORTRAN'" in content or "CLOSE(UNIT=6)" in content:
        content = content.replace("OPEN(UNIT=6,CARRIAGECONTROL='FORTRAN')", "! OPEN(UNIT=6)")
        content = content.replace("CLOSE(UNIT=6)", "! CLOSE(UNIT=6)")
        patched = True
    if "flag == .false." in content:
        content = content.replace("flag == .false.", ".not. flag")
        patched = True
    if "DCPG=0.D0" in content:
        content = content.replace("DCPG=0.D0", "IF (ALLOCATED(DCPG)) DCPG=0.D0")
        patched = True

    if src_path.name == "ProPan2025_v1.0.f90":
        content = content.replace("CALL CPU_TIME(TIME1)", "CALL CPU_TIME(TIME1)\nWRITE(*,*) 'TRACE: START PROPAN'")
        content = content.replace("CALL INPUT(10)", "WRITE(*,*) 'TRACE: BEFORE INPUT(10)'\nCALL INPUT(10)\nWRITE(*,*) 'TRACE: AFTER INPUT(10)'")
        content = content.replace("CALL INPUT(11)", "WRITE(*,*) 'TRACE: BEFORE INPUT(11)'\nCALL INPUT(11)\nWRITE(*,*) 'TRACE: AFTER INPUT(11)'")
        content = content.replace("CALL INPUT(12)", "WRITE(*,*) 'TRACE: BEFORE INPUT(12)'\nCALL INPUT(12)\nWRITE(*,*) 'TRACE: AFTER INPUT(12)'")
        content = content.replace("CALL INPUT(13)", "WRITE(*,*) 'TRACE: BEFORE INPUT(13)'\nCALL INPUT(13)\nWRITE(*,*) 'TRACE: AFTER INPUT(13)'")
        content = content.replace("CALL COUNTERS", "WRITE(*,*) 'TRACE: BEFORE COUNTERS'\nCALL COUNTERS\nWRITE(*,*) 'TRACE: AFTER COUNTERS'")
        content = content.replace("CALL INIVARS", "WRITE(*,*) 'TRACE: BEFORE INIVARS'\nCALL INIVARS\nWRITE(*,*) 'TRACE: AFTER INIVARS'")
        patched = True

    if patched:
        out_path = PATCH_DIR / src_path.name
        with open(out_path, "w", encoding="latin-1") as f:
            f.write(content)
        return out_path
    return src_path

def main():
    obj_files = []
    print(f"Compiling {len(SOURCES)} source files...")
    
    for idx, rel_path in enumerate(SOURCES):
        if os.path.isabs(rel_path):
            src_path = Path(rel_path)
        else:
            src_path = SRC_ROOT / rel_path
            
        if not src_path.exists():
            print(f"ERROR: Source file not found: {src_path}")
            sys.exit(1)
            
        real_src = get_patched_file(src_path)
        
        obj_name = f"obj_{idx:03d}_{src_path.stem}.o"
        obj_path = BUILD_DIR / obj_name
        obj_files.append(obj_path)
        
        flags = ["-c", "-O2", "-fno-automatic", "-J", str(BUILD_DIR)]
        if real_src.suffix.lower() == ".f":
            flags.extend(["-std=legacy", "-fallow-argument-mismatch", "-w"])
        else:
            flags.extend(["-fallow-argument-mismatch", "-w"])
            
        cmd = [GFORTRAN] + flags + [str(real_src), "-o", str(obj_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FAILED: {src_path.name}")
            print(res.stderr)
            sys.exit(1)
            
    print(f"Successfully compiled all {len(obj_files)} object files. Linking executable...")
    link_cmd = [GFORTRAN, "-O2", "-Wl,--stack,268435456"] + [str(o) for o in obj_files] + ["-o", str(OUT_EXE)]
    res = subprocess.run(link_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("LINK FAILED:")
        print(res.stderr)
        sys.exit(1)
        
    print(f"SUCCESS! Executable built at: {OUT_EXE}")

if __name__ == "__main__":
    main()
