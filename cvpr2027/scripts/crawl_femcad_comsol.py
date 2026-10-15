"""Bounded crawl of published COMSOL FEM examples and original geometry figures.

Only fetches existing pages/images. Model selection and figure review are recorded
separately; this script does not generate engineering problems or drawings.
"""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tmp/femcad-comsol-crawl"
DATA = ROOT / "data/femcad-hard-v1"


def clean(s):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s)).split())


def get(url, suffix="html"):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:16] + "." + suffix)
    if not path.exists():
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
    return path.read_bytes(), path


def discover():
    galleries = {"nonlinear-structural-materials-module": 8, "composite-materials-module": 3,
                 "mems-module": 4, "acoustics-module": 3, "structural-mechanics-module": 3}
    urls = [f"https://www.comsol.com/models/{module}" + (f"/page/{n}?sort=popularity" if n > 1 else "")
            for module, count in galleries.items() for n in range(1, count + 1)]
    def one(url):
        content, path = get(url)
        s = content.decode()
        entries = []
        for m in re.finditer(r'<a class="model_db__title" href="([^"]+)"[^>]*>(.*?)</a>', s, re.S):
            fragment = s[m.end():m.end()+2200]
            desc = re.search(r'<p class="model_db__model_desc">(.*?)</p>', fragment, re.S)
            entries.append(dict(title=clean(m[2]), gallery_url=url, url=urljoin(url,html.unescape(m[1])),
                                gallery_description=clean(desc[1]) if desc else ""))
        return entries
    found = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for entries in pool.map(one, urls):
            for r in entries:
                found.setdefault(r["url"], r)
    (CACHE / "discovered.json").write_text(json.dumps(list(found.values()), indent=2))
    print(f"Crawled {len(urls)} gallery pages; discovered {len(found)} distinct existing examples.")
    for i, r in enumerate(found.values()):
        print(i, r["title"])


def inspect_one(r):
    model_id = r["url"].split("-")[-1]
    files_path = CACHE / (f"files-{model_id}.json")
    if not files_path.exists():
        resp = requests.post("https://www.comsol.com/models/get-the-files", data={"id":model_id}, timeout=60)
        resp.raise_for_status()
        files_path.write_text(resp.text)
    files_html = json.loads(files_path.read_text())["data"]["html"]
    pdfs = re.findall(r'href="([^"]+/models\.([^.]+)\.([^.]+)\.pdf)"', files_html)
    if not pdfs:
        return dict(**r, error="No published tutorial PDF found")
    module, name = pdfs[-1][1:]
    content = None
    for version in ("6.4", "6.3", "6.2"):
        url = f"https://doc.comsol.com/{version}/doc/com.comsol.help.models.{module}.{name}/{name}.html"
        try:
            content, path = get(url)
            if b"Modeling Instructions" in content or b"Model Definition" in content:
                break
        except requests.RequestException:
            continue
    if content is None:
        return dict(**r, error="Tutorial HTML unavailable")
    s = content.decode()
    body = re.findall(r'<div class="Body_text"[^>]*>(.*?)</div>', s, re.S)
    paragraphs = [clean(x) for x in body]
    figures = []
    for m in re.finditer(r'<div class="FigureTitle_ML"[^>]*>(.*?)</div>', s, re.S):
        before = s[:m.start()]
        images = re.findall(r'<img[^>]+src="([^"]+)"',before)
        if images:
            figures.append(dict(caption=clean(m[1]), url=urljoin(url, html.unescape(images[-1]))))
    return dict(**r, source_url=url, source_local=str(path.relative_to(ROOT)),
                source_sha256=hashlib.sha256(content).hexdigest(), tutorial_pdf_url=urljoin(r["url"], pdfs[-1][0]),
                module=module, model_name=name, paragraphs=paragraphs, figure_candidates=figures)


def inspect():
    rows = json.loads((CACHE / "discovered.json").read_text())
    selected = json.loads((CACHE / "selection.json").read_text())
    chosen = [rows[i] for i in selected]
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(inspect_one,r):r for r in chosen}
        for f in concurrent.futures.as_completed(futures):
            r = futures[f]
            try:
                result = f.result()
            except Exception as e:
                result = dict(**r, error=str(e))
            out.append(result)
            print(result["title"], result.get("error",f"{len(result.get('figure_candidates',[]))} source figures"), flush=True)
    out.sort(key=lambda r: selected.index(next(i for i in selected if rows[i]["url"] == r["url"])))
    (CACHE / "inspected.json").write_text(json.dumps(out, indent=2))


def collect():
    inspected = json.loads((CACHE / "inspected.json").read_text())
    selected = json.loads((DATA / "comsol-crawl-selection.json").read_text())["studies"]
    advanced_path = DATA / "advanced-source-studies.json"
    advanced = json.loads(advanced_path.read_text())
    # Keep the five studies already requested; repeated runs replace crawl additions.
    advanced["studies"] = advanced["studies"][:5]
    pages = advanced["pages"][:6]
    jobs, additions = [], []
    for i, selection in enumerate(selected, 6):
        r = inspected[selection["crawl_index"]]
        if r.get("error"):
            raise ValueError(f"Selected study lacks a fetched tutorial: {r['title']}")
        category = ("Multiphysics" if r["module"] in {"mems","acdc"} else
                    "Acoustics" if r["module"] == "aco" else "Solid Mechanics")
        row = dict(id=f"FEMCAD-ADV-{i:03d}", title=r["title"], category=category,
                   model_kind="Published source study; see tutorial for dimensional formulation",
                   source_url=r["source_url"], gallery_url=r["url"], tutorial_pdf_url=r["tutorial_pdf_url"],
                   source_sha256=r["source_sha256"],
                   geometry="Original geometry references are reproduced below. Exact dimensions, material definitions, boundary selections and construction steps remain in the linked tutorial and any referenced model files.",
                   analysis=selection["analysis"], outputs=selection["outputs"],
                   reference="Published study outputs are available in the linked source. Numerical grading references and tolerances have not been extracted or validated; no new FEM solution was run.",
                   notes="Existing published analysis, summarized from the crawled tutorial. Difficulty is an editorial assessment, not a measured solver or model failure rate.",
                   figures=[])
        for j in selection["figures"]:
            f = r["figure_candidates"][j]
            number = re.search(r"Figure\s+(\d+)",f["caption"])[1]
            kind = "part-mesh" if "mesh" in f["caption"].lower() else "reference-image"
            jobs.append((row,dict(url=f["url"], caption=f"Original source Figure {number}: geometry reference",
                                  original_source_caption=f["caption"], kind=kind)))
        additions.append(row)
        pages.append(dict(url=r["source_url"],local=r["source_local"],sha256=r["source_sha256"]))
    def fetch_image(job):
        row, f = job
        try:
            content, path = get(f["url"],"png")
            with Image.open(path) as image:
                image.verify()
            f["local"] = str(path.relative_to(ROOT))
            f["sha256"] = hashlib.sha256(content).hexdigest()
            return row, f, None
        except Exception as error:
            return row, f, str(error)
    missing = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for row, f, error in pool.map(fetch_image,jobs):
            if error:
                missing.append(dict(id=row["id"],url=f["url"],reason=error))
            else:
                row["figures"].append(f)
    advanced["studies"].extend(additions)
    advanced["pages"] = pages
    advanced["crawl"] = dict(gallery_pages=21, discovered_examples=193, inspected_examples=len(inspected),
                             selected_additions=len(additions), retrieved_geometry_images=len(jobs)-len(missing),
                             omitted_unavailable_images=missing, visual_review="pending")
    advanced["fetched_utc"] = datetime.now(timezone.utc).isoformat()
    advanced_path.write_text(json.dumps(advanced,indent=2)+"\n")
    print(f"{len(advanced['studies'])} advanced published studies; {len(jobs)-len(missing)} new reference images; {len(missing)} unavailable images omitted.")


if __name__ == "__main__":
    import sys
    CACHE.mkdir(parents=True, exist_ok=True)
    {"discover":discover,"inspect":inspect,"collect":collect}[sys.argv[1]]()
