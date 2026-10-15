"""Progress of the open-weight runs: python status.py RUN_ID [RUN_ID ...]"""
import json
import sys
from pathlib import Path

for run in sys.argv[1:]:
    root = Path(__file__).parent / "runs" / run
    tasks = sorted(root.glob("*/transcript.jsonl"))
    done = [t for t in tasks if (t.parent / "result.json").exists()]
    print(f"== {run}: {len(done)} done, {len(tasks) - len(done)} running")
    for t in tasks:
        res = t.parent / "result.json"
        if res.exists():
            r = json.loads(res.read_text())
            x = r["replay"]
            print(f"  {r['task_id']:28s} {r['status']:16s} calls={r['tool_calls']:3d} cmd={r.get('command_seconds', 0) / 60:4.1f}min "
                  f"model={r.get('model_latency_seconds', 0) / 60:5.1f}min wall={r['generation_seconds'] / 60:5.1f}min replay={x.get('exit_code')} files={len(x.get('outputs', {}))}")
        else:
            ev = [json.loads(l) for l in t.read_text().splitlines()]
            asst = [e for e in ev if e["event"] == "assistant"]
            calls = sum(1 for e in ev if e["event"] == "tool")
            last = asst[-1] if asst else None
            print(f"  {t.parent.name:28s} running          calls={calls:3d} wall={(last['t'] if last else 0) / 60:5.1f}min "
                  f"ctx={(last['usage']['prompt_tokens'] if last else 0) // 1000}k main.py={(t.parent / 'work' / 'main.py').exists()}")
