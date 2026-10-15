"""Draw the reference FEM solution of each frame task: undeformed frame (grey), deformed shape (exaggerated) with members
coloured by their peak extreme-fibre stress, the probe displacement and the peak stress. Same stiffness routine as the
reference solver (cad_astra_benchmark.stiffness); the plotted numbers are checked against the stored reference."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm, colors
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from cad_astra_benchmark import stiffness  # noqa: E402

def displacements(model):
    ids = list(model["nodes"]); idx = {n: i for i, n in enumerate(ids)}; nd = 3 * len(ids)
    K, f = np.zeros((nd, nd)), np.zeros(nd)
    for m in model["members"]:
        k, T, A, I = stiffness(model["nodes"][m["a"]], model["nodes"][m["b"]], m["E"], m["b_mm"], m["h_mm"])
        d = np.array([3 * idx[m["a"]] + j for j in range(3)] + [3 * idx[m["b"]] + j for j in range(3)])
        K[np.ix_(d, d)] += T.T @ k @ T
    for n, load in model["loads"].items():
        f[3 * idx[n]:3 * idx[n] + 3] += load
    fixed = sorted({3 * idx[n] + d for n, ds in model["supports"].items() for d in ds})
    free = np.setdiff1d(np.arange(nd), fixed); u = np.zeros(nd)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], f[free])
    return idx, u.reshape(-1, 3)

def plot(task, out):
    m, ref = task["model"], task["reference"]
    idx, u = displacements(m)
    p = idx[m["probe"]]
    assert abs(u[p, 0] - ref["ux_mm"]) < 1e-6 and abs(u[p, 1] - ref["uy_mm"]) < 1e-6
    xy = np.array([m["nodes"][n] for n in idx], float)
    span = np.ptp(xy, axis=0).max(); scale = 0.06 * span / np.abs(u[:, :2]).max()
    st = ref["member_stress_mpa"]; norm = colors.Normalize(0, max(st.values())); cmap = cm.viridis
    fig, ax = plt.subplots(figsize=(10, 7.5))
    for mm in m["members"]:
        a, b = idx[mm["a"]], idx[mm["b"]]
        ax.plot(*xy[[a, b]].T, color="0.82", lw=1.2, zorder=1)
        # deformed member: cubic Hermite interpolation of the end displacements and rotations
        L = np.linalg.norm(xy[b] - xy[a]); c, s = (xy[b] - xy[a]) / L; t = np.linspace(0, 1, 21)
        ua = np.array([c * u[a, 0] + s * u[a, 1], -s * u[a, 0] + c * u[a, 1], u[a, 2]])
        ub = np.array([c * u[b, 0] + s * u[b, 1], -s * u[b, 0] + c * u[b, 1], u[b, 2]])
        axial = ua[0] * (1 - t) + ub[0] * t
        h1, h2, h3, h4 = 1 - 3 * t**2 + 2 * t**3, L * (t - 2 * t**2 + t**3), 3 * t**2 - 2 * t**3, L * (-t**2 + t**3)
        trans = h1 * ua[1] + h2 * ua[2] + h3 * ub[1] + h4 * ub[2]
        X = xy[a, 0] + t * L * c + scale * (axial * c - trans * s)
        Y = xy[a, 1] + t * L * s + scale * (axial * s + trans * c)
        ax.plot(X, Y, color=cmap(norm(st[mm["id"]])), lw=3.0, zorder=2)
    for n in m["supports"]:
        ax.plot(*xy[idx[n]], marker="s", color="0.3", ms=7, zorder=3)
    ax.plot(xy[p, 0] + scale * u[p, 0], xy[p, 1] + scale * u[p, 1], "o", mfc="none", mec="crimson", ms=12, mew=2, zorder=4)
    worst = max(st, key=st.get)
    ax.set_title(f"{m['name']}: reference linear frame FEM ({len(m['members'])} members)\n"
                 f"probe {m['probe']}: ux = {ref['ux_mm']:.4f} mm, uy = {ref['uy_mm']:.4f} mm;  peak stress {ref['peak_stress_mpa']:.3f} MPa in {worst}",
                 fontsize=11)
    ax.set_aspect("equal"); ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
    ax.text(0.01, 0.01, f"grey: undeformed; coloured: deformed shape x{scale:.0f}; squares: clamped bases; circle: probe",
            transform=ax.transAxes, fontsize=8, color="0.35")
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.8, label="member peak extreme-fibre stress (MPa)")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)

if __name__ == "__main__":
    dest = ROOT / "output/astra-frame-drawings-20261016"
    for data in ("data/eng-frame-bench-xxl", "data/eng-frame-bench-xxl2", "data/eng-frame-bench-xl"):
        for t in json.loads((ROOT / data / "tasks.json").read_text())["tasks"]:
            plot(t, dest / f"{t['id']}.reference-fem.png")
            print("wrote", t["id"])
