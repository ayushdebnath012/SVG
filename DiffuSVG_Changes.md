# DiffuSVG Pipeline — Changes & Rationale

**File:** `DiffuSVG_Pipeline_v3.py`
**Date:** March 2026
**Context:** Pipeline was producing black/blank SVG renders, crashing on T4 GPU with OOM, and reporting false success metrics.

---

## 1. Black Rendered PNGs — Transparency Compositing Fix

**Where:** `render_svg_to_pil()` (~line 191)

**What changed:**
```python
# Before
img = Image.open(io.BytesIO(png)).convert("RGB")

# After
img = Image.open(io.BytesIO(png)).convert("RGBA")
bg = Image.new("RGB", img.size, (255, 255, 255))
bg.paste(img, mask=img.split()[3])
```

**Why:**
SVGs often have transparent backgrounds (no explicit `background-color`). When cairosvg renders them, the output PNG carries an alpha channel. Calling `.convert("RGB")` on a transparent PNG fills every transparent pixel with black — PIL's default fill for alpha removal. The fix composites the RGBA image over a white background before discarding the alpha channel, so transparent regions become white instead of black.

---

## 2. Missing White Background in Model-Generated SVGs

**Where:** `generate_svg()` (~line 930)

**What changed:**
```python
# Added after SVG extraction
if "<svg" in svg:
    svg = re.sub(
        r"(<svg[^>]*>)",
        r'\1<rect width="100%" height="100%" fill="white"/>',
        svg, count=1,
    )
```

**Why:**
vtracer-generated SVGs (used for training data) always include a white background rectangle because vtracer traces the full image including background. The fine-tuned Qwen2-VL model, however, learned to generate shape paths without a background rect — matching what a human SVG author would write. When cairosvg renders these, the canvas is transparent, and even with the compositing fix above, shapes drawn in dark colors against a transparent background look correct, but shapes with `fill="none"` or no fill at all still render as black outlines on white. Injecting the rect unconditionally after the `<svg>` opening tag ensures every model-generated SVG has the same baseline as training data.

---

## 3. Paths Without Fill Attribute Rendering Black

**Where:** `generate_svg()` (~line 940)

**What changed:**
```python
# Added after white rect injection
if not re.search(r'fill\s*=\s*["\'](?!white|#fff|#FFF)', svg):
    svg = re.sub(r'(<path\b(?![^>]*\bfill\b)[^/]*)(/>|>)', r'\1 fill="#555555"\2', svg)
```

**Why:**
The SVG specification defines the default value of `fill` as `black`. So `<path d="..."/>` with no `fill` attribute renders as a solid black shape. When the model generates an SVG with all paths missing fill attributes — which happened frequently in early training with only 24–46 samples — the entire image renders as black shapes on white, which CLIP scores near-identically to a blank image (both score ~20). The fix detects when the entire SVG has no color fill declarations and patches all unfilled paths with a neutral grey (`#555555`). The regex deliberately skips SVGs that already have at least one non-white fill, so it doesn't overwrite intentional coloring.

---

## 4. Truncated SVG — Model Hitting Token Limit Before `</svg>`

**Where:** `generate_svg()` (~line 915)

**What changed:**
```python
# Before: single regex, returns None if </svg> missing
m = re.search(r"(<svg[\s\S]*?</svg>)", resp)
svg = m.group(1) if m else resp

# After: salvage partial SVG and close it manually
m = re.search(r"(<svg[\s\S]*?</svg>)", resp)
if m:
    svg = m.group(1)
else:
    m2 = re.search(r"(<svg[^>]*>[\s\S]+)", resp)
    svg = (m2.group(1).rstrip() + "\n</svg>") if m2 else resp
```

**Why:**
With `max_new_tokens=800`, the model sometimes ran out of token budget mid-SVG, producing output like `<svg ...><path d="M 10 10 L ...` with no closing `</svg>`. The first regex `(<svg[\s\S]*?</svg>)` found no match and fell through to passing raw model output (including chat template artifacts) to cairosvg, which threw an exception → `render_svg_to_pil` returned `None` → the result was logged as a failure with CLIP=0. The salvage regex `(<svg[^>]*>[\s\S]+)` captures whatever SVG content exists and appends `</svg>`, giving cairosvg a parseable document. Even a partial SVG with a few paths is better than a null result.

---

## 5. SVGs Too Long — Path Count Cap in Vectorizer

**Where:** `Vectorizer._normalize_and_minify()` (~line 255)

**What changed:**
```python
# Added at end of _normalize_and_minify
paths = re.findall(r"<path\b[^>]*/?>", svg, flags=re.DOTALL)
if len(paths) > max_paths:
    header = re.match(r"^(<svg[^>]*>)", svg)
    hdr = header.group(1) if header else "<svg>"
    svg = hdr + " " + " ".join(paths[:max_paths]) + " </svg>"
```

**Why:**
FLUX.1-schnell (and SDXL) generate photorealistic images when given prompts like "a red apple" — full shading, reflections, gradients. vtracer traces these pixel-by-pixel, producing SVGs with 300–2000 path elements and 40,000–330,000 characters. These SVGs:
- Exceed the model's `MAX_SEQ_LEN` entirely (can't be trained on)
- Take minutes to render with cairosvg
- Are useless as training targets (model can't learn 300 paths)

vtracer outputs paths largest-to-smallest (most significant visual areas first). Keeping only the first N paths preserves the dominant shapes (background, main object silhouette, large color areas) and discards fine texture detail. On T4, the cap is set to 30 paths, which produces SVGs of ~1k–8k characters — well within the 2048-token training budget.

---

## 6. SDXL OOM → FLUX.1-schnell 4-bit NF4 on T4

**Where:** `_generate_with_local_flux()` (~line 418)

**What changed:**

Replaced SDXL local generation entirely with FLUX.1-schnell in 4-bit NF4 quantization for low-VRAM GPUs.

```python
# SDXL (removed — OOM on T4)
# StableDiffusionXLPipeline ~9-10 GB weights + activations → OOM on 14.56 GB T4

# FLUX 4-bit NF4 (new)
bnb_4bit = TBitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
)
transformer = FluxTransformer2DModel.from_pretrained(
    "black-forest-labs/FLUX.1-schnell", subfolder="transformer",
    quantization_config=bnb_4bit, torch_dtype=torch.float16,
)
text_encoder_2 = T5EncoderModel.from_pretrained(
    "black-forest-labs/FLUX.1-schnell", subfolder="text_encoder_2",
    quantization_config=bnb_4bit, torch_dtype=torch.float16,
)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    transformer=transformer, text_encoder_2=text_encoder_2,
    torch_dtype=torch.float16,
).to("cuda")
pipe.enable_attention_slicing()
```

**Why:**
SDXL (stabilityai/stable-diffusion-xl-base-1.0) requires ~9–10 GB for weights alone; with activations during a 25-step inference pass it peaks above 14.56 GB (T4's total VRAM), causing a hard OOM crash. The project requirement is that FLUX.1-schnell must be used on all hardware tiers — it produces significantly better vector-friendly images than SDXL and uses only 4 inference steps.

FLUX.1-schnell has a 12-billion parameter transformer and a 4.7-billion parameter T5 text encoder. In bfloat16 this totals ~37 GB (fits only on H100/A100-80). The solution is to quantize the two largest components independently:

| Component | Full bfloat16 | 4-bit NF4 |
|-----------|--------------|-----------|
| Transformer (12B) | ~24 GB | ~6 GB |
| T5 encoder (4.7B) | ~9 GB | ~2.4 GB |
| CLIP + VAE | ~1 GB | ~1 GB |
| Activations (512×512, 4 steps) | ~3 GB | ~3 GB |
| **Total** | **~37 GB** | **~12.4 GB** |

At ~12.4 GB this fits in T4's 14.56 GB with ~2 GB headroom. `enable_attention_slicing()` further caps activation peaks by processing attention heads one at a time.

The transformer and T5 are quantized separately (not via `FluxPipeline.from_pretrained(..., quantization_config=...)` directly) because FLUX's VAE and CLIP must stay in float16 — quantizing them causes degenerate image artifacts. Separate component loading keeps those weights at full precision.

---

## 7. Phantom Eval Successes — CLIP Threshold Fix

**Where:** `evaluate_pipeline()` (~line 1060)

**What changed:**
```python
# Before
success = True   # any render = success

# After
success = score >= 21.5
```

**Why:**
The original pipeline counted any SVG that cairosvg rendered without throwing an exception as a "success". This produced false results: a blank white SVG renders fine, and CLIP scores a blank white image against any text prompt at approximately 20.0 (baseline cosine similarity from random noise in the embedding space). The original run reported 15/20 successes, but inspection of the output files showed all 15 were blank white renders scoring between 19.8 and 20.4.

The threshold of 21.5 is slightly above the blank-image baseline (~20.0) but below what any recognizable content scores (typically 22–30+). This means a "success" requires that the rendered SVG contains enough visual information for CLIP to associate it with the prompt text — a blank white image cannot pass this threshold.

---

## 8. T4 Training Precision — bf16/fp16 Flag Fix

**Where:** `train_lora()` TrainingArguments (~line 1010)

**What changed:**
```python
# Before
bf16=True,   # always

# After
bf16=not cfg.USE_4BIT,   # H100/A100 only
fp16=cfg.USE_4BIT,       # T4: fp16 mixed precision
```

**Why:**
T4 GPUs have no native bfloat16 tensor cores — they support only float16 and float32. Setting `bf16=True` on T4 causes PyTorch to silently fall back to float32 for all operations (negating quantization savings) or, in some driver versions, throws a runtime error. Setting `fp16=True` enables proper float16 mixed precision training, which T4 supports natively via its Turing tensor cores. On A100/H100, `bf16=True` is correct because bfloat16 has better numerical stability than float16 (wider exponent range, less prone to NaN/Inf during gradient accumulation).

---

## 9. GPU Config Applied Too Late

**Where:** `main()` (~line 1244)

**What changed:**
```python
# Before: _adapt_cfg_to_gpu() called after generate_dataset()
# After:  called immediately after GPU detection, before all stages
_adapt_cfg_to_gpu()   # tune batch/rank/quantization to the actual GPU
```

**Why:**
`_adapt_cfg_to_gpu()` sets T4-specific values for `VEC_RESOLUTION`, `VEC_FILTER_SPECKLE`, `VEC_COLOR_PRECISION`, `SVG_MAX_PATHS`, `USE_4BIT`, and training hyperparameters. When it was called after Stage 1 (`generate_dataset()`), the vectorizer was already initialized with the default H100 settings (`VEC_RESOLUTION=512`, `VEC_FILTER_SPECKLE=4`, `SVG_MAX_PATHS=500`). This meant Stage 1 on T4 produced 40k–300k character SVGs — the very problem the config was meant to prevent. Moving the call to before all stages ensures the config is correct for the entire run.

---

## Summary Table

| # | Problem | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | Black PNG renders | PIL `.convert("RGB")` fills alpha=0 with black | Composite RGBA over white PIL background |
| 2 | Black model SVG renders | No background rect in generated SVGs | Inject `<rect fill="white"/>` after `<svg>` tag |
| 3 | Black paths in model SVGs | Missing `fill` attribute → SVG default = black | Patch unfilled paths with `fill="#555555"` |
| 4 | CLIP=0 from truncated SVG | Model hits token limit before `</svg>` | Salvage partial SVG + append `</svg>` |
| 5 | All SVGs "too long" | Photorealistic images → 300+ paths from vtracer | Path-count cap (30 on T4) + lower vtracer resolution |
| 6 | SDXL OOM on T4 | SDXL ~10 GB + activations > 14.56 GB | FLUX.1-schnell 4-bit NF4 (~12 GB, fits T4) |
| 7 | False success metrics | `success=True` for any render (blank white passes) | `success = CLIP_score >= 21.5` |
| 8 | Training instability on T4 | `bf16=True` unsupported on T4 | `fp16=True` on T4, `bf16=True` on A100/H100 |
| 9 | Wrong T4 settings in Stage 1 | `_adapt_cfg_to_gpu()` called after Stage 1 ran | Move call to before all pipeline stages |
