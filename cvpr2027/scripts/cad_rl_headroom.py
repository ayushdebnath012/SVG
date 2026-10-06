"""RL headroom probe for the final multisource 3B CAD editor: does it ever sample the target?

Group-relative RL (GRPO, as in RLRF and cadrille) only learns from prompts whose sampled group contains both
successes and failures, and in practice it mostly concentrates probability on answers the policy can already
sample. pass@k of the SFT policy is therefore a cheap upper-bound signal for what RL on this policy can reach.

  sample : greedy (fidelity check against the saved Colab predictions) plus k temperature samples per task
           from Qwen2.5-Coder-3B-Instruct + the final adapter, on Apple MPS in bf16 (Colab used an NF4 base)
  score  : apply each patch with cad_edit_contracts and run score_multisource_cad_geometry.py on every
           sample; report pass@k, per-task success counts and the GRPO-learnable fraction
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from math import comb
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply, target_match  # noqa: E402
from multisource_cad_astra_benchmark import DATA, RESULTS, _local_reference, _reference_index, tasks  # noqa: E402

MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
REVISION = "488639f1ff808d1d3d0ba301aef8c11461451ec5"  # results-final/run_manifest.json


def sample(out: Path, limit: int, k: int, temperature: float, seed: int) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    system = json.loads((DATA / "manifest.json").read_text())["system"]
    rows = tasks()[:limit]
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    base = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.bfloat16).to("mps")
    model = PeftModel.from_pretrained(base, str(RESULTS / "adapter")).eval()
    out.mkdir(parents=True, exist_ok=True)
    (out / "protocol.json").write_text(json.dumps(dict(
        model=MODEL, revision=REVISION, adapter=str((RESULTS / "adapter").relative_to(ROOT)), device="mps",
        dtype="bfloat16 (Colab evaluation used an NF4 double-quantized base)", tasks=len(rows), k=k,
        temperature=temperature, top_p=1.0, seed=seed, max_new_tokens=768,
        order="multisource_cad_astra_benchmark.tasks() prefix (sources alternate)"), indent=2) + "\n")
    path = out / "samples.jsonl"
    done = {json.loads(line)["id"] for line in path.read_text().splitlines()} if path.exists() else set()
    with path.open("a") as handle:
        for n, row in enumerate(rows):
            if row["id"] in done:
                continue
            started = time.perf_counter()
            prompt = tokenizer.apply_chat_template([dict(role="system", content=system),
                                                    dict(role="user", content=row["input"])],
                                                   tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").to("mps")
            width = inputs.input_ids.shape[1]
            with torch.inference_mode():
                greedy = model.generate(**inputs, max_new_tokens=768, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)[:, width:]
                torch.manual_seed(seed + n)
                drawn = model.generate(**inputs, max_new_tokens=768, do_sample=True, temperature=temperature,
                                       top_p=1.0, top_k=0, num_return_sequences=k,
                                       pad_token_id=tokenizer.eos_token_id)[:, width:]
            record = dict(id=row["id"], source=row["source"], category=row["category"],
                          greedy=tokenizer.decode(greedy[0], skip_special_tokens=True),
                          samples=tokenizer.batch_decode(drawn, skip_special_tokens=True),
                          seconds=time.perf_counter() - started)
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            print(n + 1, "/", len(rows), row["source"], f"{record['seconds']:.1f}s", flush=True)


def _prediction(row: dict, text: str, index: dict, tag: str) -> dict:
    error = code = None
    match = False
    try:
        st = text.strip()
        if st.startswith("```"):
            st = "\n".join(st.splitlines()[1:-1])
        code = apply(row["code"], json.loads(st), row["representation"])
        match = target_match(code, row["edited_code"], row["representation"])
    except Exception as e:  # noqa: BLE001
        error = type(e).__name__ + ": " + str(e)[:250]
    return dict(id=tag, source=row["source"], representation=row["representation"], category=row["category"],
                prediction=text, applicable=error is None, target_match=match, error=error, predicted_code=code,
                reference_code=row["edited_code"], reference_step=_local_reference(row, index),
                reference_step_sha256=row.get("reference_step_sha256"))


def _pass_at(n: int, c: int, k: int) -> float:
    return 1.0 if n - c < k else 1 - comb(n - c, k) / comb(n, k)


def score(out: Path, python: Path) -> None:
    rows = {r["id"]: r for r in tasks()}
    records = [json.loads(line) for line in (out / "samples.jsonl").read_text().splitlines()]
    index = _reference_index()
    preds = []
    for rec in records:
        row = rows[rec["id"]]
        preds.append(_prediction(row, rec["greedy"], index, rec["id"] + "#greedy"))
        preds += [_prediction(row, text, index, f"{rec['id']}#{j}") for j, text in enumerate(rec["samples"])]
    (out / "predictions.jsonl").write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([str(python), str(ROOT / "scripts/score_multisource_cad_geometry.py"),
                    str(out / "predictions.jsonl")], check=True, stdout=subprocess.DEVNULL)
    geom = {json.loads(l)["id"]: json.loads(l) for l in (out / "predictions-geometry.jsonl").read_text().splitlines()}
    saved = {json.loads(l)["id"]: json.loads(l) for l in (RESULTS / "trained-predictions.jsonl").read_text().splitlines()}
    astra_dir = ROOT / "runs/multisource-cad-astra-20261004/scored"
    astra = {json.loads(l)["id"]: json.loads(l)["match_strict"]
             for l in (astra_dir / "astra-predictions-geometry.jsonl").read_text().splitlines()}
    colab = {json.loads(l)["id"]: json.loads(l)["match_strict"]
             for l in (astra_dir / "trained-predictions-geometry.jsonl").read_text().splitlines()}
    summary = {"tasks": len(records), "k": len(records[0]["samples"]), "by_source": {}}
    for source in (None, "BenchCAD", "CAD-Editor"):
        recs = [r for r in records if (source is None or r["source"] == source)
                and geom[r["id"] + "#greedy"]["reference_valid"] is not False]
        k = len(recs[0]["samples"])
        counts = [sum(geom[f"{r['id']}#{j}"]["match_strict"] for j in range(k)) for r in recs]
        executed = [sum(geom[f"{r['id']}#{j}"]["executable"] is True for j in range(k)) for r in recs]
        entry = dict(
            tasks=len(recs),
            greedy_text_equals_colab=sum(r["greedy"].strip() == saved[r["id"]]["prediction"].strip() for r in recs),
            greedy_strict_local=sum(geom[r["id"] + "#greedy"]["match_strict"] for r in recs),
            colab_greedy_strict=sum(colab[r["id"]] for r in recs),
            astra_strict=sum(astra[r["id"]] for r in recs),
            sampled_executed_rate=round(sum(executed) / (k * len(recs)), 4),
            **{f"pass@{m}": round(sum(_pass_at(k, c, m) for c in counts) / len(recs), 4) for m in (1, 2, 4, k)},
            tasks_any_success=sum(c > 0 for c in counts),
            grpo_learnable_mixed=sum(0 < c < k for c in counts),
            all_fail=sum(c == 0 for c in counts), all_success=sum(c == k for c in counts),
            success_count_histogram=dict(sorted(Counter(counts).items())),
            astra_solved_but_never_sampled=sum(astra[r["id"]] and c == 0 for r, c in zip(recs, counts)))
        summary["by_source"][source or "all"] = entry
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--limit", type=int, default=64)
    s.add_argument("--k", type=int, default=8)
    s.add_argument("--temperature", type=float, default=1.0)
    s.add_argument("--seed", type=int, default=17)
    c = sub.add_parser("score")
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--python", type=Path, default=ROOT / "tmp/cad-runtime/bin/python")
    a = p.parse_args()
    if a.cmd == "sample":
        sample(a.out, a.limit, a.k, a.temperature, a.seed)
    else:
        score(a.out, a.python)


if __name__ == "__main__":
    main()
