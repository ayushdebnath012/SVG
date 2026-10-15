"""Ghost-geometry CAD-edit traps, modelled on Astra's propeller miss (it placed a boss on a cone's nominal apex after a
through-bore had already cut the apex away, leaving the boss floating).

In every task an earlier operation (a bore through a tapered tip, a tapered extrusion, a chamfer, an inward shell, a
hexagon given by its circumscribed diameter) moves or shrinks the surface the instruction refers to. The edit is
correct only if it uses the actual geometry, not the nominal parameters. Same one-shot protocol as the 252-task CAD-edit
run (system prompt, input format, JSON line patch, medium effort, 6000-token cap, no tools).

  tmp/cq-env/bin/python scripts/astra_traps/ghost_geometry.py build   # writes tasks + validates checkers (free)
  tmp/hosted-harness-env/bin/python scripts/astra_traps/ghost_geometry.py run --budget-usd 1.0   # paid, one call per task
  tmp/cq-env/bin/python scripts/astra_traps/ghost_geometry.py score
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/astra-ghost-geometry-20261015"
SYSTEM = json.loads((ROOT / "data/multisource-cad-edits-v1/manifest.json").read_text())["system"]
ENDPOINT = "https://api.openai.com/v1/chat/completions"
P_IN, P_OUT = 12.5, 50.0


def wrap(body: list[str]) -> str:
    return "\n".join(["import cadquery as cq", "result = (", *body, ")", "show_object(result)"])


def tasks() -> list[dict]:
    T = []
    # 1. bored apex: the bore removes the cone tip, so the hub's highest material is where cone radius = bore radius
    for i, (H, R, R1, T_, rt, d, D, t) in enumerate([(20.0, 15.0, 13.0, 8.0, 1.5, 7.0, 16.0, 3.0),
                                                       (16.0, 12.0, 10.5, 6.0, 1.2, 6.0, 12.0, 2.5),
                                                       (24.0, 18.0, 16.0, 10.0, 2.0, 9.0, 20.0, 4.0)]):
        base = wrap([f'    cq.Workplane("XY")', f"    .cylinder({H}, {R})", '    .faces(">Z").workplane()', f"    .circle({R1})",
                     f"    .workplane(offset={T_})", f"    .circle({rt})", "    .loft(combine=True)", '    .faces(">Z").workplane()', f"    .hole({d})"])
        z_top = H / 2 + T_ * (R1 - d / 2) / (R1 - rt)
        T.append(dict(id=f"bored-apex-{i+1}", family="bored-apex", code=base, check="seated_boss", z_top=z_top, D=D, t=t,
                      instruction=f"Add a flat round boss {D:g} mm in diameter and {t:g} mm thick, centred on the central axis and "
                                  f"seated on top of the tapered hub so that it is fused to the hub material.",
                      naive=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H/2 + T_}).circle({D/2}).extrude({t}))\nshow_object(result)"),
                      reference=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={z_top - 0.3:.6f}).circle({D/2}).extrude({t}))\nshow_object(result)")))
    # 2. tapered extrusion: the top face is smaller than the sketch by 2 h tan(a)
    for i, (L, W, H, a, c) in enumerate([(60.0, 40.0, 25.0, 8.0, 2.0), (80.0, 50.0, 30.0, 5.0, 3.0), (50.0, 50.0, 20.0, 12.0, 2.5)]):
        base = wrap(['    cq.Workplane("XY")', f"    .rect({L}, {W})", f"    .extrude({H}, taper={a})"])
        s = 2 * H * math.tan(math.radians(a))
        T.append(dict(id=f"tapered-cap-{i+1}", family="tapered-cap", code=base, check="iou",
                      instruction=f"Add a {c:g} mm thick cover plate on top of the block whose outline exactly matches the outline of the top face.",
                      naive=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).rect({L}, {W}).extrude({c}))\nshow_object(result)"),
                      reference=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).rect({L - s:.6f}, {W - s:.6f}).extrude({c}))\nshow_object(result)")))
    # 3. chamfered top: the flat top face has radius R - c
    for i, (R, H, c, w, h) in enumerate([(25.0, 30.0, 4.0, 2.0, 3.0), (40.0, 20.0, 6.0, 3.0, 4.0), (18.0, 40.0, 3.0, 1.5, 2.5)]):
        base = wrap(['    cq.Workplane("XY")', f"    .circle({R})", f"    .extrude({H})", '    .faces(">Z")', f"    .chamfer({c})"])
        ro = R - c
        T.append(dict(id=f"chamfer-collar-{i+1}", family="chamfer-collar", code=base, check="iou",
                      instruction=f"Add a {h:g} mm tall ring on the flat top face, {w:g} mm wall thickness, whose outer edge is flush with the "
                                  f"outer edge of the flat top face.",
                      naive=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).circle({R}).circle({R - w}).extrude({h}))\nshow_object(result)"),
                      reference=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).circle({ro}).circle({ro - w}).extrude({h}))\nshow_object(result)")))
    # 4. inward shell: inner span W - 2t, inner floor at z = t
    for i, (L, W, H, t, rb, rh) in enumerate([(100.0, 60.0, 40.0, 3.0, 3.0, 12.0), (80.0, 50.0, 30.0, 4.0, 2.0, 10.0), (120.0, 70.0, 50.0, 5.0, 4.0, 15.0)]):
        base = wrap(['    cq.Workplane("XY")', f"    .box({L}, {W}, {H}, centered=(True, True, False))", '    .faces(">Z")', f"    .shell(-{t})"])
        T.append(dict(id=f"shell-rib-{i+1}", family="shell-rib", code=base, check="iou",
                      instruction=f"Add a stiffening rib inside the box at its middle, parallel to the short side: {rb:g} mm thick and {rh:g} mm tall, "
                                  f"standing on the inner floor and spanning exactly between the two long inner walls (touching them, not passing through them).",
                      naive=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').box({rb}, {W}, {rh}, centered=(True, True, False)))\nshow_object(result)"),
                      reference=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').box({rb}, {W - 2 * t}, {rh}, centered=(True, True, False)).translate((0, 0, {t})))\nshow_object(result)")))
    # 5. hexagon given by circumscribed diameter: across flats = d cos 30
    for i, (d, H, w, h) in enumerate([(30.0, 12.0, 3.0, 8.0), (24.0, 10.0, 2.5, 6.0), (40.0, 15.0, 4.0, 10.0)]):
        base = wrap(['    cq.Workplane("XY")', f"    .polygon(6, {d})", f"    .extrude({H})"])
        af = d * math.cos(math.radians(30))
        T.append(dict(id=f"hex-collar-{i+1}", family="hex-collar", code=base, check="iou",
                      instruction=f"Add a cylindrical collar of {w:g} mm wall thickness and {h:g} mm height on top of the hexagonal prism, centred on it, "
                                  f"whose inner diameter equals the prism's distance across flats.",
                      naive=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).circle({d / 2 + w}).circle({d / 2}).extrude({h}))\nshow_object(result)"),
                      reference=base.replace("show_object(result)", f"result = result.union(cq.Workplane('XY').workplane(offset={H}).circle({af / 2 + w:.6f}).circle({af / 2:.6f}).extrude({h}))\nshow_object(result)")))
    return T


def user_input(t: dict) -> str:
    return f"Representation: cadquery\nOriginal CAD (line indices are implicit):\n{t['code']}Edit instruction:\n{t['instruction']}"


def execute(code: str):
    ns = {"show_object": lambda *a, **k: None}
    exec(code, ns)
    r = ns["result"]
    return r.val() if hasattr(r, "val") else r


def judge(t: dict, code: str) -> dict:
    import cadquery as cq  # noqa: F401
    try:
        s = execute(code)
    except Exception as e:                                        # noqa: BLE001
        return dict(ok=False, why=f"does not execute: {type(e).__name__}: {str(e)[:120]}")
    solids = s.Solids()
    if len(solids) != 1:
        return dict(ok=False, why=f"{len(solids)} solids (added feature not attached)")
    if t["check"] == "iou":
        ref = execute(t["reference"])
        inter = ref.intersect(s).Volume()
        iou = inter / (ref.Volume() + s.Volume() - inter)
        return dict(ok=iou >= 0.995, iou=round(iou, 5), why="" if iou >= 0.995 else f"geometry differs from the instruction (IoU {iou:.4f})")
    base = execute(t["code"])
    add = s.cut(base)
    bb = add.BoundingBox()
    D, th, z = t["D"], t["t"], t["z_top"]
    errs = []
    if abs((bb.xmax - bb.xmin) - D) > 0.1 or abs((bb.ymax - bb.ymin) - D) > 0.1 or abs(bb.xmin + bb.xmax) > 0.1 or abs(bb.ymin + bb.ymax) > 0.1:
        errs.append(f"boss footprint {bb.xmax - bb.xmin:.2f} x {bb.ymax - bb.ymin:.2f} mm, centre ({(bb.xmin + bb.xmax) / 2:.2f}, {(bb.ymin + bb.ymax) / 2:.2f})")
    zb = bb.zmax - th                                             # underside of a boss of the requested thickness
    if zb > z + 0.02:
        errs.append(f"boss underside at z = {zb:.3f} mm is above the hub's highest material (z = {z:.3f} mm)")
    if zb < z - 1.0:
        errs.append(f"boss sunk {z - zb:.2f} mm into the hub")
    return dict(ok=not errs, why="; ".join(errs), boss_underside_z=round(zb, 4), hub_top_z=round(z, 4))


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = tasks()
    val = []
    for t in rows:
        r, n = judge(t, t["reference"]), judge(t, t["naive"])
        val.append(dict(id=t["id"], reference_accepted=r["ok"], naive_rejected=not n["ok"], naive_why=n["why"]))
        print(json.dumps(val[-1]), flush=True)
    (OUT / "tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in rows))
    (OUT / "validation.json").write_text(json.dumps(dict(all_ok=all(v["reference_accepted"] and v["naive_rejected"] for v in val), tasks=val), indent=1) + "\n")
    print("checker validation:", all(v["reference_accepted"] and v["naive_rejected"] for v in val))


def run(budget: float) -> None:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY unavailable; no calls made")
    rows = [json.loads(l) for l in (OUT / "tasks.jsonl").read_text().splitlines()]
    spent = sum(json.loads(p.read_text()).get("cost_usd", 0) for p in OUT.glob("*/result.json"))
    for t in rows:
        d = OUT / t["id"]
        if (d / "result.json").exists():
            continue
        if spent + 6000 * P_OUT / 1e6 + 0.01 > budget:                # never start a call that could cross the cap
            print("BUDGET-STOP", t["id"], f"spent ${spent:.3f}", flush=True)
            break
        d.mkdir(parents=True, exist_ok=True)
        payload = {"model": "gpt-6-astra", "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_input(t)}],
                   "reasoning_effort": "medium", "max_completion_tokens": 6000, "store": False}
        req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                raw = json.load(resp)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace").replace(key, "[REDACTED]")
            (d / "result.json").write_text(json.dumps(dict(id=t["id"], status="api_error", error=body[:600], cost_usd=0)) + "\n")
            print("API ERROR", t["id"], body[:200], flush=True)
            if "insufficient_quota" in body:
                break
            continue
        u = raw.get("usage") or {}
        cost = (u.get("prompt_tokens", 0) * P_IN + u.get("completion_tokens", 0) * P_OUT) / 1e6
        spent += cost
        (d / "response.txt").write_text(raw["choices"][0]["message"].get("content") or "")
        (d / "result.json").write_text(json.dumps(dict(id=t["id"], status="completed", finish_reason=raw["choices"][0].get("finish_reason"),
                                                       usage=u, cost_usd=round(cost, 5), seconds=round(time.time() - t0, 1), response_id=raw.get("id"))) + "\n")
        print(f"END {t['id']} ${cost:.4f} total ${spent:.3f}", flush=True)


def score() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from cad_edit_contracts import apply
    rows = [json.loads(l) for l in (OUT / "tasks.jsonl").read_text().splitlines()]
    out = []
    for t in rows:
        d = OUT / t["id"]
        if not (d / "response.txt").exists():
            continue
        txt = (d / "response.txt").read_text()
        try:
            code = apply(t["code"], json.loads(txt), "cadquery")
        except Exception as e:                                    # noqa: BLE001
            out.append(dict(id=t["id"], family=t["family"], ok=False, why=f"patch unusable: {type(e).__name__}: {str(e)[:100]}"))
            continue
        out.append(dict(id=t["id"], family=t["family"], **judge(t, code)))
    for r in out:
        print(f"{r['id']:18s} {'PASS' if r['ok'] else 'FAIL'}  {r.get('why', '')}")
    (OUT / "score.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"failed {sum(not r['ok'] for r in out)} of {len(out)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["build", "run", "score"])
    ap.add_argument("--budget-usd", type=float, default=1.0)
    a = ap.parse_args()
    {"build": build, "run": lambda: run(a.budget_usd), "score": score}[a.command]()
