"""Upload .hf-staging to the public HF dataset repo as one commit per folder group; resumable via done.json.
LFS blobs already on the Hub are not re-sent, so a rerun after an interruption continues cheaply."""
import json, os, time
from collections import defaultdict
from pathlib import Path
from huggingface_hub import HfApi
REPO, STAGE = "Conditiondark/svg-cadfem-data", Path("/Users/ayushdebnath/SVG/.hf-staging")
DONE = Path(__file__).with_name("done.json")
done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
api = HfApi()
groups, sizes = defaultdict(list), defaultdict(int)
for p in STAGE.rglob("*"):
    if not p.is_file() or ".cache" in p.parts:
        continue
    rel = p.relative_to(STAGE).as_posix(); parts = rel.split("/")
    if rel.startswith("cvpr2027/output/datasets/"):
        key = "/".join(parts[:4])
    elif parts[0] == "cvpr2027":
        key = "/".join(parts[:3])
    elif len(parts) > 1:
        key = "/".join(parts[:2])
    else:
        key = rel
    groups[key].append(rel); sizes[key] += p.stat().st_size
todo = [k for k in sorted(groups, key=lambda k: sizes[k]) if k not in done]
print(f"{len(groups)} groups, {len(todo)} to upload, {sum(sizes[k] for k in todo) / 2**30:.2f} GiB", flush=True)
for i, key in enumerate(todo, 1):
    pattern = [key] if groups[key] == [key] else [f"{key}/**"]
    for attempt in range(1, 4):
        try:
            t0 = time.time()
            api.upload_folder(repo_id=REPO, repo_type="dataset", folder_path=str(STAGE), allow_patterns=pattern,
                              commit_message=f"Add {key}")
            done.add(key); DONE.write_text(json.dumps(sorted(done)))
            print(f"[{i}/{len(todo)}] {key}: {len(groups[key])} files, {sizes[key] / 2**20:.1f} MiB in {time.time() - t0:.0f} s", flush=True)
            break
        except Exception as e:                                    # noqa: BLE001
            print(f"[{i}/{len(todo)}] {key}: attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}", flush=True)
            time.sleep(30 * attempt)
    else:
        print(f"GIVING UP on {key} for now (rerun to retry)", flush=True)
print("UPLOAD-DONE" if all(k in done for k in groups) else "UPLOAD-INCOMPLETE", flush=True)
