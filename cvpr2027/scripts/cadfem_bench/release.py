"""Build the CADFEM-Bench release end to end (no solver runs, no model calls; reads the existing convergence studies).

  tmp/cq-env/bin/python scripts/cadfem_bench/release.py    # base build -> v1.1 migration -> verification -> docs
  tmp/cq-env/bin/python scripts/cadfem_bench/report.py     # PDF
  tmp/cq-env/bin/python scripts/cadfem_bench/package.py    # dataset folder + zip (+ copy to the SVG root)

Stages: build.py writes the admitted tasks in the v1.0 structure; repair_release.py applies the 2026-10-13 audit
corrections (published references only, held tasks, CADWorld shear-stress definition, workflow artifact contract,
evaluator evidence bundle); assets/ supplies the candidate README, submission schema and review protocol;
apply_bands.py applies the 2026-10-14 convergence-study tolerances (v1.2) and the fcVM buckling admissions (v1.3);
geometry_refs.py (run first) writes the reference solids behind the v1.3 drawing/spec -> CAD geometry gates;
verify.py re-runs the audit probes; card.py writes the dataset card.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile

import apply_bands
import build
import card
import common as C
import geometry_refs
import verify

ASSETS = C.HERE / "assets"


def main() -> None:
    refs = geometry_refs.build_all()      # v1.3: evaluator-only reference solids for the drawing/spec -> CAD tasks
    print(f"geometry references: {len(refs)} (max volume error {max(r['relative_volume_error'] for r in refs.values()):.1e})", flush=True)
    build.main()
    snap = C.ROOT / "tmp/cadfem-bench-v1.1/base-snapshot.zip"
    snap.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(snap, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(C.OUT.rglob("*")):
            if p.is_file():
                z.write(p, str(p.relative_to(C.OUT)))
    subprocess.run([sys.executable, str(C.HERE / "repair_release.py"), "--workspace", str(C.ROOT.parent), "--package", str(C.OUT),
                    "--snapshot", str(snap)], check=True)
    shutil.copy2(ASSETS / "submission.schema.json", C.CAND / "submission.schema.json")
    shutil.copy2(ASSETS / "REVIEW_PROTOCOL.md", C.EVAL / "REVIEW_PROTOCOL.md")
    for f in ("score.py", "prepare_review.py"):
        shutil.copy2(C.HERE / f, C.EVAL / f)
    print("v1.2/v1.3 stage:", apply_bands.apply(), flush=True)
    ts = [json.loads(x) for x in (C.CAND / "tasks.jsonl").read_text().splitlines() if x.strip()]
    tmpl = (ASSETS / "candidate-README.md").read_text()
    (C.CAND / "README.md").write_text(tmpl.replace("{version}", C.VERSION).replace("{n}", str(len(ts)))
                                      .replace("{a}", str(sum(t["track"] == "A" for t in ts))).replace("{b}", str(sum(t["track"] == "B" for t in ts))))
    ver = verify.main()
    C.jdump(ver, C.EVAL / "verification.json")
    val = json.loads((C.EVAL / "validation.json").read_text())
    (C.EVAL / "DATASET_CARD.md").write_text(card.write(val, ver))
    C.META.mkdir(parents=True, exist_ok=True)
    for f in C.META.iterdir():
        f.unlink()
    shutil.copy2(C.EVAL / "DATASET_CARD.md", C.META / "README.md")
    for f in ("tasks.jsonl", "README.md", "submission.schema.json"):
        shutil.copy2(C.CAND / f, C.META / ("CANDIDATE_README.md" if f == "README.md" else f))
    for f in ("references.jsonl", "registry.jsonl", "validation.json", "verification.json", "evidence-manifest.jsonl"):
        shutil.copy2(C.EVAL / f, C.META / f)
    for f in ("tasks.jsonl", "references.jsonl", "excluded-local-targets.jsonl"):
        shutil.copy2(C.OUT / "held" / f, C.META / f"held-{f}")
    print(json.dumps(dict(tasks=val["tasks"], graded_outputs=val["graded_outputs"], held=val["held_tasks"],
                          verification={k: ver[k] for k in ("invalid_cad_files", "evidence_files", "leak_scan_hits")}), indent=1))


if __name__ == "__main__":
    main()
