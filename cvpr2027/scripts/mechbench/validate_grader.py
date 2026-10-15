"""Validate the mechanism-design grader: a hand-sized fixture must pass every task (feasibility), and each deliberately
broken variant must fail the check it targets. Writes validation.json next to the dataset.

  tmp/cq-env/bin/python scripts/mechbench/validate_grader.py --tasks TASKS.jsonl --out DIR
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixture_scissor as F  # noqa: E402
import grade as G  # noqa: E402

PY = sys.executable
SY = {"S700MC": 700.0, "10.9": 940.0, "12.9": 1080.0}


def size(spec: dict, margin: float = 1.12) -> dict:
    """Hand sizing at the lowest height (two-force arms; T = W / tan(theta), C = W / (2 sin(theta)))."""
    W, h0, h1, fs = spec["rated_load_N"], spec["h_min_mm"], spec["h_max_mm"], spec["fs_yield"]
    r = min(17.0, (h0 - 12) / 4 - 0.5)                            # end radius limited by the collapsed height
    zb, ztop = r + 4, r + 6
    L = math.ceil((h1 - zb - ztop) / (2 * math.sin(math.radians(70))))
    th0 = math.asin((h0 - zb - ztop) / (2 * L))
    T, C = W / math.tan(th0), W / (2 * math.sin(th0))
    pin_d = math.ceil(math.sqrt(4 * C * fs * margin / (2 * math.pi * 0.577 * SY["S700MC"])))
    t = 2.5
    r = max(r, (pin_d + 0.2 + C * fs * margin / (2 * t * SY["S700MC"])) / 2)
    while (h0 - 12) / 4 - 0.5 < r and t < 6:                      # height-limited end radius: thicker plates instead
        t += 0.5
        r = max(12.0, (pin_d + 0.2 + C * fs * margin / (2 * t * SY["S700MC"])) / 2)
    zb, ztop = r + 4, r + 6
    L = math.ceil((h1 - zb - ztop) / (2 * math.sin(math.radians(70))))
    th0 = math.asin((h0 - zb - ztop) / (2 * L))
    T, C = W / math.tan(th0), W / (2 * math.sin(th0))
    minor = math.ceil(2 * math.sqrt(T * fs * margin / SY["12.9"] / math.pi) * 10) / 10
    w = max(minor / 2 + 4, 10.0)
    return {"rated_load_N": W, "h_min_mm": h0, "h_max_mm": h1, "arm_pin_spacing_mm": L, "arm_depth_mm": 2 * r, "end_radius_mm": round(r, 2),
            "plate_t_mm": t, "inner_half_width_mm": round(w, 1), "gap_mm": 1.0, "web_setback_mm": round(max(r + 6, 0.75 * minor + 14), 1),
            "pivot_sep_mm": round(2 * r + 4, 1), "base_pivot_z_mm": round(zb, 2), "saddle_top_above_pivot_mm": round(ztop, 2), "pin_d_mm": pin_d,
            "screw_d_mm": round(minor * 1.18, 1), "screw_minor_d_mm": minor, "screw_overhang_mm": 25, "screw_head_d_mm": round(minor * 1.8, 1),
            "screw_head_t_mm": 10, "trunnion_mm": round(max(2 * minor, 2 * (w - 1)) * 0.9, 1), "lug_t_mm": 4, "base_len_mm": round(4 * r + 40, 1),
            "base_wid_mm": round(2 * (w + 2.5 + 3), 1), "base_t_mm": 4, "saddle_len_mm": round(2 * r + 4, 1), "saddle_t_mm": 5,
            "mat_arm": "S700MC", "mat_body": "S700MC", "mat_pin": "10.9", "mat_screw": "12.9"}


def submission(params: dict, d: Path, verdict: str = "meets") -> Path:
    if d.exists():
        shutil.rmtree(d)
    F.build(copy.deepcopy(params), d)
    shutil.copy2(HERE / "fixture_scissor.py", d / "main.py")
    (d / "params.json").write_text(json.dumps(params, indent=1) + "\n")
    a = json.loads((d / "analysis.json").read_text())
    a["verdict"] = verdict
    (d / "analysis.json").write_text(json.dumps(a, indent=1) + "\n")
    return d


def failing(r: dict) -> list[str]:
    return sorted(k for k, v in r["checks"].items() if not v.get("ok"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    tasks = [json.loads(l) for l in a.tasks.read_text().splitlines() if l.strip()]
    work = a.out / "work"
    work.mkdir(parents=True, exist_ok=True)
    report = {"feasibility": [], "broken_variants": []}
    for task in tasks:
        p = size(task["spec"])
        r = G.grade(task, submission(p, work / task["task_id"]), PY)
        for _ in range(4):                                        # thicken plates if the hand sizing fell short
            if r["passed"] or "strength" not in failing(r):
                break
            p["plate_t_mm"] = round(p["plate_t_mm"] + 0.5, 2)
            r = G.grade(task, submission(p, work / task["task_id"]), PY)
        report["feasibility"].append(dict(task_id=task["task_id"], passed=r["passed"], failing=failing(r),
                                          mass_kg=r["checks"]["economy"]["mass_kg"], budget_kg=task["spec"]["mass_budget_kg"],
                                          min_yield_fs=r["checks"].get("strength", {}).get("min_yield_fs"),
                                          min_buckling_fs=r["checks"].get("strength", {}).get("min_buckling_fs"),
                                          governing=r["checks"].get("strength", {}).get("governing"), params=p))
        print(json.dumps({k: v for k, v in report["feasibility"][-1].items() if k != "params"}), flush=True)
    # broken variants on the first feasible task
    base_task = next(t for t, f in zip(tasks, report["feasibility"]) if f["passed"])
    p0 = next(f["params"] for f in report["feasibility"] if f["task_id"] == base_task["task_id"])
    variants = []

    def add(name, target, d, note):
        r = G.grade(base_task, d, PY)
        variants.append(dict(variant=name, targets=target, failing=failing(r), caught=target in failing(r), note=note,
                             problems={k: v.get("problems") for k, v in r["checks"].items() if not v.get("ok")}))
        print(json.dumps({k: variants[-1][k] for k in ("variant", "targets", "failing", "caught")}), flush=True)

    d = submission(p0, work / "v_floating")
    asm = json.loads((d / "assembly.json").read_text())
    asm["joints"] = [j for j in asm["joints"] if "arm_ul" not in j["parts"] or j["type"] == "gear"]
    asm["joints"] = [j for j in asm["joints"] if j["name"] != "gear_top"]
    (d / "assembly.json").write_text(json.dumps(asm))
    add("floating arm (its mates removed)", "mates", d, "post: 'assembly mates didn't exist'")
    d = submission(p0, work / "v_unrealised")
    asm = json.loads((d / "assembly.json").read_text())
    for j in asm["joints"]:
        if j["name"] == "side_ul":
            j["origin"][0] += 4.0
    (d / "assembly.json").write_text(json.dumps(asm))
    add("declared pivot with no pin or hole there", "mates", d, "a mate that is only declared, not modelled")
    add("interpenetrating arms (negative gap)", "motion", submission(dict(p0, gap_mm=-3.0), work / "v_clash"),
        "StoryGold: 'parts interpenetrate'")
    add("load path ignored (thin plates, small screw)", "strength",
        submission(dict(p0, plate_t_mm=1.0, screw_minor_d_mm=round(p0["screw_minor_d_mm"] * 0.55, 1), pin_d_mm=6), work / "v_weak"),
        "post: 'the load path was never considered'")
    add("overbuilt (everything doubled)", "economy",
        submission(dict(p0, plate_t_mm=p0["plate_t_mm"] * 2.4, screw_minor_d_mm=p0["screw_minor_d_mm"] * 1.6,
                        screw_d_mm=p0["screw_d_mm"] * 1.6, screw_head_d_mm=p0["screw_head_d_mm"] * 1.6,
                        trunnion_mm=p0["trunnion_mm"] * 1.6, inner_half_width_mm=p0["inner_half_width_mm"] * 1.6), work / "v_heavy"),
        "post: 'passed by making every part so overbuilt'")
    d = submission(p0, work / "v_hardcoded")
    src = (d / "main.py").read_text().replace('    L, s, zb, ztop = p["arm_pin_spacing_mm"],', f'    L, s, zb, ztop = {p0["arm_pin_spacing_mm"]},')
    src = src.replace('    L, bw, t, r, w, e, dp = p["arm_pin_spacing_mm"],', f'    L, bw, t, r, w, e, dp = {p0["arm_pin_spacing_mm"]},')
    (d / "main.py").write_text(src)
    add("geometry not driven by its dimensions (hard-coded arm length)", "dimensions", d, "post: 'sketches had no real dimensions'")
    d = submission(p0, work / "v_report")
    an = json.loads((d / "analysis.json").read_text())
    th = math.asin((0.5 * (p0["h_min_mm"] + p0["h_max_mm"]) - p0["base_pivot_z_mm"] - p0["saddle_top_above_pivot_mm"]) / (2 * p0["arm_pin_spacing_mm"]))
    an["screw_tension_N"] = p0["rated_load_N"] / math.tan(th)                   # checked at mid height, not the worst case
    an["max_arm_compression_N"] = p0["rated_load_N"] / (2 * math.sin(th))
    (d / "analysis.json").write_text(json.dumps(an))
    add("report checks mid height instead of the lowest", "report", d, "worst case never considered")
    d = submission(dict(p0, plate_t_mm=1.0, screw_minor_d_mm=round(p0["screw_minor_d_mm"] * 0.55, 1), pin_d_mm=6), work / "v_falsepass", verdict="meets")
    add("weak design that claims to meet the requirements", "report", d, "post: 'the FEA passed'")
    report["broken_variants"] = variants
    report["all_feasible"] = all(f["passed"] for f in report["feasibility"])
    report["all_variants_caught"] = all(v["caught"] for v in variants)
    (a.out / "validation.json").write_text(json.dumps(report, indent=1, default=float) + "\n")
    print(json.dumps({"all_feasible": report["all_feasible"], "all_variants_caught": report["all_variants_caught"]}))


if __name__ == "__main__":
    main()
