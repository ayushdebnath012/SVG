"""Repair-turn (ReAct) instruction-tuning data from the student's own failures on the TRAINING split.

For each training row, the student's greedy answer and samples (sample_student_bestofn.py --splits train) are
checked in order with react_rounds.check (quote anchoring + target-free gates). The first failing answer becomes
one extra training example: [task, failed answer, checker feedback] -> the row's original target. Original rows
are kept unchanged; validation and test are copied from the distill dataset.

  python build_react_dataset.py --samples TRAIN_SAMPLES.jsonl --out data/multisource-cad-react-v1
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from react_rounds import FIX, check  # noqa: E402

SOURCE = ROOT / "data/multisource-cad-distill-v1/distill"


def first_failure(row: dict, texts: list[str]) -> dict | None:
    seen = set()
    for text in texts:
        if text in seen:
            continue
        seen.add(text)
        result = check(row, text)
        if not result["ok"]:
            return dict(answer=text, problem=result["problem"])
    return None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--samples", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=6)
    a = p.parse_args()
    rows = {json.loads(l)["id"]: json.loads(l) for l in (SOURCE / "train.jsonl").read_text().splitlines()}
    recs = [json.loads(l) for l in a.samples.read_text().splitlines() if json.loads(l)["id"] in rows]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        failures = list(pool.map(lambda r: first_failure(rows[r["id"]], [r["greedy"]] + r["samples"]), recs))
    repairs = []
    for rec, fail in zip(recs, failures):
        if fail:
            row = dict(rows[rec["id"]])
            row.update(id=rec["id"] + "#repair", repair=True,
                       history=[dict(role="assistant", content=fail["answer"]),
                                dict(role="user", content=FIX.format(problem=fail["problem"]))])
            repairs.append(row)
    a.out.mkdir(parents=True, exist_ok=True)
    train = list(rows.values()) + repairs
    files = {}
    data = "".join(json.dumps(r) + "\n" for r in train)
    (a.out / "train.jsonl").write_text(data)
    files["train"] = hashlib.sha256(data.encode()).hexdigest()
    for split in ("validation", "test"):
        shutil.copy(SOURCE / f"{split}.jsonl", a.out / f"{split}.jsonl")
        files[split] = hashlib.sha256((a.out / f"{split}.jsonl").read_bytes()).hexdigest()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    manifest.update(variant="react", files=files,
                    counts=dict(train=dict(original=len(rows), repair=len(repairs)), validation=None, test=None),
                    react=dict(source_samples=str(a.samples), checked_tasks=len(recs),
                               repair_rule="first failing of greedy+samples; target = original row target",
                               problems={k: sum(k in r["history"][1]["content"] for r in repairs)
                                         for k in ("failed to build a valid solid", "Applying your patch")}))
    (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["counts"]), json.dumps(manifest["react"]["problems"]))


if __name__ == "__main__":
    main()
