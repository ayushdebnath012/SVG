"""
Generate a text-only SVG SFT dataset using Qwen2.5-VL-7B-Instruct as teacher.

Uses the base model to generate SVG drafts for diverse prompts, keeps only
renderable/colorful ones, and saves in LlamaFactory sharegpt format.

Prompt difficulty:
  Medium-to-hard scene prompts work best for the base model — scenes with a
  clear spatial structure (sky / ground / main object) in 3-6 elements.
  Simple single objects (apple, star) give trivial SVGs; very hard combos
  (octopus + pipe organ) give unrecognisable blobs. Both extremes hurt SFT.

  By default loads prompts from --prompt-file (../prompts.txt), which contains
  ~150 curated medium-hard landscape/scene prompts. Falls back to SCENE_PROMPTS.

Run:
    python 00_create_sft_data.py --n-samples 5000
    python 00_create_sft_data.py --n-samples 2000 --prompt-file ../prompts.txt
"""

import argparse
import json
import logging
import os
import random
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("create_sft")

DATA_DIR     = Path("data")
OUT_FILE     = DATA_DIR / "d_sft_gen.jsonl"   # separate from official d_sft.jsonl
DATASET_INFO = DATA_DIR / "dataset_info.json"
MODEL_NAME   = "Qwen/Qwen2.5-VL-7B-Instruct"

# ── Medium-to-hard scene prompts ─────────────────────────────────────────────
# These are the sweet spot for base-model SFT generation:
#   - Clear 3-layer spatial structure (sky / midground / ground)
#   - 3-6 named visual elements the base model knows
#   - No unusual subject-object combos (those only work after DPO/GRPO)
# Simple single objects (apple, star, butterfly) produce trivial SVGs.
# Very hard combos (octopus playing organ) produce unrecognisable blobs.

SCENE_PROMPTS = [
    # Coastal / water
    "a red barn with green fields below and blue sky above with white clouds",
    "a lighthouse on rocky cliffs with waves crashing below and seagulls above",
    "a sailboat on blue water with an orange sunset sky behind it",
    "a harbor town with colorful boats on water and houses on a hillside above",
    "a tropical beach with palm trees on the left and a setting sun on the water",
    "a old harbor at night with fishing boats reflected in dark water and a full moon",
    "a harbor at dawn with fishing boats, nets, and a pale orange sky",
    "a busy harbor with fishing boats and seagulls flying overhead",
    "a coastal village with white-washed houses on a steep hillside above the sea",
    "a Viking longship with a striped sail crossing stormy ocean waves",
    # Mountains / highlands
    "a mountain peak with white snow at the top and green pine trees below",
    "a Swiss chalet on a green hillside with snow-capped mountains behind it",
    "a snowy cabin in a pine forest with a chimney and orange light in the windows",
    "a mountain lake with a wooden rowboat and pine trees reflected in the still water",
    "a alpine meadow with wildflowers in the foreground and snowy peaks behind",
    "a Norwegian fjord with steep cliffs, a waterfall, and a small village below",
    "a Scottish highland scene with rolling purple heather and a stone wall",
    "a Himalayan village with stone houses and terraced fields on steep slopes",
    # Forests / meadows
    "a campfire in a forest clearing with stars in the dark sky above",
    "a autumn forest path with orange and red leaves and golden sunlight through trees",
    "a spring meadow with colorful wildflowers, a stream, and butterflies",
    "a waterfall over mossy rocks into a blue pool surrounded by green ferns",
    "a bamboo forest with a winding path and morning mist between the tall stalks",
    "a sunflower field stretching to the horizon under a blue sky with white clouds",
    "a bluebell forest in spring with a path winding through the flowers",
    "a forest of giant redwoods with shafts of sunlight and ferns on the ground",
    # Deserts / drylands
    "a desert scene with orange sand dunes and a cactus under a blazing sun",
    "a Saharan oasis with date palms, a pool of water, and sand dunes around it",
    "a Grand Canyon vista with layered red rock formations and a river below",
    "a desert highway cutting straight through red rock country with a thunderstorm ahead",
    # Villages / architecture
    "a medieval castle on a green hill above a blue moat with colorful flags",
    "a windmill in a Dutch landscape with colorful tulip fields in the foreground",
    "a Japanese pagoda on a hill with cherry blossom trees on either side",
    "a Italian cliffside village at sunset with colorful houses and boats below",
    "a Tuscan hill town with terracotta rooftops, a church tower, and rolling vineyards",
    "a traditional Irish cottage with a thatched roof beside a stone wall and green fields",
    "a fairy tale cottage with a thatched roof, flower garden, and a forest behind",
    "a treehouse connected by rope bridges between tall oak trees",
    # Skies / weather
    "a hot air balloon floating above a green and yellow patchwork of fields",
    "a city skyline at night with lit windows and a full moon above",
    "a stormy lighthouse at night with crashing waves and lightning in the sky",
    "a rainbow over green rolling hills with a blue river in the valley",
    "a rocket launching into a starry sky with a bright exhaust flame below",
    "a space scene with a blue planet, a silver moon, and stars in the black sky",
    # Gardens / parks
    "a flowering garden with roses in the foreground and a stone arch behind",
    "a Japanese zen garden with raked white gravel, rocks, and a red maple tree",
    "a cherry blossom park with a stone path, lanterns, and people under the trees",
    "a English country garden in summer with roses, lavender, and a stone wall",
    "a lavender field in Provence with a stone farmhouse and cypress trees behind",
    # Agricultural / rural
    "a autumn vineyard with golden leaves on the vines and a stone winery building",
    "a rice terraces landscape with layered green fields on steep hillsides",
    "a wheat field in summer with red poppies and a dirt road cutting through it",
    "a green tea plantation on misty rolling hills",
    "a savanna at sunset with a silhouette of an acacia tree and orange sky",
    # Water / rivers
    "a river scene with a wooden mill, a waterwheel, and ducks in the water",
    "a old stone bridge over a river with weeping willows on each bank",
    "a glacial lake with icebergs floating on perfectly still blue-green water",
    "a foggy morning on a lake with a wooden rowboat and reeds in the foreground",
    "a underground cave with stalactites and a glowing underground lake",
    # Fantasy / imaginative (still visually structured)
    "a fantasy castle floating on clouds with rainbows and waterfalls beneath it",
    "a fantasy underground city carved into a giant cavern with glowing mushrooms",
    "a dark fairy-tale forest with gnarled trees, glowing eyes, and a full moon above",
    "a flooded cathedral in a fantasy landscape with fish swimming between the spires",
    "a pirate ship in a cove with a waterfall and hidden treasure on the beach",
]


def _load_prompts(prompt_file: str | None) -> list[str]:
    """Load prompts from file, skipping blank lines and comments (#)."""
    if prompt_file:
        path = Path(prompt_file)
        if path.exists():
            prompts = [
                line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            if prompts:
                log.info(f"Loaded {len(prompts)} prompts from {path}")
                return prompts
            log.warning(f"Prompt file empty: {path}")
    log.info(f"Using built-in SCENE_PROMPTS ({len(SCENE_PROMPTS)} medium-hard scenes)")
    return SCENE_PROMPTS


def _make_prompt(text: str) -> str:
    return (
        f"You are an expert SVG artist. Generate a complete, colorful SVG image for: '{text}'. "
        f"Draw in layers — background first (sky/ground), then midground objects, then foreground details. "
        f"Use a viewBox of '0 0 200 200'. Every element must have a fill color. "
        f"Return ONLY the SVG code, starting with <svg and ending with </svg>. No explanation."
    )


def _generate_svgs(prompts, model, processor, device):
    """Generate SVGs for a list of prompts using the model."""
    import torch
    results = []
    for prompt in prompts:
        msg = [{"role": "user", "content": _make_prompt(prompt)}]
        text = processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], return_tensors="pt").to(device)
        try:
            with torch.inference_mode():
                ids = model.generate(
                    **inputs,
                    max_new_tokens=1536,
                    do_sample=False,
                    pad_token_id=processor.tokenizer.eos_token_id,
                )
            n = inputs["input_ids"].shape[1]
            raw = processor.tokenizer.decode(ids[0][n:], skip_special_tokens=True).strip()
            m = re.search(r'(<svg[\s>].*?</svg>)', raw, re.DOTALL | re.IGNORECASE)
            results.append((prompt, m.group(1).strip() if m else None))
        except Exception as e:
            log.warning(f"  generation failed: {e}")
            results.append((prompt, None))
    return results


def main(args):
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    from svg_utils import standardize_svg, is_colorful, is_renderable

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log.info(f"Loading model: {MODEL_NAME}")
    quant = BitsAndBytesConfig(load_in_8bit=True, llm_int8_skip_modules=["visual"])
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_NAME, quantization_config=quant, device_map="auto"
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load medium-hard prompts from file (or built-in SCENE_PROMPTS)
    source_prompts = _load_prompts(args.prompt_file)
    base_prompts = source_prompts * ((args.n_samples // len(source_prompts)) + 2)
    random.shuffle(base_prompts)
    all_prompts = base_prompts[:args.n_samples]

    # Resume: count rows already in the output file
    n_ok = 0
    if OUT_FILE.exists():
        n_ok = sum(1 for line in OUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip())
        if n_ok >= args.n_samples:
            log.info(f"Already have {n_ok} samples in {OUT_FILE}, nothing to do.")
            return
        log.info(f"Resuming from {n_ok} existing samples")

    with open(OUT_FILE, "a", encoding="utf-8") as fout:
        for i in range(0, len(all_prompts), args.batch_size):
            batch = all_prompts[i:i + args.batch_size]
            results = _generate_svgs(batch, model, processor, device)
            for prompt, svg_raw in results:
                if svg_raw is None:
                    continue
                try:
                    svg = standardize_svg(svg_raw)
                except Exception:
                    svg = None
                if svg is None:
                    # Fall back to lightly-cleaned raw SVG if standardize fails
                    svg = svg_raw
                try:
                    if not is_colorful(svg):
                        log.info(f"  rejected (not colorful)")
                        continue
                except Exception:
                    log.info(f"  rejected (filter exception)")
                    continue
                row = {
                    "conversations": [
                        {"from": "human", "value": _make_prompt(prompt)},
                        {"from": "gpt",   "value": svg},
                    ]
                }
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                n_ok += 1
                log.info(f"  accepted {n_ok}/{args.n_samples}")
                if n_ok % 10 == 0:
                    log.info(f"  checkpoint: {n_ok} saved")
            if n_ok >= args.n_samples:
                break

    log.info(f"Done: {n_ok} samples → {OUT_FILE}")

    # Merge d_sft_gen entry into existing dataset_info.json (don't overwrite other entries)
    info = json.loads(DATASET_INFO.read_text(encoding="utf-8")) if DATASET_INFO.exists() else {}
    info["d_sft_gen"] = {
        "file_name": "d_sft_gen.jsonl",
        "formatting": "sharegpt",
        "columns": {"messages": "conversations"},
    }
    DATASET_INFO.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"dataset_info.json updated with d_sft_gen entry")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples",   type=int, default=5000)
    parser.add_argument("--batch-size",  type=int, default=4)
    parser.add_argument("--prompt-file", type=str, default=None,
                        help="Path to prompt file (one per line, # for comments). "
                             "Defaults to ../prompts.txt if it exists, else built-in scenes.")
    args = parser.parse_args()
    # Default prompt file: ../prompts.txt relative to script location
    if args.prompt_file is None:
        default_pf = Path(__file__).parent.parent / "prompts.txt"
        args.prompt_file = str(default_pf) if default_pf.exists() else None
    main(args)
