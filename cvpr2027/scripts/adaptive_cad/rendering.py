"""Native CAD rendering for Astra semantic verification, no learned local model."""
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RENDER_WORKER = '\nimport json, sys\nsys.path.insert(0, sys.argv[2])\nimport numpy as np, matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt\nfrom mpl_toolkits.mplot3d.art3d import Poly3DCollection\nfrom verify_mechanical_cad_edits import execute\njob = json.load(open(sys.argv[1]))\nsrc, cand = execute(job["source"]), execute(job["candidate"])\ndef mesh(s):\n    v, f = s.tessellate(0.4); return np.array([p.toTuple() for p in v]), np.array(f)\nms = [mesh(src), mesh(cand)]\nallv = np.vstack([m[0] for m in ms]); lo, hi = allv.min(0), allv.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 * 1.05\nfig = plt.figure(figsize=(6.4, 6.4), dpi=80)\nfor row, (elev, azim, name) in enumerate(((28, -55, "isometric"), (90, -90, "top"))):\n    for col, (v, f) in enumerate(ms):\n        ax = fig.add_subplot(2, 2, row * 2 + col + 1, projection="3d")\n        tri = v[f]; n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12\n        shade = 0.35 + 0.65 * np.clip(np.abs(n @ np.array([0.3, -0.5, 0.8])), 0, 1)\n        ax.add_collection3d(Poly3DCollection(tri, facecolors=plt.cm.Blues(shade * 0.8 + 0.2), edgecolor="none"))\n        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)\n        ax.view_init(elev, azim); ax.set_axis_off(); ax.set_box_aspect((1, 1, 1), zoom=1.45)\n        ax.set_title(("original " if col == 0 else "edited ") + name, fontsize=9)\nfig.tight_layout(); fig.savefig(sys.argv[3]); print("ok")\n'

def renderer(python=None,timeout=120):
    runtime=str(python or ROOT/'tmp/cad-runtime/bin/python')
    def render(source,code,png):
        png=Path(png);png.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'worker.py';src=Path(d)/'input.json'
            w.write_text(RENDER_WORKER);src.write_text(json.dumps({'source':source,'candidate':code}))
            try:
                p=subprocess.run([runtime,str(w),str(src),str(ROOT/'scripts'),str(png)],capture_output=True,timeout=timeout)
                return p.returncode==0 and png.exists()
            except subprocess.TimeoutExpired:return False
    return render
