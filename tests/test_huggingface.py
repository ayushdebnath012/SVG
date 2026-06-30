from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from svgpatchlab.models.huggingface import HuggingFaceAdapter
from svgpatchlab.types import ModelRequest


class FakeGenerationConfig:
    def __init__(self):
        self.max_length = 20


class FakeBitsAndBytesConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakePipeline:
    def __init__(self):
        self.model = SimpleNamespace(generation_config=FakeGenerationConfig())
        self.calls = []

    def __call__(self, model_input, **kwargs):
        self.calls.append((model_input, kwargs))
        return [{"generated_text": f"{model_input}patched"}]


class HuggingFaceAdapterTests(unittest.TestCase):
    def test_legacy_torch_dtype_config_is_sent_as_dtype(self):
        captured = {}

        def fake_pipeline(task, **kwargs):
            captured["task"] = task
            captured["kwargs"] = kwargs
            captured["pipeline"] = FakePipeline()
            return captured["pipeline"]

        fake_transformers = SimpleNamespace(
            BitsAndBytesConfig=FakeBitsAndBytesConfig,
            GenerationConfig=FakeGenerationConfig,
            pipeline=fake_pipeline,
        )
        fake_torch = SimpleNamespace(float16="float16", bfloat16="bfloat16")

        with patch.dict(
            sys.modules,
            {
                "torch": fake_torch,
                "transformers": fake_transformers,
            },
        ):
            adapter = HuggingFaceAdapter(
                {
                    "model": "example/model",
                    "task": "text-generation",
                    "torch_dtype": "auto",
                    "quantization": "4bit",
                    "max_new_tokens": 128,
                    "do_sample": True,
                    "temperature": 0.4,
                }
            )

        kwargs = captured["kwargs"]
        self.assertNotIn("torch_dtype", kwargs)
        self.assertEqual(kwargs["device_map"], "auto")
        self.assertEqual(kwargs["model_kwargs"]["dtype"], "auto")
        self.assertTrue(kwargs["model_kwargs"]["quantization_config"].kwargs["load_in_4bit"])

        generation_config = adapter.pipeline_kwargs["generation_config"]
        self.assertEqual(generation_config.max_new_tokens, 128)
        self.assertIsNone(generation_config.max_length)
        self.assertTrue(generation_config.do_sample)
        self.assertEqual(generation_config.temperature, 0.4)

        response = adapter.generate(ModelRequest("prompt "))
        self.assertEqual(response.text, "patched")
        _, call_kwargs = captured["pipeline"].calls[-1]
        self.assertIn("generation_config", call_kwargs)
        self.assertFalse(call_kwargs["clean_up_tokenization_spaces"])
        self.assertNotIn("max_new_tokens", call_kwargs)
        self.assertNotIn("do_sample", call_kwargs)


if __name__ == "__main__":
    unittest.main()
