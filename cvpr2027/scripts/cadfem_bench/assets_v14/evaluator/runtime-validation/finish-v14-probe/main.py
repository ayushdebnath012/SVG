import json, os, socket
from pathlib import Path
T = {"read_this_package": "/Users/ayushdebnath/SVG/cvpr2027/output/datasets/cadfem-bench-v1.4/evaluator/references.jsonl", "read_released_v13": "/Users/ayushdebnath/SVG/cadfem-bench-v1.3/evaluator/references.jsonl", "read_workspace_data": "/Users/ayushdebnath/SVG/cvpr2027/data/femcad-hard-v1/tasks.jsonl", "write_outside": "/Users/ayushdebnath/SVG/cvpr2027/tmp/cadfem-bench-v1.4-sandbox-probe/forbidden.txt"}
r = {}
for k in ("read_this_package", "read_released_v13", "read_workspace_data"):
    try:
        open(T[k]).read(1); r[k] = "ALLOWED"
    except PermissionError:
        r[k] = "denied"
for k, path in (("write_outside", T["write_outside"]), ("modify_input", str(Path(os.environ["CADFEM_INPUT_DIR"]) / "task.json"))):
    try:
        open(path, "a").write("x"); r[k] = "ALLOWED"
    except PermissionError:
        r[k] = "denied"
try:
    socket.create_connection(("1.1.1.1", 443), timeout=2); r["outbound_network"] = "ALLOWED"
except OSError:
    r["outbound_network"] = "denied"
import cadquery, gmsh, numpy, scipy  # the pinned CAD/FEM runtime imports inside the sandbox
r["runtime_imports"] = "ok"
Path("probe.json").write_text(json.dumps(r))
