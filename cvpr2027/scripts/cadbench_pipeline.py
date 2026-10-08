"""The agentic CAD pipeline on Parametric CAD Bench v2 and v3 (FreeCAD PartDesign scripts).

Each task is solved twice with the same model so the comparison is paired:
  single     one generated answer.py, executed once, no feedback (the model's zero-shot answer)
  pipeline   graph of candidate scripts: the single answer, diagnosis-driven repairs of failing candidates and
             independent alternatives; every candidate is executed in FreeCAD 1.1.0 and checked target-free
             (script runs; required FCStd files exist; the validator's own reference-free integrity gates:
             exactly one non-empty PartDesign Body, an editable feature tree with no baked TopoShape; one valid
             solid; values stated in the instruction appear in the script); passing candidates are clustered by
             executed geometry (volume IoU >= 0.99) and the largest agreeing cluster is chosen
Held-back references and spec.json are used only by the official verifiers afterwards: v2 with
gnucleus-freecad-validator 0.4.0 (cadbench_eval.py), v3 with 0.6.0 (cadbench_v3_eval.py).

  python cadbench_pipeline.py smoke --limit 5                    execution + gates on Astra's published v2 scripts
  python cadbench_pipeline.py run --backend open|gemini|astra --model M --out DIR [--bench v2,v3] [--lanes 6]
  python cadbench_pipeline.py score --out DIR
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path(os.environ.get("CADBENCH_ROOT", ROOT / "tmp/cadbench"))  # environment overrides serve a Linux GPU host
FC_PYTHON = Path(os.environ.get("CADBENCH_FC_PYTHON", BENCH / "fc-venv-060/bin/python"))
FREECAD_LIB = Path(os.environ.get("CADBENCH_FREECAD_LIB", BENCH / "FreeCAD.app/Contents/Resources/lib"))
SUITES = {"v2": Path(os.environ.get("CADBENCH_V2", BENCH / "harbor-tasks/cad-bench")),
          "v3": Path(os.environ.get("CADBENCH_V3", BENCH / "harbor-tasks-v3/cad-bench"))}
SYSTEM = ("You are an expert FreeCAD 1.1 scripter. Write one complete, self-contained Python script for FreeCAD 1.1 that "
          "builds the requested part as an editable PartDesign feature tree: exactly one PartDesign::Body producing exactly one "
          "solid, built from sketches and PartDesign features (Pad, Pocket, Revolution, Hole, Fillet, Chamfer, patterns ...), "
          "driven by named document objects; never a Part::Feature holding a baked TopoShape. Derive every output path from "
          "__file__ as the task asks, call doc.recompute() before saving, and return only the script in one ```python block.")
API_REFERENCE = """
FreeCAD 1.1 headless API reference (generic patterns; adapt names and dimensions to the task):
```python
from pathlib import Path
import FreeCAD as App, Part, Sketcher
doc = App.newDocument("Part")
body = doc.addObject("PartDesign::Body", "Body")
params = body.newObject("App::VarSet", "Parameters")               # named, editable parameters
params.addProperty("App::PropertyLength", "width", "Dimensions", "overall width"); params.width = 40.0
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")     # every sketch and feature is created through the Body
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])        # origin planes XY_Plane, XZ_Plane, YZ_Plane; axes X_Axis, Y_Axis, Z_Axis
sketch.MapMode = "FlatFace"                                         # lift: sketch.AttachmentOffset = App.Placement(App.Vector(0, 0, z), App.Rotation())
sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(40, 0, 0)), False)
sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 5.0), False)
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))  # optional
pad = body.newObject("PartDesign::Pad", "Pad"); pad.Profile = sketch; pad.Length = 10.0   # pad.Midplane = True / pad.Reversed = True
pad.setExpression("Length", "Parameters.width")                     # drive features from the parameters
pocket = body.newObject("PartDesign::Pocket", "Bore"); pocket.Profile = hole_sketch; pocket.Type = "ThroughAll"   # or pocket.Length
rev = body.newObject("PartDesign::Revolution", "Revolve"); rev.Profile = profile; rev.ReferenceAxis = (profile, ["V_Axis"]); rev.Angle = 360.0
groove = body.newObject("PartDesign::Groove", "Groove")              # subtractive revolution, same fields
pattern = body.newObject("PartDesign::PolarPattern", "Pattern"); pattern.Originals = [pocket]
pattern.Axis = (doc.getObject("Z_Axis"), [""]); pattern.Angle = 360.0; pattern.Occurrences = 6
chamfer = body.newObject("PartDesign::Chamfer", "Chamfer"); chamfer.Base = (pad, ["Edge1"]); chamfer.Size = 1.0   # Fillet uses .Radius
doc.recompute()
doc.saveAs(str(Path(__file__).resolve().with_suffix(".FCStd")))
```
Headless: never use FreeCADGui, ViewObject or setActiveWorkbench. These types do not exist: PartDesign::Sketch,
PartDesign::SketchObject, App::Parameter. For create-and-edit tasks save the base as <stem>_base.FCStd, then change the
parameters/features, doc.recompute() and save again as <stem>_edit.FCStd.
"""
SYSTEM = SYSTEM + "\n" + API_REFERENCE
GATE_WORKER = r'''
import json, sys, os
sys.path.append(os.environ["FREECAD_LIB"])
import FreeCAD
from freecad_validator.comparators.integrity_gates import partdesign_body_gate, partdesign_feature_tree_gate, select_scored_body
out = {}
for path in sys.argv[1:]:
    rec = {}
    try:
        doc = FreeCAD.openDocument(path); doc.recompute()
        rec["body_gate"] = partdesign_body_gate(doc); rec["tree_gate"] = partdesign_feature_tree_gate(doc)
        body = select_scored_body(doc)
        shape = body.Shape if body is not None else None
        if shape is not None and not shape.isNull():
            bb = shape.BoundBox
            rec.update(valid=bool(shape.isValid()), solids=len(shape.Solids), volume=round(shape.Volume, 4),
                       bbox=[round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)], features=len(body.Group))
            shape.exportBrep(path + ".brep")
        FreeCAD.closeDocument(doc.Name)
    except Exception as e:
        rec["error"] = type(e).__name__ + ": " + str(e)[:300]
    out[os.path.basename(path)] = rec
print(json.dumps(out))
'''
IOU_WORKER = r'''
import json, sys, os
sys.path.append(os.environ["FREECAD_LIB"])
import Part
shapes = [Part.read(p) if p else None for p in json.loads(sys.argv[1])]
n = len(shapes); m = [[0.0] * n for _ in range(n)]
for i in range(n):
    for j in range(i, n):
        if shapes[i] is None or shapes[j] is None: continue
        try:
            inter = shapes[i].common(shapes[j]).Volume; u = shapes[i].Volume + shapes[j].Volume - inter
            m[i][j] = m[j][i] = inter / u if u > 0 else 0.0
        except Exception: pass
print(json.dumps(m))
'''


def tasks(benches: list[str]) -> list[dict]:
    out = []
    for b in benches:
        for t in sorted(p for p in SUITES[b].iterdir() if (p / "task.toml").exists()):
            # task.toml lists the graded artifacts, so the task type is known without the grader (tests/ may be absent)
            kind = "create+edit" if "answer_base.FCStd" in (t / "task.toml").read_text() else (
                "drawing" if list((t / "environment").glob("*.png")) else "create")
            files = ["answer_base.FCStd", "answer_edit.FCStd"] if kind == "create+edit" else ["answer.FCStd"]
            out.append(dict(id=f"{b}/{t.name}", bench=b, task=t.name, kind=kind, dir=str(t), files=files,
                            instruction=(t / "instruction.md").read_text(), images=[str(p) for p in (t / "environment").glob("*.png")]))
    return out


def execute(task: dict, script: str) -> dict:
    """Run answer.py in a fresh directory (inputs alongside), then the reference-free gates on every required FCStd."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "answer.py").write_text(script)
        for img in task["images"]:
            shutil.copy(img, d / Path(img).name)
        env = dict(os.environ, FREECAD_LIB=str(FREECAD_LIB), PYTHONPATH=str(FREECAD_LIB))
        try:
            r = subprocess.run([str(FC_PYTHON), "answer.py"], cwd=d, capture_output=True, text=True, timeout=300, env=env)
            stderr = "\n".join(l for l in (r.stderr or "").splitlines() if "3DconnexionNavlib" not in l)  # macOS FreeCAD noise
            err = stderr[-1500:] if r.returncode != 0 else None
        except subprocess.TimeoutExpired:
            err = "script timed out after 300 s"
        produced = [f for f in task["files"] if (d / f).exists()]
        res = dict(error=err, produced=produced, missing=[f for f in task["files"] if f not in produced], files={})
        if produced:
            Path(d, "g.py").write_text(GATE_WORKER)
            try:
                g = subprocess.run([str(FC_PYTHON), "g.py", *[str(d / f) for f in produced]], cwd=d, capture_output=True, text=True,
                                   timeout=300, env=env)
                res["files"] = json.loads(g.stdout.strip().splitlines()[-1])
            except Exception as e:  # noqa: BLE001
                res["gate_error"] = type(e).__name__
        res["artifacts"] = {f: (d / f).read_bytes() for f in produced}
        res["breps"] = {f: (d / (f + ".brep")).read_bytes() for f in produced if (d / (f + ".brep")).exists()}
    numbers = set(re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])", task["instruction"]))
    numbers = {n for n in numbers if float(n) not in (0.0, 1.0, 1.1)}
    res["missing_values"] = sorted(n for n in numbers if n not in script and str(float(n)) not in script)[:10]
    return res


def diagnosis(res: dict) -> list[str]:
    out = []
    if res.get("error"):
        out.append("The script failed when run with FreeCAD 1.1:\n" + res["error"])
    for f in res.get("missing", []):
        out.append(f"The script did not save {f} next to itself.")
    for f, rec in res.get("files", {}).items():
        for gate in ("body_gate", "tree_gate"):
            if rec.get(gate):
                out.append(f"{f}: {rec[gate]}")
        if rec.get("error"):
            out.append(f"{f} could not be opened: {rec['error']}")
        if "valid" in rec and (not rec["valid"] or rec.get("solids") != 1):
            out.append(f"{f}: the Body shape must be one valid solid (valid={rec['valid']}, solids={rec.get('solids')}).")
    return out


def passes(res: dict) -> bool:
    return not diagnosis(res)


def extract_code(text: str) -> str:
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    if m:
        return max(m, key=len).strip() + "\n"
    body = re.sub(r"^\s*```(?:python)?\s*\n", "", text)  # an unclosed fence (truncated or sloppy reply)
    return re.sub(r"\n```\s*$", "", body).strip() + "\n"


class Model:
    def __init__(self, backend: str, model: str, endpoint: str, rpm: float, log: Path, max_tokens: int = 0):
        sys.path.insert(0, str(ROOT / "scripts"))
        from adaptive_cad.live import ASTRA, gemini_backend, open_backend, post
        self.post = post
        self.b = {"astra": ASTRA, "gemini": gemini_backend(model, rpm), "open": open_backend(endpoint, model)}[backend]
        self.key = os.environ.get(self.b.get("key_env", "OPENAI_API_KEY" if self.b["priced"] else ""), "local") or "local"
        self.log, self.max_tokens = log, max_tokens

    def __call__(self, task: dict, messages: list[dict]) -> str:
        if task["images"] and messages[-1]["role"] == "user" and isinstance(messages[-1]["content"], str):
            content = [{"type": "text", "text": messages[-1]["content"]}]
            for img in task["images"]:
                content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(Path(img).read_bytes()).decode()}})
            messages = messages[:-1] + [{"role": "user", "content": content}]
        body = {"model": self.b["model"], "messages": [{"role": "system", "content": SYSTEM}, *messages], **self.b["params"],
                self.b["max_key"]: self.max_tokens or self.b["tokens"].get("single", 8192)}  # thinking needs room on long scripts
        reply = self.post(self.b, self.key, body, 900)
        text = reply["choices"][0]["message"].get("content") or ""
        with self.log.open("a") as h:
            h.write(json.dumps(dict(task=task["id"], usage=reply.get("usage"), finish=reply["choices"][0].get("finish_reason"))) + "\n")
        return text


def ious(breps: list[bytes | None]) -> list[list[float]]:
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for k, b in enumerate(breps):
            if b is None:
                paths.append(None); continue
            p = Path(d, f"{k}.brep"); p.write_bytes(b); paths.append(str(p))
        Path(d, "w.py").write_text(IOU_WORKER)
        env = dict(os.environ, FREECAD_LIB=str(FREECAD_LIB), PYTHONPATH=str(FREECAD_LIB))
        r = subprocess.run([str(FC_PYTHON), "w.py", json.dumps(paths)], cwd=d, capture_output=True, text=True, timeout=600, env=env)
        return json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else [[0.0] * len(breps) for _ in breps]


def save(out: Path, variant: str, task: dict, script: str, res: dict) -> None:
    d = out / "answers" / variant / task["bench"] / task["task"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "answer.py").write_text(script)
    for f, b in res.get("artifacts", {}).items():
        (d / f).write_bytes(b)


def solve(task: dict, model: Model, out: Path, repairs: int, alternatives: int) -> dict:
    folder = out / "trace" / task["bench"] / task["task"]
    if (folder / "result.json").exists():
        return json.loads((folder / "result.json").read_text())
    folder.mkdir(parents=True, exist_ok=True)
    user = task["instruction"] + ("\n\nThe drawing is attached and is saved next to the script under the same file name." if task["images"] else "")
    nodes = []

    def add(kind, script, parent=None):
        res = execute(task, script)
        nodes.append(dict(kind=kind, parent=parent, script=script, res=res, ok=passes(res), diagnosis=diagnosis(res)))
        return nodes[-1]
    first = add("single", extract_code(model(task, [{"role": "user", "content": user}])))
    save(out, "single", task, first["script"], first["res"])
    frontier = [first]
    for k in range(alternatives):  # diverse hypotheses: independent constructions of the same part
        frontier.append(add(f"alternative{k + 1}", extract_code(model(task, [{"role": "user", "content": user + "\n\nWrite an independent "
                        "construction: choose the sketch planes, feature order and PartDesign features afresh."}]))))
    for node in list(frontier):  # diagnosis-driven repair, a few rounds per failing branch
        cur = node
        for r in range(repairs):
            if cur["ok"]:
                break
            msg = [{"role": "user", "content": user}, {"role": "assistant", "content": "```python\n" + cur["script"] + "```"},
                   {"role": "user", "content": "Checks on this script found:\n- " + "\n- ".join(cur["diagnosis"])[:4000]
                    + "\n\nReturn the corrected complete script."}]
            cur = add(f"repair{r + 1}-of-{node['kind']}", extract_code(model(task, msg)), parent=node["kind"])
    ok = [n for n in nodes if n["ok"]]
    if ok:
        key = task["files"][-1]  # the edited part for create+edit, otherwise the only part
        m = ious([n["res"]["breps"].get(key) for n in ok])
        support = [sum(x >= 0.99 for x in row) for row in m]
        choice = max(range(len(ok)), key=lambda i: (support[i], -nodes.index(ok[i])))  # largest agreeing cluster, earliest
        pick = ok[choice]
    else:
        pick = first
    save(out, "pipeline", task, pick["script"], pick["res"])
    summary = dict(id=task["id"], kind=task["kind"], nodes=[dict(kind=n["kind"], ok=n["ok"], diagnosis=n["diagnosis"][:3]) for n in nodes],
                   single_ok=first["ok"], picked=pick["kind"], any_ok=bool(ok))
    for n in nodes:
        (folder / f"{n['kind']}.py").write_text(n["script"])
    (folder / "result.json").write_text(json.dumps(summary, indent=1))
    return summary


def run(a) -> None:
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    model = Model(a.backend, a.model, a.endpoint, a.rpm, out / "calls.jsonl", a.max_tokens)
    todo = [t for t in tasks(a.bench.split(",")) if not a.limit or True][: a.limit or None]
    with ThreadPoolExecutor(a.lanes) as pool:
        for n, fut in enumerate(as_completed([pool.submit(solve, t, model, out, a.repairs, a.alternatives) for t in todo]), 1):
            try:
                s = fut.result()
                print("DONE", s["id"], "single_ok", s["single_ok"], "picked", s["picked"], "nodes", len(s["nodes"]), flush=True)
            except Exception as e:  # noqa: BLE001
                print("ERROR", type(e).__name__, str(e)[:200], flush=True)


def score(out: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    for variant in ("single", "pipeline"):
        base = out / "answers" / variant
        if (base / "v3").exists():
            subprocess.run([sys.executable, str(ROOT / "scripts/cadbench_v3_eval.py"), "score", "--answers", str(base / "v3"),
                            "--name", f"{out.name}-{variant}"], check=True)
        if (base / "v2").exists():
            v2 = base / "v2-flat"
            v2.mkdir(exist_ok=True)
            for t in (base / "v2").iterdir():  # cadbench_eval.py expects <answers>/<task id without prefix>/answer.FCStd
                dst = v2 / t.name.replace("freecad-", "")
                if not dst.exists():
                    shutil.copytree(t, dst)
            subprocess.run([sys.executable, str(ROOT / "scripts/cadbench_eval.py"), "score", "--answers", str(v2), "--work",
                            str(out / f"v2-score-{variant}")], check=True)


def smoke(limit: int) -> None:
    """Execution and gates on Astra's published v2 scripts (no model calls): the backend must accept them."""
    ts = {t["task"]: t for t in tasks(["v2"])}
    rows = []
    for d in sorted((BENCH / "answers-astra").iterdir())[:limit]:
        t = ts.get("freecad-" + d.name)
        if t and (d / "answer.py").exists():
            t0 = time.time(); res = execute(t, (d / "answer.py").read_text())
            rows.append(dict(task=d.name, ok=passes(res), diagnosis=diagnosis(res)[:2], files={k: {x: v for x, v in r.items() if x != "bbox"}
                             for k, r in res["files"].items()}, seconds=round(time.time() - t0, 1)))
            print(json.dumps(rows[-1])[:400], flush=True)
    print(f"{sum(r['ok'] for r in rows)}/{len(rows)} Astra scripts pass the target-free checks")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("smoke", "run", "score"))
    p.add_argument("--backend", choices=("open", "gemini", "astra"), default="open")
    p.add_argument("--model", default="Qwen/Qwen3.5-35B-A3B-FP8")
    p.add_argument("--endpoint", default="http://localhost:8011/v1/chat/completions")
    p.add_argument("--rpm", type=float, default=10)
    p.add_argument("--out", default=str(ROOT / "runs/cadbench-pipeline"))
    p.add_argument("--bench", default="v2,v3")
    p.add_argument("--lanes", type=int, default=6)
    p.add_argument("--repairs", type=int, default=3)
    p.add_argument("--alternatives", type=int, default=2)
    p.add_argument("--limit", type=int)
    p.add_argument("--max-tokens", type=int, default=0, help="completion cap per call, reasoning included (0: backend default)")
    a = p.parse_args()
    if a.cmd == "smoke":
        smoke(a.limit or 5)
    elif a.cmd == "run":
        run(a)
    else:
        score(Path(a.out))


if __name__ == "__main__":
    main()
