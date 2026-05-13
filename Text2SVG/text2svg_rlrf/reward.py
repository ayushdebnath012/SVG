from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import torch

from .config import RewardConfig, RuntimeConfig, SVGConfig
from .prompts import judge_prompt
from .svg import SVGRender, render_svg


@dataclass
class RewardResult:
    reward: float
    parts: Dict[str, float]
    render: SVGRender


class VLMJudge:
    def __init__(self, runtime: RuntimeConfig, reward: RewardConfig, model_name: str):
        self.runtime = runtime
        self.reward = reward
        self.model_name = model_name
        self.processor = None
        self.model = None

    def _load(self) -> None:
        if self.model is not None:
            return
        from transformers import AutoProcessor

        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=self.reward.trust_remote_code,
            cache_dir=self.runtime.cache_dir,
        )
        try:
            from transformers import Qwen2_5_VLForConditionalGeneration
            model_cls = Qwen2_5_VLForConditionalGeneration
        except Exception:
            from transformers import AutoModelForVision2Seq
            model_cls = AutoModelForVision2Seq

        load_kwargs: dict = dict(
            device_map="auto",
            trust_remote_code=self.reward.trust_remote_code,
            cache_dir=self.runtime.cache_dir,
        )
        if self.reward.judge_load_in_4bit:
            from transformers import BitsAndBytesConfig
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            dtype = torch.bfloat16 if self.runtime.dtype in ("bf16", "bfloat16") else torch.float16
            load_kwargs["torch_dtype"] = dtype if torch.cuda.is_available() else torch.float32

        self.model = model_cls.from_pretrained(self.model_name, **load_kwargs)
        self.model.eval()

    @torch.no_grad()
    def score(self, image, description: str, template_file: str) -> float:
        self._load()
        text_prompt = judge_prompt(description, template_file)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": text_prompt},
                ],
            }
        ]
        try:
            chat = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(text=[chat], images=[image], return_tensors="pt", padding=True)
        except Exception:
            inputs = self.processor(text=[text_prompt], images=[image], return_tensors="pt", padding=True)
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        output = self.model.generate(**inputs, max_new_tokens=4, do_sample=False)
        decoded = self.processor.batch_decode(output, skip_special_tokens=True)[0].lower()
        tail = decoded[-96:]
        yes = "yes" in tail
        no = "no" in tail
        if yes and not no:
            return self.reward.yes_reward
        if no and not yes:
            return self.reward.no_reward
        return self.reward.ambiguous_reward


class CLIPScorer:
    """CLIP image-text cosine similarity, used as a continuous training reward signal."""

    def __init__(self, runtime: RuntimeConfig, model_name: str):
        self.runtime = runtime
        self.model_name = model_name
        self._model = None
        self._processor = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import CLIPModel, CLIPProcessor

        self._processor = CLIPProcessor.from_pretrained(
            self.model_name, cache_dir=self.runtime.cache_dir
        )
        # CLIP runs at fp32 for stability; small model so VRAM cost is minimal
        self._model = CLIPModel.from_pretrained(
            self.model_name, cache_dir=self.runtime.cache_dir
        )
        if torch.cuda.is_available():
            self._model = self._model.cuda()
        self._model.eval()

    @torch.no_grad()
    def score(self, image, caption: str) -> float:
        self._load()
        device = next(self._model.parameters()).device
        inputs = self._processor(
            text=[caption], images=[image], return_tensors="pt", padding=True, truncation=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        outputs = self._model(**inputs)
        # logits_per_image = cosine_similarity × temperature (≈100)
        # Rescale from [0.10, 0.35] typical range to [0, 1]
        raw = outputs.logits_per_image[0, 0].item() / 100.0
        normalized = (raw - 0.10) / (0.35 - 0.10)
        return float(max(0.0, min(1.0, normalized)))


class Text2SVGReward:
    def __init__(self, runtime: RuntimeConfig, svg: SVGConfig, reward: RewardConfig):
        self.runtime = runtime
        self.svg = svg
        self.reward = reward
        self.judge = VLMJudge(runtime, reward, reward.judge_model_name_or_path)
        self.clip: Optional[CLIPScorer] = (
            CLIPScorer(runtime, reward.clip_model_name_or_path)
            if reward.clip_model_name_or_path and not reward.use_clip_as_metric_only
            else None
        )

    def _judge_score(self, image, caption: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        prompt_map = {
            "easy": self.reward.judge_prompts.easy_template_file,
            "hard": self.reward.judge_prompts.hard_template_file,
        }
        for name in self.reward.train_judge_prompts:
            scores[f"judge_{name}"] = self.judge.score(image, caption, prompt_map[name])
        return scores

    def score(self, generated_text: str, caption: str) -> RewardResult:
        rendered = render_svg(generated_text, caption, self.svg)
        if not rendered.valid or rendered.image is None:
            reward = self.reward.render_fail_reward
            if rendered.blank:
                reward -= self.reward.blank_penalty
            if rendered.copied_text:
                reward -= self.reward.prompt_copy_penalty
            return RewardResult(
                reward=reward,
                parts={"valid": 0.0, "render_fail": 1.0, "copied_text": float(rendered.copied_text)},
                render=rendered,
            )

        parts = self._judge_score(rendered.image, caption)
        judge_reward = sum(parts.values()) / max(1, len(parts))

        # CLIP similarity: continuous signal on top of binary VLM judge
        clip_score = 0.0
        if self.clip is not None:
            clip_score = self.clip.score(rendered.image, caption)
            parts["clip_similarity"] = clip_score

        visible_bonus = self.reward.visible_element_bonus * min(
            1.0, rendered.visible_elements / max(1, self.svg.min_visible_elements)
        )
        length_penalty = 0.0
        svg_len = len(rendered.sanitized_svg)
        if svg_len < self.reward.min_svg_chars_reward_floor:
            length_penalty = (self.reward.min_svg_chars_reward_floor - svg_len) / self.reward.min_svg_chars_reward_floor
        elif svg_len > self.reward.max_svg_chars_reward_ceiling:
            length_penalty = (svg_len - self.reward.max_svg_chars_reward_ceiling) / self.reward.max_svg_chars_reward_ceiling

        reward = (
            judge_reward
            + self.reward.clip_reward_weight * clip_score
            + visible_bonus
            - self.reward.length_penalty_weight * length_penalty
        )
        if rendered.copied_text:
            reward -= self.reward.prompt_copy_penalty

        parts.update(
            {
                "valid": 1.0,
                "visible_bonus": visible_bonus,
                "length_penalty": length_penalty,
                "copied_text": float(rendered.copied_text),
            }
        )
        return RewardResult(reward=float(reward), parts=parts, render=rendered)

    def score_many(self, generated_texts: List[str], captions: List[str]) -> List[RewardResult]:
        return [self.score(text, caption) for text, caption in zip(generated_texts, captions)]
