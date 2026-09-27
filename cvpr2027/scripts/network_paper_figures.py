"""Figures for the network paper: what recovery sees, and how Astra and our pipeline compare."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_networks as N  # noqa: E402
import engsvg_svg_geometry as geometry  # noqa: E402

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PALETTE = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#42d4f4", "#f032e6", "#9a6324",
           "#469990", "#800000", "#808000", "#000075", "#bfef45", "#fabed4", "#dcbeff", "#aaffc3"]


def _structure(svg: str, family: str):
    """Recovered nodes as coloured segment groups (the same steps recovery performs)."""
    found = geometry.extract(svg)
    segments = found["segments"]
    if family == "pipe_network":
        segments = [s for s in segments if s["stroke_width"] >= N.PIPE_MIN_WIDTH]
    dots, _ = N._split_circles(found["circles"], segments, N.TOL)
    segments = N._split_at_junctions(segments, dots, N.TOL)
    points = N._Points(N.TOL)
    ends = [(points.add(s["a"]), points.add(s["b"])) for s in segments]
    groups = []
    if family == "dc_network":
        union = N._Union(len(points.xy))
        for a, b in ends:
            union.join(a, b)
        roots = sorted({union.find(a) for a, _ in ends})
        for k, root in enumerate(roots):
            groups.append([(s["a"], s["b"]) for s, (a, _) in zip(segments, ends) if union.find(a) == root])
    else:
        degree = {}
        for a, b in ends:
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
        dotted = {points.find(d["center"]) for d in dots} - {None}
        nodes = {i for i in degree if degree[i] != 2 or i in dotted}
        for rect in found["rectangles"]:
            corners = rect["corners"]
            for i in degree:
                if min(N._point_to_polyline(points.xy[i], [corners[k], corners[(k + 1) % 4]]) for k in range(4)) <= N.TOL:
                    nodes.add(i)
        for chain in N.pipe_chains({"xy": points.xy, "edges": ends}, nodes):
            groups.append([(points.xy[a], points.xy[b]) for a, b in zip(chain, chain[1:])])
    return groups


def overlay(svg: str, family: str) -> str:
    groups = _structure(svg, family)
    width = 9 if family == "dc_network" else 12
    marks = []
    for k, group in enumerate(groups):
        colour = PALETTE[k % len(PALETTE)]
        for a, b in group:
            marks.append(f'<line x1="{a[0]:.3f}" y1="{a[1]:.3f}" x2="{b[0]:.3f}" y2="{b[1]:.3f}" '
                         f'stroke="{colour}" stroke-width="{width}" stroke-opacity="0.55" stroke-linecap="round"/>')
    head, rest = svg.split(">", 1)
    body, tail = rest.rsplit("</svg>", 1)
    return f'{head}>{body}<g id="recovered-overlay">{"".join(marks)}</g></svg>{tail}'


def png(svg: str, path: Path, size=(1100, 720)) -> None:
    svg_path = path.with_suffix(".svg")
    svg_path.write_text(svg)
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={size[0]},{size[1]}", f"--screenshot={path}", svg_path.resolve().as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)


def _size(svg: str):
    import re
    match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    return int(match.group(1)), int(match.group(2))


def teaser(out: Path, data: Path) -> dict:
    rows = [json.loads(line) for line in gzip.open(data / "test.jsonl.gz", "rt")]
    picks = {}
    for row in sorted(rows, key=lambda r: r["id"]):
        want = {"dc_network": "parallel_branch", "pipe_network": "add_pipe"}[row["family"]]
        if row["edit_kind"] == want and row["family"] not in picks and row["verdict_changed"]:
            picks[row["family"]] = row
    made = {}
    for family, row in picks.items():
        for side in ("source", "target"):
            svg = row[f"{side}_svg"]
            png(svg, out / f"teaser-{family}-{side}.png", _size(svg))
        png(overlay(row["target_svg"], family), out / f"teaser-{family}-recovered.png", _size(row["target_svg"]))
        made[family] = {"id": row["id"], "instruction": row["instruction"],
                        "before": {k: row["before_verification"][k] for k in ("pass", "violations")},
                        "after": {k: row["after_verification"][k] for k in ("pass", "violations")}}
    (out / "teaser.json").write_text(json.dumps(made, indent=2, ensure_ascii=False) + "\n")
    return made


def size_curve(out: Path, data: Path) -> None:
    """Edit accuracy against drawing size (SVG elements), from paper/network/figure-data.json."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    points = json.loads(data.read_text())
    edges = [0, 50, 75, 100, 130, 170, 240]
    styles = {"Astra": ("#555555", "o", "--"), "1.5B positional": ("#d95f02", "s", ":"),
              "1.5B id": ("#1b9e77", "^", "-"), "7B id": ("#7570b3", "D", "-")}
    fig, ax = plt.subplots(figsize=(3.4, 2.3), dpi=200)
    for label, rows in points.items():
        xs, ys, ns = [], [], []
        for lo, hi in zip(edges, edges[1:]):
            subset = [ok for n, _, ok in rows if lo <= n < hi]
            if len(subset) >= 5:
                xs.append((lo + hi) / 2); ys.append(100 * sum(subset) / len(subset)); ns.append(len(subset))
        colour, marker, line = styles.get(label, ("black", "o", "-"))
        ax.plot(xs, ys, color=colour, marker=marker, linestyle=line, markersize=3.5, linewidth=1.2, label=label)
    ax.axvline(121, color="#bbbbbb", linewidth=0.8)  # largest source drawing in the training split
    ax.text(123, 8, "larger than any\ntraining drawing", fontsize=5.5, color="#777777")
    ax.set_xlabel("SVG elements in the source drawing", fontsize=7)
    ax.set_ylabel("edit correct (%)", fontsize=7)
    ax.set_ylim(-3, 103)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.5, frameon=False, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "size-curve.pdf")
    fig.savefig(out / "size-curve.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "paper/network/figures")
    parser.add_argument("--data", type=Path, default=ROOT / "data/engsvg-network-edit-v1")
    parser.add_argument("--curve", action="store_true", help="only redraw the size curve")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.curve:
        size_curve(args.out, ROOT / "paper/network/figure-data.json")
    else:
        print(json.dumps(teaser(args.out, args.data), indent=2, ensure_ascii=False))
