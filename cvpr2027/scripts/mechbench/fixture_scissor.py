"""Parametric scissor-jack design used to validate the mechanism-design grader (not an answer key).

Writes a submission in the task contract: params.json, main.py (this file), parts/*.step, assembly.json, analysis.json.
Geometry, x horizontal, z up, y out of plane, collapsed pose:
  base with two pivot lugs at x = -s/2, +s/2, height z_b;   four channel arms of pin spacing L (lower pair geared
  at the base, upper pair geared at the saddle);   trunnions at the side nodes carry the arm pins;   a lead screw
  fixed in the right trunnion and running through the left one sets the trunnion spacing (the drive).
Lower-arm side plates sit at |y| in [w, w+t]; upper-arm plates nest outside at [w+t+g, w+2t+g]; webs stop e mm short
of each pin so they clear the trunnions and the screw.

  python fixture_scissor.py --params params.json --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cadquery as cq

DENSITY = {"S355": 7850, "S700MC": 7850, "10.9": 7850, "12.9": 7850}


def arm(p: dict, a: tuple, b: tuple, web_side: int) -> cq.Workplane:
    """Channel arm between pin points a and b (x, z): two side plates plus a web offset to web_side (+1 up / -1 down)."""
    L, bw, t, r, w, e, dp = p["arm_pin_spacing_mm"], p["arm_depth_mm"], p["plate_t_mm"], p["end_radius_mm"], p["_w"], p["web_setback_mm"], p["pin_d_mm"]
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    if b[0] < a[0]:
        web_side = -web_side                                                  # local +z maps to global -z when the arm points left
    prof = cq.Workplane("XZ").center(L / 2, 0).slot2D(L + 2 * r, 2 * r, 0)
    plate = prof.extrude(-t)                                                    # XZ workplane normal is -y; extrude(-t) goes +y
    holes = cq.Workplane("XZ").pushPoints([(0, 0), (L, 0)]).circle(dp / 2 + 0.1).extrude(-t)
    plate = plate.cut(holes)
    plates = plate.translate((0, w, 0)).union(plate.translate((0, -w - t, 0)))
    web = cq.Workplane("XY").box(L - 2 * e, 2 * (w + t), t).translate((L / 2, 0, web_side * (bw / 2 - t / 2)))
    body = plates.union(web)
    return body.rotate((0, 0, 0), (0, 1, 0), -ang).translate((a[0], 0, a[1]))


def build(p: dict, out: Path) -> None:
    W = p["rated_load_N"]
    L, s, zb, ztop = p["arm_pin_spacing_mm"], p["pivot_sep_mm"], p["base_pivot_z_mm"], p["saddle_top_above_pivot_mm"]
    t, g, dp, ds = p["plate_t_mm"], p["gap_mm"], p["pin_d_mm"], p["screw_d_mm"]
    p["_w"] = w = p["inner_half_width_mm"]
    wu = w + t + g                                                             # upper-arm plate inner face
    theta = math.asin((p["h_min_mm"] - zb - ztop) / (2 * L))
    zs, xs = zb + L * math.sin(theta), s / 2 + L * math.cos(theta)              # side node
    zt = zb + 2 * L * math.sin(theta)                                           # saddle pivots
    parts = {}
    # base: plate + two lugs inside the lower-arm plates, pins along y through both lower-arm plates
    base = cq.Workplane("XY").box(p["base_len_mm"], p["base_wid_mm"], p["base_t_mm"], centered=(True, True, False))
    for x in (-s / 2, s / 2):
        tl, r_ = p["lug_t_mm"], p["end_radius_mm"]
        for sy in (1, -1):
            lug = cq.Workplane("XY").box(2 * r_, tl, zb + r_, centered=(True, True, False)).translate((x, sy * (w - g - tl / 2), 0))
            base = base.union(lug)
        pin = cq.Workplane("XZ").center(x, zb).circle(dp / 2).extrude(-(w + t + 1)).union(
              cq.Workplane("XZ").center(x, zb).circle(dp / 2).extrude(w + t + 1))
        base = base.union(pin)
    parts["base"] = base
    parts["arm_ll"] = arm(p, (-s / 2, zb), (-xs, zs), -1)
    parts["arm_lr"] = arm(p, (s / 2, zb), (xs, zs), -1)
    pu = dict(p, _w=wu)
    parts["arm_ul"] = arm(pu, (-xs, zs), (-s / 2, zt), +1)
    parts["arm_ur"] = arm(pu, (xs, zs), (s / 2, zt), +1)
    # saddle: top pad + lugs inside the upper-arm plates, pins through the upper-arm plates
    sad = cq.Workplane("XY").box(p["saddle_len_mm"], 2 * (wu + t), p["saddle_t_mm"], centered=(True, True, False)).translate(
        (0, 0, zt + ztop - p["saddle_t_mm"]))
    for x in (-s / 2, s / 2):
        tl, r_ = p["lug_t_mm"], p["end_radius_mm"]
        hgt = zt + ztop - p["saddle_t_mm"] - (zt - r_)
        for sy in (1, -1):
            lug = cq.Workplane("XY").box(2 * r_, tl, hgt, centered=(True, True, False)).translate((x, sy * (wu - g - tl / 2), zt - r_))
            sad = sad.union(lug)
        pin = cq.Workplane("XZ").center(x, zt).circle(dp / 2).extrude(-(wu + t + 1)).union(
              cq.Workplane("XZ").center(x, zt).circle(dp / 2).extrude(wu + t + 1))
        sad = sad.union(pin)
    parts["saddle"] = sad
    # trunnions at the side nodes, with a cross hole for the screw and pins through lower and upper plates
    a = p["trunnion_mm"]
    for side, x in (("l", -xs), ("r", xs)):
        blk = cq.Workplane("XY").box(a, 2 * (w - g), a).translate((x, 0, zs))
        blk = blk.cut(cq.Workplane("YZ").center(0, zs).circle(ds / 2 + 0.3).extrude(a, both=True).translate((x, 0, 0)))
        stub = cq.Workplane("XZ").center(x, zs).circle(dp / 2).extrude(-(wu + t + 1 - (w - g - 2))).translate((0, w - g - 2, 0))
        stub2 = stub.mirror("XZ")
        parts[f"trunnion_{side}"] = blk.union(stub).union(stub2)
    # lead screw along x through both trunnions; threaded length modelled at the thread minor diameter, head at the right
    x0, x1 = -xs - a / 2 - p["screw_overhang_mm"], xs + max(a / 2, p["end_radius_mm"] + 1.0)   # head clear of the arm end plates
    screw = cq.Workplane("YZ").center(0, zs).circle(p["screw_minor_d_mm"] / 2).extrude(x1 - x0).translate((x0, 0, 0))
    head = cq.Workplane("YZ").center(0, zs).circle(p["screw_head_d_mm"] / 2).extrude(p["screw_head_t_mm"]).translate((x1 + 0.5, 0, 0))
    collar = cq.Workplane("YZ").center(0, zs).circle(ds / 2).extrude(x1 + 0.5 - (xs + a / 2)).translate((xs + a / 2, 0, 0))
    parts["screw"] = screw.union(head).union(collar)
    out.mkdir(parents=True, exist_ok=True)
    (out / "parts").mkdir(exist_ok=True)
    mats = {"base": p["mat_body"], "saddle": p["mat_body"], "arm_ll": p["mat_arm"], "arm_lr": p["mat_arm"], "arm_ul": p["mat_arm"],
            "arm_ur": p["mat_arm"], "trunnion_l": p["mat_pin"], "trunnion_r": p["mat_pin"], "screw": p["mat_screw"]}
    roles = {"base": "base", "saddle": "saddle", "screw": "screw", "trunnion_l": "trunnion", "trunnion_r": "trunnion"}
    for name, wp in parts.items():
        cq.exporters.export(wp, str(out / "parts" / f"{name}.step"))
    R = lambda n, A, B, x, z: {"name": n, "type": "revolute", "parts": [A, B], "origin": [x, 0.0, z]}
    joints = [R("base_l", "base", "arm_ll", -s / 2, zb), R("base_r", "base", "arm_lr", s / 2, zb),
              {"name": "gear_low", "type": "gear", "parts": ["arm_ll", "arm_lr"], "ratio": -1.0},
              R("top_l", "saddle", "arm_ul", -s / 2, zt), R("top_r", "saddle", "arm_ur", s / 2, zt),
              {"name": "gear_top", "type": "gear", "parts": ["arm_ul", "arm_ur"], "ratio": -1.0},
              R("side_ll", "trunnion_l", "arm_ll", -xs, zs), R("side_ul", "trunnion_l", "arm_ul", -xs, zs),
              R("side_lr", "trunnion_r", "arm_lr", xs, zs), R("side_ur", "trunnion_r", "arm_ur", xs, zs),
              {"name": "screw_fix", "type": "fixed", "parts": ["screw", "trunnion_r"]},
              {"name": "nut", "type": "prismatic", "parts": ["trunnion_l", "screw"], "origin": [-xs, 0.0, zs], "axis": [1.0, 0.0, 0.0]},
              {"name": "drive", "type": "distance", "parts": ["trunnion_l", "trunnion_r"], "point_a": [-xs, 0.0, zs], "point_b": [xs, 0.0, zs]}]
    th1 = math.asin((p["h_max_mm"] - zb - ztop) / (2 * L))
    asm = {"units": "mm", "plane": "xz", "ground": "base",
           "parts": [{"name": n, "step": f"parts/{n}.step", "material": mats[n], "role": roles.get(n, "arm")} for n in parts],
           "joints": joints, "driver": "drive", "driver_range_mm": [2 * xs, s + 2 * L * math.cos(th1)],
           "load_point": [0.0, 0.0, zt + ztop]}
    (out / "assembly.json").write_text(json.dumps(asm, indent=1) + "\n")
    # hand analysis at the governing (lowest) pose: two-force arms, T = W / tan(theta), C = W / (2 sin(theta))
    T, C = W / math.tan(theta), W / (2 * math.sin(theta))
    mass = sum(wp.val().Volume() * 1e-9 * DENSITY[mats[n]] for n, wp in parts.items())
    (out / "analysis.json").write_text(json.dumps({"governing_height_mm": p["h_min_mm"], "screw_tension_N": T,
                                                   "max_arm_compression_N": C, "mass_kg": mass}, indent=1) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=Path, default=Path(__file__).with_name("params.json"))
    ap.add_argument("--out", type=Path, default=Path("."))
    a = ap.parse_args()
    build(json.loads(a.params.read_text()), a.out)
