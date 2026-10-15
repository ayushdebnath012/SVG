"""Print the last steps of each task transcript in a run: python peek.py RUN_ID [N]"""
import json, sys
from pathlib import Path
run, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 12
for t in sorted((Path(__file__).parent / "runs" / run).glob("*/transcript.jsonl")):
    rows = []
    for l in t.read_text().splitlines():
        e = json.loads(l)
        if e["event"] == "assistant":
            tc = (e.get("tool_calls") or [{}])[0].get("function", {})
            rows.append(f"  A t={e['t']}s {tc.get('name')} {str(tc.get('arguments', ''))[:120]!r} tok={e['usage']['completion_tokens']}")
        elif e["event"] == "tool":
            rows.append("  T: " + e["output"][:160].replace("\n", " | "))
        elif e["event"] in ("error", "compacted"):
            rows.append(f"  {e['event'].upper()}: " + e.get("error", "")[:300])
    res = t.parent / "result.json"
    print(f"== {t.parent.name}  steps={len(rows)}" + (f"  RESULT {json.loads(res.read_text())['status']}" if res.exists() else ""))
    print("\n".join(rows[-n:]))
