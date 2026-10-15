"""Illustrated PDF of FEMCAD-Hard v1: a summary page, the FEM page's category showcase, then one page per task with the
source page's drawings of the part, the geometry and analysis specification and the outputs with their references.

The PDF embeds Wolfram's and MFEM's images (local copies from tmp/femcad-figures/), so it is written to git-ignored tmp/
and is for research use, not for redistribution.

  python scripts/export_femcad_hard_pdf.py   -> tmp/femcad-hard-v1.pdf
"""
from __future__ import annotations

from collections import Counter
import html
import json
from pathlib import Path
import re
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/femcad-hard-v1"
ASSETS = {r['id']: r for r in json.loads((DATA / 'reference-assets.json').read_text())['studies']}
OUT = ROOT / "tmp/femcad-hard-v1.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CATEGORIES = ["Geometric Modeling", "Mesh Generation", "Heat Transfer", "Fluid Dynamics", "Mass Transport", "Solid Mechanics",
              "Acoustics", "Electromagnetics", "Multiphysics", "System Physics", "Seamless Workflow"]
CSS = """
@page { size: A4; margin: 14mm 14mm 16mm; }
* { box-sizing: border-box; }
body { font: 9.6pt/1.42 "Helvetica Neue", Helvetica, Arial, sans-serif; color: #17232e; margin: 0; }
h1 { font-size: 26pt; margin: 0 0 4pt; letter-spacing: -.01em; }
h2 { font-size: 13pt; margin: 14pt 0 6pt; }
.kick { font: 600 8pt/1 Menlo, monospace; letter-spacing: .12em; text-transform: uppercase; color: #1d6a8a; }
.lede { font-size: 10.5pt; max-width: 165mm; }
.stats { display: flex; gap: 18pt; border-top: 2px solid #17232e; border-bottom: 1px solid #cdd6dc; padding: 8pt 0; margin: 10pt 0; }
.stats b { display: block; font-size: 20pt; line-height: 1; } .stats span { font: 7.5pt Menlo, monospace; text-transform: uppercase; color: #5a6672; }
table { border-collapse: collapse; width: 100%; } th, td { text-align: left; padding: 3pt 6pt; border-bottom: 1px solid #dfe5e9; vertical-align: top; }
th { font: 600 7.5pt Menlo, monospace; text-transform: uppercase; letter-spacing: .05em; color: #5a6672; background: #f2f5f7; }
td.m { font-family: Menlo, monospace; font-size: 8.5pt; white-space: nowrap; }
.task { break-before: page; }
.meta { display: flex; gap: 8pt; align-items: center; font-size: 8.5pt; color: #5a6672; }
.id { font: 600 9pt Menlo, monospace; color: #17232e; }
.pill { font: 600 7pt Menlo, monospace; text-transform: uppercase; padding: 1pt 6pt; border-radius: 8pt; }
.hard { background: #e1f0e5; color: #2f6a40; } .complex { background: #f6ecd6; color: #865a0c; } .hardest { background: #f7e1dd; color: #9a2f23; }
h3 { font-size: 14.5pt; margin: 4pt 0 3pt; }
.src { font-size: 8.5pt; color: #3b4853; margin-bottom: 6pt; overflow-wrap: anywhere; } .flag { color: #865a0c; }
.figs { display: grid; grid-template-columns: repeat(var(--n), 1fr); gap: 6pt; margin: 6pt 0 8pt; }
.figs figure { margin: 0; border: 1px solid #dfe5e9; border-radius: 4pt; padding: 4pt; background: #fff; }
.figs img { width: 100%; height: var(--h); object-fit: contain; display: block; }
.figs figcaption { font-size: 7pt; color: #5a6672; margin-top: 2pt; line-height: 1.25; }
.figs .k { font: 600 6.5pt Menlo, monospace; text-transform: uppercase; color: #1d6a8a; }
.spec h4 { font: 600 7.5pt Menlo, monospace; text-transform: uppercase; letter-spacing: .06em; color: #5a6672; margin: 7pt 0 2pt; }
.spec p { margin: 0; text-align: justify; }
.ref { font-family: Menlo, monospace; font-size: 8.5pt; } .pend { color: #8a8f96; } .page { font-size: 6.5pt; color: #5a6672; }
.tags { margin-top: 6pt; } .tags span { display: inline-block; font-size: 7.5pt; border: 1px dashed #c5cfd6; border-radius: 3pt; padding: 0 5pt; margin: 0 4pt 3pt 0; color: #5a6672; }
ul.notes { margin: 4pt 0 0; padding-left: 12pt; font-size: 8pt; color: #5a6672; }
.show { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8pt; } .show figure { margin: 0; } .show img { width: 100%; }
.cat { break-inside: avoid; margin-top: 8pt; } .cat h4 { font: 600 8pt Menlo, monospace; text-transform: uppercase; letter-spacing: .06em; color: #1d6a8a; margin: 0 0 4pt; }
.show figcaption { font-size: 8pt; color: #5a6672; }
.foot { font-size: 7.5pt; color: #5a6672; margin-top: 10pt; }
.advanced { background: #f7e1dd; color: #9a2f23; }
.drawing-sheet figure { margin: 7pt 0; border: 1px solid #dfe5e9; padding: 5pt; break-inside: avoid; }
.drawing-sheet img { width: 100%; max-height: 65mm; object-fit: contain; }
.drawing-sheet figcaption { font-size: 8pt; color: #5a6672; }
.asset-note { font-size: 8pt; margin: 5pt 0; padding: 5pt 7pt; background: #edf5f7; border-left: 2pt solid #1d6a8a; }
.asset-index td { font-size: 8pt; padding: 5pt 5pt; overflow-wrap: anywhere; }
"""


def e(s) -> str:
    return html.escape(str(s))


def img(local: str) -> str:
    return (ROOT / local).as_uri()


def pick(figs: list[dict], n: int = 4) -> list[dict]:
    """Prefer dimensioned drawings, then the most complete CAD views (later on the page), then a part mesh."""
    seen, unique = [], []
    for f in figs:  # the same picture can sit on a page under two output names: compare 24 x 24 grey thumbnails
        if not f.get("local"):
            continue
        im = Image.open(ROOT / f["local"])
        im.seek(0)
        thumb = list(im.convert("RGBA").resize((24, 24)).convert("L").tobytes())
        if all(sum(abs(a - b) for a, b in zip(thumb, t)) / len(t) > 4 for t in seen):
            seen.append(thumb)
            unique.append(f)
    figs = unique
    by = {k: [f for f in figs if f["kind"] == k and f.get("local")] for k in ("drawing", "cad", "part-mesh")}
    chosen = by["drawing"][:2] + by["cad"][-3:] + by["part-mesh"][:1]
    chosen = chosen[:n] if len(chosen) >= n else chosen + [f for f in figs if f not in chosen and f.get("local")][:n - len(chosen)]
    return sorted(chosen, key=figs.index)


def task_page(r: dict) -> str:
    pr = r["prompt"]
    geo = pr.split("Geometry. ", 1)[1].split("\n\nAnalysis. ", 1)[0]
    ana = pr.split("\n\nAnalysis. ", 1)[1].split("\n\nOutputs", 1)[0]
    figs = pick(r["figures"])
    n = len(figs)
    height = {1: "62mm", 2: "58mm", 3: "48mm", 4: "40mm"}.get(n, "40mm")
    fig_html = "".join(f'<figure><img src="{img(f["local"])}"><figcaption><span class="k">{e(f["kind"])}</span> '
                       f'{e(f["caption"][:90])}</figcaption></figure>' for f in figs)
    gp = r["source"].get("geometry_page")
    src = (f'Source: {e(r["source"]["page"])} ({r["source"]["site"]}) &middot; <span style="font-family:Menlo">'
           f'{e(r["source"]["url"])}</span>')
    if gp:
        src += f'<br>Part built on: {e(gp["page"])} &middot; <span style="font-family:Menlo">{e(gp["url"])}</span>'
    if r["analysis_source"] != "source page":
        src += '<br><span class="flag">Analysis set here: the source page builds the CAD only.</span>'
    qrows = "".join(
        f'<tr><td class="m">{e(q["key"])}</td><td>{e(q["unit"])}</td><td>{e(q["definition"])}</td>'
        + (f'<td class="ref pend">pending</td>' if q["reference"] is None else
           f'<td class="ref">{e(q["reference"])}<div class="page">{e(q["reference_source"])}</div></td>')
        + f'<td class="ref">&plusmn;{round(q["rel_tol"] * 100)}%</td></tr>' for q in r["qois"])
    notes = "".join(f"<li>{e(x)}</li>" for x in r["provenance_notes"])
    return f'''<section class="task">
  <div class="meta"><span class="id">{r["id"]}</span><span class="pill {r["tier"]}">{r["tier"]}</span>
    <span>{e(r["category"])} &middot; {e(r["model_kind"])} &middot; {len(r["figures"])} drawings on the page</span></div>
  <h3>{e(r["title"])}</h3>
  <div class="src">{src}</div>
  <div class="figs" style="--n:{max(n, 1)};--h:{height}">{fig_html}</div>
  <div class="spec"><h4>Geometry</h4><p>{e(geo)}</p><h4>Analysis</h4><p>{e(ana)}</p></div>
  <h4 style="font:600 7.5pt Menlo,monospace;text-transform:uppercase;letter-spacing:.06em;color:#5a6672;margin:8pt 0 3pt">Outputs</h4>
  <table><tr><th>Key</th><th>Unit</th><th>Definition</th><th>Reference</th><th>Tol</th></tr>{qrows}</table>
  <div class="tags">{"".join(f"<span>{e(w)}</span>" for w in r["targets_failure_modes"])}</div>
  {f'<ul class="notes">{notes}</ul>' if notes else ""}
</section>'''


def cover(rows: list[dict], advanced: list[dict]) -> str:
    cats = Counter(r["category"] for r in rows + advanced)
    status = Counter(r["reference"]["status"] for r in rows)
    tiers = Counter(r["tier"] for r in rows)
    set_here = [r["id"] for r in rows if r["analysis_source"] != "source page"]
    cat_rows = "".join(
        f"<tr><td>{c}</td><td>{sum(r['category'] == c for r in advanced)}</td><td>"
        + (f"{sum(r['category'] == c for r in advanced)} published FEM studies" if any(r['category'] == c for r in advanced) else "&mdash;")
        + "</td></tr>"
        for c in CATEGORIES)
    index_rows = [f'<tr><td class="m">{r["id"]}</td><td>{e(r["title"])}</td><td>{e(r["category"])}</td><td>{r["tier"]}</td>'
                  f'<td>{r["reference"]["status"]}</td></tr>' for r in rows]
    index_rows += [f'<tr><td class="m">{r["id"]}</td><td>{e(r["title"])}</td><td>{e(r["category"])}</td>'
                   '<td>advanced*</td><td>source study</td></tr>' for r in advanced]
    index = "".join(f'<section><h2 style="break-before:page">Task index ({start+1}-{min(start+16,len(index_rows))} of {len(index_rows)})</h2>'
                    '<table><thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Tier</th><th>Reference</th></tr></thead>'
                    f'<tbody>{"".join(index_rows[start:start+16])}</tbody></table></section>'
                    for start in range(0,len(index_rows),16))
    stats = [(len(advanced), "published FEM studies"),
             (len({f["url"] for r in advanced for f in r["figures"]}), "source images"),
             (len({r['source_url'] for r in advanced}), "linked tutorials")]
    return f'''<div class="kick">ReSolve &middot; CVPR 2027 &middot; dataset</div>
<h1>FEMCAD-Hard v1</h1>
<p class="lede">{len(advanced)} published COMSOL FEM source studies selected for demanding nonlinear mechanics,
coupled physics, composite laminates and structural dynamics. Every study comes from a crawled source tutorial;
reference images are reproduced from that source. No new engineering problem, loading case or drawing was invented.
Geometry references include CAD views, dimensioned drawings, layer layouts and part meshes.</p>
<div class="stats">{"".join(f"<div><b>{n}</b><span>{l}</span></div>" for n, l in stats)}</div>
<h2>Categories: difficult FEM source studies</h2>
<table><tr><th>Category</th><th>Tasks</th><th>IDs (FEMCAD-)</th></tr>{cat_rows}</table>
<p class="foot">*Difficulty is assessed from the published geometry and FEM analysis, not measured model performance.
These source studies have not been tested against Astra. Full numerical grading references and tolerances have not
been validated; no new CAD or FEM solutions were generated. All 50 studies now link to published solver models
with verified binary mesh and solution archive entries. Four standalone numerical reference tables are included
in the asset catalog. See the published FEM assets appendix. Introductory examples are excluded from this edition.
Original reference images &copy; COMSOL.</p>
{index}
<p class="foot">ADV entries summarize the source's geometry, analysis and published outputs. Exact construction and full
solver settings remain in the linked tutorials. Approximate values and plots are not automatic grading targets.</p>'''


def showcase() -> str:
    """Every diagram of the Wolfram FEM page's category carousels (wolfram.com/language/core-areas/fem), by category."""
    show = json.loads((DATA / "fem-showcase.json").read_text())["categories"]
    sections = []
    for c in CATEGORIES:
        figs = [f for f in show.get(c, []) if f.get("local")]
        cells = "".join(f'<figure><img src="{img(f["local"])}"><figcaption>{e(label(f["url"]))}</figcaption></figure>'
                        for f in figs)
        sections.append(f'<div class="cat"><h4>{e(c)} &middot; {len(figs)}</h4><div class="show">{cells}</div></div>')
    n = sum(len([f for f in show.get(c, []) if f.get("local")]) for c in CATEGORIES)
    return (f'<section class="task"><div class="kick">Wolfram FEM page</div><h2>FEM diagrams by category ({n})</h2>'
            f'<p class="foot" style="margin-top:0">All carousel diagrams of https://www.wolfram.com/language/core-areas/fem/ '
            f'under its eleven categories, crawled from the page. &copy; Wolfram Research; included for research use.</p>'
            + "".join(sections) + "</section>")


def label(url: str) -> str:
    """'FEM-StressInSpoon-1.png' -> 'Stress In Spoon'; generic names keep their number: 'fem-mesh-generation-03-3.png' ->
    'Mesh Generation 3' (the diagrams carry their own captions)."""
    stem = re.sub(r"^(fem|FEM)-", "", url.rsplit("/", 1)[-1].rsplit(".", 1)[0])
    number = re.search(r"-(\d+)$", stem)
    stem = re.sub(r"(-\d+)+$", "", stem)
    named = bool(re.search(r"[a-z][A-Z]", stem))  # CamelCase names say what the diagram shows
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem).replace("-", " ").split()
    text = " ".join(w if w.isupper() else w.capitalize() for w in words)
    return text if named or not number else f"{text} {int(number.group(1))}"


def advanced_page(r: dict) -> str:
    figs = r["figures"][:2] if r["id"] == "FEMCAD-ADV-005" else r["figures"]
    n = len(figs)
    height = "80mm" if n == 1 else "65mm" if n == 2 else "55mm"
    columns = n
    if r["id"] == "FEMCAD-ADV-005":
        columns, height = 1, "48mm"
    elif n == 3:
        columns, height = 2, "50mm"
    fig_html = "".join(
        ('<figure style="grid-column:span 2;--h:60mm">' if n == 3 and
         ((r["id"] == "FEMCAD-ADV-002" and i == 2) or (r["id"] == "FEMCAD-ADV-004" and i == 0)) else '<figure>')
        + f'<a href="{e(f["url"])}"><img src="{img(f["local"])}"></a>'
        f'<figcaption><span class="k">{e(f["kind"])}</span> {e(f["caption"])}</figcaption></figure>'
        for i, f in enumerate(figs))
    geometry_src = (f'<br>Base geometry/thermal study: <a href="{e(r["geometry_source"])}">{e(r["geometry_source"])}</a>'
                    if r.get("geometry_source") else "")
    tier = "Difficult FEM*"
    assets = ASSETS.get(r['id'], {})
    solved = next((f for f in assets.get('files', []) if f.get('solution_binary_entries')), None)
    numeric = [f for f in assets.get('files', []) if f.get('data_kind') in ('experimental_reference', 'published_response_reference')]
    asset_note = (f'<div class="asset-note"><b>Published FEM data:</b> <a href="{e(solved["url"])}">{e(solved["name"])}</a> '
                  f'(COMSOL {e(solved["version"])}): binary mesh and solution entries verified. '
                  + (f'{len(numeric)} standalone numerical reference table(s). ' if numeric else '')
                  + 'Source solution; accuracy and grading tolerances not independently validated.</div>') if solved else ''
    out = f'''<section class="task">
<div class="meta"><span class="id">{e(r['id'])}</span><span class="pill advanced">{tier}</span>
<span>{e(r['category'])} &middot; source study</span></div>
<h3>{e(r['title'])}</h3>
<div class="src">Source: COMSOL tutorial &middot; <a href="{e(r['source_url'])}">{e(r['source_url'])}</a>{geometry_src}</div>
{f'<div class="figs" style="--n:{columns};--h:{height}">{fig_html}</div>' if figs else '<p class="foot">No source geometry image was retrievable; drawing omitted.</p>'}
<div class="spec"><h4>Model</h4><p>{e(r['model_kind'])}</p>
<h4>Geometry and reference drawings</h4><p>{e(r['geometry'])}</p>
<h4>Published analysis</h4><p>{e(r['analysis'])}</p>
<h4>Published outputs</h4><p>{e(r['outputs'])}</p>
<h4>Reference status</h4><p>{e(r['reference'])}</p></div>
{asset_note}
<p class="foot">{e(r['notes'])}<br>*Difficulty is an editorial assessment. Original source figures; no geometry or solution invented here.</p>
</section>'''
    if r["id"] == "FEMCAD-ADV-005":
        sheet = "".join(f'<figure><a href="{e(f["url"])}"><img src="{img(f["local"])}"></a>'
                        f'<figcaption>{e(f["caption"])}</figcaption></figure>' for f in r["figures"][2:])
        out += f'''<section class="task drawing-sheet"><div class="kick">FEMCAD-ADV-005 &middot; reference drawings</div>
<h3>Perforated muffler: dimensioned baffles</h3>
<div class="src">Original source Figures 3-5 &middot; <a href="{e(r['source_url'])}">COMSOL: Muffler with Perforates</a></div>
{sheet}<p class="foot">The analysis represents these perforations using impedance regions. Drawings retain the physical hole layout.</p></section>'''
    return out


def asset_appendix(advanced: list[dict]) -> str:
    parts = ['<section class="task"><div class="kick">Published source assets</div><h3>FEM solver models and numerical references</h3>'
             '<p>All 50 source studies have publicly downloadable COMSOL model files. Their archive directories contain '
             'binary mesh and solution entries, matching the tutorial version used in this dataset. These are existing '
             'published solutions; no model was solved or numerical answer synthesized here.</p>'
             '<p>COMSOL is required to interpret or export the binary fields. Archive checks establish that mesh and solution '
             'data are stored; they do not independently certify physical accuracy or mesh convergence. No complete set of '
             'nodal CSV exports or validated grading tolerances was found in the checked file listings.</p>'
             '<p>80 source files were saved locally (about 159 MB). Larger solver models are linked and their archive '
             'directories were inspected remotely; the full model set is about 19.6 GB. Source URLs, versions, file sizes, '
             'archive entry sizes and hashes of stored files are recorded in reference-assets.json.</p>'
             '<h2>Standalone numerical reference tables</h2><table class="asset-index"><thead><tr><th>Study</th><th>Published file</th><th>Rows</th><th>Reference</th></tr></thead><tbody>']
    for r in advanced:
        for f in ASSETS[r['id']]['files']:
            if f.get('data_kind') in ('experimental_reference', 'published_response_reference'):
                parts.append(f'<tr><td class="m">{e(r["id"])}</td><td><a href="{e(f["url"])}">{e(f["name"])}</a></td>'
                             f'<td>{f["numeric_row_count"]}</td><td>{e(f["data_description"])}</td></tr>')
    parts.append('</tbody></table><h2>Published experimental intervals</h2><p>Sheet metal forming (FEMCAD-ADV-021), '
                 'source Table 1: forming angle 19.6-21.0 degrees; angle after release 53.4-55.8 degrees. '
                 'These are published measurement intervals, not dataset-authored pass/fail tolerances.</p>'
                 '<p class="foot">Material tables, prescribed-displacement functions, CAD profiles and evaluation expressions '
                 'are included as supporting inputs; they are not labeled output ground truth.</p></section>')
    for start in range(0, len(advanced), 14):
        parts.append(f'<section class="task"><div class="kick">Published FEM assets</div><h3>Solver inventory '
                     f'({start+1}-{min(start+14,len(advanced))} of {len(advanced)})</h3>'
                     '<table class="asset-index"><thead><tr><th>Study</th><th>Published solver model</th><th>Version</th><th>Solution entries</th><th>Mesh entries</th></tr></thead><tbody>')
        for r in advanced[start:start+14]:
            f = next(f for f in ASSETS[r['id']]['files'] if f.get('solution_binary_entries'))
            parts.append(f'<tr><td class="m">{e(r["id"])}</td><td><a href="{e(f["url"])}">{e(f["name"])}</a></td>'
                         f'<td>{e(f["version"])}</td><td>{len(f["solution_binary_entries"])}</td>'
                         f'<td>{len(f["mesh_binary_entries"])}</td></tr>')
        parts.append('</tbody></table><p class="foot">Counts refer to binary archive entries, not independent simulations, '
                     'nodes or validated result fields. Click a model filename to retrieve the original source file.</p></section>')
    return ''.join(parts)


def main() -> None:
    rows = []  # Original examples remain in tasks.jsonl; this edition selects difficult source studies.
    advanced_path = DATA / "advanced-source-studies.json"
    advanced = json.loads(advanced_path.read_text())["studies"] if advanced_path.exists() else []
    page = (f"<!doctype html><meta charset=utf-8><title>FEMCAD-Hard v1</title><style>{CSS}</style>"
            + cover(rows, advanced)
            + "".join(advanced_page(r) for r in advanced)
            + asset_appendix(advanced)
            + showcase())  # the Wolfram FEM page's diagrams, all eleven categories
    src = ROOT / "tmp/femcad-hard-v1-print.html"
    src.write_text(page)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--allow-file-access-from-files", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT}", src.as_uri()], check=True, capture_output=True)
    print(OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
