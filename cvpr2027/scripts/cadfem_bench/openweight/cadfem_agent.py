"""CADFEM-Bench open-weight agent harness (runs on the GPU host next to a local vLLM OpenAI-compatible server).

For every task: a fresh workspace with read-only copies of the task's candidate inputs, a fixed system prompt (the
candidate README contract), and four tools: bash, write_file, read_file, submit, plus view_image for vision models.
Every command the model runs executes under landlock_run. That allows reading the system, the pinned CAD/FEM runtime
and the task inputs, and writing the workspace only; all TCP, including the local model server, is denied. The policy
is kernel-enforced: the host denies namespaces and Docker. After submit, or when the budget runs out, the submitted
*.py files are frozen and main.py is re-run from scratch in a clean sandbox (600 s wall, 600 s CPU, 8 GB RSS). Only
that re-run's artifacts are kept for scoring, under submissions/<run>/<task_id>/. References never reach this host;
scoring happens elsewhere with evaluator/score.py.

  python cadfem_agent.py --suite-dir candidate --run-id gpt-oss-120b-high --model openai/gpt-oss-120b \\
      --base-url http://127.0.0.1:8100/v1 --reasoning-effort high --parallel 6 [--tasks ID ...] [--vision]

Hosted models (e.g. OpenAI gpt-6-astra) use the same tools, prompts, budget and replay with --api responses (OpenAI
Responses API; encrypted reasoning items are passed back each turn, store=False) and a USD cap (--budget-usd with
--price-in/--price-cached/--price-out per million tokens). On macOS (--sandbox macos) commands run under a Seatbelt
profile: no network, no reads below /Users except the runtime, the job and the task inputs, writes only in the job.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

HERE = Path(__file__).resolve().parent
LL = HERE / "landlock_run"
RUNTIME = Path.home() / "miniconda3/envs/cadfem-runtime"     # overridden by --runtime
SANDBOX = "landlock"                                        # or "macos"; set from --sandbox
RUNTIME_BASE = None                                         # macOS: the interpreter's sys.base_prefix (venv base), readable in the sandbox
SYSTEM_RO = ["/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc", "/proc", "/sys"]
DEV_RW = ["/dev/null", "/dev/zero", "/dev/urandom", "/dev/random", "/dev/shm"]
OUT_HEAD, OUT_TAIL = 3000, 9000
LOCK = threading.Lock()
SPEND = dict(usd=0.0)                                       # hosted APIs: running cost of this process (USD)


def call_cost(a, prompt: int, cached: int, completion: int) -> float:
    return ((prompt - cached) * a.price_in + cached * a.price_cached + completion * a.price_out) / 1e6


def over_budget(a, reserve: float = 0.0) -> bool:
    return bool(a.budget_usd) and SPEND["usd"] + reserve >= a.budget_usd


def rtools(vision: bool) -> list:
    """The same tools in Responses API form."""
    return [dict(type="function", name=t["function"]["name"], description=t["function"]["description"], parameters=t["function"]["parameters"]) for t in tools(vision)]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def inventory(d: Path) -> dict:
    return {str(f.relative_to(d)): dict(sha256=sha(f), bytes=f.stat().st_size) for f in sorted(d.rglob("*")) if f.is_file() and not f.is_symlink()}


def group_rss_kb(pgid: int) -> int:
    if SANDBOX == "macos":
        ps = subprocess.run(["/bin/ps", "-axo", "pgid=,rss="], capture_output=True, text=True).stdout
        return sum(int(l.split()[1]) for l in ps.splitlines() if len(l.split()) == 2 and l.split()[0] == str(pgid))
    tot = 0
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            st = (p / "stat").read_text()
            f = st[st.rindex(")") + 2:].split()
            if int(f[2]) == pgid:
                tot += int(f[21]) * 4
        except (OSError, ValueError, IndexError):
            pass
    return tot


def mac_profile(ro: list, rw: list) -> str:
    """Seatbelt: deny network; deny reads below /Users except runtime, base interpreter, inputs and job; deny writes outside the job."""
    q = lambda p: json.dumps(str(Path(p).resolve()))
    reads = [RUNTIME, RUNTIME_BASE] + list(ro) + list(rw)
    s = "(version 1)\n(allow default)\n(deny network*)\n(deny file-read* (subpath \"/Users\"))\n"
    s += "(allow file-read* " + " ".join(f"(subpath {q(p)})" for p in reads if p) + ")\n(allow file-read-metadata)\n"
    s += "(deny file-write*)\n(allow file-write* " + " ".join(f"(subpath {q(p)})" for p in rw) + " (literal \"/dev/null\") (literal \"/dev/zero\"))\n"
    return s


def sandboxed(cmd: list, cwd: Path, ro: list, rw: list, env: dict, wall: int, cpu: int, ram_mb: int, log: Path) -> dict:
    if SANDBOX == "macos":
        prof = log.with_suffix(".sb").resolve()
        prof.write_text(mac_profile(ro, rw))
        args = ["/usr/bin/sandbox-exec", "-f", str(prof)] + cmd
    else:
        args = [str(LL)]
        for p in SYSTEM_RO + [str(RUNTIME)] + [str(x) for x in ro]:
            args += ["--ro", p]
        for p in [str(x) for x in rw] + DEV_RW:
            args += ["--rw", p]
        args += ["--"] + cmd

    def limits():
        import resource
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2 << 30, 2 << 30))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    t0, why, peak = time.monotonic(), None, 0
    with log.open("wb") as out:
        p = subprocess.Popen(args, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, preexec_fn=limits)
        while p.poll() is None:
            if time.monotonic() - t0 > wall:
                why = "wall_time_limit"
            rss = group_rss_kb(p.pid)
            peak = max(peak, rss)
            if rss > ram_mb * 1024:
                why = "memory_limit"
            if why:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                break
            time.sleep(0.25)
        code = p.wait()
    return dict(exit_code=code, elapsed_seconds=round(time.monotonic() - t0, 2), termination_reason=why, peak_rss_kb=peak)


AGENT_TOOLS = HERE / "agent-tools"          # apply_patch, on PATH during the agent session only


def runtime_env(home: Path, inputs: Path, outdir: Path, agent: bool = False) -> dict:
    for d in ("tmp", "cache"):
        (home / d).mkdir(parents=True, exist_ok=True)
    return {"PATH": (f"{AGENT_TOOLS}:" if agent else "") + f"{RUNTIME}/bin:/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(home / "tmp"), "XDG_CACHE_HOME": str(home / "cache"),
            "MPLCONFIGDIR": str(home / "cache"), "LANG": "C.UTF-8", "TZ": "UTC", "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "VECLIB_MAXIMUM_THREADS": "2",
            "CADFEM_INPUT_DIR": str(inputs), "CADFEM_OUTPUT_DIR": str(outdir)}


def clip(s: str) -> str:
    return s if len(s) <= OUT_HEAD + OUT_TAIL else s[:OUT_HEAD] + f"\n...[{len(s) - OUT_HEAD - OUT_TAIL} characters omitted]...\n" + s[-OUT_TAIL:]


def tools(vision: bool) -> list:
    T = [
        dict(type="function", function=dict(name="bash", description="Run a bash command in your workspace (the working directory). Python 3.12 with cadquery, OCP, gmsh, scikit-fem, numpy, scipy and meshio is on PATH as `python`. No network. Returns the exit code and combined stdout/stderr (long output is clipped).",
             parameters=dict(type="object", properties=dict(command=dict(type="string"), timeout_s=dict(type="integer", description="wall-clock limit, at most 900 (default 300)")), required=["command"]))),
        dict(type="function", function=dict(name="write_file", description="Create or overwrite a text file in your workspace (relative path).",
             parameters=dict(type="object", properties=dict(path=dict(type="string"), content=dict(type="string")), required=["path", "content"]))),
        dict(type="function", function=dict(name="read_file", description="Read a text file. Paths are relative to the workspace; use the prefix 'inputs/' for task input files. Returns numbered lines.",
             parameters=dict(type="object", properties=dict(path=dict(type="string"), start_line=dict(type="integer"), max_lines=dict(type="integer")), required=["path"]))),
        dict(type="function", function=dict(name="submit", description="Finish the task. main.py in the workspace will then be re-run from scratch in a clean sandbox and only that run's artifacts are scored.",
             parameters=dict(type="object", properties=dict(summary=dict(type="string")), required=["summary"]))),
    ]
    if vision:
        T.insert(3, dict(type="function", function=dict(name="view_image", description="Look at an image or PDF input file (path with prefix 'inputs/'). PDFs are shown page by page (first 3 pages).",
                         parameters=dict(type="object", properties=dict(path=dict(type="string")), required=["path"]))))
    return T


def system_prompt(contract: str, a, vision: bool) -> str:
    return f"""You are an engineering analysis agent. You solve one CAD + finite-element task by writing and running Python in an isolated {"macOS" if SANDBOX == "macos" else "Linux"} workspace, using the tools provided.

Environment: Python 3.12 with cadquery 2.8 (OpenCASCADE / OCP), gmsh 4.15, scikit-fem 12, numpy, scipy and meshio; CPU only, 2 threads; no internet and no package installation. Task input files are read-only: their directory is in the environment variable CADFEM_INPUT_DIR and readable through read_file with the prefix 'inputs/'. Your workspace is the working directory, and CADFEM_OUTPUT_DIR points to it during this session.{'' if vision else ' You cannot view images: image and PDF inputs are not readable by you, so use the text inputs and the prompt.'}

For editing files you can use write_file, or `apply_patch` in bash (a patch in the '*** Begin Patch' / '*** Update File: path' / '@@' / '*** End Patch' format on stdin).

Deliverable: main.py in the workspace. It must regenerate every required artifact when run as `python main.py`, with CADFEM_INPUT_DIR set and the working directory equal to CADFEM_OUTPUT_DIR (write all outputs there), within 600 s wall time, 600 s CPU and 8 GB memory. Helper .py files next to main.py are allowed. After you call submit, main.py is re-run from scratch in a clean sandbox; only the artifacts of that re-run are scored, so files you create by hand are ignored. Check your numbers (mesh convergence, units, the exact output keys) before submitting.

Budget: at most {a.max_calls} tool calls and {a.max_minutes} minutes of total command execution time (time spent running your bash/apply_patch commands) for this task. Call submit when done.

The artifact contract of the benchmark follows.

{contract}"""


def rmtree_force(path: Path) -> None:
    """Remove a previous attempt; its inputs/ folder was made read-only on purpose."""
    for d, _, files in os.walk(path):
        os.chmod(d, 0o755)
        for f in files:
            try:
                os.chmod(os.path.join(d, f), 0o644)
            except OSError:
                pass
    shutil.rmtree(path)


def norm_tool(name: str) -> str:
    """gpt-oss sometimes leaks harmony markup into the tool name ("bash<|channel|>commentary", "functions.bash")."""
    name = name.split("<|", 1)[0].strip()
    return name[len("functions."):] if name.startswith("functions.") else name


def norm_command(cmd) -> str:
    """Accept the list form some models use for shell tools (["bash", "-lc", "..."])."""
    if isinstance(cmd, list):
        import shlex
        if len(cmd) >= 3 and cmd[0] in ("bash", "sh", "/bin/bash", "/bin/sh") and cmd[1] in ("-c", "-lc"):
            return str(cmd[2])
        return shlex.join(str(x) for x in cmd)
    return str(cmd)


def safe_rel(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if not p.is_relative_to(base.resolve()):
        raise ValueError("path outside the allowed directory")
    return p


def pdf_pages(path: Path, n: int = 3) -> list:
    import pymupdf
    doc = pymupdf.open(path)
    return [doc[i].get_pixmap(dpi=110).tobytes("png") for i in range(min(n, len(doc)))]


def run_task(task: dict, a, contract: str, client: OpenAI) -> dict:
    tid = task["task_id"]
    root = Path(a.out) / a.run_id / tid
    final = root / "result.json"
    if final.exists():
        return json.loads(final.read_text())
    if SPEND.get("no_credit"):               # the provider refused for lack of credit: leave the task unrun
        return dict(task_id=tid, status="not_run_no_credit", usage=dict(prompt_tokens=0, completion_tokens=0, calls=0), generation_seconds=0, execution_verified=False)
    if over_budget(a, a.task_reserve_usd):   # not started (too little left for a typical task); no result.json, so a later run picks it up
        with LOCK:
            print(f"{tid:34s} NOT RUN: USD budget {a.budget_usd} reached (spent {SPEND['usd']:.2f})", flush=True)
        return dict(task_id=tid, status="not_run_usd_budget", usage=dict(prompt_tokens=0, completion_tokens=0, calls=0), generation_seconds=0, execution_verified=False)
    if root.exists():
        old = root / "transcript.jsonl"            # keep the record of an interrupted attempt (its API spend) before restarting
        if old.exists():
            keep = root.parent / "_interrupted" / f"{tid}-{int(old.stat().st_mtime)}.jsonl"
            keep.parent.mkdir(exist_ok=True)
            shutil.copy2(old, keep)
        rmtree_force(root)
    inputs, work = root / "inputs", root / "work"
    inputs.mkdir(parents=True)
    work.mkdir()
    for i in task["inputs"]:
        src = Path(a.suite_dir) / ("tasks" if a.suite_kind == "candidate" else "inputs") / Path(i["path"]).relative_to("tasks")
        dst = inputs / Path(i["path"]).name
        shutil.copy2(src, dst)
        assert sha(dst) == i["sha256"], (tid, i["path"])
        dst.chmod(0o444)
    inputs.chmod(0o555)
    in_inv = inventory(inputs)
    listing = "\n".join(f"- {Path(i['path']).name} ({i['bytes']} bytes, role {i['role']})" for i in task["inputs"]) or "- (none)"
    user = f"Task {tid}: {task['title']}\n\n{task['prompt']}\n\nInput files in CADFEM_INPUT_DIR (also readable as inputs/<name>):\n{listing}"
    sysmsg = system_prompt(contract, a, a.vision)
    msgs = [dict(role="system", content=sysmsg), dict(role="user", content=user)]     # chat API
    items = [dict(role="user", content=user)]                                        # responses API (system text -> instructions)
    trans = (root / "transcript.jsonl").open("w")
    trans.write(json.dumps(dict(event="start", task_id=tid, run_id=a.run_id, model=a.model, system_sha256=hashlib.sha256(sysmsg.encode()).hexdigest(),
                                user_sha256=hashlib.sha256(user.encode()).hexdigest(), time=time.time())) + "\n")
    env = runtime_env(work, inputs, work, agent=True)
    usage = dict(prompt_tokens=0, completion_tokens=0, calls=0, cached_tokens=0, reasoning_tokens=0, cost_usd=0.0)
    t0, ncalls, status, cell = time.time(), 0, "budget_exhausted", 0
    tool_s, model_s = 0.0, 0.0             # command-execution time (budgeted) and model latency (reported only)
    extra = {}
    if a.reasoning_effort:
        extra["reasoning_effort"] = a.reasoning_effort
    try:
        while ncalls < a.max_calls and tool_s < a.max_minutes * 60 and time.time() - t0 < a.max_wall_minutes * 60:
            if over_budget(a):
                status = "usd_budget_stop"
                break
            if a.api == "chat":
                try:
                    tq = time.time()
                    r = client.chat.completions.create(model=a.model, messages=msgs, tools=tools(a.vision), tool_choice="auto", temperature=a.temperature,
                                                       top_p=a.top_p, max_tokens=a.max_tokens, extra_body=dict(extra, **json.loads(a.extra_body)), timeout=1800)
                except Exception as e:                      # context overflow or server error: compact once, then give up
                    if "context" in str(e).lower() and compact(msgs, keep=4):
                        trans.write(json.dumps(dict(event="compacted", error=str(e)[:500])) + "\n")
                        continue
                    raise
                model_s += time.time() - tq
                usage["calls"] += 1
                usage["prompt_tokens"] += r.usage.prompt_tokens
                usage["completion_tokens"] += r.usage.completion_tokens
                cached = getattr(getattr(r.usage, "prompt_tokens_details", None), "cached_tokens", None) or 0
                m = r.choices[0].message
                reasoning = getattr(m, "reasoning_content", None) or getattr(m, "reasoning", None)
                am = dict(role="assistant", content=m.content or "")
                if m.tool_calls:
                    am["tool_calls"] = [dict(id=c.id, type="function", function=dict(name=c.function.name, arguments=c.function.arguments)) for c in m.tool_calls]
                if a.pass_reasoning and reasoning and m.tool_calls:   # models that expect their earlier reasoning back (Qwen3.8 preserve_thinking, gpt-oss tool turns); cut-off turns without a tool call are not fed back
                    am["reasoning_content"] = am["reasoning"] = reasoning
                msgs.append(am)
                text, finish, prompt_toks = m.content, r.choices[0].finish_reason, r.usage.prompt_tokens
                calls = [(c.id, c.function.name, c.function.arguments) for c in (m.tool_calls or [])]
                udump = r.usage.model_dump()
                cost = call_cost(a, r.usage.prompt_tokens, cached, r.usage.completion_tokens)
            else:                                           # OpenAI Responses API: reasoning items (encrypted) go back every turn
                try:
                    tq = time.time()
                    kw = dict(reasoning=dict(effort=a.reasoning_effort, summary="auto")) if a.reasoning_effort else {}
                    r = client.responses.create(model=a.model, instructions=sysmsg, input=items, tools=rtools(a.vision), store=False,
                                                include=["reasoning.encrypted_content"], max_output_tokens=a.max_tokens, timeout=1800, **kw)
                except Exception as e:
                    if "context" in str(e).lower() and compact_items(items, keep=4):
                        trans.write(json.dumps(dict(event="compacted", error=str(e)[:500])) + "\n")
                        continue
                    raise
                model_s += time.time() - tq
                u = r.usage
                cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", None) or 0
                rtok = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None) or 0
                usage["calls"] += 1
                usage["prompt_tokens"] += u.input_tokens
                usage["completion_tokens"] += u.output_tokens
                usage["reasoning_tokens"] += rtok
                out_items = [o.model_dump(mode="json", exclude_none=True) for o in r.output]
                items.extend(out_items)
                reasoning = "\n".join(sm.get("text", "") for o in out_items if o.get("type") == "reasoning" for sm in o.get("summary", []))
                text, finish, prompt_toks = r.output_text, getattr(r, "status", None), u.input_tokens
                calls = [(o["call_id"], o["name"], o.get("arguments", "")) for o in out_items if o.get("type") == "function_call"]
                udump = u.model_dump()
                cost = call_cost(a, u.input_tokens, cached, u.output_tokens)
            usage["cached_tokens"] += cached
            usage["cost_usd"] += cost
            with LOCK:
                SPEND["usd"] += cost
            trans.write(json.dumps(dict(event="assistant", content=text, reasoning=reasoning,
                                        tool_calls=[dict(id=i, function=dict(name=n, arguments=g)) for i, n, g in calls] or None,
                                        finish_reason=finish, usage=udump, cost_usd=round(cost, 5), t=round(time.time() - t0, 1))) + "\n")
            if prompt_toks > a.compact_at:
                compact(msgs, keep=6) if a.api == "chat" else compact_items(items, keep=6)
            if not calls:
                nudge = "Continue with a tool call. When the task is complete, call submit."
                (msgs if a.api == "chat" else items).append(dict(role="user", content=nudge))
                continue
            done = False
            images = []
            for cid, cname, cargs in calls:
                ncalls += 1
                try:
                    args = json.loads(cargs or "{}")
                except json.JSONDecodeError as e:
                    out = f"ERROR: tool arguments are not valid JSON ({e})"
                    args = None
                if args is not None:
                    try:
                        name = norm_tool(cname)
                        if name == "bash":
                            cell += 1
                            log = work / ".cells" / f"cmd_{cell:03d}.log"
                            log.parent.mkdir(exist_ok=True)
                            cmd = args.get("command", args.get("cmd"))           # some models name the argument "cmd"
                            if cmd is None:
                                raise ValueError("bash needs a 'command' argument")
                            left = max(10, int(a.max_minutes * 60 - tool_s))
                            res = sandboxed(["/bin/bash", "-c", norm_command(cmd)], work, [inputs, AGENT_TOOLS], [work], env,
                                            min(int(args.get("timeout_s") or 300), 900, left), 900, a.ram_mb, log)
                            tool_s += res["elapsed_seconds"]
                            out = f"exit_code={res['exit_code']} elapsed={res['elapsed_seconds']}s" + (f" KILLED: {res['termination_reason']}" if res["termination_reason"] else "") + "\n" + clip(log.read_text(errors="replace"))
                        elif name == "write_file":
                            p = safe_rel(work, args["path"])
                            p.parent.mkdir(parents=True, exist_ok=True)
                            p.write_text(args["content"])
                            out = f"wrote {p.relative_to(work)} ({len(args['content'])} characters)"
                        elif name == "read_file":
                            rel = args["path"]
                            p = safe_rel(inputs, rel[len("inputs/"):]) if rel.startswith("inputs/") else safe_rel(work, rel)
                            lines = p.read_text(errors="replace").splitlines()
                            s0, n = max(1, int(args.get("start_line") or 1)), min(int(args.get("max_lines") or 400), 1000)
                            out = "\n".join(f"{k}: {l}" for k, l in enumerate(lines[s0 - 1:s0 - 1 + n], start=s0)) + f"\n[{len(lines)} lines total]"
                            out = clip(out)
                        elif name == "view_image" and a.vision:
                            rel = args["path"]
                            p = safe_rel(inputs, rel[len("inputs/"):] if rel.startswith("inputs/") else rel)
                            pngs = pdf_pages(p) if p.suffix.lower() == ".pdf" else [p.read_bytes()]
                            mime = "image/png" if p.suffix.lower() in (".pdf", ".png") else "image/jpeg"
                            images += [f"data:{mime};base64,{base64.b64encode(b).decode()}" for b in pngs]
                            out = f"showing {len(pngs)} image(s) of {rel} in the next message"
                        elif name == "apply_patch":                       # not advertised; gpt-oss calls it by habit
                            patch = args.get("patch", args.get("input", args.get("content", next((v for v in args.values() if isinstance(v, str)), ""))))
                            cell += 1
                            log = work / ".cells" / f"cmd_{cell:03d}.log"
                            log.parent.mkdir(exist_ok=True)
                            pf = work / "tmp" / f"patch_{cell:03d}.txt"
                            pf.write_text(patch)
                            res = sandboxed(["/bin/bash", "-c", f"apply_patch < {pf}"], work, [inputs, AGENT_TOOLS], [work], env, 60, 60, a.ram_mb, log)
                            tool_s += res["elapsed_seconds"]
                            out = f"exit_code={res['exit_code']}\n" + clip(log.read_text(errors="replace"))
                        elif name == "submit":
                            out, done, status = "submitted", True, "submitted"
                        else:
                            out = f"ERROR: unknown tool {name}"
                    except Exception as e:
                        out = f"ERROR: {type(e).__name__}: {e}"
                if a.api == "chat":
                    msgs.append(dict(role="tool", tool_call_id=cid, content=out))
                else:
                    items.append(dict(type="function_call_output", call_id=cid, output=out))
                trans.write(json.dumps(dict(event="tool", name=cname, arguments=(cargs or "")[:20000], output=out[:20000], t=round(time.time() - t0, 1))) + "\n")
            if images:
                if a.api == "chat":
                    msgs.append(dict(role="user", content=[dict(type="text", text="Requested image(s):")] + [dict(type="image_url", image_url=dict(url=u)) for u in images]))
                else:
                    items.append(dict(role="user", content=[dict(type="input_text", text="Requested image(s):")] + [dict(type="input_image", image_url=u) for u in images]))
            if done:
                break
    except Exception as e:
        if "insufficient_quota" in str(e) or "credit_balance_exhausted" in str(e):
            SPEND["no_credit"] = True        # stop the whole run; tasks without result.json run again once credit is added
            trans.close()
            with LOCK:
                print(f"{tid:34s} NOT RUN: provider reports no credit (spent so far {SPEND['usd']:.2f} USD)", flush=True)
            if usage["calls"] == 0:
                rmtree_force(root)
            return dict(task_id=tid, status="not_run_no_credit", usage=usage, generation_seconds=0, execution_verified=False)
        status = "harness_or_model_error"
        trans.write(json.dumps(dict(event="error", error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-3000:])) + "\n")
    gen_s = time.time() - t0
    trans.close()
    rec = dict(task_id=tid, run_id=a.run_id, model=a.model, status=status, tool_calls=ncalls, generation_seconds=round(gen_s, 1), usage=usage,
               command_seconds=round(tool_s, 1), model_latency_seconds=round(model_s, 1), api=a.api, cost_usd=round(usage["cost_usd"], 4),
               reasoning_effort=a.reasoning_effort, vision=a.vision, inputs_unchanged=inventory(inputs) == in_inv)
    rec["replay"] = replay(tid, root, work, inputs, a)
    rec["execution_verified"] = rec["replay"].get("execution_verified", False)
    final.write_text(json.dumps(rec, indent=1) + "\n")
    with LOCK:
        print(f"{tid:34s} {status:22s} calls={ncalls:3d} gen={gen_s / 60:5.1f}min tokens={usage['prompt_tokens'] // 1000}k/{usage['completion_tokens'] // 1000}k "
              f"replay={rec['replay'].get('exit_code')} {rec['replay'].get('termination_reason') or ''} artifacts={len(rec['replay'].get('outputs', {}))}", flush=True)
    return rec


def compact(msgs: list, keep: int) -> bool:
    """Shorten old tool outputs (all but the last `keep` tool messages) to save context. Returns True if anything changed."""
    idx = [i for i, m in enumerate(msgs) if m["role"] == "tool"]
    changed = False
    for i in idx[:-keep] if keep else idx:
        c = msgs[i]["content"]
        if len(c) > 400:
            msgs[i]["content"] = c[:200] + "\n...[older output removed to save context]...\n" + c[-150:]
            changed = True
    for m in msgs:
        if m["role"] == "user" and isinstance(m["content"], list):     # drop old images
            m["content"] = "[image removed to save context]"
            changed = True
    asst = [m for m in msgs if m["role"] == "assistant"]
    for m in asst[:-keep] if keep else asst:                          # drop old reasoning traces
        if m.pop("reasoning_content", None) is not None:
            m.pop("reasoning", None)
            changed = True
    return changed


def compact_items(items: list, keep: int) -> bool:
    """Responses API counterpart of compact(): shorten old tool outputs and drop old images."""
    idx = [i for i, it in enumerate(items) if it.get("type") == "function_call_output"]
    changed = False
    for i in idx[:-keep] if keep else idx:
        c = items[i]["output"]
        if isinstance(c, str) and len(c) > 400:
            items[i]["output"] = c[:200] + "\n...[older output removed to save context]...\n" + c[-150:]
            changed = True
    for it in items:
        if it.get("role") == "user" and isinstance(it.get("content"), list) and any(x.get("type") == "input_image" for x in it["content"]):
            it["content"] = "[image removed to save context]"
            changed = True
    return changed


def replay(tid: str, root: Path, work: Path, inputs: Path, a) -> dict:
    rp = root / "replay"
    if rp.exists():
        shutil.rmtree(rp)
    sub, out = rp / "submission", rp / "output"
    sub.mkdir(parents=True)
    out.mkdir()
    for f in work.rglob("*.py"):
        if ".cells" in f.parts or "tmp" in f.relative_to(work).parts or "cache" in f.relative_to(work).parts:
            continue
        dst = sub / f.relative_to(work)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    if not (sub / "main.py").is_file():
        return dict(status="no_main_py", execution_verified=False, outputs={})
    code_inv, in_inv = inventory(sub), inventory(inputs)
    env = runtime_env(rp, inputs, out)
    res = sandboxed([f"{RUNTIME}/bin/python", "-E", "-s", "-B", str(sub / "main.py")], out, [inputs, sub], [out, rp / "tmp", rp / "cache"], env,
                    a.replay_wall, a.replay_wall, a.ram_mb, rp / "replay.log")
    outs = inventory(out)
    frozen = inventory(inputs) == in_inv and inventory(sub) == code_inv
    res.update(outputs=outs, frozen_inputs_and_code_unchanged=frozen, submission=code_inv,
               execution_verified=res["exit_code"] == 0 and not res["termination_reason"] and frozen,
               sandbox="linux-landlock (fs: system+runtime+inputs read-only, job read-write; all TCP denied)" if SANDBOX == "landlock"
               else "macos-seatbelt (no network; no reads below /Users except runtime+inputs+job; writes only in the job)")
    dst = Path(a.out) / "submissions" / a.run_id / tid
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for rel in outs:
        q = dst / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out / rel, q)
    if (sub / "main.py").is_file() and not (dst / "main.py").exists():
        shutil.copy2(sub / "main.py", dst / "main.py")       # the contract's main.py artifact is the submitted entry point
    (rp / "execution.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-dir", required=True, help="candidate/ (primary) or a suite folder with tasks.jsonl + inputs/")
    ap.add_argument("--suite-kind", choices=["candidate", "suite"], default="candidate")
    ap.add_argument("--readme", default=None, help="artifact contract text (default: <suite-dir>/README.md)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:8100/v1")
    ap.add_argument("--out", default=str(HERE / "runs"))
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--vision", action="store_true")
    ap.add_argument("--reasoning-effort", default=None)
    ap.add_argument("--pass-reasoning", action="store_true", help="send each assistant turn's reasoning back in later requests")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--extra-body", default="{}", help="JSON merged into the request body (e.g. top_k)")
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--max-calls", type=int, default=250)
    ap.add_argument("--max-minutes", type=float, default=45, help="budget of command-execution minutes per task")
    ap.add_argument("--max-wall-minutes", type=float, default=180, help="wall-clock safety cap per task")
    ap.add_argument("--compact-at", type=int, default=90000)
    ap.add_argument("--replay-wall", type=int, default=600)
    ap.add_argument("--ram-mb", type=int, default=8192)
    ap.add_argument("--api", choices=["chat", "responses"], default="chat")
    ap.add_argument("--api-key-env", default=None, help="environment variable holding the API key (hosted APIs); never logged")
    ap.add_argument("--sandbox", choices=["landlock", "macos"], default="macos" if sys.platform == "darwin" else "landlock")
    ap.add_argument("--runtime", default=None, help="pinned CAD/FEM runtime prefix (default ~/miniconda3/envs/cadfem-runtime)")
    ap.add_argument("--price-in", type=float, default=0.0, help="USD per million uncached input tokens")
    ap.add_argument("--price-cached", type=float, default=0.0, help="USD per million cached input tokens")
    ap.add_argument("--price-out", type=float, default=0.0, help="USD per million output tokens (incl. reasoning)")
    ap.add_argument("--budget-usd", type=float, default=0.0, help="stop starting/continuing tasks once this much is spent (0 = no cap)")
    ap.add_argument("--task-reserve-usd", type=float, default=0.0, help="do not start a task unless this much budget is left")
    a = ap.parse_args()
    global SANDBOX, RUNTIME, RUNTIME_BASE
    a.out, a.suite_dir = str(Path(a.out).resolve()), str(Path(a.suite_dir).resolve())     # tools run with cwd = workspace: every path must be absolute
    if a.readme:
        a.readme = str(Path(a.readme).resolve())
    SANDBOX = a.sandbox
    if a.runtime:
        RUNTIME = Path(a.runtime)
    assert RUNTIME.is_dir() and (RUNTIME / "bin/python").exists(), RUNTIME
    if SANDBOX == "landlock":
        assert LL.is_file()
    else:
        assert Path("/usr/bin/sandbox-exec").exists()
        RUNTIME_BASE = subprocess.run([str(RUNTIME / "bin/python"), "-I", "-c", "import sys; print(sys.base_prefix)"], capture_output=True, text=True, check=True).stdout.strip()
    if a.budget_usd:
        assert a.price_in > 0 and a.price_out > 0, "a USD budget needs --price-in/--price-out"
    tasks = [json.loads(x) for x in (Path(a.suite_dir) / "tasks.jsonl").read_text().splitlines() if x.strip()]
    if a.tasks:                               # run in the order given (lets a USD-capped run cover every family first)
        by_id = {t["task_id"]: t for t in tasks}
        tasks = [by_id[x] for x in a.tasks if x in by_id]
    contract = Path(a.readme or Path(a.suite_dir) / "README.md").read_text()
    client = OpenAI(base_url=a.base_url or None, api_key=os.environ[a.api_key_env] if a.api_key_env else "local", max_retries=4)
    meta = Path(a.out) / a.run_id / "run.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(dict(vars(a), started=time.strftime("%Y-%m-%dT%H:%M:%S"), tasks=[t["task_id"] for t in tasks],
                                    harness_sha256=sha(Path(__file__)), landlock_run_sha256=sha(LL) if LL.is_file() else None, apply_patch_sha256=sha(AGENT_TOOLS / "apply_patch"),
                                    runtime=str(RUNTIME), runtime_base=RUNTIME_BASE, platform=sys.platform,
                                    system_prompt_sha256=hashlib.sha256(system_prompt(contract, a, a.vision).encode()).hexdigest()), indent=1) + "\n")
    with ThreadPoolExecutor(a.parallel) as ex:
        recs = list(ex.map(lambda t: run_task(t, a, contract, client), tasks))
    summ = dict(run_id=a.run_id, model=a.model, tasks=len(recs), submitted=sum(r["status"] == "submitted" for r in recs),
                execution_verified=sum(bool(r["execution_verified"]) for r in recs),
                prompt_tokens=sum(r["usage"]["prompt_tokens"] for r in recs), completion_tokens=sum(r["usage"]["completion_tokens"] for r in recs),
                generation_hours=round(sum(r["generation_seconds"] for r in recs) / 3600, 2), finished=time.strftime("%Y-%m-%dT%H:%M:%S"),
                cost_usd=round(SPEND["usd"], 2), not_run_usd_budget=sum(r["status"] == "not_run_usd_budget" for r in recs),
                not_run_no_credit=sum(r["status"] == "not_run_no_credit" for r in recs))
    (Path(a.out) / a.run_id / "summary.json").write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
