"""Polite breadth-first crawl of https://mfem.org/ (same host only) for FEM problem descriptions.

Saves each page's raw HTML and extracted text, headings, code blocks (sample runs such as `ex2 -m ../data/beam-tet.mesh`)
and same-site links to tmp/mfem-scrape/ (git-ignored), and a provenance manifest (URL, title, hash, date, code-block
count, mesh files mentioned) to data/femcad-hard-v1/mfem-sources.json. mfem.org serves no robots.txt; requests are still
spaced and capped. URLs are normalised (https, no query or fragment, directory pages with a trailing slash) so filter
views and http/https twins are fetched once, and pages already on disk are reused.

  python scripts/scrape_mfem_site.py [--max-pages 500] [--delay 1.0]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "tmp/mfem-scrape"
MANIFEST = ROOT / "data/femcad-hard-v1/mfem-sources.json"
SEED = "https://mfem.org/"
UA = "Mozilla/5.0 (compatible; academic FEM-benchmark research; contact ayushdebnath0123@gmail.com)"
SKIP_EXT = re.compile(r"\.(png|jpe?g|gif|svg|pdf|zip|gz|tgz|mp4|webm|ico|css|js|xml|txt|mesh|vtk|bib)$", re.I)
MESH = re.compile(r"[\w./-]*\.(?:mesh|msh|vtk|mfem|gen|cdf)\b")


def get(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                if "text/html" not in r.headers.get("Content-Type", ""):
                    return None
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print("RETRY", attempt, url, type(e).__name__, flush=True)
            time.sleep(4 * (attempt + 1))
    return None


def norm(href: str) -> str:
    u = urllib.parse.urlparse(href)
    path = u.path or "/"
    if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return f"https://{u.netloc}{path}"


def parse(url: str, page: str) -> dict:
    soup = BeautifulSoup(page, "html.parser")
    main = soup.find("div", {"role": "main"}) or soup.find("main") or soup.body or soup
    title = soup.title.get_text(strip=True) if soup.title else ""
    headings = [h.get_text(" ", strip=True) for h in main.find_all(["h1", "h2", "h3", "h4"])]
    code = [c.get_text("\n", strip=True) for c in main.find_all(["pre", "code"]) if c.get_text(strip=True)]
    text = [p.get_text(" ", strip=True) for p in main.find_all(["p", "li", "td"]) if p.get_text(strip=True)]
    links = []
    for a in soup.find_all("a", href=True):
        href = norm(urllib.parse.urljoin(url, a["href"]))
        if urllib.parse.urlparse(href).netloc == "mfem.org" and not SKIP_EXT.search(href):
            links.append(href)
    meshes = sorted({m for block in code + text for m in MESH.findall(block)})
    return dict(url=url, title=title, headings=headings, text=text, code=code, meshes=meshes, links=sorted(set(links)))


def crawl(max_pages: int, delay: float) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    queue, seen, pages, last = [SEED], set(), [], 0.0
    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[1]).strip("_")[:150] or "root"
        if (RAW / f"{slug}.html").exists() and (RAW / f"{slug}.json").exists():  # reuse: do not fetch a page twice
            page, fetched = (RAW / f"{slug}.html").read_text(), json.loads((RAW / f"{slug}.json").read_text())["fetched_utc"]
        else:
            wait = last + delay - time.time()
            if wait > 0:
                time.sleep(wait)
            last = time.time()
            page, fetched = get(url), datetime.now(timezone.utc).isoformat(timespec="seconds")
            if page is None:
                continue
            (RAW / f"{slug}.html").write_text(page)
        rec = parse(url, page)
        rec.update(fetched_utc=fetched, sha256=hashlib.sha256(page.encode()).hexdigest(), slug=slug)
        (RAW / f"{slug}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        pages.append(rec)
        print(f"OK code={len(rec['code']):3d} meshes={len(rec['meshes']):2d} {rec['title'][:60]} {url}", flush=True)
        queue.extend(l for l in rec["links"] if l not in seen)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(dict(seed=SEED, scope="mfem.org only (no robots.txt served); spaced, capped crawl",
        pages=[dict(url=p["url"], title=p["title"], fetched_utc=p["fetched_utc"], sha256=p["sha256"],
                    code_blocks=len(p["code"]), meshes=p["meshes"]) for p in pages]), indent=1, ensure_ascii=False))
    print(json.dumps(dict(pages=len(pages), with_meshes=sum(bool(p["meshes"]) for p in pages))))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--max-pages", type=int, default=500)
    p.add_argument("--delay", type=float, default=1.0)
    a = p.parse_args()
    crawl(a.max_pages, a.delay)


if __name__ == "__main__":
    main()
