"""ReAct-style repair rounds for the PLAN+PATCH student: act (answer) -> observe (validator/executor) -> retry.

Round 0 answers are the greedy answers from sample_student_bestofn.py. Each round, every answer is quote-anchored
and checked with the target-free gates of cad_edit_verifier.py (patch applies, program executes to a valid solid).
Failures go back to the model as a conversation -- original task, its last answer, the error -- and the replies,
generated on the GPU host by generate_conversations.py, become the next round's answers. No reference is used
before final scoring with the official geometry scorers.

  python react_rounds.py --samples SAMPLES.jsonl --out DIR --adapter REMOTE_ADAPTER --rounds 3
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from best_of_n_select import SPLITS, anchored_text  # noqa: E402
from cad_edit_contracts import apply  # noqa: E402
from cad_edit_verifier import extract  # noqa: E402
from multisource_cad_astra_benchmark import _local_reference, _reference_index  # noqa: E402

PYTHON = ROOT / "tmp/cad-runtime/bin/python"
SSH = ["-o", "ControlPath=/tmp/h100cm.sock", "-o", "BatchMode=yes"]
HOST, REMOTE = "trishita@10.71.9.40", "svg-compute/bestofn-20261006"
FIX = ("{problem}\n\nReturn the corrected answer in the same PLAN/PATCH format. Indices refer to the ORIGINAL "
       "program's zero-based lines.")


def check(row: dict, text: str) -> dict:
    """Gates only: anchored patch applies and the program executes to a valid solid."""
    anchored = anchored_text(row["code"], text)
    task = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"],
                candidates=[anchored])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
        json.dump(task, h)
    try:
        proc = subprocess.run([str(PYTHON), str(ROOT / "scripts/cad_edit_verifier.py"), h.name], capture_output=True,
                              text=True, timeout=300)
        cand = json.loads(proc.stdout.splitlines()[-1])["candidates"][0] if proc.returncode == 0 else None
    except subprocess.TimeoutExpired:
        cand = dict(gates=False, error="TimeoutExpired: execution exceeded 300 s")
    finally:
        os.unlink(h.name)
    if cand is None:
        return dict(ok=False, anchored=anchored, problem="The original program could not be executed by the checker.")
    if cand["gates"]:
        return dict(ok=True, anchored=anchored, problem=None)
    error = cand["error"] or "unknown error"
    stage = ("Your patch applied, but the patched program failed to build a valid solid"
             if any(k in error for k in ("Standard_Failure", "solid", "Workplane", "StdFail", "OCP"))
             else "Applying your patch to the original program failed")
    return dict(ok=False, anchored=anchored, problem=f"{stage}: {error}")


def run(samples: Path, out: Path, adapter: str, rounds: int, workers: int) -> None:
    system = json.loads((ROOT / "data/multisource-cad-distill-v1/distill/manifest.json").read_text())["system"]
    rows = {json.loads(l)["id"]: json.loads(l) for s in ("test", "validation")
            for l in (SPLITS / f"{s}-retained.jsonl").read_text().splitlines()}
    recs = [json.loads(l) for l in samples.read_text().splitlines()]
    answers = {r["id"]: r["greedy"] for r in recs}
    split = {r["id"]: r["split"] for r in recs}
    out.mkdir(parents=True, exist_ok=True)
    history = {i: [] for i in answers}
    for r in range(rounds + 1):
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = dict(zip(answers, pool.map(lambda i: check(rows[i], answers[i]), answers)))
        for i, res in results.items():
            history[i].append(dict(round=r, answer=answers[i], ok=res["ok"], problem=res["problem"]))
        failing = [i for i, res in results.items() if not res["ok"]]
        print(f"round {r}: {len(answers) - len(failing)}/{len(answers)} pass gates; {len(failing)} to repair", flush=True)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        if r == rounds or not failing:
            break
        convs = [dict(id=i, messages=[dict(role="system", content=system), dict(role="user", content=rows[i]["input"]),
                                      dict(role="assistant", content=answers[i]),
                                      dict(role="user", content=FIX.format(problem=results[i]["problem"]))]) for i in failing]
        local = out / f"round{r + 1}-convs.jsonl"
        local.write_text("".join(json.dumps(c) + "\n" for c in convs))
        subprocess.run(["scp", "-q", *SSH, str(local), f"{HOST}:{REMOTE}/{local.name}"], check=True)
        subprocess.run(["ssh", *SSH, HOST, f"cd {REMOTE} && CUDA_VISIBLE_DEVICES=0 ~/miniconda3/envs/engsvg/bin/python "
                        f"generate_conversations.py --adapter {adapter} --inp {local.name} --out round{r + 1}-replies.jsonl "
                        f"> round{r + 1}.log 2>&1"], check=True)
        subprocess.run(["scp", "-q", *SSH, f"{HOST}:{REMOTE}/round{r + 1}-replies.jsonl", str(out)], check=True)
        for line in (out / f"round{r + 1}-replies.jsonl").read_text().splitlines():
            reply = json.loads(line)
            answers[reply["id"]] = reply["reply"]
    # final answers -> scorer inputs (anchored), per split
    index = _reference_index()
    for s in ("test", "validation"):
        items = []
        for i in (k for k in answers if split[k] == s):
            row, text = rows[i], history[i][-1]["answer"]
            anchored, code, error = anchored_text(row["code"], text), None, None
            try:
                _, patch = extract(anchored)
                code = apply(row["code"], patch, row["representation"])
            except Exception as e:  # noqa: BLE001
                error = type(e).__name__ + ": " + str(e)[:200]
            items.append(dict(id=i, source=row["source"], category=row["category"], representation=row["representation"],
                              predicted_code=code, error=error, applicable=error is None, prediction=anchored,
                              reference_code=row["edited_code"], reference_step_sha256=row.get("reference_step_sha256"),
                              reference_step=_local_reference(row, index) if s == "test" and row.get("reference_step") else None))
        (out / f"{s}-final.jsonl").write_text("".join(json.dumps(x) + "\n" for x in items))
    print("final answers written; score with score_multisource_cad_geometry.py / score_validation_geometry.py")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--samples", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--adapter", default="adapter")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    run(a.samples, a.out, a.adapter, a.rounds, a.workers)


if __name__ == "__main__":
    main()
