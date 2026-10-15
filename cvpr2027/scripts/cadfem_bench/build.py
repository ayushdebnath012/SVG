"""Base stage of CADFEM-Bench: tasks, references and registry from every admitted source (v1.0 structure).

release.py then applies the v1.1 audit corrections (repair_release.py), verifies and writes the docs.

  tmp/cq-env/bin/python scripts/cadfem_bench/build.py     # tasks, references, registry, validation
  tmp/cq-env/bin/python scripts/cadfem_bench/report.py    # PDF
  tmp/cq-env/bin/python scripts/cadfem_bench/package.py   # complete dataset folder + cadfem-bench-v1.zip

Outputs
  output/datasets/cadfem-bench-v1/candidate/   model-visible: tasks.jsonl, tasks/<id>/ inputs, README.md, submission schema
  output/datasets/cadfem-bench-v1/evaluator/   hidden: references.jsonl, registry.jsonl, score.py, validation.json
  data/cadfem-bench-v1/                        committable copy of the metadata (no CAD)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict

import common as C
import fam_agentfem
import fam_cadworld
import fam_calib
import fam_cycloidal
import fam_fcvm
import fam_geopinonet
import fam_modal
import fam_rigging
import fam_simjeb
import fam_valve
import registry

FAMILIES = [fam_simjeb, fam_agentfem, fam_geopinonet, fam_modal, fam_cycloidal, fam_cadworld, fam_calib, fam_valve, fam_rigging, fam_fcvm]


def leak_scan(tasks: list, refs: list) -> list:
    """Reference numbers must not appear in prompts or in text inputs."""
    hits = []
    for t, e in zip(tasks, refs):
        texts = [t["prompt"]] + [(C.CAND / i["path"]).read_text(errors="ignore") for i in t["inputs"]
                                 if i["path"].endswith((".json", ".md", ".txt", ".csv", ".fee"))]
        blob = "\n".join(texts)
        for k, r in e["references"].items():
            v = r["value"]
            if isinstance(v, bool) or v == 0:
                continue
            for s in {f"{v:.4g}", f"{v:.5g}", f"{v:.6g}"}:
                if len(s.replace(".", "").replace("-", "").lstrip("0")) >= 4 and re.search(rf"(?<![\d.]){re.escape(s)}(?!\d)", blob):
                    hits.append(dict(task_id=t["task_id"], key=k, value=s))
    return hits


def oracle(refs: list, root, scale: float) -> None:
    for e in refs:
        if e["grader"] != "numeric":
            continue
        outs = {}
        for k, r in e["references"].items():
            v = r["value"]
            if isinstance(v, bool):
                outs[k] = v if scale == 1.0 else (not v)
            else:
                off = r["tol"].get("offset", 0.0)
                outs[k] = off + (v - off) * scale
        p = root / e["task_id"] / "results.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(outputs=outs)))


def readme_candidate(tasks: list) -> str:
    by = Counter((t["track"], t["tier"]) for t in tasks)
    fam = Counter(t["family"] for t in tasks)
    lines = [f"# CADFEM-Bench v{C.VERSION}: CAD + FEM engineering tasks (candidate package)", "",
             f"{len(tasks)} tasks. Each line of `tasks.jsonl` is one task: `prompt`, `inputs` (files under `tasks/<task_id>/`),",
             "`outputs` (keys, units, definitions). Answers go to `<task_id>/results.json` as `{\"outputs\": {key: value}}`;",
             "tracks B and C also submit `part.step` and the script that built it.", "", "## Tracks", ""]
    lines += [f"- **{k}**: {v}" for k, v in C.TRACKS.items()]
    lines += ["", "## Task counts", "", "| track | tier | tasks |", "|---|---|---:|"]
    lines += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(by.items())]
    lines += ["", "| family | tasks |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in sorted(fam.items())]
    lines += ["", "## Rules", "",
              "- Use only the files of the task you are solving; do not look up the source online (sources are public).",
              "- Compute answers with your own CAD and FEM workflow; report the requested quantities in the stated units.",
              "- Face numbers in `faces.json` follow OpenCASCADE's face order of the supplied STEP/BREP; the geometric",
              "  descriptors (type, area, centroid, normal/axis) identify the same faces in any CAD system.",
              "- Licences differ per source (see each task's `source`); some sources are local-research-only.", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    if C.OUT.exists():
        shutil.rmtree(C.OUT)
    tasks, refs = [], []
    for m in FAMILIES:
        rows = m.build()
        print(f"{m.__name__}: {len(rows)} tasks", flush=True)
        for t, e in rows:
            tasks.append(t)
            refs.append(e)
    ids = [t["task_id"] for t in tasks]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    assert not dup, dup
    for t in tasks:
        for i in t["inputs"]:
            p = C.CAND / i["path"]
            assert p.exists() and C.sha256(p) == i["sha256"], i
    fam_count = Counter(t["family"] for t in tasks)
    reg = []
    for rid, path, title, status, fams, reason in registry.SOURCES:
        row = dict(registry_id=rid, collection=path, title=title, status=status, reason=reason)
        if status != "admitted":
            row["blocker"] = registry.CATEGORY[rid]
        if status == "admitted":
            row["families"] = fams
            row["tasks"] = sum(fam_count[f] for f in fams)
            assert row["tasks"] > 0, rid
        else:
            row["candidates"] = fams
        reg.append(row)
    covered = {f for r in reg if r["status"] == "admitted" for f in r["families"]}
    assert covered == set(fam_count), (covered ^ set(fam_count))
    C.jsonl(tasks, C.CAND / "tasks.jsonl")
    C.jsonl(refs, C.EVAL / "references.jsonl")
    C.jsonl(reg, C.EVAL / "registry.jsonl")
    (C.CAND / "README.md").write_text(readme_candidate(tasks))
    C.jdump(dict(type="object", required=["outputs"], properties=dict(outputs=dict(type="object", additionalProperties={"type": ["number", "boolean"]}))),
            C.CAND / "submission.schema.json")
    shutil.copy2(C.HERE / "score.py", C.EVAL / "score.py")

    leaks = leak_scan(tasks, refs)
    n_out = sum(len([k for k, r in e["references"].items() if r.get("graded", True)]) for e in refs)
    C.jdump(dict(stage="base (v1.0 structure, migrated by repair_release.py)", tasks=len(tasks), graded_outputs=n_out,
                 inputs_hash_checked=sum(len(t["inputs"]) for t in tasks), leak_scan_hits=leaks), C.EVAL / "validation.json")
    print(f"base: {len(tasks)} tasks, {n_out} graded outputs, leaks {len(leaks)}", flush=True)
    print("next: release.py (v1.1 migration, verification, docs), report.py, package.py", flush=True)

if __name__ == "__main__":
    main()
