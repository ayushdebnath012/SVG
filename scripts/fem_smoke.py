"""FEM smoke test for engineering_v4 (feasibility of build steps 5 and 6).

Test 1  Laplace, L-shaped plate, Dirichlet.  scikit-fem (P2) against the finite-difference
        reference in runs/reference-v3.  Reports the nodal difference at the FD grid points, the
        field-fidelity epsilon of the FD isolines evaluated on the FEM field (same definition as
        scripts/field_fidelity.py: mean |u - level| in percentage points of the field range), and
        the two-resolution floor (h vs h/2).
Test 2  Plane stress, quarter plate with a central circular hole under remote uniaxial tension.
        Hoop stress around the hole against Kirsch sigma(1 - 2 cos 2theta); sigma_xx along the
        transverse axis against Kirsch; peak Kt against 3.0 (infinite plate) and Howland/Pilkey
        (finite width).

Outputs runs/fem-smoke/summary.json, lshape.png, kirsch.png.
Run:    .venv/bin/python scripts/fem_smoke.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from skfem import (CellBasis, ElementTriP1, ElementTriP2, ElementVector, FacetBasis, MeshTri, asm,
                   condense, solve)
from skfem.models.elasticity import lame_parameters, linear_elasticity
from skfem.models.poisson import laplace
from skfem.assembly import LinearForm

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "runs" / "reference-v3"
OUT = ROOT / "runs" / "fem-smoke"


# ----------------------------------------------------------------------------- helpers

def oriented(p: np.ndarray, t: np.ndarray) -> MeshTri:
    """Build a MeshTri with counter-clockwise triangles."""
    a = p[:, t[0]]
    b = p[:, t[1]]
    c = p[:, t[2]]
    area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    t = t.copy()
    flip = area < 0
    t[1, flip], t[2, flip] = t[2, flip], t[1, flip]
    return MeshTri(p, t)


def probe(basis: CellBasis, u: np.ndarray, pts: np.ndarray, chunk: int = 1000) -> np.ndarray:
    """Evaluate the FEM field at points (2, n).  Chunked: scikit-fem's element finder tests every
    candidate element against every query point at once, which is O(points x elements) memory."""
    out = np.empty(pts.shape[1])
    for i in range(0, pts.shape[1], chunk):
        out[i:i + chunk] = basis.probes(pts[:, i:i + chunk]) @ u
    return out


def nudge_into_lshape(pts: np.ndarray, d: float = 1e-7) -> np.ndarray:
    """Move points that sit exactly on the L-shape boundary a hair inside so the element finder
    never has to decide on a boundary point."""
    x = np.clip(pts[0], d, 1 - d)
    y = np.clip(pts[1], d, 1 - d)
    in_notch = (x >= 0.5 - d) & (y >= 0.5 - d)
    # push out of the notch along the axis that is closer to the notch edge
    dx, dy = x - 0.5, y - 0.5
    push_x = in_notch & (dx <= dy)
    push_y = in_notch & ~push_x
    x = np.where(push_x, 0.5 - d, x)
    y = np.where(push_y, 0.5 - d, y)
    return np.array([x, y])


# ----------------------------------------------------------------------------- test 1

def solve_lshape(n: int):
    """Laplace on the L-shape [0,1]^2 minus [0.5,1]^2. Left edge 100, all else 0 (as fd_reference)."""
    xs = np.linspace(0, 1, n + 1)
    m = MeshTri.init_tensor(xs, xs)
    cen = m.p[:, m.t].mean(axis=1)
    m = m.remove_elements(np.where((cen[0] > 0.5) & (cen[1] > 0.5))[0])
    basis = CellBasis(m, ElementTriP2())
    A = asm(laplace, basis)
    x = basis.zeros()
    loc = basis.doflocs
    left = np.isclose(loc[0], 0.0) & (loc[1] > 1e-9) & (loc[1] < 1 - 1e-9)
    x[left] = 100.0
    D = basis.get_dofs()  # every boundary dof; non-left ones stay 0
    t0 = time.perf_counter()
    u = solve(*condense(A, basis.zeros(), x=x, D=D))
    return m, basis, u, time.perf_counter() - t0


def test_lshape(summary: dict):
    z = np.load(REF / "laplace_L_shape.npz")
    fx, fy, ffield = z["x"], z["y"], z["field"]
    X, Y = np.meshgrid(fx, fy)
    interior = (X > 0) & (X < 1) & (Y > 0) & (Y < 1) & ~((X >= 0.5) & (Y >= 0.5)) & np.isfinite(ffield)
    pts = np.array([X[interior], Y[interior]])

    res = {}
    fields = {}
    for n in (80, 160):
        m, basis, u, dt = solve_lshape(n)
        fem_at_fd = probe(basis, u, pts)
        diff = fem_at_fd - ffield[interior]
        # the boundary value jumps 100 -> 0 at (0,0) and (0,1); both solvers are inaccurate there
        far = (np.hypot(pts[0], pts[1]) > 0.05) & (np.hypot(pts[0], pts[1] - 1) > 0.05)
        imax = int(np.abs(diff).argmax())
        res[n] = dict(ndofs=int(basis.N), solve_s=round(dt, 3),
                      max_abs_diff_pp=float(np.abs(diff).max()),
                      max_abs_diff_at=[float(pts[0, imax]), float(pts[1, imax])],
                      rms_diff_pp=float(np.sqrt(np.mean(diff ** 2))),
                      max_abs_diff_pp_excluding_jump_corners=float(np.abs(diff[far]).max()),
                      rms_diff_pp_excluding_jump_corners=float(np.sqrt(np.mean(diff[far] ** 2))))
        fields[n] = (basis, u)
        print(f"L-shape FEM n={n:4d}  dofs={basis.N:7d}  solve={dt:.2f}s  "
              f"vs FD: max|Δ|={np.abs(diff).max():.3f} pp at ({pts[0, imax]:.4f},{pts[1, imax]:.4f})  "
              f"rms={np.sqrt(np.mean(diff**2)):.3f} pp  | excluding 0.05 of the jump corners: max={np.abs(diff[far]).max():.3f} rms={np.sqrt(np.mean(diff[far]**2)):.3f} pp")

    # two-resolution floor: field at h vs h/2, evaluated at the same points
    b80, u80 = fields[80]
    b160, u160 = fields[160]
    floor = np.abs(probe(b80, u80, pts) - probe(b160, u160, pts))
    res["floor_h_vs_h2_pp"] = dict(max=float(floor.max()), mean=float(floor.mean()))
    print(f"L-shape two-resolution floor (h vs h/2): max {floor.max():.3f} pp, mean {floor.mean():.4f} pp")

    # epsilon of the FD isolines on the FEM field (same definition as field_fidelity.py)
    iso = json.loads((REF / "laplace_L_shape.isolines.json").read_text())
    eps, eps_far = {}, {}
    for level, segs in iso.items():
        s = np.asarray(segs)  # (nseg, 4) = x0, y0, x1, y1
        p = np.concatenate([s[:, :2], s[:, 2:]]).T
        vals = probe(b160, u160, nudge_into_lshape(p))
        err = np.abs(vals - float(level))  # range is 100 → pp
        far = (np.hypot(p[0], p[1]) > 0.05) & (np.hypot(p[0], p[1] - 1) > 0.05)
        eps[level] = float(err.mean())
        eps_far[level] = float(err[far].mean()) if far.any() else float("nan")
    res["eps_fd_isolines_on_fem_pp"] = eps
    res["eps_fd_isolines_on_fem_pp_excluding_jump_corners_0p05"] = eps_far
    print("epsilon of FD isolines on FEM field (pp):        " + ", ".join(f"{k}: {v:.3f}" for k, v in eps.items()))
    print("  same, excluding points within 0.05 of the two Dirichlet-jump corners: " + ", ".join(f"{k}: {v:.3f}" for k, v in eps_far.items()))
    summary["lshape"] = res

    # figure: FD isolines (red dashed) over FEM contours
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 5))
        gx = np.linspace(0, 1, 201)
        GX, GY = np.meshgrid(gx, gx)
        inside = ~((GX >= 0.5) & (GY >= 0.5))
        vals = np.full(GX.shape, np.nan)
        q = nudge_into_lshape(np.array([GX[inside], GY[inside]]))
        vals[inside] = probe(b160, u160, q)
        ax.contour(GX, GY, vals, levels=[10, 20, 30, 40, 50, 60, 80], colors="C0", linewidths=1.2)
        for level, segs in iso.items():
            s = np.asarray(segs)
            ax.plot([s[:, 0], s[:, 2]], [s[:, 1], s[:, 3]], color="C3", ls="--", lw=0.8)
        ax.plot([0, 1, 1, 0.5, 0.5, 0, 0], [0, 0, 0.5, 0.5, 1, 1, 0], "k-", lw=1)
        ax.set_aspect("equal"); ax.set_title("L-shape: FEM (blue) vs FD reference (red dashed)")
        fig.tight_layout(); fig.savefig(OUT / "lshape.png", dpi=150); plt.close(fig)
    except Exception as e:  # figure is a courtesy, never a failure
        print("figure skipped:", e)


# ----------------------------------------------------------------------------- test 2

def quarter_plate_mesh(a: float, W: float, n_s: int = 64, n_t: int = 96, beta: float = 3.5,
                       L: float | None = None) -> MeshTri:
    """Quarter plate [0,L]x[0,W] (L defaults to W) minus the quarter disc of radius a, meshed
    with Triangle (Shewchuk): 30-degree minimum angle, global area cap, and the fine polyline on
    the arc (n_t segments) drives local refinement at the hole.

    A structured polar O-grid was the first attempt.  It is fine for a square plate but produces
    sliver elements on elongated plates (net-section equilibrium was off by 8 percent at L = 8W
    and Kt drifted to 2.79), so unstructured meshing is the path for engineering_v4.  n_s and
    beta are accepted for call compatibility; n_s sets the far-field element size W / n_s * 3."""
    import triangle as tr
    L = W if L is None else L
    th = np.linspace(0, np.pi / 2, n_t + 1)
    arc = np.array([a * np.cos(th), a * np.sin(th)]).T                 # (a,0) → (0,a)
    pts = np.vstack([arc, [[0.0, W], [L, W], [L, 0.0]]])
    n = len(pts)
    seg = np.array([[i, i + 1] for i in range(n - 1)] + [[n - 1, 0]])
    h_far = 3.0 * W / n_s
    out = tr.triangulate({"vertices": pts, "segments": seg}, f"pq30a{h_far ** 2 / 2:.6f}")
    return oriented(np.ascontiguousarray(out["vertices"].T), np.ascontiguousarray(out["triangles"].T))


def test_kirsch(summary: dict, W_over_a: float = 10.0, n_s: int = 64, beta: float = 3.5, tag: str = "kirsch",
                L_over_a: float | None = None):
    """Quarter model of a 2L x 2W plate with a central hole of radius a under remote tension
    sigma along x.  L defaults to W (square plate).  Besides the Kirsch comparison, two checks
    that do not depend on any closed form: sigma_rr = 0 on the free hole surface, and the
    net-section force across x = 0 equals the applied force (equilibrium)."""
    E, nu, sigma = 200e3, 0.3, 100.0     # MPa, -, MPa
    a = 5.0                               # mm: hole radius
    W = W_over_a * a                      # mm: half-width of the plate (transverse to the load)
    L = W if L_over_a is None else L_over_a * a   # mm: half-length along the load
    lam3, mu = lame_parameters(E, nu)
    lam = 2 * lam3 * mu / (lam3 + 2 * mu)  # plane-stress Lamé parameter

    m = quarter_plate_mesh(a, W, n_s=n_s, n_t=96, beta=beta, L=L)
    vb = CellBasis(m, ElementVector(ElementTriP2()))
    K = asm(linear_elasticity(lam, mu), vb)

    right = m.facets_satisfying(lambda x: np.isclose(x[0], L))
    fb_right = FacetBasis(m, vb.elem, facets=right)

    @LinearForm
    def traction(v, w):
        return sigma * v[0]

    f = asm(traction, fb_right)
    Dx = vb.get_dofs(lambda x: np.isclose(x[0], 0.0)).all(["u^1"])
    Dy = vb.get_dofs(lambda x: np.isclose(x[1], 0.0)).all(["u^2"])
    D = np.unique(np.concatenate([Dx, Dy]))
    t0 = time.perf_counter()
    u = solve(*condense(K, f, D=D))
    dt = time.perf_counter() - t0

    def stress_at(fb: FacetBasis):
        g = np.asarray(fb.interpolate(u).grad)  # (2, 2, nf, nq): g[i, j] = d u_i / d x_j
        exx, eyy = g[0, 0], g[1, 1]
        exy = 0.5 * (g[0, 1] + g[1, 0])
        tr = exx + eyy
        return lam * tr + 2 * mu * exx, lam * tr + 2 * mu * eyy, 2 * mu * exy

    # hoop stress on the hole vs Kirsch
    hole = m.facets_satisfying(lambda x: np.hypot(x[0], x[1]) < a * 1.001)
    fb_hole = FacetBasis(m, vb.elem, facets=hole)
    xh = np.asarray(fb_hole.global_coordinates().value)
    th = np.arctan2(xh[1], xh[0]).ravel()
    sxx, syy, sxy = (s.ravel() for s in stress_at(fb_hole))
    s_tt = sxx * np.sin(th) ** 2 + syy * np.cos(th) ** 2 - 2 * sxy * np.sin(th) * np.cos(th)
    kirsch_tt = sigma * (1 - 2 * np.cos(2 * th))
    hoop_err = np.abs(s_tt - kirsch_tt) / sigma
    kt_fem = float(s_tt.max() / sigma)
    theta_peak = float(np.degrees(th[np.argmax(s_tt)]))
    # free-surface check: the radial stress on the hole must vanish, whatever the plate size
    s_rr = sxx * np.cos(th) ** 2 + syy * np.sin(th) ** 2 + 2 * sxy * np.sin(th) * np.cos(th)
    free_surface = float(np.abs(s_rr).max() / sigma)

    # sigma_xx along the transverse axis x = 0, a <= y <= W, vs Kirsch; and equilibrium
    sym = m.facets_satisfying(lambda x: np.isclose(x[0], 0.0))
    fb_sym = FacetBasis(m, vb.elem, facets=sym)
    sxx_sym_q = stress_at(fb_sym)[0]
    equilibrium = float(np.sum(sxx_sym_q * fb_sym.dx) / (sigma * W))  # net-section force / applied force
    ys = np.asarray(fb_sym.global_coordinates().value)[1].ravel()
    sxx_sym = sxx_sym_q.ravel()
    kirsch_xx = sigma * (1 + a ** 2 / (2 * ys ** 2) + 3 * a ** 4 / (2 * ys ** 4))
    near = ys <= 5 * a
    axis_err_near = float(np.max(np.abs(sxx_sym[near] - kirsch_xx[near]) / kirsch_xx[near]))
    axis_err_all = float(np.max(np.abs(sxx_sym - kirsch_xx) / kirsch_xx))

    dW = 2 * a / (2 * W)
    ktn_howland = 3.000 - 3.140 * dW + 3.667 * dW ** 2 - 1.527 * dW ** 3   # net-section fit (Pilkey), strip
    kt_howland = ktn_howland / (1 - dW)

    res = dict(W_over_a=W_over_a, L_over_a=L / a, ndofs=int(vb.N), nelems=int(m.t.shape[1]), solve_s=round(dt, 3),
               kt_fem=round(kt_fem, 4), kt_kirsch_infinite=3.0, kt_howland_strip=round(kt_howland, 4),
               theta_peak_deg=round(theta_peak, 2),
               free_surface_max_srr_over_sigma=round(free_surface, 5),
               equilibrium_net_section_over_applied=round(equilibrium, 5),
               hoop_max_abs_err_over_sigma=round(float(hoop_err.max()), 4),
               hoop_mean_abs_err_over_sigma=round(float(hoop_err.mean()), 4),
               sigma_xx_axis_max_rel_err_y_le_5a=round(axis_err_near, 4),
               sigma_xx_axis_max_rel_err_all=round(axis_err_all, 4))
    summary[tag] = res
    print(f"Kirsch FEM  L/a={L / a:g} W/a={W_over_a:g} (d/W={dW:.3f})  elems={m.t.shape[1]}  dofs={vb.N}  solve={dt:.2f}s")
    print(f"  Kt: FEM {kt_fem:.4f}  | Kirsch (infinite) 3.0000 | Howland strip {kt_howland:.4f}  peak at θ={theta_peak:.1f}°")
    print(f"  checks: σ_rr/σ on the hole max {free_surface:.5f}   net-section force / applied {equilibrium:.5f}")
    print(f"  hoop stress vs Kirsch: max |Δ|/σ = {hoop_err.max():.4f}, mean {hoop_err.mean():.4f}")
    print(f"  σxx on transverse axis vs Kirsch: max rel err {axis_err_near:.4f} (y ≤ 5a), {axis_err_all:.4f} (all)")

    # von Mises nodal field for a figure and for later reuse
    sb = vb.with_element(ElementTriP1())
    g = np.asarray(vb.interpolate(u).grad)
    exx, eyy, exy = g[0, 0], g[1, 1], 0.5 * (g[0, 1] + g[1, 0])
    tr = exx + eyy
    Sxx, Syy, Sxy = lam * tr + 2 * mu * exx, lam * tr + 2 * mu * eyy, 2 * mu * exy
    vm = np.sqrt(Sxx ** 2 - Sxx * Syy + Syy ** 2 + 3 * Sxy ** 2)
    vm_nodal = sb.project(vm)
    np.savez(OUT / f"{tag}_quarter_plate.npz", p=m.p, t=m.t, von_mises=vm_nodal, a=a, W=W, sigma=sigma)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.tri as mtri
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.6))
        order = np.argsort(th)
        a1.plot(np.degrees(th[order]), kirsch_tt[order] / sigma, "C3--", lw=1.4, label="Kirsch")
        a1.plot(np.degrees(th[order]), s_tt[order] / sigma, "C0", lw=1.2, label="FEM")
        a1.set_xlabel("θ from load axis (deg)"); a1.set_ylabel("σ_θθ / σ"); a1.legend(); a1.grid(alpha=.3)
        a1.set_title("Hoop stress on the hole")
        tri = mtri.Triangulation(m.p[0], m.p[1], m.t.T)
        cs = a2.tricontour(tri, vm_nodal / sigma, levels=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 2.8],
                           cmap="viridis", linewidths=1)
        a2.clabel(cs, fontsize=7, fmt="%.2f")
        a2.set_aspect("equal"); a2.set_xlim(0, 3 * a); a2.set_ylim(0, 3 * a)
        a2.set_title("von Mises / σ near the hole (quarter model)")
        fig.tight_layout(); fig.savefig(OUT / f"{tag}.png", dpi=150); plt.close(fig)
    except Exception as e:
        print("figure skipped:", e)


# ----------------------------------------------------------------------------- main

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    test_lshape(summary)
    test_kirsch(summary, W_over_a=10.0, tag="kirsch_W10a")           # square plate, d/W = 0.1
    test_kirsch(summary, W_over_a=10.0, L_over_a=40.0, tag="kirsch_strip_W10a")  # long strip, d/W = 0.1: Howland applies
    test_kirsch(summary, W_over_a=40.0, n_s=96, beta=6.0, tag="kirsch_W40a")  # near-infinite plate: Kirsch applies
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote", OUT / "summary.json")


if __name__ == "__main__":
    main()
