"""Smoke test: run the whole pipeline on data/sample and check the outputs.

    python tests/smoke_test.py

Takes ~40 s. Writes to a temp folder, not results/.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"


def main():
    if not (SAMPLE / "K.txt").is_file():
        print(f"SKIP: sample data not found in {SAMPLE}")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "smoke"
        proc = subprocess.run([sys.executable, "run.py", "--images", str(SAMPLE), "--out", str(out)],
                              cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout[-2000:], proc.stderr[-2000:])
            print(f"FAIL: run.py exited with {proc.returncode}")
            return 1

        # --- Output files exist ---
        for name in ["sparse.ply", "sparse_clean.ply", "turntable.gif", "metrics.json"]:
            assert (out / name).stat().st_size > 0, f"missing or empty: {name}"

        # --- Numbers are sane (sample normally gives 11/11, ~15k points, ~0.23 px) ---
        m = json.loads((out / "metrics.json").read_text())
        assert m["images_registered"] >= 9, f"only {m['images_registered']} images registered"
        assert m["points3d_clean"] >= 5000, f"only {m['points3d_clean']} points"
        assert m["mean_reprojection_error_px"] < 1.0, f"reprojection error {m['mean_reprojection_error_px']} px"

    print(f"PASS: {m['images_registered']}/{m['images_total']} registered, {m['points3d_clean']} points, "
          f"{m['mean_reprojection_error_px']} px, {m['runtime_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
