"""Run a language model on the SimJEB CAD + FEM benchmark (scripts/simjeb_bench.py) and score it.

Modes
  oneshot  the model gets the task and answers once with CadQuery code (no tools).
  agent    the model works with tools under budgets, then submits:
             run_cadquery(code)  build the part; returns errors or mass, bounding box, rule checks (and views)
             fem_check(code)     preview FEM on a coarser mesh (2 mm): per-case peak stress, displacement, pass/fail
             submit(code)        final answer, graded by the benchmark's full evaluation (1.2 mm mesh)
           For redesign / lighten tasks the original part is available to the code as ORIGINAL_STEP
           (e.g. base = cq.importers.importStep(ORIGINAL_STEP)).

Providers (keys from the environment; nothing is stored)
  openai     OpenAI-compatible chat completions with function calling: OpenAI (OPENAI_API_KEY), Gemini via
             --base-url https://generativelanguage.googleapis.com/v1beta/openai/ (GEMINI_API_KEY), OpenRouter
             (OPENROUTER_API_KEY), DeepSeek, or a local vLLM server (no key).
  anthropic  Anthropic Messages API (ANTHROPIC_API_KEY).

  python simjeb_agent.py run --tasks data/simjeb-bench/frontier.jsonl --provider anthropic --model claude-opus-5-5 \\
         --mode agent --out tmp/simjeb/runs/opus --api-key-env ANTHROPIC_API_KEY
  python simjeb_bench.py score --results tmp/simjeb/runs/opus/results.jsonl

Model-written code runs on this machine in a subprocess with a timeout; run inside a container for untrusted models.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("simjeb_bench", HERE / "simjeb_bench.py")
bench = importlib.util.module_from_spec(_s)
_s.loader.exec_module(bench)

PREVIEW_MESH = 2.0
SYSTEM = ("You are a mechanical design engineer. You write CadQuery (Python, cadquery 2.x) that assigns the finished "
          "single solid to a variable named `result`. Units are millimetres. Check your work with the tools before "
          "submitting; budgets are limited.")
TOOLS = [
    dict(name="run_cadquery", description="Build the part from CadQuery code (the code must assign the solid to `result`). "
         "Returns build errors, or mass, bounding box, solid count and rule checks; with images enabled, also views of the part.",
         parameters=dict(type="object", properties=dict(code=dict(type="string")), required=["code"])),
    dict(name="fem_check", description="Preview FEM of the part built by this CadQuery code: the four load cases on a coarser "
         "mesh (about 2 mm, results within roughly 10 % of the final grading). Returns per-case peak von Mises stress (with "
         "location), maximum displacement, safety factor, pass / fail and interface checks.",
         parameters=dict(type="object", properties=dict(code=dict(type="string")), required=["code"])),
    dict(name="submit", description="Submit the final CadQuery code. Ends the task.",
         parameters=dict(type="object", properties=dict(code=dict(type="string"), notes=dict(type="string")), required=["code"])),
]


# ---------------------------------------------------------------- tools
def build(code: str, task: dict, work: Path, tag: str) -> tuple[Path | None, str | None]:
    pre = f"ORIGINAL_STEP = {str(bench.ROOT / task['step'])!r}\n" if task.get("step") else ""
    src = work / f"{tag}.py"
    src.write_text(pre + code)
    step = work / f"{tag}.step"
    err = bench.run_cadquery(src, step)
    return (None, err) if err else (step, None)


def render(step: Path, out_png: Path) -> bool:
    script = f'''
import cadquery as cq, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
s = cq.importers.importStep({str(step)!r}).val()
v, t = s.tessellate(0.3, 0.3)
V = np.array([p.toTuple() for p in v]); T = np.array(t)
P = V[T]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
fig = plt.figure(figsize=(12, 4), dpi=90)
for k, (el, az, title) in enumerate(((25, -60, "iso"), (90, -90, "top (+z)"), (0, -90, "front (-y)"))):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    sh = 0.35 + 0.65 * np.abs(n @ np.array([0.3, -0.4, 0.85]) / np.linalg.norm([0.3, -0.4, 0.85]))
    ax.add_collection3d(Poly3DCollection(P, facecolors=np.c_[sh, sh, sh * 1.05].clip(0, 1), edgecolors="none"))
    lo, hi = V.min(0), V.max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_title(title, fontsize=9)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
fig.savefig({str(out_png)!r}, bbox_inches="tight")
'''
    r = subprocess.run([str(bench.CAD_PY), "-I", "-c", script], capture_output=True, text=True, timeout=300)
    return r.returncode == 0 and out_png.exists()


def quick_checks(step: Path, task: dict, env: dict) -> dict:
    chk = subprocess.run([str(bench.CAD_PY), "-I", str(HERE / "cad_checks.py"), str(step), "--samples", "1500"],
                         capture_output=True, text=True, timeout=900)
    lines = [ln for ln in chk.stdout.splitlines() if ln.startswith("{")]
    c = json.loads(lines[-1]) if lines else dict(error=chk.stderr[-300:])
    rho = (task.get("props") or bench.MATERIALS["Ti-6Al-4V"])["rho"]
    out = dict(solids=c.get("solids"), mass_kg=c["volume_mm3"] * rho * 1e3 if c.get("volume_mm3") else None,
               bbox_min=c.get("bbox_min"), bbox_max=c.get("bbox_max"), rule_violations=bench.geometry_rules(c, env))
    if task.get("mass_limit_kg"):
        out["mass_limit_kg"] = task["mass_limit_kg"]
    return out


def fem_preview(step: Path, task: dict) -> dict:
    g = bench.fem_grade(step, task.get("props"), task.get("load_scale", 1.0), PREVIEW_MESH)
    itf = bench.interface_rules(g.get("interfaces") or {}) if g.get("interfaces") else ["GE interfaces not found"]
    out = dict(passed=g.get("passed") if not itf else False, safety_factor=g.get("safety_factor"),
               worst_case=g.get("worst_case"), mass_kg=g.get("mass_kg"), interface_violations=itf, error=g.get("reason"))
    if g.get("cases"):
        out["cases"] = {c: dict(peak_von_mises_MPa=round(v["peak_von_mises_MPa"], 1), peak_at_mm=v["peak_at"],
                                max_displacement_mm=round(v["max_displacement_mm"], 4)) for c, v in g["cases"].items()}
    return out


# ---------------------------------------------------------------- model clients
def http_json(url: str, body: dict, headers: dict, timeout: int = 900) -> dict:
    req = urllib.request.Request(url, json.dumps(body).encode(), dict({"Content-Type": "application/json"}, **headers))
    for attempt in range(5):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 4:
                time.sleep(20 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:500]!r}") from e
    raise RuntimeError("unreachable")


class OpenAIChat:
    def __init__(self, model, base_url, key, max_tokens, images):
        self.model, self.url, self.key, self.max_tokens, self.images = model, base_url.rstrip("/") + "/chat/completions", key, max_tokens, images
        self.messages, self.usage = [], dict(input_tokens=0, output_tokens=0)

    def start(self, system, user):
        self.messages = [dict(role="system", content=system), dict(role="user", content=user)]

    def step(self, tools: bool):
        body = {"model": self.model, "messages": self.messages, getattr(self, "token_field", "max_completion_tokens"): self.max_tokens}
        if tools:
            body["tools"] = [dict(type="function", function=t) for t in TOOLS]
        r = http_json(self.url, body, {"Authorization": f"Bearer {self.key}"} if self.key else {})
        u = r.get("usage") or {}
        self.usage["input_tokens"] += u.get("prompt_tokens", 0)
        self.usage["output_tokens"] += u.get("completion_tokens", 0)
        msg = r["choices"][0]["message"]
        self.messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        calls = [dict(id=c["id"], name=c["function"]["name"], args=json.loads(c["function"]["arguments"] or "{}"))
                 for c in msg.get("tool_calls") or []]
        return msg.get("content") or "", calls

    def tool_results(self, results):
        imgs = []
        for call, text, png in results:
            self.messages.append(dict(role="tool", tool_call_id=call["id"], content=text))
            if png and self.images:
                imgs.append(dict(type="image_url", image_url=dict(url="data:image/png;base64," + base64.b64encode(png.read_bytes()).decode())))
        if imgs:
            self.messages.append(dict(role="user", content=[dict(type="text", text="Views of the part:")] + imgs))

    def say(self, text):
        self.messages.append(dict(role="user", content=text))


class AnthropicChat:
    def __init__(self, model, base_url, key, max_tokens, images):
        self.model, self.url, self.key, self.max_tokens, self.images = model, (base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages", key, max_tokens, images
        self.messages, self.system, self.usage = [], "", dict(input_tokens=0, output_tokens=0)

    def start(self, system, user):
        self.system, self.messages = system, [dict(role="user", content=user)]

    def step(self, tools: bool):
        body = dict(model=self.model, system=self.system, messages=self.messages, max_tokens=self.max_tokens)
        if tools:
            body["tools"] = [dict(name=t["name"], description=t["description"], input_schema=t["parameters"]) for t in TOOLS]
        r = http_json(self.url, body, {"x-api-key": self.key, "anthropic-version": "2023-06-01"})
        u = r.get("usage") or {}
        self.usage["input_tokens"] += u.get("input_tokens", 0)
        self.usage["output_tokens"] += u.get("output_tokens", 0)
        self.messages.append(dict(role="assistant", content=r["content"]))
        text = "".join(b.get("text", "") for b in r["content"] if b["type"] == "text")
        calls = [dict(id=b["id"], name=b["name"], args=b["input"]) for b in r["content"] if b["type"] == "tool_use"]
        return text, calls

    def tool_results(self, results):
        blocks = []
        for call, text, png in results:
            content = [dict(type="text", text=text)]
            if png and self.images:
                content.append(dict(type="image", source=dict(type="base64", media_type="image/png", data=base64.b64encode(png.read_bytes()).decode())))
            blocks.append(dict(type="tool_result", tool_use_id=call["id"], content=content))
        self.messages.append(dict(role="user", content=blocks))

    def say(self, text):
        self.messages.append(dict(role="user", content=text))


class ReplayChat:
    """Test client: calls run_cadquery, fem_check and submit with the code from --replay-code (no model, no key)."""
    def __init__(self, model, base_url, key, max_tokens, images, code=""):
        self.code, self.k, self.usage = code, 0, dict(input_tokens=0, output_tokens=0)

    def start(self, system, user):
        self.k = 0

    def step(self, tools: bool):
        self.k += 1
        if not tools:
            return f"```python\n{self.code}\n```", []
        name = ["run_cadquery", "fem_check", "submit"][min(self.k - 1, 2)]
        return "", [dict(id=f"c{self.k}", name=name, args=dict(code=self.code))]

    def tool_results(self, results):
        for _, text, _ in results:
            print("  tool ->", text[:300], flush=True)

    def say(self, text):
        pass


# ---------------------------------------------------------------- episode
def code_from(text: str) -> str | None:
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return max(blocks, key=len) if blocks else None


def episode(task: dict, client, a, env: dict, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    prompt = task["prompt"]
    if task.get("step"):
        prompt += f"\n\nThe original part is available to your code as the STEP file path ORIGINAL_STEP."
        if task.get("current"):
            prompt += "\nCurrent FEM results of the original: " + json.dumps(task["current"].get("cases") or task["current"])[:3000]
    if a.mode == "agent":
        prompt += (f"\n\nBudgets: {a.cad_budget} run_cadquery calls, {a.fem_budget} fem_check calls, {a.max_turns} turns. "
                   "Finish with submit(code).")
    else:
        prompt += "\n\nAnswer with one complete Python code block (CadQuery) that assigns the finished solid to `result`."
    client.start(SYSTEM, prompt)
    log, used, final, t0 = [], dict(run_cadquery=0, fem_check=0), None, time.time()
    for turn in range(a.max_turns if a.mode == "agent" else 1):
        text, calls = client.step(tools=a.mode == "agent")
        log.append(dict(turn=turn, text=text[:4000], calls=[dict(name=c["name"], code=(c["args"].get("code") or "")[:6000]) for c in calls]))
        if a.mode == "oneshot":
            final = code_from(text)
            break
        if not calls:
            final = code_from(text)
            if final or turn == a.max_turns - 1:
                break
            client.say("Use the tools, and finish with submit(code).")
            continue
        results = []
        for c in calls:
            png = None
            if c["name"] == "submit":
                final = c["args"].get("code")
                results.append((c, "submitted", None))
                continue
            if used.get(c["name"], 0) >= (a.cad_budget if c["name"] == "run_cadquery" else a.fem_budget):
                results.append((c, f"{c['name']} budget used up; submit your best code.", None))
                continue
            used[c["name"]] += 1
            step, err = build(c["args"].get("code", ""), task, work, f"t{turn}_{c['name']}_{used[c['name']]}")
            if err:
                out = dict(error=err[-1500:])
            elif c["name"] == "run_cadquery":
                out = quick_checks(step, task, env)
                if a.images:
                    png = work / f"t{turn}_view.png"
                    png = png if render(step, png) else None
            else:
                out = fem_preview(step, task)
            results.append((c, json.dumps(out), png))
        client.tool_results(results)
        if final is not None:
            break
    rec = dict(id=task["id"], family=task["family"], model=a.model, mode=a.mode, turns=len(log), tool_calls=used,
               usage=client.usage, seconds_model_and_tools=round(time.time() - t0, 1))
    (work / "transcript.json").write_text(json.dumps(dict(rec, log=log), indent=1))
    if not final:
        return dict(rec, success=False, valid=False, score=0.0, violations=["no code submitted"])
    (work / "final.py").write_text(final)
    r = subprocess.run([str(bench.FEM_PY), "-I", str(HERE / "simjeb_bench.py"), "evaluate", "--family", task["family"],
                        "--id", task["id"], "--cadquery", str(work / "final.py"), "--out", str(work / "eval")],
                       capture_output=True, text=True, timeout=7200)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    verdict = json.loads(lines[-1]) if lines else dict(success=False, score=0.0, violations=["evaluation crashed"])
    return dict(rec, **{k: v for k, v in verdict.items() if k not in ("id", "family")})


def run(a) -> None:
    tasks = [json.loads(x) for x in open(a.tasks)]
    tasks = [t for t in tasks if t["family"] in ("design", "redesign", "lighten")]
    if a.ids:
        keep = set(a.ids.split(","))
        tasks = [t for t in tasks if t["id"] in keep]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res_file = out / "results.jsonl"
    done = {json.loads(x)["id"] for x in open(res_file)} if res_file.exists() else set()
    key = os.environ.get(a.api_key_env, "") if a.api_key_env else ""
    _, env = bench.load_baseline()
    for t in tasks:
        if t["id"] in done:
            continue
        if a.provider == "replay":
            client = ReplayChat(a.model, None, None, 0, False, Path(a.replay_code).read_text())
        else:
            client = (AnthropicChat if a.provider == "anthropic" else OpenAIChat)(a.model, a.base_url, key, a.max_tokens, a.images)
            client.token_field = a.max_tokens_field
        try:
            row = episode(t, client, a, env, out / t["id"])
        except Exception as e:  # noqa: BLE001 - one failed task must not stop the run
            row = dict(id=t["id"], family=t["family"], model=a.model, success=False, score=0.0, error=f"{type(e).__name__}: {e}"[:500])
        with open(res_file, "a") as h:
            h.write(json.dumps(row) + "\n")
        print(json.dumps({k: row.get(k) for k in ("id", "success", "valid", "passed", "mass_kg", "score", "violations", "tool_calls", "usage")}), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--tasks", required=True)
    r.add_argument("--provider", choices=["openai", "anthropic", "replay"], required=True)
    r.add_argument("--replay-code", help="replay provider: CadQuery file to submit (harness test)")
    r.add_argument("--max-tokens-field", default="max_completion_tokens", help="max_tokens for servers that need it (vLLM, older APIs)")
    r.add_argument("--model", required=True)
    r.add_argument("--base-url", default="https://api.openai.com/v1")
    r.add_argument("--api-key-env", default="")
    r.add_argument("--mode", choices=["oneshot", "agent"], default="agent")
    r.add_argument("--out", required=True)
    r.add_argument("--ids", default="")
    r.add_argument("--max-turns", type=int, default=30)
    r.add_argument("--cad-budget", type=int, default=20)
    r.add_argument("--fem-budget", type=int, default=6)
    r.add_argument("--max-tokens", type=int, default=16000)
    r.add_argument("--images", action="store_true")
    a = p.parse_args()
    if a.provider == "anthropic" and a.base_url == "https://api.openai.com/v1":
        a.base_url = None
    run(a)


if __name__ == "__main__":
    main()
