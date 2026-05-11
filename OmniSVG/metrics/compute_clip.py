import argparse
import os

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


DEFAULT_CLIP_MODEL = "openai/clip-vit-base-patch32"


def calculate_clip_score(image_path, text_path, model_name=DEFAULT_CLIP_MODEL):
    """Calculate cosine CLIP similarity between an image and a text prompt file."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(model_name).to(device).eval()
    processor = CLIPProcessor.from_pretrained(model_name)

    image = Image.open(image_path).convert("RGB")
    with open(text_path, "r", encoding="utf-8") as f:
        caption = f.read().strip()

    inputs = processor(
        text=[caption],
        images=image,
        return_tensors="pt",
        padding=True,
    ).to(device)

    with torch.no_grad():
        image_features = model.get_image_features(pixel_values=inputs["pixel_values"])
        text_features = model.get_text_features(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
        )
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return (image_features @ text_features.T).item()


def main():
    parser = argparse.ArgumentParser(description="Compute CLIP text-image similarity.")
    parser.add_argument("text_path", help="Path to a text file containing the prompt")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--model", default=DEFAULT_CLIP_MODEL, help="HF CLIP model or local path")
    args = parser.parse_args()

    if not os.path.isfile(args.text_path):
        raise FileNotFoundError(f"Text file does not exist: {args.text_path}")
    if not os.path.isfile(args.image_path):
        raise FileNotFoundError(f"Image file does not exist: {args.image_path}")

    score = calculate_clip_score(args.image_path, args.text_path, args.model)
    print(f"{score:.4f}")


if __name__ == "__main__":
    main()
