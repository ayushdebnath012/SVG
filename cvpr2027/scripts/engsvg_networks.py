"""Resistor and water-pipe networks drawn as SVG, recovered from the drawing alone, and re-solved.

Recovery reads only visible geometry and text. Wire and pipe endpoints, T-junctions and junction
dots become nodes; rectangles and circles whose terminals touch wires become components; labels are
matched to the nearest component. Nothing on the recovery path reads ids or data attributes, so the
same code scores a generated drawing, an edited drawing, or one written by hand.

Circuits are solved by modified nodal analysis (KCL at every node, one equation per source).
Pipe networks are solved by Newton's method on pipe flows and junction heads with Darcy-Weisbach
losses (Churchill friction factor, valid from laminar to fully rough) and cross-checked by an
independent Hardy Cross loop iteration.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import random
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_svg_geometry as geometry  # noqa: E402


TOL = 1e-3            # px: points closer than this are the same point
PIPE_MIN_WIDTH = 4.0  # stroke width: pipes are heavy lines; thinner strokes are annotation
RHO, MU, GRAVITY = 998.0, 0.001002, 9.80665


class RecoveryError(ValueError):
    """The drawing does not describe a network the solver can read."""


class IllPosed(ValueError):
    """The network is readable but has no unique solution."""


def _fmt(value: float) -> str:
    return f"{value:.6g}"


class _Union:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def join(self, first: int, second: int) -> bool:
        first, second = self.find(first), self.find(second)
        if first == second:
            return False
        self.parent[max(first, second)] = min(first, second)
        return True


class _Points:
    """Points merged within a tolerance, looked up through a hash grid."""

    def __init__(self, tol: float):
        self.tol, self.cells, self.xy = tol, {}, []

    def _key(self, point):
        return math.floor(point[0] / self.tol), math.floor(point[1] / self.tol)

    def find(self, point):
        kx, ky = self._key(point)
        best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for index in self.cells.get((kx + dx, ky + dy), ()):
                    distance = math.dist(self.xy[index], point)
                    if distance <= self.tol and (best is None or distance < best[0]):
                        best = (distance, index)
        return None if best is None else best[1]

    def add(self, point) -> int:
        index = self.find(point)
        if index is None:
            self.xy.append([float(point[0]), float(point[1])])
            index = len(self.xy) - 1
            self.cells.setdefault(self._key(point), []).append(index)
        return index


def _split_at_junctions(segments: list[dict], dots: list[dict], tol: float) -> list[dict]:
    """Split segments where another segment ends on them (a T) or where a junction dot sits.

    Two segments that merely cross are not connected unless a dot marks the crossing, which is the
    drafting convention for both schematics and piping plans.
    """
    cuts = [segment["a"] for segment in segments] + [segment["b"] for segment in segments]
    cuts += [dot["center"] for dot in dots]
    cuts = np.array(cuts, dtype=float).reshape(-1, 2)
    result = []
    for segment in segments:
        a, b = np.array(segment["a"], float), np.array(segment["b"], float)
        direction = b - a
        length2 = float(direction @ direction)
        if length2 <= tol * tol:
            continue
        length = math.sqrt(length2)
        t = ((cuts - a) @ direction) / length2
        distance = np.linalg.norm(cuts - (a + np.outer(t, direction)), axis=1)
        inside = (distance <= tol) & (t * length > tol) & (t * length < length - tol)
        chain = [a] + [a + value * direction for value in sorted(set(np.round(t[inside], 12)))] + [b]
        for first, second in zip(chain, chain[1:]):
            if np.linalg.norm(second - first) > tol:
                result.append({**segment, "a": [float(v) for v in first], "b": [float(v) for v in second]})
    return result


def _split_circles(circles: list[dict], segments: list[dict], tol: float):
    """Junction dots sit on a wire; component bodies are touched by wires only at their rim.

    Classifying by where the wires meet the circle, not by its radius, keeps recovery unchanged
    when the whole drawing is scaled.
    """
    dots, bodies = [], []
    for circle in circles:
        on_wire = any(_point_to_polyline(circle["center"], [s["a"], s["b"]]) <= tol for s in segments)
        (dots if on_wire else bodies).append(circle)
    return dots, bodies


def _median(values, default: float) -> float:
    return float(np.median(values)) if len(values) else default


def _assign_labels(labels: list, anchors: list, distance, limit: float) -> dict:
    """Greedy one-to-one nearest matching; returns {anchor index: label index}."""
    pairs = sorted((distance(label, anchor), i, j)
                   for i, label in enumerate(labels) for j, anchor in enumerate(anchors))
    used_labels, result = set(), {}
    for gap, i, j in pairs:
        if gap > limit:
            break
        if i in used_labels or j in result:
            continue
        result[j] = i
        used_labels.add(i)
    return result


def _point_to_polyline(point, polyline) -> float:
    best = math.inf
    p = np.array(point, float)
    for first, second in zip(polyline, polyline[1:]):
        a, b = np.array(first, float), np.array(second, float)
        d = b - a
        t = 0.0 if not d.any() else float(np.clip((p - a) @ d / (d @ d), 0, 1))
        best = min(best, float(np.linalg.norm(p - (a + t * d))))
    return best


# --------------------------------------------------------------------------------------------
# Circuits
# --------------------------------------------------------------------------------------------

C_X0, C_Y0, C_DX, C_DY = 140, 150, 190, 170
C_STROKE = "#172b4d"
E6 = (10, 15, 22, 33, 47, 68)
RESISTOR_VALUES = tuple(value * decade for decade in (1, 10, 100) for value in E6)
VOLTAGES = (5, 9, 12, 15, 24, 48)
RESISTOR_LABEL = re.compile(r"^\s*R(\d+)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*(k|M)?\s*(?:Ω|ohms?)\s*$")
SOURCE_LABEL = re.compile(r"^\s*V(\d+)\s*[=:]?\s*(\d+(?:\.\d+)?)\s*V\s*$")
RATING_NOTE = re.compile(r"rated\s+(\d+(?:\.\d+)?)\s*W", re.I)
FUSE_NOTE = re.compile(r"fuses?\s+(\d+(?:\.\d+)?)\s*A\b", re.I)


def _ohm_text(value: float) -> str:
    return f"{_fmt(value / 1000)} kΩ" if value >= 1000 else f"{_fmt(value)} Ω"


def _cxy(rc) -> tuple[float, float]:
    return C_X0 + rc[1] * C_DX, C_Y0 + rc[0] * C_DY


def _grid_edges(rows: int, cols: int) -> list[tuple]:
    edges = [((r, c), (r, c + 1)) for r in range(rows) for c in range(cols - 1)]
    edges += [((r, c), (r + 1, c)) for r in range(rows - 1) for c in range(cols)]
    return edges


def _connected(vertices, edges) -> bool:
    vertices = set(vertices)
    if not vertices:
        return True
    adjacency = {v: [] for v in vertices}
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    start = next(iter(vertices))
    seen, stack = {start}, [start]
    while stack:
        for other in adjacency[stack.pop()]:
            if other not in seen:
                seen.add(other)
                stack.append(other)
    return seen == vertices


def _bridgeless(vertices, edges) -> bool:
    return all(_connected(vertices, edges[:i] + edges[i + 1:]) for i in range(len(edges)))


def circuit_netlist(model: dict) -> dict:
    """Reference netlist straight from the parametric model (never from the drawing)."""
    vertices = sorted({tuple(edge[end]) for edge in model["edges"] for end in ("a", "b")})
    index = {vertex: i for i, vertex in enumerate(vertices)}
    union = _Union(len(vertices))
    for edge in model["edges"]:
        if edge["kind"] == "wire":
            union.join(index[tuple(edge["a"])], index[tuple(edge["b"])])
    node = lambda rc: union.find(index[tuple(rc)])  # noqa: E731
    resistors, sources, ends = [], [], {}
    for edge in model["edges"]:
        if edge["kind"] == "resistor":
            ends[edge["name"]] = [node(edge["a"]), node(edge["b"])]
            resistors.append({"name": edge["name"], "ohm": float(edge["ohm"]), "nodes": ends[edge["name"]]})
        elif edge["kind"] == "source":
            plus, minus = (edge["a"], edge["b"]) if edge["plus"] == "a" else (edge["b"], edge["a"])
            ends[edge["name"]] = [node(plus), node(minus)]
            sources.append({"name": edge["name"], "volt": float(edge["volt"]),
                            "plus": node(plus), "minus": node(minus)})
    for branch in model.get("parallel", []):
        resistors.append({"name": branch["name"], "ohm": float(branch["ohm"]),
                          "nodes": list(ends[branch["across"]])})
    return _renumber({"resistors": resistors, "sources": sources,
                      "rating_W": float(model["rating_W"]), "fuse_A": float(model["fuse_A"])})


def _renumber(net: dict) -> dict:
    order = {}
    for item in net["resistors"]:
        for node in item["nodes"]:
            order.setdefault(node, len(order))
    for item in net["sources"]:
        for key in ("plus", "minus"):
            order.setdefault(item[key], len(order))
    net = copy.deepcopy(net)
    for item in net["resistors"]:
        item["nodes"] = [order[node] for node in item["nodes"]]
    for item in net["sources"]:
        item["plus"], item["minus"] = order[item["plus"]], order[item["minus"]]
    net["node_count"] = len(order)
    return net


def solve_circuit(net: dict) -> dict:
    """Modified nodal analysis; one grounded node per connected part of the network."""
    count, resistors, sources = net["node_count"], net["resistors"], net["sources"]
    for source in sources:
        if source["plus"] == source["minus"]:
            raise IllPosed(f"{source['name']} is short-circuited")
    for resistor in resistors:
        if resistor["ohm"] <= 0 or not math.isfinite(resistor["ohm"]):
            raise IllPosed(f"{resistor['name']} has non-positive resistance")
    union = _Union(count)
    for resistor in resistors:
        union.join(*resistor["nodes"])
    for source in sources:
        union.join(source["plus"], source["minus"])
    grounded = {union.find(node) for node in range(count)}
    unknown = [node for node in range(count) if node not in grounded]
    column = {node: i for i, node in enumerate(unknown)}
    size = len(unknown) + len(sources)
    matrix, rhs = np.zeros((size, size)), np.zeros(size)
    for resistor in resistors:
        conductance = 1.0 / resistor["ohm"]
        a, b = resistor["nodes"]
        for first, second in ((a, b), (b, a)):
            if first in column:
                matrix[column[first], column[first]] += conductance
                if second in column:
                    matrix[column[first], column[second]] -= conductance
    for k, source in enumerate(sources):
        row = len(unknown) + k
        if source["plus"] in column:
            matrix[column[source["plus"]], row] -= 1
            matrix[row, column[source["plus"]]] += 1
        if source["minus"] in column:
            matrix[column[source["minus"]], row] += 1
            matrix[row, column[source["minus"]]] -= 1
        rhs[row] = source["volt"]
    if size and np.linalg.cond(matrix) > 1e12:
        raise IllPosed("singular network: a loop of sources or a floating source")
    solution = np.linalg.solve(matrix, rhs) if size else np.zeros(0)
    voltage = np.zeros(count)
    for node, i in column.items():
        voltage[node] = solution[i]
    currents = solution[len(unknown):]
    injection = np.zeros(count)
    result = {"node_count": count, "resistors": {}, "sources": {}}
    for resistor in resistors:
        a, b = resistor["nodes"]
        current = (voltage[a] - voltage[b]) / resistor["ohm"]
        injection[a] -= current
        injection[b] += current
        result["resistors"][resistor["name"]] = {
            "ohm": resistor["ohm"], "current_A": float(current), "abs_current_A": abs(float(current)),
            "drop_V": abs(float(voltage[a] - voltage[b])), "power_W": float(current * current * resistor["ohm"])}
    for source, current in zip(sources, currents):
        injection[source["plus"]] += current
        injection[source["minus"]] -= current
        result["sources"][source["name"]] = {"volt": source["volt"], "current_A": float(current),
                                             "power_W": float(source["volt"] * current)}
    delivered = sum(item["power_W"] for item in result["sources"].values())
    dissipated = sum(item["power_W"] for item in result["resistors"].values())
    parts = len(grounded)
    result.update({
        "kcl_residual_A": float(np.abs(injection).max()) if count else 0.0,
        "power_balance_residual_W": float(abs(delivered - dissipated)),
        "independent_loops": len(resistors) + len(sources) - count + parts,
    })
    return result


def check_circuit(net: dict, solution: dict) -> dict:
    violations = [f"{name} dissipates {_fmt(item['power_W'])} W > {_fmt(net['rating_W'])} W rating"
                  for name, item in sorted(solution["resistors"].items()) if item["power_W"] > net["rating_W"]]
    violations += [f"{name} draws {_fmt(abs(item['current_A']))} A > {_fmt(net['fuse_A'])} A fuse"
                   for name, item in sorted(solution["sources"].items()) if abs(item["current_A"]) > net["fuse_A"]]
    return {"pass": not violations, "violations": violations}


def recover_circuit(svg: str, tol: float = TOL) -> dict:
    """Rebuild the netlist from visible geometry and text only."""
    found = geometry.extract(svg)
    dots, bodies = _split_circles(found["circles"], found["segments"], tol)
    segments = _split_at_junctions(found["segments"], dots, tol)
    points = _Points(tol)
    ends = [(points.add(s["a"]), points.add(s["b"])) for s in segments]
    union = _Union(len(points.xy))
    for a, b in ends:
        union.join(a, b)
    components = []
    for rect in found["rectangles"]:
        corners = rect["corners"]
        sides = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
        lengths = [math.dist(*side) for side in sides]
        if abs(lengths[0] - lengths[1]) <= tol:
            continue
        short = (1, 3) if lengths[1] < lengths[0] else (0, 2)
        terminals = [[(sides[k][0][0] + sides[k][1][0]) / 2, (sides[k][0][1] + sides[k][1][1]) / 2] for k in short]
        indices = [points.find(t) for t in terminals]
        if None in indices:
            continue
        center = [sum(c[0] for c in corners) / 4, sum(c[1] for c in corners) / 4]
        components.append({"kind": "resistor", "points": indices, "center": center, "size": max(lengths)})
    for body in bodies:
        touching = [i for i, xy in enumerate(points.xy)
                    if abs(math.dist(xy, body["center"]) - body["radius"]) <= tol]
        if not touching:
            continue
        if len(touching) != 2:
            raise RecoveryError(f"source at {body['center']} has {len(touching)} terminals")
        marks = [t for t in found["texts"] if t["text"] == "+"
                 and math.dist(t["position"], body["center"]) <= body["radius"]]
        if len(marks) != 1:
            raise RecoveryError(f"source at {body['center']} has no single '+' polarity mark")
        plus = min(touching, key=lambda i: math.dist(points.xy[i], marks[0]["position"]))
        minus = touching[1] if plus == touching[0] else touching[0]
        components.append({"kind": "source", "points": [plus, minus], "center": body["center"]})
    labels = {"resistor": [], "source": []}
    for text in found["texts"]:
        match = RESISTOR_LABEL.match(text["text"])
        if match:
            scale = {"k": 1e3, "M": 1e6}.get(match.group(3), 1.0)
            labels["resistor"].append(("R" + match.group(1), float(match.group(2)) * scale, text["position"]))
        match = SOURCE_LABEL.match(text["text"])
        if match:
            labels["source"].append(("V" + match.group(1), float(match.group(2)), text["position"]))
    resistors, sources = [], []
    # Labels sit about a third of a resistor body away; allow one body length (56 px as drawn).
    reach = 1.1 * _median([c["size"] for c in components if c["kind"] == "resistor"], 56.0)
    for kind in ("resistor", "source"):
        parts = [c for c in components if c["kind"] == kind]
        assigned = _assign_labels(labels[kind], parts, lambda label, part: math.dist(label[2], part["center"]), reach)
        for j, part in enumerate(parts):
            if j not in assigned:
                raise RecoveryError(f"{kind} at {[round(v, 2) for v in part['center']]} has no value label")
            name, value, _ = labels[kind][assigned[j]]
            a, b = (union.find(i) for i in part["points"])
            if kind == "resistor":
                resistors.append({"name": name, "ohm": value, "nodes": [a, b]})
            else:
                sources.append({"name": name, "volt": value, "plus": a, "minus": b})
    names = [item["name"] for item in resistors + sources]
    if len(set(names)) != len(names):
        raise RecoveryError("duplicate component names in the drawing")
    if not sources:
        raise RecoveryError("no voltage source found")
    notes = " ".join(t["text"] for t in found["texts"])
    rating, fuse = RATING_NOTE.search(notes), FUSE_NOTE.search(notes)
    if not rating or not fuse:
        raise RecoveryError("power rating or fuse note missing")
    return _renumber({"resistors": resistors, "sources": sources,
                      "rating_W": float(rating.group(1)), "fuse_A": float(fuse.group(1))})


def _circuit_signature(net: dict):
    """Complete invariant of a named-component network: which terminals share each node."""
    groups = {}
    for resistor in net["resistors"]:
        for node in resistor["nodes"]:
            groups.setdefault(node, []).append(resistor["name"])
    for source in net["sources"]:
        groups.setdefault(source["plus"], []).append(source["name"] + "+")
        groups.setdefault(source["minus"], []).append(source["name"] + "-")
    values = sorted([(r["name"], r["ohm"]) for r in net["resistors"]] +
                    [(s["name"], s["volt"]) for s in net["sources"]])
    return sorted(tuple(sorted(v)) for v in groups.values()), values, (net["rating_W"], net["fuse_A"])


def compare_circuits(reference: dict, other: dict, rel: float = 1e-9) -> dict:
    same = _circuit_signature(reference) == _circuit_signature(other)
    first, second = solve_circuit(reference), solve_circuit(other)
    gaps = []
    for name, item in first["resistors"].items():
        if name in second["resistors"]:
            gaps.append(abs(item["abs_current_A"] - second["resistors"][name]["abs_current_A"]))
    for name, item in first["sources"].items():
        if name in second["sources"]:
            gaps.append(abs(item["current_A"] - second["sources"][name]["current_A"]))
    # Scale by the largest current anywhere: two opposing sources can nearly cancel at the supply.
    scale = max([abs(i["current_A"]) for i in list(first["sources"].values()) + list(first["resistors"].values())]
                + [1e-12])
    equal_physics = (set(first["resistors"]) == set(second["resistors"]) and
                     set(first["sources"]) == set(second["sources"]) and max(gaps + [0]) <= rel * scale + 1e-12)
    return {"topology_equal": same, "physics_equal": equal_physics, "max_current_gap_A": max(gaps + [0.0])}


def circuit_model(rng: random.Random, index: int = 0, rows_choices=(2, 3), cols_choices=(3, 4, 5),
                  loops=(2, 6)) -> dict:
    while True:
        rows, cols = rng.choice(rows_choices), rng.choice(cols_choices)
        vertices = [(r, c) for r in range(rows) for c in range(cols)]
        edges = _grid_edges(rows, cols)
        target = rng.randint(loops[0], min(loops[1], (rows - 1) * (cols - 1)))
        order = edges[:]
        rng.shuffle(order)
        for edge in order:
            if len(edges) - len(vertices) + 1 <= target:
                break
            trial = [e for e in edges if e != edge]
            if _bridgeless(vertices, trial):
                edges = trial
        edges.sort(key=lambda e: (e[0], e[1][0] != e[0][0]))
        picks = list(range(len(edges)))
        rng.shuffle(picks)
        source_count = 2 if rng.random() < 0.4 else 1
        kinds = ["resistor"] * len(edges)
        for i in picks[:source_count]:
            kinds[i] = "source"
        for i in picks[source_count:]:
            if rng.random() < 0.2:
                kinds[i] = "wire"
        items, r_count, v_count = [], 0, 0
        for (a, b), kind in zip(edges, kinds):
            item = {"a": list(a), "b": list(b), "kind": kind}
            if kind == "resistor":
                r_count += 1
                item.update(name=f"R{r_count}", ohm=rng.choice(RESISTOR_VALUES))
            elif kind == "source":
                v_count += 1
                item.update(name=f"V{v_count}", volt=rng.choice(VOLTAGES), plus=rng.choice(("a", "b")))
            items.append(item)
        model = {"family": "dc_network", "grid": [rows, cols], "edges": items, "parallel": [],
                 "rating_W": rng.choice((0.25, 0.5, 1.0, 2.0)), "fuse_A": rng.choice((0.1, 0.25, 0.5, 1.0))}
        if r_count < 3 or not _circuit_well_posed(model):
            continue
        return model


def _circuit_well_posed(model: dict) -> bool:
    net = circuit_netlist(model)
    if any(r["nodes"][0] == r["nodes"][1] for r in net["resistors"]):
        return False
    union = _Union(net["node_count"])
    if not all(union.join(s["plus"], s["minus"]) for s in net["sources"]):
        return False
    try:
        solution = solve_circuit(net)
    except IllPosed:
        return False
    return any(abs(s["current_A"]) > 1e-9 for s in solution["sources"].values())


def _label(key: str, x: float, y: float, text: str, anchor: str = "middle") -> str:
    # The labels group defaults to centred text; only the exceptions carry text-anchor.
    extra = "" if anchor == "middle" else f' text-anchor="{anchor}"'
    return f'<text id="{key}" x="{_fmt(x)}" y="{_fmt(y)}"{extra}>{text}</text>'


def _component_parts(edge: dict) -> tuple[list[str], list[str]]:
    """Symbol elements and label elements for one resistor or source on a grid edge."""
    (ax, ay), (bx, by) = _cxy(edge["a"]), _cxy(edge["b"])
    horizontal = ay == by
    ux, uy = (1, 0) if horizontal else (0, 1)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    name = edge["name"]
    if edge["kind"] == "resistor":
        half = 28
        body = (f'<rect id="{name}-body" x="{_fmt(mx - 28 if horizontal else mx - 10)}" '
                f'y="{_fmt(my - 10 if horizontal else my - 28)}" width="{56 if horizontal else 20}" '
                f'height="{20 if horizontal else 56}"/>')
        label = (mx, my - 18, "middle") if horizontal else (mx + 16, my + 5, "start")
        labels = [_label(f"{name}-label", *label[:2], f"{name} {_ohm_text(edge['ohm'])}", label[2])]
    else:
        half = 22
        body = f'<circle id="{name}-body" cx="{_fmt(mx)}" cy="{_fmt(my)}" r="22" fill="white"/>'
        sign = -1 if edge["plus"] == "a" else 1
        label = (mx, my - 30, "middle") if horizontal else (mx + 28, my + 5, "start")
        labels = [_label(f"{name}-plus", mx + sign * ux * 9.9, my + sign * uy * 9.9 + 5, "+"),
                  _label(f"{name}-minus", mx - sign * ux * 9.9, my - sign * uy * 9.9 + 5, "−"),
                  _label(f"{name}-label", *label[:2], f"{name} {_fmt(edge['volt'])} V", label[2])]
    shapes = [f'<g id="{name}">',
              f'<line id="{name}-a" x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(mx - half * ux)}" y2="{_fmt(my - half * uy)}"/>',
              f'<line id="{name}-b" x1="{_fmt(mx + half * ux)}" y1="{_fmt(my + half * uy)}" x2="{_fmt(bx)}" y2="{_fmt(by)}"/>',
              body, '</g>']
    return shapes, labels


def _parallel_parts(branch: dict, across: dict) -> tuple[list[str], list[str]]:
    (ax, y), (bx, _) = _cxy(across["a"]), _cxy(across["b"])
    mx, low, name = (ax + bx) / 2, y + 40, branch["name"]
    t1, t2 = ax + 30, bx - 30
    lines = [(t1, y, t1, low), (t1, low, mx - 28, low), (mx + 28, low, t2, low), (t2, low, t2, y)]
    shapes = [f'<g id="{name}">']
    shapes += [f'<line id="{name}-w{i}" x1="{_fmt(a)}" y1="{_fmt(b)}" x2="{_fmt(c)}" y2="{_fmt(d)}"/>'
               for i, (a, b, c, d) in enumerate(lines, 1)]
    shapes += [f'<rect id="{name}-body" x="{_fmt(mx - 28)}" y="{_fmt(low - 10)}" width="56" height="20"/>',
               f'<circle id="{name}-tap-a" cx="{_fmt(t1)}" cy="{_fmt(y)}" r="5" fill="{C_STROKE}" stroke="none"/>',
               f'<circle id="{name}-tap-b" cx="{_fmt(t2)}" cy="{_fmt(y)}" r="5" fill="{C_STROKE}" stroke="none"/>',
               '</g>']
    return shapes, [_label(f"{name}-label", mx, low + 22, f"{name} {_ohm_text(branch['ohm'])}")]


def render_circuit(model: dict) -> str:
    rows, cols = model["grid"]
    height = C_Y0 + (rows - 1) * C_DY + 190
    width = max(1000, C_X0 + (cols - 1) * C_DX + 100)  # 1000 for the five-column v1 grids
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
             f'<rect id="background" width="{width}" height="{height}" fill="white"/>',
             f'<g id="wires" stroke="{C_STROKE}" stroke-width="3" fill="none">']
    degree = {}
    for edge in model["edges"]:
        for end in ("a", "b"):
            degree[tuple(edge[end])] = degree.get(tuple(edge[end]), 0) + 1
        if edge["kind"] == "wire":
            (ax, ay), (bx, by) = _cxy(edge["a"]), _cxy(edge["b"])
            key = f"r{edge['a'][0]}c{edge['a'][1]}-r{edge['b'][0]}c{edge['b'][1]}"
            parts.append(f'<line id="w-{key}" x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}"/>')
    parts += ['</g>', f'<g id="components" stroke="{C_STROKE}" stroke-width="3" fill="#fff2cc">']
    labels, by_name = [], {}
    for edge in model["edges"]:
        if edge["kind"] != "wire":
            by_name[edge["name"]] = edge
            shapes, texts = _component_parts(edge)
            parts += shapes
            labels += texts
    for branch in model.get("parallel", []):
        shapes, texts = _parallel_parts(branch, by_name[branch["across"]])
        parts += shapes
        labels += texts
    parts += ['</g>', f'<g id="junctions" fill="{C_STROKE}">']
    for (r, c), count in sorted(degree.items()):
        if count >= 3:
            x, y = _cxy((r, c))
            parts.append(f'<circle id="dot-r{r}c{c}" cx="{_fmt(x)}" cy="{_fmt(y)}" r="5"/>')
    base = C_Y0 + (rows - 1) * C_DY + 120
    parts += ['</g>', f'<g id="labels" font-size="14" fill="{C_STROKE}" text-anchor="middle">', *labels, '</g>',
              f'<g id="notes" font-size="15" fill="{C_STROKE}">',
              f'<text id="title" x="40" y="50" font-size="22" font-weight="bold">DC resistor network</text>',
              f'<text id="rating-note" x="40" y="{base}">All resistors rated {_fmt(model["rating_W"])} W</text>',
              f'<text id="fuse-note" x="40" y="{base + 26}">Supply fuses {_fmt(model["fuse_A"])} A</text>',
              '</g>', '</svg>']
    return "\n".join(parts)


def circuit_edits(model: dict, rng: random.Random) -> list[tuple]:
    resistors = [e for e in model["edges"] if e["kind"] == "resistor"]
    sources = [e for e in model["edges"] if e["kind"] == "source"]

    def value_edit(exclude=()):
        pool = [e for e in resistors if e["name"] not in exclude]
        pick = rng.choice(pool)
        target = copy.deepcopy(model)
        value = rng.choice([v for v in RESISTOR_VALUES if v != pick["ohm"]])
        next(e for e in target["edges"] if e.get("name") == pick["name"])["ohm"] = value
        return (f"Set {pick['name']} to {_ohm_text(value)}.", target, "component_value"), pick["name"]

    first, used = value_edit()
    pick = rng.choice(sources)
    target = copy.deepcopy(model)
    volt = rng.choice([v for v in VOLTAGES if v != pick["volt"]])
    next(e for e in target["edges"] if e.get("name") == pick["name"])["volt"] = volt
    second = (f"Change {pick['name']} to {_fmt(volt)} V.", target, "source_value")

    third = None
    if len(sources) == 2:
        pick = rng.choice(sources)
        target = copy.deepcopy(model)
        edge = next(e for e in target["edges"] if e.get("name") == pick["name"])
        edge["plus"] = "b" if edge["plus"] == "a" else "a"
        third = (f"Reverse the polarity of {pick['name']}.", target, "polarity")
    else:
        for pick in rng.sample(resistors, len(resistors)):
            target = copy.deepcopy(model)
            target["edges"] = [e for e in target["edges"] if e.get("name") != pick["name"]]
            if _circuit_well_posed(target):
                third = (f"Remove {pick['name']} and leave its branch open.", target, "open_branch")
                break
    if third is None:
        third, _ = value_edit(exclude=(used,))

    horizontal = [e for e in resistors if e["a"][0] == e["b"][0]]
    if horizontal:
        pick = rng.choice(horizontal)
        target = copy.deepcopy(model)
        name = f"R{len(resistors) + 1}"
        value = rng.choice(RESISTOR_VALUES)
        target["parallel"] = [{"name": name, "ohm": value, "across": pick["name"]}]
        fourth = (f"Add {name} = {_ohm_text(value)} in parallel with {pick['name']}.", target, "parallel_branch")
    else:
        fourth, _ = value_edit(exclude=(used,))
    return [first, second, third, fourth]


def circuit_report(svg: str, model: dict) -> dict:
    """Recover the drawing, solve it, check it, and confirm it matches the model it came from."""
    recovered = recover_circuit(svg)
    solution = solve_circuit(recovered)
    verdict = check_circuit(recovered, solution)
    match = compare_circuits(circuit_netlist(model), recovered)
    return {"method": "modified_nodal_analysis_of_recovered_drawing", **verdict,
            "recovered_matches_model": match["topology_equal"] and match["physics_equal"],
            "nodes": solution["node_count"], "independent_loops": solution["independent_loops"],
            "source_currents_A": {k: round(v["current_A"], 12) for k, v in sorted(solution["sources"].items())},
            "resistor_currents_A": {k: round(v["abs_current_A"], 12) for k, v in sorted(solution["resistors"].items())},
            "resistor_powers_W": {k: round(v["power_W"], 12) for k, v in sorted(solution["resistors"].items())},
            "kcl_residual_A": solution["kcl_residual_A"],
            "power_balance_residual_W": solution["power_balance_residual_W"],
            "criteria": {"resistor_rating_W": recovered["rating_W"], "fuse_A": recovered["fuse_A"]}}


# --------------------------------------------------------------------------------------------
# Water pipe networks
# --------------------------------------------------------------------------------------------

P_X0, P_Y0, P_DX, P_DY, P_RES = 260, 180, 160, 150, 110
P_STROKE = "#1f4e79"
DIAMETERS = (80, 100, 125, 150, 200, 250, 300)
PIPE_LABEL = re.compile(r"^\s*P(\d+)\s+(\d+(?:\.\d+)?)\s*m\s+(?:Ø|DN)\s*(\d+(?:\.\d+)?)\s*(?:mm)?\s*$")
JUNCTION_LABEL = re.compile(r"^\s*J(\d+)\s+q\s*=\s*(\d+(?:\.\d+)?)\s*L/s\s+z\s*=\s*(-?\d+(?:\.\d+)?)\s*m\s*$")
RESERVOIR_LABEL = re.compile(r"^\s*R(\d+)\s+H\s*=\s*(\d+(?:\.\d+)?)\s*m\s*$")
ROUGHNESS_NOTE = re.compile(r"roughness\s*(?:ε\s*)?=\s*(\d+(?:\.\d+)?)\s*mm", re.I)
ELBOW_NOTE = re.compile(r"elbow\s+K\s*=\s*(\d+(?:\.\d+)?)", re.I)
PRESSURE_NOTE = re.compile(r"minimum\s+pressure\s+head\s+(\d+(?:\.\d+)?)\s*m", re.I)
VELOCITY_NOTE = re.compile(r"maximum\s+velocity\s+(\d+(?:\.\d+)?)\s*m/s", re.I)


def _pxy(rc, cols: int) -> tuple[float, float]:
    r, c = rc
    x = P_X0 - P_RES if c < 0 else P_X0 + (cols - 1) * P_DX + P_RES if c >= cols else P_X0 + c * P_DX
    return x, P_Y0 + r * P_DY


def churchill_friction(reynolds: float, relative_roughness: float) -> float:
    """Churchill (1977) Darcy friction factor, continuous from laminar through fully rough flow."""
    if reynolds <= 1.0:
        return 64.0 / max(reynolds, 1e-300)
    a = (-2.457 * math.log((7.0 / reynolds) ** 0.9 + 0.27 * relative_roughness)) ** 16
    b = (37530.0 / reynolds) ** 16
    return 8.0 * ((8.0 / reynolds) ** 12 + (a + b) ** -1.5) ** (1.0 / 12.0)


def pipe_head_loss(flow: float, pipe: dict, roughness_m: float) -> float:
    """Head drop (m) from the pipe's first end to its second for signed flow (m^3/s)."""
    diameter = pipe["diameter_m"]
    area = math.pi * diameter ** 2 / 4
    velocity = flow / area
    if velocity == 0:
        return 0.0
    reynolds = RHO * abs(velocity) * diameter / MU
    friction = churchill_friction(reynolds, roughness_m / diameter)
    return (friction * pipe["length_m"] / diameter + pipe["minor_K"]) * velocity * abs(velocity) / (2 * GRAVITY)


def _head_slope(flow: float, pipe: dict, roughness_m: float) -> float:
    step = 1e-6 * max(abs(flow), 1e-7)
    return (pipe_head_loss(flow + step, pipe, roughness_m) - pipe_head_loss(flow - step, pipe, roughness_m)) / (2 * step)


def _tree_flows(net: dict):
    """Flows that satisfy continuity exactly, carried on a spanning tree rooted at the reservoirs."""
    reservoirs = {r["name"] for r in net["reservoirs"]}
    demand = {j["name"]: j["demand_m3_s"] for j in net["junctions"]}
    adjacency = {name: [] for name in list(demand) + list(reservoirs)}
    for k, pipe in enumerate(net["pipes"]):
        a, b = pipe["ends"]
        adjacency[a].append((k, b))
        adjacency[b].append((k, a))
    parent, order, stack = {}, [], [name for name in sorted(reservoirs)]
    seen = set(stack)
    while stack:
        node = stack.pop()
        order.append(node)
        for k, other in adjacency[node]:
            if other not in seen:
                seen.add(other)
                parent[other] = (k, node)
                stack.append(other)
    if seen != set(adjacency):
        missing = sorted(set(adjacency) - seen)
        raise IllPosed(f"junctions with no path to a reservoir: {missing}")
    flows = np.zeros(len(net["pipes"]))
    carried = {name: demand.get(name, 0.0) for name in adjacency}
    for node in reversed(order):
        if node in parent:
            k, up = parent[node]
            a, _ = net["pipes"][k]["ends"]
            flows[k] = carried[node] if a == up else -carried[node]
            carried[up] += carried[node]
    return flows, parent


def solve_pipes(net: dict, tol_head: float = 1e-10, tol_flow: float = 1e-13) -> dict:
    """Newton's method on pipe flows and junction heads (the global gradient formulation)."""
    junctions = [j["name"] for j in net["junctions"]]
    column = {name: i for i, name in enumerate(junctions)}
    fixed = {r["name"]: r["head_m"] for r in net["reservoirs"]}
    demand = np.array([j["demand_m3_s"] for j in net["junctions"]])
    pipes, eps = net["pipes"], net["roughness_m"]
    count = len(pipes)
    flows, _ = _tree_flows(net)
    heads = np.full(len(junctions), max(fixed.values()))

    def head(name, values):
        return fixed[name] if name in fixed else values[column[name]]

    def residual(q, h):
        energy = np.array([pipe_head_loss(q[k], p, eps) - (head(p["ends"][0], h) - head(p["ends"][1], h))
                           for k, p in enumerate(pipes)])
        mass = -demand.copy()
        for k, p in enumerate(pipes):
            a, b = p["ends"]
            if b in column:
                mass[column[b]] += q[k]
            if a in column:
                mass[column[a]] -= q[k]
        return energy, mass

    def size(energy, mass):
        return math.sqrt(float(energy @ energy) + float((mass * 1e3) @ (mass * 1e3)))

    energy, mass = residual(flows, heads)
    for iteration in range(200):
        if np.abs(energy).max(initial=0) < tol_head and np.abs(mass).max(initial=0) < tol_flow:
            break
        jacobian = np.zeros((count + len(junctions),) * 2)
        for k, p in enumerate(pipes):
            a, b = p["ends"]
            jacobian[k, k] = _head_slope(flows[k], p, eps)
            if a in column:
                jacobian[k, count + column[a]] -= 1
                jacobian[count + column[a], k] -= 1
            if b in column:
                jacobian[k, count + column[b]] += 1
                jacobian[count + column[b], k] += 1
        step = np.linalg.solve(jacobian, -np.concatenate([energy, mass]))
        current, scale = size(energy, mass), 1.0
        while True:
            q, h = flows + scale * step[:count], heads + scale * step[count:]
            e, m = residual(q, h)
            if size(e, m) <= (1 - 1e-4 * scale) * current or scale < 1e-8:
                break
            scale /= 2
        flows, heads, energy, mass = q, h, e, m
    else:
        raise IllPosed("pipe network did not converge")
    result = {"pipes": {}, "junctions": {}, "iterations": iteration}
    for k, p in enumerate(pipes):
        area = math.pi * p["diameter_m"] ** 2 / 4
        velocity = flows[k] / area
        result["pipes"][p["name"]] = {
            "ends": list(p["ends"]), "flow_m3_s": float(flows[k]), "velocity_m_s": abs(float(velocity)),
            "reynolds": RHO * abs(float(velocity)) * p["diameter_m"] / MU,
            "head_loss_m": abs(pipe_head_loss(flows[k], p, eps))}
    for j in net["junctions"]:
        h = float(heads[column[j["name"]]])
        result["junctions"][j["name"]] = {"head_m": h, "pressure_head_m": h - j["elevation_m"]}
    supplied = 0.0
    for k, p in enumerate(pipes):
        a, b = p["ends"]
        supplied += flows[k] * ((a in fixed) - (b in fixed))
    result.update({"energy_residual_m": float(np.abs(energy).max(initial=0)),
                   "continuity_residual_m3_s": float(np.abs(mass).max(initial=0)),
                   "mass_balance_residual_m3_s": float(abs(supplied - demand.sum())),
                   "independent_loops": count - len(junctions)})
    return result


def hardy_cross(net: dict, tol: float = 1e-14, max_sweeps: int = 50000) -> dict:
    """Independent loop-correction solve; reservoirs join through a virtual datum node."""
    fixed = {r["name"]: r["head_m"] for r in net["reservoirs"]}
    eps = net["roughness_m"]
    pipes = list(net["pipes"])
    flows, _ = _tree_flows(net)
    flows = list(flows)
    edges = [(p["ends"][0], p["ends"][1], k) for k, p in enumerate(pipes)]
    edges += [("*datum*", name, ("virtual", name)) for name in sorted(fixed)]
    flows += [0.0] * len(fixed)
    nodes = sorted({e[0] for e in edges} | {e[1] for e in edges})
    adjacency = {n: [] for n in nodes}
    for i, (a, b, _) in enumerate(edges):
        adjacency[a].append((i, b, 1))
        adjacency[b].append((i, a, -1))
    parent, depth, stack = {"*datum*": None}, {"*datum*": 0}, ["*datum*"]
    tree = set()
    while stack:
        node = stack.pop()
        for i, other, _ in adjacency[node]:
            if other not in parent:
                parent[other], depth[other] = (i, node), depth[node] + 1
                tree.add(i)
                stack.append(other)
    reservoir_flow = {name: 0.0 for name in fixed}
    for k, p in enumerate(pipes):
        a, b = p["ends"]
        if a in fixed:
            reservoir_flow[a] += flows[k]
        if b in fixed:
            reservoir_flow[b] -= flows[k]
    for i, (_, name, tag) in enumerate(edges):
        if isinstance(tag, tuple):
            flows[i] = reservoir_flow[name]

    def path_up(node):
        steps = []
        while parent[node] is not None:
            i, up = parent[node]
            steps.append((i, 1 if edges[i][1] == node else -1, node))
            node = up
        return steps

    loops = []
    for i, (a, b, _) in enumerate(edges):
        if i in tree:
            continue
        # loop: a -> b along the chord, then b -> a through the tree
        up_b, up_a = path_up(b), path_up(a)
        common = {n for _, _, n in up_b} & {n for _, _, n in up_a}
        loop = [(i, 1)]
        for j, sign, node in up_b:
            if node in common:
                break
            loop.append((j, -sign))
        for j, sign, node in up_a:
            if node in common:
                break
            loop.append((j, sign))
        loops.append(loop)

    def drop(i, q):
        tag = edges[i][2]
        return -fixed[tag[1]] if isinstance(tag, tuple) else pipe_head_loss(q, pipes[tag], eps)

    def slope(i, q):
        tag = edges[i][2]
        return 0.0 if isinstance(tag, tuple) else _head_slope(q, pipes[tag], eps)

    for sweep in range(max_sweeps):
        largest = 0.0
        for loop in loops:
            imbalance = sum(sign * drop(i, flows[i]) for i, sign in loop)
            correction = -imbalance / sum(slope(i, flows[i]) for i, _ in loop)
            for i, sign in loop:
                flows[i] += sign * correction
            largest = max(largest, abs(correction))
        if largest < tol:
            break
    else:
        raise IllPosed("Hardy Cross did not converge")
    return {"flows_m3_s": {pipes[k]["name"]: flows[i] for i, (_, _, k) in enumerate(edges)
                           if not isinstance(k, tuple)}, "sweeps": sweep + 1, "loops": len(loops)}


def check_pipes(net: dict, solution: dict) -> dict:
    violations = [f"{name} velocity {_fmt(item['velocity_m_s'])} m/s > {_fmt(net['max_velocity_m_s'])} m/s"
                  for name, item in sorted(solution["pipes"].items())
                  if item["velocity_m_s"] > net["max_velocity_m_s"]]
    violations += [f"{name} pressure head {_fmt(item['pressure_head_m'])} m < {_fmt(net['min_pressure_m'])} m"
                   for name, item in sorted(solution["junctions"].items())
                   if item["pressure_head_m"] < net["min_pressure_m"]]
    return {"pass": not violations, "violations": violations}


def pipe_chains(points: dict, nodes: set) -> list[dict]:
    """Walk from node to node through pass-through points; returns point paths."""
    adjacency = {}
    for a, b in points["edges"]:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
    used, chains = set(), []
    for start in sorted(nodes, key=lambda n: points["xy"][n]):
        for first in adjacency.get(start, []):
            if frozenset((start, first)) in used:
                continue
            path = [start, first]
            used.add(frozenset((start, first)))
            while path[-1] not in nodes:
                options = [n for n in adjacency[path[-1]] if frozenset((path[-1], n)) not in used]
                if len(options) != 1:
                    raise RecoveryError("pipe path branches without a junction")
                used.add(frozenset((path[-1], options[0])))
                path.append(options[0])
            chains.append(path)
    return chains


def _bends(polyline) -> int:
    count = 0
    for before, here, after in zip(polyline, polyline[1:], polyline[2:]):
        d1 = np.subtract(here, before)
        d2 = np.subtract(after, here)
        cosine = float(d1 @ d2 / (np.linalg.norm(d1) * np.linalg.norm(d2)))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        if angle < 0.5:
            continue
        if abs(angle - 90) > 1.0:
            raise RecoveryError(f"pipe bend of {angle:.1f} degrees is not a 90 degree elbow")
        count += 1
    return count


def recover_pipes(svg: str, tol: float = TOL) -> dict:
    found = geometry.extract(svg)
    heavy = [s for s in found["segments"] if s["stroke_width"] >= PIPE_MIN_WIDTH]
    dots, _ = _split_circles(found["circles"], heavy, tol)
    segments = _split_at_junctions(heavy, dots, tol)
    points = _Points(tol)
    edges = [(points.add(s["a"]), points.add(s["b"])) for s in segments]
    edges = [e for e in edges if e[0] != e[1]]
    degree = {}
    for a, b in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    reservoir_of = {}
    tanks = []
    for rect in found["rectangles"]:
        corners = rect["corners"]
        on_edge = [i for i in degree
                   if min(_point_to_polyline(points.xy[i], [corners[k], corners[(k + 1) % 4]]) for k in range(4)) <= tol]
        if on_edge:
            center = [sum(c[0] for c in corners) / 4, sum(c[1] for c in corners) / 4]
            tanks.append({"center": center, "points": on_edge})
            for i in on_edge:
                reservoir_of[i] = len(tanks) - 1
    dotted = {points.find(d["center"]) for d in dots} - {None}
    nodes = {i for i in degree if degree[i] != 2 or i in dotted or i in reservoir_of}
    if not nodes:
        raise RecoveryError("no pipe junctions found")
    chains = pipe_chains({"xy": points.xy, "edges": edges}, nodes)
    labels = {"pipe": [], "junction": [], "reservoir": []}
    for text in found["texts"]:
        if (m := PIPE_LABEL.match(text["text"])):
            labels["pipe"].append(("P" + m.group(1), float(m.group(2)), float(m.group(3)), text["position"]))
        elif (m := JUNCTION_LABEL.match(text["text"])):
            labels["junction"].append(("J" + m.group(1), float(m.group(2)), float(m.group(3)), text["position"]))
        elif (m := RESERVOIR_LABEL.match(text["text"])):
            labels["reservoir"].append(("R" + m.group(1), float(m.group(2)), text["position"]))
    junction_points = sorted(n for n in nodes if n not in reservoir_of)
    # Reach scales with the drawing: the median pipe segment is one grid step (160 px as drawn).
    step = _median([math.dist(points.xy[a], points.xy[b]) for a, b in edges], 160.0)
    to_junction = _assign_labels(labels["junction"], junction_points,
                                 lambda label, n: math.dist(label[3], points.xy[n]), 0.35 * step)
    to_tank = _assign_labels(labels["reservoir"], tanks,
                             lambda label, t: math.dist(label[2], t["center"]), 0.6 * step)
    to_pipe = _assign_labels(labels["pipe"], chains,
                             lambda label, c: _point_to_polyline(label[3], [points.xy[i] for i in c]), 0.3 * step)
    name_of, junctions, reservoirs = {}, [], []
    for j, n in enumerate(junction_points):
        if j not in to_junction:
            raise RecoveryError(f"junction at {[round(v, 2) for v in points.xy[n]]} has no demand/elevation label")
        name, q, z, _ = labels["junction"][to_junction[j]]
        name_of[n] = name
        junctions.append({"name": name, "demand_m3_s": q / 1000, "elevation_m": z})
    for t, tank in enumerate(tanks):
        if t not in to_tank:
            raise RecoveryError("reservoir without a head label")
        name, head, _ = labels["reservoir"][to_tank[t]]
        reservoirs.append({"name": name, "head_m": head})
        for n in tank["points"]:
            name_of[n] = name
    notes = " ".join(t["text"] for t in found["texts"])
    found_notes = [ROUGHNESS_NOTE.search(notes), ELBOW_NOTE.search(notes),
                   PRESSURE_NOTE.search(notes), VELOCITY_NOTE.search(notes)]
    if not all(found_notes):
        raise RecoveryError("roughness, elbow, pressure or velocity note missing")
    roughness, elbow, pressure, velocity = (float(m.group(1)) for m in found_notes)
    pipes = []
    for c, chain in enumerate(chains):
        if c not in to_pipe:
            raise RecoveryError(f"pipe starting at {[round(v, 2) for v in points.xy[chain[0]]]} has no label")
        name, length, diameter, _ = labels["pipe"][to_pipe[c]]
        ends = [name_of[chain[0]], name_of[chain[-1]]]
        if ends[0] == ends[1]:
            raise RecoveryError(f"{name} starts and ends at {ends[0]}")
        bends = _bends([points.xy[i] for i in chain])
        pipes.append({"name": name, "ends": ends, "length_m": length, "diameter_m": diameter / 1000,
                      "elbows": bends, "minor_K": bends * elbow})
    names = [p["name"] for p in pipes] + [j["name"] for j in junctions] + [r["name"] for r in reservoirs]
    if len(set(names)) != len(names):
        raise RecoveryError("duplicate names in the drawing")
    if not reservoirs:
        raise RecoveryError("no reservoir found")
    return {"junctions": junctions, "reservoirs": reservoirs, "pipes": pipes, "roughness_m": roughness / 1000,
            "elbow_K": elbow, "min_pressure_m": pressure, "max_velocity_m_s": velocity}


def pipe_netlist(model: dict) -> dict:
    """Reference network straight from the parametric model."""
    at = {tuple(j["at"]): j["name"] for j in model["junctions"]}
    at.update({tuple(r["at"]): r["name"] for r in model["reservoirs"]})
    pipes = []
    for p in model["pipes"]:
        route = [tuple(rc) for rc in p["route"]]
        elbows = sum(1 for a, b, c in zip(route, route[1:], route[2:])
                     if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]))
        pipes.append({"name": p["name"], "ends": [at[route[0]], at[route[-1]]], "length_m": float(p["length_m"]),
                      "diameter_m": p["diameter_mm"] / 1000, "elbows": elbows, "minor_K": elbows * model["elbow_K"]})
    return {"junctions": [{"name": j["name"], "demand_m3_s": j["demand_Ls"] / 1000, "elevation_m": float(j["elev_m"])}
                          for j in model["junctions"]],
            # A tank no pipe touches is not part of the network (recovery cannot see it either).
            "reservoirs": [{"name": r["name"], "head_m": float(r["head_m"])} for r in model["reservoirs"]
                           if any(r["name"] in p["ends"] for p in pipes)],
            "pipes": pipes, "roughness_m": model["roughness_mm"] / 1000, "elbow_K": model["elbow_K"],
            "min_pressure_m": float(model["min_pressure_m"]), "max_velocity_m_s": float(model["max_velocity_m_s"])}


def _pipe_signature(net: dict):
    pipes = sorted((p["name"], tuple(sorted(p["ends"])), round(p["length_m"], 9), round(p["diameter_m"], 9), p["elbows"])
                   for p in net["pipes"])
    junctions = sorted((j["name"], round(j["demand_m3_s"], 12), j["elevation_m"]) for j in net["junctions"])
    reservoirs = sorted((r["name"], r["head_m"]) for r in net["reservoirs"])
    notes = (round(net["roughness_m"], 12), net["elbow_K"], net["min_pressure_m"], net["max_velocity_m_s"])
    return pipes, junctions, reservoirs, notes


def compare_pipes(reference: dict, other: dict, flow_tol: float = 1e-9, head_tol: float = 1e-7) -> dict:
    same = _pipe_signature(reference) == _pipe_signature(other)
    first, second = solve_pipes(reference), solve_pipes(other)
    gaps, head_gaps = [], []
    for name, item in first["pipes"].items():
        if name in second["pipes"]:
            gaps.append(abs(abs(item["flow_m3_s"]) - abs(second["pipes"][name]["flow_m3_s"])))
    for name, item in first["junctions"].items():
        if name in second["junctions"]:
            head_gaps.append(abs(item["head_m"] - second["junctions"][name]["head_m"]))
    equal = (set(first["pipes"]) == set(second["pipes"]) and set(first["junctions"]) == set(second["junctions"])
             and max(gaps + [0]) <= flow_tol and max(head_gaps + [0]) <= head_tol)
    return {"topology_equal": same, "physics_equal": equal,
            "max_flow_gap_m3_s": max(gaps + [0.0]), "max_head_gap_m": max(head_gaps + [0.0])}


def _random_tree(vertices, edges, rng):
    union, order, chosen = _Union(len(vertices)), edges[:], []
    index = {v: i for i, v in enumerate(vertices)}
    rng.shuffle(order)
    for a, b in order:
        if union.join(index[a], index[b]):
            chosen.append((a, b))
    return chosen


def pipe_model(rng: random.Random, index: int = 0, rows_choices=(2, 3), cols_choices=(3, 4, 5),
               chords=(1, 3)) -> dict:
    while True:
        rows, cols = rng.choice(rows_choices), rng.choice(cols_choices)
        vertices = [(r, c) for r in range(rows) for c in range(cols)]
        grid = _grid_edges(rows, cols)
        edges = _random_tree(vertices, grid, rng)
        spare = [e for e in grid if e not in edges]
        rng.shuffle(spare)
        edges += spare[:rng.randint(chords[0], min(chords[1], len(spare)))]
        degree = {}
        for a, b in edges:
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
        for leaf in [v for v in vertices if degree.get(v) == 1]:
            if rng.random() < 0.4:
                edge = next(e for e in edges if leaf in e)
                edges.remove(edge)
                for v in edge:
                    degree[v] -= 1
        present = sorted(v for v in vertices if degree.get(v, 0) > 0)
        left_rows = [r for r in range(rows) if (r, 0) in present]
        right_rows = [r for r in range(rows) if (r, cols - 1) in present]
        if not left_rows:
            continue
        reservoirs = [{"name": "R1", "at": [rng.choice(left_rows), -1]}]
        if right_rows and rng.random() < 0.4:
            reservoirs.append({"name": "R2", "at": [rng.choice(right_rows), cols]})
        for tank in reservoirs:
            r, c = tank["at"]
            inner = (r, 0) if c < 0 else (r, cols - 1)
            edges.append(((r, c), inner))
            degree[inner] += 1
            degree[(r, c)] = 1
        tank_points = {tuple(t["at"]) for t in reservoirs}
        nodes = {v for v, d in degree.items() if d > 0 and (d != 2 or v in tank_points)}
        nodes |= {v for v, d in degree.items() if d == 2 and rng.random() < 0.35}
        chains = _model_chains(edges, nodes)
        if chains is None:
            continue
        junction_points = sorted(n for n in nodes if n not in tank_points)
        junctions = [{"name": f"J{i}", "at": list(v), "demand_Ls": rng.choice((0, 2, 4, 6, 8, 10, 15)),
                      "elev_m": rng.randrange(0, 31, 2)} for i, v in enumerate(junction_points, 1)]
        if not any(j["demand_Ls"] for j in junctions):
            continue
        top = max(j["elev_m"] for j in junctions)
        for tank in reservoirs:
            tank["head_m"] = top + rng.randint(18, 50)
        pipes = [{"name": f"P{i}", "route": [list(v) for v in chain], "length_m": rng.randrange(100, 801, 10),
                  "diameter_mm": rng.choice(DIAMETERS)} for i, chain in enumerate(chains, 1)]
        model = {"family": "pipe_network", "grid": [rows, cols], "reservoirs": reservoirs, "junctions": junctions,
                 "pipes": pipes, "roughness_mm": rng.choice((0.0015, 0.05, 0.15, 0.26)), "elbow_K": 0.9,
                 "min_pressure_m": rng.choice((10, 15, 20)), "max_velocity_m_s": rng.choice((1.5, 2.0, 2.5))}
        try:
            solve_pipes(pipe_netlist(model))
        except IllPosed:
            continue
        return model


def _model_chains(edges, nodes):
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
    for _ in range(10):
        used, chains, ok = set(), [], True
        for start in sorted(nodes):
            for first in sorted(adjacency[start]):
                if frozenset((start, first)) in used:
                    continue
                path = [start, first]
                used.add(frozenset((start, first)))
                while path[-1] not in nodes:
                    step = next(n for n in adjacency[path[-1]] if frozenset((path[-1], n)) not in used)
                    used.add(frozenset((path[-1], step)))
                    path.append(step)
                if path[0] == path[-1]:
                    nodes.add(path[len(path) // 2])
                    ok = False
                    break
                chains.append(path)
            if not ok:
                break
        if ok:
            return chains
    return None


def _label_anchor(route, cols):
    xy = [_pxy(rc, cols) for rc in route]
    pairs = list(zip(xy, xy[1:]))
    (ax, ay), (bx, by) = max(pairs, key=lambda pair: math.dist(*pair))
    if ay == by:
        return (ax + bx) / 2, ay - 12, "middle"
    return ax + 12, (ay + by) / 2 + 4, "start"


def render_pipes(model: dict) -> str:
    rows, cols = model["grid"]
    height = P_Y0 + (rows - 1) * P_DY + 200
    width = max(1100, P_X0 + (cols - 1) * P_DX + P_RES + 90)  # 1100 for the five-column v1 grids
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
             f'<rect id="background" width="{width}" height="{height}" fill="white"/>',
             f'<text id="title" x="40" y="50" font-size="22" font-weight="bold" fill="{P_STROKE}">'
             'Water distribution network</text>',
             f'<g id="pipes" fill="none" stroke="{P_STROKE}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">']
    for pipe in model["pipes"]:
        xy = [_pxy(rc, cols) for rc in pipe["route"]]
        d = "M" + " L".join(f"{_fmt(x)} {_fmt(y)}" for x, y in xy)
        parts.append(f'<path id="{pipe["name"]}" d="{d}"/>')
    parts += ['</g>', f'<g id="pipe-labels" font-size="12" fill="{P_STROKE}">']
    for pipe in model["pipes"]:
        x, y, anchor = _label_anchor(pipe["route"], cols)
        parts.append(f'<text id="{pipe["name"]}-label" x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="{anchor}">'
                     f'{pipe["name"]} {_fmt(pipe["length_m"])} m Ø{_fmt(pipe["diameter_mm"])}</text>')
    parts += ['</g>', f'<g id="reservoirs" stroke="{P_STROKE}">']
    for tank in model["reservoirs"]:
        x, y = _pxy(tank["at"], cols)
        left = x - 70 if tank["at"][1] < 0 else x
        parts += [f'<g id="{tank["name"]}">',
                  f'<rect id="{tank["name"]}-body" x="{_fmt(left)}" y="{_fmt(y - 25)}" width="70" height="50" '
                  f'fill="#cfe8ff" stroke-width="2"/>',
                  f'<line id="{tank["name"]}-level" x1="{_fmt(left + 8)}" y1="{_fmt(y - 12)}" x2="{_fmt(left + 62)}" '
                  f'y2="{_fmt(y - 12)}" stroke-width="1.5"/>',
                  f'<text id="{tank["name"]}-label" x="{_fmt(left + 35)}" y="{_fmt(y - 36)}" font-size="13" '
                  f'text-anchor="middle" stroke="none" fill="{P_STROKE}">{tank["name"]} H={_fmt(tank["head_m"])} m</text>',
                  '</g>']
    parts += ['</g>', f'<g id="junctions" fill="{P_STROKE}">']
    for j in model["junctions"]:
        x, y = _pxy(j["at"], cols)
        parts += [f'<g id="{j["name"]}">',
                  f'<circle id="{j["name"]}-dot" cx="{_fmt(x)}" cy="{_fmt(y)}" r="6"/>',
                  f'<text id="{j["name"]}-label" x="{_fmt(x + 8)}" y="{_fmt(y + 22)}" font-size="11">'
                  f'{j["name"]} q={_fmt(j["demand_Ls"])} L/s z={_fmt(j["elev_m"])} m</text>',
                  '</g>']
    base = P_Y0 + (rows - 1) * P_DY + 110
    notes = [("roughness-note", f'Pipe roughness ε = {_fmt(model["roughness_mm"])} mm'),
             ("elbow-note", f'Minor loss: 90° elbow K = {_fmt(model["elbow_K"])}'),
             ("pressure-note", f'Minimum pressure head {_fmt(model["min_pressure_m"])} m'),
             ("velocity-note", f'Maximum velocity {_fmt(model["max_velocity_m_s"])} m/s')]
    parts.append('</g>')
    for i, (key, text) in enumerate(notes):
        parts.append(f'<text id="{key}" x="{40 + 520 * (i % 2)}" y="{base + 26 * (i // 2)}" font-size="14" '
                     f'fill="{P_STROKE}">{text}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def pipe_edits(model: dict, rng: random.Random) -> list[tuple]:
    def diameter_edit():
        pick = rng.choice(model["pipes"])
        target = copy.deepcopy(model)
        value = rng.choice([d for d in DIAMETERS if d != pick["diameter_mm"]])
        next(p for p in target["pipes"] if p["name"] == pick["name"])["diameter_mm"] = value
        return f"Change the diameter of {pick['name']} to {value} mm.", target, "pipe_diameter"

    first = diameter_edit()
    pick = rng.choice(model["junctions"])
    target = copy.deepcopy(model)
    value = rng.choice([q for q in (0, 2, 4, 6, 8, 10, 15, 20) if q != pick["demand_Ls"]])
    next(j for j in target["junctions"] if j["name"] == pick["name"])["demand_Ls"] = value
    second = (f"Set the demand at {pick['name']} to {value} L/s.", target, "junction_demand")

    third = None
    for pipe in rng.sample(model["pipes"], len(model["pipes"])):
        target = copy.deepcopy(model)
        target["pipes"] = [p for p in target["pipes"] if p["name"] != pipe["name"]]
        if len(pipe_netlist(target)["reservoirs"]) != len(model["reservoirs"]):
            continue  # never cut a reservoir off entirely
        try:
            _tree_flows(pipe_netlist(target))
            solve_pipes(pipe_netlist(target))
        except IllPosed:
            continue
        third = (f"Remove pipe {pipe['name']}.", target, "remove_pipe")
        break
    if third is None:
        tank = rng.choice(model["reservoirs"])
        target = copy.deepcopy(model)
        value = tank["head_m"] + rng.choice((-12, -8, 8, 12))
        next(t for t in target["reservoirs"] if t["name"] == tank["name"])["head_m"] = value
        third = (f"Set reservoir {tank['name']} to H = {value} m.", target, "reservoir_head")

    used_edges = {frozenset((tuple(a), tuple(b))) for p in model["pipes"] for a, b in zip(p["route"], p["route"][1:])}
    at = {tuple(j["at"]): j["name"] for j in model["junctions"]}
    candidates = []
    for a in at:
        for b in ((a[0], a[1] + 1), (a[0] + 1, a[1])):
            if b in at and frozenset((a, b)) not in used_edges:
                candidates.append((a, b))
    if candidates:
        a, b = rng.choice(candidates)
        target = copy.deepcopy(model)
        name = f"P{len(model['pipes']) + 1}"
        length, diameter = rng.randrange(100, 801, 10), rng.choice(DIAMETERS)
        target["pipes"].append({"name": name, "route": [list(a), list(b)], "length_m": length, "diameter_mm": diameter})
        fourth = (f"Add pipe {name} ({length} m, Ø{diameter} mm) between {at[a]} and {at[b]}.", target, "add_pipe")
    else:
        pick = rng.choice(model["pipes"])
        target = copy.deepcopy(model)
        value = pick["length_m"] + rng.choice((-50, 50, 100))
        next(p for p in target["pipes"] if p["name"] == pick["name"])["length_m"] = value
        fourth = (f"Change the length of {pick['name']} to {value} m.", target, "pipe_length")
    return [first, second, third, fourth]


def pipe_report(svg: str, model: dict) -> dict:
    recovered = recover_pipes(svg)
    solution = solve_pipes(recovered)
    loops = hardy_cross(recovered)
    agreement = max([abs(loops["flows_m3_s"][n] - item["flow_m3_s"]) for n, item in solution["pipes"].items()] + [0.0])
    verdict = check_pipes(recovered, solution)
    match = compare_pipes(pipe_netlist(model), recovered)
    return {"method": "newton_flow_head_solve_of_recovered_drawing", **verdict,
            "recovered_matches_model": match["topology_equal"] and match["physics_equal"],
            "independent_loops": solution["independent_loops"],
            "pipe_flows_L_s": {k: round(v["flow_m3_s"] * 1000, 9) for k, v in sorted(solution["pipes"].items())},
            "pipe_velocities_m_s": {k: round(v["velocity_m_s"], 9) for k, v in sorted(solution["pipes"].items())},
            "pressure_heads_m": {k: round(v["pressure_head_m"], 9) for k, v in sorted(solution["junctions"].items())},
            "energy_residual_m": solution["energy_residual_m"],
            "continuity_residual_m3_s": solution["continuity_residual_m3_s"],
            "mass_balance_residual_m3_s": solution["mass_balance_residual_m3_s"],
            "hardy_cross_max_flow_gap_m3_s": agreement,
            "criteria": {"max_velocity_m_s": recovered["max_velocity_m_s"],
                         "min_pressure_head_m": recovered["min_pressure_m"]},
            "assumptions": ["steady incompressible water at 20 C", "Churchill friction factor",
                            "tee and junction losses neglected", "90 degree elbows counted from the drawing"]}


FAMILIES = {
    "dc_network": (circuit_model, circuit_edits, render_circuit, circuit_report,
                   recover_circuit, circuit_netlist, compare_circuits),
    "pipe_network": (pipe_model, pipe_edits, render_pipes, pipe_report,
                     recover_pipes, pipe_netlist, compare_pipes),
}


def physics_match(svg: str, family: str, target_model: dict) -> dict:
    """Score any SVG (e.g. a model's edited drawing) against the target design by re-solving it."""
    _, _, _, _, recover, netlist, compare = FAMILIES[family]
    try:
        recovered = recover(svg)
    except (RecoveryError, ValueError) as error:
        return {"recovered": False, "physics_equal": False, "reason": str(error)[:200]}
    try:
        result = compare(netlist(target_model), recovered)
    except IllPosed as error:
        return {"recovered": True, "physics_equal": False, "reason": "ill-posed: " + str(error)[:200]}
    return {"recovered": True, **result}


# --------------------------------------------------------------------------------------------
# Analytical controls
# --------------------------------------------------------------------------------------------

def controls() -> list[dict]:
    rows = []

    def add(name, value, expected, tol):
        value, expected = float(value), float(expected)
        rows.append({"control": name, "value": value, "expected": expected,
                     "pass": bool(abs(value - expected) <= tol * max(1.0, abs(expected)))})

    net = {"resistors": [{"name": "R1", "ohm": 100.0, "nodes": [0, 1]}, {"name": "R2", "ohm": 220.0, "nodes": [1, 2]}],
           "sources": [{"name": "V1", "volt": 12.0, "plus": 0, "minus": 2}], "node_count": 3, "rating_W": 1, "fuse_A": 1}
    add("series current V/(R1+R2)", solve_circuit(net)["sources"]["V1"]["current_A"], 12 / 320, 1e-12)
    net["resistors"][1]["nodes"] = [0, 2]
    net["resistors"][0]["nodes"] = [0, 2]
    add("parallel current V(1/R1+1/R2)", solve_circuit(net)["sources"]["V1"]["current_A"], 12 / 100 + 12 / 220, 1e-12)

    def bridge(r1, r2, r3, r4, r5, v=10.0):
        return {"resistors": [{"name": "Ra", "ohm": r1, "nodes": [0, 1]}, {"name": "Rb", "ohm": r2, "nodes": [1, 3]},
                              {"name": "Rc", "ohm": r3, "nodes": [0, 2]}, {"name": "Rd", "ohm": r4, "nodes": [2, 3]},
                              {"name": "Rg", "ohm": r5, "nodes": [1, 2]}],
                "sources": [{"name": "V1", "volt": v, "plus": 0, "minus": 3}], "node_count": 4, "rating_W": 1, "fuse_A": 1}
    add("balanced Wheatstone bridge current", solve_circuit(bridge(100, 200, 50, 100, 330))["resistors"]["Rg"]["current_A"], 0.0, 1e-15)
    r1, r2, r3, r4, r5, v = 100.0, 220.0, 150.0, 470.0, 47.0, 10.0  # 220/320 != 470/620
    thevenin_v = v * (r2 / (r1 + r2) - r4 / (r3 + r4))
    thevenin_r = r1 * r2 / (r1 + r2) + r3 * r4 / (r3 + r4)
    add("unbalanced bridge vs Thevenin", solve_circuit(bridge(r1, r2, r3, r4, r5))["resistors"]["Rg"]["current_A"],
        thevenin_v / (thevenin_r + r5), 1e-12)
    two = {"resistors": [{"name": "R1", "ohm": 10.0, "nodes": [0, 1]}, {"name": "R2", "ohm": 20.0, "nodes": [1, 2]},
                         {"name": "R3", "ohm": 30.0, "nodes": [1, 3]}],
           "sources": [{"name": "V1", "volt": 12.0, "plus": 0, "minus": 3}, {"name": "V2", "volt": 5.0, "plus": 2, "minus": 3}],
           "node_count": 4, "rating_W": 1, "fuse_A": 1}
    both = solve_circuit(two)["resistors"]["R3"]["current_A"]
    alone = []
    for keep in ("V1", "V2"):
        single = copy.deepcopy(two)
        for s in single["sources"]:
            if s["name"] != keep:
                s["volt"] = 0.0
        alone.append(solve_circuit(single)["resistors"]["R3"]["current_A"])
    add("superposition of two sources", both, sum(alone), 1e-12)

    pipe = {"name": "P1", "ends": ["R1", "R2"], "length_m": 500.0, "diameter_m": 0.15, "minor_K": 0.0, "elbows": 0}
    single = {"junctions": [], "reservoirs": [{"name": "R1", "head_m": 40.0}, {"name": "R2", "head_m": 30.0}],
              "pipes": [pipe], "roughness_m": 5e-5}
    low, high = 0.0, 1.0
    for _ in range(200):
        mid = (low + high) / 2
        low, high = (mid, high) if pipe_head_loss(mid, pipe, 5e-5) < 10.0 else (low, mid)
    add("two reservoirs vs bisection (m3/s)", solve_pipes(single)["pipes"]["P1"]["flow_m3_s"], low, 1e-9)
    laminar = {"name": "P1", "ends": ["R1", "J1"], "length_m": 100.0, "diameter_m": 0.1, "minor_K": 0.0, "elbows": 0}
    q = 1e-5
    add("laminar loss vs Hagen-Poiseuille (m)", pipe_head_loss(q, laminar, 5e-5),
        128 * MU * 100.0 * q / (math.pi * RHO * GRAVITY * 0.1 ** 4), 1e-9)
    reynolds, rel = 1e6, 1e-4
    colebrook = 0.02
    for _ in range(100):
        colebrook = (-2 * math.log10(rel / 3.7 + 2.51 / (reynolds * math.sqrt(colebrook)))) ** -2
    add("Churchill vs Colebrook at Re=1e6 (relative gap)", churchill_friction(reynolds, rel) / colebrook, 1.0, 0.02)
    loop = {"junctions": [{"name": "J1", "demand_m3_s": 0.0, "elevation_m": 0.0},
                          {"name": "J2", "demand_m3_s": 0.03, "elevation_m": 0.0},
                          {"name": "J3", "demand_m3_s": 0.02, "elevation_m": 0.0},
                          {"name": "J4", "demand_m3_s": 0.025, "elevation_m": 0.0}],
            "reservoirs": [{"name": "R1", "head_m": 60.0}, {"name": "R2", "head_m": 55.0}],
            "pipes": [{"name": n, "ends": e, "length_m": L, "diameter_m": d, "minor_K": 0.0, "elbows": 0}
                      for n, e, L, d in (("P1", ["R1", "J1"], 300, 0.25), ("P2", ["J1", "J2"], 400, 0.2),
                                         ("P3", ["J1", "J3"], 350, 0.15), ("P4", ["J2", "J4"], 300, 0.15),
                                         ("P5", ["J3", "J4"], 450, 0.1), ("P6", ["J2", "J3"], 250, 0.1),
                                         ("P7", ["R2", "J4"], 500, 0.15))],
            "roughness_m": 5e-5}
    newton, cross = solve_pipes(loop), hardy_cross(loop)
    add("Newton vs Hardy Cross, two loops + two reservoirs (m3/s)",
        max(abs(newton["pipes"][n]["flow_m3_s"] - cross["flows_m3_s"][n]) for n in newton["pipes"]), 0.0, 1e-9)
    add("mass balance: reservoir supply = demand (m3/s)", newton["mass_balance_residual_m3_s"], 0.0, 1e-12)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--selftest", type=int, default=0, help="round-trip N random designs per family")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    if args.controls:
        print(json.dumps(controls(), indent=2))
    if args.selftest:
        rng = random.Random(args.seed)
        for family, (make, edits, render, report, *_rest) in FAMILIES.items():
            ok = 0
            for i in range(args.selftest):
                model = make(rng, i)
                result = report(render(model), model)
                ok += result["recovered_matches_model"]
                for _, target, _ in edits(model, rng):
                    ok += report(render(target), target)["recovered_matches_model"]
            print(family, f"{ok}/{args.selftest * 5} drawings recovered and re-solved to the model")
