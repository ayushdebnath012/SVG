"""Best-of-n for the PLAN+PATCH student: quote anchoring, target-free verifier selection, official scoring.

Candidates per task are the greedy answer plus n samples (sample_student_bestofn.py). Every candidate is
re-anchored by its quoted plan lines (anchor_plan_patches.anchor). cad_edit_verifier.py then ranks the
candidates from the source program, instruction and candidates alone. All distinct candidate programs are scored
against the references (test: score_multisource_cad_geometry.py; validation: score_validation_geometry.py), so the
greedy, single-sample, verifier-selected and oracle (any candidate correct) rates come from identical scoring.

  prepare : anchored candidates + scorer inputs     verify : verifier per task     report : metrics
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from anchor_plan_patches import anchor  # noqa: E402
from cad_edit_contracts import apply  # noqa: E402
from cad_edit_verifier import extract  # noqa: E402
from multisource_cad_astra_benchmark import _local_reference, _reference_index  # noqa: E402

SPLITS = ROOT / "runs/multisource-cad-colab-20261002/results-final"
PYTHON = ROOT / "tmp/cad-runtime/bin/python"


def anchored_text(code: str, text: str) -> str:
    try:
        patch, _ = anchor(code, text)
        plan, _ = extract(text)
        return "PLAN:\n" + plan + "\nPATCH:\n" + json.dumps(patch, separators=(",", ":"))
    except Exception:  # noqa: BLE001 - unparseable answers stay as generated and fail the gates
        return text


def prepare(samples: Path, out: Path) -> None:
    rows = {json.loads(l)["id"]: json.loads(l) for s in ("test", "validation")
            for l in (SPLITS / f"{s}-retained.jsonl").read_text().splitlines()}
    index = _reference_index()
    out.mkdir(parents=True, exist_ok=True)
    tasks, scorer = [], {"test": [], "validation": []}
    seen = set()
    for line in samples.read_text().splitlines():
        rec = json.loads(line)
        row = rows[rec["id"]]
        cands = [anchored_text(row["code"], t) for t in [rec["greedy"]] + rec["samples"]]
        keys = []
        for text in cands:
            code, error = None, None
            try:
                _, patch = extract(text)
                code = apply(row["code"], patch, row["representation"])
            except Exception as e:  # noqa: BLE001
                error = type(e).__name__ + ": " + str(e)[:200]
            key = hashlib.sha256((code or "ERR" + text).encode()).hexdigest()[:16]
            keys.append(key)
            if (rec["id"], key) not in seen:
                seen.add((rec["id"], key))
                ref = _local_reference(row, index) if rec["split"] == "test" and row.get("reference_step") else None
                scorer[rec["split"]].append(dict(id=f"{rec['id']}#{key}", source=row["source"], category=row["category"],
                                                 representation=row["representation"], predicted_code=code, error=error,
                                                 applicable=error is None, prediction=text, reference_code=row["edited_code"],
                                                 reference_step=ref, reference_step_sha256=row.get("reference_step_sha256")))
        tasks.append(dict(id=rec["id"], split=rec["split"], source=row["source"], candidates=cands, keys=keys))
    (out / "tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
    for split, items in scorer.items():
        (out / f"{split}-candidates.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items))
    print(len(tasks), "tasks;", {s: len(v) for s, v in scorer.items()}, "distinct candidate programs to score")


def verify(out: Path, workers: int) -> None:
    rows = {json.loads(l)["id"]: json.loads(l) for s in ("test", "validation")
            for l in (SPLITS / f"{s}-retained.jsonl").read_text().splitlines()}
    tasks = [json.loads(l) for l in (out / "tasks.jsonl").read_text().splitlines()]
    done = {json.loads(l)["id"] for l in (out / "verdicts.jsonl").read_text().splitlines()} if (out / "verdicts.jsonl").exists() else set()

    def one(t):
        row = rows[t["id"]]
        payload = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"],
                       candidates=t["candidates"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
            json.dump(payload, h)
        try:
            proc = subprocess.run([str(PYTHON), str(ROOT / "scripts/cad_edit_verifier.py"), h.name], capture_output=True,
                                  text=True, timeout=600)
            v = json.loads(proc.stdout.splitlines()[-1]) if proc.returncode == 0 else dict(selected=None, error=proc.stderr[-300:])
        except subprocess.TimeoutExpired:
            v = dict(selected=None, error="verifier_timeout")
        finally:
            os.unlink(h.name)
        return dict(id=t["id"], selected=v.get("selected"), consensus=v.get("selected_consensus"),
                    clusters=v.get("clusters"), error=v.get("error"))
    with ThreadPoolExecutor(max_workers=workers) as pool, (out / "verdicts.jsonl").open("a") as handle:
        for n, v in enumerate(pool.map(one, [t for t in tasks if t["id"] not in done])):
            handle.write(json.dumps(v) + "\n")
            handle.flush()
            if n % 25 == 0:
                print("verified", n, flush=True)


def report(out: Path) -> dict:
    tasks = {json.loads(l)["id"]: json.loads(l) for l in (out / "tasks.jsonl").read_text().splitlines()}
    verdicts = {json.loads(l)["id"]: json.loads(l) for l in (out / "verdicts.jsonl").read_text().splitlines()}
    strict = {}
    for split in ("test", "validation"):
        for l in (out / f"{split}-candidates-geometry.jsonl").read_text().splitlines():
            g = json.loads(l)
            strict[g["id"]] = (g["match_strict"], g.get("reference_valid") is not False)
    summary = {}
    for split in ("test", "validation"):
        ts = [t for t in tasks.values() if t["split"] == split]
        ok = lambda t, k: strict[f"{t['id']}#{t['keys'][k]}"][0]  # noqa: E731
        def counts(sub):
            n = len(sub[0]["keys"]) if sub else 0
            pick = lambda t: verdicts.get(t["id"], {}).get("selected") or 0  # no executable candidate: keep greedy  # noqa: E731
            majority = 0
            for t in sub:
                top = Counter(t["keys"]).most_common(1)[0][0]
                majority += strict[f"{t['id']}#{top}"][0]
            return dict(tasks=len(sub), candidates=n, greedy=sum(ok(t, 0) for t in sub),
                        single_sample=round(sum(ok(t, k) for t in sub for k in range(1, n)) / max(1, n - 1), 1),
                        majority_vote=majority,
                        verifier_pick=sum(ok(t, pick(t)) for t in sub),
                        verifier_fallback_to_greedy=sum(verdicts.get(t["id"], {}).get("selected") is None for t in sub),
                        oracle_any=sum(any(ok(t, k) for k in range(n)) for t in sub))
        summary[split] = counts(ts)
        summary[split]["sources"] = {s: counts([t for t in ts if t["source"] == s]) for s in ("BenchCAD", "CAD-Editor")}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--samples", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--out", type=Path, required=True)
    v.add_argument("--workers", type=int, default=4)
    r = sub.add_parser("report")
    r.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.cmd == "prepare":
        prepare(args.samples, args.out)
    elif args.cmd == "verify":
        verify(args.out, args.workers)
    else:
        report(args.out)


if __name__ == "__main__":
    main()
