"""Assemble the complete CADFEM-Bench dataset folder and zip it (run after release.py and report.py).

  output/datasets/cadfem-bench-v<version>/
    README.md            dataset card + folder layout + quick start
    SHA256SUMS.txt       hash of every file in the folder
    candidate/           give to the model: tasks.jsonl, tasks/<task_id>/ inputs, README.md, submission.schema.json
    evaluator/           keep hidden: references.jsonl, registry.jsonl, score.py, validation.json, DATASET_CARD.md
    report/              cadfem-bench-v<version>.pdf
    scripts/cadfem_bench builder, adapters, grader, report generator
  output/datasets/cadfem-bench-v<version>.zip
"""
from __future__ import annotations

import shutil
import zipfile

import common as C

PDF = C.ROOT / f"output/pdf/{C.OUT.name}.pdf"
ZIP = C.OUT.parent / f"{C.OUT.name}.zip"

LAYOUT = """
## Folder layout

| path | contents | who sees it |
|---|---|---|
| `candidate/tasks.jsonl` | active tasks: prompt, input files, output keys and units, required artifacts, source and licence | model |
| `candidate/tasks/<task_id>/` | CAD (STEP/BREP/.geo), `faces.json` face descriptors, drawings, boundary-condition figures, property tables | model |
| `candidate/README.md`, `candidate/submission.schema.json` | artifact contract and answer format | model |
| `evaluator/references.jsonl` | hidden reference values, tolerances, provenance, evidence file list, flags | evaluator only |
| `evaluator/evidence/`, `evaluator/evidence-manifest.jsonl` | original source files behind every reference, with SHA-256 and original location | evaluator only |
| `evaluator/score.py`, `evaluator/prepare_review.py`, `evaluator/REVIEW_PROTOCOL.md` | scorer (never runs candidate code), review template tool, trusted-review protocol | evaluator only |
| `evaluator/registry.jsonl`, `validation.json`, `verification.json`, `task-hashes.json` | source registry with blockers, release counts, build-time verification, task hashes | evaluator only |
| `held/` | held tasks with their inputs and reasons; `excluded-local-targets.jsonl` lists the 190 removed v1.0 targets | evaluator only |
| `report/<release>.pdf` | composition, audit corrections, verification, one page per engineering family | everyone |
| `scripts/cadfem_bench/` | builder: `release.py` (build.py -> repair_release.py -> apply_bands.py -> verify.py -> card.py), `report.py`, `package.py` | maintainers |
| `SHA256SUMS.txt` | SHA-256 of every file | everyone |

## Quick start

1. Give a model only `candidate/` (or one `candidate/tasks/<task_id>/` folder plus its line of `tasks.jsonl`).
2. Collect `runs/<model>/<task_id>/` with the eight artifacts listed in `candidate/README.md`.
3. For each task you review, create a template with `python evaluator/prepare_review.py --tasks candidate/tasks.jsonl --task-id <id> --submissions runs/<model> --run-id <run> --out reviews/<id>.jsonl`, follow `evaluator/REVIEW_PROTOCOL.md`, and concatenate the reviews.
4. Score: `python evaluator/score.py --refs evaluator/references.jsonl --tasks candidate/tasks.jsonl --submissions runs/<model> --run-id <run> --reviews reviews.jsonl --out score.json`. Without reviews you get numerical accuracy only (`numerical_passed`); `passed` needs a review.

The builder scripts read the original source collections under `cvpr2027/data` and `cvpr2027/tmp`; they are included for provenance and are not needed to run the benchmark.
"""

LAYOUT_SUITES = """
## Folder layout

| path | contents | who sees it |
|---|---|---|
| `candidate/` | primary suite only: `tasks.jsonl`, `tasks/<task_id>/` inputs, `README.md` (artifact contract), `submission.schema.json` | model |
| `evaluator/references.jsonl`, `evaluator/score.py` | primary-suite hidden references and the scorer (never runs candidate code; reports the release version) | evaluator only |
| `evaluator/suites/<suite>/` | `tasks.jsonl`, `references.jsonl` and inputs of `primary`, `calibration`, `reserved-public`, `related-public`; score each suite separately with its own files | evaluator only |
| `evaluator/task-pool/` | the full v1.3 source-backed pool with its card and report | evaluator only |
| `evaluator/sandbox_runner.py`, `evaluation-protocol.json`, `runtime-lock.json`, `requirements-runtime.txt` | offline replay of a submitted `main.py` and the common run protocol | evaluator only |
| `evaluator/verify_static_fields.py`, `evaluator/runtime-validation/` | cycloidal field-equilibrium checker; sandbox denial, timeout and solver-baseline records | evaluator only |
| `evaluator/evidence/`, `evidence-manifest.jsonl` | original source files behind every reference, with SHA-256 | evaluator only |
| `evaluator/source-review/` | collected sources still under review (not tasks) | evaluator only |
| `evaluator/registry.jsonl`, `validation.json`, `verification.json`, `suite-manifest.json`, `task-hashes.json`, `limitations-status.json` | source registry, release counts, build-time verification, suite policy, task hashes, open limitations | evaluator only |
| `held/` | held tasks with their inputs and reasons; `excluded-local-targets.jsonl` lists the 190 removed v1.0 targets | evaluator only |
| `report/<release>.pdf` | composition, suites, verification, one page per engineering family | everyone |
| `scripts/cadfem_bench/` | builders: `release.py` (full pool), `release_v14.py` + `suites.py` (suites), `finish_v14.py` (verification, report, package) | maintainers |
| `SHA256SUMS.txt` | SHA-256 of every file | everyone |
"""


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy-to", help="also copy the folder and zip into this directory (refuses to overwrite)")
    a = ap.parse_args()
    assert (C.CAND / "tasks.jsonl").exists() and (C.EVAL / "references.jsonl").exists(), "run build.py first"
    assert PDF.exists(), "run report.py first"
    for cache in C.OUT.rglob("__pycache__"):
        shutil.rmtree(cache)
    for sub in ("report", "scripts"):
        if (C.OUT / sub).exists():
            shutil.rmtree(C.OUT / sub)
    (C.OUT / "report").mkdir(parents=True)
    shutil.copy2(PDF, C.OUT / "report" / PDF.name)
    dst = C.OUT / "scripts/cadfem_bench"
    dst.mkdir(parents=True)
    for f in sorted(C.HERE.glob("*.py")):
        shutil.copy2(f, dst / f.name)
    shutil.copytree(C.HERE / "assets", dst / "assets")
    card = (C.EVAL / "DATASET_CARD.md").read_text()
    (C.OUT / "README.md").write_text(card.rstrip() + "\n" + (LAYOUT_SUITES if (C.EVAL / "suites").exists() else LAYOUT))
    files = sorted(p for p in C.OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt" and "__pycache__" not in p.parts)
    (C.OUT / "SHA256SUMS.txt").write_text("".join(f"{C.sha256(p)}  {p.relative_to(C.OUT)}\n" for p in files))
    files.append(C.OUT / "SHA256SUMS.txt")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, f"{C.OUT.name}/{p.relative_to(C.OUT)}")
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names)) == len(files)
        sums = z.read(f"{C.OUT.name}/SHA256SUMS.txt").decode().splitlines()
        assert len(sums) == len(files) - 1
    size = sum(p.stat().st_size for p in files)
    print(f"folder {C.OUT}  files {len(files)}  {size / 1e6:.1f} MB")
    print(f"zip    {ZIP}  {ZIP.stat().st_size / 1e6:.1f} MB  sha256 {C.sha256(ZIP)}")
    if a.copy_to:
        from pathlib import Path
        dest = Path(a.copy_to)
        assert not (dest / C.OUT.name).exists() and not (dest / ZIP.name).exists(), "destination exists; refusing to overwrite"
        shutil.copytree(C.OUT, dest / C.OUT.name)
        shutil.copy2(ZIP, dest / ZIP.name)
        print(f"copied to {dest / C.OUT.name} and {dest / ZIP.name}")


if __name__ == "__main__":
    main()
