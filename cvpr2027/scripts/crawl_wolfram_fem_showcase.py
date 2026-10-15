"""Crawl the category showcase diagrams of https://www.wolfram.com/language/core-areas/fem/ (one carousel per category).

Each <section> of the page has an <h2> category title and carousel slides <img src="Files/index.en/...png"> (550 x 300,
with the caption drawn into the image). The page repeats each carousel for small and large screens, so images are
de-duplicated by URL. Images are downloaded politely into git-ignored tmp/femcad-figures/fem-page/ and listed in
data/femcad-hard-v1/fem-showcase.json by category (URL, local path, order); they stay Wolfram's and are referenced by URL.

  python scripts/crawl_wolfram_fem_showcase.py
"""
from __future__ import annotations

import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE = "https://www.wolfram.com/language/core-areas/fem/"
OUT = ROOT / "tmp/femcad-figures/fem-page"
UA = "Mozilla/5.0 (compatible; academic FEM-benchmark research; contact ayushdebnath0123@gmail.com)"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    soup = BeautifulSoup(get(PAGE).decode("utf-8", errors="replace"), "html.parser")
    showcase, seen = {}, set()
    for sec in soup.find_all("section"):
        h2 = sec.find("h2")
        if not h2:
            continue
        cat = h2.get_text(" ", strip=True)
        imgs = []
        for img in sec.find_all("img"):
            src = urllib.parse.urljoin(PAGE, img.get("src") or "")
            if "Files/index.en/" not in src or src in seen:
                continue
            seen.add(src)
            dest = OUT / Path(urllib.parse.urlparse(src).path).name
            if not dest.exists():
                dest.write_bytes(get(src))
                time.sleep(0.5)
            imgs.append(dict(url=src, local=str(dest.relative_to(ROOT)), width=int(img.get("width") or 0),
                             height=int(img.get("height") or 0), links=[a.get_text(" ", strip=True) for a in sec.find_all("a")
                                                                         if a.get("href", "").startswith("https://reference")][:6]))
        if imgs:
            showcase[cat] = imgs
            print(f"{cat:22s} {len(imgs)} images", flush=True)
    (ROOT / "data/femcad-hard-v1/fem-showcase.json").write_text(json.dumps(dict(
        page=PAGE, note="Category showcase diagrams of Wolfram's FEM page; Wolfram's images, referenced by URL; local copies "
                        "in git-ignored tmp/femcad-figures/fem-page/.", categories=showcase), indent=1, ensure_ascii=False))
    print(json.dumps(dict(categories=len(showcase), images=sum(len(v) for v in showcase.values()))))


if __name__ == "__main__":
    main()
