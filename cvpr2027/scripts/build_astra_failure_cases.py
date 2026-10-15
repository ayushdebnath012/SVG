"""Build the Astra failure-case collection from saved runs (local; no model calls).

Every recorded GPT-6 Astra miss in this repository is re-checked here, and only misses that survive the check are
admitted as Astra failures. A miss is not admitted when our own reference or task is at fault: a released reference
STEP that differs from its own program, a reference whose added feature floats free of the part, a reference that
contradicts its instruction, an instruction that admits more than one reading, or a task that cannot be satisfied.

Sources: the 35 audited CAD-edit misses (runs/astra-failure-analysis-20261008, from the 252-task multisource CAD-edit
holdout run of 2026-10-04), the network-analysis run (runs/network-astra-20260927), the structural-frame screens
(runs/eng-frame-aggregate.json) and the CADFEM-Bench v1.5 hosted run (runs/hosted-v1.5).

  tmp/cq-env/bin/python scripts/build_astra_failure_cases.py      # needs OCP/CadQuery for the CAD measurements
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cad_edit_contracts import apply  # noqa: E402

VERSION = "0.1"
OUT = ROOT / f"output/datasets/astra-failure-cases-v{VERSION}"
TESTS = ROOT / "runs/multisource-cad-colab-20261002/results-final/test-retained.jsonl"
ASTRA = ROOT / "runs/multisource-cad-astra-20261004"
REPAIR = ROOT / "runs/multisource-cad-astra-repair-20261006"
AUDIT = ROOT / "runs/astra-failure-analysis-20261008/cases.json"
VENV = ROOT.parent / ".venv/bin/python"

# Adjudication of the 35 audited CAD-edit misses. Classes: astra_failure, reference_defect, task_defect,
# ambiguous_instruction. The measurements written next to each case are recomputed below.
VERDICTS = {
    # Astra's own answer is unusable or physically wrong.
    "d000c8c09d558154": ("astra_failure", "Patch inserts '.union(' after the statement's closing parenthesis, so the program does not run. "
                         "After one execution-feedback round it runs, but the boss sits at z 18.3-21.3 mm, the cone's nominal apex: the 6.7 mm "
                         "through-hole ends the hub at z 17.156 mm, so the boss floats 1.144 mm above it (two solids). "
                         "The reference boss also floats, 11.8 mm above the hub, so geometry is judged against the instruction, not the reference."),
    "511b48e9304b4f20": ("astra_failure", "Selects every edge of all +Z faces, including concave edges where the shank meets the bosses; "
                         "the 1.3 mm chamfer fails in the kernel and no solid is produced. Another Astra draft (alt1) solved it, and one "
                         "execution-feedback round produced a solid (IoU 0.983 with the reference program)."),
    "5eb603a43d1d4c21": ("astra_failure", "Raw API content is 223 characters of JSON patch that stops before its closing ']}' although finish_reason "
                         "is 'stop'; unparseable. The saved repair-round output is byte-identical with no response id, so it is not counted as a "
                         "second sample. The instruction is contradictory (2x2 grid 'around' the existing hole), so only the format failure counts."),
    # Our released reference STEP does not match its own reference program; Astra matches the program exactly.
    "78ed9867fdc028e6": ("reference_defect", "Astra's solid equals the reference program (IoU 1.000000); the released knob STEP differs from that program."),
    "ecf0700cefb8d74e": ("reference_defect", "Astra's solid equals the reference program (IoU 1.000000); the released knob STEP differs from that program."),
    "b2096df2210f9ba0": ("reference_defect", "Astra's solid equals the reference program (IoU 1.000000); the released knob STEP differs from that program."),
    "02f4de6321541a5c": ("reference_defect", "Astra's solid equals the reference program (IoU 1.000000); the released STEP's body is shorter, so its cap floats 0.65 mm above it."),
    "0a16dd8acdfcef6b": ("reference_defect", "Audit A1: exact 9.4/3 versus a reference rounded to 3.133; IoU 1.0000 to four decimals."),
    "a5b5cc677cadf72d": ("reference_defect", "Audit A1: patch identical to the reference program; the released reference STEP is invalid."),
    "99705d173001fd23": ("reference_defect", "Audit A1: patch identical to the reference program; the released STEP differs from that program."),
    "401745921cc1b509": ("reference_defect", "Audit A1: patch identical to the reference program; the released STEP differs from that program."),
    # The reference geometry is physically wrong or contradicts the instruction; Astra's answer satisfies the instruction.
    "36fbd041eb815d50": ("reference_defect", "Reference program centres a 30 mm boss over a 37.8 mm-wide through-slot, so the boss floats as a separate solid. "
                         "Astra puts it on the solid land beside the slot ('flanking the pocket'): one attached solid."),
    "277d8aa207505807": ("reference_defect", "Reference STEP is two solids: one end plate sits 19 mm away from the rest of the bracket. Astra's draft cannot be judged against it."),
    "1918890a624c01e6": ("reference_defect", "Reference STEP is two separate solids (raised face/neck left floating after the body height change). "
                         "Astra keeps them attached: one solid with exactly the same total volume (39,598.46 mm^3)."),
    "af5c96f6ae6060d3": ("reference_defect", "Bottom face is at z = -5.7 mm. Astra places the cross-holes 25 and 45 mm above it, as instructed; "
                         "the reference uses absolute z = 25 and 45 mm."),
    "5349e2901f1920ed": ("reference_defect", "Astra's bevel is the requested one (top apothem 4.50 mm = 6.50 - 2, drop 1.1547 mm = 30 degrees on all six edges). "
                         "The reference chamfer(2.0, 1.1547) swaps the lengths on some edges: asymmetric top face and a 60-degree bevel down to z = 13.0."),
    "75843f475cb19d81": ("reference_defect", "Astra keeps both hole rows at their original positions, as instructed; the reference deletion also removes "
                         "the workplane offset and moves every hole by 1.5 mm."),
    # The task cannot be satisfied as written.
    "51b6a18ad24356d6": ("task_defect", "A ring with 26 mm inner radius cannot lie against a waist whose largest radius is 25.3 mm; both reference and Astra rings float."),
    "ca142e3a04e88741": ("task_defect", "Instruction calls the r = 100 mm wall the inlet 'outer radius', but the outer wall is r = 123.2 mm; the reference edit makes the profile self-intersect."),
    # More than one reasonable reading; Astra chose a defensible one.
    "c2b9c8d36d164d83": ("ambiguous_instruction", "Audit A2: instruction says 33 mm; reference hole is 33.4 mm."),
    "6689506209c6d6ff": ("ambiguous_instruction", "Audit A2: instruction gives 18 x 7 x 7; reference uses 18.16 x 6.81 x 7.06."),
    "d4b7105feb7f1c04": ("ambiguous_instruction", "Audit A2: instruction says 21 mm; reference hole is 20.98 mm."),
    "15eccb8909e47128": ("ambiguous_instruction", "Audit A3: reference also deletes the central bore that the instruction says stays; Astra keeps it."),
    "43b8a23fd4235e98": ("ambiguous_instruction", "Audit A3: instruction says cut a slot; the reference removes the existing slot."),
    "9137a0ea501a2de0": ("ambiguous_instruction", "Audit A3: Astra computes 2 x across-flats correctly (26.0); the reference uses 2 x circumscribed diameter (30.0)."),
    "478c058d89cf5ac9": ("ambiguous_instruction", "Audit A3: instruction adds a dome; the reference deletes the existing spherical cut."),
    "76ca895fdaf81169": ("ambiguous_instruction", "Audit A3: polygon radius 9.08 versus CadQuery's diameter convention; the reference uses 9.08 directly."),
    "96c09e186858d9e9": ("ambiguous_instruction", "Audit A3: the reference slot is neither longer nor re-centred as the instruction asks."),
    "b61bd7f12f1b5e94": ("ambiguous_instruction", "Shank is 8.5 mm in Y and 17.3 mm in Z, so its widest flat faces are +-Y, and the original part already drills from >Y. "
                         "Astra drills along Y; the reference drills along Z."),
    "8faf5ad46eb9869e": ("ambiguous_instruction", "Body height raised; Astra keeps the raised face and neck on top, the reference leaves them buried in the taller body."),
    "1bb334960dd15881": ("ambiguous_instruction", "'Throat radius' may be the inner or the outer wall; Astra keeps wall thickness. Three other Astra drafts matched the reference."),
    "3352116bd60064e5": ("ambiguous_instruction", "End profile after removing the top convolution is unspecified. Three other Astra drafts matched the reference."),
    "bc48c07fbbe8a300": ("ambiguous_instruction", "Astra rescales the profile uniformly about the bore (peaks 18.48 mm); the reference changes only the peaks. Both keep count and pitch."),
    "de5dd311e2060f59": ("ambiguous_instruction", "'Replace the rectangular protrusions with semicircular protrusions': Astra builds semicircles, the reference rounded-end arms."),
    "4e9651f30263c884": ("ambiguous_instruction", "The 32.9 mm bore lies inside the 33.4 mm through-cut; removing only the cut (reference) exposes a blind pocket, Astra removes both."),
}

EXCLUDED_OTHER = [
    dict(case_id="CADFEM-v1.5/A-CADWORLD-001", domain="CAD+FEM", cls="task_defect",
         reason="Prompt stated first-order tetrahedra; the publisher model is second-order. Astra's 20.27 mm equals the independent first-order solution.",
         evidence="runs/hosted-v1.5/SPEND.md"),
    dict(case_id="eng-frame/building_edit (20 Sep pilot)", domain="structural drawing + frame FEM", cls="not_reproduced",
         reason="179 MPa versus 20.356 MPa once; 3 of 3 fresh samples correct.", evidence="reports/ENG_FRAME_FAILURE_BOUNDARY_20260922.md"),
    dict(case_id="eng-frame/threebay_edit (14 members)", domain="structural drawing + frame FEM", cls="not_reproduced",
         reason="Declined once; 3 of 3 fresh samples correct.", evidence="runs/eng-frame-aggregate.json"),
    dict(case_id="field-plot/plate_convective_edges", domain="FEM contour drawing", cls="not_reproduced",
         reason="One historical call hit its token limit with no SVG; both reruns returned accurate contours.", evidence="reports/ASTRA_FEM_FAILURE_RECHECK.md"),
]

EXTERNAL = [
    dict(source="StoryGold (LinkedIn posts, Oct 2026, pasted by the user)",
         claims=["30 CAD models run through Astra looked right, but most mechanisms that should move had no articulation: parts interpenetrate or float; "
                 "scissor arms could not pivot; conveyor rollers and belt were fixed.",
                 "Parametric reconstruction in FreeCAD on four private assemblies: 94% geometric similarity / 83% feature-tree quality from STEP, "
                 "86% / 65% from STL."],
         data_released=False, verified_here=False,
         note="No files or protocol published; not reproduced. Same failure class (floating parts) found here in our own BenchCAD references."),
    dict(source="CADEngBench-A (arXiv 2608.09296)", url="https://arxiv.org/html/2608.09296v1", models="eight; Astra not tested",
         claims=["Best end-to-end joint pass 15.8%; correct entity pair found far more often than the correct joint type and frame; pin-slot joints 0%."],
         data_released="not confirmed", verified_here=False),
    dict(source="CAD-bench (ICML 2026)", url="https://icml.cc/virtual/2026/67851", models="Astra not named",
         claims=["Functional assemblies (threaded pairs, gear trains) near zero for standalone runs; agents build the gearbox 96.9% of the time but score 4.0% on function."],
         data_released="not confirmed", verified_here=False),
    dict(source="LMBuild (arXiv 2610.04292)", url="https://arxiv.org/abs/2610.04292", models="30 systems; Astra not named",
         claims=["Functional affordance and physical operability, not appearance, are the bottleneck for frontier models."],
         data_released="not confirmed", verified_here=False),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_cq(code: str):
    ns = {"show_object": lambda *a, **k: None}
    exec(code, ns)
    r = ns["result"]
    return r.val() if hasattr(r, "val") else r


def step_solids(path: Path) -> dict:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.STEPControl import STEPControl_Reader
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    rd = STEPControl_Reader()
    rd.ReadFile(str(path))
    rd.TransferRoots()
    e, solids = TopExp_Explorer(rd.OneShape(), TopAbs_SOLID), []
    while e.More():
        solids.append(e.Current())
        e.Next()
    vols = []
    for s in solids:
        g = GProp_GProps()
        BRepGProp.VolumeProperties_s(s, g)
        vols.append(round(g.Mass(), 2))
    gap = None
    if len(solids) > 1:
        gap = min(BRepExtrema_DistShapeShape(a, b).Value() for i, a in enumerate(solids) for b in solids[i + 1:])
    return dict(solids=len(solids), volumes_mm3=vols, min_gap_between_solids_mm=None if gap is None else round(gap, 4))


def measure(row: dict, patch_text: str) -> dict:
    out = {}
    try:
        ref = run_cq(apply(row["code"], json.loads(row["target"]), row["representation"]))
        out["reference_program"] = dict(solids=len(ref.Solids()), volume_mm3=round(ref.Volume(), 4))
    except Exception as exc:                                     # noqa: BLE001
        out["reference_program"] = dict(error=f"{type(exc).__name__}: {exc}"[:300])
        return out
    try:
        patch = json.loads(patch_text)
    except Exception as exc:                                     # noqa: BLE001
        out["astra"] = dict(status="unparseable_patch", error=f"{type(exc).__name__}: {exc}"[:300])
        return out
    try:
        ast = run_cq(apply(row["code"], patch, row["representation"]))
    except Exception as exc:                                     # noqa: BLE001
        out["astra"] = dict(status="does_not_execute", error=f"{type(exc).__name__}: {exc}"[:300])
        return out
    inter = ref.intersect(ast).Volume()
    out["astra"] = dict(status="executes", solids=len(ast.Solids()), volume_mm3=round(ast.Volume(), 4),
                        iou_vs_reference_program=round(inter / (ref.Volume() + ast.Volume() - inter), 6))
    return out


def cad_cases(ev: Path) -> list[dict]:
    rows = {json.loads(l)["id"][:16]: json.loads(l) for l in TESTS.read_text().splitlines()}
    scored = {json.loads(l)["id"][:16]: json.loads(l) for l in (ASTRA / "scored/astra-predictions-geometry.jsonl").read_text().splitlines()}
    audit = {c["id"]: c for c in json.loads(AUDIT.read_text())}
    assert set(audit) == set(VERDICTS), set(audit) ^ set(VERDICTS)
    steps = {}
    for p in (ROOT / "data").glob("**/*.step"):
        steps.setdefault(p.name, []).append(p)
    recs = []
    for cid, (cls, reason) in sorted(VERDICTS.items(), key=lambda kv: (kv[1][0], kv[0])):
        row, a = rows[cid], audit[cid]
        d = ev / "cad-edit" / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "source.py").write_text(row["code"])
        (d / "instruction.txt").write_text(row["instruction"] + "\n")
        (d / "reference_patch.json").write_text(json.dumps(json.loads(row["target"]), indent=1) + "\n")
        resp = (ASTRA / cid / "response.txt").read_text()
        (d / "astra_response.txt").write_text(resp)
        shutil.copy2(ASTRA / cid / "result.json", d / "astra_result.json")
        ref = next(p for p in steps[Path(row["reference_step"]).name] if sha(p) == row["reference_step_sha256"])
        shutil.copy2(ref, d / "reference.step")
        m = dict(released_reference_step=step_solids(ref), **measure(row, resp))
        rep = REPAIR / cid / "response.txt"
        if rep.is_file():                                        # one execution-feedback round, 2026-10-06
            shutil.copy2(rep, d / "astra_repair_response.txt")
            m["astra_after_one_feedback_round"] = measure(row, rep.read_text()).get("astra")
            if m["astra_after_one_feedback_round"].get("solids", 1) > 1:
                solids = sorted(run_cq(apply(row["code"], json.loads(rep.read_text()), row["representation"])).Solids(), key=lambda x: x.Volume())
                from OCP.BRepExtrema import BRepExtrema_DistShapeShape
                m["astra_after_one_feedback_round"]["min_gap_between_solids_mm"] = round(
                    min(BRepExtrema_DistShapeShape(a.wrapped, b.wrapped).Value() for i, a in enumerate(solids) for b in solids[i + 1:]), 4)
        s = scored.get(cid, {})
        m["original_scorer"] = {k: s.get(k) for k in ("status", "volume_iou", "match_strict", "predicted_solid_count")}
        (d / "measurements.json").write_text(json.dumps(m, indent=1) + "\n")
        recs.append(dict(case_id=f"cad-edit/{cid}", domain="CAD editing (CadQuery patch)", protocol="one-shot JSON line patch, medium effort, 2026-10-04",
                         source="BenchCAD (CC-BY-4.0, huggingface.co/datasets/BenchCAD/BenchCAD)", component=row["component_id"], tier=row["category"],
                         instruction=row["instruction"], cls=cls, reason=reason, audit_category_20261008=a["category"],
                         other_astra_drafts_solved=a["rescued_by_other_astra_draft"], samples="1 vanilla answer (plus graph-search drafts where noted)",
                         measurements=m, evidence=str(d.relative_to(OUT))))
    return recs


def network_case(ev: Path) -> dict:
    d = ev / "network/net-pipe_network-0003371ea274123f_edit-4"
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(VENV), str(ROOT / "scripts/network_paper_astra_failure.py"), "--out", str(d)], check=True, capture_output=True)
    run = ROOT / "runs/network-astra-20260927/net-pipe_network-0003371ea274123f_edit-4"
    shutil.copy2(run / "response.txt", d / "astra_response.txt")
    shutil.copy2(run / "result.json", d / "astra_result.json")
    w = json.loads((d / "astra-failure-worked.json").read_text())
    return dict(case_id="network/net-pipe_network-0003371ea274123f:edit-4", domain="pipe-network drawing edit + hydraulic analysis",
                protocol="SVG edit + analysis, medium effort, 2026-09-27", instruction="Change the length of P9 to 340 m.", cls="astra_failure",
                reason=(f"Edit is exactly the target SVG, but the analysis reports J4 = {w['astra_claim']['min_pressure_head_m']['value']} m and verdict 'pass'. "
                        f"Solving the returned SVG gives J4 = {w['solved_J4_pressure_head_m']:.4f} m < 20 m minimum: the design fails. "
                        f"P4 velocity reported {w['astra_claim']['pipe_velocities_m_s']['P4']} m/s, solved {w['solved_P4_velocity_m_s']:.4f} m/s."),
                failure_type="silent wrong engineering verdict", samples="1 (not re-run; credits ran out)",
                reference="benchmark's own Darcy-Weisbach/Churchill network solver (engsvg_networks.py)", evidence=str(d.relative_to(OUT)))


def frame_cases(ev: Path) -> list[dict]:
    agg = json.loads((ROOT / "runs/eng-frame-aggregate.json").read_text())
    runs = {"EngFrame XL screen": "eng-frame-xl-20260922", "EngFrame XL confirm deg27": "eng-frame-xl-confirm-20260922",
            "EngFrame XL confirm 20-member": "eng-frame-xl-confirm2-20260922"}
    out = []
    for tid, members in (("threebay_three_edit", 21), ("twobay_four_generate", 20)):
        rows = [r for r in agg["rows"] if r["id"] == tid]
        d = ev / "frame" / tid
        for r in rows:
            src = ROOT / "runs" / runs[r["run"]] / tid / r["sample"]
            if src.is_dir():
                dst = d / f"{runs[r['run']]}-{r['sample']}"
                dst.mkdir(parents=True, exist_ok=True)
                for f in src.iterdir():
                    if f.is_file():
                        shutil.copy2(f, dst / f.name)
        n = {k: sum(r["outcome"] == k for r in rows) for k in ("declined", "computed_correct", "computed_wrong", "excluded_api")}
        confirmed = n["declined"] >= 2 and n["declined"] > n["computed_correct"]
        out.append(dict(case_id=f"eng-frame/{tid}", domain="dimensioned structural elevation + frame FEM", members=members,
                        protocol="drawing edit/generation + member-end stress analysis, medium effort, 2026-09-22",
                        cls="astra_failure" if confirmed else "unconfirmed",
                        failure_type="declines the required analysis (returns status 'unavailable' and nulls); no wrong numbers",
                        outcomes=n, samples=sum(n.values()) - n["excluded_api"],
                        reason=(f"Declined {n['declined']} of {n['declined'] + n['computed_correct']} completed samples." if confirmed else
                                f"Declined {n['declined']} of {n['declined'] + n['computed_correct']} completed samples; "
                                f"{n['excluded_api']} confirmation samples lost to API errors."),
                        evidence=str(d.relative_to(OUT)), report="reports/ENG_FRAME_FAILURE_BOUNDARY_20260922.md"))
    return out


def xxl_frame_cases(ev: Path) -> list[dict]:
    """Larger frames built 2026-10-15 (scripts/astra_traps/frames_xxl.py), same prompt and protocol, 16k-token cap."""
    out = []
    plan = [("astra-frames-xxl-20261015", "fivebay_five_generate", "data/eng-frame-bench-xxl"),
            ("astra-frames-xxl-20261015-b", "fourbay_four_generate", "data/eng-frame-bench-xxl")]
    plan += [(f"astra-frames10-20261015/{r['id']}", r["id"], "data/eng-frame-bench-xxl" if r["id"] in
              ("fourbay_four_edit", "threebay_six_generate", "threebay_six_edit", "fivebay_five_edit") else "data/eng-frame-bench-xxl2")
             for r in json.loads((ROOT / "runs/astra-frames10-20261015/summary.json").read_text())["rows"]]
    for run, tid, data in plan:
        src = ROOT / "runs" / run / tid / "sample-0"
        if not src.is_dir():
            continue
        r = json.loads((src / "response.json").read_text())
        txt = r["choices"][0]["message"]["content"]
        sys.path.insert(0, str(ROOT / "scripts/astra_traps"))
        from run_frames10 import analysis
        an = analysis(txt) or {}
        declined = str(an.get("status", "")).lower() == "unavailable" or (an.get("uy_mm") is None and an.get("peak_stress_mpa") is None)
        task = next(t for t in json.loads((ROOT / data / "tasks.json").read_text())["tasks"] if t["id"] == tid)
        d = ev / "frame-xxl" / tid
        d.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            shutil.copy2(f, d / f.name)
        out.append(dict(case_id=f"eng-frame-xxl/{tid}", domain="dimensioned structural elevation + frame FEM", members=task["members"],
                        indeterminacy=task["indeterminacy"], protocol="drawing generation + member-end stress analysis, medium effort, no tools, 16k cap, 2026-10-15",
                        cls="astra_failure" if declined else "unconfirmed", failure_type="declines the required analysis (status 'unavailable', nulls)",
                        samples=1, reason=f"Declined 1 of 1 sample ({task['members']} members, indeterminacy {task['indeterminacy']}); the drawing itself is complete.",
                        evidence=str(d.relative_to(OUT)), task_source=data))
    return out


def readme(cases: list, excluded: list) -> str:
    cad = [c for c in cases + excluded if c["case_id"].startswith("cad-edit/")]
    by = {k: sum(c["cls"] == k for c in cad) for k in ("astra_failure", "reference_defect", "task_defect", "ambiguous_instruction")}
    lines = [f"# Astra failure cases v{VERSION}", "",
             "Every recorded GPT-6 Astra miss in this repository, re-checked. A miss is admitted only when Astra's own answer is wrong "
             "or unusable. It is excluded when our reference or task is at fault, or when it did not reproduce. Built by "
             "`scripts/build_astra_failure_cases.py` from saved runs; no model calls. Measurements are recomputed by the build.", "",
             "## Admitted Astra failures", "", "| Case | Domain | Failure | Evidence strength |", "|---|---|---|---|"]
    for c in cases:
        if c["cls"] == "astra_failure":
            lines.append(f"| `{c['case_id']}` | {c['domain']} | {c['reason']} | {c['samples']} |")
    lines += ["", "## Unconfirmed", ""]
    lines += [f"- `{c['case_id']}`: {c['reason']}" for c in cases if c["cls"] == "unconfirmed"]
    lines += ["", f"## The 35 audited CAD-edit misses (2026-10-08 audit, re-checked here)", "",
              f"- Astra failures: {by['astra_failure']} (no usable solid on the first answer: code that does not run, a kernel-rejected chamfer, "
              "truncated JSON; the propeller's repaired answer also leaves its boss floating)",
              f"- Our reference defects: {by['reference_defect']} (released STEP differs from its program; added features floating free of the part; "
              "wrong datum; irregular chamfer; holes moved by the reference edit)",
              f"- Impossible tasks: {by['task_defect']}",
              f"- Ambiguous instructions: {by['ambiguous_instruction']}", "",
              "In several excluded cases Astra's answer is the physically correct one: it keeps features attached where the reference "
              "leaves them floating, measures from the stated face, and keeps holes where the instruction says they stay. "
              "The connecting-rod holes and twisted-bracket plates previously listed as Astra failures "
              "(output/audits/astra-failure-search-20261015) are reclassified: ambiguous and reference defect respectively.", "",
              "## Other excluded records", ""]
    lines += [f"- `{c['case_id']}` ({c['cls']}): {c['reason']}" for c in excluded if not c["case_id"].startswith("cad-edit/")]
    lines += ["", "CADFEM-Bench v1.5 hosted run (medium effort, $9.98): 7 of 7 valid tasks pass; no failures to admit.", "",
              "## External reports (not verified here)", ""]
    for e in EXTERNAL:
        lines.append(f"- **{e['source']}**: " + " ".join(e["claims"]) + (f" Note: {e['note']}" if e.get("note") else ""))
    lines += ["", "## Limits", "",
              "- Admitted failures are single-sample or few-sample observations at medium effort; they are not failure rates. "
              "Earlier single-sample Astra misses in this repository mostly did not reproduce.",
              "- The CAD-edit protocol is one-shot line patching without execution feedback. One execution-feedback round "
              "(runs/multisource-cad-astra-repair-20261006) made 16 of 32 failed answers valid and 1 a strict match.",
              "- Only 35 of the 146 strict CAD-edit misses were audited; the rest are not classified here.",
              "- BenchCAD material is CC-BY-4.0 (attribution required). Network and frame tasks are this project's own. "
              "Local research package; check the external sources before redistribution.", "",
              "Files: `cases.jsonl` (admitted and unconfirmed), `excluded.jsonl`, `external-reports.json`, `evidence/`, `SHA256SUMS`."]
    return "\n".join(lines) + "\n"


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    ev = OUT / "evidence"
    ev.mkdir(parents=True)
    cad = cad_cases(ev)
    cases = [c for c in cad if c["cls"] == "astra_failure"] + [network_case(ev)] + frame_cases(ev) + xxl_frame_cases(ev)
    excluded = [c for c in cad if c["cls"] != "astra_failure"] + [dict(c) for c in EXCLUDED_OTHER]
    (OUT / "cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    (OUT / "excluded.jsonl").write_text("".join(json.dumps(c) + "\n" for c in excluded))
    (OUT / "external-reports.json").write_text(json.dumps(EXTERNAL, indent=1) + "\n")
    (OUT / "README.md").write_text(readme(cases, excluded))
    shutil.copy2(Path(__file__), OUT / Path(__file__).name)
    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    (OUT / "SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(OUT)}\n" for p in files))
    with zipfile.ZipFile(OUT.parent / f"{OUT.name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, Path(OUT.name) / p.relative_to(OUT))
    print(json.dumps(dict(admitted=sum(c["cls"] == "astra_failure" for c in cases), unconfirmed=sum(c["cls"] == "unconfirmed" for c in cases),
                          excluded=len(excluded), out=str(OUT)), indent=1))


if __name__ == "__main__":
    main()
