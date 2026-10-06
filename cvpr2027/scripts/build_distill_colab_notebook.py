"""Build the credential-free Colab notebook for the verifier-guided distillation student (Qwen2.5-Coder-3B)."""
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from multisource_cad_astra_benchmark import _local_reference, _reference_index  # noqa: E402

DATA = ROOT / "data/multisource-cad-distill-v1"
SCRIPTS = ["train_distill_cad_colab.py", "decode_split_colab.py", "cad_edit_contracts.py", "cad_edit_verifier.py", "cad_editor_geometry.py",
           "verify_mechanical_cad_edits.py", "score_multisource_cad_geometry.py"]
BASELINES = {"3B SFT, patch only (runs/multisource-cad-colab-20261002, local re-score)": (39, 25, 14),
             "Astra gpt-6-astra, zero-shot (runs/multisource-cad-astra-20261004)": (106, 89, 17)}


def bundle() -> bytes:
    index, buffer = _reference_index(), io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        def add(name, data):
            info = tarfile.TarInfo(name)
            info.size, info.mtime = len(data), 0
            tar.addfile(info, io.BytesIO(data))
        for name in SCRIPTS:
            add("scripts/" + name, (ROOT / "scripts" / name).read_bytes())
        references = {}
        for variant in ("template", "distill", "distill-ref"):
            manifest = json.loads((DATA / variant / "manifest.json").read_text())
            for split in ("train", "validation", "test"):
                rows = [json.loads(l) for l in (DATA / variant / f"{split}.jsonl").read_text().splitlines()]
                for r in rows:
                    if split == "test" and r.get("reference_step"):
                        references[r["id"]] = Path(_local_reference(r, index))
                    if r.get("reference_step"):
                        r["reference_step"] = f"/content/cad_distill/references/{r['id']}.step"
                data = "".join(json.dumps(r) + "\n" for r in rows).encode()
                manifest["files"][split] = hashlib.sha256(data).hexdigest()
                add(f"data/{variant}/{split}.jsonl", data)
            manifest["portable_reference_remap"] = "Only STEP paths changed; inputs, targets and patches unchanged."
            add(f"data/{variant}/manifest.json", json.dumps(manifest, indent=2).encode())
        for rid, path in sorted(references.items()):
            add(f"references/{rid}.step", path.read_bytes())
    return buffer.getvalue()


def main() -> None:
    payload = bundle()
    encoded = "\n".join(textwrap.wrap(base64.b64encode(payload).decode(), 1024))
    cells = []

    def md(s):
        cells.append(dict(cell_type="markdown", metadata={}, source=s.splitlines(True)))

    def code(s, form=False):
        cells.append(dict(cell_type="code", execution_count=None, outputs=[],
                          metadata={"cellView": "form"} if form else {}, source=s.splitlines(True)))
    md("# CAD editing: verifier-guided distillation, Astra teacher -> Qwen2.5-Coder-3B student\n\n"
       "Same QLoRA recipe, splits and scorer as the completed 3B run; only the training targets change.\n"
       "Targets are `PLAN:` (quoted zero-based original lines) then `PATCH:` (the JSON patch).\n\n"
       "* **template**: plans generated from the reference patch, no teacher (control; isolates the plan format).\n"
       "* **distill**: BenchCAD training rows whose Astra candidates pass the target-free CAD verifier "
       "(execution gates + numeric checks + geometric consensus of n samples) use the teacher's answer.\n"
       "* **distill-ref**: as distill, keeping only teacher answers that also match the training reference.\n\n"
       "Use **Runtime -> Change runtime type -> GPU** (A100/L4 is ~4x faster than T4), then **Run all**. "
       "No API keys or passwords are in this notebook; teacher outputs were generated beforehand on the "
       "training split only.")
    code('!pip -q install "transformers==4.51.3" "peft==0.15.2" accelerate bitsandbytes "cadquery==2.8.0"\n'
         "!apt-get -qq update && apt-get -qq install -y libglu1-mesa libgl1\n"
         "import torch\nassert torch.cuda.is_available(), 'Select a GPU runtime first'\n"
         "print(torch.cuda.get_device_name(0), torch.cuda.mem_get_info())")
    code("#@title Unpack data, scripts and test reference STEP files\nimport base64, hashlib, io, tarfile\n"
         "from pathlib import Path\nencoded = \"\"\"\n" + encoded + "\n\"\"\"\nbundle = base64.b64decode(encoded)\n"
         f"assert hashlib.sha256(bundle).hexdigest() == \"{hashlib.sha256(payload).hexdigest()}\"\n"
         "ROOT = Path('/content/cad_distill'); ROOT.mkdir(exist_ok=True)\n"
         "tarfile.open(fileobj=io.BytesIO(bundle), mode='r:gz').extractall(ROOT)\n"
         "for v in ['template', 'distill']:\n"
         "    import json; m = json.loads((ROOT/'data'/v/'manifest.json').read_text())\n"
         "    print(v, m['counts']['train'], m.get('acceptance'), m.get('teacher_audit'))", form=True)
    code("#@title Which student to train\nVARIANTS = ['distill']  #@param {type:\"raw\"}\n"
         "# distill: verifier-selected teacher answers (consensus of 2 Astra samples), no reference used\n"
         "# distill-ref: additionally keeps only teacher answers whose solid matches the reference (training split)\n"
         "# Each takes ~1.3 h on an L4; drop one to halve the run. 'template' results already exist.")
    md("## Train, evaluate and decode validation (background job)\n\nTwo epochs; final checkpoint; greedy decoding "
       "on all 252 held-out tasks, then on the 172 validation tasks (used offline to check the plan-quote "
       "anchoring rule on data that played no part in designing it). Runs as a background process logging to "
       "`train.log`, so a dropped VS Code or browser connection does not stop it: reconnect and re-run the wait "
       "cell. A completed variant is never retrained; an incomplete one is moved aside and restarted.")
    code("import json, os, subprocess, sys, time\nLOG, PID = ROOT/'train.log', ROOT/'train.pid'\n"
         "def status(v):  # completed only if trained on exactly the current data files\n"
         "    m = ROOT/f'results-{v}'/'run_manifest.json'\n"
         "    if not m.exists(): return None\n"
         "    run = json.loads(m.read_text())\n"
         "    same = run.get('source_manifest', {}).get('files') == json.loads((ROOT/'data'/v/'manifest.json').read_text())['files']\n"
         "    return run['status'] if same else 'stale'\n"
         "def alive():\n    if LOG.exists() and 'EXIT=' in LOG.read_text(errors='replace')[-300:]: return False\n    try:\n        os.kill(int(PID.read_text()), 0); return True\n"
         "    except (OSError, ValueError):\n        return False\n"
         "steps = []\nfor v in VARIANTS:\n    run = ROOT/f'results-{v}'\n"
         "    if status(v) != 'completed':\n"
         "        if run.exists() and not alive(): run.rename(run.with_name(f'{run.name}.incomplete-{int(time.time())}'))\n"
         "        steps.append(f'{sys.executable} -u {ROOT}/scripts/train_distill_cad_colab.py --data {ROOT}/data/{v} --output {run}')\n"
         "    if not (run/'validation-predictions.jsonl').exists():\n"
         "        steps.append(f'{sys.executable} -u {ROOT}/scripts/decode_split_colab.py --data {ROOT}/data/{v} --run {run} --split validation')\n"
         "if alive():\n    print('Job already running: go to the next cell')\n"
         "elif not steps:\n    print('All requested variants are trained and decoded')\nelse:\n"
         "    proc = subprocess.Popen(f'(cd {ROOT}/scripts && ' + ' && '.join(steps) + f') > {LOG} 2>&1; echo EXIT=$? >> {LOG}', shell=True, start_new_session=True)\n"
         "    PID.write_text(str(proc.pid)); print('Started', len(steps), 'steps, pid', proc.pid)")
    code("#@title Wait for training (re-run after a reconnect)\nseen = 0\nwhile True:\n"
         "    lines = LOG.read_text(errors='replace').replace('\\r', '\\n').splitlines() if LOG.exists() else []\n"
         "    for line in lines[seen:]:\n"
         "        if any(k in line for k in (\"'loss'\", \"'eval_loss'\", 'trained ', 'validation ', 'EXIT=', 'Error', 'Traceback', 'train_runtime')):\n"
         "            print(line[:300], flush=True)\n    seen = len(lines)\n"
         "    if any(l.startswith('EXIT=') for l in lines): break\n    time.sleep(60)\n"
         "assert 'EXIT=0' in lines[-1], '\\n'.join(lines[-60:])\nprint('Training, test and validation decoding finished')")
    md("## Execute predictions against the reference solids\n\nBenchCAD uses author-released STEP targets; "
       "CAD-Editor uses locally reconstructed sequence targets. Strict = volume IoU >= 0.99999.")
    code("for v in VARIANTS:\n    run = ROOT/f'results-{v}'\n"
         "    subprocess.run([sys.executable, '-u', str(ROOT/'scripts/score_multisource_cad_geometry.py'), "
         "str(run/'trained-predictions.jsonl')], check=True, cwd=ROOT/'scripts', stdout=subprocess.DEVNULL)\n"
         f"baselines = {json.dumps(BASELINES)}\n"
         "print(f\"{'system':78s} strict  BenchCAD  CAD-Editor\")\n"
         "for name, (a, b, c) in baselines.items(): print(f'{name:78s} {a:6d} {b:9d} {c:11d}')\n"
         "for v in VARIANTS:\n    g = json.loads((ROOT/f'results-{v}'/'trained-predictions-geometry.json').read_text())\n"
         "    print(f\"{'3B student, '+v:78s} {g['match_strict']:6d} {g['sources']['BenchCAD']['match_strict']:9d} "
         "{g['sources']['CAD-Editor']['match_strict']:11d}\")")
    md("## Save results into this notebook\n\n`files.download` and `drive.mount` are unavailable when a local "
       "notebook runs on a Colab kernel from VS Code, so the small result files (predictions, geometry scores, "
       "metrics, manifests, training history) are printed below as base64 between BEGIN/END markers. **Save the "
       "notebook (Cmd/Ctrl+S)** so the output is written to the .ipynb. Adapter weights (~40 MB) are excluded; "
       "their SHA-256 is in run_manifest.json. In browser Colab a full ZIP is also downloaded.")
    code("import base64, hashlib, io, tarfile, zipfile\nfor v in VARIANTS:\n    run = ROOT/f'results-{v}'\n"
         "    buf = io.BytesIO()\n    with tarfile.open(fileobj=buf, mode='w:gz') as tar:\n"
         "        for f in sorted(run.rglob('*')):\n"
         "            if f.is_file() and 'checkpoints' not in f.parts and (f.parent.name != 'adapter' or f.name == 'adapter_config.json'):\n"
         "                tar.add(f, arcname=str(f.relative_to(run)))\n"
         "    data = buf.getvalue(); text = base64.b64encode(data).decode()\n"
         "    print(f'BEGIN-RESULTS {v} {len(data)} {hashlib.sha256(data).hexdigest()}')\n"
         "    for i in range(0, len(text), 1000): print(text[i:i + 1000])\n    print(f'END-RESULTS {v}')\n"
         "    try:\n        from google.colab import files\n"
         "        archive = Path(f'/content/cad-distill-{v}-results.zip')\n"
         "        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:\n"
         "            for f in run.rglob('*'):\n"
         "                if f.is_file() and 'checkpoints' not in f.parts: z.write(f, f.relative_to(run))\n"
         "        files.download(str(archive))\n"
         "    except Exception as error:\n        print('ZIP download unavailable here:', type(error).__name__)")
    nb = dict(nbformat=4, nbformat_minor=5, cells=cells,
              metadata=dict(colab=dict(name="CAD_Astra_Distill_Train.ipynb", provenance=[]), accelerator="GPU",
                            kernelspec=dict(name="python3", display_name="Python 3"), language_info=dict(name="python")))
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "notebooks/CAD_Astra_Distill_Train.ipynb"
    out.write_text(json.dumps(nb, indent=1) + "\n")
    print(out, "bytes", out.stat().st_size, "bundle sha256", hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    main()
