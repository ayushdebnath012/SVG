#!/usr/bin/env python3
"""Finite-difference reference solutions for configs/prompts/engineering_v3_fields.json.

Solves each case's Laplace/Poisson problem on a grid with red-black SOR (numpy only) and writes
runs/reference-v3/<id>.npz (x, y, field) plus <id>.isolines.json (marching-squares segments in
domain coordinates) for overlays. Robin edges use a first-order ghost relation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / "runs" / "reference-v3"


def sor(field, fixed, source, dx, robin=None, omega=1.92, tol=1e-7, max_iter=60000):
    """Solve lap(f) = -source on the grid; `fixed` nodes keep their value. Returns field, iterations."""
    f = field.astype(float).copy()
    ny, nx = f.shape
    jj, ii = np.mgrid[0:ny, 0:nx]
    red = ((ii + jj) % 2 == 0)
    interior = np.zeros_like(fixed)
    interior[1:-1, 1:-1] = True
    free = interior & ~fixed
    rhs = source * dx * dx
    for it in range(max_iter):
        f_old = f.copy()
        for colour in (red, ~red):
            m = free & colour
            nb = np.zeros_like(f)
            nb[1:-1, 1:-1] = f[:-2, 1:-1] + f[2:, 1:-1] + f[1:-1, :-2] + f[1:-1, 2:]
            f[m] = (1 - omega) * f[m] + omega * 0.25 * (nb[m] + rhs[m])
        if robin is not None:
            robin(f)
        if it % 50 == 0 and np.max(np.abs(f - f_old)) < tol:
            return f, it
    return f, max_iter


def marching_squares(x, y, f, level):
    """Return line segments [(x0,y0,x1,y1), ...] of the iso-contour f == level."""
    segs = []
    ny, nx = f.shape
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = [f[j, i], f[j, i + 1], f[j + 1, i + 1], f[j + 1, i]]
            if any(np.isnan(v) for v in c):
                continue
            idx = sum(1 << k for k, v in enumerate(c) if v >= level)
            if idx in (0, 15):
                continue
            pts_xy = [(x[i], y[j]), (x[i + 1], y[j]), (x[i + 1], y[j + 1]), (x[i], y[j + 1])]
            edges = []
            for k in range(4):
                a, b = c[k], c[(k + 1) % 4]
                if (a >= level) != (b >= level):
                    t = (level - a) / (b - a)
                    (xa, ya), (xb, yb) = pts_xy[k], pts_xy[(k + 1) % 4]
                    edges.append((xa + t * (xb - xa), ya + t * (yb - ya)))
            for k in range(0, len(edges) - 1, 2):
                segs.append((*edges[k], *edges[k + 1]))
    return segs


def grid(x0, x1, y0, y1, n_per_unit):
    nx, ny = int(round((x1 - x0) * n_per_unit)) + 1, int(round((y1 - y0) * n_per_unit)) + 1
    x, y = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(x, y)
    return x, y, X, Y, 1.0 / n_per_unit


def save(id_, x, y, f, levels, mask_nan=None, note=""):
    OUT.mkdir(parents=True, exist_ok=True)
    fplot = f.copy()
    if mask_nan is not None:
        fplot[mask_nan] = np.nan
    np.savez(OUT / f"{id_}.npz", x=x, y=y, field=fplot)
    iso = {str(lv): marching_squares(x, y, fplot, lv) for lv in levels}
    (OUT / f"{id_}.isolines.json").write_text(json.dumps(iso))
    print(f"{id_:26s} {note}  range [{np.nanmin(fplot):.3f}, {np.nanmax(fplot):.3f}]  segments {sum(len(v) for v in iso.values())}")


def laplace_L_shape():
    x, y, X, Y, dx = grid(0, 1, 0, 1, 160)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    notch = (X >= 0.5) & (Y >= 0.5)
    fixed[notch] = True                       # removed quadrant (value 0 on its edges)
    fixed[:, 0] = True; f[:, 0] = 100.0       # left edge hot
    fixed[:, -1] = fixed[0, :] = fixed[-1, :] = True
    f[0, 0] = f[-1, 0] = 0.0
    f, it = sor(f, fixed, np.zeros_like(f), dx)
    save("laplace_L_shape", x, y, f, [10, 20, 30, 40, 50, 60, 80], mask_nan=(X > 0.5) & (Y > 0.5), note=f"SOR {it} it")


def torsion_square_prandtl():
    x, y, X, Y, dx = grid(0, 1, 0, 1, 160)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    fixed[:, 0] = fixed[:, -1] = fixed[0, :] = fixed[-1, :] = True
    f, it = sor(f, fixed, 2.0 * np.ones_like(f), dx)
    pmax = f.max()
    J = 2 * np.trapezoid(np.trapezoid(f, x, axis=1), y)  # torsion constant, G*theta = 1
    pct = 100 * f / pmax
    save("torsion_square_prandtl", x, y, pct, [20, 40, 60, 80], note=f"SOR {it} it, phi_max {pmax:.4f}, J/a^4 {J:.4f}")
    (OUT / "torsion_square_prandtl.extra.json").write_text(json.dumps({"phi_max": pmax, "J_over_a4": J}))


def square_hole_plate():
    x, y, X, Y, dx = grid(0, 1, 0, 1, 160)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    hole = (X >= 0.4 - 1e-9) & (X <= 0.6 + 1e-9) & (Y >= 0.4 - 1e-9) & (Y <= 0.6 + 1e-9)
    fixed[hole] = True; f[hole] = 100.0
    fixed[:, 0] = fixed[:, -1] = fixed[0, :] = fixed[-1, :] = True
    f, it = sor(f, fixed, np.zeros_like(f), dx)
    save("square_hole_plate", x, y, f, [20, 40, 60, 80], mask_nan=(X > 0.4) & (X < 0.6) & (Y > 0.4) & (Y < 0.6), note=f"SOR {it} it")


def channel_step_streamlines():
    x, y, X, Y, dx = grid(0, 3, 0, 1, 100)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    block = (X >= 1.5 - 1e-9) & (Y <= 0.5 + 1e-9)
    fixed[block] = True; f[block] = 0.0
    fixed[0, :] = True; f[0, :] = 0.0            # bottom wall
    fixed[-1, :] = True; f[-1, :] = 1.0          # top wall
    fixed[:, 0] = True; f[:, 0] = Y[:, 0]        # inlet
    fixed[:, -1] = True; f[:, -1] = np.clip(2 * (Y[:, -1] - 0.5), 0, 1)  # outlet
    f, it = sor(f, fixed, np.zeros_like(f), dx)
    save("channel_step_streamlines", x, y, 100 * f, [20, 40, 60, 80], mask_nan=(X > 1.5) & (Y < 0.5), note=f"SOR {it} it")


def square_conductor_in_shell():
    x, y, X, Y, dx = grid(-1, 1, -1, 1, 100)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    outside = X**2 + Y**2 >= 1.0
    fixed[outside] = True
    cond = (np.abs(X) <= 0.3 + 1e-9) & (np.abs(Y) <= 0.3 + 1e-9)
    fixed[cond] = True; f[cond] = 100.0
    f, it = sor(f, fixed, np.zeros_like(f), dx)
    save("square_conductor_in_shell", x, y, f, [20, 40, 60, 80], mask_nan=outside | ((np.abs(X) < 0.3) & (np.abs(Y) < 0.3)), note=f"SOR {it} it")


def plate_convective_edges():
    x, y, X, Y, dx = grid(0, 2, 0, 1, 100)
    f = np.zeros_like(X); fixed = np.zeros(X.shape, bool)
    fixed[:, 0] = True; f[:, 0] = 100.0
    hk = 5.0
    def robin(g):  # dT/dn = -hk T on right, top, bottom edges (first-order ghost)
        g[:, -1] = g[:, -2] / (1 + hk * dx)
        g[0, 1:] = g[1, 1:] / (1 + hk * dx)
        g[-1, 1:] = g[-2, 1:] / (1 + hk * dx)
    f, it = sor(f, fixed, np.zeros_like(f), dx, robin=robin)
    save("plate_convective_edges", x, y, f, [10, 20, 40, 60, 80], note=f"SOR {it} it")


if __name__ == "__main__":
    for fn in (laplace_L_shape, torsion_square_prandtl, square_hole_plate, channel_step_streamlines, square_conductor_in_shell, plate_convective_edges):
        fn()
