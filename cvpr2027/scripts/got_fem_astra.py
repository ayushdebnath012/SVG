"""Graph-of-Thoughts verification with an FEM check on top of GPT-6 Astra (BenchCAD held-out tasks).

Per task the graph is:  vanilla Astra answer (existing, medium effort)  +  GENERATE 3 alternative interpretations
(one low-effort Astra call)  ->  SCORE every branch  ->  REFINE once when no branch passes  ->  KEEP BEST.
Scoring reads only the source program, instruction and candidates: the patch must apply and execute
(cad_edit_verifier.py gates), the executed solid must pass a scenario FEM check (mechanical_cad_fem.py: tetrahedral
mesh, fixed lower 5 % band, 1 N upper-band load, E=210 GPa, nu=0.3; anchored components, finite equilibrium and
energy checks), instruction values should appear in inserted lines, and branches are clustered by executed geometry.
Ties keep vanilla Astra. References are used only by the final scorer. BenchCAD only: CAD-Editor sequences have
no physical scale for FEM.

  branch  : Astra alternatives (hard USD budget, list price; saved; never re-billed)
  check   : verifier + FEM for every distinct candidate and the source
  refine  : one Astra refinement for tasks with no passing branch, then re-check
  select  : choose, write scorer input, report with paired statistics
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cad_edit_contracts import apply  # noqa: E402
from cad_edit_verifier import extract  # noqa: E402
from multisource_cad_astra_benchmark import DATA, ENDPOINT, _cost, _local_reference, _reference_index, tasks  # noqa: E402

PYTHON = ROOT / "tmp/cad-runtime/bin/python"
ASTRA = ROOT / "runs/multisource-cad-astra-20261004"
BRANCH_PROMPT = (
    "\n\nPropose exactly 3 alternative answers that differ where the instruction is ambiguous (which feature, edge "
    "set, reference dimension, or construction is meant); if it is unambiguous, vary the implementation. Return only "
    'JSON {"candidates":[{"interpretation":"...","edits":[{"start":0,"delete":0,"insert":["line"]}]}, ...]} with '
    "zero-based ORIGINAL line indices, ordered and non-overlapping.")
REFINE_PROMPT = ("Your previous patch was checked by external CAD tools:\n{obs}\n\nReturn only the corrected JSON patch "
                 '{{"edits":[...]}} with zero-based ORIGINAL line indices.')
FEM_WORKER = r'''
import json, sys, tempfile, numpy as np
sys.path.insert(0, sys.argv[2])
from verify_mechanical_cad_edits import execute
from mechanical_cad_fem import mesh_step, solve
import cadquery as cq
code = open(sys.argv[1]).read()
try:
    solid = execute(code)
    bb = solid.BoundingBox(); h = max(bb.DiagonalLength / 18.0, 0.5)
    with tempfile.TemporaryDirectory() as d:
        step = d + "/part.step"; cq.exporters.export(solid, step)
        xyz, tet = mesh_step(step, d + "/part.msh", h)
        metrics, _, _ = solve(xyz, tet)
    print(json.dumps(dict(ok=True, compliance=metrics.get("compliance_N_mm"), components=metrics.get("connected_components"), nodes=metrics.get("nodes"))))
except Exception as e:
    print(json.dumps(dict(ok=False, error=type(e).__name__ + ": " + str(e)[:160])))
'''


def bench_tasks() -> list[dict]:
    return [t for t in tasks() if t["source"] == "BenchCAD"]


def post(payload: dict, key: str) -> dict:
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)


def spent(out: Path) -> float:
    return sum(_cost(json.loads(p.read_text()).get("usage")) for p in out.glob("*/*-result.json"))


def call(out: Path, row: dict, name: str, messages: list, budget: float, cap: int) -> str | None:
    folder = out / row["id"][:16]
    folder.mkdir(parents=True, exist_ok=True)
    rec_path = folder / f"{name}-result.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        return (folder / f"{name}.txt").read_text() if rec.get("status") == "completed" else None
    worst = (4000 * 10 + cap * 50) / 1e6
    if spent(out) + worst > budget:
        print("BUDGET-STOP", row["id"][:16], name, flush=True)
        return None
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY unavailable")
    rec = dict(id=row["id"], call=name, started=time.time())
    try:
        raw = post({"model": "gpt-6-astra", "messages": messages, "reasoning_effort": "low",
                    "max_completion_tokens": cap, "store": False}, key)
        text = raw["choices"][0]["message"].get("content") or ""
        (folder / f"{name}.txt").write_text(text)
        rec.update(status="completed", usage=raw.get("usage"), finish_reason=raw["choices"][0].get("finish_reason"))
    except urllib.error.HTTPError as e:
        rec.update(status="api_error", http_status=e.code, error=e.read().decode(errors="replace").replace(key, "[REDACTED]")[:600])
        text = None
    except Exception as e:  # noqa: BLE001
        rec.update(status="client_error", error=str(e).replace(key, "[REDACTED]")[:300])
        text = None
    rec_path.write_text(json.dumps(rec, indent=2) + "\n")
    print("END", row["id"][:16], name, rec["status"], f"total ${spent(out):.3f}", flush=True)
    return text


BRANCH_SYSTEM = (
    "You edit mechanical CAD programs. Propose exactly 3 alternative edits for the instruction. Where the instruction "
    "is ambiguous (which feature, edge set, reference dimension or construction is meant), make each alternative follow "
    "a different reading; if it is unambiguous, vary the implementation. Return only JSON "
    '{"candidates":[{"interpretation":"one sentence","edits":[{"start":0,"delete":0,"insert":["replacement line"]}]},'
    ' ...]}. Indices are zero-based lines of the ORIGINAL input; operations must be ordered, nonoverlapping and in '
    "bounds. Preserve unrelated features. Return no other text.")


def branch(out: Path, budget: float, workers: int, limit: int | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    def one(row):
        call(out, row, "branches", [{"role": "system", "content": BRANCH_SYSTEM},
                                    {"role": "user", "content": row["input"]}], budget, 3500)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, bench_tasks()[:limit]))


def candidates(out: Path, row: dict) -> list[dict]:
    """[vanilla, alt1..3, refined?] as {name, text}; unparseable branch files contribute nothing."""
    folder = out / row["id"][:16]
    cands = [dict(name="vanilla", text=(ASTRA / row["id"][:16] / "response.txt").read_text())]
    if (folder / "branches.txt").exists():
        try:
            body = (folder / "branches.txt").read_text().strip()
            body = body[body.find("{"):body.rfind("}") + 1]
            for k, c in enumerate(json.loads(body)["candidates"][:3]):
                cands.append(dict(name=f"alt{k + 1}", text=json.dumps({"edits": c["edits"]})))
        except Exception:  # noqa: BLE001
            pass
    if (folder / "refine.txt").exists():
        cands.append(dict(name="refined", text=(folder / "refine.txt").read_text()))
    return cands


def fem(code: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "c.py").write_text(code)
        Path(d, "w.py").write_text(FEM_WORKER)
        try:
            p = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "c.py")), str(ROOT / "scripts")],
                               capture_output=True, text=True, timeout=240)
            return json.loads(p.stdout.strip().splitlines()[-1])
        except Exception as e:  # noqa: BLE001
            return dict(ok=False, error="FEM worker: " + type(e).__name__)


def check_task(out: Path, row: dict) -> dict:
    cands = candidates(out, row)
    payload = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"],
                   candidates=[c["text"] for c in cands])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
        json.dump(payload, h)
    try:
        p = subprocess.run([str(PYTHON), str(ROOT / "scripts/cad_edit_verifier.py"), h.name], capture_output=True,
                           text=True, timeout=900)
        verdict = json.loads(p.stdout.splitlines()[-1]) if p.returncode == 0 else None
    except subprocess.TimeoutExpired:
        verdict = None
    finally:
        os.unlink(h.name)
    source_fem = fem(row["code"])
    rows = []
    for c, v in zip(cands, (verdict or {}).get("candidates", [{}] * len(cands))):
        code = None
        try:
            _, patch = extract(c["text"])
            code = apply(row["code"], patch, row["representation"])
        except Exception:  # noqa: BLE001
            pass
        f = fem(code) if (code and v.get("gates")) else dict(ok=False, error="not executed")
        nums = [x["ok"] for x in v.get("numbers", [])]
        rows.append(dict(name=c["name"], code=code, gates=bool(v.get("gates")), fem=f, consensus=v.get("consensus", 0),
                         numbers_ok=(all(nums) if nums else None), changed=v.get("changed"),
                         error=v.get("error")))
    result = dict(id=row["id"], source_fem=source_fem, candidates=rows)
    (out / row["id"][:16] / "check.json").write_text(json.dumps(result, indent=1))
    return result


def passes(c: dict, source_fem: dict) -> bool:
    fem_ok = c["fem"].get("ok") or not source_fem.get("ok")  # FEM gates only parts whose source solves
    return c["gates"] and fem_ok and c["numbers_ok"] is not False and c["changed"] is not False


def score(c: dict, n: int) -> float:
    return (c["consensus"] / n) + (0.5 if c["numbers_ok"] else 0.0) + (0.25 if c["changed"] else 0.0) + (0.01 if c["name"] == "vanilla" else 0.0)


def check(out: Path, workers: int) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(lambda row: check_task(out, row), bench_tasks()):
            ok = [c["name"] for c in r["candidates"] if passes(c, r["source_fem"])]
            print("CHECK", r["id"][:16], "source_fem", r["source_fem"].get("ok"), "passing", ok, flush=True)


def refine(out: Path, budget: float, workers: int) -> None:
    system = json.loads((DATA / "manifest.json").read_text())["system"]

    def one(row):
        folder = out / row["id"][:16]
        chk = json.loads((folder / "check.json").read_text())
        if any(passes(c, chk["source_fem"]) for c in chk["candidates"]):
            return
        best = max(chk["candidates"], key=lambda c: (c["gates"], score(c, len(chk["candidates"]))))
        obs = []
        if not best["gates"]:
            obs.append(f"- patch application/execution failed: {best['error']}")
        elif not best["fem"].get("ok") and chk["source_fem"].get("ok"):
            obs.append(f"- the edited solid fails the structural FEM check that the original part passes: {best['fem'].get('error')}")
        if best["numbers_ok"] is False:
            obs.append("- some values requested in the instruction do not appear in the changed lines")
        if best["changed"] is False:
            obs.append("- the edited solid is geometrically identical to the original")
        text = next(c for c in candidates(out, row) if c["name"] == best["name"])["text"]
        call(out, row, "refine", [{"role": "system", "content": system}, {"role": "user", "content": row["input"]},
                                  {"role": "assistant", "content": text},
                                  {"role": "user", "content": REFINE_PROMPT.format(obs="\n".join(obs) or "- no check passed")}],
             budget, 2500)
        check_task(out, row)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, bench_tasks()))


def select(out: Path, python: Path, source: str = "check") -> None:
    index = _reference_index()
    preds, choice = [], {}
    for row in bench_tasks():
        chk = json.loads((out / row["id"][:16] / f"{source}.json").read_text())
        cands = chk["candidates"]
        ok = [c for c in cands if passes(c, chk["source_fem"])]
        pick = max(ok, key=lambda c: score(c, len(cands))) if ok else cands[0]  # no passing branch: keep vanilla
        choice[row["id"]] = pick["name"]
        preds.append(dict(id=row["id"], source=row["source"], category=row["category"], representation=row["representation"],
                          predicted_code=pick["code"], error=None if pick["code"] else "no executable selection",
                          applicable=pick["code"] is not None, prediction=pick["name"], reference_code=row["edited_code"],
                          reference_step=_local_reference(row, index), reference_step_sha256=row["reference_step_sha256"]))
    path = out / f"selected-{source}-predictions.jsonl"
    path.write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([str(python), str(ROOT / "scripts/score_multisource_cad_geometry.py"), str(path)], check=True,
                   stdout=subprocess.DEVNULL)
    got = {json.loads(l)["id"]: json.loads(l) for l in (out / f"selected-{source}-predictions-geometry.jsonl").read_text().splitlines()}
    van = {json.loads(l)["id"]: json.loads(l) for l in (ASTRA / "scored/astra-predictions-geometry.jsonl").read_text().splitlines()}
    ids = list(got)
    from math import comb
    g = sum(got[i]["match_strict"] and not van[i]["match_strict"] for i in ids)
    l_ = sum(van[i]["match_strict"] and not got[i]["match_strict"] for i in ids)
    n, k = g + l_, min(g, l_)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    from collections import Counter
    summary = dict(tasks=len(ids), vanilla=sum(van[i]["match_strict"] for i in ids), got_fem=sum(got[i]["match_strict"] for i in ids),
                   recovered=g, regressed=l_, mcnemar_p=p, chosen=dict(Counter(choice.values())),
                   source_fem_ok=sum(json.loads((out / i[:16] / "check.json").read_text())["source_fem"].get("ok", False) for i in ids),
                   api_cost_usd=round(spent(out), 4))
    summary["selection"] = "GoT+FEM" if source == "check" else "GoT+MCTS+FEM"
    (out / f"summary-{source}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))


DIVERSIFY_PROMPT = ("External CAD checks pass for these alternatives:\n{alts}\n\nPropose ONE further alternative edit that "
                    'is meaningfully different from all of them. Return only JSON {{"edits":[...]}} with zero-based ORIGINAL '
                    "line indices.")


def node_eval(row: dict, text: str, source_fem: dict) -> dict:
    """Target-free value of one node: gates, FEM, instruction numbers, change; value in [0, 1]."""
    payload = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"], candidates=[text])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
        json.dump(payload, h)
    try:
        p = subprocess.run([str(PYTHON), str(ROOT / "scripts/cad_edit_verifier.py"), h.name], capture_output=True,
                           text=True, timeout=600)
        v = json.loads(p.stdout.splitlines()[-1])["candidates"][0] if p.returncode == 0 else {}
    except subprocess.TimeoutExpired:
        v = {}
    finally:
        os.unlink(h.name)
    code = None
    try:
        _, patch = extract(text)
        code = apply(row["code"], patch, row["representation"])
    except Exception:  # noqa: BLE001
        pass
    f = fem(code) if (code and v.get("gates")) else dict(ok=False, error="not executed")
    nums = [x["ok"] for x in v.get("numbers", [])]
    e = dict(gates=bool(v.get("gates")), fem=f, numbers_ok=(all(nums) if nums else None), changed=v.get("changed"),
             error=v.get("error"), code=code)
    fem_ok = f.get("ok") or not source_fem.get("ok")
    e["value"] = 0.0 if not e["gates"] else 0.4 + 0.2 * bool(fem_ok) + 0.2 * (e["numbers_ok"] is not False) + 0.2 * (e["changed"] is not False)
    return e


def observations(e: dict, source_fem: dict) -> str:
    obs = []
    if not e["gates"]:
        obs.append(f"- patch application/execution failed: {e['error']}")
    elif not e["fem"].get("ok") and source_fem.get("ok"):
        obs.append(f"- the edited solid fails the structural FEM check that the original part passes: {e['fem'].get('error')}")
    if e["numbers_ok"] is False:
        obs.append("- some values requested in the instruction do not appear in the changed lines")
    if e["changed"] is False:
        obs.append("- the edited solid is geometrically identical to the original")
    return "\n".join(obs) or "- no issue detected"


def mcts_task(out: Path, row: dict, expansions: int, budget: float, c_uct: float = 0.7) -> dict:
    import math
    system = json.loads((DATA / "manifest.json").read_text())["system"]
    folder = out / row["id"][:16]
    state_path = folder / "mcts.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    chk = json.loads((folder / "check.json").read_text())
    source_fem = chk["source_fem"]
    nodes = []
    for c, cand in zip(chk["candidates"], candidates(out, row)):
        fem_ok = c["fem"].get("ok") or not source_fem.get("ok")
        value = 0.0 if not c["gates"] else 0.4 + 0.2 * bool(fem_ok) + 0.2 * (c["numbers_ok"] is not False) + 0.2 * (c["changed"] is not False)
        nodes.append(dict(name=c["name"], parent=None, text=cand["text"], visits=1, value_sum=value,
                          eval=dict(gates=c["gates"], fem=c["fem"], numbers_ok=c["numbers_ok"], changed=c["changed"], error=c["error"], code=c["code"])))
    for k in range(expansions):
        total = sum(n["visits"] for n in nodes)
        pick = max(range(len(nodes)), key=lambda i: nodes[i]["value_sum"] / nodes[i]["visits"]
                   + c_uct * math.sqrt(math.log(total) / nodes[i]["visits"]))
        parent = nodes[pick]
        if parent["value_sum"] / parent["visits"] < 1.0:
            messages = [{"role": "system", "content": system}, {"role": "user", "content": row["input"]},
                        {"role": "assistant", "content": parent["text"]},
                        {"role": "user", "content": REFINE_PROMPT.format(obs=observations(parent["eval"], source_fem))}]
            kind = "refine"
        else:
            alts = "\n".join(f"- {n['text']}" for n in nodes if n["eval"]["gates"])[:6000]
            messages = [{"role": "system", "content": system}, {"role": "user", "content": row["input"]},
                        {"role": "user", "content": DIVERSIFY_PROMPT.format(alts=alts)}]
            kind = "diversify"
        text = call(out, row, f"mcts{k + 1}", messages, budget, 2500)
        if text is None:
            break
        e = node_eval(row, text, source_fem)
        nodes.append(dict(name=f"mcts{k + 1}-{kind}", parent=pick, text=text, visits=1, value_sum=e["value"], eval=e))
        i = pick
        while i is not None:  # back up the new value along the path to the root
            nodes[i]["visits"] += 1
            nodes[i]["value_sum"] += e["value"]
            i = nodes[i]["parent"]
    # final keep-best over every node with geometric consensus
    payload = dict(source=row["code"], instruction=row["instruction"], representation=row["representation"],
                   candidates=[n["text"] for n in nodes])
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as h:
        json.dump(payload, h)
    try:
        p = subprocess.run([str(PYTHON), str(ROOT / "scripts/cad_edit_verifier.py"), h.name], capture_output=True,
                           text=True, timeout=900)
        cons = [c.get("consensus", 0) for c in json.loads(p.stdout.splitlines()[-1])["candidates"]] if p.returncode == 0 else [0] * len(nodes)
    except subprocess.TimeoutExpired:
        cons = [0] * len(nodes)
    finally:
        os.unlink(h.name)
    final = []
    for n, cs in zip(nodes, cons):
        e = n["eval"]
        final.append(dict(name=n["name"], code=e["code"], gates=e["gates"], fem=e["fem"], consensus=cs,
                          numbers_ok=e["numbers_ok"], changed=e["changed"]))
    state = dict(id=row["id"], source_fem=source_fem, nodes=[{k: v for k, v in n.items() if k != "text"} for n in nodes],
                 candidates=final)
    state_path.write_text(json.dumps(state, indent=1))
    return state


def priority(out: Path, row: dict) -> int:
    """0: no branch passes (refine); 1: passing branches disagree on geometry (search can matter); 2: unanimous."""
    chk = json.loads((out / row["id"][:16] / "check.json").read_text())
    ok = [c for c in chk["candidates"] if passes(c, chk["source_fem"])]
    if not ok:
        return 0
    return 2 if max(c["consensus"] for c in ok) == len(chk["candidates"]) else 1


def mcts(out: Path, budget: float, workers: int, expansions: int) -> None:
    """Spend the remaining budget where search can change the choice; unanimous tasks get no expansion."""
    ranked = sorted(bench_tasks(), key=lambda row: priority(out, row))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for st in pool.map(lambda row: mcts_task(out, row, expansions if priority(out, row) < 2 else 0, budget), ranked):
            print("MCTS", st["id"][:16], [n["name"] for n in st["nodes"]], flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("branch", "check", "refine", "select", "mcts", "select-mcts"))
    p.add_argument("--out", type=Path, default=ROOT / "runs/got-fem-astra-20261007")
    p.add_argument("--budget", type=float, default=5.0)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--limit", type=int)
    p.add_argument("--expansions", type=int, default=2)
    a = p.parse_args()
    {"branch": lambda: branch(a.out, a.budget, a.workers, a.limit), "check": lambda: check(a.out, a.workers),
     "refine": lambda: refine(a.out, a.budget, a.workers), "select": lambda: select(a.out, PYTHON),
     "mcts": lambda: mcts(a.out, a.budget, a.workers, a.expansions),
     "select-mcts": lambda: select(a.out, PYTHON, "mcts")}[a.cmd]()


if __name__ == "__main__":
    main()
