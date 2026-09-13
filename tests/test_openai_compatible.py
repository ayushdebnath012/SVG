import json
import unittest
from unittest import mock

from svgpatchlab.models.openai_compatible import OpenAICompatibleAdapter
from svgpatchlab.types import ModelRequest


class OpenAICompatibleTests(unittest.TestCase):
    def _capture_payload(self, config):
        adapter = OpenAICompatibleAdapter(config)
        sent = {}

        def fake_read_json(path, payload):
            sent["path"] = path
            sent["payload"] = payload
            return {"choices": [{"message": {"content": "ok"}, "text": "ok"}], "usage": {}}

        with mock.patch.object(adapter, "_read_json", side_effect=fake_read_json):
            adapter.generate(ModelRequest(prompt="hi"))
        return sent

    def test_temperature_sent_by_default(self):
        sent = self._capture_payload({"model": "m"})
        self.assertEqual(sent["payload"]["temperature"], 0.0)

    def test_null_temperature_omits_field(self):
        sent = self._capture_payload({"model": "gpt-6-astra", "temperature": None})
        self.assertNotIn("temperature", sent["payload"])
        self.assertNotIn("top_p", sent["payload"])
        self.assertEqual(sent["payload"]["model"], "gpt-6-astra")

    def test_null_temperature_omits_field_on_completions(self):
        sent = self._capture_payload({"model": "m", "temperature": None, "endpoint": "completions"})
        self.assertEqual(sent["path"], "completions")
        self.assertNotIn("temperature", sent["payload"])

    def test_max_tokens_param_default(self):
        sent = self._capture_payload({"model": "m"})
        self.assertEqual(sent["payload"]["max_tokens"], 512)
        self.assertNotIn("max_completion_tokens", sent["payload"])

    def test_max_completion_tokens_for_reasoning_models(self):
        sent = self._capture_payload(
            {"model": "gpt-6-astra", "temperature": None, "max_tokens_param": "max_completion_tokens", "max_tokens": 64}
        )
        self.assertEqual(sent["payload"]["max_completion_tokens"], 64)
        self.assertNotIn("max_tokens", sent["payload"])

    def test_unknown_max_tokens_param_rejected(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleAdapter({"model": "m", "max_tokens_param": "bogus"})

    def test_api_key_env_becomes_bearer_header(self):
        with mock.patch.dict("os.environ", {"EXPLABS_API_KEY": "xpl_test"}):
            adapter = OpenAICompatibleAdapter(
                {"model": "m", "base_url": "https://api.experientiallabs.ai/v1", "api_key_env": "EXPLABS_API_KEY"}
            )
        self.assertEqual(adapter._headers()["Authorization"], "Bearer xpl_test")


if __name__ == "__main__":
    unittest.main()
