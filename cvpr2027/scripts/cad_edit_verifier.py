"""Target-free CAD edit verifier: rank teacher candidates without looking at the reference edit.

Signals, all computed from the source program, the instruction and the candidates only:
  gates      the patch parses and applies, the program executes in the restricted CadQuery executor and
             yields one or more valid solids with positive volume
  numbers    values the instruction asks for ("from 12.49 to 16.24", "a 21 diameter hole", new values
             that are not in the source) appear in the inserted lines, directly or as a constant
             expression (9.4 / 3), or as half/double for radius/diameter wording; a "from A" value must
             lose at least one occurrence
  consensus  candidates are clustered by executed-solid IoU >= 0.99999; a geometry that several
             independent teacher samples agree on is preferred
  changed    the edited solid differs from the source solid (soft: some correct edits are symmetric)
  minimal    fewer edited lines break ties

The optional reference program is executed only to fill audit_* fields that measure the verifier; it is
never read by the score or the selection.

  python cad_edit_verifier.py TASK.json   (run under the CadQuery runtime; prints one JSON object)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cad_edit_contracts import apply  # noqa: E402

STRICT = 0.99999
NUMBER = r"-?\d+(?:\.\d+)?"


def extract(text: str) -> tuple[str, dict]:
    """Split a PLAN/PATCH answer (or a bare JSON patch) into (plan, patch)."""
    plan, body = "", text.strip()
    if "PATCH:" in body:
        plan, body = body.split("PATCH:", 1)
        plan = plan.replace("PLAN:", "", 1).strip()
    body = body.strip()
    if body.startswith("```"):
        body = "\n".join(body.splitlines()[1:-1])
    try:
        return plan, json.loads(body)
    except ValueError:
        start = body.find("{")
        if start < 0:
            raise ValueError("No JSON patch object") from None
        value, _ = json.JSONDecoder().raw_decode(body[start:])
        return plan, value


def _constant_values(line: str) -> list[float]:
    """Numeric literals and constant arithmetic sub-expressions in one line of code."""
    values = [float(x) for x in re.findall(NUMBER, line)]
    try:
        tree = ast.parse(line.strip().lstrip("."), mode="exec")
    except SyntaxError:
        return values
    for node in ast.walk(tree):
        if isinstance(node, (ast.BinOp, ast.UnaryOp)):
            try:
                value = eval(compile(ast.Expression(node), "<const>", "eval"), {"__builtins__": {}}, {})
            except Exception:  # noqa: BLE001 - non-constant expression
                continue
            if isinstance(value, (int, float)):
                values.append(float(value))
    return values


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, 1e-4 * abs(b))


def numeric_checks(instruction: str, source: str, patch: dict) -> list[dict]:
    inserted = [v for op in patch["edits"] for line in op["insert"] for v in _constant_values(line)]
    lines = source.splitlines()
    removed = [v for op in patch["edits"] for line in lines[op["start"]:op["start"] + op["delete"]]
               for v in _constant_values(line)]
    deltas = {float(x): bool(pct) for x, pct in re.findall(rf"\bby\s+({NUMBER})\s*(%|percent)?", instruction, re.I)}
    source_values = [float(x) for x in re.findall(NUMBER, source)]
    pairs = re.findall(rf"from\s+({NUMBER})\s*(?:mm|deg|degrees|°)?\s+to\s+({NUMBER})", instruction, re.I)
    olds = {float(a) for a, _ in pairs}
    wanted = {float(b) for _, b in pairs}
    for x in re.findall(NUMBER, instruction):
        value = float(x)
        if value not in olds and not any(_close(s, value) for s in source_values) and value not in (0.0, 1.0):
            wanted.add(value)
    radial = re.search(r"diamet|radius|radii|Ø|bore|hole", instruction, re.I) is not None
    checks = []
    for value in sorted(wanted):
        forms = [value] + ([value / 2, value * 2] if radial else [])
        ok = any(_close(v, f) for v in inserted for f in forms)
        if not ok and value in deltas:  # "by X" / "by X %": a changed literal moves by X
            percent = deltas[value]
            ok = any(_close(abs(v / u - 1) * 100, value) if percent and u else _close(abs(v - u), value)
                     for v in inserted for u in removed)
        checks.append(dict(kind="delta" if value in deltas else "value_present", value=value, ok=ok))
    for value in sorted(olds):
        before = sum(_close(s, value) for s in source_values)
        after_text = apply(source, patch, "cadquery")
        after = sum(_close(float(s), value) for s in re.findall(NUMBER, after_text))
        checks.append(dict(kind="old_value_changed", value=value, ok=after < before))
    return checks


def _iou(a, b) -> float:
    inter = a.intersect(b).Volume()
    union = a.Volume() + b.Volume() - inter
    return max(0.0, min(1.0, inter / union)) if union > 0 else 0.0


def verify(task: dict) -> dict:
    """task: {source, instruction, representation, candidates: [text], reference_code?}"""
    from verify_mechanical_cad_edits import execute
    from cad_editor_geometry import execute_sequence

    rep = task["representation"]
    executor, built = execute if rep == "cadquery" else execute_sequence, {}

    def run(code):  # identical candidate programs are executed once
        if code not in built:
            built[code] = executor(code)
        return built[code]
    source_solid = run(task["source"])
    rows, solids = [], {}
    for i, text in enumerate(task["candidates"]):
        row = dict(index=i, gates=False, error=None, plan="", edited_lines=None, numbers=[], changed=None)
        try:
            row["plan"], patch = extract(text)
            code = apply(task["source"], patch, rep)
            row["edited_lines"] = sum(op["delete"] + len(op["insert"]) for op in patch["edits"])
            row["code"] = code
            row["patch"] = patch
            if rep == "cadquery":
                row["numbers"] = numeric_checks(task["instruction"], task["source"], patch)
            solids[i] = run(code)
            row["gates"] = True
            row["volume"] = solids[i].Volume()
            row["changed"] = _iou(source_solid, solids[i]) < STRICT
        except Exception as error:  # noqa: BLE001 - recorded per candidate
            row["error"] = type(error).__name__ + ": " + str(error)[:200]
        rows.append(row)
    # consensus clusters over executed candidates; identical programs share a solid
    passed = [r["index"] for r in rows if r["gates"]]
    parent = {i: i for i in passed}

    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for x, i in enumerate(passed):
        for j in passed[x + 1:]:
            if find(i) == find(j):
                continue
            same_code = rows[i]["code"] == rows[j]["code"]
            if same_code or _iou(solids[i], solids[j]) >= STRICT:
                parent[find(j)] = find(i)
    clusters = {}
    for i in passed:
        clusters.setdefault(find(i), []).append(i)
    n = len(task["candidates"])
    for r in rows:
        if not r["gates"]:
            r["score"] = None
            continue
        r["consensus"] = len(clusters[find(r["index"])])
        numbers_ok = [c["ok"] for c in r["numbers"]]
        r["numbers_fraction"] = sum(numbers_ok) / len(numbers_ok) if numbers_ok else None
        r["score"] = (r["consensus"] / n + (r["numbers_fraction"] if numbers_ok else 0.5)
                      + 0.25 * bool(r["changed"]) - 0.001 * r["edited_lines"])
    ranked = sorted((r for r in rows if r["gates"]), key=lambda r: -r["score"])
    best = ranked[0] if ranked else None
    result = dict(n=n, executed=len(passed), clusters=sorted(map(len, clusters.values()), reverse=True),
                  selected=best["index"] if best else None,
                  selected_consensus=best["consensus"] if best else 0,
                  selected_numbers_fraction=best["numbers_fraction"] if best else None,
                  selected_changed=best["changed"] if best else None,
                  candidates=[{k: v for k, v in r.items() if k not in ("code",)} for r in rows])
    if task.get("reference_code") is not None:  # audit only; computed after selection
        reference = run(task["reference_code"])
        audits = {i: _iou(solids[i], reference) for i in passed}
        for r in result["candidates"]:
            r["audit_reference_iou"] = audits.get(r["index"])
        result["audit_selected_strict"] = bool(best) and audits[best["index"]] >= STRICT
        result["audit_any_strict"] = any(v >= STRICT for v in audits.values())
        result["audit_reference_changed"] = _iou(source_solid, reference) < STRICT
    return result


if __name__ == "__main__":
    print(json.dumps(verify(json.loads(Path(sys.argv[1]).read_text()))))
