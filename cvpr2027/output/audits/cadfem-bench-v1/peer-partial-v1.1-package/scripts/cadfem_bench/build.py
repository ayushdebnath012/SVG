"""Build CADFEM-Bench v1: the final CAD + FEM benchmark assembled from every collected source.

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
import subprocess
import sys
from collections import Counter, defaultdict

import common as C
import card
import fam_agentfem
import fam_cadworld
import fam_calib
import fam_cycloidal
import fam_geopinonet
import fam_modal
import fam_rigging
import fam_simjeb
import fam_valve
import registry

FAMILIES = [fam_simjeb, fam_agentfem, fam_geopinonet, fam_modal, fam_cycloidal, fam_cadworld, fam_calib, fam_valve, fam_rigging]


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
    tmp = C.OUT / "_selftest"
    oracle(refs, tmp / "oracle", 1.0)
    oracle(refs, tmp / "perturbed", 1.3)
    res = {}
    for name in ("oracle", "perturbed"):
        out = tmp / f"{name}.json"
        subprocess.run([sys.executable, str(C.EVAL / "score.py"), "--refs", str(C.EVAL / "references.jsonl"),
                        "--submissions", str(tmp / name), "--out", str(out)], check=True, capture_output=True)
        s = json.loads(out.read_text())
        num = [x for x in s["tasks"] if x["track"] != "C" and not any(k.startswith("_") for k in x.get("checks", {}))]
        res[name] = dict(numeric_tasks=len(num), passed=sum(x["passed"] for x in num))
    shutil.rmtree(tmp)
    assert res["oracle"]["passed"] == res["oracle"]["numeric_tasks"], res
    assert res["perturbed"]["passed"] == 0, res
    by_track = defaultdict(Counter)
    for t in tasks:
        by_track[t["track"]][t["tier"]] += 1
    n_out = sum(len([k for k, r in e["references"].items() if r.get("graded", True)]) for e in refs)
    val = dict(version=C.VERSION, date=C.DATE, tasks=len(tasks), graded_outputs=n_out, families=len(fam_count),
               by_track={k: dict(v) for k, v in sorted(by_track.items())}, by_family=dict(sorted(fam_count.items())),
               ref_classes=dict(Counter(r["ref_class"] for e in refs for r in e["references"].values())),
               sources_admitted=sum(r["status"] == "admitted" for r in reg), sources_held=sum(r["status"] == "held" for r in reg),
               sources_excluded=sum(r["status"] == "excluded" for r in reg), inputs_hash_checked=sum(len(t["inputs"]) for t in tasks),
               leak_scan_hits=leaks, grader_selftest=res, solver_runs=0, model_calls=0)
    C.jdump(val, C.EVAL / "validation.json")
    print(json.dumps({k: v for k, v in val.items() if k != "leak_scan_hits"}, indent=1), "\nleaks:", len(leaks), flush=True)

    (C.EVAL / "DATASET_CARD.md").write_text(card.write(tasks, refs, reg, val))
    C.META.mkdir(parents=True, exist_ok=True)
    shutil.copy2(C.EVAL / "DATASET_CARD.md", C.META / "README.md")
    shutil.copy2(C.CAND / "README.md", C.META / "CANDIDATE_README.md")
    for f in ("tasks.jsonl", "submission.schema.json"):
        shutil.copy2(C.CAND / f, C.META / f)
    for f in ("references.jsonl", "registry.jsonl", "validation.json"):
        shutil.copy2(C.EVAL / f, C.META / f)
    print("next: report.py (PDF), then package.py (dataset folder + cadfem-bench-v1.zip)", flush=True)

if __name__ == "__main__":
    main()
