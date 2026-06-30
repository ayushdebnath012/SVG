from __future__ import annotations

from typing import Any

from svgpatchlab.types import ModelRequest, ModelResponse

from .base import ModelAdapter


class HuggingFaceAdapter(ModelAdapter):
    """Lazy local Transformers pipeline adapter.

    The adapter is intentionally generic. Switch models by changing `model` and
    `task` in configuration rather than changing experiment code.
    """

    def __init__(self, config: dict[str, Any]):
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError("install svgpatchlab[hf] to use the Hugging Face adapter") from exc

        self.task = str(config.get("task", "text-generation"))
        kwargs: dict[str, Any] = {"model": str(config["model"])}
        for name in ("device", "device_map", "torch_dtype", "trust_remote_code"):
            if name in config:
                kwargs[name] = config[name]
        self.pipeline = pipeline(self.task, **kwargs)
        self.generation = {
            "max_new_tokens": int(config.get("max_new_tokens", 512)),
            "do_sample": bool(config.get("do_sample", False)),
        }
        if self.generation["do_sample"]:
            self.generation["temperature"] = float(config.get("temperature", 0.2))

    def generate(self, request: ModelRequest) -> ModelResponse:
        if self.task == "image-text-to-text":
            content: list[dict[str, str]] = [
                *({"type": "image", "url": image} for image in request.images),
                {"type": "text", "text": request.prompt},
            ]
            model_input: Any = [{"role": "user", "content": content}]
        else:
            model_input = request.prompt
        result = self.pipeline(model_input, **self.generation)
        generated = result[0]["generated_text"]
        if isinstance(generated, list):
            assistant_messages = [
                message for message in generated if message.get("role") == "assistant"
            ]
            text = assistant_messages[-1]["content"] if assistant_messages else str(generated[-1])
        else:
            text = str(generated)
            if self.task == "text-generation" and text.startswith(request.prompt):
                text = text[len(request.prompt) :]
        return ModelResponse(text=text, metadata={"adapter": "huggingface"})
