#!/usr/bin/env python3
"""Generate configs/prompts/engineering_v2_physics.json.

Each prompt asks for a drawing whose labels must carry physics results. Expected
values are computed here (closed-form solutions) so the number_near checks test
whether the model did the physics, not whether it drew something plausible.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

cases = []


def case(id_, prompt, checks, kind, ground_truth):
    cases.append({"id": id_, "kind": kind, "prompt": prompt, "ground_truth": ground_truth, "checks": checks})


def near(value, tol=0.02):
    values = value if isinstance(value, list) else [value]
    return {"number_near": [round(v, 4) for v in values], "tol": tol}


VIEWBOX = {"root_attr": "viewBox"}

# 1. Cantilever deflection -----------------------------------------------------
E, b, h, L, P = 200e9, 0.05, 0.10, 2.0, 5000.0
I = b * h**3 / 12
d_tip = P * L**3 / (3 * E * I) * 1e3
d_mid = P * (L / 2) ** 2 * (3 * L - L / 2) / (6 * E * I) * 1e3
sigma = (P * L) * (h / 2) / I / 1e6
case(
    "cantilever_deflection",
    "Steel cantilever beam, length 2 m, rectangular section 50 mm wide x 100 mm deep, E = 200 GPa, "
    "point load 5 kN at the free tip. Draw the undeformed beam and the deflected shape (exaggerated) "
    "from Euler-Bernoulli theory, with the fixed support symbol. Compute and label: the tip deflection in mm, "
    "the deflection at mid-length in mm, and the maximum bending stress at the root in MPa. Show the formula used.",
    [near(d_tip), near(d_mid), near(sigma), {"tag": "text", "min": 4}, {"tag": "path", "min": 1}, VIEWBOX],
    "closed_form",
    {"tip_mm": d_tip, "mid_mm": d_mid, "sigma_root_MPa": sigma},
)

# 2. Composite wall conduction ---------------------------------------------------
layers = [("plaster", 0.02, 0.5), ("insulation", 0.05, 0.04), ("brick", 0.10, 0.7)]  # inside -> outside
T_in, T_out = 20.0, -5.0
R = sum(t / k for _, t, k in layers)
q = (T_in - T_out) / R
T = [T_in]
for _, t, k in layers:
    T.append(T[-1] - q * t / k)
case(
    "composite_wall_conduction",
    "One-dimensional steady heat conduction through a three-layer wall, inside to outside: 20 mm plaster "
    "(k = 0.5 W/m.K), 50 mm insulation (k = 0.04 W/m.K), 100 mm brick (k = 0.7 W/m.K). Inside surface 20 C, "
    "outside surface -5 C. Draw the wall section to scale with the layers hatched differently and, aligned above "
    "it, the temperature profile through the wall (piecewise linear). Compute and label the heat flux in W/m2 "
    "and the temperature at each of the two internal interfaces in C.",
    [near(q), near(T[1], 0.01), near(T[2], 0.05), {"tag": "text", "min": 5}, {"any_tag": ["polyline", "path", "line"], "min": 3}, VIEWBOX],
    "closed_form",
    {"q_W_m2": q, "T_plaster_insulation": T[1], "T_insulation_brick": T[2]},
)

# 3. Kirsch stress concentration -----------------------------------------------
s0, a = 100.0, 10.0
def s_theta(r):  # along theta = 90 deg (transverse axis)
    return s0 / 2 * (2 + (a / r) ** 2 + 3 * (a / r) ** 4)
case(
    "plate_hole_kirsch",
    "A large thin plate with a central circular hole of radius 10 mm under remote uniaxial tension of 100 MPa "
    "along x. Draw the plate with the hole and the applied stress arrows, and plot the tangential stress "
    "sigma_theta along the y-axis from the hole edge out to 4 radii (Kirsch solution). Label the stress at the "
    "hole edge on the y-axis, at 2 radii, and the stress at the hole edge on the x-axis (theta = 0). Mark the "
    "stress concentration factor.",
    [near(s_theta(a)), near(s_theta(2 * a)), near(-s0), near(3.0, 0.01), {"tag": "text", "min": 4}, {"tag": "circle", "min": 1}, VIEWBOX],
    "closed_form",
    {"sigma_edge_y": s_theta(a), "sigma_2a": s_theta(2 * a), "sigma_edge_x": -s0, "Kt": 3.0},
)

# 4. Truss member forces ---------------------------------------------------------
span, height, W = 8.0, 3.0, 24.0
Lm = math.hypot(span / 2, height)
R_ = W / 2
F_AC = R_ * Lm / height  # compression
F_AB = F_AC * (span / 2) / Lm  # tension
case(
    "truss_member_forces",
    "A triangular truss: pin support A at (0, 0), roller support B at (8 m, 0), apex C at (4 m, 3 m), members "
    "AB, AC, BC. A vertical load of 24 kN acts at C. Draw the truss with supports and load, compute the reactions "
    "and every member force by the method of joints, and label each member with its force in kN and T for "
    "tension or C for compression. Include a free-body diagram of joint C.",
    [near(R_), near(F_AC), near(F_AB), {"text_contains": "kN"}, {"tag": "text", "min": 5}, VIEWBOX],
    "closed_form",
    {"reaction_kN": R_, "F_AC_kN_C": F_AC, "F_BC_kN_C": F_AC, "F_AB_kN_T": F_AB},
)

# 5. Mohr's circle ------------------------------------------------------------------
sx, sy, txy = 80.0, -20.0, 30.0
c = (sx + sy) / 2
Rm = math.hypot((sx - sy) / 2, txy)
s1, s2 = c + Rm, c - Rm
theta_p = math.degrees(math.atan2(2 * txy, sx - sy)) / 2
case(
    "mohr_circle",
    "Plane stress state: sigma_x = 80 MPa, sigma_y = -20 MPa, tau_xy = 30 MPa. Draw Mohr's circle to scale with "
    "labelled sigma and tau axes, the plotted points for the x and y faces, the centre and radius, and label "
    "the principal stresses sigma_1 and sigma_2, the maximum in-plane shear stress, and the principal angle "
    "theta_p in degrees. Also draw the element rotated to the principal orientation.",
    [near(s1), near(s2), near(Rm), near(theta_p, 0.03), {"tag": "circle", "min": 1}, {"tag": "text", "min": 5}, VIEWBOX],
    "closed_form",
    {"sigma1": s1, "sigma2": s2, "tau_max": Rm, "theta_p_deg": theta_p},
)

# 6. Cantilever mode shapes -----------------------------------------------------
E, rho, bb, Lb = 200e9, 7850.0, 0.01, 1.0
Ib, Ab = bb**4 / 12, bb**2
betaL = [1.87510407, 4.69409113, 7.85475744]
freqs = [(bl / Lb) ** 2 / (2 * math.pi) * math.sqrt(E * Ib / (rho * Ab)) for bl in betaL]
case(
    "cantilever_mode_shapes",
    "First three bending mode shapes of a uniform steel cantilever (E = 200 GPa, density 7850 kg/m3), "
    "length 1 m, square section 10 mm x 10 mm. Draw the three normalised mode shapes stacked and aligned, with "
    "the clamped end on the left and node positions marked. Label each mode with its beta_n*L eigenvalue and "
    "its natural frequency in Hz.",
    [near(betaL[0], 0.005), near(betaL[1], 0.005), near(betaL[2], 0.005), near(freqs[0], 0.03), near(freqs[1], 0.03), near(freqs[2], 0.03), {"tag": "path", "min": 3}, VIEWBOX],
    "closed_form",
    {"betaL": betaL, "f_Hz": freqs},
)

# 7. Hagen-Poiseuille -------------------------------------------------------------
D, mu, dpdx, rho_oil = 0.02, 0.1, 200.0, 900.0
Rp = D / 2
u_max = dpdx * Rp**2 / (4 * mu)
u_mean = u_max / 2
Q = u_mean * math.pi * Rp**2
Re = rho_oil * u_mean * D / mu
case(
    "poiseuille_profile",
    "Fully developed laminar flow of oil (viscosity 0.1 Pa.s, density 900 kg/m3) in a 20 mm diameter pipe with "
    "a pressure gradient of 200 Pa/m. Draw a longitudinal section of the pipe with the parabolic velocity "
    "profile as velocity arrows and the profile envelope curve, and the linear shear-stress distribution beside "
    "it. Compute and label the centreline velocity in m/s, the mean velocity in m/s, the volumetric flow rate in "
    "litres per minute, and the Reynolds number.",
    [near(u_max), near(u_mean), near([Q * 60000, Q * 1e6, Q * 3.6e6, Q * 1e3], 0.03), near(Re, 0.05), {"tag": "text", "min": 4}, {"tag": "path", "min": 1}, VIEWBOX],
    "closed_form",
    {"u_max": u_max, "u_mean": u_mean, "Q_L_min": Q * 60000, "Re": Re},
)

# 8. RC Bode plot -------------------------------------------------------------------
Rr, Cc = 10e3, 100e-9
fc = 1 / (2 * math.pi * Rr * Cc)
case(
    "rc_bode_plot",
    "Bode magnitude and phase plots of the first-order RC low-pass filter with R = 10 kOhm and C = 100 nF, "
    "from 1 Hz to 100 kHz on a log frequency axis. Draw both plots stacked and aligned with gridlines at each "
    "decade. Label the corner frequency in Hz, the gain at the corner in dB, the high-frequency slope in "
    "dB/decade, and the phase at the corner in degrees.",
    [near(fc), near(-3.01, 0.05), near(-20, 0.01), near(-45, 0.01), {"tag": "text", "min": 6}, {"any_tag": ["path", "polyline"], "min": 2}, VIEWBOX],
    "closed_form",
    {"fc_Hz": fc, "gain_fc_dB": -3.01, "slope_dB_dec": -20, "phase_fc_deg": -45},
)

# 9. UDL beam ---------------------------------------------------------------------
w, Lu = 10.0, 8.0
case(
    "udl_beam_shear_moment",
    "Simply supported beam of span 8 m carrying a uniformly distributed load of 10 kN/m over its full length. "
    "Draw the loaded beam, the shear force diagram (linear) and the bending moment diagram (parabolic), stacked "
    "and aligned. Label the reactions, the maximum shear force, and the maximum bending moment with its "
    "location.",
    [near(w * Lu / 2), near(w * Lu**2 / 8), {"tag": "text", "min": 5}, {"any_tag": ["path", "polygon", "polyline"], "min": 2}, VIEWBOX],
    "closed_form",
    {"reaction_kN": w * Lu / 2, "Mmax_kNm": w * Lu**2 / 8},
)

# 10. Pin fin -----------------------------------------------------------------------
kf, Df, Lf, hf, Tb, Tinf = 200.0, 0.005, 0.05, 50.0, 100.0, 20.0
Pf, Af = math.pi * Df, math.pi * Df**2 / 4
m = math.sqrt(hf * Pf / (kf * Af))
T_tip = Tinf + (Tb - Tinf) / math.cosh(m * Lf)
eta = math.tanh(m * Lf) / (m * Lf)
q_fin = math.sqrt(hf * Pf * kf * Af) * (Tb - Tinf) * math.tanh(m * Lf)
case(
    "pin_fin_temperature",
    "Aluminium pin fin (k = 200 W/m.K), diameter 5 mm, length 50 mm, base at 100 C, ambient 20 C, convection "
    "coefficient 50 W/m2.K, adiabatic tip. Draw the fin in section with convection arrows and, aligned below it, "
    "the temperature distribution along the fin from the one-dimensional fin equation. Label the fin parameter "
    "m in 1/m, the tip temperature in C, the fin efficiency in percent, and the heat dissipated in W.",
    [near(m), near(T_tip, 0.01), near(eta * 100, 0.02), near(q_fin, 0.03), {"tag": "text", "min": 4}, {"tag": "path", "min": 1}, VIEWBOX],
    "closed_form",
    {"m_per_m": m, "T_tip_C": T_tip, "eta_pct": eta * 100, "q_W": q_fin},
)

# 11. Euler buckling ---------------------------------------------------------------
dc, Lc = 0.04, 3.0
Ic = math.pi * dc**4 / 64
Ac = math.pi * dc**2 / 4
Pcr = math.pi**2 * E * Ic / Lc**2
lam = Lc / (dc / 4)
scr = Pcr / Ac / 1e6
case(
    "euler_buckling",
    "Pinned-pinned steel column (E = 200 GPa), solid circular section 40 mm diameter, length 3 m. Draw the "
    "straight column with pin symbols and the first Euler buckling mode shape (half sine) beside it. Compute and "
    "label the critical load in kN, the slenderness ratio, and the critical stress in MPa.",
    [near([Pcr / 1e3, Pcr]), near(lam, 0.01), near(scr), {"tag": "text", "min": 3}, {"tag": "path", "min": 1}, VIEWBOX],
    "closed_form",
    {"Pcr_kN": Pcr / 1e3, "slenderness": lam, "sigma_cr_MPa": scr},
)

# 12. Laplace isotherms (field problem) ---------------------------------------------
case(
    "laplace_plate_isotherms",
    "Two-dimensional steady heat conduction in a 1 m x 1 m square plate with no internal generation. The top "
    "edge is held at 100 C and the other three edges at 0 C. Draw the plate and the isotherms at 10, 20, 40, 60 "
    "and 80 C as smooth curves that satisfy the boundary conditions (they must meet the top edge and stay off "
    "the cold edges), label each isotherm, and label the exact temperature at the plate centre.",
    [near(25.0, 0.01), {"tag": "text", "min": 5}, {"tag": "path", "min": 4}, VIEWBOX],
    "field_solver",
    {"T_centre_C": 25.0, "note": "series solution; centre exactly 25 C by symmetry"},
)

# 13. Potential flow past a cylinder (field problem) ---------------------------------
case(
    "potential_flow_cylinder",
    "Ideal (potential) flow of a uniform stream U = 1 m/s past a circular cylinder of radius 0.5 m, no "
    "circulation. Draw at least eight streamlines that divide correctly around the cylinder (the dividing "
    "streamline meets the surface at the stagnation points), mark both stagnation points, label the maximum "
    "surface speed in m/s and where it occurs, and label the minimum pressure coefficient Cp on the surface.",
    [near(-3.0, 0.01), near(2.0, 0.01), {"text_contains": "stagnation"}, {"tag": "path", "min": 8}, {"tag": "circle", "min": 1}, VIEWBOX],
    "field_solver",
    {"u_max": 2.0, "Cp_min": -3.0},
)

# 14. I-beam shear stress -----------------------------------------------------------
V = 100e3
bf, tf, d_, tw = 146.0, 9.1, 258.0, 6.1
hw = d_ - 2 * tf
Iw = (bf * d_**3 - (bf - tw) * hw**3) / 12  # mm^4
Q_flange = bf * tf * (d_ / 2 - tf / 2)
Q_na = Q_flange + tw * (hw / 2) * (hw / 4)
tau_na = V * Q_na / (Iw * tw)  # N/mm^2 = MPa
tau_junction_web = V * Q_flange / (Iw * tw)
tau_junction_flange = V * Q_flange / (Iw * bf)
case(
    "ibeam_shear_stress",
    "W250x33 steel I-beam section: depth 258 mm, flange width 146 mm, flange thickness 9.1 mm, web thickness "
    "6.1 mm, carrying a vertical shear force of 100 kN. Draw the section and, beside it, the transverse shear "
    "stress distribution over the depth from tau = VQ/(I t): parabolic in the web with the jump at the "
    "web-flange junction. Compute and label the second moment of area in mm4, the maximum shear stress at the "
    "neutral axis in MPa, and the shear stress on the web side of the junction in MPa.",
    [near(tau_na), near(tau_junction_web), near([Iw, Iw / 1e6, Iw / 1e4], 0.03), {"tag": "text", "min": 4}, {"any_tag": ["path", "polygon", "polyline"], "min": 2}, VIEWBOX],
    "closed_form",
    {"I_mm4": Iw, "tau_NA_MPa": tau_na, "tau_junction_web_MPa": tau_junction_web, "tau_junction_flange_MPa": tau_junction_flange},
)

# 15. Parallel-plate capacitor field (field problem) ---------------------------------
V0, gap = 100.0, 0.02
Efield = 2 * V0 / gap
case(
    "capacitor_fringe_field",
    "Two parallel conducting plates 100 mm long and 20 mm apart at +100 V and -100 V, in air. Draw the plates "
    "and the equipotential lines at -75, -50, -25, 0, +25, +50 and +75 V, including realistic fringing "
    "curvature near the plate ends, plus at least six electric field lines perpendicular to the equipotentials. "
    "Label the uniform field strength between the plates in kV/m and mark the 0 V equipotential.",
    [near([Efield / 1e3, Efield, Efield / 1e5], 0.01), {"tag": "text", "min": 7}, {"tag": "path", "min": 8}, VIEWBOX],
    "field_solver",
    {"E_kV_m": Efield / 1e3},
)

# 16. Thick cylinder (Lame) ---------------------------------------------------------
ri, ro, pi_ = 50.0, 100.0, 50.0
s_t_in = pi_ * (ro**2 + ri**2) / (ro**2 - ri**2)
s_t_out = 2 * pi_ * ri**2 / (ro**2 - ri**2)
case(
    "thick_cylinder_lame",
    "Thick-walled cylinder, inner radius 50 mm, outer radius 100 mm, internal pressure 50 MPa, no external "
    "pressure. Draw the cross-section and plot the radial and tangential (hoop) stress distributions through the "
    "wall thickness from Lame's equations. Label the hoop stress at the inner and outer surfaces in MPa and the "
    "radial stress at the inner and outer surfaces in MPa.",
    [near(s_t_in), near(s_t_out), near(-pi_, 0.01), {"tag": "text", "min": 4}, {"tag": "circle", "min": 2}, {"tag": "path", "min": 2}, VIEWBOX],
    "closed_form",
    {"hoop_inner": s_t_in, "hoop_outer": s_t_out, "radial_inner": -pi_, "radial_outer": 0.0},
)

# 17. Shaft torsion ---------------------------------------------------------------------
ds, Ts, G, Ls = 0.05, 2000.0, 80e9, 1.0
J = math.pi * ds**4 / 32
tau_max = Ts * (ds / 2) / J / 1e6
phi = math.degrees(Ts * Ls / (G * J))
case(
    "shaft_torsion",
    "Solid steel shaft (G = 80 GPa), diameter 50 mm, length 1 m, transmitting a torque of 2 kN.m. Draw the shaft "
    "with the applied torque arrows, a cross-section showing the linear shear-stress distribution from the "
    "centre to the surface, and the angle of twist between the ends. Compute and label the polar second moment "
    "of area in mm4, the maximum shear stress in MPa, and the total angle of twist in degrees.",
    [near(tau_max), near(phi, 0.03), near([J * 1e12, J * 1e6, J * 1e8], 0.03), {"tag": "text", "min": 4}, {"tag": "circle", "min": 1}, VIEWBOX],
    "closed_form",
    {"J_mm4": J * 1e12, "tau_max_MPa": tau_max, "twist_deg": phi},
)

# 18. RC step response ---------------------------------------------------------------
tau_rc = Rr * Cc * 1e3  # ms
case(
    "rc_step_response",
    "Step response of the RC low-pass filter with R = 10 kOhm and C = 100 nF to a 0 to 5 V input step. Draw the "
    "input step and the capacitor voltage versus time from 0 to 6 ms on a labelled, gridded plot. Label the time "
    "constant in ms, the voltage reached at one time constant in V and as a percentage, and the times to reach "
    "95 percent and 99 percent of the final value in ms.",
    [near(tau_rc, 0.01), near(63.2, 0.01), near(3.16, 0.03), near(3.0, 0.03), near(4.6, 0.03), {"tag": "text", "min": 5}, {"tag": "path", "min": 1}, VIEWBOX],
    "closed_form",
    {"tau_ms": tau_rc, "V_tau": 5 * (1 - math.exp(-1)), "pct_tau": 63.2, "t95_ms": -math.log(0.05) * tau_rc, "t99_ms": -math.log(0.01) * tau_rc},
)

# 19. Von Mises map on the L-bracket (field problem) ----------------------------------
# Upright is 80 wide x 8 thick, bent by the horizontal load: Z = b t^2 / 6. Lever arm either to the
# flange top (52 mm) or to the flange bottom (60 mm) -- both are defensible, accept either.
Z_up = 80 * 8**2 / 6
sigma_root_52 = 2000 * 52 / Z_up
sigma_root_60 = 2000 * 60 / Z_up
case(
    "lbracket_von_mises",
    "The L-shaped steel bracket (80 mm wide, 60 mm tall, 40 mm deep, 8 mm thick) is bolted down through its "
    "base flange and loaded with 2 kN horizontally at the top edge of the upright. Draw the bracket in side "
    "elevation with a colour-mapped von Mises stress field as you would expect from a finite element analysis: "
    "a stress concentration at the inner corner, low stress at the free tip, and a legend with a MPa scale. "
    "Estimate and label the peak stress in MPa and state the bending stress at the base of the upright from "
    "simple beam theory as a check.",
    [near([sigma_root_52, sigma_root_60], 0.05), {"text_contains": "MPa"}, {"any_tag": ["linearGradient", "radialGradient", "path", "polygon"], "min": 6}, {"tag": "text", "min": 4}, VIEWBOX],
    "field_solver",
    {"beam_theory_sigma_MPa_h52": sigma_root_52, "beam_theory_sigma_MPa_h60": sigma_root_60, "note": "M/Z with Z = 80 x 8^2 / 6; lever arm 52 or 60 mm"},
)

# 20. Projectile-free: dam hydrostatic pressure ---------------------------------------
Hd, gam = 6.0, 9.81
F = 0.5 * gam * Hd**2  # kN per m width
case(
    "dam_hydrostatic",
    "A vertical concrete dam face retains fresh water 6 m deep. Draw the dam and the water, the triangular "
    "hydrostatic pressure distribution on the face with pressure arrows, the resultant force vector at its "
    "point of action, and dimension the depth. Compute and label the pressure at the base in kPa, the "
    "resultant force per metre width in kN/m, and the depth of the centre of pressure below the surface in m.",
    [near(gam * Hd), near(F), near(2 * Hd / 3, 0.01), {"tag": "text", "min": 4}, {"any_tag": ["polygon", "path"], "min": 1}, VIEWBOX],
    "closed_form",
    {"p_base_kPa": gam * Hd, "F_kN_per_m": F, "centre_of_pressure_m": 2 * Hd / 3},
)

out = {
    "version": 2,
    "description": "Physics-bearing engineering prompts. Labels must carry computed results; ground_truth holds the closed-form values the number_near checks test against. kind=field_solver marks problems that need a field solution (FEM/PINN) to draw faithfully.",
    "cases": cases,
}
path = Path(__file__).resolve().parents[1] / "configs" / "prompts" / "engineering_v2_physics.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote {path} ({len(cases)} cases, {sum(len(c['checks']) for c in cases)} checks)")
for c in cases:
    gt = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in c["ground_truth"].items()}
    print(f"  {c['id']:28s} {c['kind']:12s} {gt}")
