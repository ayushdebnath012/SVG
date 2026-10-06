"""Build the Colab notebook that runs open Qwen models on Parametric CAD Bench v2 and scores them officially."""
import base64
import hashlib
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tmp/cadbench/harbor-tasks/cad-bench"
FILES = ["instruction.md", "tests/run_scorer.py", "tests/grader/spec.json", "tests/grader/param_check.py",
         "tests/grader/reference.FCStd"]
MODELS = [("qwen2.5-coder-3b", "Qwen/Qwen2.5-Coder-3B-Instruct"),
          ("qwen2.5-coder-7b", "Qwen/Qwen2.5-Coder-7B-Instruct"),
          ("qwen2.5-coder-32b-awq", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")]


def main() -> None:
    hashes = {f"{t.name}/{f}": hashlib.sha256((t / f).read_bytes()).hexdigest()
              for t in sorted(TASKS.glob("freecad-*")) for f in FILES if (t / f).exists()}
    published = json.loads((ROOT / "tmp/cadbench/published_v2_means.json").read_text())
    agent = base64.b64encode((ROOT / "scripts/cadbench_colab_agent.py").read_bytes()).decode()
    cells = []

    def md(s):
        cells.append(dict(cell_type="markdown", metadata={}, source=s.splitlines(True)))

    def code(s):
        cells.append(dict(cell_type="code", execution_count=None, outputs=[], metadata={}, source=s.splitlines(True)))
    md("# Parametric CAD Bench v2: open Qwen models with execution feedback\n\n"
       "Runs Qwen2.5-Coder 3B / 7B / 32B-AWQ on the 100 official `gnucleus-ai/cad-bench@v2` tasks and scores "
       "them with each task's own verifier (`gnucleus-freecad-validator==0.4.0` on conda-forge FreeCAD 1.1.0, "
       "the leaderboard's runtime). Protocol: verbatim task instruction, greedy decoding, the model returns "
       "answer.py; FreeCAD executes it; a Python error, missing FCStd, or a non-PartDesign document is sent back "
       "for up to 3 repairs. The reference part and the grader's spec files are used only for final scoring.\n\n"
       "**Runtime -> Change runtime type -> A100 GPU** (32B-AWQ needs >= 24 GB), then **Run all**. Use a runtime "
       "that is not still training the distillation student. Save the notebook (Cmd/Ctrl+S) at the end.")
    code("!pip -q install vllm uv\nimport torch\nassert torch.cuda.is_available(), 'Select a GPU runtime'\n"
         "print(torch.cuda.get_device_name(0), round(torch.cuda.mem_get_info()[1] / 2**30), 'GB')")
    code("#@title FreeCAD 1.1.0 + validator 0.4.0 (same packages as the official verifier image)\n"
         "!curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C /content bin/micromamba\n"
         "!/content/bin/micromamba create -q -y -p /content/fcenv -c conda-forge python=3.12 \"freecad=1.1.0\" "
         "\"numpy=2.4.6\" scipy pydantic\n"
         "!echo /content/fcenv/lib > $(/content/fcenv/bin/python -c 'import site; print(site.getsitepackages()[0])')/freecad.pth\n"
         "!/content/fcenv/bin/python -m pip install -q \"gnucleus-freecad-validator==0.4.0\"\n"
         "import os\nos.environ['FREECAD_LIB'] = '/content/fcenv/lib:/content/fcenv/Mod:/content/fcenv/share/Mod'\n"
         "!/content/fcenv/bin/python -c \"import FreeCAD, importlib.metadata as m; print(FreeCAD.Version()[:3], "
         "m.version('gnucleus-freecad-validator'))\"")
    code("#@title Official task suite (Harbor) checked against the locally verified file hashes\n"
         "import base64, hashlib, json\nfrom pathlib import Path\n"
         "!uvx --from harbor harbor download gnucleus-ai/cad-bench@v2 -o /content/cadbench\n"
         "TASKS = Path('/content/cadbench/cad-bench')\n"
         f"HASHES = json.loads('''{json.dumps(hashes)}''')\n"
         "bad = [k for k, h in HASHES.items() if not (TASKS / k).exists() or hashlib.sha256((TASKS / k).read_bytes()).hexdigest() != h]\n"
         "assert not bad, f'{len(bad)} task files differ from the verified suite, e.g. {bad[:3]}'\n"
         "print(len(list(TASKS.glob('freecad-*'))), 'tasks;', len(HASHES), 'files verified')\n"
         "Path('/content/cadbench_colab_agent.py').write_bytes(base64.b64decode('''" + "\n".join(textwrap.wrap(agent, 1000))
         + "'''))")
    code("#@title Models\nMODELS = " + json.dumps(MODELS) + "\nREPAIRS = 3\n"
         "if torch.cuda.mem_get_info()[1] < 30 * 2**30 and any('32b' in t for t, _ in MODELS):\n"
         "    MODELS = [m for m in MODELS if '32b' not in m[0]]\n"
         "    print('GPU under 30 GB: the 32B model is skipped (it needs an A100 40/80 GB)')\n"
         "print(MODELS)")
    md("## Generate, execute, repair, score (background job)\n\nEach model runs in its own process (GPU memory is "
       "released between models) and is scored right after. Re-run the wait cell after a reconnect.")
    code("import subprocess, sys, time\nOUT, LOG, PID = Path('/content/cadbench-out'), Path('/content/cadbench.log'), "
         "Path('/content/cadbench.pid')\n"
         "def alive():\n    try:\n        os.kill(int(PID.read_text()), 0); return True\n    except (OSError, ValueError):\n        return False\n"
         "if alive():\n    print('Already running')\nelse:\n    steps = []\n    for tag, model in MODELS:\n"
         "        if (OUT / tag / 'summary.json').exists(): continue\n"
         "        common = f'--tasks {TASKS} --out {OUT} --tag {tag} --fc-python /content/fcenv/bin/python'\n"
         "        steps.append(f'{sys.executable} -u /content/cadbench_colab_agent.py run {common} --model {model} --repairs {REPAIRS}')\n"
         "        steps.append(f'{sys.executable} -u /content/cadbench_colab_agent.py score {common}')\n"
         "    proc = subprocess.Popen('(' + ' && '.join(steps) + f') > {LOG} 2>&1; echo EXIT=$? >> {LOG}', shell=True, start_new_session=True)\n"
         "    PID.write_text(str(proc.pid)); print('Started', len(steps) // 2, 'models')")
    code("#@title Wait (re-run after a reconnect)\nseen = 0\nwhile True:\n"
         "    lines = LOG.read_text(errors='replace').splitlines() if LOG.exists() else []\n"
         "    for line in lines[seen:]:\n"
         "        if any(k in line for k in ('round ', 'mean_combined', 'EXIT=', 'Error', 'Traceback')): print(line[:300], flush=True)\n"
         "    seen = len(lines)\n    if any(l.startswith('EXIT=') for l in lines): break\n    time.sleep(60)\n"
         "print('\\n'.join(lines[-40:]) if 'EXIT=0' not in lines[-1] else 'All models finished')")
    code("#@title Results next to the published v2 leaderboard (mean reward over 100 tasks)\n"
         f"PUBLISHED = {json.dumps([(r['agent'], r['model'], r['effort'], r['mean']) for r in published])}\n"
         "rows = [(f'{a} / {m} ({e})', v) for a, m, e, v in PUBLISHED]\n"
         "for tag, _ in MODELS:\n    s = OUT / tag / 'summary.json'\n"
         "    if s.exists():\n        d = json.loads(s.read_text())\n"
         "        rows.append((f'{tag} + FreeCAD feedback ({REPAIRS} repairs), single-shot chat', d['mean_combined']))\n"
         "        print(tag, 'passing execution+gates by round:', [r['passing_total'] for r in d['rounds']])\n"
         "for name, v in sorted(rows, key=lambda r: -r[1]): print(f'{v:8.4f}  {name}')")
    md("## Save results into this notebook\n\nPrints answer.py, transcripts and per-task scores (no FCStd; answers "
       "are re-executable) as base64 between BEGIN/END markers. **Save the notebook afterwards.**")
    code("import io, tarfile\nbuf = io.BytesIO()\nwith tarfile.open(fileobj=buf, mode='w:gz') as tar:\n"
         "    for f in sorted(OUT.rglob('*')):\n"
         "        if f.is_file() and f.suffix in ('.py', '.json') and not f.name.startswith('_'):\n"
         "            tar.add(f, arcname=str(f.relative_to(OUT)))\n"
         "data = buf.getvalue(); text = base64.b64encode(data).decode()\n"
         "print(f'BEGIN-RESULTS cadbench {len(data)} {hashlib.sha256(data).hexdigest()}')\n"
         "for i in range(0, len(text), 1000): print(text[i:i + 1000])\nprint('END-RESULTS cadbench')")
    nb = dict(nbformat=4, nbformat_minor=5, cells=cells,
              metadata=dict(colab=dict(name="CadBench_Open_Models.ipynb", provenance=[]), accelerator="GPU",
                            kernelspec=dict(name="python3", display_name="Python 3"), language_info=dict(name="python")))
    out = ROOT / "notebooks/CadBench_Open_Models.ipynb"
    out.write_text(json.dumps(nb, indent=1) + "\n")
    print(out, out.stat().st_size, "bytes;", len(hashes), "hashed task files")


if __name__ == "__main__":
    main()
