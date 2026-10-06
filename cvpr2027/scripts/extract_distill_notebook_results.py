"""Recover distillation results printed into a saved notebook (BEGIN-RESULTS/END-RESULTS base64 blocks).

  python extract_distill_notebook_results.py notebooks/CAD_Astra_Distill_Train.ipynb runs/cad-distill-colab-YYYYMMDD
"""
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile


def main() -> None:
    notebook, out = Path(sys.argv[1]), Path(sys.argv[2])
    text = "".join("".join(o.get("text", "")) if isinstance(o.get("text"), list) else o.get("text", "")
                   for cell in json.loads(notebook.read_text())["cells"] for o in cell.get("outputs", []))
    found = 0
    for block in text.split("BEGIN-RESULTS ")[1:]:
        header, rest = block.split("\n", 1)
        variant, size, digest = header.split()
        data = base64.b64decode("".join(rest.split(f"END-RESULTS {variant}")[0].split()))
        assert len(data) == int(size) and hashlib.sha256(data).hexdigest() == digest, f"{variant}: corrupt block"
        target = out / f"results-{variant}"
        target.mkdir(parents=True, exist_ok=True)
        tarfile.open(fileobj=io.BytesIO(data), mode="r:gz").extractall(target)
        print(variant, "->", target, sorted(p.name for p in target.iterdir()))
        found += 1
    if not found:
        raise SystemExit("No BEGIN-RESULTS blocks: was the notebook saved after the export cell ran?")


if __name__ == "__main__":
    main()
