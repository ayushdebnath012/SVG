"""Render the one verified Astra network-analysis failure from its saved response.

The SVG returned by Astra is solved before presentation overlays are added.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import engsvg_networks as N  # noqa: E402
import network_astra_benchmark as B  # noqa: E402

ROW_ID = "net-pipe_network-0003371ea274123f:edit-4"
RUN = ROOT / "runs/network-astra-20260927/net-pipe_network-0003371ea274123f_edit-4"


def _load() -> tuple[dict, str, dict]:
    data = ROOT / "data/engsvg-network-edit-v1/test.jsonl.gz"
    with gzip.open(data, "rt", encoding="utf-8") as handle:
        row = next(row for row in map(json.loads, handle) if row["id"] == ROW_ID)
    svg, analysis = B._blocks((RUN / "response.txt").read_text())
    assert svg == row["target_svg"]  # exact edit, so the error is in the analysis
    grade = B.score_answer(row, svg, analysis)
    assert grade["edit_correct"] and not grade["verdict_correct"]
    return row, svg, analysis


def _solve(svg: str) -> tuple[dict, dict]:
    network = N.recover_pipes(svg)
    solution = N.solve_pipes(network)
    return solution, N.check_pipes(network, solution)


def _annotate(svg: str, claim: dict, solved: dict) -> str:
    match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    assert match and match.groups() == ("1100", "530")
    svg = svg.replace(match.group(0), 'viewBox="0 0 1100 704"', 1).replace('height="530"', 'height="704"', 1)
    j4 = solved["junctions"]["J4"]["pressure_head_m"]
    annotation = f"""
<g font-family="Arial,Helvetica,sans-serif">
  <path d="M580 330 H740" fill="none" stroke="#d77b1e" stroke-width="12" stroke-dasharray="18 8" opacity=".78"/>
  <circle cx="420" cy="330" r="18" fill="none" stroke="#bf3434" stroke-width="5"/>
  <rect x="18" y="537" width="1064" height="152" rx="14" fill="#f5f8fb" stroke="#cbd8e4" stroke-width="2"/>
  <circle cx="54" cy="574" r="10" fill="#d77b1e"/>
  <text x="78" y="584" font-size="27" font-weight="bold" fill="#193b59">Astra edit: P9 290 to 340 m - drawing is correct</text>
  <text x="78" y="624" font-size="27" font-weight="bold" fill="#a24a0e">Astra analysis: PASS; J4 = {claim['min_pressure_head_m']['value']:.2f} m</text>
  <circle cx="54" cy="657" r="10" fill="#bf3434"/>
  <text x="78" y="667" font-size="27" font-weight="bold" fill="#9d292c">Solve of returned SVG: FAIL; J4 = {j4:.2f} m (min 20 m)</text>
</g>"""
    return svg.replace("</svg>", annotation + "\n</svg>")


def _teaser(svg: str, claim: dict, solved: dict) -> str:
    match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    assert match and match.groups() == ("1100", "530")
    svg = svg.replace(match.group(0), 'viewBox="0 100 1100 390"', 1).replace('height="530"', 'height="390"', 1)
    j4 = solved["junctions"]["J4"]["pressure_head_m"]
    annotation = f"""
<g font-family="Arial,Helvetica,sans-serif">
  <text x="340" y="140" font-size="30" font-weight="bold" fill="#193b59">Edit P9: 290 to 340 m</text>
  <path d="M580 330 H740" fill="none" stroke="#d77b1e" stroke-width="13" stroke-dasharray="18 8" opacity=".8"/>
  <circle cx="420" cy="330" r="20" fill="none" stroke="#bf3434" stroke-width="6"/>
  <rect x="18" y="393" width="515" height="90" rx="12" fill="#fff4e7" stroke="#d77b1e" stroke-width="3"/>
  <rect x="550" y="393" width="532" height="90" rx="12" fill="#fff0ef" stroke="#bf3434" stroke-width="3"/>
  <text x="43" y="429" font-size="26" font-weight="bold" fill="#a24a0e">Astra analysis: PASS</text>
  <text x="43" y="466" font-size="29" font-weight="bold" fill="#a24a0e">J4 = {claim['min_pressure_head_m']['value']:.2f} m</text>
  <text x="575" y="429" font-size="26" font-weight="bold" fill="#9d292c">Solve returned SVG: FAIL</text>
  <text x="575" y="466" font-size="29" font-weight="bold" fill="#9d292c">J4 = {j4:.2f} m &lt; 20 m</text>
</g>"""
    return svg.replace("</svg>", annotation + "\n</svg>")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "paper/network/figures")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    row, response_svg, claim = _load()
    before, before_check = _solve(row["source_svg"])
    solved, solved_check = _solve(response_svg)
    assert claim["verdict"] == "pass" and not solved_check["pass"]
    assert solved_check["violations"] == ["J4 pressure head 19.2277 m < 20 m"]
    annotated = _annotate(response_svg, claim, solved)
    teaser = _teaser(response_svg, claim, solved)
    import fitz
    for name, svg in (("astra-failure-source", row["source_svg"]),
                      ("astra-failure-response-annotated", annotated),
                      ("astra-failure-teaser", teaser)):
        path = args.out / f"{name}.svg"
        path.write_text(svg, encoding="utf-8")
        with fitz.open(stream=svg.encode(), filetype="svg") as drawing:
            path.with_suffix(".pdf").write_bytes(drawing.convert_to_pdf())
    facts = {
        "row_id": ROW_ID,
        "instruction": row["instruction"],
        "loops": row["before_verification"]["independent_loops"],
        "response_svg_sha256": hashlib.sha256(response_svg.encode()).hexdigest(),
        "response_is_exact_target": True,
        "source_J4_pressure_head_m": before["junctions"]["J4"]["pressure_head_m"],
        "source_pass": before_check["pass"],
        "astra_claim": claim,
        "solved_J4_pressure_head_m": solved["junctions"]["J4"]["pressure_head_m"],
        "solved_P4_velocity_m_s": solved["pipes"]["P4"]["velocity_m_s"],
        "solved_verdict": solved_check,
    }
    (args.out / "astra-failure-worked.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps({k: v for k, v in facts.items() if k != "astra_claim"}, indent=2))


if __name__ == "__main__":
    main()
