"""Polite scraper for Wolfram's FEM material: the FEM core-area page and the Wolfram documentation it links to.

Scope: starts at https://www.wolfram.com/language/core-areas/fem/ and follows its links to Wolfram hosts only
(www.wolfram.com FEM pages, reference.wolfram.com PDE-model, FEMDocumentation and OpenCascadeLink tutorials and guides,
community.wolfram.com posts). From the PDE-model overview it also follows every Model Collection tutorial, and from the
tutorials and guides it follows their links to further PDE-model, FEMDocumentation and OpenCascadeLink tutorials
(up to depth 3). robots.txt is honoured, requests are spaced, pages already on disk are reused, and the crawl is capped.

Raw HTML and full extracted text/code go to tmp/wolfram-fem-scrape/ (git-ignored: Wolfram's pages are copyrighted and
are not redistributed). data/femcad-hard-v1/wolfram-sources.json keeps only provenance (URL, title, hash, date), the
physics area and the numeric parameters found in each page's code cells.

  python scripts/scrape_wolfram_fem.py [--max-pages 160] [--delay 1.5]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html as htmllib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tmp/wolfram-fem-scrape"
MANIFEST = ROOT / "data/femcad-hard-v1/wolfram-sources.json"
SEED = "https://www.wolfram.com/language/core-areas/fem/"
UA = "Mozilla/5.0 (compatible; academic FEM-benchmark research; contact ayushdebnath0123@gmail.com)"
HOSTS = {"www.wolfram.com", "reference.wolfram.com", "community.wolfram.com"}
FOLLOW = re.compile(r"^https://(www\.wolfram\.com/language/core-areas/fem/|reference\.wolfram\.com/language/"
                    r"(PDEModels/tutorial/|OpenCascadeLink/(tutorial|guide)/|FEMDocumentation/(tutorial|guide)/"
                    r"|guide/[A-Za-z]*(PDEModels|DerivedRegions|Multiphysics))"
                    r"|community\.wolfram\.com/groups/-/m/t/)")
DOCS = re.compile(r"^https://reference\.wolfram\.com/language/(PDEModels/tutorial/|OpenCascadeLink/(tutorial|guide)/"
                  r"|FEMDocumentation/(tutorial|guide)/)[A-Za-z0-9/]+\.html$")
MODEL = re.compile(r"^https://reference\.wolfram\.com/language/PDEModels/tutorial/[A-Za-z]+/ModelCollection/[A-Za-z0-9]+\.html$")


def area_of(url: str) -> str:
    for key, name in (("HeatTransfer", "heat transfer"), ("StructuralMechanics", "solid mechanics"), ("SolidMechanics", "solid mechanics"),
                      ("FluidDynamics", "fluid dynamics"), ("MassTransport", "mass transport"), ("Acoustics", "acoustics"),
                      ("Electromagnetics", "electromagnetics"), ("Multiphysics", "multiphysics"), ("SystemPhysics", "system physics"),
                      ("OpenCascadeLink", "geometric modeling (CAD)"), ("core-areas/fem", "FEM overview")):
        if key in url:
            return name
    return "other"


class Fetcher:
    def __init__(self, delay: float):
        self.delay, self.last, self.robots = delay, 0.0, {}

    def allowed(self, url: str) -> bool:
        host = urllib.parse.urlparse(url).netloc
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser(f"https://{host}/robots.txt")
            try:
                rp.read()
            except Exception:  # noqa: BLE001 - unreadable robots.txt: be conservative and skip the host
                rp = None
            self.robots[host] = rp
        rp = self.robots[host]
        return bool(rp and rp.can_fetch(UA, url))

    def get(self, url: str) -> str | None:
        if not self.allowed(url):
            print("ROBOTS-SKIP", url, flush=True)
            return None
        wait = self.last + self.delay - time.time()
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    return r.read().decode("utf-8", errors="replace")
            except Exception as e:  # noqa: BLE001
                print("RETRY", attempt, url, type(e).__name__, flush=True)
                time.sleep(5 * (attempt + 1))
        return None


NUM = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?(?:\*\^-?\d+|[eE]-?\d+)?)\s*;?")
QTY = re.compile(r'Quantity\[\s*(-?[\d.]+(?:\*\^-?\d+)?)\s*,\s*"([^"]+)"\s*\]')


def parse(url: str, page: str) -> dict:
    soup = BeautifulSoup(page, "html.parser")
    title = (soup.title.string or "").replace("—Wolfram Documentation", "").strip() if soup.title else ""
    code = []
    for fig in soup.select("figcaption.screen-reader-only"):
        c = fig.find("code")
        if c:
            code.append(htmllib.unescape(c.get_text()).strip())
    text = [p.get_text(" ", strip=True) for p in soup.select("p.Text, div.MCap, ul.Text li, p.MathCaption")]
    if not text:  # marketing / community pages
        text = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "h1", "h2", "h3", "li"]) if p.get_text(strip=True)]
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    links = []
    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(url, a["href"]).split("#")[0]
        if urllib.parse.urlparse(href).netloc in HOSTS:
            links.append(href)
    params = {}
    for block in code:
        for name, val in NUM.findall(block):
            params.setdefault(name, val.replace("*^", "e"))
    quantities = sorted({f"{v.replace('*^', 'e')} {u}" for block in code for v, u in QTY.findall(block)})
    return dict(url=url, title=title, area=area_of(url), headings=headings[:40], text=text, code=code,
                params=params, quantities=quantities, links=sorted(set(links)))


def crawl(max_pages: int, delay: float) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    f = Fetcher(delay)
    queue, seen, pages = [(SEED, 0)], set(), []
    while queue and len(pages) < max_pages:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[1]).strip("_")[:150]
        cached = RAW / f"{slug}.json"
        if cached.exists() and (RAW / f"{slug}.html").exists():  # reuse: do not fetch a page twice
            page, fetched = (RAW / f"{slug}.html").read_text(), json.loads(cached.read_text())["fetched_utc"]
        else:
            page, fetched = f.get(url), datetime.now(timezone.utc).isoformat(timespec="seconds")
            if page is None:
                continue
            (RAW / f"{slug}.html").write_text(page)
        rec = parse(url, page)
        rec.update(depth=depth, fetched_utc=fetched, sha256=hashlib.sha256(page.encode()).hexdigest(), slug=slug)
        (RAW / f"{slug}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        pages.append(rec)
        print(f"OK d={depth} code={len(rec['code']):3d} params={len(rec['params']):3d} {rec['title'][:70]}", flush=True)
        for link in rec["links"]:
            if link in seen:
                continue
            is_model = bool(MODEL.match(link))
            if depth == 0 and FOLLOW.match(link):
                queue.append((link, 1))
            elif depth >= 1 and is_model and depth < 3:
                queue.append((link, depth + 1))
            elif depth == 1 and "PDEModelsOverview" in link:
                queue.append((link, 2))
            elif 1 <= depth < 3 and DOCS.match(link):
                queue.append((link, depth + 1))
    manifest = [dict(url=p["url"], title=p["title"], area=p["area"], depth=p["depth"], fetched_utc=p["fetched_utc"],
                     sha256=p["sha256"], code_cells=len(p["code"]), params=p["params"], quantities=p["quantities"],
                     is_model_collection=bool(MODEL.match(p["url"]))) for p in pages]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(seed=SEED, scope="Wolfram hosts only; robots.txt honoured", pages=manifest), indent=1, ensure_ascii=False))
    models = [p for p in manifest if p["is_model_collection"]]
    print(json.dumps(dict(pages=len(pages), model_collection_pages=len(models),
                          by_area={a: sum(p["area"] == a for p in manifest) for a in sorted({p["area"] for p in manifest})})))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--max-pages", type=int, default=320)
    p.add_argument("--delay", type=float, default=1.5)
    a = p.parse_args()
    crawl(a.max_pages, a.delay)


if __name__ == "__main__":
    main()
