"""Fetch the five user-selected COMSOL studies and their original reference drawings.

These are source-study additions to the PDF, not validated tasks.jsonl benchmarks.
No CAD, FEM solution, tolerance, or numerical reference is generated here.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/femcad-hard-v1"
CACHE = ROOT / "tmp/femcad-comsol-sources"
BASE = "https://doc.comsol.com/"


def source(version, module, model):
    return f"{BASE}{version}/doc/com.comsol.help.models.{module}.{model}/{model}.html"


def figure(model, number, caption, kind="cad", digits=2, url=None):
    return dict(filename=f"{model}.1.1.{number:0{digits}d}.png", caption=caption, kind=kind, source_url=url)


ROWS = [
    dict(id="FEMCAD-ADV-001", title="Rubber boot seal with frictional self-contact", category="Solid Mechanics",
         model_kind="3-D assembly; half-domain symmetry", source_url=source("6.3", "nsm", "rubber_boot_seal"),
         geometry="Five decreasing-radius convolutions join a rubber boot to a rigid pipe. Original CAD view below; the source appendix gives the construction dimensions and operations. A 1 mm interference establishes the shrink fit.",
         analysis="Nearly incompressible Yeoh rubber: c1 = 100 kPa, c2 = 6 kPa, c3 = -30 Pa. First mount the seal; then incrementally rotate the pipe 40 degrees about y, with the boot base fixed. Pipe/rubber friction = 0.7; rubber/rubber self-contact friction = 0.8. The source uses Nitsche contact.",
         outputs="Deformed geometry, stress distribution and active contact surfaces through the rotation sequence (source Figures 2-4).",
         reference="Published fields and deformation sequence; no numerical scalar grading reference or tolerance extracted. No new FEM run.",
         notes="Difficulty assessment: complex thin geometry, finite strain, near incompressibility, interference and changing frictional self-contact.",
         figures=[figure("rubber_boot_seal", 1, "Source Figure 1: undeformed boot seal and rigid pipe", digits=3)]),
    dict(id="FEMCAD-ADV-002", title="Layered piezoelectric valve and hyperelastic seal", category="Multiphysics",
         model_kind="2-D axisymmetric analysis; 3-D assembly reference", source_url=source("6.3", "mems", "piezoelectric_valve"),
         geometry="Annular bimorph actuator, alternating PZT/electrode layers, rubber seal and stainless-steel support. Figure 1 labels the components; Figure 2 resolves the actuator stack. Follow the source geometry sequence for dimensions.",
         analysis="Couple electric potential and piezoelectric deformation to nonlinear seal contact. Alternate electrodes are grounded or driven; adjacent PZT layers have opposite polarization. The outer actuator rim is clamped. Voltage bends the actuator and presses the seal onto the annular opening.",
         outputs="Seal strain, actuator stress, electric potential and contact-pressure distribution (source Figures 3-6).",
         reference="The narrative reports maximum contact pressure 6e5 Pa. Its results text discusses 60 V while Figure 4 says 50 V; the operating point needs reconciliation before this value can be used for grading.",
         notes="Difficulty assessment: thin multilayer geometry, coupled electromechanics and nonlinear contact. This source solves an axisymmetric model, not full 3-D fluid shutoff.",
         figures=[figure("piezoelectric_valve", 1, "Source Figure 1 (top): labeled axisymmetric section", "drawing"),
                  figure("piezoelectric_valve", 2, "Source Figure 1 (bottom): full 3-D valve geometry"),
                  figure("piezoelectric_valve", 3, "Source Figure 2: actuator layers and seal detail", "drawing")]),
    dict(id="FEMCAD-ADV-003", title="Internally cooled turbine stator blade: thermal stress and creep", category="Multiphysics",
         model_kind="3-D solid; sequential thermal/structural analysis", source_url=source("6.3", "nsm", "turbine_stator_creep"),
         geometry_source=source("6.3", "sme", "turbine_stator"),
         geometry="Stator airfoil, mounting platforms and an internal cooling duct. The base study imports turbine_stator.mphbin; these CAD views are not a complete dimensioned drawing. Reference CAD is needed for exact reconstruction.",
         analysis="Start with the linked base study: GTD111 DS alloy, temperature-dependent properties, gas at 1150 K, coolant at 650 K and roller/spring supports. Then hold the solved temperature field constant for 400 h and evolve isotropic secondary Norton creep: A = 2.5e-23 /h, n = 6.75, reference stress 1 MPa, activation energy 350 kJ/mol, activation reference temperature 900 K.",
         outputs="Temperature, displacement, stress relaxation and creep-strain fields over operating time, as displayed by the source studies.",
         reference="Published solution fields; no numerical scalar grading reference or tolerance extracted. The tutorial assumes isotropic creep despite the directionally solidified alloy.",
         notes="Difficulty assessment: complex internal CAD, temperature-dependent properties and nonlinear time evolution.",
         figures=[figure("turbine_stator_creep", 1, "Creep study Figure 1: blade and mounting details"),
                  figure("turbine_stator", 2, "Base study Figure 2: internal cooling duct", url=source("6.3", "sme", "turbine_stator"))]),
    dict(id="FEMCAD-ADV-004", title="Compound gear train: tooth contact and housing vibration", category="Solid Mechanics",
         model_kind="2-D contact FEM + 3-D multibody/elastic housing", source_url=source("6.4", "mbd", "gear_train"),
         geometry="Two spur-gear pairs, three shafts and an elastic housing. Each pinion/wheel has 20/30 teeth, 50/75 mm pitch diameter, 25-degree pressure angle and 10 mm width. Source geometry parameters and imported housing define the assembly.",
         analysis="First compute gear-mesh stiffness by rotating a contacting 2-D steel gear pair through mesh cycles with 0.5-degree twist. Use that varying stiffness in the transient assembly: input speed 600 rad/s, output torque 100 N m. Shafts/gears are rigid in this second stage; the housing is elastic.",
         outputs="Mesh stiffness versus angle; tooth stresses; gear contact forces; shaft motion; housing acceleration and frequency content.",
         reference="The source reports dominant housing frequencies near 550 and 2000 Hz. These are approximate spectral observations, not mesh-converged scalar grading references.",
         notes="Difficulty assessment: involute geometry, changing tooth contact and sequential contact/dynamics analysis; not full flexible-body 3-D tooth contact.",
         figures=[figure("gear_train", 1, "Source Figure 1: compound gear train and housing"),
                  figure("gear_train", 2, "Source Figure 2: gear-pair section for stiffness analysis", "drawing"),
                  figure("gear_train", 7, "Source Figure 4: gear-pair mesh", "part-mesh")]),
    dict(id="FEMCAD-ADV-005", title="Hybrid muffler with perforated pipes and four baffles", category="Acoustics",
         model_kind="3-D acoustic domain; upper-half symmetry", source_url=source("6.3", "aco", "perforated_muffler"),
         geometry="Multi-chamber muffler with outlet pipe and four baffles. Figures 1-5 supply the cross-section and dimensioned engineering drawings. Preserve the outlined perforated regions used by the source model.",
         analysis="Frequency-domain pressure acoustics, 20-600 Hz, air at 20 degC and 1 atm; rigid walls and symmetry at z = 0. Ports define excitation and transmission. Perforates use interior impedance boundaries: plate thickness 1.5 mm, hole diameter 5 mm, pipe porosity 0.22 and inlet/outlet baffle porosity 0.46/0.30; include the source sleeve resistance.",
         outputs="Transmission loss versus frequency and sound-pressure fields; comparison with the measured curve in source Figure 7.",
         reference="Published FEM/experimental curves; no digitized scalar grading references or tolerances. The source notes disagreement at 170-300 Hz.",
         notes="Difficulty assessment: complex chambers and interface conditions. Individual holes are represented by impedance regions in the FEM analysis.",
         figures=[figure("perforated_muffler", 1, "Source Figure 1: muffler cross-section", "drawing"),
                  figure("perforated_muffler", 2, "Source Figure 2: dimensioned outlet pipe", "drawing"),
                  figure("perforated_muffler", 3, "Source Figure 3: dimensioned baffle 1", "drawing"),
                  figure("perforated_muffler", 4, "Source Figure 4: dimensioned baffles 2 and 3", "drawing"),
                  figure("perforated_muffler", 5, "Source Figure 5: dimensioned baffle 4", "drawing")]),
]


def fetch(url):
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    return r.content


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    urls = sorted({u for r in ROWS for u in (r["source_url"], r.get("geometry_source")) if u})
    manifests = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for url, content in zip(urls, pool.map(fetch, urls)):
            filename = url.split("/")[-1]
            local = CACHE / filename
            local.write_bytes(content)
            manifests.append(dict(url=url, local=str(local.relative_to(ROOT)),
                                  sha256=hashlib.sha256(content).hexdigest()))
    jobs = []
    for row in ROWS:
        for f in row["figures"]:
            f["url"] = urljoin(f.pop("source_url") or row["source_url"], "images/" + f.pop("filename"))
            jobs.append(f)
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f, content in zip(jobs, pool.map(fetch, [f["url"] for f in jobs])):
            local = CACHE / f["url"].split("/")[-1]
            local.write_bytes(content)
            with Image.open(local) as im:
                im.verify()
            f["local"] = str(local.relative_to(ROOT))
            f["sha256"] = hashlib.sha256(content).hexdigest()
    result = dict(status="source studies; not validated grading tasks", fetched_utc=datetime.now(timezone.utc).isoformat(),
                  difficulty="super hard: editorial assessment, not a measured tier", pages=manifests, studies=ROWS)
    (DATA / "advanced-source-studies.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Fetched {len(urls)} source pages and {len(jobs)} original geometry figures for {len(ROWS)} studies.")


if __name__ == "__main__":
    main()
