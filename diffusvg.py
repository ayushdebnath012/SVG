#!/usr/bin/env python3
"""
DiffuSVG: Complete SVG Generation Pipeline
==========================================

A three-stage pipeline for zero-shot SVG generation:
1. Prompt → Diffusion (SVG-friendly image generation)
2. Image → VLM (code synthesis with chain-of-thought)
3. Refinement Loop (iterative correction)

Requirements:
    pip install torch torchvision diffusers transformers accelerate peft
    pip install anthropic openai  # For VLM APIs
    pip install cairosvg pillow numpy
    pip install lpips clip  # For evaluation metrics
    pip install datasets huggingface_hub  # For data loading
    pip install pydiffvg  # For differentiable rendering (optional)

Usage:
    # Quick inference
    python diffusvg.py --prompt "a red apple" --output output.svg
    
    # Train LoRA
    python diffusvg.py --mode train --dataset ./vector_images
    
    # Batch processing
    python diffusvg.py --mode batch --input prompts.txt --output_dir ./outputs

Author: DiffuSVG Team
Date: February 2026
"""

import os
import io
import re
import json
import base64
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import numpy as np
from PIL import Image

# Deep Learning
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Diffusion
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
    AutoencoderKL,
    UNet2DConditionModel,
)
from diffusers.loaders import LoraLoaderMixin
from peft import LoraConfig, get_peft_model

# Transformers
from transformers import (
    CLIPProcessor,
    CLIPModel,
    AutoProcessor,
    AutoModelForCausalLM,
    Blip2Processor,
    Blip2ForConditionalGeneration,
)

# SVG Processing
import cairosvg

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

def _get_hf_token() -> str:
    """Helper to try getting HF token from Kaggle Secrets, then environment."""
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        try:
            from kaggle_secrets import UserSecretsClient # type: ignore
            user_secrets = UserSecretsClient()
            hf_token = user_secrets.get_secret("HF_TOKEN")
        except Exception:
            pass
    if not hf_token:
        hf_token = "YOUR_HF_TOKEN_HERE" # fallback
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
    return hf_token

@dataclass
class DiffusionConfig:
    """Configuration for diffusion model."""
    model_name: str = "stabilityai/stable-diffusion-xl-base-1.0"
    use_lora: bool = True
    lora_path: Optional[str] = None
    lora_rank: int = 32
    lora_alpha: int = 32
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    resolution: int = 1024
    dtype: str = "float16"
    device: str = "cuda"
    hf_token: str = field(default_factory=_get_hf_token)
    
    # Style prompts
    style_prefix: str = "flat vector illustration, clean edges, solid colors, minimal gradients, "
    negative_prompt: str = "gradient, photorealistic, blurry, complex textures, shadows, 3d render, realistic"


@dataclass
class VLMConfig:
    """Configuration for Vision-Language Model."""
    provider: str = "anthropic"  # "anthropic", "openai", "local"
    model_name: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.1
    api_key: Optional[str] = None  # Uses env var if None
    
    # Local model settings (for provider="local")
    local_model_name: str = "Qwen/Qwen2-VL-7B-Instruct"
    local_device: str = "cuda"


@dataclass  
class RefinementConfig:
    """Configuration for iterative refinement."""
    max_iterations: int = 5
    dino_threshold: float = 0.85
    clip_threshold: float = 0.25
    use_diffvg: bool = False  # Use differentiable rendering
    render_size: int = 512


@dataclass
class TrainingConfig:
    """Configuration for LoRA training."""
    output_dir: str = "./vector_lora"
    learning_rate: float = 1e-4
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_train_steps: int = 2000
    lr_scheduler: str = "cosine"
    lr_warmup_steps: int = 100
    seed: int = 42
    mixed_precision: str = "fp16"
    save_steps: int = 500


@dataclass
class PipelineConfig:
    """Master configuration."""
    diffusion: DiffusionConfig = field(default_factory=DiffusionConfig)
    vlm: VLMConfig = field(default_factory=VLMConfig)
    refinement: RefinementConfig = field(default_factory=RefinementConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    
    # Output settings
    output_format: str = "svg"  # "svg", "both" (svg + png)
    viewbox_size: int = 200


# =============================================================================
# SVG UTILITIES
# =============================================================================

class SVGValidator:
    """Validates and repairs SVG code."""
    
    @staticmethod
    def extract_svg(text: str) -> Optional[str]:
        """Extract SVG code from text response."""
        # Try to find SVG tags
        patterns = [
            r'<svg[\s\S]*?</svg>',
            r'```svg\s*([\s\S]*?)```',
            r'```xml\s*([\s\S]*?)```',
            r'```\s*([\s\S]*?)```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                svg = match.group(0) if '<svg' in match.group(0) else match.group(1)
                if '<svg' in svg:
                    return svg.strip()
        
        # If text itself starts with svg
        if text.strip().startswith('<svg'):
            return text.strip()
        
        return None
    
    @staticmethod
    def validate_svg(svg_code: str) -> bool:
        """Check if SVG renders without errors."""
        try:
            cairosvg.svg2png(bytestring=svg_code.encode('utf-8'))
            return True
        except Exception as e:
            logger.warning(f"SVG validation failed: {e}")
            return False
    
    @staticmethod
    def repair_svg(svg_code: str) -> str:
        """Attempt basic repairs on malformed SVG."""
        # Ensure xmlns is present
        if 'xmlns' not in svg_code:
            svg_code = svg_code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        # Ensure viewBox is present
        if 'viewBox' not in svg_code and 'viewbox' not in svg_code.lower():
            svg_code = svg_code.replace('<svg', '<svg viewBox="0 0 200 200"', 1)
        
        # Close unclosed tags
        unclosed_tags = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path']
        for tag in unclosed_tags:
            # Find tags that aren't self-closing
            pattern = rf'<{tag}([^>]*[^/])>'
            svg_code = re.sub(pattern, rf'<{tag}\1/>', svg_code)
        
        return svg_code
    
    @staticmethod
    def render_svg(svg_code: str, size: int = 512) -> Optional[Image.Image]:
        """Render SVG to PIL Image."""
        try:
            png_data = cairosvg.svg2png(
                bytestring=svg_code.encode('utf-8'),
                output_width=size,
                output_height=size
            )
            return Image.open(io.BytesIO(png_data)).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to render SVG: {e}")
            return None


class SVGMetrics:
    """Compute SVG quality metrics."""
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self._clip_model = None
        self._clip_processor = None
        self._dino_model = None
        self._dino_processor = None
    
    @property
    def clip_model(self):
        if self._clip_model is None:
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        return self._clip_model, self._clip_processor
    
    @property
    def dino_model(self):
        if self._dino_model is None:
            self._dino_model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14').to(self.device)
            self._dino_model.eval()
        return self._dino_model
    
    def clip_score(self, image: Image.Image, text: str) -> float:
        """Compute CLIP similarity between image and text."""
        model, processor = self.clip_model
        
        inputs = processor(text=[text], images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            similarity = outputs.logits_per_image.item() / 100.0
        
        return similarity
    
    def dino_similarity(self, image1: Image.Image, image2: Image.Image) -> float:
        """Compute DINO feature similarity between two images."""
        model = self.dino_model
        
        # Preprocess images
        transform = torch.nn.Sequential(
            torch.nn.Upsample(size=(224, 224), mode='bilinear'),
        )
        
        def to_tensor(img):
            img = img.resize((224, 224))
            arr = np.array(img).astype(np.float32) / 255.0
            arr = (arr - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
            return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).float().to(self.device)
        
        t1 = to_tensor(image1)
        t2 = to_tensor(image2)
        
        with torch.no_grad():
            f1 = model(t1)
            f2 = model(t2)
            similarity = F.cosine_similarity(f1, f2).item()
        
        return similarity
    
    def compute_all(self, svg_code: str, original_image: Image.Image, prompt: str) -> Dict[str, float]:
        """Compute all metrics for an SVG."""
        rendered = SVGValidator.render_svg(svg_code)
        
        if rendered is None:
            return {"valid": False, "clip_score": 0.0, "dino_score": 0.0}
        
        return {
            "valid": True,
            "clip_score": self.clip_score(rendered, prompt),
            "dino_score": self.dino_similarity(original_image, rendered),
            "path_count": svg_code.count('<path'),
            "element_count": len(re.findall(r'<(rect|circle|ellipse|polygon|path|line)', svg_code)),
        }


# =============================================================================
# DIFFUSION MODULE
# =============================================================================

class SVGFriendlyDiffusion:
    """Diffusion model fine-tuned for SVG-friendly outputs."""
    
    def __init__(self, config: DiffusionConfig):
        self.config = config
        self.device = config.device
        self.dtype = torch.float16 if config.dtype == "float16" else torch.float32
        self.pipeline = None
        
    def load_model(self):
        """Load the diffusion pipeline."""
        logger.info(f"Loading diffusion model: {self.config.model_name}")
        
        # Load base model
        if "xl" in self.config.model_name.lower():
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                self.config.model_name,
                torch_dtype=self.dtype,
                use_safetensors=True,
                variant="fp16" if self.dtype == torch.float16 else None,
                token=self.config.hf_token,
            )
        else:
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.config.model_name,
                torch_dtype=self.dtype,
                token=self.config.hf_token,
            )
        
        # Use faster scheduler
        self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipeline.scheduler.config
        )
        
        # Load LoRA if specified
        if self.config.use_lora and self.config.lora_path:
            logger.info(f"Loading LoRA weights from: {self.config.lora_path}")
            self.pipeline.load_lora_weights(self.config.lora_path)
        
        self.pipeline = self.pipeline.to(self.device)
        
        # Enable memory optimizations
        if hasattr(self.pipeline, 'enable_xformers_memory_efficient_attention'):
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
            except Exception:
                pass
        
        logger.info("Diffusion model loaded successfully")
    
    def generate(
        self,
        prompt: str,
        num_images: int = 1,
        seed: Optional[int] = None,
    ) -> List[Image.Image]:
        """Generate SVG-friendly images from prompt."""
        if self.pipeline is None:
            self.load_model()
        
        # Add style prefix
        full_prompt = self.config.style_prefix + prompt
        
        # Set seed for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # Generate
        with torch.inference_mode():
            result = self.pipeline(
                prompt=full_prompt,
                negative_prompt=self.config.negative_prompt,
                num_images_per_prompt=num_images,
                num_inference_steps=self.config.num_inference_steps,
                guidance_scale=self.config.guidance_scale,
                generator=generator,
            )
        
        return result.images
    
    def train_lora(
        self,
        dataset_path: str,
        config: TrainingConfig,
    ):
        """Train LoRA adapter for vector-style generation."""
        from accelerate import Accelerator
        from torch.optim import AdamW
        from torch.optim.lr_scheduler import CosineAnnealingLR
        
        logger.info("Starting LoRA training...")
        
        # Initialize accelerator
        accelerator = Accelerator(
            mixed_precision=config.mixed_precision,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
        )
        
        # Load base model components
        vae = AutoencoderKL.from_pretrained(
            self.config.model_name, subfolder="vae", torch_dtype=self.dtype
        )
        unet = UNet2DConditionModel.from_pretrained(
            self.config.model_name, subfolder="unet", torch_dtype=self.dtype
        )
        
        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            target_modules=["to_q", "to_k", "to_v", "to_out.0"],
            lora_dropout=0.1,
        )
        
        unet = get_peft_model(unet, lora_config)
        unet.print_trainable_parameters()
        
        # Create dataset
        dataset = VectorStyleDataset(dataset_path, self.config.resolution)
        dataloader = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=4,
        )
        
        # Optimizer and scheduler
        optimizer = AdamW(unet.parameters(), lr=config.learning_rate)
        scheduler = CosineAnnealingLR(
            optimizer,
            T_max=config.max_train_steps,
            eta_min=config.learning_rate * 0.1,
        )
        
        # Prepare for distributed training
        unet, optimizer, dataloader, scheduler = accelerator.prepare(
            unet, optimizer, dataloader, scheduler
        )
        vae = vae.to(accelerator.device)
        
        # Training loop
        global_step = 0
        unet.train()
        
        while global_step < config.max_train_steps:
            for batch in dataloader:
                with accelerator.accumulate(unet):
                    # Encode images to latents
                    latents = vae.encode(batch["pixel_values"]).latent_dist.sample()
                    latents = latents * vae.config.scaling_factor
                    
                    # Sample noise
                    noise = torch.randn_like(latents)
                    timesteps = torch.randint(
                        0, 1000, (latents.shape[0],), device=latents.device
                    )
                    
                    # Add noise
                    noisy_latents = self.pipeline.scheduler.add_noise(
                        latents, noise, timesteps
                    )
                    
                    # Get text embeddings (simplified - use actual text encoder)
                    encoder_hidden_states = batch["text_embeddings"]
                    
                    # Predict noise
                    noise_pred = unet(
                        noisy_latents,
                        timesteps,
                        encoder_hidden_states,
                    ).sample
                    
                    # Compute loss
                    loss = F.mse_loss(noise_pred, noise)
                    
                    accelerator.backward(loss)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                
                global_step += 1
                
                if global_step % 100 == 0:
                    logger.info(f"Step {global_step}, Loss: {loss.item():.4f}")
                
                if global_step % config.save_steps == 0:
                    save_path = os.path.join(config.output_dir, f"checkpoint-{global_step}")
                    unet.save_pretrained(save_path)
                
                if global_step >= config.max_train_steps:
                    break
        
        # Save final model
        unet.save_pretrained(os.path.join(config.output_dir, "final"))
        logger.info(f"Training complete. Model saved to {config.output_dir}")


class VectorStyleDataset(Dataset):
    """Dataset for vector-style images."""
    
    def __init__(self, root_dir: str, resolution: int = 1024):
        self.root_dir = Path(root_dir)
        self.resolution = resolution
        
        # Find all images
        self.image_paths = list(self.root_dir.glob("**/*.png")) + \
                          list(self.root_dir.glob("**/*.jpg")) + \
                          list(self.root_dir.glob("**/*.jpeg"))
        
        # Load captions if available
        self.captions = {}
        caption_file = self.root_dir / "captions.json"
        if caption_file.exists():
            with open(caption_file) as f:
                self.captions = json.load(f)
        
        logger.info(f"Loaded {len(self.image_paths)} images")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        
        # Load and preprocess image
        image = Image.open(img_path).convert("RGB")
        image = image.resize((self.resolution, self.resolution), Image.LANCZOS)
        
        # Normalize to [-1, 1]
        pixel_values = np.array(image).astype(np.float32) / 127.5 - 1.0
        pixel_values = torch.from_numpy(pixel_values).permute(2, 0, 1)
        
        # Get caption
        caption = self.captions.get(img_path.name, "flat vector illustration")
        
        return {
            "pixel_values": pixel_values,
            "caption": caption,
        }


# =============================================================================
# VLM MODULE
# =============================================================================

class VLMCodeGenerator(ABC):
    """Abstract base class for VLM code generators."""
    
    @abstractmethod
    def generate_svg(self, image: Image.Image, prompt: str) -> str:
        """Generate SVG code from image."""
        pass
    
    @abstractmethod
    def critique_svg(
        self, 
        original_image: Image.Image, 
        rendered_svg: Image.Image,
        current_svg: str,
    ) -> Tuple[str, str]:
        """Critique and refine SVG code."""
        pass


class AnthropicVLM(VLMCodeGenerator):
    """Anthropic Claude-based VLM for SVG generation."""
    
    SYSTEM_PROMPT = """You are an expert SVG code generator. When given an image, analyze its visual components and generate precise, valid SVG code.

## ANALYSIS STEPS

STEP 1 - IDENTIFY ALL SHAPES:
For each distinct shape, note:
- Shape type (rect, circle, ellipse, polygon, path)
- Fill color (use hex codes like #FF0000)
- Approximate center position (x, y) in a 200x200 coordinate system
- Approximate dimensions (width, height or radius)
- Any stroke properties

STEP 2 - DETERMINE Z-ORDER (LAYERING):
List shapes from BACK to FRONT:
- Background elements first
- Overlapping elements: which is on top?
- Small details and accents last

STEP 3 - GENERATE SVG CODE:
Follow these rules:
1. Use viewBox="0 0 200 200" 
2. Coordinate system: (0,0) is top-left, (200,200) is bottom-right
3. Use semantic grouping: <g id="object_name">
4. Use appropriate primitives:
   - rect: for rectangles and squares (x, y, width, height)
   - circle: for circles (cx, cy, r)
   - ellipse: for ovals (cx, cy, rx, ry)
   - polygon: for triangles, stars, irregular shapes (points="x1,y1 x2,y2 ...")
   - path: for complex curves only (use M, L, C, A, Z commands)
5. Order elements by z-index (background first, foreground last)
6. Use solid fill colors, avoid gradients

## OUTPUT FORMAT
Output ONLY valid SVG code.
Start with: <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
End with: </svg>
No explanation, no markdown code blocks, just the raw SVG code."""

    CRITIQUE_PROMPT = """Compare the original image (first) with the rendered SVG (second).

Identify up to 3 specific discrepancies:
1. Missing elements - shapes present in original but absent in SVG
2. Position errors - shapes in wrong locations
3. Color mismatches - incorrect fill or stroke colors
4. Size errors - shapes too large or too small
5. Shape errors - wrong primitive used (e.g., circle instead of ellipse)

For each issue, be specific about:
- What is wrong
- Where it is located
- How to fix it

Then provide the CORRECTED SVG code that addresses these issues.

Output format:
ISSUES:
1. [issue description]
2. [issue description]
...

CORRECTED SVG:
<svg ...>
...
</svg>"""

    FEW_SHOT_EXAMPLES = [
        {
            "description": "A simple red circle",
            "svg": '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><circle cx="100" cy="100" r="80" fill="#FF0000"/></svg>'
        },
        {
            "description": "A blue rectangle with rounded corners",
            "svg": '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="40" width="160" height="120" rx="10" fill="#0066CC"/></svg>'
        },
        {
            "description": "A yellow sun with rays",
            "svg": '''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <g id="sun">
    <circle cx="100" cy="100" r="40" fill="#FFD700"/>
    <g id="rays" stroke="#FFD700" stroke-width="4">
      <line x1="100" y1="20" x2="100" y2="50"/>
      <line x1="100" y1="150" x2="100" y2="180"/>
      <line x1="20" y1="100" x2="50" y2="100"/>
      <line x1="150" y1="100" x2="180" y2="100"/>
    </g>
  </g>
</svg>'''
        },
    ]
    
    def __init__(self, config: VLMConfig):
        self.config = config
        
        # Import anthropic
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _build_few_shot_content(self) -> str:
        """Build few-shot examples string."""
        examples = []
        for i, ex in enumerate(self.FEW_SHOT_EXAMPLES, 1):
            examples.append(f"Example {i}: {ex['description']}\nOutput:\n{ex['svg']}")
        return "\n\n".join(examples)
    
    def generate_svg(self, image: Image.Image, prompt: str) -> str:
        """Generate SVG code from image using Claude."""
        image_b64 = self._image_to_base64(image)
        
        user_content = [
            {
                "type": "text",
                "text": f"Generate SVG code for this image. The image represents: {prompt}\n\n{self._build_few_shot_content()}\n\nNow generate SVG for the provided image:"
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_b64,
                }
            }
        ]
        
        response = self.client.messages.create(
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}]
        )
        
        return response.content[0].text
    
    def critique_svg(
        self,
        original_image: Image.Image,
        rendered_svg: Image.Image,
        current_svg: str,
    ) -> Tuple[str, str]:
        """Critique and refine SVG code."""
        orig_b64 = self._image_to_base64(original_image)
        rendered_b64 = self._image_to_base64(rendered_svg)
        
        user_content = [
            {"type": "text", "text": "Original image:"},
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": orig_b64}
            },
            {"type": "text", "text": "Current SVG render:"},
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": rendered_b64}
            },
            {"type": "text", "text": f"Current SVG code:\n{current_svg}\n\n{self.CRITIQUE_PROMPT}"}
        ]
        
        response = self.client.messages.create(
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": user_content}]
        )
        
        text = response.content[0].text
        
        # Extract issues and corrected SVG
        issues = ""
        if "ISSUES:" in text:
            issues_match = re.search(r'ISSUES:(.*?)(?:CORRECTED SVG:|<svg)', text, re.DOTALL)
            if issues_match:
                issues = issues_match.group(1).strip()
        
        corrected_svg = SVGValidator.extract_svg(text) or current_svg
        
        return issues, corrected_svg


class OpenAIVLM(VLMCodeGenerator):
    """OpenAI GPT-4V based VLM for SVG generation."""
    
    def __init__(self, config: VLMConfig):
        self.config = config
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def _image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def generate_svg(self, image: Image.Image, prompt: str) -> str:
        """Generate SVG code from image using GPT-4V."""
        image_b64 = self._image_to_base64(image)
        
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {
                    "role": "system",
                    "content": AnthropicVLM.SYSTEM_PROMPT  # Reuse the same system prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Generate SVG code for this image representing: {prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
    
    def critique_svg(
        self,
        original_image: Image.Image,
        rendered_svg: Image.Image,
        current_svg: str,
    ) -> Tuple[str, str]:
        """Critique and refine SVG code."""
        orig_b64 = self._image_to_base64(original_image)
        rendered_b64 = self._image_to_base64(rendered_svg)
        
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Original image:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{orig_b64}"}},
                        {"type": "text", "text": "Current SVG render:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{rendered_b64}"}},
                        {"type": "text", "text": f"Current SVG:\n{current_svg}\n\n{AnthropicVLM.CRITIQUE_PROMPT}"}
                    ]
                }
            ]
        )
        
        text = response.choices[0].message.content
        
        issues = ""
        if "ISSUES:" in text:
            issues_match = re.search(r'ISSUES:(.*?)(?:CORRECTED SVG:|<svg)', text, re.DOTALL)
            if issues_match:
                issues = issues_match.group(1).strip()
        
        corrected_svg = SVGValidator.extract_svg(text) or current_svg
        
        return issues, corrected_svg


class LocalVLM(VLMCodeGenerator):
    """Local VLM using Qwen-VL or similar."""
    
    def __init__(self, config: VLMConfig):
        self.config = config
        self.model = None
        self.processor = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            logger.info(f"Loading local VLM: {self.config.local_model_name}")
            
            self.processor = AutoProcessor.from_pretrained(self.config.local_model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.local_model_name,
                torch_dtype=torch.float16,
                device_map="auto",
            )
    
    def generate_svg(self, image: Image.Image, prompt: str) -> str:
        """Generate SVG using local model."""
        self._load_model()
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": f"{AnthropicVLM.SYSTEM_PROMPT}\n\nGenerate SVG for: {prompt}"}
                ]
            }
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], return_tensors="pt").to(self.config.local_device)
        
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_tokens,
                do_sample=True,
                temperature=self.config.temperature,
            )
        
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        return SVGValidator.extract_svg(response) or ""
    
    def critique_svg(
        self,
        original_image: Image.Image,
        rendered_svg: Image.Image,
        current_svg: str,
    ) -> Tuple[str, str]:
        """Critique using local model."""
        self._load_model()
        
        # Combine images side by side
        combined = Image.new('RGB', (original_image.width * 2, original_image.height))
        combined.paste(original_image, (0, 0))
        combined.paste(rendered_svg, (original_image.width, 0))
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": combined},
                    {"type": "text", "text": f"Left: original, Right: SVG render.\n{current_svg}\n\n{AnthropicVLM.CRITIQUE_PROMPT}"}
                ]
            }
        ]
        
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[combined], return_tensors="pt").to(self.config.local_device)
        
        with torch.inference_mode():
            outputs = self.model.generate(**inputs, max_new_tokens=self.config.max_tokens)
        
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        corrected_svg = SVGValidator.extract_svg(response) or current_svg
        return "", corrected_svg


def create_vlm(config: VLMConfig) -> VLMCodeGenerator:
    """Factory function to create VLM based on provider."""
    if config.provider == "anthropic":
        return AnthropicVLM(config)
    elif config.provider == "openai":
        return OpenAIVLM(config)
    elif config.provider == "local":
        return LocalVLM(config)
    else:
        raise ValueError(f"Unknown VLM provider: {config.provider}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class DiffuSVGPipeline:
    """Complete DiffuSVG pipeline."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        
        # Initialize components (lazy loading)
        self._diffusion = None
        self._vlm = None
        self._metrics = None
    
    @property
    def diffusion(self) -> SVGFriendlyDiffusion:
        if self._diffusion is None:
            self._diffusion = SVGFriendlyDiffusion(self.config.diffusion)
        return self._diffusion
    
    @property
    def vlm(self) -> VLMCodeGenerator:
        if self._vlm is None:
            self._vlm = create_vlm(self.config.vlm)
        return self._vlm
    
    @property
    def metrics(self) -> SVGMetrics:
        if self._metrics is None:
            self._metrics = SVGMetrics(self.config.diffusion.device)
        return self._metrics
    
    def generate(
        self,
        prompt: str,
        seed: Optional[int] = None,
        return_intermediate: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate SVG from text prompt.
        
        Args:
            prompt: Text description of desired SVG
            seed: Random seed for reproducibility
            return_intermediate: If True, return dict with intermediate results
        
        Returns:
            SVG code string, or dict with intermediate results if requested
        """
        logger.info(f"Generating SVG for: {prompt}")
        
        # Phase 1: Generate SVG-friendly image
        logger.info("Phase 1: Generating SVG-friendly image...")
        images = self.diffusion.generate(prompt, num_images=1, seed=seed)
        diffusion_image = images[0]
        
        # Phase 2: Generate SVG code via VLM
        logger.info("Phase 2: Generating SVG code via VLM...")
        raw_response = self.vlm.generate_svg(diffusion_image, prompt)
        svg_code = SVGValidator.extract_svg(raw_response)
        
        if svg_code is None:
            logger.error("Failed to extract SVG from VLM response")
            svg_code = self._fallback_svg(prompt)
        
        # Attempt repair if invalid
        if not SVGValidator.validate_svg(svg_code):
            logger.warning("Invalid SVG, attempting repair...")
            svg_code = SVGValidator.repair_svg(svg_code)
        
        # Phase 3: Iterative refinement
        logger.info("Phase 3: Iterative refinement...")
        svg_code, refinement_history = self._refine(diffusion_image, svg_code, prompt)
        
        if return_intermediate:
            return {
                "svg": svg_code,
                "diffusion_image": diffusion_image,
                "refinement_history": refinement_history,
                "metrics": self.metrics.compute_all(svg_code, diffusion_image, prompt),
            }
        
        return svg_code
    
    def _refine(
        self,
        original_image: Image.Image,
        svg_code: str,
        prompt: str,
    ) -> Tuple[str, List[Dict]]:
        """Iteratively refine SVG using VLM feedback."""
        history = []
        
        for iteration in range(self.config.refinement.max_iterations):
            # Render current SVG
            rendered = SVGValidator.render_svg(svg_code, self.config.refinement.render_size)
            
            if rendered is None:
                logger.warning(f"Iteration {iteration}: Failed to render SVG")
                break
            
            # Compute similarity
            dino_score = self.metrics.dino_similarity(original_image, rendered)
            clip_score = self.metrics.clip_score(rendered, prompt)
            
            logger.info(f"Iteration {iteration}: DINO={dino_score:.3f}, CLIP={clip_score:.3f}")
            
            history.append({
                "iteration": iteration,
                "dino_score": dino_score,
                "clip_score": clip_score,
                "svg": svg_code,
            })
            
            # Check convergence
            if dino_score >= self.config.refinement.dino_threshold:
                logger.info("Converged! DINO threshold met.")
                break
            
            # Get critique and refinement
            issues, refined_svg = self.vlm.critique_svg(original_image, rendered, svg_code)
            
            if issues:
                logger.info(f"Issues found: {issues[:100]}...")
            
            # Validate refined SVG
            if SVGValidator.validate_svg(refined_svg):
                svg_code = refined_svg
            else:
                logger.warning("Refined SVG invalid, keeping previous version")
        
        return svg_code, history
    
    def _fallback_svg(self, prompt: str) -> str:
        """Generate a simple fallback SVG."""
        return f'''<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="180" height="180" fill="#f0f0f0" stroke="#ccc"/>
  <text x="100" y="100" text-anchor="middle" font-size="12" fill="#666">{prompt[:20]}</text>
</svg>'''
    
    def batch_generate(
        self,
        prompts: List[str],
        output_dir: str,
        seeds: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Generate SVGs for multiple prompts."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for i, prompt in enumerate(prompts):
            seed = seeds[i] if seeds else None
            
            logger.info(f"Processing {i+1}/{len(prompts)}: {prompt}")
            
            try:
                result = self.generate(prompt, seed=seed, return_intermediate=True)
                
                # Save SVG
                svg_path = output_path / f"{i:04d}.svg"
                with open(svg_path, 'w') as f:
                    f.write(result["svg"])
                
                # Save diffusion image
                img_path = output_path / f"{i:04d}_diffusion.png"
                result["diffusion_image"].save(img_path)
                
                # Save rendered SVG
                rendered = SVGValidator.render_svg(result["svg"])
                if rendered:
                    rendered.save(output_path / f"{i:04d}_rendered.png")
                
                results.append({
                    "prompt": prompt,
                    "svg_path": str(svg_path),
                    "metrics": result["metrics"],
                    "success": True,
                })
                
            except Exception as e:
                logger.error(f"Failed to process prompt: {e}")
                results.append({
                    "prompt": prompt,
                    "error": str(e),
                    "success": False,
                })
        
        # Save results summary
        with open(output_path / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    def train_lora(self, dataset_path: str):
        """Train LoRA adapter for vector-style generation."""
        self.diffusion.train_lora(dataset_path, self.config.training)


# =============================================================================
# EVALUATION
# =============================================================================

class SVGEvaluator:
    """Comprehensive SVG evaluation."""
    
    def __init__(self, device: str = "cuda"):
        self.metrics = SVGMetrics(device)
    
    def evaluate_batch(
        self,
        svg_codes: List[str],
        prompts: List[str],
        reference_images: Optional[List[Image.Image]] = None,
    ) -> Dict[str, float]:
        """Evaluate a batch of SVGs."""
        results = {
            "clip_scores": [],
            "dino_scores": [],
            "validity_rate": 0.0,
            "avg_paths": 0.0,
            "avg_elements": 0.0,
        }
        
        valid_count = 0
        total_paths = 0
        total_elements = 0
        
        for i, (svg, prompt) in enumerate(zip(svg_codes, prompts)):
            ref_img = reference_images[i] if reference_images else None
            
            # Render SVG
            rendered = SVGValidator.render_svg(svg)
            
            if rendered is None:
                continue
            
            valid_count += 1
            
            # CLIP score
            clip_score = self.metrics.clip_score(rendered, prompt)
            results["clip_scores"].append(clip_score)
            
            # DINO score (if reference available)
            if ref_img:
                dino_score = self.metrics.dino_similarity(ref_img, rendered)
                results["dino_scores"].append(dino_score)
            
            # Count elements
            paths = svg.count('<path')
            elements = len(re.findall(r'<(rect|circle|ellipse|polygon|path|line)', svg))
            total_paths += paths
            total_elements += elements
        
        # Compute averages
        n = len(svg_codes)
        results["validity_rate"] = valid_count / n if n > 0 else 0.0
        results["avg_clip"] = np.mean(results["clip_scores"]) if results["clip_scores"] else 0.0
        results["avg_dino"] = np.mean(results["dino_scores"]) if results["dino_scores"] else 0.0
        results["avg_paths"] = total_paths / valid_count if valid_count > 0 else 0.0
        results["avg_elements"] = total_elements / valid_count if valid_count > 0 else 0.0
        
        return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="DiffuSVG: SVG Generation Pipeline")
    
    # Mode selection
    parser.add_argument("--mode", choices=["generate", "batch", "train", "evaluate"],
                       default="generate", help="Operation mode")
    
    # Generation arguments
    parser.add_argument("--prompt", type=str, help="Text prompt for SVG generation")
    parser.add_argument("--output", type=str, default="output.svg", help="Output SVG file")
    parser.add_argument("--seed", type=int, help="Random seed")
    
    # Batch arguments
    parser.add_argument("--input", type=str, help="Input file with prompts (one per line)")
    parser.add_argument("--output_dir", type=str, default="./outputs", help="Output directory")
    
    # Training arguments
    parser.add_argument("--dataset", type=str, help="Dataset path for LoRA training")
    parser.add_argument("--lora_output", type=str, default="./vector_lora", help="LoRA output directory")
    
    # Model arguments
    parser.add_argument("--diffusion_model", type=str, 
                       default="stabilityai/stable-diffusion-xl-base-1.0",
                       help="Diffusion model name")
    parser.add_argument("--lora_path", type=str, help="Path to LoRA weights")
    parser.add_argument("--vlm_provider", choices=["anthropic", "openai", "local"],
                       default="anthropic", help="VLM provider")
    parser.add_argument("--vlm_model", type=str, help="VLM model name")
    
    # Other arguments
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--no_refine", action="store_true", help="Skip refinement loop")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build configuration
    config = PipelineConfig()
    config.diffusion.model_name = args.diffusion_model
    config.diffusion.device = args.device
    config.diffusion.lora_path = args.lora_path
    config.vlm.provider = args.vlm_provider
    if args.vlm_model:
        config.vlm.model_name = args.vlm_model
    config.training.output_dir = args.lora_output
    
    if args.no_refine:
        config.refinement.max_iterations = 0
    
    # Create pipeline
    pipeline = DiffuSVGPipeline(config)
    
    # Execute based on mode
    if args.mode == "generate":
        if not args.prompt:
            parser.error("--prompt required for generate mode")
        
        result = pipeline.generate(args.prompt, seed=args.seed, return_intermediate=True)
        
        # Save SVG
        with open(args.output, 'w') as f:
            f.write(result["svg"])
        
        logger.info(f"SVG saved to {args.output}")
        logger.info(f"Metrics: {result['metrics']}")
        
        # Save diffusion image
        img_path = args.output.replace('.svg', '_diffusion.png')
        result["diffusion_image"].save(img_path)
        logger.info(f"Diffusion image saved to {img_path}")
        
    elif args.mode == "batch":
        if not args.input:
            parser.error("--input required for batch mode")
        
        with open(args.input) as f:
            prompts = [line.strip() for line in f if line.strip()]
        
        results = pipeline.batch_generate(prompts, args.output_dir)
        
        # Summary
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        logger.info(f"Batch complete: {success_rate*100:.1f}% success rate")
        
    elif args.mode == "train":
        if not args.dataset:
            parser.error("--dataset required for train mode")
        
        pipeline.train_lora(args.dataset)
        
    elif args.mode == "evaluate":
        if not args.input:
            parser.error("--input required for evaluate mode")
        
        # Load SVGs and prompts from directory
        input_path = Path(args.input)
        svg_files = sorted(input_path.glob("*.svg"))
        
        svg_codes = []
        prompts = []
        
        for svg_file in svg_files:
            with open(svg_file) as f:
                svg_codes.append(f.read())
            
            # Try to load prompt from companion file
            prompt_file = svg_file.with_suffix('.txt')
            if prompt_file.exists():
                with open(prompt_file) as f:
                    prompts.append(f.read().strip())
            else:
                prompts.append(svg_file.stem)
        
        evaluator = SVGEvaluator(args.device)
        results = evaluator.evaluate_batch(svg_codes, prompts)
        
        print("\n=== Evaluation Results ===")
        print(f"Validity Rate: {results['validity_rate']*100:.1f}%")
        print(f"Average CLIP Score: {results['avg_clip']:.3f}")
        print(f"Average DINO Score: {results['avg_dino']:.3f}")
        print(f"Average Paths: {results['avg_paths']:.1f}")
        print(f"Average Elements: {results['avg_elements']:.1f}")


# =============================================================================
# QUICK START FUNCTIONS
# =============================================================================

def quick_generate(prompt: str, output_path: str = "output.svg") -> str:
    """Quick function for simple SVG generation."""
    config = PipelineConfig()
    pipeline = DiffuSVGPipeline(config)
    
    svg_code = pipeline.generate(prompt)
    
    with open(output_path, 'w') as f:
        f.write(svg_code)
    
    return svg_code


def demo():
    """Run a quick demo."""
    print("=" * 60)
    print("DiffuSVG Demo")
    print("=" * 60)
    
    prompts = [
        "a red apple",
        "a yellow sun with rays",
        "a blue house with red roof",
    ]
    
    config = PipelineConfig()
    # Use smaller model for demo
    config.diffusion.num_inference_steps = 20
    config.refinement.max_iterations = 2
    
    pipeline = DiffuSVGPipeline(config)
    
    for i, prompt in enumerate(prompts):
        print(f"\n[{i+1}/{len(prompts)}] Generating: {prompt}")
        
        result = pipeline.generate(prompt, return_intermediate=True)
        
        output_file = f"demo_{i}.svg"
        with open(output_file, 'w') as f:
            f.write(result["svg"])
        
        print(f"  Saved to: {output_file}")
        print(f"  CLIP Score: {result['metrics'].get('clip_score', 'N/A'):.3f}")
        print(f"  DINO Score: {result['metrics'].get('dino_score', 'N/A'):.3f}")
        print(f"  Elements: {result['metrics'].get('element_count', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
