"""
Generate a text-only SVG SFT dataset using Qwen2.5-VL-7B-Instruct as teacher.

Uses the base model to generate SVG drafts for diverse prompts, keeps only
renderable/colorful ones, and saves in LlamaFactory sharegpt format.

This self-supervised approach mirrors the IntroSVG paper's D_G^direct step
but requires no external data sources.

Run:
    python 00_create_sft_data.py --n-samples 5000 --batch-size 4
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

DATA_DIR = Path("data")
OUT_FILE = DATA_DIR / "d_sft.jsonl"
DATASET_INFO = DATA_DIR / "dataset_info.json"
MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

# ── Diverse prompt bank ───────────────────────────────────────────────────────

PROMPT_TEMPLATES = [
    # Nature
    "a red apple with a green leaf and a brown stem",
    "a yellow sunflower with a dark center and green stem",
    "a blue butterfly with detailed wing patterns",
    "a green cactus with pink flowers",
    "a purple lavender bouquet tied with a ribbon",
    "a colorful parrot perched on a branch",
    "a red and orange autumn maple leaf",
    "a pink cherry blossom branch with white flowers",
    "a golden wheat field under a blue sky",
    "a snow-capped mountain peak at sunset",
    # Objects
    "a red coffee cup with rising steam",
    "a blue bicycle with yellow wheels",
    "a vintage camera in brown and gold",
    "a green watering can with water drops",
    "a yellow taxi cab on a city street",
    "a colorful kite flying in a blue sky",
    "a wooden treasure chest with golden lock",
    "a red fire hydrant with silver details",
    "a blue umbrella with rain drops",
    "a green mailbox with a red flag",
    # Animals
    "an orange cat sitting with a curled tail",
    "a brown bear eating honey from a jar",
    "a white rabbit with pink ears in grass",
    "a colorful tropical fish in blue water",
    "a red ladybug with black spots on a leaf",
    "a yellow duck swimming on blue water",
    "a green frog sitting on a lily pad",
    "an orange fox running through autumn leaves",
    "a black and white zebra",
    "a pink flamingo standing on one leg",
    # Geometric / Abstract
    "a rainbow arc over green hills",
    "a colorful mandala with intricate patterns",
    "a geometric star with alternating colors",
    "a spiral galaxy with colorful stars",
    "a kaleidoscope pattern in blue and gold",
    "a mosaic of colorful hexagonal tiles",
    "a pinwheel toy with four colorful blades",
    "a set of colorful concentric circles",
    "a decorative Celtic knot in green and gold",
    "a stained glass window pattern",
    # Scenes
    "a red barn with a weathervane on a farm",
    "a sailboat on calm blue water at sunset",
    "a cozy wooden cabin in a snowy forest",
    "a lighthouse on rocky cliffs by the ocean",
    "a tropical beach with palm trees and sun",
    "a city skyline at night with lit windows",
    "a hot air balloon over colorful fields",
    "a park bench under a cherry blossom tree",
    "a windmill in a Dutch landscape with tulips",
    "a campfire under a starry night sky",
    # Food
    "a slice of pizza with red sauce and toppings",
    "a colorful bowl of fruit salad",
    "a layered chocolate cake with strawberries",
    "a cup of ice cream with sprinkles",
    "a glass of lemonade with a straw",
    "a bunch of colorful lollipops",
    "a steaming bowl of ramen noodles",
    "a stack of fluffy pancakes with maple syrup",
    "a colorful macaron tower",
    "a watermelon slice with black seeds",
    # Symbols / Icons
    "a golden crown decorated with colorful gems",
    "a red heart with golden wings",
    "a crescent moon with three golden stars",
    "a blue shield with a golden eagle emblem",
    "a colorful musical note",
    "a trophy cup in gold with a blue ribbon",
    "a graduation cap with gold tassel",
    "a peace symbol in rainbow colors",
    "a recycling symbol in green",
    "a compass rose in blue and gold",
    # Fantasy
    "a purple dragon breathing fire",
    "a unicorn with a rainbow mane",
    "a castle with colorful flags on towers",
    "a magic wand with sparkles and stars",
    "a mermaid with a blue tail in the ocean",
    "a wizard hat with golden stars",
    "a crystal ball with swirling colors",
    "a fairy sitting on a mushroom",
    "an enchanted forest with glowing mushrooms",
    "a phoenix rising from orange flames",
    # Vehicles
    "a vintage red steam locomotive with smoke",
    "a rocket launching into a starry sky",
    "a vintage wooden sailing ship",
    "a yellow school bus",
    "a colorful vintage Volkswagen Beetle",
    "a green tractor on a farm",
    "a blue submarine underwater",
    "a red double-decker bus",
    "a silver spaceship",
    "a colorful hot air balloon basket",
    # Flowers
    "a red rose with thorny green stem",
    "a blue forget-me-not flower cluster",
    "a yellow and orange marigold",
    "a white daisy with yellow center",
    "a pink peony in full bloom",
    "a purple iris with ruffled petals",
    "a red poppy field",
    "an orange tulip",
    "a white magnolia blossom",
    "a blue cornflower",
    # Complex scenes (layered: background + midground + foreground)
    "a red barn with green fields below and blue sky above with white clouds",
    "a lighthouse on rocky cliffs with waves crashing below and seagulls above",
    "a city skyline at night with lit windows and a yellow moon above",
    "a sailboat on blue water with an orange sunset sky behind it",
    "a mountain peak with white snow at the top and green pine trees below",
    "a tropical beach with palm trees on the left and a setting sun on the water",
    "a campfire in a forest clearing with stars in the dark sky above",
    "a waterfall over mossy rocks into a blue pool surrounded by green ferns",
    "a desert scene with orange sand dunes and a cactus under a hot yellow sun",
    "a hot air balloon floating above a green and yellow patchwork of fields",
    "a snowy cabin in a pine forest with a chimney and orange light in the windows",
    "a medieval castle on a green hill above a blue moat with colorful flags",
    "a coral reef with orange and yellow fish swimming above blue and purple coral",
    "a rainbow over green rolling hills with a blue river in the valley",
    "a Japanese pagoda on a hill with pink cherry blossom trees on each side",
    "a Viking longship with a red and white striped sail on a grey stormy sea",
    "a savanna at sunset with a silhouette of an acacia tree and orange sky",
    "a cozy library interior with bookshelves, a reading chair, and a fireplace",
    "a underwater scene with a sunken ship, colorful fish, and blue water above",
    "a autumn forest path with orange and red leaves and golden sunlight through trees",
    "a spring meadow with colorful wildflowers, a stream, and butterflies",
    "a harbor town with colorful boats on water and houses on a hillside above",
    "a winter scene with a frozen pond, bare trees, and snow on the ground",
    "a rocket launching into a starry sky with a bright exhaust flame below",
    "a ancient ruins on a cliff above a blue sea with seabirds flying",
    "a dark cave opening with sunlight streaming in and moss on the rocks",
    "a suspension bridge over a deep green gorge with mist below",
    "a bamboo forest with light filtering through green stalks and a path below",
    "a flowering garden with roses in the foreground and a stone arch behind",
    "a river scene with a wooden mill, a waterwheel, and ducks in the water",
    "a Nordic fjord with steep green cliffs, blue water, and a small red house",
    "a rice terrace with layered green fields, a blue sky, and clouds reflected in water",
    "a night market with colorful lanterns, food stalls, and a crowd of people",
    "a space scene with a blue planet, a silver moon, and stars in the black sky",
    "a mountain lake with a wooden rowboat, pine trees reflected in the water",
    "a fairy tale cottage with a thatched roof, flower garden, and a forest behind",
    "a beach at dawn with pink and orange sky, gentle waves, and a lighthouse",
    "a autumn vineyard with golden leaves on the vines and a stone house behind",
    "a lagoon with turquoise water, white sand, palm trees, and a wooden pier",
    "a thunderstorm over the ocean with dark clouds, lightning, and rough waves",
]


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

    # Expand prompts to target count via random variation
    all_prompts = []
    base_prompts = PROMPT_TEMPLATES * ((args.n_samples // len(PROMPT_TEMPLATES)) + 2)
    random.shuffle(base_prompts)
    all_prompts = base_prompts[:args.n_samples]

    n_ok = 0
    with open(OUT_FILE, "w", encoding="utf-8") as fout:
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

    # Write dataset_info.json
    info = {
        "d_sft": {
            "file_name": "d_sft.jsonl",
            "formatting": "sharegpt",
            "columns": {"messages": "conversations"},
        },
        "d_pref_g": {
            "file_name": "d_pref_g.jsonl",
            "formatting": "sharegpt",
            "ranking": True,
            "columns": {"messages": "messages", "chosen": "chosen", "rejected": "rejected"},
        },
    }
    DATASET_INFO.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"dataset_info.json → {DATASET_INFO}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples",  type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    main(args)
