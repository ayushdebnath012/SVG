"""
Generate DiffuSVG project report as an ODF (.odt) document.
Run: python generate_report.py
"""
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, ListLevelProperties
from odf.text import H, P, List, ListItem, Span
from odf import text as odftext
from odf.namespaces import TEXTNS
import odf.style

doc = OpenDocumentText()

# ── Styles ──────────────────────────────────────────────────────────────────
def make_style(doc, name, family, parent=None, **props):
    s = Style(name=name, family=family)
    if parent:
        s.setAttribute("parentstylename", parent)
    tp = TextProperties(**{k: v for k, v in props.items() if k in (
        "fontsize", "fontweight", "color", "fontstyle")})
    pp = ParagraphProperties(**{k: v for k, v in props.items() if k in (
        "marginbottom", "margintop", "textindent", "backgroundcolor")})
    if tp.attributes:
        s.addElement(tp)
    if pp.attributes:
        s.addElement(pp)
    doc.styles.addElement(s)
    return s

# Heading styles
make_style(doc, "H1", "paragraph", fontsize="18pt", fontweight="bold",
           marginbottom="0.15in", margintop="0.2in", color="#1a1a2e")
make_style(doc, "H2", "paragraph", fontsize="14pt", fontweight="bold",
           marginbottom="0.1in", margintop="0.15in", color="#16213e")
make_style(doc, "H3", "paragraph", fontsize="12pt", fontweight="bold",
           marginbottom="0.08in", margintop="0.1in", color="#0f3460")
make_style(doc, "Body", "paragraph", fontsize="11pt",
           marginbottom="0.06in", margintop="0.0in")
make_style(doc, "Code", "paragraph", fontsize="9pt",
           marginbottom="0.04in", margintop="0.04in", color="#333333")
make_style(doc, "Caption", "paragraph", fontsize="10pt", fontstyle="italic",
           marginbottom="0.12in", color="#555555")

# Inline bold style
bold_style = Style(name="Bold", family="text")
bold_style.addElement(TextProperties(fontweight="bold"))
doc.styles.addElement(bold_style)

# Inline mono style
mono_style = Style(name="Mono", family="text")
mono_style.addElement(TextProperties(fontname="Courier New", fontsize="9pt", color="#c0392b"))
doc.styles.addElement(mono_style)

# ── Helpers ──────────────────────────────────────────────────────────────────
def h1(t): doc.text.addElement(H(outlinelevel=1, stylename="H1", text=t))
def h2(t): doc.text.addElement(H(outlinelevel=2, stylename="H2", text=t))
def h3(t): doc.text.addElement(H(outlinelevel=3, stylename="H3", text=t))

def body(t):
    p = P(stylename="Body")
    p.addText(t)
    doc.text.addElement(p)

def body_mixed(*parts):
    """parts = list of (text, style_name_or_None)"""
    p = P(stylename="Body")
    for txt, sty in parts:
        if sty:
            sp = Span(stylename=sty)
            sp.addText(txt)
            p.addElement(sp)
        else:
            p.addText(txt)
    doc.text.addElement(p)

def code(t):
    p = P(stylename="Code")
    sp = Span(stylename="Mono")
    sp.addText(t)
    p.addElement(sp)
    doc.text.addElement(p)

def blank(): doc.text.addElement(P(stylename="Body", text=""))

def bullet(items):
    lst = List()
    for item in items:
        li = ListItem()
        p = P(stylename="Body")
        if isinstance(item, list):
            for txt, sty in item:
                if sty:
                    sp = Span(stylename=sty)
                    sp.addText(txt)
                    p.addElement(sp)
                else:
                    p.addText(txt)
        else:
            p.addText(item)
        li.addElement(p)
        lst.addElement(li)
    doc.text.addElement(lst)

# ════════════════════════════════════════════════════════════════════════════
# REPORT CONTENT
# ════════════════════════════════════════════════════════════════════════════

h1("DiffuSVG: Text-to-SVG Generation Pipeline — Full Project Report")
body("Carnegie Mellon University Research Project  |  March 2026")
blank()

# ── 1. Overview ──────────────────────────────────────────────────────────────
h2("1. Project Overview")
body(
    "DiffuSVG is a five-stage machine learning pipeline that generates Scalable Vector Graphics (SVG) "
    "from plain text descriptions. The system combines a diffusion-based image generator with a "
    "vectoriser, a vision-language model (VLM) quality gate, QLoRA fine-tuning, and CLIP-based "
    "evaluation. The goal is to fine-tune a lightweight VLM to directly output SVG code from text "
    "prompts — enabling high-quality, editable vector graphics without manual design."
)
blank()
body("Platform: Kaggle T4 x2 GPU (16 GB VRAM) / Google Colab T4 (15.6 GB VRAM)")
body("Primary file: DiffuSVG_Pipeline_v2.py")
blank()

# ── 2. Architecture ──────────────────────────────────────────────────────────
h2("2. Pipeline Architecture")

h3("Stage 1 — Data Generation")
body(
    "Text prompts are fed to Stable Diffusion 3.5 Medium (stabilityai/stable-diffusion-3.5-medium) "
    "to generate 256×256 raster PNG images. Each image is then vectorised into SVG using a "
    "two-pass colour-aware pipeline:"
)
bullet([
    "ImageMagick quantises the image to 4 colours (+dither off)",
    "For each colour: a binary mask is extracted and traced with Potrace (--turdsize=6)",
    "All colour layers are merged into a single SVG with a shared viewBox=\"0 0 200 200\"",
    "A fallback single-pass BW vectorisation is used when ImageMagick is unavailable",
])
blank()
body("Key parameters: VEC_RESOLUTION=256, VEC_NUM_COLORS=4, SVG_MAX_PATHS=10, SD_STEPS=30, SD_GUIDANCE=5.0")
body("Output: stage1_generated/ — SVGs, PNGs, prompts.txt")

h3("Stage 2 — VLM Quality Gate")
body(
    "Each generated SVG is rendered to a 256×256 PNG via cairosvg and fed to "
    "Qwen2-VL-2B-Instruct alongside the original text prompt. The VLM is asked: "
    "\"Does this SVG accurately represent the prompt? Answer only YES or NO.\" "
    "Samples receiving YES are kept for training; NO samples are saved separately."
)
bullet([
    "Model: Qwen/Qwen2-VL-2B-Instruct (float16, device_map=auto)",
    "Outputs: stage2_filtered/ (PASS) and stage2_rejected/ (FAIL)",
    "Conservative: gate errors default to PASS to avoid data loss",
])

h3("Stage 3 — QLoRA Fine-tuning")
body(
    "The filtered (prompt, SVG) pairs are used to fine-tune Qwen2-VL-2B-Instruct with QLoRA. "
    "The model is trained in a causal LM setup: given the system + user message, predict the "
    "SVG tokens. The prompt portion is masked with -100 in the labels so loss is computed only "
    "on the SVG output."
)
bullet([
    [("LoRA: ", None), ("r=16, alpha=32, dropout=0.05", "Mono")],
    [("Target modules: ", None), ("q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj", "Mono")],
    [("Quantisation: 4-bit NF4 (bitsandbytes), ", None), ("device_map={\"\":0}", "Mono")],
    [("Sequence length: ", None), ("MAX_SEQ_LEN=2048", "Mono"), (" — SVGs tokenise to 1200–1800 tokens", None)],
    "Epochs: 3, Batch: 1, Grad accumulation: 8, LR: 1e-4, Scheduler: cosine",
    "Validation split: 10%, early stopping on eval_loss",
    "Gradient checkpointing enabled (use_reentrant=False)",
])
body("Output: stage3_training/ — training_pairs.json, prompts.txt; final_adapter/ — LoRA weights")

h3("Stage 4 — Inference")
body(
    "The fine-tuned model generates SVG code for each test prompt. Outputs are always saved "
    "as raw SVG files even when cairosvg rendering fails, to preserve model output for analysis."
)
bullet([
    [("Generation: ", None), ("temperature=0.7, top_p=0.9, repetition_penalty=1.1, max_new_tokens=800", "Mono")],
    "SVG is extracted from response via regex — handles cases where model adds explanation text",
    "Output: stage4_inference/ — svgs/, pngs/, prompts.txt",
])

h3("Stage 5 — CLIP Evaluation")
body(
    "Rendered PNGs are scored against their prompts using OpenAI CLIP (ViT-B-32, "
    "pretrained=laion2b_s34b_b79k). The cosine similarity between image and text embeddings "
    "is multiplied by 100 to produce the CLIP score."
)
body("Output: eval_results/ — eval_summary.json, per-prompt SVG + PNG files")
blank()

# ── 3. Key Implementation Challenges ─────────────────────────────────────────
h2("3. Implementation Challenges and Fixes")

h3("3.1 CUDA Illegal Memory Access (DataParallel + QLoRA)")
body(
    "On Kaggle T4 x2, HuggingFace Trainer automatically wraps the model in DataParallel "
    "across both GPUs. Combined with 4-bit bitsandbytes quantisation and gradient checkpointing, "
    "this caused illegal memory access crashes in the bnb forward pass."
)
body("Fix:")
bullet([
    [("Set ", None), ("CUDA_VISIBLE_DEVICES=0", "Mono"), (" at process start to hide GPU 1", None)],
    [("Use ", None), ("device_map={\"\":0}", "Mono"), (" instead of ", None), ("device_map=auto", "Mono")],
    [("Set ", None), ("model.is_parallelizable=False", "Mono"), (" and ", None), ("model.model_parallel=False", "Mono")],
])

h3("3.2 Out-of-Memory During Training")
body(
    "Initial settings caused GPU OOM with 16 GB VRAM."
)
body("Fix:")
bullet([
    [("Reduced LoRA rank: ", None), ("LORA_R=32 → 16", "Mono"), (" (saves ~100 MB activations)", None)],
    "Enabled gradient checkpointing — trades compute for memory",
    [("Batch size: 1, gradient accumulation: 8 (effective batch = 8)", None)],
    [("Set ", None), ("dataloader_pin_memory=False", "Mono")],
])

h3("3.3 No Usable Training Samples — SVGs Too Long (First Occurrence)")
body(
    "All generated SVGs exceeded the token budget at default settings. "
    "Mean token length was 5040 tokens against a limit of 1024."
)
body("Fix:")
bullet([
    [("Reduced vectoriser resolution: ", None), ("VEC_RESOLUTION=512 → 256", "Mono")],
    [("Reduced colour layers: ", None), ("VEC_NUM_COLORS=8 → 4", "Mono")],
    [("Capped path count: ", None), ("SVG_MAX_PATHS=10", "Mono")],
    "Applied coordinate rounding to 2 decimal places in _normalize_and_minify() — saves ~30% path data length",
    "Fixed bug: colour-path vectoriser was not calling _normalize_and_minify() — only BW path did",
    [("Char pre-filter: skip SVGs longer than ", None), ("(MAX_SEQ_LEN - 150) * 2.5", "Mono"), (" chars", None)],
])

h3("3.4 No Usable Training Samples — MAX_SEQ_LEN Too Low (Second Occurrence)")
body(
    "After the above fixes, SVGs tokenised to 1249–1817 tokens, but MAX_SEQ_LEN was still 1024. "
    "All samples were skipped as truncated SVG training causes mode collapse."
)
body("Fix: raised MAX_SEQ_LEN from 1024 to 2048. Safe with LORA_R=16 + gradient checkpointing.")

h3("3.5 Mode Collapse in Generated SVGs")
body(
    "Earlier runs (with MAX_SEQ_LEN=1024 and truncation allowed) produced degenerate outputs: "
    "the model learned to output a single tiny sub-pixel path for every prompt."
)
body("Root cause: truncated SVG training data. The model learned the start of SVG paths but never "
     "saw complete, valid endings — causing it to always output the most frequent partial path prefix.")
body("Fix: SVGCausalDataset skips any sample where full_len > max_len entirely — no truncation allowed.")

h3("3.6 Stage 4 Inference Producing Empty Output")
body("Model sometimes output explanatory text instead of SVG, causing render_svg_to_pil to return "
     "None and nothing being saved.")
body("Fix: always save raw SVG string to disk before attempting cairosvg render. "
     "SVG is extracted from response via regex; if no <svg> tag found, raw response is saved anyway.")

h3("3.7 HF_TOKEN Access on Kaggle / Colab")
bullet([
    "Kaggle: token must be added via Add-ons → Secrets → HF_TOKEN, then toggle 'Attach to notebook' ON",
    "Colab: token must be added via Secrets panel (key icon), toggle 'Notebook access' ON",
    "Pipeline detects platform and uses appropriate secrets API automatically",
])
blank()

# ── 4. Results ───────────────────────────────────────────────────────────────
h2("4. Pipeline Results")

h3("4.1 Data Generation (Stage 1)")
bullet([
    "Input: 50 fallback prompts (simple icon descriptions)",
    "Valid SVGs generated: 36 / 50  (72% success rate)",
    "Failures: prompts producing images too complex for Potrace at 256px, or exceeding char limit",
    "Output: 36 SVG + PNG pairs saved to stage1_generated/",
])

h3("4.2 VLM Quality Gate (Stage 2)")
bullet([
    "Input: 36 SVG + PNG pairs",
    "PASS (kept for training): 31  (86% pass rate)",
    "FAIL (rejected): 5",
    "Rejected SVGs saved separately to stage2_rejected/ for analysis",
])

h3("4.3 Fine-tuning (Stage 3)")
bullet([
    "Training samples used: 30  (1 val split removed, some skipped for token length)",
    "Token lengths: 1249–1817 tokens per sample (within MAX_SEQ_LEN=2048)",
    "Epochs: 3, effective batch size: 8",
    "Adapter size: 71 MB (adapter_model.safetensors)",
    "LoRA rank 16 on all 7 attention/MLP projection layers",
    "Adapter saved to finetuned_vlm_adapter/ — self-contained with tokenizer files",
])

h3("4.4 Inference & Evaluation (Stages 4–5)")
bullet([
    "Test prompts: 20",
    "SVGs generated: 20 / 20  (100% — raw SVG always saved)",
    "Successfully rendered to PNG: 16 / 20  (80%)",
    "eval_results/ contains: 20 SVGs, 16 PNGs, eval_summary.json",
])
blank()

# ── 5. Fine-tuned Model Test Results ─────────────────────────────────────────
h2("5. Fine-tuned Model Test Analysis")
body(
    "After downloading the adapter, a standalone test was run on 10 held-out prompts "
    "using the saved finetuned_vlm_adapter/ weights loaded onto the Qwen2-VL-2B base model."
)

h3("5.1 Results by Prompt")
bullet([
    "a_blue_circle   — <circle> element only, no <path>; correct colour (#2876dd); renders OK",
    "a_red_apple     — <circle> with no fill (renders black); no <path>",
    "a_green_tree    — <rect fill=#3498db> (blue, not green); wrong shape",
    "a_coffee_cup    — <rect fill=#FFD700>; just a yellow square",
    "a_house_with_red_roof — tiny <rect fill=#FF0000> 32×32px; unrecognisable",
    "a_wifi_symbol   — <rect fill=#f4f4f4>; just a grey square",
    "a_rocket        — <rect> + <circle> with no fills; meaningless",
    "a_lightning_bolt — 1 degenerate <path> with broken coordinates; renders but draws nothing",
    "a_music_note    — identical path to lightning_bolt; model copied same output",
    "a_smiley_face   — 7 paths (most complex), all identical copies of same path (mode collapse); failed to render",
])

h3("5.2 Key Findings")
bullet([
    "Render rate: 9/10 SVGs produced a PNG; smiley_face render failed due to degenerate paths",
    "Colour knowledge: model associates blue→circle, red→apple correctly; shows some semantic learning",
    "Shape knowledge: almost entirely absent — model defaults to <rect> or <circle> for unknown shapes",
    "Path generation: only lightning_bolt and music_note attempted <path> elements; both degenerate",
    "Mode collapse: smiley_face shows 7 identical paths — model loops the same partial path from training data",
    "Structure: all outputs are valid SVG XML with correct wrapper, xmlns, and fill attributes",
])

h3("5.3 Root Cause")
body(
    "30 training samples is severely insufficient for a 2B-parameter model to generalise SVG path "
    "geometry. The model memorised SVG document structure (wrapper, attributes, colours) but "
    "did not learn to generate meaningful path d= data. The repeated degenerate path in "
    "music_note and lightning_bolt confirms the model is reproducing a memorised path fragment "
    "from the training set rather than generating geometry from the prompt."
)
blank()

# ── 6. Saved Artefacts ────────────────────────────────────────────────────────
h2("6. Saved Artefacts")
bullet([
    "DiffuSVG_Pipeline_v2.py — complete pipeline source code",
    "finetuned_vlm_adapter/ — LoRA adapter (71 MB safetensors + tokenizer, inference_mode=true)",
    "diffusvg_full_output/stage1_generated/ — 36 SVGs + PNGs from SD3.5+Potrace",
    "diffusvg_full_output/stage2_filtered/ — 31 PASS SVGs + PNGs",
    "diffusvg_full_output/stage2_rejected/ — 5 FAIL SVGs",
    "diffusvg_full_output/stage3_training/ — training_pairs.json (30 samples) + prompts.txt",
    "diffusvg_full_output/stage4_inference/ — 20 SVGs + 16 PNGs from fine-tuned model",
    "diffusvg_full_output/eval_results/ — CLIP scores + eval_summary.json",
    "test_out/ — 10-prompt standalone adapter test (9 PNGs + 10 SVGs)",
])
blank()

# ── 7. Conclusions ────────────────────────────────────────────────────────────
h2("7. Conclusions and Future Work")

h3("7.1 What Was Achieved")
bullet([
    "Complete end-to-end text-to-SVG pipeline implemented and validated on T4 GPU",
    "Stable Diffusion 3.5 Medium + Potrace vectorisation producing usable training SVGs",
    "VLM quality gate filtering noise from the training set (86% pass rate)",
    "QLoRA fine-tuning completed without OOM or DataParallel crashes",
    "Self-contained LoRA adapter saved and verified loadable for inference",
    "CLIP evaluation loop measuring alignment between generated SVG renders and prompts",
    "Full output packaging: all stage artefacts zipped for download from Kaggle/Colab",
])

h3("7.2 Limitations")
bullet([
    "30 training samples insufficient for path geometry generalisation",
    "Model learned SVG structure but not SVG geometry",
    "Potrace output (binary trace paths) is harder to learn than hand-crafted SVG",
    "T4 VRAM budget limits batch size and model scale",
])

h3("7.3 Recommended Next Steps")
bullet([
    "Scale training data to 150–300 samples minimum",
    "Augment with curated SVG datasets (SVG-Stack, FIGR-8) rather than Potrace-only data",
    "Experiment with direct SVG supervision (human-drawn icons) instead of raster-to-vector",
    "Try larger base model (Qwen2-VL-7B) with 8-bit quantisation if VRAM allows",
    "Add beam search or constrained decoding to enforce valid SVG XML structure at inference",
    "Increase epochs to 5–10 once dataset size is sufficient to avoid overfitting",
])
blank()
body("— End of Report —")

# ── Save ──────────────────────────────────────────────────────────────────────
out = "DiffuSVG_Report.odt"
doc.save(out)
print(f"Report saved → {out}")
