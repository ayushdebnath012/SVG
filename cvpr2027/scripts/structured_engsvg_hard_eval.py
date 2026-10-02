"""Corrected out-of-template evaluation for the structured engineering SVG pilot.

This evaluates interpretation only. Geometry, SVG, and FEM remain deterministic.
The cases are authored independently of ``structured_engsvg.dataset`` and are
never passed to the trainer.  Version 2 removes the contradictory canonical-value
suffixes from the original clarification prompts and records targets in outputs.
"""
from __future__ import annotations

import argparse
import base64
import copy
import gc
import hashlib
import json
from pathlib import Path
import re
import shutil

import structured_engsvg as S
import engsvg_rule_interpreter as R


BENCHMARK_VERSION = "structured-engsvg-hard-v2"


def row(kind, source, request, target, case_id):
    expected = S.execute(source, target)
    return {
        "id": case_id,
        "kind": kind,
        "source": source,
        "request": request,
        "prompt": S.SCHEMA + "\nExisting design: " + json.dumps(source) + "\nRequest: " + request,
        "target": target,
        "expected": expected,
    }


def hard_cases():
    p = {
        "width_mm": 1400, "height_mm": 850, "section_b_mm": 50,
        "section_h_mm": 90, "E_mpa": 200000,
        "vertical_load_N": 1200, "horizontal_load_N": 150,
    }
    create_specs = [
        ("A 1.4 m wide and 85 cm tall table side frame uses a 5 cm by 9 cm rectangular section, E 200 GPa, a 1.2 kN downward load and 0.15 kN rightward load.", p),
        ("Use 70 GPa material. Build the fixed-base portal 900 mm high and 1.8 m across, with a 40 x 80 mm section. At the top right apply 2 kN down and no sideways load.",
         {"width_mm": 1800, "height_mm": 900, "section_b_mm": 40, "section_h_mm": 80, "E_mpa": 70000, "vertical_load_N": 2000, "horizontal_load_N": 0}),
        ("Draw a rigid portal: span 125 cm; rise 0.75 m; member breadth 45 mm; member depth 0.1 m; modulus 210 GPa; loads at D are 350 N to the right and 0.9 kN downward.",
         {"width_mm": 1250, "height_mm": 750, "section_b_mm": 45, "section_h_mm": 100, "E_mpa": 210000, "vertical_load_N": 900, "horizontal_load_N": 350}),
        ("For a 60 by 110 mm section and E=200000 MPa, create a 2.2 m span, 1.1 m high side frame carrying 1.75 kN vertically and 0.4 kN horizontally at D.",
         {"width_mm": 2200, "height_mm": 1100, "section_b_mm": 60, "section_h_mm": 110, "E_mpa": 200000, "vertical_load_N": 1750, "horizontal_load_N": 400}),
        ("Make the portal 1600 millimetres wide by 95 centimetres tall. Section is 35 mm x 75 mm, Young's modulus is 70 GPa, and D carries 650 N down plus 25 N right.",
         {"width_mm": 1600, "height_mm": 950, "section_b_mm": 35, "section_h_mm": 75, "E_mpa": 70000, "vertical_load_N": 650, "horizontal_load_N": 25}),
        ("Create the frame with a 1.05 m width, 800 mm height, 0.04 m breadth, 0.08 m depth, 200 GPa modulus, 0.5 kN down and 0.1 kN right.",
         {"width_mm": 1050, "height_mm": 800, "section_b_mm": 40, "section_h_mm": 80, "E_mpa": 200000, "vertical_load_N": 500, "horizontal_load_N": 100}),
    ]
    rows = [row("create", None, request, {"action": "create", "parameters": params}, f"create-{i:02d}")
            for i, (request, params) in enumerate(create_specs, 1)]

    edits = [
        ("Widen it by 0.2 m; retain every other setting.", {"width_mm": 1600}),
        ("Make it five centimetres shorter and leave the remaining design untouched.", {"height_mm": 800}),
        ("Double the downward load only.", {"vertical_load_N": 2400}),
        ("Increase the downward force by 25 percent; do not change the lateral force.", {"vertical_load_N": 1500}),
        ("Use a 60 by 100 mm member section, with the first number as breadth. Preserve geometry, material, and loads.", {"section_b_mm": 60, "section_h_mm": 100}),
        ("Switch the material stiffness to 210 GPa only.", {"E_mpa": 210000}),
        ("Remove the sideways load while retaining the vertical one.", {"horizontal_load_N": 0}),
        ("Set the span to 1.55 m and the height to 90 cm. Everything else stays as supplied.", {"width_mm": 1550, "height_mm": 900}),
        ("Add 0.05 kN to the lateral force and reduce the downward force by 0.2 kN.", {"horizontal_load_N": 200, "vertical_load_N": 1000}),
        ("Make the section depth ten millimetres larger without changing its breadth.", {"section_h_mm": 100}),
    ]
    rows += [row("edit", p, request, {"action": "edit", "changes": changes}, f"edit-{i:02d}")
             for i, (request, changes) in enumerate(edits, 1)]

    clarify_specs = [
        ("Create a 1.4 m by 0.85 m frame with a 50 x 90 mm section and E=200 GPa. I have not specified either applied load.", ["vertical_load_N", "horizontal_load_N"]),
        ("I need a portal 1.8 m wide carrying 1 kN downward and zero lateral force. Use 200 GPa material.", ["height_mm", "section_b_mm", "section_h_mm"]),
        ("Create the table frame with a 40 x 80 mm section, 900 N down and 100 N right. The geometry and material have not been given.", ["width_mm", "height_mm", "E_mpa"]),
        ("Make a 1200 mm wide, 800 mm tall frame. Nothing else is known yet.", ["section_b_mm", "section_h_mm", "E_mpa", "vertical_load_N", "horizontal_load_N"]),
        ("Use aluminium-like stiffness of 70 GPa, 1.6 m width and 0.9 m height, with 0.5 kN down. Ask me for whatever is still required.", ["section_b_mm", "section_h_mm", "horizontal_load_N"]),
        ("Create the frame using a 50 by 100 mm section under 1.5 kN downward and 0.2 kN rightward.", ["width_mm", "height_mm", "E_mpa"]),
    ]
    for i, (request, missing) in enumerate(clarify_specs, 1):
        rows.append(row("clarify", None, request,
                        {"action": "clarify", "missing": missing}, f"clarify-{i:02d}"))
    return rows


def parse(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def assess(item, text):
    try:
        action = parse(text)
        design = S.execute(item["source"], action)
        if item["kind"] == "clarify":
            success = (action.get("action") == "clarify"
                       and set(action.get("missing", [])) == set(item["target"]["missing"])
                       and len(action.get("missing", [])) == len(item["target"]["missing"]))
        else:
            success = design == item["expected"]
        physics_ok = None
        if design is not None:
            artifact, _ = S.artifact(design)
            physics_ok = max(abs(x) for x in artifact["analysis"]["equilibrium_residual_N_Nmm"]) < 1e-3
            success = success and physics_ok
        return {"valid_action": True, "success": bool(success), "physics_ok": physics_ok,
                "prediction": action, "result_design": design}
    except Exception as exc:
        return {"valid_action": False, "success": False, "error": str(exc)[:300]}


def trajectories():
    start = {"width_mm": 1200, "height_mm": 800, "section_b_mm": 40,
             "section_h_mm": 80, "E_mpa": 200000,
             "vertical_load_N": 800, "horizontal_load_N": 100}
    return [
        ("geometry-load", start, [
            ("Increase the span by 15 cm.", {"width_mm": 1350}),
            ("Now make the frame 10 percent taller.", {"height_mm": 880}),
            ("Finally double only the horizontal load.", {"horizontal_load_N": 200}),
        ]),
        ("section-material", start, [
            ("Change the section to 5 cm breadth by 9 cm depth.", {"section_b_mm": 50, "section_h_mm": 90}),
            ("Switch the modulus to 70 GPa.", {"E_mpa": 70000}),
            ("Reduce the downward load by one quarter.", {"vertical_load_N": 600}),
        ]),
        ("mixed", start, [
            ("Make it 0.2 m wider and add 0.1 kN to the downward load.", {"width_mm": 1400, "vertical_load_N": 900}),
            ("Remove the lateral load.", {"horizontal_load_N": 0}),
            ("Add 5 mm to the section depth and leave its breadth alone.", {"section_h_mm": 85}),
        ]),
    ]


def generate(model, tokenizer, prompt):
    import torch
    inputs = tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                           tokenize=False, add_generation_prompt=True)
    encoded = tokenizer(inputs, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        output = model.generate(**encoded, max_new_tokens=260, do_sample=False,
                                pad_token_id=tokenizer.pad_token_id)
    return tokenizer.decode(output[0][encoded["input_ids"].shape[1]:], skip_special_tokens=True)


def evaluate(model, tokenizer, tag, output):
    records = []
    for i, item in enumerate(hard_cases(), 1):
        raw = generate(model, tokenizer, item["prompt"])
        result = assess(item, raw)
        result.update(id=item["id"], kind=item["kind"], request=item["request"],
                      target=item["target"], expected=item["expected"], raw=raw)
        records.append(result)
        (output / f"hard-{tag}-predictions.json").write_text(json.dumps(records, indent=2))
        print("HARD", tag, i, len(hard_cases()), item["id"], result["success"], flush=True)

    rollout_records = []
    for name, initial, steps in trajectories():
        current = copy.deepcopy(initial)
        alive = True
        for step, (request, changes) in enumerate(steps, 1):
            target = {"action": "edit", "changes": changes}
            item = row("edit", current, request, target, f"{name}-{step}")
            raw = generate(model, tokenizer, item["prompt"]) if alive else ""
            result = assess(item, raw) if alive else {"valid_action": False, "success": False,
                                                       "error": "prior rollout step failed"}
            if result["success"]:
                current = result["result_design"]
            else:
                alive = False
            result.update(trajectory=name, step=step, raw=raw)
            rollout_records.append(result)
            print("ROLLOUT", tag, name, step, result["success"], flush=True)
    (output / f"rollout-{tag}-predictions.json").write_text(json.dumps(rollout_records, indent=2))
    by_kind = {kind: {"n": sum(r["kind"] == kind for r in records),
                      "success": sum(r["kind"] == kind and r["success"] for r in records)}
               for kind in ("create", "edit", "clarify")}
    by_kind["rollout_steps"] = {"n": len(rollout_records),
                                 "success": sum(r["success"] for r in rollout_records)}
    by_kind["complete_trajectories"] = {
        "n": len(trajectories()),
        "success": sum(all(r["success"] for r in rollout_records if r["trajectory"] == name)
                       for name, _, _ in trajectories()),
    }
    return by_kind


def evaluate_rule(output):
    """Run the deterministic conversion/arithmetic layer without a GPU."""
    records = []
    for item in hard_cases():
        try:
            action = R.interpret(item["request"], item["source"])
            raw = json.dumps(action, separators=(",", ":"))
            result = assess(item, raw)
        except Exception as exc:
            action = None
            result = {"valid_action": False, "success": False, "error": str(exc)[:300]}
        result.update(id=item["id"], kind=item["kind"], request=item["request"],
                      target=item["target"], expected=item["expected"], prediction=action)
        records.append(result)
    (output / "hard-rule-predictions.json").write_text(json.dumps(records, indent=2) + "\n")

    rollout_records = []
    for name, initial, steps in trajectories():
        current = copy.deepcopy(initial)
        alive = True
        for step, (request, changes) in enumerate(steps, 1):
            target = {"action": "edit", "changes": changes}
            item = row("edit", current, request, target, f"{name}-{step}")
            try:
                action = R.interpret(request, current) if alive else None
                result = assess(item, json.dumps(action)) if alive else {
                    "valid_action": False, "success": False, "error": "prior rollout step failed"
                }
            except Exception as exc:
                action = None
                result = {"valid_action": False, "success": False, "error": str(exc)[:300]}
            if result["success"]:
                current = result["result_design"]
            else:
                alive = False
            result.update(trajectory=name, step=step, request=request, target=target,
                          expected=item["expected"], prediction=action)
            rollout_records.append(result)
    (output / "rollout-rule-predictions.json").write_text(json.dumps(rollout_records, indent=2) + "\n")

    by_kind = {kind: {"n": sum(r["kind"] == kind for r in records),
                      "success": sum(r["kind"] == kind and r["success"] for r in records)}
               for kind in ("create", "edit", "clarify")}
    by_kind["rollout_steps"] = {"n": len(rollout_records),
                                 "success": sum(r["success"] for r in rollout_records)}
    by_kind["complete_trajectories"] = {
        "n": len(trajectories()),
        "success": sum(all(r["success"] for r in rollout_records if r["trajectory"] == name)
                       for name, _, _ in trajectories()),
    }
    summary = {
        "benchmark": BENCHMARK_VERSION,
        "corrects": "v1 clarification prompts contained contradictory appended canonical values",
        "frozen_before_model_evaluation": True,
        "training_overlap": "none; manually authored wording, conversions, composite and relative edits",
        "deterministic_rule_layer": by_kind,
        "scope": "One portal topology; interpretation plus deterministic frame FEM; not detached SVG or Astra",
    }
    (output / "rule-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.glob("*.json"))
        if path.name != "sha256-manifest.json"
    }
    (output / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return by_kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--emit-base64", action="store_true")
    ap.add_argument("--rule-only", action="store_true")
    args = ap.parse_args()
    args.run.mkdir(parents=True, exist_ok=True)
    rule_result = evaluate_rule(args.run)
    if args.rule_only:
        print(json.dumps({"benchmark": BENCHMARK_VERSION,
                          "deterministic_rule_layer": rule_result}, indent=2), flush=True)
        return
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch

    model_name = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16, device_map="cuda")
    base.eval()
    base_result = evaluate(base, tokenizer, "base", args.run)
    del base
    gc.collect()
    torch.cuda.empty_cache()

    trained_base = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16,
                                                        device_map="cuda")
    trained = PeftModel.from_pretrained(trained_base, args.run / "adapter").merge_and_unload()
    trained.eval()
    trained_result = evaluate(trained, tokenizer, "trained", args.run)
    summary = {
        "benchmark": BENCHMARK_VERSION,
        "corrects": "v1 clarification prompts contained contradictory appended canonical values",
        "frozen_before_evaluation": True,
        "training_overlap": "none; manually authored wording, conversions, composite and relative edits",
        "model": model_name,
        "base": base_result,
        "trained": trained_result,
        "deterministic_rule_layer": rule_result,
        "scope": "One portal topology; interpretation plus deterministic frame FEM; not detached SVG or Astra",
    }
    (args.run / "hard-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {}
    for path in sorted(p for p in args.run.rglob("*") if p.is_file()):
        manifest[str(path.relative_to(args.run))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (args.run / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = shutil.make_archive(str(args.run) + "-artifacts", "zip", args.run)
    print(json.dumps(summary, indent=2), flush=True)
    print("HARD_COMPLETED", archive, flush=True)
    if args.emit_base64:
        payload = base64.b64encode(Path(archive).read_bytes()).decode("ascii")
        print("ARTIFACT_B64_BEGIN", flush=True)
        print(payload, flush=True)
        print("ARTIFACT_B64_END", flush=True)


if __name__ == "__main__":
    main()
