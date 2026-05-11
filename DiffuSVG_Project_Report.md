# DiffuSVG Updated Project Report

**Date:** May 1, 2026  
**Project:** Text-to-SVG generation with diffusion-generated data, QLoRA fine-tuning, and render-based evaluation

---

## Executive Summary

DiffuSVG is a text-to-SVG generation pipeline. It first uses a diffusion model to create raster images from text prompts, vectorizes those images into SVGs, filters the pairs, then fine-tunes a VLM/LLM adapter so inference can go directly from text prompt to SVG code.

The trained model is **not currently overfitting**, based on the available loss curves and generation metrics, but it is at **high risk** because the current effective training set is extremely small.

Key evidence:

- Eval loss decreased from **1.089 to 0.805** across 5 epochs.
- Eval loss is slightly lower than train loss, with an eval/train ratio of about **0.96**.
- The seen-vs-unseen CLIP gap is only **+1.87**, which does not indicate prompt memorization.
- Broader evaluation produced **46/50 valid SVGs**, **45 unique SVGs among 46 valid outputs**, and no obvious mode collapse.
- The main risk is scale: **20 samples for roughly 40M LoRA parameters**, giving a data-to-parameter ratio of about **5e-7**.

Because epoch 5 showed only a **1.2% marginal improvement**, additional training on the same tiny dataset is likely to push the model into memorization. The training defaults have therefore been changed to the safer configuration:

- epochs: **5 -> 3**
- LoRA rank: **16 -> 4**
- LoRA alpha: **32 -> 16**
- LoRA dropout: **0.05 -> 0.15**
- early stopping: enabled when validation data exists

---

## Current Pipeline

```text
Text prompt
  -> Diffusion model raster generation
  -> SVG vectorization with vtracer or Potrace
  -> VLM quality gate
  -> prompt/SVG training pair
  -> QLoRA fine-tuning
  -> direct text-to-SVG inference
  -> render-based evaluation with CLIP, DINO, validity, uniqueness
```

The diffusion model is not the final deployed model. It acts as a **data generator / teacher** that creates visual examples from prompts. The final model is trained to write SVG code directly.

---

## Evaluation Results

### Local 20-Prompt Evaluation

The local evaluation artifact at `DiffuSVG-20260325T073905Z-3-001/DiffuSVG/eval_summary.json` reports:

| Metric | Value |
|---|---:|
| Prompts | 20 |
| Successes | 20 |
| CLIP mean | 28.254 |
| CLIP median | 26.851 |
| CLIP std | 5.414 |

This indicates that the fine-tuned model can generate valid prompt-aligned outputs for the simple icon set. It should not be interpreted as broad generalization because the prompt set is small and icon-like.

### Broader 50-Prompt Evaluation

The broader `results.json` artifact reports:

| Metric | Value |
|---|---:|
| Prompts | 50 |
| Valid outputs | 46 |
| Validity | 92.0% |
| Valid-output CLIP mean | 24.913 |
| Valid-output DINO mean | 0.450 |
| Unique valid SVGs | 45/46 |
| Average elements | 3.5 |

If the four extraction failures are included as zero-score outputs, the mean CLIP score becomes about **22.92**. This distinction matters: validity and extraction reliability should be tracked separately from semantic quality.

---

## Overfitting Assessment

### Verdict

The current run does **not** show overfitting yet, but the system is operating near the limit of what the small dataset can support.

### Good Signs

| Signal | Interpretation |
|---|---|
| Eval loss decreased monotonically | The model continued improving on held-out examples. |
| Eval loss below train loss | No clear train-only memorization pattern yet. |
| Small CLIP seen/unseen gap | Outputs are not collapsing only to seen prompt templates. |
| 45 unique SVGs among 46 valid outputs | No mode collapse in the broader evaluation. |

### Risk Signs

| Signal | Interpretation |
|---|---|
| 20 training examples | Too small for stable adapter learning. |
| Roughly 40M trainable LoRA parameters | Adapter capacity is far larger than the dataset. |
| Epoch 5 marginal gain only 1.2% | The run is approaching its learning ceiling. |
| Simple geometry bias | Many outputs use generic circles, rectangles, and polygons even when CLIP passes. |

### Recommendation

Do not continue training the same adapter for more epochs on the 20-sample set. The next training run should use **500-2000+ examples**, lower adapter capacity, stronger dropout, and early stopping.

---

## Perplexity Experiment

Perplexity should be measured separately on:

1. **Generated training set**: the local DiffuSVG-generated prompt/SVG pairs.
2. **Generated held-out set**: prompts from the same generation pipeline but excluded from training.
3. **Kaggle/curated dataset**: external prompt/SVG examples from the Kaggle SVG dataset.
4. **OOD creative benchmark prompts**: Gally/Simon-style unusual compositions.

I added `evaluate_perplexity.py` for this. It masks the prompt tokens and computes perplexity only over SVG output tokens:

```bash
python evaluate_perplexity.py \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --adapter /kaggle/working/qwen2vl_svg_lora/final_adapter \
  --dataset generated=/kaggle/input/diffusvg/training_pairs.json \
  --dataset kaggle=/kaggle/input/svg-dataset-for-generative-llm/data.jsonl \
  --output-json perplexity_report.json
```

Interpretation:

| Pattern | Meaning |
|---|---|
| Train PPL low, generated-heldout PPL close | Healthy in-domain learning. |
| Train PPL low, Kaggle PPL much higher | Overfitting to local generated style. |
| Train PPL low, OOD PPL extreme | Weak compositional generalization. |
| All PPL high | Undertrained or prompt/template mismatch. |
| Train PPL keeps falling while eval PPL rises | Classic overfitting. |

The Kaggle dataset linked in the notes is useful because it combines text descriptions with SVG code and includes sources such as Visual Scene Instructions, StarVector text2svg-stack-scale data, and DeepSeek SVG examples. It is a better expansion source than repeatedly training on the same 20 generated samples.

---

## RLRF Expansion

The RLRF paper, **Rendering-Aware Reinforcement Learning for Vector Graphics Generation**, addresses the exact weakness in SVG language modeling: supervised fine-tuning learns token sequences, but it does not directly learn whether the rendered SVG actually looks correct.

### Core Idea

RLRF means **Reinforcement Learning from Rendering Feedback**. The model samples SVG rollouts, renders them to images, compares those images with the target, and receives a reward. This lets the model improve from visual feedback even though SVG token sampling and rendering are not differentiable.

### Two-Stage Training

1. **SVG-SFT**

   The model is first trained with normal supervised fine-tuning on prompt/image-to-SVG pairs. This teaches syntax, structure, and common primitives.

2. **RLRF**

   The SFT model becomes the policy. For each condition, it samples multiple SVG outputs, renders them, scores them, and updates the model with GRPO-style reinforcement learning while staying close to the SFT model through KL regularization.

### Reward Components

The paper uses a composite reward:

| Reward | Purpose |
|---|---|
| Pixel reconstruction / L2 | Measures low-level image fidelity. |
| Edge-aware reward | Helps align shape boundaries and contours. |
| DreamSim / CLIP / DINO-style semantic reward | Measures high-level perceptual similarity. |
| Code efficiency reward | Penalizes unnecessarily long or redundant SVG code. |
| VLM-as-judge for Text2SVG | Scores semantic accuracy, resemblance, and aesthetics when CLIP is weak. |

One important note from the paper: CLIP can be weak for abstract SVG-style images because CLIP was trained mostly on natural image distributions. For Text2SVG, a VLM judge can provide a better reward than CLIP alone.

### How DiffuSVG Can Use RLRF

A practical version for this project would be:

1. Start from the current SFT/QLoRA model.
2. For each prompt, sample 4-8 SVG candidates.
3. Render each SVG with CairoSVG.
4. Score each candidate using:
   - SVG validity: parses and renders
   - CLIP text-image score
   - DINO or SSIM if a target raster exists
   - path/element count penalty
   - byte-size penalty
   - optional Qwen2-VL judge score
5. Use the reward either for reranking first, then later for GRPO training.

The safer near-term step is **RLRF-lite reranking**. Full GRPO should wait until the dataset is larger and evaluation is stable.

---

## How to Explain the Diffusion Model

In DiffuSVG, the diffusion model is best explained as the visual-data engine:

1. Start with random noise.
2. Condition the denoising process on the text prompt.
3. Gradually remove noise until the raster image matches the prompt.
4. Convert the raster to SVG using vector tracing.
5. Use the resulting prompt/SVG pair to train the direct SVG generator.

For the report or presentation, show it as:

```text
Prompt: "a red apple"
  -> diffusion raster image
  -> vectorized SVG
  -> training pair
  -> fine-tuned model learns prompt -> SVG directly
```

The key point: diffusion produces pixels well, but SVG requires structured code. DiffuSVG uses diffusion to bootstrap SVG supervision, then trains an autoregressive model to produce the code.

---

## Dataset Expansion Plan

The next dataset should mix local generated examples and curated external examples:

| Source | Role |
|---|---|
| Local DiffuSVG generated samples | Matches the project style and 200x200 icon format. |
| Kaggle SVG dataset | Adds scale, vocabulary, and external variation. |
| StarVector/text2svg-style samples | Adds large-scale text-to-SVG patterns. |
| Failure-mined prompts | Targets prompts where CLIP/DINO/validity failed. |
| Gally/Simon creative prompts | Tests compositional SVG ability outside icon-like prompts. |

Recommended split:

- 70% train
- 10% validation
- 20% test
- Deduplicate by normalized SVG hash and near-duplicate prompt hash.
- Keep a separate OOD prompt suite that is never used in training.

Target size:

- Minimum useful next run: **500 examples**
- Stronger run: **2,000+ examples**
- RLRF/GRPO-ready run: **10,000+ examples**

---

## External Context

### OmniSVG

OmniSVG is a NeurIPS 2025 SVG generation framework using Qwen-VL plus a specialized SVG tokenizer. It introduces MMSVG-2M, a multimodal SVG dataset with icon, illustration, and character subsets. Its main lesson for DiffuSVG is that SVG generation improves when the model sees large-scale structured SVG tokens rather than raw XML alone.

### Gally / Simon SVG Benchmark

The Gally benchmark extends Simon Willison's pelican-style SVG test with 30 creative prompts across frontier models. It is valuable for qualitative out-of-distribution evaluation because prompts like unusual objects performing unusual actions stress compositional reasoning, not only icon memorization.

### Kaggle Text2SVG Notebook

The Qwen2.5-Coder Text2SVG notebook is useful as a baseline direction: a code-specialized language model can be fine-tuned to emit SVG directly. DiffuSVG differs by using diffusion/vectorization to bootstrap data and VLM/rendering metrics to evaluate visual alignment.

---

## Completed Code Changes

- Added `evaluate_perplexity.py` for separate dataset perplexity measurement.
- Updated `DiffuSVG_Pipeline_v6.py` anti-overfitting defaults:
  - `EPOCHS = 3`
  - `LORA_R = 4`
  - `LORA_ALPHA = 16`
  - `LORA_DROPOUT = 0.15`
  - early stopping when validation exists
- Updated `DiffuSVG_Kaggle.py` with the same defaults and early stopping.

---

## Next Steps

1. Build a 500-2000 example dataset from local generated data plus the Kaggle/curated SVG dataset.
2. Run `evaluate_perplexity.py` on generated, Kaggle, and held-out splits before and after training.
3. Retrain with the safer LoRA defaults now in the code.
4. Evaluate validity, uniqueness, CLIP, DINO, and human visual quality separately.
5. Add RLRF-lite reranking before attempting full GRPO.

---

## References

- Kaggle dataset: https://www.kaggle.com/datasets/kaushikyh/svg-dataset-for-generative-llm
- Kaggle Qwen2.5-Coder notebook: https://www.kaggle.com/code/gumballnguyen/fine-turning-model-qwen2-5-coder-text2svg
- RLRF paper: https://arxiv.org/abs/2505.20793
- RLRF project page: https://starvector.github.io/rlrf/
- OmniSVG: https://omnisvg.github.io/
- Gally SVG benchmark: https://gally.net/temp/20251107pelican-alternatives/index.html
- Simon Willison SVG benchmark note: https://simonwillison.net/2025/Nov/25/llm-svg-generation-benchmark/
