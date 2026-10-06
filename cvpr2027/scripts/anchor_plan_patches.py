"""Re-anchor PLAN+PATCH answers by the source line each plan bullet quotes, then write scorer-ready predictions.

The 3B student quotes the right original line in its plan but often miscounts the zero-based index. For each
patch operation paired (in order) with a plan bullet `- [i] `quoted line` -> ...`, the operation's start is
moved to the source line the quote identifies when that match is unique (exact, or a prefix of a quote of 20+
characters truncated with "..."). Inputs: the source program and the model's own answer only -- never the
reference edit. Operations without a unique match keep the model's index.

  python anchor_plan_patches.py PREDICTIONS.jsonl OUT.jsonl     (then run score_multisource_cad_geometry.py)
"""
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cad_edit_contracts import apply, target_match  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "runs/multisource-cad-colab-20261002/results-final/test-retained.jsonl"
BULLET = re.compile(r"^- \[(\d+|END)\] `(.*)` ->", re.M)


def anchor(code: str, text: str) -> tuple[dict, int]:
    plan, _, body = text.partition("PATCH:")
    patch, lines, moved = json.loads(body.strip()), code.splitlines(), 0
    for op, (index, quote) in zip(patch["edits"], BULLET.findall(plan)):
        if index == "END":
            continue
        quote = quote[:-3] if quote.endswith("...") else quote
        hits = [k for k, line in enumerate(lines) if line == quote or (len(quote) >= 20 and line.startswith(quote))]
        if len(hits) == 1 and hits[0] != op["start"]:
            op["start"], moved = hits[0], moved + 1
    patch["edits"].sort(key=lambda e: e["start"])
    return patch, moved


def main() -> None:
    source, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = {json.loads(l)["id"]: json.loads(l) for l in TEST.read_text().splitlines()}
    result, moved_answers = [], 0
    for line in source.read_text().splitlines():
        p = json.loads(line)
        r, q = rows[p["id"]], dict(p)
        try:
            patch, moved = anchor(r["code"], p["prediction"])
            if moved:
                moved_answers += 1
                code = apply(r["code"], patch, r["representation"])
                q.update(applicable=True, error=None, predicted_code=code, anchored=True,
                         target_match=target_match(code, r["edited_code"], r["representation"]),
                         exact_patch=patch == json.loads(r["target"]))
        except Exception:  # noqa: BLE001 - unparseable or still-invalid answers keep the original verdict
            pass
        result.append(q)
    out.write_text("".join(json.dumps(q) + "\n" for q in result))
    print(f"re-anchored {moved_answers} answers; applicable {sum(q['applicable'] for q in result)}; "
          f"program match {sum(q['target_match'] for q in result)}")


if __name__ == "__main__":
    main()
