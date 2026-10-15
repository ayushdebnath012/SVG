# CADFEM local MLX training pilot

Completed 256-step QLoRA training on the cached Qwen2.5-Coder 1.5B 4-bit model using 128 original AgentFEM training geometries and 16 original validation geometries. Base model revision and packages are pinned in run_manifest.json. Publisher test and benchmark cases are excluded from this training dataset.

The trained adapter is adapter/adapters.safetensors. Load it with mlx_lm.load(base_model_path, adapter_path=adapter_directory). Use the source dataset system prompt and structured geometry/material/load input when generating.

validation-comparison.json gives before/after numeric validation metrics with identical single-fence normalization. The strict original outputs are retained separately in base-metrics.json and trained-metrics.json. Lower loss and correct JSON do not prove physical correctness. This is a small, within-family numerical surrogate warm-up, not a solver agent or a broad engineering benchmark result. No remote GPU jobs were modified.
