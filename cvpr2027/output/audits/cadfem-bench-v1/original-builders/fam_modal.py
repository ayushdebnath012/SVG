"""Track A, gold modal tasks.

Morphing-wing cantilever plates (Huang & Zhang, Mendeley 8jxw5533py, CC BY 4.0): uniform and stepped PLA plates.
The STEP includes a 19 mm clamping grip (x = 0-19 mm, clamp scallops at x = 9.5 mm); the source FE models cover only
the free length from the clamp line (90/125/250 mm in the Abaqus decks, 150/250/300 mm in the Nastran decks, all
equal to the STEP length minus 19 mm) with ENCASTRE / SPC 123456 at the clamp line. References: Abaqus thick-shell
(S8R) results for Tests 1-3 and Nastran plate-plate (PP) results for Tests 5-9, from the publisher workbook. Test 4
is excluded (its STEP name fef50% conflicts with the result block f75%).

DeepWheel (KAIST SmartDesignLab, CC BY-NC 4.0): free-free modal analysis of generated automotive wheels in A356-T6.
References: Mode 7 (first elastic) and Mode 11 frequencies from the publisher CSV. CAD mass at the publisher
density is 3.25 % below the CSV mass (about 1.6 % in frequency); stated, not corrected.
"""
from __future__ import annotations

import json
import re

import common as C

MORPH = C.DATA / "web-cad-fem-aerospace/morphing-modal"
P100 = C.ROOT / "output/datasets/published-cad-fem-100/manifest.json"
WHEEL = C.DATA / "web-cad-fem-more-families/deepwheel"
MORPH_SRC = dict(name="Experimental and numerical data of candidate structural models for active camber morphing wings (Huang & Zhang)",
                 url="https://data.mendeley.com/datasets/8jxw5533py/1", license="CC BY 4.0", redistributable=True)
WHEEL_SRC = dict(name="DeepWheel synthetic wheel dataset (Yoo & Kang, KAIST SmartDesignLab / Narnia Labs)",
                 url="https://huggingface.co/datasets/KAIST-SmartDesignLab/DeepWheel", license="CC BY-NC 4.0",
                 redistributable=True)
TESTS = {1: ("Test1 AR1.8.STEP", "ABAQUS inp Files/AR1d8_SHEARSHELL.inp"), 2: ("Test2 AR2.5.STEP", "ABAQUS inp Files/AR2d5_SHEARSHELL.inp"),
         3: ("Test3 AR5.0.STEP", "ABAQUS inp Files/AR5_SHEARSHELL.inp"), 5: ("Test5 AR5.0_fef50%.STEP", "Nastran bdf Files/AR5fef0d5PPModel.bdf"),
         6: ("Test6 AR5.0_fef25%.STEP", "Nastran bdf Files/AR5fef0d25PPModel.bdf"), 7: ("Test7 AR6.0_fef50%.STEP", "Nastran bdf Files/AR6fef0d5PPModel.bdf"),
         8: ("Test8 AR4.0_fef50%.STEP", "Nastran bdf Files/AR4fef0d5PPModel.bdf"), 9: ("Test9 AR3.0_fef50%.STEP", "Nastran bdf Files/AR3fef0d5PPModel.bdf")}
MODES = {"1-B": ("f_1B_Hz", "first out-of-plane bending mode"), "1-T": ("f_1T_Hz", "first torsion mode about the span (x) axis"),
         "2-B": ("f_2B_Hz", "second out-of-plane bending mode")}


def _material(deck: str) -> tuple[float, float]:
    t = (MORPH / deck).read_text(errors="replace")
    if deck.endswith(".inp"):
        e, nu = re.search(r"\*Elastic\n\s*([\d.]+),\s*([\d.]+)", t).groups()
        return float(e), float(nu)
    m = re.search(r"MAT1\*\s+1\s+([\d.+-]+)\s+([\d.+-]+)\s+([\d.]+)", t)
    return float(m.group(1).replace("+", "e+")) / 1e6, float(m.group(3))


def _free_length(deck: str) -> float:
    """Span of the source FE model from the clamp line to the tip, in mm."""
    t = (MORPH / deck).read_text(errors="replace")
    if deck.endswith(".inp"):
        block = re.search(r"\*Node\n(.*?)\n\*", t, re.S).group(1)
        x = [float(l.split(",")[1]) for l in block.splitlines()]
        return max(x) - min(x)
    num = lambda s: float(re.sub(r"^([+-]?[\d.]+)([+-]\d+)$", r"\1e\2", s.strip()) or 0)
    y = [num(l[32:40]) for l in t.splitlines() if l.startswith("GRID ") ]
    return (max(y) - min(y)) * 1e3


def morphing() -> list:
    cases = {c["case_id"]: c for c in json.loads(P100.read_text())["cases"]}
    rows = []
    for n, (stp, deck) in TESTS.items():
        c = cases[f"WING-Test{n}"]
        tid = f"A-MORPHWING-Test{n}"
        shape = C.read_shape(MORPH / "FDM Stp Files" / stp)
        summ = C.shape_summary(shape)
        length = summ["bbox_mm"][3]
        e, nu = _material(deck)
        assert abs(_free_length(deck) - (length - 19.0)) < 1e-6, (tid, _free_length(deck), length)
        stepped = "fef" in stp
        inputs = [C.put(tid, MORPH / "FDM Stp Files" / stp, "part.step")]
        geo = ("a uniform 4 mm plate" if not stepped else
               "a 4 mm plate with a 1 mm-thick flexible strip (mid-plane z = 2 mm) along part of its width, the stepped "
               "plate used for active camber morphing")
        prompt = f"""Cantilever plate specimen for an active-camber morphing-wing study (FDM-printed PLA): {geo}. part.step is one solid in millimetres, {length:g} x {summ['bbox_mm'][4]:g} x {summ['bbox_mm'][5]:g} mm, with a 19 mm clamping grip at x = 0-19 mm (the scalloped clamp region).
Model the vibrating structure only: the free part x >= 19 mm, clamped (all displacements and rotations zero) along its whole cross-section at x = 19 mm. The grip is held in the fixture and is not part of the model.
Material: PLA treated as isotropic linear elastic, E = {e:g} MPa, Poisson ratio {nu:g}, density 1180 kg/m^3.
Analysis: undamped natural frequencies (modal analysis), no prestress, no gravity. Identify the modes by their shapes."""
        outs, refs = [], {}
        for lab, (key, definition) in MODES.items():
            v = c["reference_values"][lab]
            outs.append(C.out(key, "Hz", definition))
            refs[key] = C.refv(v["value"], "frequency", "published_table",
                               f"'1-1 Modal Test Experiment and Numerical Results.xlsx' cell {v['cell']} "
                               f"({'Abaqus thick shell S8R' if deck.endswith('.inp') else 'Nastran plate-plate model'})")
        rows.append(C.task(tid, "A", "gold", "morphing-wing-plates", f"Morphing-wing cantilever plate, Test {n}", ["modal"],
                           prompt, inputs, outs, MORPH_SRC,
                           dict(solids=1, faces=summ["faces"], assembly=False, cad_bbox_mm=summ["bbox_mm"]), refs,
                           flags=["reference is a shell-model solution of the free length; solid models converge to it within about 1-2 %"]))
    return rows


def deepwheel() -> list:
    cat = json.loads((WHEEL / "catalog.json").read_text())
    rows = []
    for r in cat["records"]:
        tid = f"A-DEEPWHEEL-{r['id'].split('_c1')[0]}"
        g, ph = r["cad_geometry"], r["physics"]
        inputs = [C.put(tid, WHEEL / r["cad"], "wheel.step")]
        prompt = f"""Automotive cast-aluminium wheel (generated design from the DeepWheel dataset). wheel.step is one solid in millimetres ({g['faces']} faces, about {g['volume_mm3'] / 1e6:.2f} litres of material).
Material: A356-T6 aluminium, isotropic linear elastic, E = 72 GPa, Poisson ratio 0.33, density 2680 kg/m^3 (publisher values).
Analysis: free-free modal analysis (no supports, no prestress). Number the modes by ascending frequency, counting the six rigid-body modes as modes 1-6. The publisher solved it with OptiStruct on 10-node tetrahedra of about 6 mm."""
        outs = [C.out("f_mode7_Hz", "Hz", "frequency of mode 7, the first elastic mode"),
                C.out("f_mode11_Hz", "Hz", "frequency of mode 11 (fifth elastic mode)")]
        prov = f"publisher deepwheel_sim_results.csv row {r['id']}"
        refs = dict(f_mode7_Hz=C.refv(r["reference"]["mode_7_frequency_Hz"], "frequency", "published_table", prov),
                    f_mode11_Hz=C.refv(r["reference"]["mode_11_frequency_Hz"], "frequency", "published_table", prov))
        rows.append(C.task(tid, "A", "gold", "deepwheel-modal", f"DeepWheel wheel {r['id'].split('_c1')[0]}: free-free modes", ["modal"],
                           prompt, inputs, outs, WHEEL_SRC,
                           dict(solids=g["solids"], faces=g["faces"], assembly=False), refs,
                           flags=["CAD mass at 2680 kg/m^3 is 3.25 % below the publisher CSV mass (about 1.6 % in frequency)",
                                  "noncommercial license (CC BY-NC 4.0)"]))
    return rows


def build() -> list:
    # DeepWheel is not admitted: CAD mass at the publisher density is 3.25 % below the publisher CSV mass and the
    # density behind the published frequencies cannot be determined (see registry `deepwheel`).
    return morphing()
