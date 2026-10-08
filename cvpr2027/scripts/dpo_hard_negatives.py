"""Synthetic hard negatives for the DPO checker: realistic wrong edits made from BenchCAD *training* references.

Astra's errors on the training tasks are too rare (213 natural pairs) to train a checker. Each training task's
reference patch is perturbed in the ways a frontier editor goes wrong while still producing a valid solid:

  value      one requested number off (x0.5, x0.8, x1.25, x2)
  partial    one changed number reverted to its original value (incomplete edit)
  location   the edited line's new content applied to another line with the same CadQuery call, or a different
             feature line removed instead of the requested one (wrong feature)
  direction  a face selector or offset sign flipped (>Z/<Z, +x/-x)
  drop       one of several edit operations omitted
  extra      the reference edit plus an unrequested change on another line

A negative is kept only if it executes, changes the source and disagrees with the reference geometry
(volume IoU < 0.99999); evidence is computed exactly as for the real drafts (dpo_checker.py). Test tasks are untouched.

  python dpo_hard_negatives.py [--per-task 6] [--workers 9]
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dpo_checker as dc  # noqa: E402
from cad_edit_contracts import apply  # noqa: E402

NUMBER = re.compile(r"(?<![\w.])(-?\d+\.\d+|-?\d+)(?![\w.])")
CALL = re.compile(r"\.(\w+)\(")
FLIPS = [(">Z", "<Z"), (">X", "<X"), (">Y", "<Y"), ("<Z", ">Z"), ("<X", ">X"), ("<Y", ">Y")]


def fmt(v: float, like: str) -> str:
    return str(int(round(v))) if "." not in like else f"{v:.{max(1, len(like.split('.')[1]))}f}"


def numbers(line: str) -> list[re.Match]:
    return [m for m in NUMBER.finditer(line) if float(m.group(1)) not in (0.0, 1.0)]


def replace_number(line: str, m: re.Match, value: str) -> str:
    return line[:m.start(1)] + value + line[m.end(1):]


def perturb(source: str, patch: dict, rng: random.Random) -> list[tuple[str, dict]]:
    src = source.splitlines()
    edits = patch["edits"]
    out = []

    def with_insert(k, line_index, new_line):
        e = [dict(op, insert=list(op["insert"])) for op in edits]
        e[k]["insert"][line_index] = new_line
        return {"edits": e}
    for k, op in enumerate(edits):
        for li, line in enumerate(op["insert"]):
            ms = numbers(line)
            if ms:
                m = rng.choice(ms)
                for f in rng.sample([0.5, 0.8, 1.25, 2.0], 2):
                    out.append(("value", with_insert(k, li, replace_number(line, m, fmt(float(m.group(1)) * f, m.group(1))))))
            old = src[op["start"] + li] if op["delete"] > li and op["start"] + li < len(src) else None
            if old is not None:
                new_ms, old_ms = numbers(line), numbers(old)
                if len(new_ms) == len(old_ms):
                    changed = [(a, b) for a, b in zip(new_ms, old_ms) if a.group(1) != b.group(1)]
                    if len(changed) >= 1 and len(new_ms) >= 2 or len(changed) >= 2:
                        a, b = rng.choice(changed)
                        out.append(("partial", with_insert(k, li, replace_number(line, a, b.group(1)))))
            for x, y in FLIPS:
                if x in line:
                    out.append(("direction", with_insert(k, li, line.replace(x, y, 1))))
                    break
            neg = [m for m in numbers(line) if float(m.group(1)) != 0 and "offset" in line or "translate" in line or "center" in line]
            if neg:
                m = rng.choice(neg)
                v = m.group(1)
                out.append(("direction", with_insert(k, li, replace_number(line, m, v[1:] if v.startswith("-") else "-" + v))))
        if op["delete"] == 1 and len(op["insert"]) == 1:
            call = CALL.search(src[op["start"]]) if op["start"] < len(src) else None
            if call:
                others = [j for j, l in enumerate(src) if j != op["start"] and f".{call.group(1)}(" in l
                          and not any(e["start"] <= j < e["start"] + max(1, e["delete"]) for e in edits)]
                for j in rng.sample(others, min(2, len(others))):
                    indent = src[j][:len(src[j]) - len(src[j].lstrip())]
                    moved = [dict(op2) for op2 in edits if op2 is not op] + [dict(start=j, delete=1, insert=[indent + op["insert"][0].lstrip()])]
                    out.append(("location", {"edits": sorted(moved, key=lambda e: e["start"])}))
        if op["delete"] >= 1 and not op["insert"]:  # deletion: remove a different feature instead (wrong feature)
            touched_now = {j for e in edits for j in range(e["start"], e["start"] + max(1, e["delete"]))}
            others = [j for j, l in enumerate(src) if j not in touched_now and CALL.search(l) and not l.strip().startswith(("import", "result =", "show_object"))]
            for j in rng.sample(others, min(2, len(others))):
                moved = [dict(op2) for op2 in edits if op2 is not op] + [dict(start=j, delete=op["delete"], insert=[])]
                out.append(("location", {"edits": sorted(moved, key=lambda e: e["start"])}))
    if len(edits) >= 2:
        for k in range(len(edits)):
            out.append(("drop", {"edits": [op for i, op in enumerate(edits) if i != k]}))
    touched = {j for e in edits for j in range(e["start"], e["start"] + max(1, e["delete"]))}
    spare = [j for j, l in enumerate(src) if j not in touched and numbers(l)]
    if spare:
        j = rng.choice(spare)
        m = rng.choice(numbers(src[j]))
        extra = dict(start=j, delete=1, insert=[replace_number(src[j], m, fmt(float(m.group(1)) * 1.2, m.group(1)))])
        out.append(("extra", {"edits": sorted([dict(e) for e in edits] + [extra], key=lambda e: e["start"])}))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--per-task", type=int, default=6)
    p.add_argument("--workers", type=int, default=9)
    a = p.parse_args()
    rows = dc.train_rows()
    path = dc.OUT / "evidence-synthetic.jsonl"
    done = {json.loads(l)["task"] for l in path.read_text().splitlines()} if path.exists() else set()
    jobs = []
    for tid, row in rows.items():
        if tid in done:
            continue
        rng = random.Random(int(tid[:8], 16))
        gold = json.loads(row["target"])
        codes = {}
        for kind, patch in perturb(row["code"], gold, rng):
            try:
                code = apply(row["code"], patch, "cadquery")
            except Exception:  # noqa: BLE001
                continue
            if code != row["edited_code"] and code != row["code"]:
                codes.setdefault(code, []).append("synthetic-" + kind)
        items = list(codes.items())
        rng.shuffle(items)
        jobs.append((tid, row, dict(items[:2 * a.per_task])))

    def one(job):
        tid, row, codes = job
        lst = list(codes)
        first = dc.worker(row["code"], lst, row["edited_code"], fem=False) if lst else None
        if first is None:
            return dict(task=tid, split="synthetic", drafts=[], error=None if not lst else "worker failed")
        keep = [k for k, c in enumerate(first["candidates"]) if "error" not in c and c.get("iou_reference", 1) < dc.STRICT
                and c["iou_source"] < dc.STRICT][:a.per_task]
        lst = [lst[k] for k in keep]
        fem = dc.worker(row["code"], lst, None, fem=True) if lst else None
        drafts = []
        for i, k in enumerate(keep):
            rec = dict(code=lst[i], origins=codes[lst[i]], **first["candidates"][k])
            if fem:
                rec["fem"] = fem["candidates"][i].get("fem")
            drafts.append(rec)
        return dict(task=tid, split="synthetic", source=first["source"], source_fem=fem["source_fem"] if fem else None, drafts=drafts)
    with ThreadPoolExecutor(a.workers) as pool, path.open("a") as handle:
        for n, fut in enumerate(as_completed([pool.submit(one, j) for j in jobs]), 1):
            handle.write(json.dumps(fut.result()) + "\n"); handle.flush()
            if n % 25 == 0:
                print("SYNTHETIC", n, "/", len(jobs), flush=True)


if __name__ == "__main__":
    main()
