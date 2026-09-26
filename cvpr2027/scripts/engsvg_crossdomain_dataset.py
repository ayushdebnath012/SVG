"""Build a leakage-safe, cross-domain dataset for text-guided engineering SVG edits."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
from html import escape
import json
import math
from pathlib import Path
import random
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from svgpatchlab.core import (  # noqa: E402
    apply_patch,
    build_scene,
    build_scene_graph,
    derive_structural_patch,
    generic_svg_policy,
    parse_patch,
    validate_patch,
)
from svgpatchlab.core.xml import normalized_tree, parse_svg  # noqa: E402


VERSION = "engsvg-crossdomain-edit-v1"
SEED = 260925
FAMILIES = ("building_plan", "furniture_table", "mechanical_part", "dc_circuit", "water_piping")
DESIGNS_PER_FAMILY = 500
EDITS_PER_DESIGN = 4
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def _svg(parts) -> str:
    text = "\n".join(parts)
    parse_svg(text)
    return text


def _building_model(rng: random.Random, index: int) -> dict:
    width = rng.randrange(7200, 10401, 100)
    height = rng.randrange(4800, 7201, 100)
    partition = rng.randrange(3000, width - 2800, 100)
    door = rng.choice((800, 900, 1000, 1100))
    door_x = rng.randrange(800, max(801, partition - door - 500), 100)
    return {"family": "building_plan", "width_mm": width, "height_mm": height,
            "partition_x_mm": partition, "door_x_mm": door_x, "door_width_mm": door,
            "left_room": f"Office {index % 17 + 1}", "right_room": "Workshop"}


def _verify_building(model: dict) -> dict:
    w, h = model["width_mm"], model["height_mm"]
    p, x, door = model["partition_x_mm"], model["door_x_mm"], model["door_width_mm"]
    violations = []
    if min(p, w - p) < 2400:
        violations.append("each room must retain at least 2400 mm clear width")
    if door < 800:
        violations.append("door clear width is below 800 mm")
    if door > 1200:
        violations.append("door clear width exceeds the supported single-door range")
    if x < 300 or x + door > w - 300:
        violations.append("door opening is too close to an exterior corner")
    if h < 2400:
        violations.append("plan depth is below the minimum usable dimension")
    return {"method": "building_plan_geometry_and_clearance_rules", "pass": not violations,
            "violations": violations, "room_widths_mm": [p, w - p],
            "door_clear_width_mm": door,
            "criteria": {"minimum_room_width_mm": 2400, "minimum_door_width_mm": 800,
                         "minimum_corner_clearance_mm": 300}}


def _render_building(model: dict) -> str:
    w, h = model["width_mm"], model["height_mm"]
    scale = min(760 / w, 460 / h); x0, y0 = 120, 100
    sw, sh, px = w * scale, h * scale, x0 + model["partition_x_mm"] * scale
    dx, dw = x0 + model["door_x_mm"] * scale, model["door_width_mm"] * scale
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700">',
        '<rect id="background" width="1000" height="700" fill="white"/>',
        '<text id="title" x="40" y="45" font-size="24" font-weight="bold">Building plan</text>',
        '<g id="walls" fill="none" stroke="#172b4d" stroke-width="8" stroke-linecap="square">',
        f'<path id="outer-wall" d="M{x0} {y0} H{x0+sw} V{y0+sh} H{dx+dw} M{dx} {y0+sh} H{x0} Z"/>',
        f'<line id="partition" x1="{px}" y1="{y0}" x2="{px}" y2="{y0+sh}"/>',
        '</g>',
        '<g id="door" fill="none" stroke="#2878b5" stroke-width="3">',
        f'<line id="door-leaf" x1="{dx}" y1="{y0+sh}" x2="{dx}" y2="{y0+sh-dw}"/>',
        f'<path id="door-swing" d="M{dx+dw} {y0+sh} A{dw} {dw} 0 0 0 {dx} {y0+sh-dw}"/>',
        '</g>',
        f'<text id="left-room" x="{x0 + model["partition_x_mm"]*scale/2}" y="{y0+sh/2}" font-size="20" text-anchor="middle">{escape(model["left_room"])}</text>',
        f'<text id="right-room" x="{px + (w-model["partition_x_mm"])*scale/2}" y="{y0+sh/2}" font-size="20" text-anchor="middle">{escape(model["right_room"])}</text>',
        f'<text id="width-note" x="{x0+sw/2}" y="{y0+sh+55}" font-size="16" text-anchor="middle">Overall width {_fmt(w)} mm</text>',
        f'<text id="door-note" x="{dx+dw/2}" y="{y0+sh+30}" font-size="14" text-anchor="middle">Door {_fmt(model["door_width_mm"])} mm</text>',
        f'<text id="depth-note" x="55" y="{y0+sh/2}" font-size="16" transform="rotate(-90 55 {y0+sh/2})" text-anchor="middle">Depth {_fmt(h)} mm</text>',
        '</svg>',
    ]
    return _svg(parts)


def _building_edits(model: dict, rng: random.Random, index: int):
    edits = []
    target = copy.deepcopy(model); target["width_mm"] += rng.choice((400, 600, 800))
    edits.append((f'Extend the building width to {target["width_mm"]} mm.', target, "dimension"))
    target = copy.deepcopy(model); target["partition_x_mm"] += rng.choice((-300, 300))
    edits.append((f'Move the internal partition to x={target["partition_x_mm"]} mm.', target, "geometry"))
    target = copy.deepcopy(model); target["door_width_mm"] = 650 if index % 8 == 0 else rng.choice((850, 950, 1050))
    edits.append((f'Set the exterior door clear width to {target["door_width_mm"]} mm.', target, "constraint"))
    target = copy.deepcopy(model); target["left_room"] = rng.choice(("Laboratory", "Meeting room", "Design studio"))
    edits.append((f'Rename the left room to {target["left_room"]}.', target, "annotation"))
    return edits


def _table_model(rng: random.Random, index: int) -> dict:
    return {"family": "furniture_table", "width_mm": rng.randrange(1200, 2201, 50),
            "height_mm": rng.randrange(700, 951, 10), "top_thickness_mm": rng.randrange(45, 76, 5),
            "top_depth_mm": rng.randrange(500, 801, 25), "leg_width_mm": rng.randrange(55, 101, 5),
            "leg_depth_mm": rng.randrange(55, 101, 5), "leg_inset_mm": rng.randrange(80, 181, 10),
            "load_N": rng.randrange(1200, 5001, 100), "E_mpa": 11000,
            "allow_bending_mpa": 35, "allow_compression_mpa": 18}


def _verify_table(model: dict) -> dict:
    width, height = model["width_mm"], model["height_mm"]
    span = width - 2 * model["leg_inset_mm"]
    load, e = model["load_N"], model["E_mpa"]
    b, h = model["top_depth_mm"], model["top_thickness_mm"]
    inertia = b * h**3 / 12
    moment = load * span / 8
    stress = moment * (h / 2) / inertia
    distributed = load / span
    deflection = 5 * distributed * span**4 / (384 * e * inertia)
    leg_area = model["leg_width_mm"] * model["leg_depth_mm"]
    leg_stress = load / 2 / leg_area
    leg_i = min(model["leg_depth_mm"] * model["leg_width_mm"]**3,
                model["leg_width_mm"] * model["leg_depth_mm"]**3) / 12
    critical = math.pi**2 * e * leg_i / height**2
    factor = critical / (load / 2)
    violations = []
    if stress > model["allow_bending_mpa"]: violations.append("tabletop bending stress exceeds limit")
    if deflection > span / 180: violations.append("tabletop deflection exceeds span/180")
    if leg_stress > model["allow_compression_mpa"]: violations.append("leg compression stress exceeds limit")
    if factor < 2: violations.append("leg Euler buckling factor is below 2")
    return {"method": "beam_bending_and_euler_buckling", "pass": not violations,
            "violations": violations, "top_bending_stress_mpa": round(stress, 6),
            "top_deflection_mm": round(deflection, 6), "leg_compression_stress_mpa": round(leg_stress, 6),
            "leg_buckling_factor": round(factor, 6),
            "criteria": {"bending_limit_mpa": model["allow_bending_mpa"], "deflection_limit": "L/180",
                         "compression_limit_mpa": model["allow_compression_mpa"], "minimum_buckling_factor": 2},
            "assumptions": ["simply supported uniform-load tabletop", "two identical pin-ended legs",
                            "linear elastic small deflection"]}


def _render_table(model: dict) -> str:
    w, h = model["width_mm"], model["height_mm"]
    scale = min(760 / w, 480 / h); x0, base = 120, 570
    top_h = max(8, model["top_thickness_mm"] * scale)
    top_y = base - h * scale
    leg_w = max(8, model["leg_width_mm"] * scale)
    left = x0 + model["leg_inset_mm"] * scale
    right = x0 + (w - model["leg_inset_mm"] - model["leg_width_mm"]) * scale
    return _svg([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700">',
        '<rect id="background" width="1000" height="700" fill="white"/>',
        '<text id="title" x="40" y="45" font-size="24" font-weight="bold">Table side elevation</text>',
        f'<rect id="top" x="{x0}" y="{top_y}" width="{w*scale}" height="{top_h}" fill="#d9b38c" stroke="#172b4d" stroke-width="3"/>',
        f'<rect id="left-leg" x="{left}" y="{top_y+top_h}" width="{leg_w}" height="{base-top_y-top_h}" fill="#b98355" stroke="#172b4d" stroke-width="3"/>',
        f'<rect id="right-leg" x="{right}" y="{top_y+top_h}" width="{leg_w}" height="{base-top_y-top_h}" fill="#b98355" stroke="#172b4d" stroke-width="3"/>',
        f'<line id="floor" x1="80" y1="{base}" x2="920" y2="{base}" stroke="#59636e" stroke-width="2"/>',
        f'<text id="width-note" x="500" y="620" font-size="16" text-anchor="middle">Width {_fmt(w)} mm</text>',
        f'<text id="height-note" x="70" y="{(base+top_y)/2}" font-size="16" transform="rotate(-90 70 {(base+top_y)/2})" text-anchor="middle">Height {_fmt(h)} mm</text>',
        f'<text id="section-note" x="500" y="655" font-size="14" text-anchor="middle">Top {_fmt(model["top_depth_mm"])} × {_fmt(model["top_thickness_mm"])} mm; load {_fmt(model["load_N"])} N</text>',
        '</svg>',
    ])


def _table_edits(model: dict, rng: random.Random, index: int):
    target = copy.deepcopy(model); target["load_N"] = round(model["load_N"] * 1.5)
    a = (f'Increase the design load to {target["load_N"]} N.', target, "load")
    target = copy.deepcopy(model); target["top_thickness_mm"] += 10
    b = (f'Increase the tabletop thickness to {target["top_thickness_mm"]} mm.', target, "section")
    target = copy.deepcopy(model); target["width_mm"] += 300
    c = (f'Extend the table width to {target["width_mm"]} mm.', target, "geometry")
    target = copy.deepcopy(model); target["height_mm"] += 150
    d = (f'Raise the table height to {target["height_mm"]} mm.', target, "geometry")
    return [a, b, c, d]


def _mechanical_model(rng: random.Random, index: int) -> dict:
    width, height = rng.randrange(240, 421, 10), rng.randrange(160, 301, 10)
    diameter = rng.randrange(10, 31, 2)
    offset = rng.randrange(max(25, diameter // 2 + 16), min(width, height) // 3 + 1, 5)
    return {"family": "mechanical_part", "width_mm": width, "height_mm": height,
            "thickness_mm": rng.randrange(6, 21), "hole_diameter_mm": diameter,
            "hole_offset_mm": offset, "slot_length_mm": rng.randrange(50, 101, 5),
            "slot_width_mm": rng.randrange(12, 31, 2)}


def _mechanical_holes(model):
    w, h, o = model["width_mm"], model["height_mm"], model["hole_offset_mm"]
    return ((o, o), (w-o, o), (o, h-o), (w-o, h-o))


def _verify_mechanical(model: dict) -> dict:
    w, h = model["width_mm"], model["height_mm"]
    r, slot_r = model["hole_diameter_mm"] / 2, model["slot_width_mm"] / 2
    slot_half = model["slot_length_mm"] / 2
    cx, cy = w / 2, h / 2
    holes = _mechanical_holes(model); violations = []
    edges = [min(x-r, y-r, w-x-r, h-y-r) for x, y in holes]
    if min(edges) < 12: violations.append("hole edge distance is below 12 mm")
    slot_edge = min(cx-slot_half-slot_r, w-cx-slot_half-slot_r, cy-slot_r, h-cy-slot_r)
    if slot_edge < 12: violations.append("slot edge distance is below 12 mm")
    ligaments = []
    for x, y in holes:
        nearest_x = max(abs(x-cx)-slot_half, 0)
        distance = math.hypot(nearest_x, y-cy) - r - slot_r
        ligaments.append(distance)
    if min(ligaments) < 10: violations.append("hole-to-slot ligament is below 10 mm")
    gross = w*h
    removed = 4*math.pi*r*r + model["slot_width_mm"] * (model["slot_length_mm"]-model["slot_width_mm"]) + math.pi*slot_r**2
    return {"method": "manufacturing_feature_geometry", "pass": not violations,
            "violations": violations, "minimum_hole_edge_mm": round(min(edges), 6),
            "minimum_slot_edge_mm": round(slot_edge, 6),
            "minimum_hole_slot_ligament_mm": round(min(ligaments), 6),
            "net_area_mm2": round(gross-removed, 6), "volume_mm3": round((gross-removed)*model["thickness_mm"], 6),
            "criteria": {"minimum_feature_edge_mm": 12, "minimum_feature_ligament_mm": 10}}


def _render_mechanical(model: dict) -> str:
    w, h = model["width_mm"], model["height_mm"]
    scale = min(700/w, 430/h); x0, y0 = 150, 120
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700">',
        '<rect id="background" width="1000" height="700" fill="white"/>',
        '<text id="title" x="40" y="45" font-size="24" font-weight="bold">Machined mounting plate</text>',
        f'<rect id="plate" x="{x0}" y="{y0}" width="{w*scale}" height="{h*scale}" fill="#e6eef5" stroke="#172b4d" stroke-width="4"/>',
        '<g id="holes" fill="white" stroke="#172b4d" stroke-width="3">',
    ]
    for i, (x, y) in enumerate(_mechanical_holes(model), 1):
        parts.append(f'<circle id="hole-{i}" cx="{x0+x*scale}" cy="{y0+(h-y)*scale}" r="{model["hole_diameter_mm"]*scale/2}"/>')
    slot_w, slot_l = model["slot_width_mm"]*scale, model["slot_length_mm"]*scale
    parts += [
        '</g>',
        f'<rect id="slot" x="{x0+w*scale/2-slot_l/2}" y="{y0+h*scale/2-slot_w/2}" width="{slot_l}" height="{slot_w}" rx="{slot_w/2}" fill="white" stroke="#2878b5" stroke-width="3"/>',
        f'<text id="size-note" x="500" y="600" font-size="16" text-anchor="middle">Plate {_fmt(w)} × {_fmt(h)} × {_fmt(model["thickness_mm"])} mm</text>',
        f'<text id="hole-note" x="500" y="630" font-size="15" text-anchor="middle">4 × Ø{_fmt(model["hole_diameter_mm"])} mm; offset {_fmt(model["hole_offset_mm"])} mm</text>',
        f'<text id="slot-note" x="500" y="660" font-size="15" text-anchor="middle">Slot {_fmt(model["slot_length_mm"])} × {_fmt(model["slot_width_mm"])} mm</text>',
        '</svg>',
    ]
    return _svg(parts)


def _mechanical_edits(model: dict, rng: random.Random, index: int):
    target = copy.deepcopy(model); target["hole_diameter_mm"] += 6
    a = (f'Increase all hole diameters to {target["hole_diameter_mm"]} mm.', target, "feature_size")
    target = copy.deepcopy(model); target["hole_offset_mm"] += 5
    b = (f'Move every hole centre to an edge offset of {target["hole_offset_mm"]} mm.', target, "feature_position")
    target = copy.deepcopy(model); target["slot_width_mm"] += 8
    c = (f'Widen the centre slot to {target["slot_width_mm"]} mm.', target, "feature_size")
    target = copy.deepcopy(model); target["thickness_mm"] += 3
    d = (f'Increase plate thickness to {target["thickness_mm"]} mm.', target, "dimension")
    return [a, b, c, d]


def _circuit_model(rng: random.Random, index: int) -> dict:
    return {"family": "dc_circuit", "voltage_V": rng.choice((12, 18, 24, 36, 48)),
            "resistors_ohm": [rng.randrange(10, 101, 5), rng.randrange(10, 101, 5)],
            "resistor_power_rating_W": 25}


def _verify_circuit(model: dict) -> dict:
    resistance = sum(model["resistors_ohm"]); current = model["voltage_V"] / resistance
    drops = [current*r for r in model["resistors_ohm"]]
    powers = [current**2*r for r in model["resistors_ohm"]]
    residual = model["voltage_V"] - sum(drops)
    violations = [f"R{i+1} exceeds {model['resistor_power_rating_W']} W rating"
                  for i, power in enumerate(powers) if power > model["resistor_power_rating_W"]]
    return {"method": "dc_series_kcl_kvl_and_power", "pass": not violations,
            "violations": violations, "current_A": round(current, 8),
            "voltage_drops_V": [round(v, 8) for v in drops],
            "resistor_powers_W": [round(v, 8) for v in powers], "kvl_residual_V": round(residual, 12),
            "criteria": {"resistor_power_rating_W": model["resistor_power_rating_W"]}}


def _render_circuit(model: dict) -> str:
    values = model["resistors_ohm"]; positions = (260, 470, 680)[:len(values)]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700">',
        '<rect id="background" width="1000" height="700" fill="white"/>',
        '<text id="title" x="40" y="45" font-size="24" font-weight="bold">DC series circuit</text>',
        '<g id="battery" stroke="#172b4d" stroke-width="4">',
        '<line id="battery-long" x1="120" y1="250" x2="120" y2="390"/>',
        '<line id="battery-short" x1="145" y1="275" x2="145" y2="365"/>',
        '</g>',
        f'<line id="wire-left" x1="120" y1="250" x2="{positions[0]-50}" y2="250" stroke="#172b4d" stroke-width="4"/>',
    ]
    for i, (value, x) in enumerate(zip(values, positions), 1):
        parts += [
            f'<g id="resistor-{i}">',
            f'<rect id="resistor-{i}-body" x="{x-50}" y="225" width="100" height="50" rx="5" fill="#fff2cc" stroke="#172b4d" stroke-width="3"/>',
            f'<text id="resistor-{i}-label" x="{x}" y="210" font-size="16" text-anchor="middle">R{i} {_fmt(value)} Ω</text>',
            '</g>',
        ]
        if i < len(values):
            parts.append(f'<line id="wire-{i}-{i+1}" x1="{x+50}" y1="250" x2="{positions[i]-50}" y2="250" stroke="#172b4d" stroke-width="4"/>')
    last = positions[-1]
    parts += [
        f'<path id="wire-return" d="M{last+50} 250 H880 V470 H120 V390" fill="none" stroke="#172b4d" stroke-width="4"/>',
        f'<text id="voltage-note" x="95" y="325" font-size="17" text-anchor="end">{_fmt(model["voltage_V"])} V</text>',
        f'<text id="rating-note" x="500" y="540" font-size="15" text-anchor="middle">Each resistor rated {_fmt(model["resistor_power_rating_W"])} W</text>',
        '</svg>',
    ]
    return _svg(parts)


def _circuit_edits(model: dict, rng: random.Random, index: int):
    target = copy.deepcopy(model); target["voltage_V"] = round(model["voltage_V"] * 1.5)
    a = (f'Increase the supply voltage to {target["voltage_V"]} V.', target, "source_value")
    target = copy.deepcopy(model); target["resistors_ohm"][0] += 20
    b = (f'Set R1 to {target["resistors_ohm"][0]} ohms.', target, "component_value")
    target = copy.deepcopy(model); target["resistors_ohm"][1] = max(5, round(model["resistors_ohm"][1] / 2))
    c = (f'Set R2 to {target["resistors_ohm"][1]} ohms.', target, "component_value")
    target = copy.deepcopy(model); target["resistors_ohm"].append(rng.choice((22, 33, 47, 68)))
    d = (f'Add R3={target["resistors_ohm"][2]} ohms in series after R2.', target, "topology")
    return [a, b, c, d]


def _piping_model(rng: random.Random, index: int) -> dict:
    return {"family": "water_piping", "length_m": rng.randrange(40, 181, 5),
            "diameter_mm": rng.randrange(60, 181, 5), "roughness_mm": 0.045,
            "flow_m3_s": rng.randrange(5, 41) / 1000, "valve_K": [rng.choice((0.2, 0.9, 2.0))]}


def _verify_piping(model: dict) -> dict:
    rho, mu, gravity = 998.0, 0.001002, 9.80665
    diameter = model["diameter_mm"] / 1000
    area = math.pi * diameter**2 / 4
    velocity = model["flow_m3_s"] / area
    reynolds = rho * velocity * diameter / mu
    relative = (model["roughness_mm"] / 1000) / diameter
    if reynolds < 2300:
        friction = 64 / reynolds
    else:
        friction = 0.25 / math.log10(relative/3.7 + 5.74/reynolds**0.9)**2
    dynamic = velocity**2 / (2*gravity)
    head = friction * model["length_m"] / diameter * dynamic + sum(model["valve_K"]) * dynamic
    pressure = rho * gravity * head
    violations = []
    if velocity > 3: violations.append("pipe velocity exceeds 3 m/s")
    if pressure > 200000: violations.append("pressure drop exceeds 200 kPa")
    return {"method": "darcy_weisbach_continuity_and_minor_losses", "pass": not violations,
            "violations": violations, "velocity_m_s": round(velocity, 8), "reynolds_number": round(reynolds, 2),
            "friction_factor": round(friction, 8), "head_loss_m": round(head, 8),
            "pressure_drop_pa": round(pressure, 4), "continuity_residual_m3_s": 0.0,
            "criteria": {"maximum_velocity_m_s": 3, "maximum_pressure_drop_pa": 200000},
            "assumptions": ["steady incompressible water flow", "constant circular diameter",
                            "Darcy-Weisbach with explicit friction-factor approximation"]}


def _render_piping(model: dict) -> str:
    count = len(model["valve_K"]); positions = [300 + i*300/(max(count-1, 1)) for i in range(count)]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700" width="1000" height="700">',
        '<defs><marker id="flow-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#2878b5"/></marker></defs>',
        '<rect id="background" width="1000" height="700" fill="white"/>',
        '<text id="title" x="40" y="45" font-size="24" font-weight="bold">Water pipeline</text>',
        '<path id="pipe" d="M100 330 H900" fill="none" stroke="#172b4d" stroke-width="18" stroke-linecap="round"/>',
        '<line id="flow" x1="170" y1="280" x2="830" y2="280" stroke="#2878b5" stroke-width="4" marker-end="url(#flow-arrow)"/>',
        '<g id="valves" fill="white" stroke="#c94b40" stroke-width="4">',
    ]
    for i, (x, loss) in enumerate(zip(positions, model["valve_K"]), 1):
        parts += [
            f'<g id="valve-{i}"><path id="valve-{i}-symbol" d="M{x-20} 310 L{x} 330 L{x-20} 350 M{x+20} 310 L{x} 330 L{x+20} 350"/>',
            f'<text id="valve-{i}-label" x="{x}" y="390" font-size="15" text-anchor="middle" fill="#172b4d" stroke="none">K={_fmt(loss)}</text></g>',
        ]
    parts += [
        '</g>',
        f'<text id="length-note" x="500" y="455" font-size="16" text-anchor="middle">Length {_fmt(model["length_m"])} m</text>',
        f'<text id="diameter-note" x="500" y="485" font-size="16" text-anchor="middle">Diameter {_fmt(model["diameter_mm"])} mm</text>',
        f'<text id="flow-note" x="500" y="515" font-size="16" text-anchor="middle">Flow {_fmt(model["flow_m3_s"])} m³/s</text>',
        '</svg>',
    ]
    return _svg(parts)


def _piping_edits(model: dict, rng: random.Random, index: int):
    target = copy.deepcopy(model); target["flow_m3_s"] = round(model["flow_m3_s"]*1.25, 6)
    a = (f'Increase flow to {_fmt(target["flow_m3_s"])} cubic metres per second.', target, "flow")
    target = copy.deepcopy(model); target["diameter_mm"] = max(40, model["diameter_mm"]-20)
    b = (f'Reduce the pipe diameter to {target["diameter_mm"]} mm.', target, "dimension")
    target = copy.deepcopy(model); target["length_m"] += 25
    c = (f'Extend the pipeline length to {target["length_m"]} m.', target, "dimension")
    target = copy.deepcopy(model); target["valve_K"].append(rng.choice((2.0, 5.0, 10.0)))
    d = (f'Add a second valve with loss coefficient K={_fmt(target["valve_K"][1])}.', target, "topology")
    return [a, b, c, d]


BUILDERS = {
    "building_plan": (_building_model, _building_edits, _render_building, _verify_building),
    "furniture_table": (_table_model, _table_edits, _render_table, _verify_table),
    "mechanical_part": (_mechanical_model, _mechanical_edits, _render_mechanical, _verify_mechanical),
    "dc_circuit": (_circuit_model, _circuit_edits, _render_circuit, _verify_circuit),
    "water_piping": (_piping_model, _piping_edits, _render_piping, _verify_piping),
}


def _make_row(family: str, split: str, design_index: int, edit_index: int, source: dict,
              target: dict, instruction: str, edit_kind: str, render, verify) -> dict:
    source_svg, target_svg = render(source), render(target)
    build_scene_graph(source_svg); build_scene_graph(target_svg)
    patch = parse_patch(derive_structural_patch(source_svg, target_svg).to_json())
    validate_patch(patch, build_scene(source_svg), generic_svg_policy(max_operations=500))
    edited = apply_patch(source_svg, patch)
    exact = normalized_tree(parse_svg(edited)) == normalized_tree(parse_svg(target_svg))
    scene = build_scene_graph(edited)
    dangling = [edge for edge in scene["reference_edges"] if edge["to"] is None]
    if not exact or dangling or scene["duplicate_xml_ids"]:
        raise AssertionError(f"unverified patch for {family}-{design_index}-{edit_index}")
    digest = _sha(_canonical(source))
    lineage = f"cross-{family}-{digest[:16]}"
    before, after = verify(source), verify(target)
    prompt = ("Edit the engineering SVG according to the instruction. Return only an SVGPatchLab patch JSON.\n"
              f"Instruction: {instruction}\nSource SVG:\n{source_svg}")
    return {
        "version": VERSION,
        "id": f"{lineage}:edit-{edit_index}",
        "lineage_id": lineage,
        "family": family,
        "split": split,
        "edit_kind": edit_kind,
        "instruction": instruction,
        "prompt": prompt,
        "source_svg": source_svg,
        "target_svg": target_svg,
        "target_patch": patch.to_dict(),
        "source_model": source,
        "target_model": target,
        "before_verification": before,
        "after_verification": after,
        "engineering_status": "verified_safe" if after["pass"] else "verified_with_violations",
        "patch_verified": True,
        "target_tree_equal": True,
        "source_sha256": _sha(source_svg),
        "target_sha256": _sha(target_svg),
        "patch_operation_types": [operation.op for operation in patch.operations],
    }


def dataset(designs_per_family: int = DESIGNS_PER_FAMILY, seed: int = SEED):
    rng = random.Random(seed)
    rows = {"train": [], "validation": [], "test": []}
    seen = set()
    for family in FAMILIES:
        make_model, make_edits, render, verify = BUILDERS[family]
        for design_index in range(designs_per_family):
            train_end, validation_end = int(designs_per_family * .8), int(designs_per_family * .9)
            split = ("train" if design_index < train_end else
                     "validation" if design_index < validation_end else "test")
            while True:
                source = make_model(rng, design_index)
                digest = _sha(_canonical(source))
                if digest not in seen:
                    seen.add(digest); break
            edits = make_edits(source, rng, design_index)
            if len(edits) != EDITS_PER_DESIGN:
                raise AssertionError("each design must supply four edit tasks")
            for edit_index, (instruction, target, kind) in enumerate(edits, 1):
                row = _make_row(family, split, design_index, edit_index, source, target, instruction,
                                kind, render, verify)
                rows[row["split"]].append(row)
    for split in rows:
        rng.shuffle(rows[split])
    return rows


def _write_jsonl_gz(path: Path, rows) -> None:
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def _render_png(svg_path: Path, png_path: Path) -> bool:
    if not CHROME.exists():
        return False
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1000,700", f"--screenshot={png_path}", svg_path.resolve().as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)
    return True


def _write_samples(out: Path, rows: dict, per_family: int = 3) -> tuple[int, int]:
    sample_dir = out / "samples"; sample_dir.mkdir()
    candidates = rows["test"] + rows["validation"]
    chosen = []
    for family in FAMILIES:
        chosen.extend([row for row in candidates if row["family"] == family][:per_family])
    pngs = 0
    for row in chosen:
        stem = row["id"].replace(":", "-")
        for side in ("source", "target"):
            svg_path = sample_dir / f"{stem}-{side}.svg"
            png_path = sample_dir / f"{stem}-{side}.png"
            svg_path.write_text(row[f"{side}_svg"])
            if _render_png(svg_path, png_path): pngs += 1
        (sample_dir / f"{stem}-record.json").write_text(json.dumps(
            {key: row[key] for key in ("id", "family", "instruction", "engineering_status",
                                       "target_patch", "before_verification", "after_verification")},
            indent=2) + "\n")
    return len(chosen) * 2, pngs


def build(out: Path, designs_per_family: int = DESIGNS_PER_FAMILY, seed: int = SEED) -> dict:
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory is not empty; dataset versions are immutable")
    out.mkdir(parents=True, exist_ok=True)
    rows = dataset(designs_per_family, seed)
    for split, items in rows.items():
        _write_jsonl_gz(out / f"{split}.jsonl.gz", items)
    svg_samples, png_samples = _write_samples(out, rows)
    all_rows = sum(rows.values(), [])
    groups = {split: {row["lineage_id"] for row in items} for split, items in rows.items()}
    if any(groups[a] & groups[b] for a in groups for b in groups if a < b):
        raise AssertionError("source lineage leaked across dataset splits")
    family_counts = {family: sum(row["family"] == family for row in all_rows) for family in FAMILIES}
    operation_counts = {name: sum(name in row["patch_operation_types"] for row in all_rows)
                        for name in sorted({op for row in all_rows for op in row["patch_operation_types"]})}
    verifier_counts = {}
    for row in all_rows:
        method = row["after_verification"]["method"]
        verifier_counts[method] = verifier_counts.get(method, 0) + 1
    summary = {
        "version": VERSION, "seed": seed,
        "source_designs": len({row["lineage_id"] for row in all_rows}),
        "edit_examples": len(all_rows), "families": list(FAMILIES),
        "family_counts": family_counts,
        "split_examples": {split: len(items) for split, items in rows.items()},
        "split_source_designs": {split: len(groups[split]) for split in groups},
        "lineage_overlap_between_splits": 0,
        "rows_with_source_svg": sum(row["source_svg"].lstrip().startswith("<svg") for row in all_rows),
        "rows_with_target_svg": sum(row["target_svg"].lstrip().startswith("<svg") for row in all_rows),
        "rows_with_gold_patch": sum(bool(row["target_patch"]["operations"]) for row in all_rows),
        "exact_patch_roundtrips": sum(row["target_tree_equal"] for row in all_rows),
        "verified_safe": sum(row["engineering_status"] == "verified_safe" for row in all_rows),
        "verified_with_violations": sum(row["engineering_status"] == "verified_with_violations" for row in all_rows),
        "patch_operation_coverage": operation_counts,
        "verifier_coverage": verifier_counts,
        "sample_svgs": svg_samples, "sample_pngs": png_samples,
        "training_objective": "source SVG + natural-language instruction -> constrained patch JSON",
        "claim_boundary": ("procedural 2D examples with family-specific idealised checks; not construction, "
                           "manufacturing, electrical or piping approval"),
    }
    (out / "dataset-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "README.md").write_text(
        "# Cross-domain engineering SVG edit dataset v1\n\n"
        "Every row contains a complete source SVG, edit instruction, complete target SVG, gold tree patch, "
        "source/target parametric models and deterministic before/after verification. Splits are assigned by "
        "source lineage, so four edits of one drawing never cross train, validation and test.\n\n"
        "Families: building plans, furniture tables, machined parts, DC circuits and water piping. "
        "Open `samples/` for ordinary SVG files, raster PNG previews and their records.\n\n"
        "Training objective: `source SVG + instruction -> target_patch`. Apply the prediction with the generic "
        "executor, parse the result again and run the family verifier before accepting it.\n")
    files = sorted(path for path in out.rglob("*") if path.is_file())
    manifest = {path.relative_to(out).as_posix(): _sha(path.read_bytes()) for path in files}
    (out / "sha256-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--designs-per-family", type=int, default=DESIGNS_PER_FAMILY)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.designs_per_family, args.seed), indent=2))
