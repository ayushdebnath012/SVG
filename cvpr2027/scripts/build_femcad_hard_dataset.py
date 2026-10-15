"""FEMCAD-Hard v1: CAD + FEM tasks built only from scraped Wolfram FEM documentation and mfem.org.

Every task asks a model to (1) build an FEM-ready CAD model in CadQuery (part.step, millimetres) and (2) run the
finite-element analysis that the source page sets up, on its own model, writing results.json. Geometry and physics come
from the scraped pages (scripts/scrape_wolfram_fem.py, scripts/scrape_mfem_site.py; provenance manifests in
data/femcad-hard-v1/). Tasks use the eleven categories of https://www.wolfram.com/language/core-areas/fem/. Prompts are
self-contained: any value the scraped code does not contain is set here and listed in provenance_notes.

Reference values are closed forms evaluated here or values stated on the source page (nothing is solved here). Only tasks
with a reference value for every output and a CAD render or meshed-part render of their part on the crawled pages
(figure-curation.json) are written.

  python scripts/build_femcad_hard_dataset.py   -> data/femcad-hard-v1/{tasks.jsonl, README.md}
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/femcad-hard-v1"
CATEGORIES = ["Geometric Modeling", "Mesh Generation", "Heat Transfer", "Fluid Dynamics", "Mass Transport", "Solid Mechanics",
              "Acoustics", "Electromagnetics", "Multiphysics", "System Physics", "Seamless Workflow"]
EPS0 = 8.8541878128e-12
WREF = "https://reference.wolfram.com/language/"
PDE = WREF + "PDEModels/tutorial/"
OCL = WREF + "OpenCascadeLink/tutorial/"

# The source pages of these tasks build the CAD only (OpenCascadeLink tutorials, an MFEM Gmsh tutorial); their analysis is set
# here. Every other task's FEM problem is the one its source page solves.
ANALYSIS_SET_HERE = {1, 2, 3, 4, 5, 6, 44}

PREAMBLE = (
    "CAD + FEM task. Deliver (1) part.py, a CadQuery script that writes part.step in millimetres in exactly the coordinate "
    "frame given (multi-region models: one STEP with one solid per region and shared, coincident interface faces; 2-D models: "
    "planar faces in the z = 0 plane), and (2) fem.py, a finite-element analysis of YOUR model with any open-source FEM "
    "library, set up exactly as under Analysis, that writes results.json with the listed keys and units. Report "
    "mesh-converged values (each changes by less than 1 % under refinement). The grader compares your geometry with the "
    "reference model and your results with the reference analysis.\n\n")


def manifests() -> dict:
    out = {}
    for name in ("wolfram-sources.json", "mfem-sources.json"):
        p = OUT / name
        if p.exists():
            for page in json.loads(p.read_text())["pages"]:
                out[page["url"].rstrip("/").replace("http://", "https://")] = page
    return out


MAN = manifests()


def task(i, category, tier, title, site, page, url, geometry, analysis, outputs, why, ref=None, page_ref=None, example_ref=None,
         tol=None, notes=(), kind="3-D solid", geo=None):
    """ref: closed-form values computed here; page_ref: values stated on the source page; example_ref: values printed by the
    MFEM example itself, run as shipped (MFEM 4.10 release); geo: (title, url) of the page that builds the part when the
    analysis comes from another page of the same site."""
    assert category in CATEGORIES
    tol = tol or {"hard": 0.02, "complex": 0.03, "hardest": 0.05}[tier]
    m = MAN.get(url.rstrip("/").replace("http://", "https://"), {})
    ref, page_ref, example_ref = ref or {}, page_ref or {}, example_ref or {}
    qois = []
    for k, u, d in outputs:
        value, src = next(((v[k], name) for name, v in (("closed form", ref), ("source page", page_ref), ("MFEM example output", example_ref))
                           if k in v), (None, None))
        qois.append(dict(key=k, unit=u, definition=d, reference=value, reference_source=src, rel_tol=tol))
    sources = {q["reference_source"] for q in qois}
    status = ("pending" if None in sources else "exact" if sources == {"closed form"} else
              "example" if "MFEM example output" in sources else "page")
    source = dict(site=site, page=page, url=url, scraped_sha256=m.get("sha256"), fetched_utc=m.get("fetched_utc"))
    if geo:
        g = MAN.get(geo[1].rstrip("/").replace("http://", "https://"), {})
        source["geometry_page"] = dict(page=geo[0], url=geo[1], scraped_sha256=g.get("sha256"), fetched_utc=g.get("fetched_utc"))
    return dict(
        id=f"FEMCAD-{i:03d}", category=category, tier=tier, title=title, model_kind=kind, source=source,
        analysis_source="set here (the source page builds the CAD only)" if i in ANALYSIS_SET_HERE else "source page",
        prompt=PREAMBLE + "Geometry. " + geometry + "\n\nAnalysis. " + analysis + "\n\nOutputs (results.json): "
        + "; ".join(f"{k} [{u}]: {d}" for k, u, d in outputs) + ".",
        qois=qois,
        reference=dict(status=status, method={
            "exact": "closed form for the stated problem, computed in build_femcad_hard_dataset.py",
            "page": "values stated on the source page (its own FEM or benchmark value)",
            "example": "values printed by the MFEM example itself, run as shipped with its default settings (MFEM 4.10 "
                       "release); nothing else is computed",
            "pending": "no reference value on the source pages; not computed"}[status]),
        geometry_check=dict(status="pending: reference CAD from the source construction",
                            rule="volume within 0.5 %, bounding box within 0.2 % of its diagonal, same region count"),
        targets_failure_modes=why, provenance_notes=list(notes), pilot=dict(status="not run", models={}))


def r3(v):
    return [round(float(x), 4) for x in v]


# --------------------------------------------------------------------------------- derived geometry (from page code)
def disc_brake_holes():
    """Disc Brake tutorial: 5 vent holes per sector on the chord between the rotated rectangle corners."""
    th = math.radians(-4.55)
    rot = lambda y, z: (y * math.cos(th) - z * math.sin(th), y * math.sin(th) + z * math.cos(th))  # noqa: E731
    p1, p3 = np.array(rot(0, 88)), np.array(rot(-30, 126))
    return [r3(p1 + k / 4 * (p3 - p1)) for k in range(5)]


def anemometer():
    a = math.atan(math.sqrt(2))
    l1 = 60 / math.sin(a) * math.sin(math.pi / 2 - a)
    pts = dict(p2=(240, 0), p5=(240 + l1, 60), p6=(960 - l1, 60), p3=(960, 0), p4=(1200, 0), p12=(1200, 80), p9=(0, 80))
    return {k: r3(v) for k, v in pts.items()}


def dew_condenser():
    th, lo, hc, hi = math.radians(30), 1.5, 0.00253, 0.02277
    cx = lo - 0.5 * math.cos(th) - (hi + hc / 2) * math.sin(th)
    cz = 0.5 * math.sin(th)
    tf = lambda p: (cx + p[0] * math.cos(th) - p[1] * math.sin(th), cz + p[0] * math.sin(th) + p[1] * math.cos(th))  # noqa: E731
    cond = [tf(p) for p in [(-0.5, -hc / 2), (-0.5, hc / 2), (0.5, hc / 2), (0.5, -hc / 2)]]
    ins = [tf(p) for p in [(-0.5, -hc / 2 - hi), (-0.5, -hc / 2), (0.5, -hc / 2), (0.5, -hc / 2 - hi)]]
    vs = (ins[3][0], ins[3][1] - 0.75)
    mm = lambda p: r3(np.array(p) * 1000)  # noqa: E731
    return dict(condenser=[mm(p) for p in cond], insulation=[mm(p) for p in ins], support=[mm(ins[3]), mm(ins[0]), mm(vs)])


# ------------------------------------------------------------------------------------------------- exact references
def spherical_capacitor():
    r1, r2, er = 0.003, 0.010, 3.9
    return {"capacitance_pF": round(4 * math.pi * EPS0 * er * r1 * r2 / (r2 - r1) * 1e12, 5)}


def bathyscaphe():
    """Hollow titanium sphere a = 80 mm, b = 100 mm under external pressure 1e5 Pa: Lame solution u = C1 r + C2 / r^2."""
    E, nu, a, b, p = 116e9, 0.32, 0.08, 0.1, 1e5
    al, be = E / (1 - 2 * nu), 2 * E / (1 + nu)
    C2 = p / (be * (1 / b ** 3 - 1 / a ** 3))
    C1 = be * C2 / (al * a ** 3)
    u = lambda r: C1 * r + C2 / r ** 2  # noqa: E731
    return {"u_outer_nm": round(u(b) * 1e9, 4), "u_inner_nm": round(u(a) * 1e9, 4),
            "max_von_mises_MPa": round(1.5 * p * b ** 3 / (b ** 3 - a ** 3) * 1e-6, 6)}


def thick_pipe():
    """Plane-strain Lame pipe a = 5, b = 15, internal pressure 20, E = 30e3, nu = 0.3 (the page's consistent units)."""
    E, nu, a, b, p = 30e3, 0.3, 5.0, 15.0, 20.0
    A, B = p * a * a / (b * b - a * a), p * a * a * b * b / (b * b - a * a)
    u = lambda r: (1 + nu) / E * ((1 - 2 * nu) * A * r + B / r)  # noqa: E731
    return {"u_inner": round(u(a), 8), "u_outer": round(u(b), 8), "max_hoop_stress": round(A + B / (a * a), 6)}


# ----------------------------------------------------------------------------------------------------------- tasks
def tasks():
    T = []
    add = T.append
    holes = disc_brake_holes()
    brake_geo = (
        "Wolfram's Disc Brake tutorial rotor, rotation axis = x. (1) Revolve 360 deg about the x-axis the cross-section "
        "polygon (x, y) = (0,144), (25,144), (25,80.5), (10,80.5), (10,74.125), (46.33,74.125), (46.33,34), (39.13,34), "
        "(39.13,67.5), (1,67.5), (1,80.5), (0,80.5). (2) Five lug holes: a cylinder of diameter 15.3 along x from x = 39.13 "
        "to 46.33 centred at (y, z) = (0, 56), united with the boxes [46.33, 60] x [-10, 10] x [45, 66] and "
        "[31.33, 39.13] x [-10, 10] x [45, 66], patterned 5 times about x (k x 72 deg) and subtracted. (3) Twenty pockets: "
        "the rectangle x in [7.5, 17.5], radial distance in [132, 154], revolved +/-7.5 deg about x, patterned 20 times "
        "(k x 18 deg) and subtracted. (4) A torus about the x-axis centred at x = 12.5, major radius 146.5, minor radius 6, "
        "subtracted. (5) 100 axial vent holes of diameter 6 running along x from x = -10 to 35, five per sector at (y, z) = "
        + ", ".join(f"({p[0]}, {p[1]})" for p in holes) + ", patterned 20 times about x (k x 18 deg), subtracted.")
    brake_notes = ["The tutorial's small chamfers and fillets are applied by OpenCascade edge index and are omitted.",
                   "Vent holes: the tutorial places them on an arc of radius 21,675 mm through the rotated rectangle corners; "
                   "it deviates < 0.01 mm from the straight chord used here."]
    add(task(1, "Geometric Modeling", "hardest", "Disc brake rotor (full Wolfram construction), free-free modes", "wolfram",
        "Disc Brake (OpenCascadeLink)", OCL + "DiscBrake.html", brake_geo,
        "Grey cast iron from Wolfram's disc-brake thermal model: E = 99.97 GPa, Poisson ratio 0.29, density 7100 kg/m^3. "
        "Free-free modal analysis (exclude the six rigid-body modes).",
        [("volume_mm3", "mm^3", "solid volume"), ("f1_Hz", "Hz", "lowest elastic free-free frequency"), ("f2_Hz", "Hz", "second")],
        ["five-step Boolean construction", "two circular patterns", "torus groove", "100 small holes"], notes=brake_notes))
    add(task(2, "Geometric Modeling", "complex", "Disc brake rotor (revolve + lug holes) under centrifugal load", "wolfram",
        "Disc Brake (OpenCascadeLink)", OCL + "DiscBrake.html",
        "Steps (1) and (2) of the Wolfram Disc Brake construction: revolve the cross-section polygon (x, y) = (0,144), (25,144), "
        "(25,80.5), (10,80.5), (10,74.125), (46.33,74.125), (46.33,34), (39.13,34), (39.13,67.5), (1,67.5), (1,80.5), (0,80.5) "
        "360 deg about the x-axis; subtract five lug holes (diameter 15.3 along x from 39.13 to 46.33 at (y, z) = (0, 56), "
        "patterned k x 72 deg about x).",
        "E = 99.97 GPa, Poisson ratio 0.29, density 7100 kg/m^3. The five lug-hole surfaces are fixed; the rotor spins at "
        "88.464 rad/s about x (the pad angular velocity of Wolfram's disc-brake model).",
        [("max_radial_disp_um", "um", "maximum radial displacement"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress")],
        ["revolve profile in the right plane", "centrifugal body force"]))
    shaft = ("Wolfram Helical Bevel Gear shaft, axis = x: revolve about the x-axis the closed profile in the x-z plane (y = 0): "
             "polyline (0,0), (0,45), (5,45), (5,39), (51,39), (51,38), (61,38), (61,36); a semicircular arc of radius 11 "
             "centred at (72, 36) from (61,36) to (83,36) passing through (72,25) (a groove); then (83,36), (131,36), "
             "(131,32.5), (163,32.5), (163,0), back to (0,0).")
    arc_note = "The page does not state the OpenCascadeCircle arc orientation; this task fixes it as a groove (through z = 25)."
    add(task(3, "Geometric Modeling", "hard", "Bevel-gear shaft (revolved profile) in torsion", "wolfram", "Helical Bevel Gear",
        OCL + "HelicalBevelGear.html", shaft,
        "Steel E = 210 GPa, Poisson ratio 0.3. Face x = 0 fixed; a torque of 100 N m about x applied on the face x = 163 as a "
        "tangential traction proportional to the distance from the axis.",
        [("twist_deg", "deg", "mean rotation of the face x = 163 about x"), ("max_shear_MPa", "MPa", "maximum shear stress")],
        ["profile with a revolved arc", "torque as distributed traction"], notes=[arc_note]))
    gear = ("Wolfram Helical Bevel Gear body, axis = x. Tooth outline in the y-z plane (x = 0), angles measured in that plane: "
            "8 teeth, each the union of a half tooth and its image under a 180 deg rotation about z; a half tooth is (a) the arc "
            "of the circle r = 85 from 90 deg to t1 = 180 deg - arccos(6/85), (b) an arc of radius 65 joining p1 = 85(cos t1, "
            "sin t1) to p2 = 50(cos t2, sin t2), t2 = 180 deg - arccos(15/50), whose centre is the point with positive "
            "coordinates at distance 65 from both, and (c) the arc of r = 50 from t2 to 112.5 deg; pattern the tooth 8 times "
            "(45 deg). Section 1 = this profile at x = 0; section 2 = profile scaled 0.75, rotated -15 deg about x, at x = -45; "
            "section 3 = scaled 0.5, rotated -30 deg, at x = -95. Loft the three sections into a solid.")
    add(task(4, "Geometric Modeling", "hardest", "Helical bevel gear (shaft + lofted gear + 13 bosses - bore), free-free modes",
        "wolfram", "Helical Bevel Gear", OCL + "HelicalBevelGear.html",
        shaft + " " + gear + " Unite shaft and gear; add 13 bosses (box x in [83, 131], y in [-5, 5], z in [34, 41]) patterned "
        "13 times about x (k x 360/13 deg); subtract a bore of diameter 35 along x from x = -120 to 200.",
        "Steel E = 210 GPa, Poisson ratio 0.3, density 7850 kg/m^3; free-free modal analysis (exclude rigid modes).",
        [("volume_mm3", "mm^3", "solid volume"), ("f1_Hz", "Hz", "lowest elastic free-free frequency")],
        ["three-section twisted loft", "arc-defined tooth", "13-fold pattern", "bore through mixed bodies"], notes=[arc_note]))
    add(task(5, "Geometric Modeling", "complex", "Twisted lofted gear body under axial load", "wolfram", "Helical Bevel Gear",
        OCL + "HelicalBevelGear.html", gear,
        "Steel E = 210 GPa, Poisson ratio 0.3. Section-1 face (x = 0) fixed; 1 kN along -x spread uniformly over the section-3 face.",
        [("axial_disp_um", "um", "mean -x displacement of the section-3 face")], ["tooth profile from three arcs", "loft with scale + twist"]))
    plate = ("Wolfram Surgical Fixation Plate (the tutorial works in cm; here 1 cm = 10 mm), centred at x = 0, long axis x: "
             "length 160, width 10, thickness 3, wave amplitude 1.5. Upper edge y = e(s), s = x + 80 in [0, 80], with phi = "
             "(160/3)(2/3) = 35.556: e = 5 + 1.5 sin(pi s/phi) for s <= 160/3 and e = 5 - 1.5 sin(pi (s/6)/phi) for 160/3 < s <= 80; "
             "mirror about x = 0 and about y = 0. Ends: arc of radius 10 centred at (-75, 0) (and (75, 0)) joined to the edge by a "
             "horizontal segment at y = +/-5. Holes: six round holes of radius 3 at x = -62.222, 8.889, 80, 62.222, -8.889, -80; "
             "three holes bounded by the superellipse |x/2|^3 + |y/5|^3 = 1 scaled by 0.8 and rotated -45 deg, centred at "
             "x = -16, 0, 16. Extrude 3 in z.")
    add(task(6, "Geometric Modeling", "hardest", "Surgical fixation plate in four-point bending", "wolfram", "Surgical fixation plate",
        OCL + "SurgicalFixationPlate.html", plate,
        "Ti-6Al-4V E = 110 GPa, Poisson ratio 0.3. Bottom face supported (u_z = 0) on 1 mm-wide strips across the width centred "
        "at x = +/-70, clear of the holes (one extra point restraint in x and y); 100 N total in -z on 1 mm top strips centred at x = +/-30.",
        [("mid_deflection_mm", "mm", "-z displacement at the bottom-face centre"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress")],
        ["piecewise sinusoidal outline", "superellipse holes", "strip supports"],
        notes=["The tutorial stops at meshing; the bending set-up is defined here."]))

    # ---------------------------------------------------------------------------------------------- Mesh Generation
    add(task(8, "Mesh Generation", "complex", "Thin thermal-contact layer (Si / contact / Al)", "wolfram", "Thermal Contact",
        PDE + "HeatTransfer/ModelCollection/ThermalContact.html",
        "2-D, mm, sector 0 <= angle <= pi/8: silicon r <= 10, contact layer 10 <= r <= 10.025, aluminium 10.025 <= r <= 20; "
        "subtract the region bounded by the quadratic Bezier curve with control points (20, 6), (4, 0), (20, -6) and the "
        "segment x = 20 from y = -6 to 6. Three regions.",
        "Steady heat: k_Si = 63, k_contact = 0.357, k_Al = 232 W/(m K); silicon generates 5 W per metre depth spread uniformly "
        "over its area; convection h = 59.9 W/(m^2 K) to 293.15 K on the outer arc and the cut; the two radial edges are symmetry lines.",
        [("T_max_K", "K", "maximum temperature"), ("contact_drop_K", "K", "mean temperature drop across the contact layer")],
        ["25 um layer between mm-size regions", "mesh grading"], kind="2-D domain"))
    # ----------------------------------------------------------------------------------------------- Heat Transfer
    add(task(11, "Heat Transfer", "complex", "Brake disc friction heating (3-D from the axisymmetric model)", "wolfram",
        "Thermal and Structural Analysis of a Disc Brake", PDE + "HeatTransfer/ModelCollection/DiscBrake.html",
        "Annular disc, axis z: inner radius 66 mm, outer 113.5 mm, thickness 11 mm (z in [-5.5, 5.5]); imprint the pad track "
        "76.5 <= r <= 113.5 mm on both faces as separate faces.",
        "Transient heat: k = 51, rho = 7100, c = 498.826 (SI). Flux into each pad track q = mu p omega r with mu = 0.5, "
        "omega = 88.464 rad/s, p = 1.47 MPa x 64.5/360 (pad-averaged); h = 100 W/(m^2 K) to 293.15 K on all other faces; "
        "T(0) = 293.15 K; t_end = 3.96 s.",
        [("T_max_K", "K", "maximum temperature at t_end")], ["face imprinting for the flux", "short transient"]))
    add(task(14, "Heat Transfer", "complex", "Shrink fitting: tungsten rod in a steel frame", "wolfram", "Shrink Fitting of Assembly",
        PDE + "HeatTransfer/ModelCollection/ShrinkFitting.html",
        "2-D, mm. Frame = rectangle [0,110] x [0,120] minus the disks (65,0) r 15, (110,120) r 35, (0,60) r 25, minus the rod. "
        "Rod = rectangle [65,160] x [50,70] united with the disk (65,60) r 10. Two regions sharing the interface.",
        "Transient heat: tungsten rho 19000, c 134, k 163; steel rho 7500, c 470, k 44 (SI). Rod starts at -10 C, frame at 84 C; "
        "h = 500 W/(m^2 K) to 17 C on every outer boundary except the rod surface inside the frame (65 <= x < 110); run 200 s.",
        [("time_clearance_12um_s", "s", "first time t at which 20 mm x (1.2e-5 (84 - Tmax_frame(t)) + 4.5e-6 (Tmin_rod(t) + 10)) "
          "reaches 12 um")], ["two-region planar assembly", "event extraction"], kind="2-D domain"))
    an = anemometer()
    add(task(15, "Heat Transfer", "hardest", "Contactless anemometer chip", "wolfram", "Contactless Anemometer",
        PDE + "HeatTransfer/ModelCollection/Anemometer.html",
        "2-D, mm (the page scales lengths by 1 mm). Silicon chip = polygon (0,0), p2, p5, p6, p3, p4, p12, p9 with "
        f"p2 = {an['p2']}, p5 = {an['p5']}, p6 = {an['p6']}, p3 = {an['p3']}, p4 = {an['p4']}, p12 = {an['p12']}, p9 = {an['p9']} "
        "(walls at arctan(sqrt 2) = 54.7 deg); the etched cavity (p2, p5, p6, p3) is an air region; heater = rectangle "
        "[590, 610] x [70, 80] cut from the membrane; flow channel [0, 1200] x [80, 380]. Four regions.",
        "Steady convection-conduction: k = 148 W/(m K) in silicon and heater, 0.0239 in air; rho c = 2330 x 710 in solids, "
        "1.040 x 1012 in air; heater source 1e7 W/m^3; channel velocity u_x = 1e-3 (1 - ((y - 230)/150)^2) m/s; temperature "
        "rise T = 0 on the chip bottom y = 0 and at the channel inlet x = 0; other boundaries insulated.",
        [("T_heater_max", "K", "maximum temperature rise in the heater")], ["54.7 deg etched cavity", "four regions"],
        kind="2-D domain", notes=["Boundary marker 1 of the page is taken as the chip bottom and channel inlet."]))

    # ------------------------------------------------------------------------------------------------ Fluid Dynamics
    add(task(16, "Fluid Dynamics", "complex", "Spherical chamber with two branch pipes (Stokes)", "wolfram", "Laminar Flow",
        PDE + "FluidDynamics/LaminarFlow.html",
        "1 page unit = 10 mm: union of a sphere of radius 10 at the origin, a cylinder of radius 2 along +z from 0 to 20 and a "
        "cylinder of radius 2 along +y from 0 to 20.",
        "Stokes flow in page units, viscosity 1: inlet velocity -(1 - r^2/0.2^2) along z on the end z = 2 of the +z pipe "
        "(r = distance from its axis); zero pressure on the end y = 2 of the +y pipe; no slip elsewhere.",
        [("pressure_drop", "-", "mean inlet pressure minus mean outlet pressure")], ["three-body union", "inlet profile"]))
    add(task(17, "Fluid Dynamics", "hard", "Contracting channel", "wolfram", "Laminar Flow", PDE + "FluidDynamics/LaminarFlow.html",
        "2-D, 1 page unit = 10 mm: union of [0,10] x [0,5] and [10,20] x [1,4].",
        "Steady Navier-Stokes in page units, rho = 1, mu = 0.01; inlet x = 0 parabolic with peak 1; outlet x = 2 at p = 0; no slip.",
        [("pressure_drop", "-", "mean inlet minus outlet pressure")], ["re-entrant corners"], kind="2-D domain",
        notes=["Fluid properties and inlet set here; the geometry is the page's."]))

    # ----------------------------------------------------------------------------------------------- Solid Mechanics
    hook_load = ("PLA at 60 % infill: E = 0.6 x 3500 MPa, Poisson ratio 0.3. Face x = 0: u_x = 0; screw zones (points within "
                 "9 mm of either hole axis, measured in the y-z plane) fixed; 300 N in -y spread over the surface points within "
                 "25 mm of (x, y) = (50, -14.29).")
    hole_txt = ("Two countersunk screw holes along x at y = 20 and y = 60, z = 10: a cylinder of radius 5 through the back bar, "
                "united with a cone of base radius 9 at x = 1.2 t narrowing to its apex at x = 0 (t = back-bar thickness).")
    url3d = PDE + "StructuralMechanics/ModelCollection/3DPrintedMechanicalDesign.html"
    add(task(19, "Solid Mechanics", "hardest", "3-D printed wall hook 1", "wolfram", "3D Print and Mechanical Design", url3d,
        "Closed outline in x-y: outer arc centre (50,0) radius 50 from -180 to 0 deg, back bar x in [0, 20] from y = 0 to 80, inner "
        "arc centre (50,0) radius 30 from -180 to 0 deg, tip-cap arc centre (90,0) radius 10 from 0 to 180 deg; extrude 20 in z; "
        "fillet every edge with radius 6. " + hole_txt + " (t = 20.)", hook_load,
        [("max_disp_mm", "mm", "maximum displacement magnitude"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress")],
        ["all-edge fillet", "countersinks", "load patch from a point set"]))
    add(task(20, "Solid Mechanics", "complex", "3-D printed wall hook 2 (pocketed)", "wolfram", "3D Print and Mechanical Design", url3d,
        "Closed outline: arc centre (50,0) radius 50 from -90 to 0 deg, line (0,-50)-(0,80), (0,80)-(12,80), (12,80)-(12,0), inner "
        "arc centre (50,0) radius 38 from -180 to 0 deg, tip-cap arc centre (94,0) radius 6 from 0 to 180 deg, line (0,-50)-(50,-50); "
        "extrude 20; subtract the extruded pocket = rectangle [6, 44] x [-44, -20] minus the disk (50,0) r 44. " + hole_txt + " (t = 12.)",
        hook_load, [("max_disp_mm", "mm", "maximum displacement magnitude")], ["quarter arcs + pocket"]))
    add(task(21, "Solid Mechanics", "complex", "3-D printed wall hook 3 (polyline)", "wolfram", "3D Print and Mechanical Design", url3d,
        "Outline polyline (0,-40), (0,80), (12,80), (12,-28), (88,-28), (88,-16), (100,-16), (100,-40), closed; extrude 20. "
        + hole_txt + " (t = 12.)", hook_load, [("max_disp_mm", "mm", "maximum displacement magnitude")], ["polyline hook"],
        notes=["The page also fillets five edges (radius 6) chosen by OpenCascade index; omitted."]))
    add(task(22, "Solid Mechanics", "complex", "Hyperelastic dogbone with clamp tabs", "wolfram", "Hyperelastic Model Comparison",
        PDE + "StructuralMechanics/ModelCollection/HyperelasticModelComparison.html",
        "Outline (mm): (0,-7.5), (2.5,-7.5), (6.25,-3.75), (43.75,-3.75), (47.5,-7.5), (50,-7.5), (50,7.5), (47.5,7.5), "
        "(43.75,3.75), (6.25,3.75), (2.5,7.5), (0,7.5); clamp tabs [-1.5,0] x [-7.5,7.5] and [50,51.5] x [-7.5,7.5]; extrude "
        "2.5 mm (z in [-1.25, 1.25]).",
        "Nearly incompressible Yeoh material, c1 = 2.25e4, c2 = 1.26e5, c3 = 1.12e5 Pa; face x = -1.5 fixed; total force 9.375 N "
        "(0.5 MPa x 2.5 mm x 7.5 mm) along +x on face x = 51.5; finite strain.",
        [("elongation_mm", "mm", "x-displacement of face x = 51.5")], ["finite strain", "dogbone outline"]))
    add(task(23, "Solid Mechanics", "complex", "Biaxial tissue specimen with suture holes", "wolfram",
        "Biaxial Tensile Test of Hyperelastic Tissue", PDE + "StructuralMechanics/ModelCollection/BiaxialTensileTestHyperelasticTissue.html",
        "Quarter model: square [0,10] x [0,10] mm, 1.2 mm thick, with six holes of radius 0.5 mm at (1.25,8), (3.75,8), (6.25,8), "
        "(8,1.25), (8,3.75), (8,6.25).",
        "Compressible neo-Hookean, C10 = 0.127 MPa (shear modulus 2 C10), D1 = 1e-6 (bulk modulus 2/D1), plane stress, finite "
        "strain; symmetry on x = 0 and y = 0; the hole edges near y = 8 are displaced +4 mm in y and those near x = 8 +4 mm in x.",
        [("mean_sxx_MPa", "MPa", "area-mean Cauchy stress xx at full stretch")], ["six holes", "displacement-controlled hyperelasticity"]))
    # ----------------------------------------------------------------------------------------------------- Acoustics
    add(task(26, "Acoustics", "hard", "Helmholtz resonator (neck + spherical cavity)", "wolfram", "Helmholtz Resonator",
        PDE + "Acoustics/ModelCollection/HelmholtzResonator.html",
        "Air volume, axis z: neck cylinder radius 10 mm from z = -50 to 0 united with a spherical cavity of radius 50 mm centred "
        "at z = -95 mm.", "Air, c = 343 m/s; p = 0 on the neck mouth z = 0; rigid elsewhere; acoustic eigenproblem.",
        [("f1_Hz", "Hz", "lowest resonance frequency")], ["neck-cavity union"]))
    # --------------------------------------------------------------------------------------------- Electromagnetics
    add(task(31, "Electromagnetics", "hard", "Spherical capacitor shell", "wolfram", "Spherical Capacitor",
        PDE + "Electromagnetics/ModelCollection/SphericalCapacitor.html",
        "Dielectric shell between spheres of radius 3 mm and 10 mm.",
        "Electrostatics, relative permittivity 3.9; inner surface carries 6e-11 C (uniform surface charge); outer surface grounded.",
        [("capacitance_pF", "pF", "charge / potential difference")], ["shell"], ref=spherical_capacitor(), tol=0.01))
    add(task(32, "Electromagnetics", "complex", "Parallel-plate capacitor with fringing", "wolfram", "Electrostatics",
        PDE + "Electromagnetics/Electrostatics.html",
        "2-D, m (export mm): air box [-1, 1]^2; two conductor plates 0.5 wide and 0.04 thick with inner faces at y = +/-0.1 "
        "(removed as holes); dielectric region |x| <= 0.25, |y| <= 0.1 between them; air elsewhere.",
        "Electrostatics: dielectric relative permittivity 4, air 1; top plate 1 V, bottom plate 0 V; box edges insulating.",
        [("capacitance_per_depth_pF_per_m", "pF/m", "per unit depth")], ["holes + embedded dielectric"], kind="2-D domain",
        notes=["The dielectric permittivity is not in the scraped code; set here."]))
    add(task(33, "Electromagnetics", "complex", "Coil pair (magnetostatic)", "wolfram", "Quasistatic Magnetic Fields",
        PDE + "Electromagnetics/QuasistaticMagneticFields.html",
        "Axis z: two ring coils of square section 2.5 x 2.5 mm, mean radius 40 mm, centred at z = +/-20 mm, inside an air cylinder "
        "of radius 76.25 mm and length 112.5 mm centred at the origin. Three solids.",
        "Magnetostatics: 1 A total azimuthal current per coil, uniform over its section, same direction; tangential A = 0 on the "
        "air boundary.", [("Bz_center_uT", "uT", "B_z at the origin")], ["revolved multi-body"]))

    # -------------------------------------------------------------------------------------------------- Multiphysics
    add(task(34, "Multiphysics", "hardest", "Electrostatically actuated MEMS beam", "wolfram", "Electrostatically Actuated MEMS Device",
        PDE + "Multiphysics/ModelCollection/ElectrostaticallyActuatedMEMS.html",
        "2-D, um (export mm x 1e-3): air box [-175, 175] x [-17, 13]; fixed electrode [25, 75] x [-2, 0] and beam [-75, 75] x [2, 4] "
        "removed as conductors; the beam is also a separate solid region.",
        "Electrostatics in vacuum: beam at 20 V, electrode and box at 0 V. Structure: E = 170 GPa, Poisson ratio 0.34, plane "
        "stress, 1 um thick, beam ends x = +/-75 clamped. Electrostatic pressure on the beam (|D0| G/(G - |v|))^2/(2 eps0), "
        "G = 2 um, D0 = field of the undeflected solution, v = local deflection; iterate to equilibrium.",
        [("max_deflection_nm", "nm", "maximum beam deflection")], ["coupled iteration"], kind="2-D domain"))
    add(task(36, "Multiphysics", "complex", "Hygroscopic swelling of a seal", "wolfram", "Hygroscopic Swelling",
        PDE + "Multiphysics/ModelCollection/HygroscopicSwelling.html",
        "2-D, mm. Rubber region: polygon (0,0), (8.735,0), (4.235,9), (0,9), (0,7), (2.55,7), (5.05,2), (0,2). Cover plate: "
        "rectangle [0, 4.235] x [9, 10]. Two regions.",
        "Moisture diffusion D = 5e-2 (rubber), 5e-10 (plate); c = 30 on the notch faces (0,7)-(2.55,7)-(5.05,2)-(0,2), c = 0 on "
        "y = 0 and y = 10. Then plane-strain, nearly incompressible neo-Hookean solid: shear modulus C1/2 in rubber "
        "(C1 = 0.31237 MPa), 1e4 C1 in the plate; swelling strain 8.3e-4 (c - 5); y = 0: u_y = 0; x = 0: u_x = 0.",
        [("max_disp_um", "um", "maximum displacement")], ["internal notch", "diffusion -> swelling"], kind="2-D domain",
        notes=["The page also couples heat; this task keeps the moisture-swelling chain."]))
    dc = dew_condenser()
    add(task(38, "Multiphysics", "hardest", "Passive dew condenser in a wind profile", "wolfram", "Water Condensation of Passive Dew Condensers",
        PDE + "Multiphysics/ModelCollection/PassiveDewCondenser.html",
        f"2-D, mm: air domain [0, 1500] x [-750, 750]; condenser plate (1 m x 2.53 mm) corners {dc['condenser']}; insulation "
        f"(22.77 mm) corners {dc['insulation']}; support triangle {dc['support']}. Regions: air, condenser, insulation + support.",
        "Steady flow of air (rho 1.2, mu 1.8e-5) with inlet profile u = 0.35 ln((z/1000 + 0.75 + 0.1)/0.1)/ln(100) m/s on x = 0 "
        "(z in mm), outlet p = 0 on x = 1500, no slip on the ground and the condenser; heat: air k 0.026, cp 1005, inlet 288 K; "
        "condenser top surface held at 283 K; insulation k 0.04.",
        [("condenser_heat_W_per_m", "W/m", "heat into the condenser per metre depth")], ["thin tilted layers", "multiple regions"],
        kind="2-D domain", notes=["The page's radiative sky model is replaced by a fixed condenser temperature."]))

    # ----------------------------------------------------------------------------------------------- Seamless Workflow
    add(task(42, "Seamless Workflow", "hardest", "3-D print infill study: CAD family -> FEM -> fitted law", "wolfram",
        "3D Print and Mechanical Design", url3d,
        "Ten 2-D specimens, mm: outer rectangle [-2.4, 52.4] x [-2.4, 62] minus a grid of square cells of pitch 50/n, each inset "
        "0.4 (line width 0.8), covering [0, 50]^2, for n = 2, 3, 5, 8, 12, 16, 20, 30, 40, plus the solid specimen.",
        "Plane strain, E = 3500 MPa for y <= 52.4 and 100 x that above, Poisson ratio 0.3; bottom edge fixed; uniform downward "
        "load on the top edge; stiffness = 1/max deflection, normalised by the stiffest specimen; least-squares fit "
        "stiffness = a x + b x^2 against infill area fraction x (area / solid area).",
        [("fit_a", "-", "linear coefficient"), ("fit_b", "-", "quadratic coefficient")], ["parametric CAD family", "fit"],
        kind="2-D domain"))
    add(task(43, "Seamless Workflow", "hardest", "Disc brake: tutorial CAD -> thermal model", "wolfram",
        "Disc Brake (OpenCascadeLink) + Thermal and Structural Analysis of a Disc Brake", OCL + "DiscBrake.html", brake_geo,
        "Transient heat with the disc-brake model's data (k 51, rho 7100, c 498.826; flux mu p omega r with mu 0.5, "
        "omega 88.464 rad/s, p = 1.47 MPa x 64.5/360) into both friction faces x = 0 and x = 25 for 80.5 <= r <= 144; h = 100 "
        "W/(m^2 K) to 293.15 K elsewhere; T(0) = 293.15 K; t = 3.96 s.",
        [("T_max_K", "K", "maximum temperature at 3.96 s")], ["chaining two pages", "flux on a patterned face"], notes=brake_notes))

    # --------------------------------------------------------------------------------------------- MFEM (mfem.org)
    add(task(44, "Heat Transfer", "hard", "Cross-heat block (MFEM tutorial Gmsh model)", "mfem", "Meshing and visualization tutorial",
        "https://mfem.org/tutorial/meshvis",
        "L = 100 mm. Cube [0, L]^3 minus two cylinders of radius L/10 running along +y through the cube with axes at "
        "(x, z) = (L/8, L/4) and (L/2, L/4) (the page's Gmsh BooleanDifference).",
        "Steady conduction, k = 1 W/(m K), no source: surface of hole 1 at 1 K, surface of hole 2 at 0 K, outer faces insulated.",
        [("conductance_W_per_K", "W/K", "heat leaving hole 1")], ["Boolean holes", "named boundaries"],
        notes=["The page names boundaries by Gmsh surface number; the hole-to-hole set-up is defined here."]))
    # ------------------------------------------------------- engineering parts added from the widened crawl (FEM on the page)
    SM, SMV = PDE + "StructuralMechanics/SolidMechanics.html", PDE + "StructuralMechanics/SolidMechanicsVerificationTests.html"
    bracket = ("Wolfram Book Shelf Bracket (d = 10, w = 50, h = 200; units mm). Wall plate: box x in [0, 10], y in [0, 50], z in "
               "[0, 200]. Shelf arm: box x in [0, 200], y in [0, 50], z in [180, 190], united with the plate. Two screw holes: "
               "cylinders of radius 5 along x through the plate at (y, z) = (25, 50) and (25, 150). Fillets of radius 10 on the "
               "concave edge where the arm underside (z = 180) meets the plate front (x = 10), and on the two vertical edges of "
               "the arm tip (x = 200, y = 0 and y = 50). 2 mm x 45 deg chamfers on both hole edges on the front face x = 10.")
    bracket_bcs = ("Back face x = 0: u_x = 0 (roller against the wall). Screws: every point of the hole and chamfer surfaces within "
                   "10 mm of a hole axis ((y - 25)^2 + (z - 50)^2 <= 100 or (y - 25)^2 + (z - 150)^2 <= 100) fixed.")
    bracket_mat = "E = 210 GPa, Poisson ratio 0.3, density 7850 kg/m^3 (the page's explicit parameter set)."
    bracket_notes = ["The tutorial applies its fillets and chamfers by OpenCascade edge number (20, 22, 30 and 52, 53); the "
                     "edges are named here from the page's drawings.",
                     "The page runs its analyses with Wolfram's Titanium entity; this task uses the explicit parameter set the "
                     "page lists in its Material Parameters section."]
    bracket_geo = ("Book Shelf Bracket (OpenCascadeLink)", OCL + "BookShelfBracket.html")
    add(task(54, "Solid Mechanics", "complex", "Bookshelf bracket under a shelf load", "wolfram", "Solid Mechanics", SM, bracket,
        bracket_mat + " " + bracket_bcs + " Load: 500 N in -z spread uniformly over the arm top face (z = 190, x >= 10). "
        "Linear elastic, small strain.",
        [("max_total_disp_mm", "mm", "maximum displacement magnitude"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress"),
         ("reaction_x_back_N", "N", "total x-reaction on the back face x = 0")],
        ["Boolean + fillets + chamfers", "partial (roller) constraint", "load on a sub-face"], notes=bracket_notes, geo=bracket_geo))
    add(task(55, "Solid Mechanics", "complex", "Bookshelf bracket: mounted eigenmodes", "wolfram", "Solid Mechanics", SM, bracket,
        bracket_mat + " " + bracket_bcs + " Undamped eigenmode analysis of the mounted bracket.",
        [("f1_Hz", "Hz", "first eigenfrequency"), ("f2_Hz", "Hz", "second"), ("f3_Hz", "Hz", "third")],
        ["eigenproblem with mixed constraints"], notes=bracket_notes, geo=bracket_geo))
    add(task(56, "Solid Mechanics", "complex", "Bookshelf bracket: free-free eigenmodes", "wolfram", "Solid Mechanics", SM, bracket,
        bracket_mat + " No constraints; exclude the six rigid-body modes.",
        [("f1_Hz", "Hz", "lowest elastic free-free frequency"), ("f2_Hz", "Hz", "second"), ("f3_Hz", "Hz", "third")],
        ["rigid-body modes"], notes=bracket_notes, geo=bracket_geo))
    add(task(57, "Solid Mechanics", "hard", "L-bracket with a filleted inner corner", "wolfram", "Solid Mechanics", SM,
        "Union of the boxes x in [0, 10], y in [0, 20], z in [0, 50] (upright) and x in [0, 50], y in [0, 20], z in [0, 10] "
        "(foot), units mm; fillet of radius 3 on the inner corner edge (x = 10, z = 10, along y).",
        "E = 210000 MPa, Poisson ratio 0.3. Top face z = 50 fixed; 1000 N in -z as a uniform traction (5 MPa) on the end face "
        "x = 50. Linear elastic.",
        [("max_von_mises_MPa", "MPa", "maximum von Mises stress (at the fillet)")], ["fillet removes a stress singularity"],
        page_ref={"max_von_mises_MPa": 230.197}, tol=0.05,
        notes=["Reference: the page's refined fillet mesh (mesh5); its coarser fillet mesh gives 232.734 MPa."]))
    add(task(58, "Solid Mechanics", "hard", "Spherical pressure hull (bathyscaphe) under sea pressure", "wolfram", "Solid Mechanics",
        SM, "One octant (x, y, z >= 0) of a hollow sphere centred at the origin, inner radius 80 mm, outer radius 100 mm.",
        "Titanium, E = 116 GPa, Poisson ratio 0.32. External pressure 1e5 Pa normal to the outer surface; symmetry on the three "
        "cut planes (u_x = 0 on x = 0, u_y = 0 on y = 0, u_z = 0 on z = 0); inner surface free.",
        [("u_outer_nm", "nm", "radial displacement of the outer surface (negative = inward)"),
         ("u_inner_nm", "nm", "radial displacement of the inner surface"),
         ("max_von_mises_MPa", "MPa", "maximum von Mises stress")], ["symmetry octant", "pressure normal to a curved face"],
        ref=bathyscaphe(), tol=0.01,
        notes=["The page passes Wolfram's Titanium entity; E and Poisson ratio are that entity's values."]))
    add(task(59, "Solid Mechanics", "hard", "Thick-walled pipe under internal pressure (plane strain)", "wolfram", "Solid Mechanics",
        SM, "Quarter annulus centred at the origin in the first quadrant, inner radius 5, outer radius 15 (units mm).",
        "Plane strain, E = 30e3, Poisson ratio 0.3, internal pressure 20 (the page's consistent units: MPa). Symmetry: u_x = 0 on "
        "x = 0, u_y = 0 on y = 0; outer surface free.",
        [("u_inner", "mm", "radial displacement at r = 5"), ("u_outer", "mm", "radial displacement at r = 15"),
         ("max_hoop_stress", "MPa", "maximum hoop stress")], ["plane strain", "symmetry"], ref=thick_pipe(), tol=0.01,
        kind="2-D domain"))
    add(task(60, "Solid Mechanics", "hard", "Sleeve with a filleted shoulder (axisymmetric)", "wolfram", "Solid Mechanics", SM,
        "Revolve about z (units mm) the region r in [1, 8], z in [0, 9] minus {r >= 6, z >= 5.5}, minus {r >= 6.5, z >= 5} and "
        "minus the disk of radius 0.5 centred at (r, z) = (6.5, 5.5): a bored sleeve (bore radius 1) of outer radius 8 for "
        "z < 5 stepping to 6 above, with a 0.5 mm fillet in the shoulder.",
        "Axisymmetric linear elasticity, E = 1000 MPa, Poisson ratio 0.33. Bore r = 1: u_r = 0; face z = 0: u_z = 0; an axial "
        "traction of +20 MPa (pulling) on the top face z = 9.",
        [("uz_top_mm", "mm", "mean axial displacement of the top face"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress")],
        ["axisymmetric shoulder fillet", "stress concentration"],
        notes=["The page works in consistent units; mm and MPa are set here."]))
    add(task(61, "Solid Mechanics", "hard", "Aluminium insert in a steel block, heated (plane stress)", "wolfram", "Solid Mechanics",
        SM, "Quarter model, units mm: rectangle [0, 75] x [0, 40] split into an aluminium region [0, 50] x [0, 15] and the "
        "L-shaped steel remainder (two faces sharing the interface).",
        "Plane stress, thickness 5 mm. Steel E = 200 GPa, Poisson ratio 0.3, alpha = 12e-6 /K; aluminium E = 70 GPa, Poisson "
        "ratio 0.33, alpha = 23e-6 /K. Uniform temperature rise 70 K from a stress-free state. Symmetry: u_x = 0 on x = 0, "
        "u_y = 0 on y = 0.",
        [("max_total_disp_um", "um", "maximum displacement magnitude"), ("max_von_mises_MPa", "MPa", "maximum von Mises stress")],
        ["two materials", "thermal strain mismatch", "re-entrant interface corner"], kind="2-D domain"))
    add(task(62, "Solid Mechanics", "hard", "Plate with a hole in tension", "wolfram", "Solid Mechanics Verification Tests", SMV,
        "Plate x in [0, 100], y in [0, 5], z in [0, 50] (units mm) with a through hole of radius 10 along y centred at "
        "(x, z) = (50, 25).",
        "E = 210000 MPa, Poisson ratio 0.3. Face x = 0 fixed; 1000 N in +x as a uniform traction on the face x = 100.",
        [("max_von_mises_MPa", "MPa", "maximum von Mises stress")], ["stress concentration at a hole"],
        page_ref={"max_von_mises_MPa": 14.9}, tol=0.05,
        notes=["Reference value and 5 % tolerance as stated by the page's verification test (SolidMechanics-FEM-Stationary-3D-0002)."]))
    add(task(63, "Solid Mechanics", "hardest", "Elastic-plastic plate with a hole", "wolfram", "Plasticity",
        PDE + "StructuralMechanics/Plasticity.html",
        "Quarter plate, units mm: rectangle [0, 40] x [0, 20] minus the quarter disk of radius 20/3 centred at the origin.",
        "Plane strain, thickness 1 mm, E = 70 GPa, Poisson ratio 0.3; von Mises plasticity with initial yield stress 2500 MPa and "
        "linear isotropic hardening modulus 15 GPa. Symmetry: u_x = 0 on x = 0, u_y = 0 on y = 0; prescribed u_x = 1.5 mm on "
        "x = 40.",
        [("vm_elastoplastic_MPa", "MPa", "von Mises stress at (x, y) = (20/2.9, 20/2.9)"),
         ("vm_elastic_MPa", "MPa", "the same point for a purely elastic material")], ["return mapping", "hole in a plate"],
        kind="2-D domain", notes=["The page uses its ExtendedPlaneStrain model form."]))
    add(task(64, "Electromagnetics", "hardest", "Horseshoe permanent magnet attracting a coin", "wolfram",
        "Magnetostatics for Permanent Magnets", PDE + "Electromagnetics/MagnetostaticsForPermanentMagnets.html",
        "Quarter model (y >= 0, z >= 0), units mm. Horseshoe leg: the rectangle x in [80, 100], z in [0, 10] in the plane y = 0 "
        "swept along the cubic Bezier centre line with control points (10, 20, 5), (40, 30, 5), (90, 30, 5), (90, 0, 5) (the "
        "rectangle sits at the curve's end and stays normal to it), split by the vertical plane through (50, 0) and (40, 50): the "
        "part containing (20, 30, 5) is the magnet, the rest iron. Coin: the half disk of radius 10 centred at (-30, 0) (y >= 0) "
        "extruded from z = 0 to 5. Air: the box [-50, 120] x [0, 100] x [0, 60]. Four regions with shared interfaces.",
        "Current-free magnetostatics with a scalar potential Vm (H = -grad Vm, B = mu0 mu_r (H + M)): iron and coin mu_r = 5000; "
        "magnet M = (8e5, 0, 0) A/m, mu_r = 1; air mu_r = 1. Vm = 0 on y = 0 (antisymmetry plane); all other boundaries "
        "natural (z = 0 is a symmetry plane).",
        [("Fx_coin_N", "N", "x-force on the whole coin (4 x the quarter) from the Maxwell stress over the coin surface")],
        ["path sweep + splitting face", "four-region conformal mesh", "Maxwell stress force"],
        geo=("Permanent Magnet with Coin (OpenCascadeLink)", OCL + "PermanentMagnetWithCoin.html")))
    add(task(65, "Fluid Dynamics", "complex", "Beaker stirred by a three-disc impeller (swirling flow)", "wolfram", "Laminar Flow",
        PDE + "FluidDynamics/LaminarFlow.html",
        "Axisymmetric about z, units mm. Fluid domain: beaker r in [0, 20], z in [0, 50] minus the stirrer: shaft r <= 1 for "
        "z in [15, 50]; discs r <= 10, z in [15, 17]; r <= 20/3, z in [19, 21]; r <= 10, z in [23, 25]. Build the 3-D fluid "
        "solid by revolving (the analysis may use the axisymmetric section).",
        "Steady incompressible Navier-Stokes with swirl, water mu = 1e-3 Pa s, rho = 1000 kg/m^3. Stirrer surfaces rotate at "
        "omega = pi rad/s (u_r = u_z = 0, u_theta = omega r); beaker wall r = 20 and bottom z = 0 no-slip; open top z = 50 with "
        "u_z = 0; p = 0 at (r, z) = (20, 50).",
        [("max_meridional_speed_mm_s", "mm/s", "maximum of sqrt(u_r^2 + u_z^2)"),
         ("u_theta_mm_s", "mm/s", "swirl velocity at (r, z) = (15, 20)")], ["swirl (2.5-D) formulation", "secondary flow"]))
    add(task(66, "Fluid Dynamics", "complex", "Power-law fluid through a looped pipe manifold", "wolfram", "Laminar Flow",
        PDE + "FluidDynamics/LaminarFlow.html",
        "2-D, units mm (the page's consistent units): union of the rectangles [0.5, 1.5] x [-1, 5], [1, 5] x [4.5, 5.5], "
        "[1, 5] x [0.75, 1.25], [4.5, 5.5] x [0.5, 5], [5.5, 9] x [0.5, 1.5], [5.5, 9] x [4.75, 5.25], [8.5, 9.5] x [1.5, 7] and "
        "the disks of radius 1 centred at (1, 5), (5, 5), (1, 1), (5, 1), (9, 1), (9, 5).",
        "Steady incompressible flow of a power-law fluid (rho = 1, exponent 2, consistency 0.01; consistent units). Inlet "
        "y = -1: u = 0, v = 2 ((x - 0.5) - (x - 0.5)^2); no-slip on every boundary with -1 < y < 7; outlet y = 7 traction-free "
        "with p = 0 at (9.5, 7).",
        [("p_inlet", "-", "pressure at (1, -1)"), ("max_speed", "-", "maximum velocity magnitude")],
        ["many-primitive union", "non-Newtonian viscosity"], kind="2-D domain"))
    add(task(67, "Heat Transfer", "hard", "Thick-walled tube heated on an inner band", "wolfram", "Heat Transfer Verification Tests",
        PDE + "HeatTransfer/HeatTransferVerificationTests.html",
        "Tube about z, units mm: inner radius 20, outer radius 100, z in [0, 140]; split the bore surface at z = 40 and z = 100 "
        "so the heated band is its own face.",
        "Steady conduction, k = 52 W/(m K). Heat flux 5e5 W/m^2 into the solid through the bore band 40 <= z <= 100; T = 273.15 K "
        "on z = 0, z = 140 and r = 100; the rest of the bore insulated.",
        [("T_probe_K", "K", "temperature at (r, z) = (40, 40)")], ["imprinted band", "axisymmetric benchmark"],
        page_ref={"T_probe_K": 332.97}, tol=0.01,
        notes=["Reference temperature as stated by the page (HeatTransfer-FEM-Stationary-2DAxisym-Single-HeatTransfer-0002)."]))
    add(task(68, "Multiphysics", "hardest", "Joule-heated tungsten heating coil", "wolfram", "Joule Heating of Tungsten Wire",
        PDE + "Multiphysics/ModelCollection/JouleHeating.html",
        "Units mm. A wire of radius 2.5 swept along the planar centre line (z = 0): straight (0, 0) -> (100, 0); half circle "
        "of radius 7.5 about (100, 7.5) to (100, 15); straight to (10, 15); half circle of radius 7.5 about (10, 22.5) through "
        "(2.5, 22.5) to (10, 30); straight to (110, 30); quarter circle of radius 7.5 about (110, 22.5) to (117.5, 22.5); "
        "straight to (117.5, -2.5). Flat end faces at x = 0 and y = -2.5.",
        "Tungsten: sigma = 1.79e7 S/m, k = 175 W/(m K). Stationary current: 0.2 V on the end face x = 0, 0 V on the end face "
        "y = -2.5. The Joule heat sigma |grad V|^2 drives steady conduction: both end faces at 300 K; the lateral surface loses "
        "heat by convection (h = 20 W/(m^2 K)) and radiation (emissivity 1) to 300 K.",
        [("joule_heat_W", "W", "total Joule heat"), ("T_max_K", "K", "maximum temperature")],
        ["swept tube with tangent arcs", "electric -> thermal chain", "radiation (nonlinear)"],
        notes=["The page's HeatRadiationValue sets no emissivity; the default 1 is stated here."]))
    add(task(69, "Multiphysics", "complex", "Disc brake: thermal stress after braking", "wolfram",
        "Thermal and Structural Analysis of a Disc Brake", PDE + "HeatTransfer/ModelCollection/DiscBrake.html",
        "As FEMCAD-011: annular disc about z, inner radius 66 mm, outer 113.5 mm, thickness 11 mm (z in [-5.5, 5.5]), pad "
        "tracks 76.5 <= r <= 113.5 mm imprinted on both faces.",
        "First the FEMCAD-011 transient heat problem to t_end = 3.96 s; then quasi-static thermoelasticity at t_end with "
        "E = 99.97 GPa, Poisson ratio 0.29, alpha = 1.08e-5 /K, stress-free at 293.15 K. Mid-plane z = 0: u_z = 0; bore "
        "r = 66: u_r = 0 (the page's two roller constraints).",
        [("max_von_mises_MPa", "MPa", "maximum von Mises stress at t_end"), ("max_uz_um", "um", "maximum |u_z| at t_end")],
        ["transient thermal -> structural chain", "imprinted faces"]))
    # ------------------------------------------------- MFEM examples (mfem.org/examples; definitions from the MFEM 4.10 release)
    EX, MESHFMT = "https://mfem.org/examples/", "https://mfem.org/mesh-format-v1.0/"
    beam_geo = ("MFEM mesh format (beam-quad.mesh)", MESHFMT)
    mfem_note = "Problem and settings as defined in the MFEM 4.10 release (examples/ex*.cpp, data/*.mesh)."
    add(task(70, "Solid Mechanics", "hardest", "Topology-optimised cantilever (Example 37)", "mfem",
        "Example Codes and Miniapps: Example 37", EX,
        "Design domain of MFEM Example 37 (the page's drawing), 1 unit = 100 mm: the rectangle [0, 3] x [0, 1]. Deliver as "
        "part.step the optimised design: the region where the filtered density is >= 0.5, as planar face(s) in z = 0.",
        "MFEM Example 37 with its default settings: the 3 x 1 square-cell mesh refined uniformly 5 times (96 x 32 cells), "
        "quadratic displacement; 2-D linear elasticity with lambda = mu = 1 scaled by the SIMP law rho_min + rho~^3 (1 - "
        "rho_min), rho_min = 1e-6; edge x = 0 fixed, all other edges traction-free; body force (0, -1) per unit area inside "
        "the disk of radius 0.05 centred at (2.9, 0.5). Density filter -eps^2 lap(rho~) + rho~ = rho with eps = 0.01 and "
        "natural boundary conditions; volume fraction 0.5. Minimise the compliance int f.u by the example's entropic mirror "
        "descent (sigmoid parametrisation, step alpha_k = k^2 with alpha_1 = 1) until the reduced-gradient norm < 1e-4 and "
        "the increment norm < 1e-2.",
        [("compliance", "-", "final compliance int f.u"), ("volume_fraction", "-", "final material volume / domain volume")],
        ["PDE-constrained optimisation", "density filter", "CAD from a density field"], tol=0.05, kind="2-D domain",
        example_ref={"compliance": 0.00387521, "volume_fraction": 0.5},
        notes=[mfem_note, "Reference: ex37 run as shipped (no options) stops at step 33 and prints these values."]))
    add(task(71, "Solid Mechanics", "hardest", "Hyperelastic cantilever in large-deformation dynamics (Example 10)", "mfem",
        "Example Codes and Miniapps: Example 10", EX,
        "MFEM's beam-quad.mesh (listed on the page), 1 unit = 10 mm: the rectangle [0, 8] x [0, 1]; boundary attribute 1 is "
        "the edge x = 0.",
        "MFEM Example 10 with its default settings: the mesh refined uniformly twice, quadratic H1 space for deformation and "
        "velocity; neo-Hookean solid with shear modulus 0.25 and bulk modulus 5, unit density, Laplacian viscosity 0.01 "
        "(dv/dt = -M^-1 (H(x) + S v), dx/dt = v); edge x = 0 fixed; start from the undeformed configuration with velocity "
        "v = (-s x^2, s x^2 (8 - x)), s = 0.1/64; integrate to t = 300 with time step 3 using SDIRK33.",
        [("EE_t300", "-", "elastic energy at t = 300"), ("KE_t300", "-", "kinetic energy at t = 300")],
        ["finite-strain dynamics", "Newton inside implicit time stepping", "viscous damping"], tol=0.05, kind="2-D domain", geo=beam_geo, example_ref={"EE_t300": 0.0119584, "KE_t300": 0.000784203},
        notes=[mfem_note, "Reference: ex10 run as shipped (no options) prints these energies at step 100, t = 300."]))
    add(task(72, "Solid Mechanics", "hardest", "Incompressible neo-Hookean cantilever (Example 19)", "mfem",
        "Example Codes and Miniapps: Example 19", EX,
        "MFEM's beam-tet.mesh: the box [0, 8] x [0, 1] x [0, 1] (1 unit = 10 mm); boundary attribute 1 = face x = 0, "
        "attribute 2 = face x = 8.",
        "MFEM Example 19 with its default settings: quadratic displacement, linear pressure; quasi-static incompressible "
        "neo-Hookean solid (shear modulus 1); face x = 0 fixed; face x = 8 held at the displacement (0, 0.25 x, 0) = (0, 2, 0); "
        "Newton with relative tolerance 1e-4.",
        [("uy_mid", "-", "vertical displacement of (4, 0.5, 0.5)")], ["saddle-point (u, p) system", "large rotation"],
        geo=beam_geo, notes=[mfem_note, "The example prints no solution values, so this task has no reference answer."]))
    return T


DRAFT_REMOVED = ("FEMCAD-007, 009, 010, 012, 013, 018, 024, 025, 027, 028, 029, 030, 035, 037, 039, 040, 041 and 045-053 "
                 "(domains, eggs, tissue, rooms and textbook spheres without a CAD drawing of an engineering part)")


def readme(rows, awaiting=()) -> str:
    by_cat = {c: sum(r["category"] == c for r in rows) for c in CATEGORIES}
    status = {k: [r["id"] for r in rows if r["reference"]["status"] == k] for k in ("exact", "page", "example")}
    set_here = [r["id"] for r in rows if r["analysis_source"] != "source page"]
    lines = ["# FEMCAD-Hard v1", "",
             f"{len(rows)} CAD + FEM tasks on engineering parts, built only from pages crawled on Wolfram's FEM documentation and "
             "mfem.org. Each asks a model to build an FEM-ready CAD model of the part (CadQuery -> part.step) and run the "
             "finite-element analysis set out on the source page (fem.py -> results.json). Every task's part is drawn on its "
             "source page (CAD render, dimensioned drawing or part mesh; see `figures`). Prompts are self-contained; values the "
             "scraped code does not contain are set in the task and listed in `provenance_notes`.", "",
             "## Categories (from https://www.wolfram.com/language/core-areas/fem/)", "",
             "| Category | Tasks |", "|---|---|"] + [f"| {c} | {n} |" for c, n in by_cat.items()] + [
             "", "Mass Transport and System Physics are empty: the crawled pages model those physics only on plain domains "
             "(rectangles, rooms), not on engineering parts.", "",
             f"Tiers: hard {sum(r['tier'] == 'hard' for r in rows)}, complex {sum(r['tier'] == 'complex' for r in rows)}, "
             f"hardest {sum(r['tier'] == 'hardest' for r in rows)}. Sources: Wolfram {sum(r['source']['site'] == 'wolfram' for r in rows)}, "
             f"mfem.org {sum(r['source']['site'] == 'mfem' for r in rows)}. 3-D solids "
             f"{sum(r['model_kind'] == '3-D solid' for r in rows)}, 2-D domains {sum(r['model_kind'] == '2-D domain' for r in rows)}.", "",
             "## FEM problems", "",
             f"{len(rows) - len(set_here)} tasks pose the FEM problem their source page solves (when the part is built on a "
             "companion page, e.g. the OpenCascadeLink Book Shelf Bracket analysed in the Solid Mechanics tutorial, "
             "`source.geometry_page` names it). " + f"{len(set_here)} ({', '.join(set_here)}) take their part from a CAD-only "
             "page and state an analysis set here (`analysis_source`).", "",
             "## Sources and scraping", "",
             "* Wolfram: crawled from the FEM core-area page into the PDE-model collection and tutorials, the FEMDocumentation "
             "tutorials and the OpenCascadeLink tutorials it links (robots.txt honoured): `scripts/scrape_wolfram_fem.py`, "
             "manifest `wolfram-sources.json`.",
             "* MFEM: crawl of mfem.org (no robots.txt served): `scripts/scrape_mfem_site.py`, manifest `mfem-sources.json`.",
             "* Raw pages stay in git-ignored `tmp/`; only URLs, hashes, dates and extracted parameters are kept here. Each task "
             "records its page URL and the hash of the page it was built from.", "",
             "## References", "",
             f"* exact (closed form computed by the build script): {', '.join(status['exact']) or 'none'}.",
             f"* page (value stated on the source page, e.g. its verification test): {', '.join(status['page']) or 'none'}.",
             f"* example (printed by the MFEM example itself, run as shipped from the MFEM 4.10 release): "
             f"{', '.join(status['example']) or 'none'}.",
             "", "Every task in the dataset has a reference answer for every output (closed form or stated on the source page; "
             "nothing is solved here) and a showcase-style picture of its part crawled from the source pages (a CAD render or a "
             "meshed-part render, like the FEM page's carousel; schematic line drawings alone do not count). Tasks missing "
             "either are left out"
             + (f": {', '.join(awaiting)}." if awaiting else " (none at present)."), "",
             "## CAD drawings", "",
             "`figures` lists the source pages' drawings of the task's part: CAD renders (`cad`), 2-D outlines and dimensioned "
             "cross-sections (`drawing`) and meshes of the part (`part-mesh`); `category_showcase` adds the CAD and meshed-part "
             "images of the Wolfram FEM page's carousel for the category. Every crawled image was reviewed by eye "
             "(`figure-curation.json`): PDE solution plots, graphs, abstract domains, set-up schematics and screenshots were "
             "dropped, and images on pages with several parts are assigned to the task whose part they show. Images are "
             "Wolfram's / MFEM's: referenced by URL, local copies in git-ignored `tmp/femcad-figures/`.", "",
             f"Draft tasks removed: {DRAFT_REMOVED}.", "",
             "## \"Cannot solve\" filter", "",
             "Not yet run (`pilot.status`). Run the available models on every task, keep the ones they fail and report pass rates.", "",
             "Built by `scripts/build_femcad_hard_dataset.py`."]
    return "\n".join(lines) + "\n"


def attach_figures(rows) -> None:
    """Source-page figures (collect_source_figures.py) and the FEM page's category showcase (crawl_wolfram_fem_showcase.py)."""
    figs = json.loads((OUT / "figures.json").read_text())["pages"] if (OUT / "figures.json").exists() else {}
    show = json.loads((OUT / "fem-showcase.json").read_text())["categories"] if (OUT / "fem-showcase.json").exists() else {}
    # Only CAD drawings of engineering parts survive (figure-curation.json); PDE solution plots, graphs, abstract domains,
    # 2-D meshes and screenshots are dropped.
    cur = json.loads((OUT / "figure-curation.json").read_text())
    keep, assign = cur["keep"], cur.get("assign", {})
    for r in rows:
        pages = [r["source"]["url"]] + ([r["source"]["geometry_page"]["url"]] if "geometry_page" in r["source"] else [])
        seen, r["figures"] = set(), []
        for page in pages:
            for f in figs.get(page.rstrip("/").replace("http://", "https://"), []):
                if f["url"] in keep and f["url"] not in seen and r["id"] in assign.get(f["url"], [r["id"]]):
                    seen.add(f["url"])
                    r["figures"].append(dict(url=f["url"], kind=keep[f["url"]], caption=f["caption"], local=f.get("local")))
        r["category_showcase"] = [dict(url=f["url"], kind=keep[f["url"]], local=f.get("local"))
                                  for f in show.get(r["category"], []) if f["url"] in keep]


def viewer(rows) -> str:
    import html as h
    keep = json.loads((OUT / "figure-curation.json").read_text())["keep"]
    show = json.loads((OUT / "fem-showcase.json").read_text())["categories"] if (OUT / "fem-showcase.json").exists() else {}
    show = {c: [f for f in fs if f["url"] in keep] for c, fs in show.items()}
    def img(f, cap=""):
        return (f'<figure><a href="{h.escape(f["url"])}"><img loading="lazy" src="../../{h.escape(f["local"])}"></a>'
                f'<figcaption>{cap}</figcaption></figure>') if f.get("local") else ""
    parts = ["<h1>FEMCAD-Hard v1: engineering CAD drawings</h1><p>CAD renders, part drawings and part meshes only (PDE solution "
             "plots and graphs removed). Images belong to Wolfram Research and the MFEM project; local copies for research use, "
             "linked to their sources.</p><h2>Wolfram FEM page: category showcase</h2>"]
    for cat in CATEGORIES:
        if not show.get(cat):
            continue
        parts.append(f'<section><h3>{cat}</h3><div class="g">' + "".join(img(f) for f in show.get(cat, [])) + "</div></section>")
    parts.append("<h2>Tasks</h2>")
    for r in rows:
        ims = "".join(img(f, f"<b>{f['kind']}</b> {h.escape(f['caption'])}") for f in r["figures"])
        parts.append(f'<section id="{r["id"]}"><h3>{r["id"]} · {h.escape(r["title"])}</h3><p>{r["category"]} · {r["tier"]} · '
                     f'<a href="{h.escape(r["source"]["url"])}">{h.escape(r["source"]["page"])}</a> · {len(r["figures"])} figures</p>'
                     f'<div class="g">{ims or "<i>no CAD drawing of an engineering part on the source page</i>"}</div></section>')
    css = ("body{font:14px system-ui;margin:24px auto;max-width:1200px;padding:0 16px;background:#f5f6f7;color:#18212b}"
           "section{background:#fff;border:1px solid #dde;border-radius:8px;padding:12px 16px;margin:12px 0}h3{font-size:16px;margin:0 0 4px}"
           ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}figure{margin:0}"
           "img{width:100%;height:190px;object-fit:contain;background:#fafafa;border:1px solid #eee}figcaption{font-size:12px;color:#555}")
    return f"<!doctype html><meta charset=utf-8><title>FEMCAD-Hard diagrams</title><style>{css}</style>" + "".join(parts)


def main() -> None:
    every = tasks()
    ids = [r["id"] for r in every]
    assert len(ids) == len(set(ids))
    attach_figures(every)
    # a showcase-style picture of the part: a CAD render or a meshed-part render (schematic line drawings alone do not count)
    drawn = lambda r: any(f["kind"] in ("cad", "part-mesh") for f in r["figures"])  # noqa: E731
    keep = lambda r: drawn(r) and r["reference"]["status"] != "pending"  # noqa: E731 - reference drawing and reference answer
    rows = [r for r in every if keep(r)]
    awaiting = [r["id"] for r in every if not keep(r)]
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "tmp/femcad-figures").mkdir(parents=True, exist_ok=True)
    (ROOT / "tmp/femcad-figures/index.html").write_text(viewer(rows))
    (OUT / "tasks.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    (OUT / "README.md").write_text(readme(rows, awaiting))
    print(json.dumps(dict(tasks=len(rows), categories={c: sum(r["category"] == c for r in rows) for c in CATEGORIES},
                          tiers={t: sum(r["tier"] == t for r in rows) for t in ("hard", "complex", "hardest")},
                          exact={r["id"]: {q["key"]: q["reference"] for q in r["qois"]} for r in rows if r["reference"]["status"] == "exact"},
                          missing_hash=[r["id"] for r in rows if not r["source"]["scraped_sha256"]],
                          figures=sum(len(r["figures"]) for r in rows), tasks_without_figures=[r["id"] for r in rows if not r["figures"]]), indent=1))


if __name__ == "__main__":
    main()
