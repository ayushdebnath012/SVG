"""Assemble the complete CADFEM-Bench v1 dataset folder and zip it (run after build.py and report.py).

  output/datasets/cadfem-bench-v1/
    README.md            dataset card + folder layout + quick start
    SHA256SUMS.txt       hash of every file in the folder
    candidate/           give to the model: tasks.jsonl, tasks/<task_id>/ inputs, README.md, submission.schema.json
    evaluator/           keep hidden: references.jsonl, registry.jsonl, score.py, validation.json, DATASET_CARD.md
    report/              cadfem-bench-v1.pdf
    scripts/cadfem_bench builder, adapters, grader, report generator
  output/datasets/cadfem-bench-v1.zip
"""
from __future__ import annotations

import shutil
import zipfile

import common as C

PDF = C.ROOT / "output/pdf/cadfem-bench-v1.pdf"
ZIP = C.OUT.parent / "cadfem-bench-v1.zip"

LAYOUT = """
## Folder layout

| path | contents | who sees it |
|---|---|---|
| `candidate/tasks.jsonl` | one task per line: prompt, input files, output keys and units, source and licence | model |
| `candidate/tasks/<task_id>/` | CAD (STEP/BREP), `faces.json` face descriptors, drawings, boundary-condition figures, property tables | model |
| `candidate/README.md`, `candidate/submission.schema.json` | rules and answer format | model |
| `evaluator/references.jsonl` | hidden reference values, tolerances, provenance, flags | grader only |
| `evaluator/registry.jsonl` | every collected source: admitted / held / excluded with its blocker | grader only |
| `evaluator/score.py` | grader (numeric outputs, track B geometry check, SimJEB verdict merge) | grader only |
| `evaluator/validation.json` | build checks: hashes, leak scan, grader self-test | grader only |
| `report/cadfem-bench-v1.pdf` | composition, policies, one page per family, source registry | everyone |
| `scripts/cadfem_bench/` | builder (`build.py`, one `fam_*.py` per source family), `report.py`, `package.py` | maintainers |
| `SHA256SUMS.txt` | SHA-256 of every file | everyone |

## Quick start

1. Give a model only `candidate/` (or one `candidate/tasks/<task_id>/` folder plus its line of `tasks.jsonl`).
2. Collect answers as `runs/<model>/<task_id>/results.json` = `{"outputs": {key: value}}`; tracks B and C also `part.step`.
3. Track C: run `python scripts/simjeb_bench.py evaluate --family <design|redesign|lighten> --id <simjeb id> --step part.step --results results.jsonl --model <model>` from the project (needs the SimJEB CAD and the FEniCSx environment).
4. Score: `python evaluator/score.py --refs evaluator/references.jsonl --submissions runs/<model> --simjeb-results results.jsonl --out score.json`.

The builder scripts read the original source collections under `cvpr2027/data` and `cvpr2027/tmp`; they are included for provenance and are not needed to run the benchmark.
"""


def main() -> None:
    assert (C.CAND / "tasks.jsonl").exists() and (C.EVAL / "references.jsonl").exists(), "run build.py first"
    assert PDF.exists(), "run report.py first"
    for sub in ("report", "scripts"):
        if (C.OUT / sub).exists():
            shutil.rmtree(C.OUT / sub)
    (C.OUT / "report").mkdir(parents=True)
    shutil.copy2(PDF, C.OUT / "report" / PDF.name)
    dst = C.OUT / "scripts/cadfem_bench"
    dst.mkdir(parents=True)
    for f in sorted(C.HERE.glob("*.py")):
        shutil.copy2(f, dst / f.name)
    card = (C.EVAL / "DATASET_CARD.md").read_text()
    (C.OUT / "README.md").write_text(card.rstrip() + "\n" + LAYOUT)
    files = sorted(p for p in C.OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt" and "__pycache__" not in p.parts)
    (C.OUT / "SHA256SUMS.txt").write_text("".join(f"{C.sha256(p)}  {p.relative_to(C.OUT)}\n" for p in files))
    files.append(C.OUT / "SHA256SUMS.txt")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, f"cadfem-bench-v1/{p.relative_to(C.OUT)}")
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) == len(files)
        sums = z.read("cadfem-bench-v1/SHA256SUMS.txt").decode().splitlines()
        assert len(sums) == len(files) - 1
    size = sum(p.stat().st_size for p in files)
    print(f"folder {C.OUT}  files {len(files)}  {size / 1e6:.1f} MB")
    print(f"zip    {ZIP}  {ZIP.stat().st_size / 1e6:.1f} MB  sha256 {C.sha256(ZIP)}")


if __name__ == "__main__":
    main()
