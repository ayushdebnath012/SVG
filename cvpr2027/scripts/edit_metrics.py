"""Edit metrics of CAD-Editor and of AgenticCADedit / neuralCAD-Edit, for every system and dataset we evaluate.

CAD-Editor (github.com/microsoft/CAD-Editor, utils/eval_cad.py, eval_dclip.py):
  validity ratio   share of outputs that build a solid
  Chamfer distance 2,000 area-weighted surface points per shape, each cloud scaled by its own max |coordinate|,
                   squared nearest-neighbour distances, mean(pred->ref) + mean(ref->pred); prediction vs ground truth
  JSD              Jensen-Shannon divergence of 28^3 occupancy distributions, predicted set vs ground-truth set
  D-CLIP           CLIP ViT-B/32 cosine between the image direction (source render -> edited render) and the text
                   direction ("This is a 3D shape." -> "This is a 3D shape. " + instruction); higher is better
AgenticCADedit (arXiv:2609.29621, following neuralCAD-Edit):
  validity, Chamfer distance, voxel IoU, DINOv2 similarity of isometric renders (prediction vs ground truth),
  VLM ratings (instruction following, quality, acceptance; separate judge step). Means score failures as zero;
  medians are over valid outputs.
Voxel IoU is the 96^3 filled-occupancy IoU of realcad_metrics.py in the shared source frame (no pose alignment, so a
misplaced edit counts as wrong).

  python edit_metrics.py geometry [--workers 8]      CAD kernel: validity, points, Chamfer, voxel IoU, renders
  python edit_metrics.py semantic                     tmp/metrics-venv: DINOv2 and D-CLIP on the renders
  python edit_metrics.py report                       tables per dataset and system (incl. JSD and exact match)
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/edit-metrics-20261008"
PYTHON = ROOT / "tmp/cad-runtime/bin/python"
TORCH = ROOT / "tmp/metrics-venv/bin/python"
SCORED = ROOT / "runs/multisource-cad-astra-20261004/scored"
SYSTEMS = {  # name -> predictions JSONL (predicted_code per task id), as scored by score_multisource_cad_geometry.py
    "GPT-6 Astra": SCORED / "astra-predictions.jsonl",
    "3B adapter": SCORED / "trained-predictions.jsonl",
    "3B base": SCORED / "base-predictions.jsonl",
    "Qwen3.5-35B single": ROOT / "runs/adaptive-cad-open-20261007/single-predictions.jsonl",
    "Qwen3.5-35B + pipeline": ROOT / "runs/adaptive-cad-open-20261007/pipeline-predictions.jsonl",
    "Gemini 3.5 Flash-Lite single": ROOT / "runs/adaptive-cad-gemini-lite-20261007/single-predictions.jsonl",
    "Gemini 3.5 Flash-Lite + pipeline": ROOT / "runs/adaptive-cad-gemini-lite-20261007/pipeline-predictions.jsonl",
}
WORKER = r'''
import json, sys, numpy as np
sys.path.insert(0, sys.argv[2])
job = json.load(open(sys.argv[1])); out_dir = sys.argv[3]
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from realcad_metrics import voxel_ious
def build(code, rep):
    if rep == "cadquery":
        from verify_mechanical_cad_edits import execute; return execute(code)
    from cad_editor_geometry import execute_sequence; return execute_sequence(code)
def tess(s):
    bb = s.BoundingBox(); v, f = s.tessellate(max(bb.DiagonalLength * 1e-3, 1e-4))
    return np.array([p.toTuple() for p in v]), np.array(f)
def sample(s, n=2000, seed=0):
    v, f = tess(s); tri = v[f]
    area = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); idx = rng.choice(len(tri), n, p=area / area.sum())
    u, w = rng.random(n), rng.random(n); flip = u + w > 1; u[flip], w[flip] = 1 - u[flip], 1 - w[flip]
    t = tri[idx]; return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def norm(pc): return pc / np.max(np.abs(pc))
def chamfer(a, b):
    from scipy.spatial import cKDTree
    da, _ = cKDTree(b).query(a); db, _ = cKDTree(a).query(b)
    return float((da ** 2).mean() + (db ** 2).mean())
def render(s, path, centre, radius):
    v, f = tess(s); tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.35 + 0.65 * np.clip(np.abs(n @ np.array([0.3, -0.5, 0.8])), 0, 1)
    fig = plt.figure(figsize=(5.12, 5.12), dpi=100); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=plt.cm.Greys(shade * 0.6 + 0.3), edgecolor="none"))
    for k, set_ in enumerate((ax.set_xlim, ax.set_ylim, ax.set_zlim)): set_(centre[k] - radius, centre[k] + radius)
    ax.view_init(28, -55); ax.set_axis_off(); ax.set_box_aspect((1, 1, 1), zoom=1.3)
    fig.savefig(path); plt.close(fig)
rep = job["representation"]; res = {"id": job["id"]}
try:
    ref = build(job["reference_code"], rep) if not job.get("reference_step") else __import__("cadquery").importers.importStep(job["reference_step"]).val()
    src = build(job["source_code"], rep)
except Exception as e:
    print(json.dumps(dict(id=job["id"], error="reference/source: " + type(e).__name__))); sys.exit()
shapes = {"__reference__": ref, "__source__": src}
for name, code in job["predictions"].items():
    try: shapes[name] = build(code, rep) if code else None
    except Exception: shapes[name] = None
allv = np.vstack([tess(s)[0] for s in (ref, src)]); lo, hi = allv.min(0), allv.max(0)
centre, radius = (lo + hi) / 2, (hi - lo).max() / 2 * 1.05  # one camera per task: source/reference frame
ref_pc = norm(sample(ref)); np.save(f"{out_dir}/{job['id'][:16]}__reference__.npy", ref_pc)
render(ref, f"{out_dir}/{job['id'][:16]}__reference__.png", centre, radius)
render(src, f"{out_dir}/{job['id'][:16]}__source__.png", centre, radius)
res["systems"] = {}
for name, s in shapes.items():
    if name.startswith("__"): continue
    key = f"{job['id'][:16]}__{job['slug'][name]}"
    if s is None or s.Volume() <= 0:
        res["systems"][name] = dict(valid=False); continue
    try:
        pc = norm(sample(s)); np.save(f"{out_dir}/{key}.npy", pc)
        render(s, f"{out_dir}/{key}.png", centre, radius)
        res["systems"][name] = dict(valid=True, chamfer=chamfer(pc, ref_pc), voxel_iou=voxel_ious(s, ref)["solid"], key=key)
    except Exception as e:
        res["systems"][name] = dict(valid=False, error=type(e).__name__)
print(json.dumps(res))
'''


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def tasks() -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    from multisource_cad_astra_benchmark import _local_reference, _reference_index, tasks as all_tasks
    index = _reference_index()
    out = {}
    for r in all_tasks():
        out[r["id"]] = dict(id=r["id"], dataset="BenchCAD" if r["source"] == "BenchCAD" else "CAD-Editor", representation=r["representation"],
                            source_code=r["code"], reference_code=r["edited_code"], instruction=r["instruction"],
                            reference_step=_local_reference(r, index) if r["source"] == "BenchCAD" else None)
    return out


def geometry(workers: int) -> None:
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    T = tasks()
    preds = {}
    for name, path in SYSTEMS.items():
        if path.exists():
            for line in path.read_text().splitlines():
                r = json.loads(line)
                preds.setdefault(r["id"], {})[name] = r.get("predicted_code") if r.get("applicable") in (True, "True") else None
    path = OUT / "geometry.jsonl"
    done = {json.loads(l)["id"] for l in path.read_text().splitlines()} if path.exists() else set()
    jobs = [dict(T[i], predictions=p, slug={n: slug(n) for n in p}) for i, p in preds.items() if i in T and i not in done]

    def one(job):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "w.py").write_text(WORKER); Path(d, "j.json").write_text(json.dumps(job))
            try:
                r = subprocess.run([str(PYTHON), str(Path(d, "w.py")), str(Path(d, "j.json")), str(ROOT / "scripts"), str(OUT / "assets")],
                                   capture_output=True, text=True, timeout=1800)
                res = json.loads(r.stdout.strip().splitlines()[-1])
            except Exception as e:  # noqa: BLE001
                res = dict(id=job["id"], error="worker: " + type(e).__name__)
        return dict(res, dataset=job["dataset"])
    with ThreadPoolExecutor(workers) as pool, path.open("a") as h:
        for n, fut in enumerate(as_completed([pool.submit(one, j) for j in jobs]), 1):
            h.write(json.dumps(fut.result()) + "\n"); h.flush()
            if n % 25 == 0:
                print("GEOMETRY", n, "/", len(jobs), flush=True)


SEMANTIC = r'''
import json, sys, torch, open_clip
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
jobs = json.load(open(sys.argv[1])); out = []
dev = "mps" if torch.backends.mps.is_available() else "cpu"
clip, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai"); clip = clip.to(dev).eval()
tokenizer = open_clip.get_tokenizer("ViT-B-32")
proc = AutoImageProcessor.from_pretrained("facebook/dinov2-base"); dino = AutoModel.from_pretrained("facebook/dinov2-base").to(dev).eval()
def img_clip(p):
    with torch.no_grad(): e = clip.encode_image(pre(Image.open(p).convert("RGB")).unsqueeze(0).to(dev)).float()
    return e / e.norm(dim=-1, keepdim=True)
def txt(t):
    with torch.no_grad(): e = clip.encode_text(tokenizer([t]).to(dev)).float()
    return e / e.norm(dim=-1, keepdim=True)
def img_dino(p):
    with torch.no_grad(): e = dino(**proc(images=Image.open(p).convert("RGB"), return_tensors="pt").to(dev)).pooler_output.float()
    return e / e.norm(dim=-1, keepdim=True)
cache = {}
def get(fn, p):
    if (fn.__name__, p) not in cache: cache[(fn.__name__, p)] = fn(p)
    return cache[(fn.__name__, p)]
for j in jobs:
    src_t = "This is a 3D shape. "
    tdir = txt(src_t + j["instruction"]) - txt(src_t); tdir = tdir / tdir.norm(dim=-1, keepdim=True)
    idir = get(img_clip, j["pred"]) - get(img_clip, j["source"])
    dclip = float((idir / (idir.norm(dim=-1, keepdim=True) + 1e-12) * tdir).sum()) if idir.abs().sum() > 0 else 0.0
    dino_sim = float((get(img_dino, j["pred"]) * get(img_dino, j["reference"])).sum())
    out.append(dict(id=j["id"], system=j["system"], dclip=dclip, dino=dino_sim))
print(json.dumps(out))
'''


def semantic() -> None:
    T = tasks()
    jobs = []
    for line in (OUT / "geometry.jsonl").read_text().splitlines():
        r = json.loads(line)
        for name, m in r.get("systems", {}).items():
            if m.get("valid") and m.get("key"):
                a = OUT / "assets"
                jobs.append(dict(id=r["id"], system=name, instruction=T[r["id"]]["instruction"], pred=str(a / f"{m['key']}.png"),
                                 source=str(a / f"{r['id'][:16]}__source__.png"), reference=str(a / f"{r['id'][:16]}__reference__.png")))
    with tempfile.TemporaryDirectory() as d:
        Path(d, "s.py").write_text(SEMANTIC); Path(d, "j.json").write_text(json.dumps(jobs))
        r = subprocess.run([str(TORCH), str(Path(d, "s.py")), str(Path(d, "j.json"))], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr[-2000:])
        (OUT / "semantic.json").write_text(r.stdout.strip().splitlines()[-1])
    print("SEMANTIC", len(jobs))


def jsd(sample_pcs, ref_pcs, resolution: int = 28) -> float:
    """CAD-Editor eval_cad.jsd_between_point_cloud_sets (in_unit_sphere=False): occupancy of all points in a unit cube grid."""
    import numpy as np

    def grid_var(pcs):
        counts = np.zeros((resolution,) * 3)
        for pc in pcs:
            idx = np.clip(((pc + 0.5) * resolution).astype(int), 0, resolution - 1)  # unit_cube_grid_point_cloud: [-0.5, 0.5]
            seen = np.zeros_like(counts, dtype=bool); seen[idx[:, 0], idx[:, 1], idx[:, 2]] = True
            counts += seen  # entropy_of_occupancy_grid: each cloud marks the cells it occupies once
        return counts.ravel()
    P, Q = grid_var(sample_pcs), grid_var(ref_pcs)
    from scipy.stats import entropy
    P_, Q_ = P / P.sum(), Q / Q.sum()
    return float(entropy((P_ + Q_) / 2, base=2) - (entropy(P_, base=2) + entropy(Q_, base=2)) / 2)


def report() -> None:
    import numpy as np
    geo = [json.loads(l) for l in (OUT / "geometry.jsonl").read_text().splitlines()]
    sem = {(r["id"], r["system"]): r for r in json.loads((OUT / "semantic.json").read_text())} if (OUT / "semantic.json").exists() else {}
    exact = {}
    for name, path in SYSTEMS.items():
        g = path.with_name(path.stem + "-geometry.jsonl")
        if g.exists():
            for l in g.read_text().splitlines():
                r = json.loads(l); exact[(r["id"], name)] = bool(r["match_strict"])
    table = {}
    for dataset in ("BenchCAD", "CAD-Editor"):
        rows = [r for r in geo if r.get("dataset") == dataset and "systems" in r]
        for name in SYSTEMS:
            ms = [(r["id"], r["systems"][name]) for r in rows if name in r["systems"]]
            if not ms:
                continue
            valid = [(i, m) for i, m in ms if m.get("valid")]
            cd = [m["chamfer"] for _, m in valid]; iou = [m["voxel_iou"] for _, m in valid]
            dclip = [sem[(i, name)]["dclip"] for i, _ in valid if (i, name) in sem]
            dino = [sem[(i, name)]["dino"] for i, _ in valid if (i, name) in sem]
            pcs = [np.load(OUT / "assets" / f"{m['key']}.npy") for _, m in valid]
            refs = [np.load(OUT / "assets" / f"{i[:16]}__reference__.npy") for i, _ in ms if (OUT / "assets" / f"{i[:16]}__reference__.npy").exists()]
            n = len(ms)
            table.setdefault(dataset, {})[name] = dict(
                tasks=n, exact_match=sum(exact.get((i, name), False) for i, _ in ms),
                validity=round(100 * len(valid) / n, 1),
                chamfer_mean_x1e3=round(1e3 * float(np.mean(cd)), 2) if cd else None, chamfer_median_x1e3=round(1e3 * float(np.median(cd)), 2) if cd else None,
                voxel_iou_mean_fail0=round(float(np.sum(iou)) / n, 3), voxel_iou_median_valid=round(float(np.median(iou)), 3) if iou else None,
                dino_mean_fail0=round(float(np.sum(dino)) / n, 3) if dino else None, dino_median_valid=round(float(np.median(dino)), 3) if dino else None,
                dclip_mean=round(float(np.mean(dclip)), 4) if dclip else None,
                jsd=round(jsd(pcs, refs), 4) if pcs and refs else None)
    (OUT / "report.json").write_text(json.dumps(table, indent=1))
    for dataset, systems in table.items():
        print(f"\n{dataset}")
        for name, m in systems.items():
            print(f"  {name:34s} " + " ".join(f"{k}={v}" for k, v in m.items()))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("geometry", "semantic", "report"))
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    {"geometry": lambda: geometry(a.workers), "semantic": semantic, "report": report}[a.cmd]()


if __name__ == "__main__":
    main()
