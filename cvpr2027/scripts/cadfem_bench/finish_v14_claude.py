"""Finish CADFEM-Bench v1.4: the balanced-suite release that release_v14.py / suites.py assembled from v1.3.

Nothing here changes a task, target, tolerance or suite assignment. Steps:
  1. install the current scorer (its version label is read from validation.json) into evaluator/;
  2. check that candidate/ holds exactly the primary suite's inputs and that no reserved/calibration CAD is model-visible;
  3. re-run the release probes (verify.py) on the primary suite;
  4. for every other suite, with that suite's own files: input hashes, leak scan, answers-only and 1.3x-scaled scoring,
     and its geometry gates (rotated/moved reference passes, 3 % larger fails);
  5. replay a sandbox denial probe through the packaged evaluator/sandbox_runner.py against this package's real path;
  6. write evaluator/verification.json, append the verification section to the card, refresh data/cadfem-bench-v1/;
  7. report.py and package.py (optionally --copy-to) with common.OUT pointed at this release.

  tmp/cq-env/bin/python scripts/cadfem_bench/finish_v14_claude.py [--copy-to /Users/ayushdebnath/SVG]
(finish_v14.py is a separate verify-and-package script written by the Codex session.)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "output/datasets/cadfem-bench-v1.4"
os.environ.update(CADFEM_BENCH_OUT=str(OUT), CADFEM_BENCH_VERSION="1.4")

import common as C          # noqa: E402  (reads the environment above)
import verify               # noqa: E402
from build import leak_scan  # noqa: E402

PY = sys.executable
SUITES = ("calibration", "reserved-public", "related-public")
VERIFY_HEADING = "## Release verification (finish_v14.py)"


def jl(p: Path) -> list:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def candidate_isolation() -> dict:
    prim = jl(C.CAND / "tasks.jsonl")
    ids = {t["task_id"] for t in prim}
    dirs = {d.name for d in (C.CAND / "tasks").iterdir() if d.is_dir()}
    assert dirs == {t["task_id"] for t in prim if t["inputs"]}, dirs ^ ids
    vis = {C.sha256(f) for f in C.CAND.rglob("*") if f.is_file()}
    hidden = {}
    for s in SUITES:
        for t in jl(C.EVAL / "suites" / s / "tasks.jsonl"):
            for i in t["inputs"]:
                if i["role"] == "cad":
                    hidden.setdefault(i["sha256"], []).append((s, t["task_id"]))
    shared = {h: v for h, v in hidden.items() if h in vis}
    # related-public shares primary CAD by definition; reserved and calibration must not
    bad = {h: v for h, v in shared.items() if any(s != "related-public" for s, _ in v)}
    assert not bad, bad
    names = {f.name for f in C.CAND.rglob("*") if f.is_file()}
    assert not names & {"references.jsonl", "evidence-manifest.jsonl", "validation.json", "registry.jsonl"}, names
    return dict(primary_tasks=len(prim), candidate_task_dirs=len(dirs), reserved_or_calibration_cad_visible=0,
                related_public_cad_shared_with_primary=len(shared))


def suite_probes() -> dict:
    sys.path.insert(0, str(C.EVAL))
    import importlib
    sc = importlib.import_module("score")
    tmp = C.ROOT / "tmp/cadfem-bench-v1.4-suite-probes"
    if tmp.exists():
        shutil.rmtree(tmp)
    out = {}
    for s in SUITES:
        d = C.EVAL / "suites" / s
        tasks, refs = jl(d / "tasks.jsonl"), jl(d / "references.jsonl")
        assert [t["task_id"] for t in tasks] == [r["task_id"] for r in refs], s
        n_in = 0
        for t in tasks:
            for i in t["inputs"]:
                p = d / "inputs" / Path(i["path"]).relative_to("tasks")
                assert p.is_file() and C.sha256(p) == i["sha256"], (s, i["path"])
                n_in += 1
        view = tmp / s / "view"              # leak_scan reads <CAND>/tasks/<id>/...; point it at this suite's inputs
        view.mkdir(parents=True)
        if (d / "inputs").exists():
            (view / "tasks").symlink_to(d / "inputs")
        cand, C.CAND = C.CAND, view
        leaks = leak_scan(tasks, refs)
        C.CAND = cand
        assert not leaks, (s, leaks[:3])

        def run(sub: Path, name: str) -> dict:
            p = subprocess.run([PY, str(C.EVAL / "score.py"), "--refs", str(d / "references.jsonl"), "--tasks", str(d / "tasks.jsonl"),
                                "--submissions", str(sub), "--run-id", "suite-probe", "--out", str(tmp / s / name)],
                               capture_output=True, text=True)
            assert p.returncode == 0, p.stderr[-1500:]
            return json.loads((tmp / s / name).read_text())
        verify.answers(refs, tmp / s / "answers")
        a = run(tmp / s / "answers", "answers.json")
        verify.answers(refs, tmp / s / "perturbed", 1.3)
        b = run(tmp / s / "perturbed", "perturbed.json")
        assert a["summary"]["all"]["numerical_passed"] == len(refs) and a["summary"]["all"]["passed"] == 0, (s, a["summary"]["all"])
        assert b["summary"]["all"]["numerical_passed"] == 0, (s, b["summary"]["all"])
        assert a["version"] == "1.4", a["version"]
        geo = {}
        for r in refs:
            chk = r.get("geometry_check")
            if not chk:
                continue
            src = d / chk["reference_step"]
            rot, big = tmp / s / f"{r['task_id']}-rot.step", tmp / s / f"{r['task_id']}-big.step"
            verify.transformed_step(src, rot, 90.0, (40.0, -15.0, 7.0))
            verify.transformed_step(src, big, 0.0, (0, 0, 0), 1.03)
            ok, g1 = sc.geometry(rot, chk, d)
            bad, g2 = sc.geometry(big, chk, d)
            assert ok and not bad, (s, r["task_id"], g1, g2)
            geo[r["task_id"]] = dict(rotated_moved=g1["relative_symmetric_difference"], scaled_103=g2.get("relative_symmetric_difference"))
        out[s] = dict(tasks=len(tasks), graded_outputs=sum(len(r["references"]) for r in refs), inputs_hash_checked=n_in, leak_scan_hits=0,
                      answers_only_numerical_passed=a["summary"]["all"]["numerical_passed"], answers_only_passed=a["summary"]["all"]["passed"],
                      perturbed_numerical_passed=b["summary"]["all"]["numerical_passed"], scorer_version=a["version"], geometry_gate_probes=geo)
    shutil.rmtree(tmp)
    return out


def sandbox_probe() -> dict:
    """Denial probe through the packaged runner, aimed at this package's real location (not the original draft's)."""
    work = C.ROOT / "tmp/cadfem-bench-v1.4-sandbox-probe"
    if work.exists():
        shutil.rmtree(work)
    sub, job = work / "submission", work / "job"
    sub.mkdir(parents=True)
    targets = dict(read_this_package=str(C.EVAL / "references.jsonl"), read_released_v13=str(C.ROOT.parent / "cadfem-bench-v1.3/evaluator/references.jsonl"),
                   read_workspace_data=str(C.DATA / "femcad-hard-v1/tasks.jsonl"), write_outside=str(work / "forbidden.txt"))
    for k in ("read_this_package", "read_released_v13", "read_workspace_data"):
        assert Path(targets[k]).is_file(), targets[k]
    (sub / "main.py").write_text(f'''import json, os, socket
from pathlib import Path
T = {json.dumps(targets)}
r = {{}}
for k in ("read_this_package", "read_released_v13", "read_workspace_data"):
    try:
        open(T[k]).read(1); r[k] = "ALLOWED"
    except PermissionError:
        r[k] = "denied"
for k, path in (("write_outside", T["write_outside"]), ("modify_input", str(Path(os.environ["CADFEM_INPUT_DIR"]) / "task.json"))):
    try:
        open(path, "a").write("x"); r[k] = "ALLOWED"
    except PermissionError:
        r[k] = "denied"
try:
    socket.create_connection(("1.1.1.1", 443), timeout=2); r["outbound_network"] = "ALLOWED"
except OSError:
    r["outbound_network"] = "denied"
import cadquery, gmsh, numpy, scipy  # the pinned CAD/FEM runtime imports inside the sandbox
r["runtime_imports"] = "ok"
Path("probe.json").write_text(json.dumps(r))
''')
    runner = C.EVAL / "sandbox_runner.py"
    rt = C.ROOT / "tmp/cq-env/bin/python"
    subprocess.run([PY, str(runner), "prepare", "--package", str(C.OUT), "--job", str(job), "--task-id", "A-CYC-Coupler-PETGCF",
                    "--submission", str(sub), "--model-id", "infrastructure-probe", "--run-id", "finish-v14-probe"], check=True, capture_output=True)
    p = subprocess.run([PY, str(runner), "replay", "--package", str(C.OUT), "--job", str(job), "--backend", "macos", "--python", str(rt),
                        "--wall-seconds", "120", "--cpu-seconds", "120", "--ram-mb", "4096"], capture_output=True, text=True)
    ex = json.loads((job / "execution.json").read_text())
    res = json.loads((job / "outputs/probe.json").read_text())
    expect = {k: "denied" for k in ("read_this_package", "read_released_v13", "read_workspace_data", "write_outside", "modify_input", "outbound_network")}
    assert p.returncode == 0 and ex["execution_verified"] and {k: res[k] for k in expect} == expect and res["runtime_imports"] == "ok", (p.stderr, ex, res)
    assert not (work / "forbidden.txt").exists()
    keep = C.EVAL / "runtime-validation/finish-v14-probe"
    if keep.exists():
        shutil.rmtree(keep)
    keep.mkdir(parents=True)
    for f in ("execution.json", "protocol.json", "profile.sb", "sandbox.log"):
        shutil.copy2(job / f, keep / f)
    shutil.copy2(job / "outputs/probe.json", keep / "probe.json")
    shutil.copy2(sub / "main.py", keep / "main.py")
    shutil.rmtree(work)
    return dict(backend=ex["sandbox"]["backend"], package=str(C.OUT), checks=res, execution_verified=ex["execution_verified"],
                elapsed_seconds=round(ex["elapsed_seconds"], 2), record="evaluator/runtime-validation/finish-v14-probe/")


def card_section(ver: dict) -> str:
    s, sb, ci = ver["suites"], ver["sandbox_probe"], ver["candidate_isolation"]
    L = [VERIFY_HEADING, "",
         f"Re-run on the finished folder (no task, target or suite changed):",
         f"- Primary suite: {ver['inputs_hash_checked']} candidate inputs hash-checked; {ver['distinct_cad_files']} distinct STEP/BREP files valid in OpenCASCADE; "
         f"{ver['evidence_files']} evidence files hash-checked; no reference value in any prompt or text input. Exact answers alone give "
         f"{ver['scorer_probes']['answers_only']['numerical_passed']} numerical passes and {ver['scorer_probes']['answers_only']['passed']} passes; "
         f"answers scaled by 1.3 give {ver['scorer_probes']['perturbed_numerical_passed']}; four malformed submissions are rejected per task; "
         f"a reviewed probe passes and fails once an artifact changes; the {len(ver['geometry_gate_probes'])} geometry gates accept the rotated, moved reference and "
         f"reject it scaled by 3 %; the independent finest-mesh values pass all {ver['converged_value_probe']['tasks']} convergence-study tasks.",
         f"- Candidate isolation: candidate/ holds exactly the {ci['primary_tasks']} primary tasks; no calibration or reserved CAD file is model-visible "
         f"(the related-public task shares {ci['related_public_cad_shared_with_primary']} CAD file with the primary suite by construction)."]
    for k, x in s.items():
        g = f"; {len(x['geometry_gate_probes'])} geometry gates pass the same probes" if x["geometry_gate_probes"] else ""
        L.append(f"- Suite `{k}`: {x['tasks']} tasks, {x['graded_outputs']} outputs, {x['inputs_hash_checked']} inputs hash-checked, no leaks; "
                 f"exact answers {x['answers_only_numerical_passed']}/{x['tasks']} numerical, {x['answers_only_passed']} passes; scaled answers "
                 f"{x['perturbed_numerical_passed']}{g}. Scorer reports version {x['scorer_version']}.")
    L.append(f"- Sandbox: the packaged `evaluator/sandbox_runner.py` replayed a denial probe against this folder ({sb['backend']}): reading this package's "
             "references, the released v1.3 references and workspace source data, writing outside the job, modifying inputs and outbound network were all "
             f"denied; the pinned CadQuery/Gmsh/NumPy/SciPy runtime imported inside the sandbox ({sb['elapsed_seconds']} s). Record: `{sb['record']}`.")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy-to")
    a = ap.parse_args()
    assert OUT.is_dir() and (C.EVAL / "suites").is_dir(), OUT
    val = json.loads((C.EVAL / "validation.json").read_text())
    assert val["version"] == "1.4", val["version"]
    shutil.copy2(HERE / "score.py", C.EVAL / "score.py")
    iso = candidate_isolation()
    print("candidate isolation:", iso, flush=True)
    ver = verify.main()
    print("primary probes ok:", ver["scorer_probes"]["answers_only"], flush=True)
    ver["suites"] = suite_probes()
    print("suites ok:", {k: (v["tasks"], v["answers_only_numerical_passed"], len(v["geometry_gate_probes"])) for k, v in ver["suites"].items()}, flush=True)
    ver["sandbox_probe"] = sandbox_probe()
    print("sandbox probe ok:", ver["sandbox_probe"]["checks"], flush=True)
    ver["candidate_isolation"] = iso
    ver["release"] = "1.4"
    C.jdump(ver, C.EVAL / "verification.json")
    card = (C.EVAL / "DATASET_CARD.md").read_text()
    card = card.split(VERIFY_HEADING)[0].rstrip() + "\n\n" + card_section(ver)
    (C.EVAL / "DATASET_CARD.md").write_text(card)
    C.META.mkdir(parents=True, exist_ok=True)
    for f in C.META.iterdir():
        f.unlink()
    shutil.copy2(C.EVAL / "DATASET_CARD.md", C.META / "README.md")
    for src, name in ((C.CAND / "tasks.jsonl", "tasks.jsonl"), (C.CAND / "README.md", "CANDIDATE_README.md"),
                      (C.EVAL / "references.jsonl", "references.jsonl"), (C.EVAL / "registry.jsonl", "registry.jsonl"),
                      (C.EVAL / "validation.json", "validation.json"), (C.EVAL / "verification.json", "verification.json"),
                      (C.EVAL / "suite-manifest.json", "suite-manifest.json"), (C.EVAL / "evaluation-protocol.json", "evaluation-protocol.json"),
                      (C.EVAL / "limitations-status.json", "limitations-status.json")):
        shutil.copy2(src, C.META / name)
    env = dict(os.environ)
    subprocess.run([PY, str(HERE / "report.py")], check=True, env=env)
    subprocess.run([PY, str(HERE / "package.py")] + (["--copy-to", a.copy_to] if a.copy_to else []), check=True, env=env)


if __name__ == "__main__":
    main()
