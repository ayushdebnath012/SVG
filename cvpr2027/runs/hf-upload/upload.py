"""Upload the large-data staging folder (hard links) to the public HF dataset repo; resumable."""
from huggingface_hub import HfApi
api = HfApi()
repo = "Conditiondark/svg-cadfem-data"
print(api.create_repo(repo, repo_type="dataset", private=False, exist_ok=True), flush=True)
api.upload_large_folder(repo_id=repo, folder_path="/Users/ayushdebnath/SVG/.hf-staging", repo_type="dataset", num_workers=8)
print("UPLOAD-DONE", flush=True)
