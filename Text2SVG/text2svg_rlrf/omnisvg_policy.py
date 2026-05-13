from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch

_SYSTEM_PROMPT = (
    "You are an expert SVG code generator. "
    "Generate precise, valid SVG path commands that accurately represent the described scene or object. "
    "Focus on capturing key shapes, spatial relationships, and visual composition."
)

_BLACK_COLOR_TOKEN = 40012


@dataclass
class OmniSVGBundle:
    model: torch.nn.Module  # sketch_decoder.transformer (Qwen2.5-VL)
    tokenizer: object        # Qwen text tokenizer
    svg_tokenizer: object    # OmniSVG SVGTokenizer: coord tokens → SVG geometry
    processor: object        # Qwen processor (chat template formatting)
    bos_token_id: int
    eos_token_id: int
    pad_token_id: int

    def format_prompt(self, caption: str) -> str:
        instruction = (
            f"Generate an SVG illustration for: {caption}\n\n"
            "Requirements:\n"
            "- Create complete SVG path commands with proper coordinates and colors\n"
            "- Ensure the image visually represents the described scene\n"
            "- Use diverse shapes and colors to capture the visual essence"
        )
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": [{"type": "text", "text": instruction}]},
        ]
        return self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )


def load_omnisvg_policy(
    omnisvg_dir: str,
    model_size: str = "4B",
    weight_path: Optional[str] = None,
    lora_cfg=None,
    cache_dir: Optional[str] = None,
) -> OmniSVGBundle:
    omnisvg_root = Path(omnisvg_dir).resolve()
    if str(omnisvg_root) not in sys.path:
        sys.path.insert(0, str(omnisvg_root))

    import yaml
    from decoder import SketchDecoder
    from tokenizer import SVGTokenizer
    from transformers import AutoTokenizer, AutoProcessor

    config_path = str(omnisvg_root / "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    models_cfg = cfg["models"][model_size]
    qwen_path = models_cfg["huggingface"]["qwen_model"]
    if weight_path is None:
        weight_path = models_cfg["huggingface"]["omnisvg_model"]

    bos_id = cfg["model"]["bos_token_id"]
    eos_id = cfg["model"]["eos_token_id"]
    pad_id = cfg["model"]["pad_token_id"]

    use_4bit = (
        torch.cuda.is_available()
        and torch.cuda.get_device_properties(0).total_memory / 1e9 < 20
    )

    tokenizer = AutoTokenizer.from_pretrained(
        qwen_path, trust_remote_code=True, padding_side="left", cache_dir=cache_dir
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = pad_id

    processor = AutoProcessor.from_pretrained(
        qwen_path, trust_remote_code=True, padding_side="left", cache_dir=cache_dir
    )
    processor.tokenizer.padding_side = "left"

    sketch_decoder = SketchDecoder(
        config_path=config_path,
        model_path=qwen_path,
        model_size=model_size,
        use_4bit=use_4bit,
    )

    # Load OmniSVG fine-tuned weights
    import os
    from huggingface_hub import hf_hub_download

    is_local = (
        os.path.exists(weight_path)
        or weight_path.startswith("/")
        or weight_path.startswith("./")
        or (len(weight_path) > 1 and weight_path[1] == ":")
    )
    if is_local:
        bin_path = os.path.join(weight_path, "pytorch_model.bin")
        if not os.path.exists(bin_path) and weight_path.endswith(".bin"):
            bin_path = weight_path
    else:
        bin_path = hf_hub_download(repo_id=weight_path, filename="pytorch_model.bin")

    state_dict = torch.load(bin_path, map_location="cpu")
    sketch_decoder.load_state_dict(state_dict)

    # Work directly with the underlying Qwen transformer (SketchDecoder.forward is not open-source)
    transformer = sketch_decoder.transformer

    if lora_cfg is not None and lora_cfg.enabled:
        from peft import LoraConfig as PeftLoraConfig, get_peft_model, prepare_model_for_kbit_training

        if use_4bit:
            transformer = prepare_model_for_kbit_training(transformer)
        peft_cfg = PeftLoraConfig(
            r=lora_cfg.r,
            lora_alpha=lora_cfg.alpha,
            lora_dropout=lora_cfg.dropout,
            target_modules=lora_cfg.target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )
        transformer = get_peft_model(transformer, peft_cfg)

    if hasattr(transformer, "gradient_checkpointing_enable"):
        transformer.gradient_checkpointing_enable()
    transformer.config.use_cache = False
    transformer.train()

    svg_tokenizer = SVGTokenizer(config_path, model_size=model_size)

    return OmniSVGBundle(
        model=transformer,
        tokenizer=tokenizer,
        svg_tokenizer=svg_tokenizer,
        processor=processor,
        bos_token_id=bos_id,
        eos_token_id=eos_id,
        pad_token_id=pad_id,
    )


@torch.no_grad()
def generate_omnisvg_rollouts(
    bundle: OmniSVGBundle,
    captions: List[str],
    rollouts_per_caption: int,
    max_new_tokens: int = 1024,
) -> List[List[torch.Tensor]]:
    model = bundle.model
    was_training = model.training
    model.eval()
    outputs: List[List[torch.Tensor]] = []
    try:
        for caption in captions:
            prompt = bundle.format_prompt(caption)
            enc = bundle.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=512
            )
            device = next(model.parameters()).device
            input_ids = enc["input_ids"].to(device)
            attention_mask = enc["attention_mask"].to(device)
            generated = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                num_return_sequences=rollouts_per_caption,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.05,
                eos_token_id=bundle.eos_token_id,
                pad_token_id=bundle.pad_token_id,
            )
            outputs.append([row.detach().cpu() for row in generated])
    finally:
        if was_training:
            model.train()
    return outputs


def decode_omnisvg_tokens_to_svg(
    bundle: OmniSVGBundle, seq: torch.Tensor, prompt_len: int
) -> str:
    generated_ids = seq[prompt_len:].unsqueeze(0).cpu()
    fake_wrapper = torch.cat(
        [
            torch.full((1, 1), bundle.bos_token_id, dtype=torch.long),
            generated_ids,
            torch.full((1, 1), bundle.eos_token_id, dtype=torch.long),
        ],
        dim=1,
    )
    try:
        generated_xy = bundle.svg_tokenizer.process_generated_tokens(fake_wrapper)
        if not generated_xy:
            return ""
        svg_tensors, color_tensors = bundle.svg_tokenizer.raster_svg(generated_xy)
        if not svg_tensors or not svg_tensors[0]:
            return ""
        num_paths = len(svg_tensors[0])
        while len(color_tensors) < num_paths:
            color_tensors.append(_BLACK_COLOR_TOKEN)
        svg = bundle.svg_tokenizer.apply_colors_to_svg(svg_tensors[0], color_tensors)
        return svg.to_str()
    except Exception:
        return ""
