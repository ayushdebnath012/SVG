"""Varied CAD+FEM analysis tasks (space truss, modal, frame buckling) for a cheap single-call Astra check.

Each task is fully specified in text (dimensioned geometry, material, supports, loads) and asks for a few numbers in
JSON. References come from our own solvers and are admitted only if their checks hold. Protocol: one call, medium effort,
no tools, 16k-token cap (as the frame failures). Heat-fin task: see heat_fin_fenicsx.py (reference added by `build`).

  tmp/cq-env/bin/python scripts/astra_traps/variety_tasks.py build
  OPENAI_API_KEY=... tmp/hosted-harness-env/bin/python scripts/astra_traps/variety_tasks.py run --budget-usd 3
  tmp/cq-env/bin/python scripts/astra_traps/variety_tasks.py score
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from scipy.linalg import eigh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/astra-variety-20261015"
SYSTEM = ("You are an engineering analysis assistant. Use your own reasoning; no external tools are provided. Do not claim "
          "you ran a solver. Answer with one JSON object only.")
P_IN, P_OUT, CAP = 12.5, 50.0, 16000


# ------------------------------------------------------------------ T1 space truss tower
def tower():
    H, n = 12000.0, 6
    def half(z):                                              # half-width tapers from 1000 (base) to 500 mm (top)
        return 1000.0 - 500.0 * z / H
    nodes = {}
    for k in range(n + 1):
        z, b = k * H / n, half(k * H / n)
        for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            nodes[f"N{k}{i}"] = (sx * b, sy * b, z)
    mem = []
    for k in range(n):
        for i in range(4):
            j = (i + 1) % 4
            mem.append((f"leg{k}{i}", f"N{k}{i}", f"N{k + 1}{i}", 2000.0))
            a, b = (f"N{k}{i}", f"N{k + 1}{j}") if k % 2 == 0 else (f"N{k}{j}", f"N{k + 1}{i}")
            mem.append((f"diag{k}{i}", a, b, 800.0))
            mem.append((f"ring{k + 1}{i}", f"N{k + 1}{i}", f"N{k + 1}{j}", 800.0))
        mem.append((f"plan{k + 1}", f"N{k + 1}0", f"N{k + 1}2", 800.0))
    fixed = [f"N0{i}" for i in range(4)]
    loads = {f"N{n}{i}": (20000.0, 0.0, -50000.0) for i in range(4)}
    return nodes, mem, fixed, loads, 200000.0


def truss_solve(nodes, mem, fixed, loads, E):
    names = list(nodes)
    idx = {k: i for i, k in enumerate(names)}
    X = np.array([nodes[k] for k in names])
    K = np.zeros((3 * len(names),) * 2)
    geo = []
    for m, a, b, A in mem:
        d = X[idx[b]] - X[idx[a]]
        L = np.linalg.norm(d)
        c = d / L
        k = E * A / L * np.outer(c, c)
        dof = np.r_[3 * idx[a]:3 * idx[a] + 3, 3 * idx[b]:3 * idx[b] + 3]
        K[np.ix_(dof, dof)] += np.block([[k, -k], [-k, k]])
        geo.append((m, idx[a], idx[b], c, L, A))
    F = np.zeros(3 * len(names))
    for k, f in loads.items():
        F[3 * idx[k]:3 * idx[k] + 3] = f
    free = np.array([d for k in names if k not in fixed for d in range(3 * idx[k], 3 * idx[k] + 3)])
    assert np.linalg.matrix_rank(K[np.ix_(free, free)]) == len(free), "truss is a mechanism"
    u = np.zeros_like(F)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    N = {m: E * A / L * (c @ (u[3 * j:3 * j + 3] - u[3 * i:3 * i + 3])) for m, i, j, c, L, A in geo}
    R = K @ u - F
    resid = np.abs(R[free]).max()
    reac = R.reshape(-1, 3)[[idx[k] for k in fixed]].sum(axis=0)
    eq = np.abs(reac + np.array(list(loads.values())).sum(axis=0)).max()
    return u.reshape(-1, 3), N, idx, dict(free_residual_N=float(resid), global_equilibrium_N=float(eq))


# ------------------------------------------------------------------ T2 shear building
def shear_building():
    m = np.array([42e3, 40e3, 40e3, 38e3, 38e3, 36e3, 34e3, 30e3])                   # kg, floor 1 (bottom) to 8
    k = np.array([62e6, 58e6, 55e6, 52e6, 48e6, 44e6, 40e6, 35e6])                   # N/m, storey 1 to 8
    n = len(m)
    K = np.zeros((n, n))
    for i in range(n):
        K[i, i] += k[i]
        if i + 1 < n:
            K[i, i] += k[i + 1]; K[i, i + 1] -= k[i + 1]; K[i + 1, i] -= k[i + 1]
    w2, V = eigh(K, np.diag(m))
    ortho = np.abs(V.T @ np.diag(m) @ V - np.eye(n)).max()
    return m, k, np.sqrt(w2) / (2 * np.pi), ortho


# ------------------------------------------------------------------ T3 portal frame buckling
def frame_buckling(sub):
    """Two-bay one-storey frame, fixed bases, rigid joints; Euler-Bernoulli elements with consistent geometric stiffness."""
    E = 210000.0
    Ic, Ac, Ib, Ab = 8.36e7, 7.8e3, 2.3e8, 9.9e3                       # columns HEB-like, beams IPE-like (mm^4, mm^2)
    pts = {"A": (0, 0), "B": (0, 5000), "C": (8000, 0), "D": (8000, 5000), "E": (14000, 0), "F": (14000, 5000)}
    members = [("A", "B", Ic, Ac), ("C", "D", Ic, Ac), ("E", "F", Ic, Ac), ("B", "D", Ib, Ab), ("D", "F", Ib, Ab)]
    loads = {"B": (0, -400e3), "D": (0, -900e3), "F": (0, -500e3)}       # N
    nodes, elems = dict(pts), []
    for a, b, I, A in members:
        prev = a
        for s in range(1, sub + 1):
            name = b if s == sub else f"{a}{b}{s}"
            if s < sub:
                pa, pb = np.array(pts[a]), np.array(pts[b])
                nodes[name] = tuple(pa + (pb - pa) * s / sub)
            elems.append((prev, name, I, A)); prev = name
    names = list(nodes); idx = {k: i for i, k in enumerate(names)}
    nd = 3 * len(names)
    def kmat(L, I, A, N=None):
        if N is None:
            return E / L ** 3 * np.array([[A * L * L, 0, 0, -A * L * L, 0, 0], [0, 12 * I, 6 * I * L, 0, -12 * I, 6 * I * L],
                                          [0, 6 * I * L, 4 * I * L * L, 0, -6 * I * L, 2 * I * L * L], [-A * L * L, 0, 0, A * L * L, 0, 0],
                                          [0, -12 * I, -6 * I * L, 0, 12 * I, -6 * I * L], [0, 6 * I * L, 2 * I * L * L, 0, -6 * I * L, 4 * I * L * L]])
        return N / (30 * L) * np.array([[0, 0, 0, 0, 0, 0], [0, 36, 3 * L, 0, -36, 3 * L], [0, 3 * L, 4 * L * L, 0, -3 * L, -L * L],
                                        [0, 0, 0, 0, 0, 0], [0, -36, -3 * L, 0, 36, -3 * L], [0, 3 * L, -L * L, 0, -3 * L, 4 * L * L]])
    def T(c, s):
        r = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        return np.block([[r, np.zeros((3, 3))], [np.zeros((3, 3)), r]])
    def assemble(Nax=None):
        K = np.zeros((nd, nd)); out = []
        for e, (a, b, I, A) in enumerate(elems):
            pa, pb = np.array(nodes[a]), np.array(nodes[b]); L = np.linalg.norm(pb - pa); c, s = (pb - pa) / L
            Tm = T(c, s); dof = np.r_[3 * idx[a]:3 * idx[a] + 3, 3 * idx[b]:3 * idx[b] + 3]
            k = kmat(L, I, A) if Nax is None else kmat(L, I, A, Nax[e])
            K[np.ix_(dof, dof)] += Tm.T @ k @ Tm; out.append((dof, Tm, L, I, A))
        return K, out
    K, info = assemble()
    F = np.zeros(nd)
    for k, (fx, fy) in loads.items():
        F[3 * idx[k]] += fx; F[3 * idx[k] + 1] += fy
    fixed = [d for k in ("A", "C", "E") for d in range(3 * idx[k], 3 * idx[k] + 3)]
    free = np.setdiff1d(np.arange(nd), fixed)
    u = np.zeros(nd); u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    Nax = []
    for dof, Tm, L, I, A in info:
        q = kmat(L, I, A) @ (Tm @ u[dof]); Nax.append(q[3])            # axial force at end b (tension positive)
    Kg, _ = assemble(Nax)                                         # geometric stiffness only (kmat with N)
    mu = eigh(-Kg[np.ix_(free, free)], K[np.ix_(free, free)], eigvals_only=True)   # K phi = -lambda Kg phi  <=>  mu = 1/lambda
    return float(1.0 / mu.max()), dict(E=E, Ic=Ic, Ac=Ac, Ib=Ib, Ab=Ab, points=pts, loads_N=loads)


def tasks() -> list[dict]:
    T = []
    nodes, mem, fixed, loads, E = tower()
    u, N, idx, chk = truss_solve(nodes, mem, fixed, loads, E)
    top = [idx[f"N6{i}"] for i in range(4)]
    assert chk["free_residual_N"] < 1e-6 and chk["global_equilibrium_N"] < 1e-6, chk
    geo = ("Pin-jointed steel lattice tower (space truss), millimetres. Levels k = 0..6 at z = 2000 k; at each level four corner nodes "
           "Nk0..Nk3 at (x, y) = (-b,-b), (b,-b), (b,b), (-b,b) with half-width b = 1000 - 500 z/12000 (tapering from 1000 at the base to 500 at "
           "the top). Members: legs Nk_i-N(k+1)_i (area 2000 mm^2); one face diagonal per face and panel, from Nk_i to N(k+1)_j for even k and "
           "from Nk_j to N(k+1)_i for odd k, with j = i+1 mod 4 (800 mm^2); ring members N(k+1)_i-N(k+1)_j (800 mm^2); one plan diagonal "
           "N(k+1)0-N(k+1)2 at every level above the base (800 mm^2). 78 members. E = 200000 MPa. The four base nodes N00..N03 are pinned "
           "(all translations fixed). Loads: at each top node N60..N63, 20 kN in +x and 50 kN downward (-z). Small displacements, linear elastic.")
    T.append(dict(id="VAR-SPACE-TRUSS", family="space-truss statics (3D)", prompt=geo + "\nReport: the x-displacement of node N62, the largest "
                  "member tension and the largest member compression (magnitudes).\nJSON keys: ux_N62_mm, max_tension_kN, max_compression_kN.",
                  reference=dict(ux_N62_mm=float(u[idx["N62"], 0]), max_tension_kN=max(N.values()) / 1e3, max_compression_kN=-min(N.values()) / 1e3),
                  tolerance=dict(ux_N62_mm=0.03, max_tension_kN=0.03, max_compression_kN=0.03), check=chk))
    m, k, f, ortho = shear_building()
    assert ortho < 1e-9
    T.append(dict(id="VAR-SHEAR-BUILDING-MODES", family="modal dynamics", prompt=(
        "Eight-storey shear building idealised as a lumped-mass chain: floor masses from floor 1 (bottom) to floor 8 (top) = "
        + ", ".join(f"{x / 1e3:g}" for x in m) + " tonnes; storey lateral stiffnesses from storey 1 (ground to floor 1) to storey 8 = "
        + ", ".join(f"{x / 1e6:g}" for x in k) + " MN/m. The ground is fixed; floors move only horizontally; no damping.\n"
        "Report the first three natural frequencies in Hz.\nJSON keys: f1_Hz, f2_Hz, f3_Hz."),
        reference=dict(f1_Hz=float(f[0]), f2_Hz=float(f[1]), f3_Hz=float(f[2])), tolerance=dict(f1_Hz=0.02, f2_Hz=0.02, f3_Hz=0.02),
        check=dict(mass_orthogonality_error=float(ortho))))
    lams = {s: frame_buckling(s)[0] for s in (4, 8, 16)}
    lam, spec = frame_buckling(16)
    conv = abs(lams[16] - lams[8]) / lams[16]
    assert conv < 1e-4, lams
    T.append(dict(id="VAR-PORTAL-BUCKLING", family="frame elastic stability", prompt=(
        "Two-bay one-storey rigid-jointed steel frame in the x-y plane, millimetres and newtons. Column bases A (0,0), C (8000,0), E (14000,0) are "
        "fully fixed (clamped). Column tops B (0,5000), D (8000,5000), F (14000,5000). Columns AB, CD, EF: I = 8.36e7 mm^4, A = 7.8e3 mm^2. Beams "
        "BD and DF: I = 2.3e8 mm^4, A = 9.9e3 mm^2. E = 210000 MPa. In-plane behaviour only (no out-of-plane or lateral-torsional buckling). "
        "Vertical loads (downward) at the column tops: B 400 kN, D 900 kN, F 500 kN. Find the elastic critical load factor: the smallest multiplier "
        "of this whole load set at which the frame buckles (linear eigenvalue buckling, including axial shortening of the members).\n"
        "JSON key: critical_load_factor."),
        reference=dict(critical_load_factor=lam), tolerance=dict(critical_load_factor=0.03),
        check=dict(lambda_by_subdivision={str(s): v for s, v in lams.items()}, relative_change_8_to_16=conv)))
    return T


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = tasks()
    fin = OUT / "heat_fin_reference.json"
    if fin.exists():
        rows.append(json.loads(fin.read_text()))
    (OUT / "tasks.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for r in rows:
        print(r["id"], {k: round(v, 4) for k, v in r["reference"].items()}, "| check", json.dumps(r["check"])[:160])


def answer(txt: str):
    try:
        return json.loads(txt)
    except Exception:                                             # noqa: BLE001
        m = re.findall(r"\{.*\}", txt, re.S)
        for b in reversed(m):
            try:
                return json.loads(b)
            except Exception:                                     # noqa: BLE001
                continue
    return None


def run(budget: float, endpoint: str = "https://api.openai.com/v1/chat/completions", key_env: str = "OPENAI_API_KEY") -> None:
    key = os.environ.get(key_env) or sys.exit(f"{key_env} unavailable; no calls made")
    rows = [json.loads(l) for l in (OUT / "tasks.jsonl").read_text().splitlines()]
    spent = sum(json.loads(p.read_text()).get("cost_usd", 0) for p in OUT.glob("*/result.json"))
    for t in rows:
        d = OUT / t["id"]
        if (d / "result.json").exists():
            continue
        if spent + (4000 * P_IN + CAP * P_OUT) / 1e6 > budget:
            print("BUDGET-STOP", t["id"], f"spent ${spent:.3f}", flush=True)
            break
        d.mkdir(parents=True, exist_ok=True)
        payload = {"model": "gpt-6-astra", "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": t["prompt"]}],
                   "reasoning_effort": "medium", "max_completion_tokens": CAP, "store": False}
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=1500) as resp:
                raw = json.load(resp)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace").replace(key, "[REDACTED]")
            (d / "result.json").write_text(json.dumps(dict(status="api_error", error=body[:500], cost_usd=0)) + "\n")
            print("API ERROR", t["id"], body[:160], flush=True)
            if "insufficient_quota" in body:
                break
            continue
        u = raw.get("usage") or {}
        cost = (u.get("prompt_tokens", 0) * P_IN + u.get("completion_tokens", 0) * P_OUT) / 1e6
        spent += cost
        (d / "response.json").write_text(json.dumps(raw) + "\n")
        (d / "result.json").write_text(json.dumps(dict(status="completed", finish_reason=raw["choices"][0].get("finish_reason"), usage=u,
                                                       cost_usd=round(cost, 5), charged_usd=u.get("cost"), endpoint=endpoint,
                                                       seconds=round(time.time() - t0, 1))) + "\n")
        print(f"END {t['id']} ${cost:.3f} total ${spent:.3f}", flush=True)


def score() -> None:
    rows = [json.loads(l) for l in (OUT / "tasks.jsonl").read_text().splitlines()]
    out = []
    for t in rows:
        d = OUT / t["id"]
        if not (d / "response.json").exists():
            continue
        raw = json.loads((d / "response.json").read_text())
        ch = raw["choices"][0]
        a = answer(ch["message"].get("content") or "") or {}
        res = {}
        for k, ref in t["reference"].items():
            v = a.get(k)
            if not isinstance(v, (int, float)):
                res[k] = dict(reported=v, reference=round(ref, 4), ok=False)
            else:
                res[k] = dict(reported=v, reference=round(ref, 4), error_pct=round(100 * (v / ref - 1), 2), ok=abs(v / ref - 1) <= t["tolerance"][k])
        reported_any = any(isinstance(r["reported"], (int, float)) for r in res.values())
        outcome = ("truncated" if ch.get("finish_reason") != "stop" else "declined" if not reported_any else
                   "correct" if all(r["ok"] for r in res.values()) else "wrong")
        out.append(dict(id=t["id"], family=t["family"], outcome=outcome, values=res, cost_usd=json.loads((d / "result.json").read_text())["cost_usd"]))
        print(f"{t['id']:26s} {outcome:9s} " + "; ".join(f"{k} {r['reported']} vs {r['reference']}" + (f" ({r['error_pct']:+.1f}%)" if 'error_pct' in r else "") for k, r in res.items()))
    (OUT / "score.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["build", "run", "score"])
    ap.add_argument("--budget-usd", type=float, default=3.0)
    ap.add_argument("--out", type=Path, help="task folder (default runs/astra-variety-20261015)")
    ap.add_argument("--endpoint", default="https://api.openai.com/v1/chat/completions", help="OpenAI-compatible chat completions URL")
    ap.add_argument("--key-env", default="OPENAI_API_KEY", help="environment variable holding the key")
    a = ap.parse_args()
    if a.out:
        OUT = a.out.resolve()
    {"build": build, "run": lambda: run(a.budget_usd, a.endpoint, a.key_env), "score": score}[a.command]()
