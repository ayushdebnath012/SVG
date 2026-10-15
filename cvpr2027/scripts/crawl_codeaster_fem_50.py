"""Acquire published Code_Aster problems, geometry illustrations and FEM baselines.

Never executes third-party geometry/solver programs or computes reference physics.
The resulting source packs are evaluator material, not answer-free model inputs.
"""
from __future__ import annotations

import ast
import concurrent.futures
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cvpr2027/tmp/fem-expansion-50"
OUT = ROOT / "cvpr2027/data/published-fem-expansion-50"
SRC = "https://gitlab.com/codeaster/src/-/raw/"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if len(response.content) > 80_000_000:
            raise ValueError("asset exceeds acquisition size limit")
        path.write_bytes(response.content)
    return {"url": url, "path": str(path.relative_to(ROOT)),
            "sha256": sha(path), "bytes": path.stat().st_size}


def published_checks(text):
    """Parse literal VALE_CALC assertions without evaluating source expressions."""
    tree = ast.parse(text)
    checks = []
    for test in ast.walk(tree):
        if not isinstance(test, ast.Call) or not isinstance(test.func, ast.Name):
            continue
        if test.func.id not in {"TEST_RESU", "TEST_TABLE", "TEST_FONCTION"}:
            continue
        for block in ast.walk(test):
            if not isinstance(block, ast.Call):
                continue
            kw = {x.arg: x.value for x in block.keywords if x.arg}
            if "VALE_CALC" not in kw:
                continue
            try:
                value = ast.literal_eval(kw["VALE_CALC"])
            except (ValueError, TypeError):
                continue
            nums = value if isinstance(value, (list, tuple)) else [value]
            if not nums or not all(type(x) in (int, float) for x in nums):
                continue
            selectors = {}
            for key in ("NOM_CHAM", "NOM_CMP", "GROUP_NO", "GROUP_MA", "NOEUD",
                        "MAILLE", "INST", "NUME_ORDRE", "NOM_PARA", "PARA",
                        "REFERENCE", "PRECISION", "CRITERE", "TYPE_TEST"):
                if key in kw:
                    try:
                        selectors[key] = ast.literal_eval(kw[key])
                    except (ValueError, TypeError):
                        selectors[key] = {"source_expression": ast.get_source_segment(text, kw[key])}
            checks.append({"source_function": test.func.id, "line": block.lineno,
                           "end_line": block.end_lineno, "published_fem_value": value,
                           "selectors": selectors,
                           "source_excerpt": ast.get_source_segment(text, block)})
    return checks


def crawl_case(item, commit):
    case = item["case"]
    dest = CACHE / "codeaster" / case
    try:
        index_asset = acquire(item["url"], dest / "docs/index.html")
        soup = BeautifulSoup((dest / "docs/index.html").read_bytes(), "html.parser")
        article = soup.select_one("article")
        if article is None:
            raise ValueError("missing documentation article")
        links = list(dict.fromkeys(urljoin(item["url"], a["href"]).split("#")[0]
                                  for a in article.select("a[href]")
                                  if a["href"] and not a["href"].startswith("#")))
        prefix = item["url"].rsplit("/", 1)[0] + "/"
        links = [u for u in links if u.startswith(prefix) and u != item["url"]]
        # One original modelling case per physical problem, not one item per mesh.
        chosen = [u for u in links if "Probl" in u or "Solution" in u or
                  "Mod_lisation_A" in u or "Synth" in u]
        if not any("Mod_lisation_A" in u for u in chosen):
            chosen += [u for u in links if "Mod" in u][:1]
        docs, figures, result_tables = [index_asset], [], []
        for url in chosen:
            file = dest / "docs" / urlsplit(url).path.rsplit("/", 1)[-1]
            asset = acquire(url, file)
            docs.append(asset)
            body = BeautifulSoup(file.read_bytes(), "html.parser").select_one("article")
            if body is None:
                continue
            for n, table in enumerate(body.select("table")):
                rows = [[c.get_text(" ", strip=True) for c in row.select("th,td")]
                        for row in table.select("tr")]
                result_tables.append({"url": url, "table_index": n, "rows": rows})
            if "Probl" in url:
                for n, image in enumerate(body.select("img[src]")):
                    image_url = urljoin(url, image["src"])
                    suffix = Path(urlsplit(image_url).path).suffix or ".png"
                    asset = acquire(image_url, dest / "figures" / f"geometry-{n + 1:02d}{suffix}")
                    asset.update(role="publisher_geometry_illustration", caption=image.get("alt", ""))
                    figures.append(asset)
        command_file = dest / "original" / Path(item["command"]).name
        cmd = acquire(SRC + commit + "/" + item["command"], command_file)
        checks = published_checks(command_file.read_text(encoding="utf-8"))
        exp_file = dest / "original" / Path(item["export"]).name
        export = acquire(SRC + commit + "/" + item["export"], exp_file)
        dependencies, missing = [], []
        for line in exp_file.read_text().splitlines():
            fields = line.split()
            if len(fields) < 5 or fields[0] != "F" or fields[-2] != "D":
                continue
            filename = fields[2]
            if fields[1] == "comm":
                continue
            if Path(filename).is_absolute() or ".." in Path(filename).parts:
                missing.append({"export_line": line, "reason": "nonportable source path"})
                continue
            source_path = filename if filename.startswith("astest/") else "astest/" + filename
            try:
                asset = acquire(SRC + commit + "/" + source_path,
                                dest / "original" / Path(filename).name)
                asset.update(export_type=fields[1], logical_unit=fields[-1])
                dependencies.append(asset)
            except Exception as exc:
                missing.append({"export_line": line, "reason": str(exc)})
        # Some optional original CAD/preprocessor definitions are not export inputs.
        geometries = []
        for suffix in ("datg", "geo", "step", "stp"):
            legacy_names = {x["path"] for x in json.loads((CACHE / "aster-tree.txt").read_text())["tree"]}
            source_path = item["command"].rsplit(".", 1)[0] + "." + suffix
            if source_path not in legacy_names:
                continue
            try:
                geometries.append(acquire(SRC + commit + "/" + source_path,
                                          dest / "original" / Path(source_path).name))
            except requests.RequestException:
                pass
        record = {"case_id": "ASTER-" + case, "source_problem_id": case,
                  "source_title": item["title"], "source_url": item["url"],
                  "source_code_commit": commit, "solver": "Code_Aster", "requires_comsol": False,
                  "documentation": docs, "geometry_illustrations": figures,
                  "original_geometry_definitions": geometries,
                  "native_cad_files": [x for x in geometries if Path(x["path"]).suffix in {".step", ".stp"}],
                  "original_solver_input": cmd, "original_export": export,
                  "original_dependencies": dependencies, "missing_export_dependencies": missing,
                  "published_fem_checks": checks, "published_document_tables": result_tables,
                  "status": "paired_source_evaluator_pack_pending_benchmark_review",
                  "admitted_to_executable_pilot": False,
                  "review_required": ["dimensioned drawing versus geometry preview",
                                      "doc/source modelling-version correspondence",
                                      "units and physical output selector",
                                      "CAD/mesh correspondence and portable geometry import",
                                      "answer-free physics extraction for each track",
                                      "independent solver replay and convergence"]}
        (dest / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
        eligible = bool(figures and checks and not missing and
                        any(x.get("export_type") in {"mmed", "mail", "msh"} for x in dependencies))
        return {"case": case, "eligible_source_pair": eligible,
                "figures": len(figures), "fem_checks": len(checks),
                "dependencies": len(dependencies), "missing_dependencies": missing,
                "record": str((dest / "record.json").relative_to(ROOT))}
    except Exception as exc:
        return {"case": case, "eligible_source_pair": False, "error": str(exc)}


def main():
    commit = json.loads((CACHE / "aster-source-commit.json").read_text())["id"]
    available = json.loads((CACHE / "aster-selected-discovery.json").read_text())
    # Explicit physical-problem shortlist; no synthetic load variants or element duplicates.
    preferred = """SDLL14 SDLL127 SDLL149 SDLL151 SDLS102 SDLS103 SDLS104 SDLS114
    SDLS120 SDLS127 SDLS130 SDLS504 SDLS505 SDLV123 SDLV129 SDLV130 SHLL103
    SSLL103 SSLL105 SSLL404 SSLP103 SSLP311 SSLP314 SSLP315 SSLP318 SSLP321 SSLP322
    SSLP323 SSLS20 SSLS104 SSLS108 SSLS112 SSLS115 SSLS120 SSLS504 SSLS505 SSLV110
    SSLV139 SSLV154 SSLV155 SSLV311 SSLV312 SSLV314 SSLV315 SSLV319 SSLV320 SSLX102
    SSLA310 SDNL133 SDNL137 SDNL140 SDNL142 SDNV110 SSNA102 SSNA104 SSNA105 SSNA106
    SSNA107 SSNA122 SSNA303 SSNL106 SSNL114 SSNL116 SSNL117 SSNL126 SSNL503 SSNP110
    SSNP123 SSNP133 SSNP153 SSNP154 SSNP156 SSNP171 SSNP178 SSNP311 SSNP312 SSNV104
    SSNV108 SSNV128 SSNV153 SSNV166 SSNV173 SSNV182 SSNV195 SSNV501 SSNV506 SSNV509
    HPLA310 HPLP100 HPLP101 HPLP310 HPLP311 HPLV102 HPLV103 HSNV105 HSNV132 FDLV115
    FDLL200""".split()
    mapping = {x["case"]: x for x in available}
    items = [mapping[k] for k in preferred if k in mapping]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda item: crawl_case(item, commit), items):
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "crawl-audit.json").write_text(json.dumps({"source_commit": commit,
        "no_physical_generation": True, "no_source_code_executed": True,
        "results": results}, indent=2, ensure_ascii=False))
    eligible = [x for x in results if x["eligible_source_pair"]]
    print(json.dumps({"crawled": len(results), "paired_source_cases": len(eligible)}))


if __name__ == "__main__":
    main()
