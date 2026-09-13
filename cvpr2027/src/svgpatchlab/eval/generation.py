"""Text-to-SVG generation evaluation: run prompts, check structure, surface failures."""

from __future__ import annotations

import html
import json
import re
import time
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from svgpatchlab.core.xml import SVGParseError, local_name, parse_svg
from svgpatchlab.eval.render import RendererUnavailable, png_data_url, render_svg_array, render_svg_png
from svgpatchlab.models.base import ModelAdapter
from svgpatchlab.types import ModelRequest

_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.DOTALL | re.IGNORECASE)
_NUMBER_RE = re.compile(r"(?<![\w.])[-\u2212\u2013]?\d[\d,]*\.?\d*")
_FENCE_RE = re.compile(r"```(?:svg|xml|html)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

# Ordered from "model produced nothing usable" to "drawing exists but is wrong".
FAILURE_KINDS = (
    "truncated",
    "no_svg",
    "parse_error",
    "render_error",
    "blank_render",
    "checks_failed",
)


def load_prompt_template(name: str = "generation_v1") -> str:
    return resources.files("svgpatchlab.prompt_templates").joinpath(f"{name}.txt").read_text()


def extract_svg(text: str) -> str | None:
    """Pull the first <svg>...</svg> block out of a model reply, fences or not."""
    fenced = _FENCE_RE.search(text)
    candidate = fenced.group(1) if fenced else text
    match = _SVG_RE.search(candidate) or _SVG_RE.search(text)
    if match:
        return match.group(0).strip()
    return None


def _element_counts(root) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element in root.iter():
        name = local_name(element.tag)
        counts[name] = counts.get(name, 0) + 1
    return counts


def _all_text(root) -> str:
    return " ".join((el.text or "") for el in root.iter() if local_name(el.tag) in {"text", "tspan"}).lower()


def _numbers_in_text(text: str) -> list[float]:
    values = []
    for token in _NUMBER_RE.findall(text):
        token = token.replace(",", "").replace("\u2212", "-").replace("\u2013", "-").rstrip(".")
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def run_checks(root, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Evaluate declarative structural checks against a parsed SVG.

    Supported forms:
      {"tag": "circle", "min": 2}              at least N elements with this local name
      {"any_tag": ["path", "line"], "min": 5}  at least N elements across these names
      {"text_contains": "mm"}                  some <text>/<tspan> contains the substring
      {"root_attr": "viewBox"}                 root <svg> carries this attribute
      {"min_elements": 30}                     total element count floor
      {"number_near": 159.2, "tol": 0.02}      some label holds a number within tol (relative,
                                               floor 0.05 absolute) of the expected value; a list
                                               accepts any of several equivalent representations
    """
    counts = _element_counts(root)
    text = _all_text(root)
    results = []
    for check in checks:
        if "tag" in check:
            got = counts.get(check["tag"], 0)
            ok = got >= int(check.get("min", 1))
            label = f"{check['tag']} >= {check.get('min', 1)} (got {got})"
        elif "any_tag" in check:
            got = sum(counts.get(tag, 0) for tag in check["any_tag"])
            ok = got >= int(check.get("min", 1))
            label = f"any of {'/'.join(check['any_tag'])} >= {check.get('min', 1)} (got {got})"
        elif "text_contains" in check:
            ok = check["text_contains"].lower() in text
            label = f"text contains {check['text_contains']!r}"
        elif "root_attr" in check:
            ok = check["root_attr"] in root.attrib
            label = f"root has {check['root_attr']}"
        elif "min_elements" in check:
            got = sum(counts.values())
            ok = got >= int(check["min_elements"])
            label = f"elements >= {check['min_elements']} (got {got})"
        elif "number_near" in check:
            # A list means "any of these equivalent representations" (unit or scale variants).
            raw = check["number_near"]
            expected_values = [float(v) for v in (raw if isinstance(raw, list) else [raw])]
            rel = float(check.get("tol", 0.02))
            found = _numbers_in_text(text)
            close = [n for e in expected_values for n in found if abs(n - e) <= max(abs(e) * rel, 0.05)]
            ok = bool(close)
            primary = expected_values[0]
            nearest = min(found, key=lambda n: abs(n - primary)) if found else None
            shown = format(close[0], "g") if ok else (format(nearest, "g") if nearest is not None else "no numbers")
            label = f"label ~ {primary:g} ±{rel:.0%} ({'got ' if ok else 'nearest '}{shown})"
        else:
            raise ValueError(f"unknown check: {check}")
        results.append({"check": label, "ok": bool(ok)})
    return results


def ink_fraction(svg: str, size: int = 128) -> float:
    """Fraction of rendered pixels that are not the white background."""
    array = render_svg_array(svg, size=size, background="white")
    return float((array < 0.98).any(axis=-1).mean())


@dataclass
class GenerationCase:
    id: str
    prompt: str
    checks: list[dict[str, Any]] = field(default_factory=list)


def load_cases(path: str | Path) -> list[GenerationCase]:
    data = json.loads(Path(path).read_text())
    return [GenerationCase(id=c["id"], prompt=c["prompt"], checks=c.get("checks", [])) for c in data["cases"]]


def evaluate_case(
    model: ModelAdapter,
    case: GenerationCase,
    template: str,
    *,
    render: bool,
    sample: int = 0,
) -> dict[str, Any]:
    started = time.perf_counter()
    response = model.generate(ModelRequest(prompt=template.format(prompt=case.prompt)))
    latency = time.perf_counter() - started
    usage = response.metadata.get("usage") or {}
    record: dict[str, Any] = {
        "id": case.id,
        "sample": sample,
        "prompt": case.prompt,
        "model": response.metadata.get("model"),
        "finish_reason": response.metadata.get("finish_reason"),
        "usage": usage,
        "latency_seconds": round(latency, 3),
        "raw_chars": len(response.text),
        "svg": None,
        "checks": [],
        "ink_fraction": None,
        "failure": None,
        "error": None,
    }
    svg = extract_svg(response.text)
    if svg is None:
        record["failure"] = "truncated" if record["finish_reason"] == "length" else "no_svg"
        record["raw_head"] = response.text[:400]
        return record
    record["svg"] = svg
    if record["finish_reason"] == "length":
        record["failure"] = "truncated"
        return record
    try:
        root = parse_svg(svg)
    except SVGParseError as exc:
        record["failure"], record["error"] = "parse_error", str(exc)
        return record
    record["checks"] = run_checks(root, case.checks)
    if render:
        try:
            record["ink_fraction"] = round(ink_fraction(svg), 4)
        except RendererUnavailable:
            raise
        except Exception as exc:  # cairosvg raises a variety of types on bad input
            record["failure"], record["error"] = "render_error", f"{type(exc).__name__}: {exc}"[:300]
            return record
        if record["ink_fraction"] < 0.002:
            record["failure"] = "blank_render"
            return record
    if not all(c["ok"] for c in record["checks"]):
        record["failure"] = "checks_failed"
    return record


def summarize(records: list[dict[str, Any]], price_in_per_m: float, price_out_per_m: float) -> dict[str, Any]:
    prompt_tokens = sum(r["usage"].get("prompt_tokens") or 0 for r in records)
    completion_tokens = sum(r["usage"].get("completion_tokens") or 0 for r in records)
    reported_cost = sum(r["usage"].get("cost") or 0 for r in records)
    failures = {kind: sum(1 for r in records if r["failure"] == kind) for kind in FAILURE_KINDS}
    ok = sum(1 for r in records if r["failure"] is None)
    check_total = sum(len(r["checks"]) for r in records)
    check_ok = sum(1 for r in records for c in r["checks"] if c["ok"])
    return {
        "cases": len(records),
        "ok": ok,
        "ok_rate": round(ok / len(records), 4) if records else None,
        "failures": failures,
        "failed_ids": [f"{r['id']}#{r['sample']}" for r in records if r["failure"]],
        "check_pass_rate": round(check_ok / check_total, 4) if check_total else None,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "mean_latency_seconds": round(sum(r["latency_seconds"] for r in records) / len(records), 2) if records else None,
        "estimated_cost_usd": round(prompt_tokens * price_in_per_m / 1e6 + completion_tokens * price_out_per_m / 1e6, 4),
        "gateway_reported_cost_usd": round(reported_cost, 6) if reported_cost else None,
    }


def write_contact_sheet(records: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path, *, render: bool) -> Path:
    """Self-contained HTML: failures first, each with prompt, render, checks, tokens."""
    ordered = sorted(records, key=lambda r: (r["failure"] is None, FAILURE_KINDS.index(r["failure"]) if r["failure"] else 99, r["id"]))
    cards = []
    for r in ordered:
        img = ""
        if render and r["svg"] and r["failure"] not in {"render_error"}:
            try:
                img = f'<img src="{png_data_url(render_svg_png(r["svg"], size=320))}" alt="">'
            except Exception:
                img = "<div class=noimg>render failed</div>"
        elif r["svg"]:
            img = f'<div class=inline>{r["svg"]}</div>'
        failed_checks = "".join(f"<li class=bad>{html.escape(c['check'])}</li>" for c in r["checks"] if not c["ok"])
        passed = sum(1 for c in r["checks"] if c["ok"])
        status = r["failure"] or "ok"
        usage = r["usage"]
        svg_link = f'<a href="outputs/{r["id"]}-{r["sample"]}.svg">svg</a>' if r["svg"] else ""
        raw_head = f"<pre>{html.escape(r.get('raw_head', ''))}</pre>" if r.get("raw_head") else ""
        error = f"<pre>{html.escape(r['error'])}</pre>" if r.get("error") else ""
        cards.append(
            f'<section class="card {status}"><header><b>{html.escape(r["id"])}</b>'
            f'<span class="badge {status}">{status}</span> {svg_link}</header>'
            f'<p class=prompt>{html.escape(r["prompt"])}</p>{img}'
            f'<ul class=checks><li>{passed}/{len(r["checks"])} checks passed</li>{failed_checks}</ul>{error}{raw_head}'
            f'<footer>{usage.get("prompt_tokens", "?")} in / {usage.get("completion_tokens", "?")} out · '
            f'{r["latency_seconds"]}s · finish={r["finish_reason"]} · ink={r["ink_fraction"]}</footer></section>'
        )
    fails = ", ".join(f"{k}: {v}" for k, v in summary["failures"].items() if v) or "none"
    page = f"""<!doctype html><meta charset=utf-8><title>SVG generation eval</title>
<style>
body{{font:14px system-ui;margin:24px;background:#fafafa;color:#222}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px;border-left:6px solid #2a9d4a}}
.card:not(.ok){{border-left-color:#d33}} header{{display:flex;gap:8px;align-items:center}}
.badge{{font-size:11px;padding:2px 6px;border-radius:4px;background:#2a9d4a;color:#fff}} .badge:not(.ok){{background:#d33}}
.prompt{{color:#555;font-size:12px;max-height:5em;overflow:auto}} img,.inline svg{{width:100%;max-height:320px;background:#fff;border:1px solid #eee}}
.checks{{padding-left:18px;margin:8px 0}} .bad{{color:#b00}} pre{{font-size:11px;white-space:pre-wrap;background:#f4f4f4;padding:6px;max-height:8em;overflow:auto}}
footer{{font-size:11px;color:#777}}
</style>
<h1>SVG generation eval</h1>
<p><b>{summary['ok']}/{summary['cases']} ok</b> · failures — {fails} · check pass rate {summary['check_pass_rate']} ·
{summary['prompt_tokens']} in / {summary['completion_tokens']} out tokens · est. ${summary['estimated_cost_usd']}</p>
<div class=grid>{''.join(cards)}</div>"""
    path = output_dir / "index.html"
    path.write_text(page)
    return path


def run_generation_eval(
    model: ModelAdapter,
    cases: list[GenerationCase],
    output_dir: str | Path,
    *,
    render: bool = True,
    samples: int = 1,
    template_name: str = "generation_v1",
    price_in_per_m: float = 0.0,
    price_out_per_m: float = 0.0,
    log=print,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    (output_dir / "outputs").mkdir(parents=True, exist_ok=True)
    template = load_prompt_template(template_name)
    records: list[dict[str, Any]] = []
    with (output_dir / "results.jsonl").open("w") as results_file:
        for case in cases:
            for sample in range(samples):
                record = evaluate_case(model, case, template, render=render, sample=sample)
                if record["svg"]:
                    (output_dir / "outputs" / f"{case.id}-{sample}.svg").write_text(record["svg"])
                records.append(record)
                results_file.write(json.dumps(record, sort_keys=True) + "\n")
                results_file.flush()
                usage = record["usage"]
                log(
                    f"[{len(records)}/{len(cases) * samples}] {case.id}: {record['failure'] or 'ok'} "
                    f"({usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out, {record['latency_seconds']}s)"
                )
    summary = summarize(records, price_in_per_m, price_out_per_m)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_contact_sheet(records, summary, output_dir, render=render)
    return summary


def rescore(output_dir: str | Path, cases: list[GenerationCase], *, render: bool, price_in_per_m: float = 0.0, price_out_per_m: float = 0.0) -> dict[str, Any]:
    """Re-run the checks over a stored results.jsonl (no model calls) and rewrite summary + contact sheet."""
    output_dir = Path(output_dir)
    by_id = {c.id: c for c in cases}
    records = [json.loads(line) for line in (output_dir / "results.jsonl").read_text().splitlines() if line.strip()]
    for record in records:
        case = by_id.get(record["id"])
        if case is None or not record.get("svg") or record["failure"] in {"truncated", "parse_error", "render_error", "blank_render"}:
            continue
        record["checks"] = run_checks(parse_svg(record["svg"]), case.checks)
        record["failure"] = None if all(c["ok"] for c in record["checks"]) else "checks_failed"
    (output_dir / "results.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    summary = summarize(records, price_in_per_m, price_out_per_m)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_contact_sheet(records, summary, output_dir, render=render)
    return summary
