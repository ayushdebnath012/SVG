"""Prepare and train a leakage-controlled multi-family EngSVG IR-action LoRA."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil

import engsvg_ir as IR
import engsvg_multifamily_benchmark as BENCH
import engsvg_plate as plate
import engsvg_truss as truss


MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
SCHEMA = ('Return one JSON object only. Allowed forms: '
          '{"action":"edit","changes":{"canonical.path":number}}, '
          '{"action":"clarify","missing":["required_information"]}, or '
          '{"action":"reject","reason":"unsupported_request"}. '
          'Do arithmetic using the supplied canonical state. Change only requested values.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compact_state(model):
    if model["kind"] == "truss2d":
        load_node = next(iter(model["loads"])); section = model["sections"]["bar"]
        return {"kind": "truss2d", "E_mpa": model["materials"]["steel"]["E_mpa"],
                "section_b_mm": section["b_mm"], "section_h_mm": section["h_mm"],
                "load_node": load_node, "downward_load_N": abs(model["loads"][load_node][1])}
    p = model["plates"][0]
    offset = next(item for item in model["dimensions"] if item["id"] == "edge_offset")["value_mm"]
    return {"kind": "mechanical_part_2d", "width_mm": p["width_mm"],
            "height_mm": p["height_mm"], "thickness_mm": p["thickness_mm"],
            "E_mpa": model["materials"]["steel"]["E_mpa"],
            "hole_count": len(model["holes"]), "hole_diameter_mm": model["holes"][0]["diameter_mm"],
            "edge_offset_mm": offset}


def prompt(model, request):
    return SCHEMA + "\nCanonical state: " + json.dumps(compact_state(model), separators=(",", ":")) + "\nRequest: " + request


def _truss_source(rng):
    model = truss.example_model()
    model["materials"]["steel"]["E_mpa"] = rng.choice([65000, 69000, 70000, 190000, 195000, 200000, 205000, 210000])
    model["sections"]["bar"]["b_mm"] = rng.randrange(20, 61, 5)
    model["sections"]["bar"]["h_mm"] = rng.randrange(15, 51, 5)
    model["loads"]["C"][1] = -rng.randrange(7000, 31000, 250)
    return IR.validate(model)


def _plate_source(rng):
    model = plate.example_model()
    model["materials"]["steel"]["E_mpa"] = rng.choice([65000, 69000, 70000, 190000, 195000, 200000, 205000, 210000])
    model["plates"][0]["thickness_mm"] = rng.randrange(4, 21)
    diameter = rng.randrange(10, 31, 2); offset = rng.randrange(max(20, diameter // 2 + 15), 51, 5)
    next(item for item in model["dimensions"] if item["id"] == "hole_diameter")["value_mm"] = diameter
    next(item for item in model["dimensions"] if item["id"] == "edge_offset")["value_mm"] = offset
    centers = ((offset, offset), (300-offset, offset), (offset, 200-offset), (300-offset, 200-offset))
    for hole, center in zip(model["holes"], centers):
        hole["center_mm"] = list(center); hole["diameter_mm"] = diameter
    return IR.validate(model)


def _row(group, kind, model, request, target):
    return {"group": group, "family": model["kind"], "kind": kind,
            "state": compact_state(model), "request": request,
            "prompt": prompt(model, request),
            "target": json.dumps(target, separators=(",", ":"))}


def _truss_edits(rng, group, model):
    state = compact_state(model); load = state["downward_load_N"]
    percent = rng.choice([5, 15, 20, 30]); added = rng.choice([500, 750, 1250, 1500])
    breadth_delta = rng.choice([5, 10]); depth = rng.choice([20, 25, 30, 35, 40, 45, 50])
    forms = [
        (rng.choice([f"Raise the load at C by {percent} percent.", f"Increase C's downward force {percent}%."]),
         {"action": "edit", "changes": {"loads.C.fy_N": -round(load * (1 + percent / 100))}}),
        (rng.choice([f"Add {added} N to the downward load at C.", f"Increase the C load by {added} newtons."]),
         {"action": "edit", "changes": {"loads.C.fy_N": -(load + added)}}),
        (rng.choice([f"Make all bars {breadth_delta} mm wider.", f"Add {breadth_delta} mm to the common bar breadth."]),
         {"action": "edit", "changes": {"sections.bar.b_mm": state["section_b_mm"] + breadth_delta}}),
        (rng.choice([f"Set the common member depth to {depth} mm.", f"Use {depth} mm for every bar depth."]),
         {"action": "edit", "changes": {"sections.bar.h_mm": depth}}),
    ]
    return [_row(group, "edit", model, request, target) for request, target in forms]


def _plate_edits(rng, group, model):
    state = compact_state(model); thickness_delta = rng.choice([1, 2, 3, 4])
    diameter_delta = rng.choice([2, 4, 6]); offset_delta = rng.choice([5, 10]); modulus = rng.choice([70000, 200000, 210000])
    forms = [
        (rng.choice([f"Add {thickness_delta} mm to the plate thickness.", f"Make the plate {thickness_delta} mm thicker."]),
         {"action": "edit", "changes": {"plates.P1.thickness_mm": state["thickness_mm"] + thickness_delta}}),
        (rng.choice([f"Increase every hole diameter by {diameter_delta} mm.", f"Enlarge all four through holes by {diameter_delta} mm in diameter."]),
         {"action": "edit", "changes": {"holes.*.diameter_mm": state["hole_diameter_mm"] + diameter_delta}}),
        (rng.choice([f"Move each hole {offset_delta} mm farther from its nearest edges.", f"Increase both edge offsets by {offset_delta} mm."]),
         {"action": "edit", "changes": {"dimensions.edge_offset.value_mm": state["edge_offset_mm"] + offset_delta}}),
        (rng.choice([f"Set the material modulus to {modulus} MPa.", f"Change E to {modulus} megapascals."]),
         {"action": "edit", "changes": {"materials.steel.E_mpa": modulus}}),
    ]
    return [_row(group, "edit", model, request, target) for request, target in forms]


def _special(rng, group, model, clarify):
    if clarify:
        if model["kind"] == "truss2d":
            request = rng.choice(["Make the truss stronger by changing its section.",
                                  "Increase the load, but I have not said by how much."])
            missing = ["requested_section_dimensions"] if "section" in request else ["load_change_amount"]
        else:
            request = rng.choice(["Move the holes farther from the edges.",
                                  "Make the plate thicker without specifying a value."])
            missing = ["edge_offset_change"] if "holes" in request else ["plate_thickness"]
        return _row(group, "clarify", model, request, {"action": "clarify", "missing": missing})
    request = rng.choice(["Turn this engineering drawing into a photograph.",
                          "Delete the physical object and write a poem instead."])
    return _row(group, "reject", model, request, {"action": "reject", "reason": "unsupported_request"})


def dataset(seed=1729):
    rng = random.Random(seed)
    heldout = {row["source_hash"] for row in BENCH.edit_cases()}
    groups = []
    for family in ("truss", "plate"):
        for index in range(1000):
            while True:
                model = _truss_source(rng) if family == "truss" else _plate_source(rng)
                group = IR.engineering_digest(model)
                if group not in heldout and all(existing[0] != group for existing in groups): break
            rows = _truss_edits(rng, group, model) if family == "truss" else _plate_edits(rng, group, model)
            rows.append(_special(rng, group, model, clarify=(index % 2 == 0)))
            groups.append((group, rows))
    rng.shuffle(groups)
    splits = {"train": [], "validation": [], "test": []}
    # Split source designs, not individual instructions.
    for index, (_, rows) in enumerate(groups):
        split = "train" if index < 1600 else "validation" if index < 1800 else "test"
        splits[split].extend(rows)
    for rows in splits.values(): rng.shuffle(rows)
    return splits, heldout


def prepare(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    splits, heldout = dataset()
    split_groups = {}
    for split, rows in splits.items():
        (out / f"{split}.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        split_groups[split] = {row["group"] for row in rows}
    assert all(not split_groups[a] & split_groups[b] for a in split_groups for b in split_groups if a < b)
    assert not set.union(*split_groups.values()) & heldout
    counts = {split: {kind: sum(row["kind"] == kind for row in rows)
                      for kind in ("edit", "clarify", "reject")} | {"total": len(rows)}
              for split, rows in splits.items()}
    all_rows = sum(splits.values(), [])
    summary = {"version": "engsvg-multifamily-train-v1", "seed": 1729,
               "model": MODEL, "counts": counts, "source_groups": len({r["group"] for r in all_rows}),
               "heldout_benchmark": BENCH.VERSION, "heldout_edit_cases": 100,
               "heldout_source_overlap": 0,
               "targets": {kind: sum(row["kind"] == kind for row in all_rows)
                           for kind in ("edit", "clarify", "reject")}}
    (out / "dataset-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(out.glob("*.json*")) if path.name != "sha256-manifest.json"}
    (out / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


def _parse(text):
    import re
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def _evaluate(model, tokenizer, rows, tag, out):
    import torch
    model.eval()
    if hasattr(model, "gradient_checkpointing_disable"):
        model.gradient_checkpointing_disable()
    if hasattr(model, "config"):
        model.config.use_cache = True
    records = []
    for index, row in enumerate(rows, 1):
        rendered = tokenizer.apply_chat_template([{"role": "user", "content": row["prompt"]}],
                                                 tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(rendered, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=180, do_sample=False,
                                    pad_token_id=tokenizer.pad_token_id)
        raw = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        try:
            prediction = _parse(raw); success = prediction == json.loads(row["target"]); error = None
        except Exception as exc:
            prediction = None; success = False; error = str(exc)[:200]
        records.append({"id": row.get("id", index), "family": row["family"], "kind": row["kind"],
                        "request": row["request"], "target": json.loads(row["target"]),
                        "prediction": prediction, "raw": raw, "success": success, "error": error})
        (out / f"{tag}-predictions.json").write_text(json.dumps(records, indent=2) + "\n")
        print(tag, index, len(rows), success, flush=True)
    return {"n": len(records), "success": sum(row["success"] for row in records),
            "by_family": {family: {"n": sum(r["family"] == family for r in records),
                                    "success": sum(r["family"] == family and r["success"] for r in records)}
                          for family in sorted({r["family"] for r in records})}}


def _benchmark_rows():
    # The frozen manifest intentionally stores the edited target but not another
    # copy of the source IR. Recreate its deterministic source catalogue here so
    # relative instructions are evaluated from the pre-edit state. Feeding the
    # target state would leak the answer and would make percentage edits wrong.
    sources = dict(BENCH._truss_variants() + BENCH._plate_variants())
    rows = []
    for item in BENCH.edit_cases():
        source = sources[item["source_id"]]
        assert IR.engineering_digest(source) == item["source_hash"]
        rows.append({"id": item["id"], "family": item["family"], "kind": "edit",
                     "request": item["request"], "prompt": prompt(source, item["request"]),
                     "target": json.dumps(item["expected_action"], separators=(",", ":"))})
    return rows


def train(out: Path, data_dir: Path, epochs=1):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, set_seed
    from peft import LoraConfig, get_peft_model
    from colab_train_engsvg import training_arguments
    if not torch.cuda.is_available(): raise RuntimeError("CUDA GPU required")
    out.mkdir(parents=True, exist_ok=True); set_seed(1729)
    rows = {split: [json.loads(line) for line in (data_dir / f"{split}.jsonl").read_text().splitlines()]
            for split in ("train", "validation", "test")}
    tokenizer = AutoTokenizer.from_pretrained(MODEL); tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    def render(row): return tokenizer.apply_chat_template([{"role": "user", "content": row["prompt"]}], tokenize=False, add_generation_prompt=True)
    def encode(items):
        result = []
        for row in items:
            p = tokenizer(render(row), add_special_tokens=False)["input_ids"]
            t = tokenizer(row["target"] + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
            if len(p + t) > 1024: raise ValueError("training example exceeds 1024 tokens")
            result.append({"input_ids": p + t, "labels": [-100] * len(p) + t})
        return result
    def collate(batch):
        length = max(len(row["input_ids"]) for row in batch)
        return {"input_ids": torch.tensor([row["input_ids"] + [tokenizer.pad_token_id] * (length-len(row["input_ids"])) for row in batch]),
                "labels": torch.tensor([row["labels"] + [-100] * (length-len(row["labels"])) for row in batch]),
                "attention_mask": torch.tensor([[1] * len(row["input_ids"]) + [0] * (length-len(row["input_ids"])) for row in batch])}
    base = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="cuda"); base.eval()
    benchmark = _benchmark_rows(); before = _evaluate(base, tokenizer, benchmark, "base", out)
    model = get_peft_model(base, LoraConfig(r=16, lora_alpha=32, lora_dropout=.05,
                                           target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
    model.enable_input_require_grads(); model.config.use_cache = False
    args = training_arguments(TrainingArguments, output_dir=str(out / "checkpoints"), num_train_epochs=epochs,
                              per_device_train_batch_size=2, gradient_accumulation_steps=8, learning_rate=1e-4,
                              lr_scheduler_type="cosine", logging_steps=25, eval_strategy="epoch", save_strategy="epoch",
                              save_total_limit=1, bf16=True, report_to=[], seed=1729,
                              gradient_checkpointing=True, remove_unused_columns=False)
    trainer = Trainer(model=model, args=args, train_dataset=encode(rows["train"]),
                      eval_dataset=encode(rows["validation"]), data_collator=collate)
    history = trainer.train(); model.save_pretrained(out / "adapter"); tokenizer.save_pretrained(out / "adapter")
    trained = model.merge_and_unload(); trained.eval(); after = _evaluate(trained, tokenizer, benchmark, "trained", out)
    summary = {"model": MODEL, "gpu": torch.cuda.get_device_name(0), "epochs": epochs,
               "dataset": json.loads((data_dir / "dataset-summary.json").read_text()),
               "before": before, "after": after, "train_metrics": history.metrics,
               "benchmark": BENCH.VERSION, "benchmark_cases": len(benchmark)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    shutil.rmtree(out / "checkpoints", ignore_errors=True)
    shutil.make_archive(str(out) + "-artifacts", "zip", out)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=["prepare", "train"])
    parser.add_argument("--out", type=Path, required=True); parser.add_argument("--data", type=Path)
    parser.add_argument("--epochs", type=int, default=1); args = parser.parse_args()
    if args.command == "prepare": print(json.dumps(prepare(args.out), indent=2))
    else:
        if not args.data: parser.error("--data is required for train")
        train(args.out, args.data, args.epochs)
