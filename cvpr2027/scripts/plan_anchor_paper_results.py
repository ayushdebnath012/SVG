"""Generate paper/network/plan-anchor-results.tex: frontier comparison, plan-anchored students, distillation.

Every number comes from saved scorer outputs (score_multisource_cad_geometry.py on test,
score_validation_geometry.py on validation) and the teacher/verifier records. Paired tests are exact
two-sided McNemar tests on strict (IoU >= 0.99999) agreement over identical task ids.
"""
from __future__ import annotations

import glob
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper/network/plan-anchor-results.tex"
SCORED = ROOT / "runs/multisource-cad-astra-20261004/scored"
RUNS = {  # label -> (test decoded, test anchored, validation anchored or None, hardware)
    "template1": ("runs/cad-distill-colab-20261005/local-scored/template-predictions-geometry.jsonl",
                  "runs/cad-distill-colab-20261005/local-scored/template-anchored-v2-predictions-geometry.jsonl",
                  None, "L4"),
    "template2": ("runs/cad-distill-pilot10-colab-20261005/results-distill/local/test-predictions-geometry.jsonl",
                  "runs/cad-distill-pilot10-colab-20261005/results-distill/local/test-anchored-predictions-geometry.jsonl",
                  "runs/cad-distill-pilot10-colab-20261005/results-distill/local/validation-predictions-anchored-geometry.jsonl",
                  "A100"),
    "distill": ("runs/cad-distill-v3-kaggle-v2-20261006/results-distill/local/test-predictions-geometry.jsonl",
                "runs/cad-distill-v3-kaggle-v2-20261006/results-distill/local/test-anchored-predictions-geometry.jsonl",
                "runs/cad-distill-v3-kaggle-v2-20261006/results-distill/local/validation-predictions-anchored-geometry.jsonl",
                "T4"),
    "distillref": ("runs/cad-distill-v2-colab-20261005/results-distill-ref/local/test-predictions-geometry.jsonl",
                   "runs/cad-distill-v2-colab-20261005/results-distill-ref/local/test-anchored-predictions-geometry.jsonl",
                   "runs/cad-distill-v2-colab-20261005/results-distill-ref/local/validation-predictions-anchored-geometry.jsonl",
                   "A100"),
}
VALIDATION_DECODED = "runs/cad-distill-pilot10-colab-20261005/results-distill/local/validation-predictions-geometry.jsonl"


def load(path: str | Path) -> dict:
    return {json.loads(l)["id"]: json.loads(l) for l in (ROOT / path).read_text().splitlines()}


def strict(rows: dict, source: str | None = None) -> int:
    return sum(r["match_strict"] for r in rows.values() if source is None or r["source"] == source)


def paired(a: dict, b: dict) -> tuple[int, int, float]:
    gain = sum(a[i]["match_strict"] and not b[i]["match_strict"] for i in a)
    loss = sum(b[i]["match_strict"] and not a[i]["match_strict"] for i in a)
    n, k = gain + loss, min(gain, loss)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return gain, loss, p


def ptex(p: float) -> str:
    if p >= 0.01:
        return f"{p:.2f}"
    mantissa, exponent = f"{p:.0e}".split("e")
    return f"{int(mantissa)}\\times10^{{{int(exponent)}}}"


def main() -> None:
    sft, astra, base = (load(SCORED / f"{x}-predictions-geometry.jsonl") for x in ("trained", "astra", "base"))
    runs = {k: (load(t), load(a), load(v) if v else None, hw) for k, (t, a, v, hw) in RUNS.items()}
    val_decoded = load(VALIDATION_DECODED)
    m = {}
    m["paBase"], m["paSft"], m["paAstra"] = strict(base), strict(sft), strict(astra)
    m["paAstraBench"], m["paAstraEditor"] = strict(astra, "BenchCAD"), strict(astra, "CAD-Editor")
    m["paSftBench"], m["paSftEditor"] = strict(sft, "BenchCAD"), strict(sft, "CAD-Editor")
    m["paBaseBench"], m["paBaseEditor"] = strict(base, "BenchCAD"), strict(base, "CAD-Editor")
    g, l, p = paired(astra, sft)
    m.update(paAstraOnly=g, paSftOnlyVsAstra=l, paAstraVsSftP=ptex(p))
    g, l, p = paired({i: r for i, r in astra.items() if r["source"] == "CAD-Editor"},
                     {i: r for i, r in sft.items() if r["source"] == "CAD-Editor"})
    m.update(paAstraEditorOnly=g, paSftEditorOnly=l, paAstraVsSftEditorP=ptex(p))
    astra_pred = [json.loads(l) for l in (SCORED / "astra-predictions.jsonl").read_text().splitlines()]
    m["paAstraEditorInvalid"] = sum(r["source"] == "CAD-Editor" and not r["applicable"] for r in astra_pred)
    m["paAstraEditorWrong"] = sum(astra[r["id"]]["executable"] is True and not astra[r["id"]]["match_strict"]
                                  for r in astra_pred if r["source"] == "CAD-Editor")
    astra_runs = [json.loads(Path(f).read_text()) for f in glob.glob(str(ROOT / "runs/multisource-cad-astra-20261004/*/result.json"))]
    m["paAstraCost"] = f"{sum((r['usage']['prompt_tokens'] * 10 + r['usage']['completion_tokens'] * 50) / 1e6 for r in astra_runs):.2f}"
    rows = []
    names = {"template1": "Plan, template (run 1)", "template2": "Plan, template (run 2)$^\\dagger$",
             "distill": "Plan, teacher (verifier)", "distillref": "Plan, teacher (ref.-filtered)"}
    for key, (dec, anc, val, hw) in runs.items():
        tag = {"template1": "TemplateA", "template2": "TemplateB", "distill": "Distill", "distillref": "DistillRef"}[key]
        m[f"pa{tag}Decoded"], m[f"pa{tag}Anchored"] = strict(dec), strict(anc)
        m[f"pa{tag}Bench"], m[f"pa{tag}Editor"] = strict(anc, "BenchCAD"), strict(anc, "CAD-Editor")
        g, l, p = paired(anc, dec)
        m.update({f"pa{tag}AnchorGain": g, f"pa{tag}AnchorLoss": l})
        g, l, p = paired(anc, sft)
        m.update({f"pa{tag}VsSftGain": g, f"pa{tag}VsSftLoss": l, f"pa{tag}VsSftP": ptex(p)})
        m[f"pa{tag}Val"] = strict(val) if val else "--"
        rows.append(f"{names[key]} & {hw} & {strict(dec)} & {strict(anc)} & {strict(anc, 'BenchCAD')} & "
                    f"{strict(anc, 'CAD-Editor')} & {strict(val) if val else '--'} \\\\")
    g, l, p = paired(runs["template2"][2], val_decoded)
    m.update(paValDecoded=strict(val_decoded), paValAnchored=strict(runs["template2"][2]), paValGain=g, paValLoss=l,
             paValP=ptex(p))
    g, l, p = paired(runs["template1"][1], runs["template2"][1])
    m.update(paRunChurnGain=g, paRunChurnLoss=l)
    g, l, p = paired(runs["distill"][1], runs["template1"][1])
    m.update(paDistillVsTemplateGain=g, paDistillVsTemplateLoss=l, paDistillVsTemplateP=ptex(p))
    g, l, p = paired(runs["distill"][1], runs["distillref"][1])
    m.update(paDistillVsRefGain=g, paDistillVsRefLoss=l, paDistillVsRefP=ptex(p))
    g, l, p = paired(astra, runs["distill"][1])
    m.update(paAstraVsDistillGain=g, paAstraVsDistillLoss=l, paAstraVsDistillP=ptex(p))
    # first-run diagnosis: BenchCAD invalid-coordinate failures before anchoring
    first = [json.loads(l) for l in (ROOT / "runs/cad-distill-colab-20261005/local-scored/template-predictions.jsonl").read_text().splitlines()]
    m["paIndexFailures"] = sum(r["source"] == "BenchCAD" and "Invalid original coordinates" in (r["error"] or "") for r in first)
    # teacher and verifier
    verdicts = [json.loads(Path(f).read_text()) for d in ("cad-astra-distill-20261004", "cad-astra-distill-n2-20261005")
                for f in glob.glob(str(ROOT / "runs" / d / "*/verify.json"))]
    ok = [v for v in verdicts if "selected" in v]
    accepted = [v for v in ok if v["selected_consensus"] >= 2]
    m.update(paTeacherTasks=len(verdicts), paTeacherVerified=len(ok), paTeacherAccepted=len(accepted),
             paTeacherAcceptedRef=sum(v["audit_selected_strict"] for v in accepted),
             paTeacherPrecision=f"{100 * sum(v['audit_selected_strict'] for v in accepted) / len(accepted):.0f}",
             paTeacherUnverifiable=len(verdicts) - len(ok))
    teacher_cost = sum((r["usage"]["prompt_tokens"] * 10 + r["usage"]["completion_tokens"] * 50) / 1e6
                       for d in ("cad-astra-distill-20261004", "cad-astra-distill-n2-20261005")
                       for r in (json.loads(Path(f).read_text()) for f in glob.glob(str(ROOT / "runs" / d / "*/result.json")))
                       if r.get("usage"))
    m["paTeacherCost"] = f"{teacher_cost:.2f}"
    lines = ["% Generated by scripts/plan_anchor_paper_results.py from saved scorer outputs. Do not edit manually."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    lines.append("\\newcommand{\\planAnchorRows}{" + "\n".join(rows) + "}")
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT, len(m), "macros")
    for k, v in m.items():
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
