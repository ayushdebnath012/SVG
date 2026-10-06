"""Build PLAN+PATCH student datasets for verifier-guided distillation from the multisource CAD-edit splits.

Every row keeps its input and gets a target in the teacher's format (cad_astra_distill.SYSTEM):
  PLAN: one bullet per edit operation quoting the zero-based ORIGINAL line, then PATCH: the JSON patch.

  template  no teacher: the plan is generated deterministically from the reference patch (control; free)
  distill   BenchCAD train rows whose Astra candidates pass the verifier use the verifier-selected teacher
            answer (its own plan and patch); all other rows use the template target

Acceptance (distill): the selected candidate passes the execution gates and at least two of the n teacher
samples agree on its geometry (consensus >= 2). --require-reference additionally keeps only teacher answers
whose solid matches the released reference (strict IoU); by default the reference is used for audit only.
Validation and test rows are identical across variants; target_patch keeps the reference patch for metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_astra_distill import RESULTS, SYSTEM  # noqa: E402

QUOTE = 100  # characters of an original line quoted in a template plan


def template_target(code: str, patch_text: str) -> str:
    lines, bullets = code.splitlines(), []
    for op in json.loads(patch_text)["edits"]:
        start, delete, insert = op["start"], op["delete"], len(op["insert"])
        if start >= len(lines):
            bullets.append(f"- [END] -> append {insert} line(s)")
            continue
        quoted = lines[start] if len(lines[start]) <= QUOTE else lines[start][:QUOTE] + "..."
        action = (f"replace {delete} line(s) with {insert} line(s)" if delete and insert
                  else f"delete {delete} line(s)" if delete else f"insert {insert} line(s) before")
        bullets.append(f"- [{start}] `{quoted}` -> {action}")
    return "PLAN:\n" + "\n".join(bullets) + "\nPATCH:\n" + json.dumps(json.loads(patch_text), separators=(",", ":"))


def teacher_targets(teachers: list[Path], require_reference: bool) -> tuple[dict, dict]:
    chosen, audit = {}, dict(tasks=0, accepted=0, accepted_reference_strict=0)
    for path in (p for teacher in teachers for p in sorted(teacher.glob("*/verify.json"))):
        verdict = json.loads(path.read_text())
        if verdict.get("selected") is None:
            continue
        audit["tasks"] += 1
        if verdict["selected_consensus"] < 2:
            continue
        if require_reference and not verdict["audit_selected_strict"]:
            continue
        text = json.loads((path.parent / "candidates.json").read_text())[verdict["selected"]]
        selected = verdict["candidates"][verdict["selected"]]
        chosen[verdict["id"]] = dict(text=text.strip(), patch=selected["patch"])
        audit["accepted"] += 1
        audit["accepted_reference_strict"] += bool(verdict["audit_selected_strict"])
    return chosen, audit


def build(out: Path, variant: str, teachers: list[Path] | None, require_reference: bool) -> dict:
    chosen, audit = teacher_targets(teachers, require_reference) if variant == "distill" else ({}, None)
    out.mkdir(parents=True, exist_ok=True)
    files, counts = {}, {}
    for split in ("train", "validation", "test"):
        rows = []
        for line in (RESULTS / f"{split}-retained.jsonl").read_text().splitlines():
            row = json.loads(line)
            row["target_patch"] = row["target"]
            if split == "train" and row["id"] in chosen:
                row["target"], row["target_origin"] = chosen[row["id"]]["text"], "teacher_verified"
            else:
                row["target"], row["target_origin"] = template_target(row["code"], row["target_patch"]), "template"
            rows.append(row)
        data = "".join(json.dumps(r) + "\n" for r in rows)
        (out / f"{split}.jsonl").write_text(data)
        files[split] = hashlib.sha256(data.encode()).hexdigest()
        counts[split] = {o: sum(r["target_origin"] == o for r in rows) for o in ("template", "teacher_verified")}
    manifest = dict(variant=variant, system=SYSTEM, files=files, counts=counts,
                    source_splits=str(RESULTS.relative_to(ROOT)), teacher=[str(t.relative_to(ROOT)) for t in teachers] if teachers else None,
                    acceptance=None if variant == "template" else
                    "verifier gates + consensus>=2" + (" + reference strict IoU" if require_reference else ""),
                    teacher_audit=audit,
                    note="Rows are the retained splits of the completed 3B run; only targets change. "
                         "Teacher calls used the training split only.")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("variant", "counts", "acceptance", "teacher_audit")}, indent=1))
    return manifest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--variant", choices=("template", "distill"), required=True)
    p.add_argument("--teacher", type=Path, action="append",
                   help="teacher run directory; repeat to combine runs (default: the pilot and the n=2 run)")
    p.add_argument("--require-reference", action="store_true")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    out = a.out or ROOT / f"data/multisource-cad-distill-v1/{a.variant}"
    teachers = a.teacher or [ROOT / "runs/cad-astra-distill-20261004", ROOT / "runs/cad-astra-distill-n2-20261005"]
    build(out, a.variant, [t for t in teachers if t.exists()] if a.variant == "distill" else None, a.require_reference)


if __name__ == "__main__":
    main()
