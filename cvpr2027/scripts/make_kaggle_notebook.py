"""Adapt a built Colab distillation notebook for Kaggle (GPU T4 x2, internet on).

All /content/cad_distill paths (also baked into the data bundle) are redirected through a symlink to
/kaggle/working/cad_distill, so results persist as Kaggle notebook output; the results ZIP is written to
/kaggle/working, downloadable from the notebook's Output tab or with `kaggle kernels output`.

  python make_kaggle_notebook.py SOURCE.ipynb OUT.ipynb [BUNDLE_DIR]   (BUNDLE_DIR: externalize the data as a Kaggle dataset)
"""
import json
from pathlib import Path
import sys

SETUP = """#@title Kaggle: keep everything under /kaggle/working (the bundle's /content paths point here)
import os
# One GPU only: the recipe is single-GPU (effective batch 4). With T4 x2 visible, the HF Trainer wraps the 4-bit
# model in DataParallel (effective batch 8, 634 steps) and bitsandbytes crashes with an illegal memory access.
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
from pathlib import Path
work = Path('/kaggle/working/cad_distill'); work.mkdir(parents=True, exist_ok=True)
Path('/content').mkdir(exist_ok=True)
link = Path('/content/cad_distill')
if not link.exists(): link.symlink_to(work)
print('outputs ->', link.resolve())"""

EXPORT = """import zipfile
for v in VARIANTS:
    run = ROOT/f'results-{v}'
    archive = Path(f'/kaggle/working/cad-distill-{v}-results.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in run.rglob('*'):
            if f.is_file() and 'checkpoints' not in f.parts: z.write(f, f.relative_to(run))
    print('Saved', archive, archive.stat().st_size, 'bytes')"""

NOTE = ("**Kaggle:** Settings -> Accelerator **GPU T4 x2**, Internet **On** (phone-verified account), then "
        "**Save Version -> Save & Run All (Commit)**; the run continues after you close the tab (about 7-8 h on "
        "a T4, under Kaggle's 12 h limit). When it finishes, download `cad-distill-<variant>-results.zip` from the "
        "version's **Output** tab.\n\n")


FROM_DATASET = """#@title Unpack data, scripts and test reference STEP files (from the attached Kaggle dataset)
import hashlib, io, json, tarfile
from pathlib import Path
source = next(Path('/kaggle/input').rglob('cad-distill-bundle.bin'))
bundle = source.read_bytes()
assert hashlib.sha256(bundle).hexdigest() == "{sha}", 'bundle differs from the built notebook'
ROOT = Path('/content/cad_distill'); ROOT.mkdir(exist_ok=True)
tarfile.open(fileobj=io.BytesIO(bundle), mode='r:gz').extractall(ROOT)
for v in ['template', 'distill', 'distill-ref']:
    m = json.loads((ROOT/'data'/v/'manifest.json').read_text())
    print(v, m['counts']['train'], m.get('acceptance'), m.get('teacher_audit'))"""


def externalize_bundle(cells: list, bundle_dir: Path) -> str:
    """Move the embedded base64 bundle into bundle_dir (a Kaggle dataset); notebooks over ~1 MB are rejected."""
    import base64
    import hashlib
    import re
    unpack = [c for c in cells if 'encoded = """' in "".join(c["source"])]
    assert len(unpack) == 1, "unpack cell not found"
    text = "".join(unpack[0]["source"])
    payload = base64.b64decode(text.split('"""')[1])
    sha = hashlib.sha256(payload).hexdigest()
    assert sha == re.search(r'== "([0-9a-f]{64})"', text).group(1)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "cad-distill-bundle.bin").write_bytes(payload)
    unpack[0]["source"] = FROM_DATASET.replace("{sha}", sha).splitlines(True)
    return sha


def main() -> None:
    source, out = Path(sys.argv[1]), Path(sys.argv[2])
    nb = json.loads(source.read_text())
    cells = nb["cells"]
    if len(sys.argv) > 3:
        print("bundle sha256", externalize_bundle(cells, Path(sys.argv[3])))
    cells[0]["source"] = [NOTE] + cells[0]["source"]
    cells.insert(1, dict(cell_type="code", execution_count=None, outputs=[], metadata={},
                         source=SETUP.splitlines(True)))
    exports = [c for c in cells if "BEGIN-RESULTS" in "".join(c["source"])]
    assert len(exports) == 1, "export cell not found"
    exports[0]["source"] = EXPORT.splitlines(True)
    for cell in cells:
        if cell["cell_type"] == "markdown" and "Save results into this notebook" in "".join(cell["source"]):
            cell["source"] = ["## Save results\n\nWrites `cad-distill-<variant>-results.zip` (everything except "
                              "training checkpoints, adapter weights included) to /kaggle/working for the Output tab."]
    nb["metadata"].pop("colab", None)
    nb["metadata"]["kaggle"] = dict(accelerator="nvidiaTeslaT4", isInternetEnabled=True, isGpuEnabled=True)
    out.write_text(json.dumps(nb, indent=1) + "\n")
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
