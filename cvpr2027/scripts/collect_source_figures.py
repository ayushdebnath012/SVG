"""Collect the source pages' own figures for every FEMCAD-Hard task (geometry/mesh views first, then result plots).

Wolfram documentation pages pair each output image (div.clipboard-output, data-src = Files/<Page>.en/O_k.png) with the
input code before it and the caption (div.MCap) before that; the code decides the kind (geometry, mesh or result).
mfem.org pages contribute their content images with nearby captions. Images are downloaded politely into git-ignored
tmp/femcad-figures/ (they are Wolfram's / MFEM's, so they are referenced by URL, not redistributed);
data/femcad-hard-v1/figures.json maps each source URL to its figures (url, caption, code, kind, size, local path), and a
local viewer tmp/femcad-figures/index.html shows every task with its figures.

  python scripts/collect_source_figures.py
"""
from __future__ import annotations

import hashlib
import html as htmllib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/femcad-hard-v1"
FIG = ROOT / "tmp/femcad-figures"
UA = "Mozilla/5.0 (compatible; academic FEM-benchmark research; contact ayushdebnath0123@gmail.com)"
GEOMETRY = re.compile(r"OpenCascadeShape|RegionPlot|Graphics3D|Graphics\[|Region\[|Cuboid|Cylinder|Ball|Polygon|Disk|"
                      r"Rectangle|BoundaryMesh|Annulus|Circle|Line\[|Tube")
MESH = re.compile(r"Wireframe|Edgeframe|ToElementMesh|ElementMesh|\bmesh\b|bmesh")
RESULT = re.compile(r"ContourPlot|DensityPlot|Plot\[|ListAnimate|Legended|SliceContour|VectorPlot|Deformation")


def raw_page(url: str) -> Path | None:
    for folder in (ROOT / "tmp/wolfram-fem-scrape", ROOT / "tmp/mfem-scrape"):
        for f in folder.glob("*.json"):
            rec = json.loads(f.read_text())
            if rec["url"].rstrip("/").replace("http://", "https://") == url.rstrip("/").replace("http://", "https://"):
                return f.with_suffix(".html")
    return None


def num(v) -> int:
    m = re.match(r"\s*(\d+)", str(v or ""))
    return int(m.group(1)) if m else 0


def curated() -> dict:
    f = DATA / "figure-curation.json"
    return json.loads(f.read_text())["keep"] if f.exists() else {}


def wolfram_figures(url: str, page: str, keep: dict) -> list[dict]:
    soup = BeautifulSoup(page, "html.parser")
    out, caption, code = [], "", ""
    for el in soup.find_all(["div", "figure", "p"]):
        cls = el.get("class") or []
        if el.name == "p" and "Picture" in cls:  # page illustrations / schematics
            img = el.find("img")
            if img and min(num(img.get("width")), num(img.get("height"))) >= 80:
                out.append(dict(url=urllib.parse.urljoin(url, img["src"]), caption=caption or (img.get("title") or ""),
                                code="", kind="figure", width=num(img.get("width")), height=num(img.get("height"))))
            continue
        if "MCap" in cls:
            caption = el.get_text(" ", strip=True).rstrip(":")
        elif el.name == "figure" and "figure-input" in cls:
            c = el.find("code")
            code = htmllib.unescape(c.get_text()).strip() if c else ""
        elif "clipboard-output" in cls and el.get("data-src"):
            w, h = num(el.get("data-out-width")), num(el.get("data-out-height"))
            src = urllib.parse.urljoin(url, el["data-src"])
            if min(w, h) < 60 and src not in keep:  # small inline results (numbers, short expressions)
                continue
            kind = "result" if RESULT.search(code) else "mesh" if MESH.search(code) else "geometry" if GEOMETRY.search(code) else None
            if kind or src in keep:
                out.append(dict(url=src, caption=caption, code=code[:400], kind=kind or "figure", width=w, height=h))
    return out


def mfem_figures(url: str, page: str) -> list[dict]:
    soup = BeautifulSoup(page, "html.parser")
    out = []
    for img in soup.body.find_all("img"):  # not only div[role=main]: the examples page lists most examples outside it
        if img.find_parent(["nav", "header", "footer"]):
            continue
        src = img.get("src") or ""
        if not src or src.startswith("data:") or re.search(r"logo|icon|badge|favicon", src, re.I):
            continue
        cap = (img.get("alt") or "").strip()
        head = img.find_previous(["h1", "h2", "h3", "h4"])  # the section (e.g. "Example 19: ...") names the picture
        if head and not cap:
            cap = head.get_text(" ", strip=True)[:300]
        base = url if url.endswith("/") else url + "/"  # mfem.org pages are directories; relative images resolve inside them
        out.append(dict(url=urllib.parse.urljoin(base, src), caption=cap, code="", kind="figure", width=0, height=0))
    return out


def download(fig: dict, folder: Path) -> None:
    name = hashlib.sha1(fig["url"].encode()).hexdigest()[:10] + Path(urllib.parse.urlparse(fig["url"]).path).suffix
    dest = folder / name
    fig["local"] = str(dest.relative_to(ROOT))
    if dest.exists():
        return
    cached = next(FIG.rglob(name), None)  # same image already fetched for another page or in the review cache
    if cached:
        dest.write_bytes(cached.read_bytes())
        return
    req = urllib.request.Request(fig["url"], headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            dest.write_bytes(r.read())
    except Exception as e:  # noqa: BLE001 - a missing image is recorded, not fatal
        fig["local"] = None
        fig["error"] = type(e).__name__
    time.sleep(0.5)


def viewer(tasks: list[dict], figs: dict) -> str:
    cards = []
    for t in tasks:
        fs = figs.get(t["source"]["url"].rstrip("/").replace("http://", "https://"), [])
        ims = "".join(f'<figure><a href="{htmllib.escape(f["url"])}"><img loading="lazy" src="../../{htmllib.escape(f["local"])}"></a>'
                      f'<figcaption><b>{f["kind"]}</b> {htmllib.escape(f["caption"])}</figcaption></figure>'
                      for f in fs if f.get("local"))
        cards.append(f'<section><h2>{t["id"]} · {htmllib.escape(t["title"])}</h2><p>{t["category"]} · {t["tier"]} · '
                     f'<a href="{htmllib.escape(t["source"]["url"])}">{htmllib.escape(t["source"]["page"])}</a> · {len(fs)} figures</p>'
                     f'<div class="g">{ims or "<i>no figures on the source page</i>"}</div></section>')
    css = ("body{font:14px system-ui;margin:24px;background:#f5f6f7;color:#18212b}section{background:#fff;border:1px solid #dde;"
           "border-radius:8px;padding:12px 16px;margin:12px 0}h2{font-size:17px;margin:0 0 4px}.g{display:grid;grid-template-columns:"
           "repeat(auto-fill,minmax(220px,1fr));gap:10px}figure{margin:0}img{width:100%;height:180px;object-fit:contain;"
           "background:#fafafa;border:1px solid #eee}figcaption{font-size:12px;color:#555}")
    return f"<!doctype html><meta charset=utf-8><title>FEMCAD-Hard figures</title><style>{css}</style>" + "".join(cards)


def main() -> None:
    tasks = [json.loads(l) for l in (DATA / "tasks.jsonl").read_text().splitlines()]
    pages = [t["source"]["url"] for t in tasks] + [t["source"]["geometry_page"]["url"] for t in tasks if "geometry_page" in t["source"]]
    urls = sorted({u.rstrip("/").replace("http://", "https://") for u in pages})
    keep, figs = curated(), {}
    for url in urls:
        raw = raw_page(url)
        if not raw or not raw.exists():
            print("NO RAW PAGE", url)
            continue
        page = raw.read_text(errors="replace")
        fs = wolfram_figures(url, page, keep) if "wolfram.com" in url else mfem_figures(url, page)
        order = {"geometry": 0, "mesh": 1, "figure": 2, "result": 3}
        fs = sorted(fs, key=lambda f: (f["url"] not in keep, order[f["kind"]]))
        fs = [f for f in fs if f["url"] in keep] + [f for f in fs if f["url"] not in keep][:max(0, 24 - sum(f["url"] in keep for f in fs))]
        folder = FIG / re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[1])[-80:]
        folder.mkdir(parents=True, exist_ok=True)
        for f in fs:
            download(f, folder)
        figs[url] = fs
        print(f"{len(fs):3d} figures ({sum(f['kind'] == 'geometry' for f in fs)} geometry, {sum(f['kind'] == 'mesh' for f in fs)} mesh) {url}", flush=True)
    (DATA / "figures.json").write_text(json.dumps(dict(note="Figures belong to their source sites; referenced by URL, local copies "
                                                            "in git-ignored tmp/femcad-figures/.", pages=figs), indent=1, ensure_ascii=False))
    (FIG / "index.html").write_text(viewer(tasks, figs))
    print(json.dumps(dict(pages=len(figs), figures=sum(len(v) for v in figs.values()),
                          downloaded=sum(1 for v in figs.values() for f in v if f.get("local")))))


if __name__ == "__main__":
    main()
