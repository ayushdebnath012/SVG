import json
import tempfile
import unittest
from pathlib import Path

from svgpatchlab.core.xml import parse_svg
from svgpatchlab.eval.generation import (
    GenerationCase,
    extract_svg,
    run_checks,
    run_generation_eval,
    summarize,
)
from svgpatchlab.types import ModelResponse

GOOD_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    '<circle cx="5" cy="5" r="4" fill="red"/><text x="1" y="9">200 mm</text></svg>'
)


class FakeModel:
    def __init__(self, replies):
        self.replies = list(replies)

    def generate(self, request):
        text, finish = self.replies.pop(0)
        return ModelResponse(text=text, metadata={"usage": {"prompt_tokens": 10, "completion_tokens": 20}, "finish_reason": finish})


class ExtractTests(unittest.TestCase):
    def test_bare_svg(self):
        self.assertEqual(extract_svg(GOOD_SVG), GOOD_SVG)

    def test_fenced_svg_with_prose(self):
        text = "Here you go:\n```svg\n" + GOOD_SVG + "\n```\nHope this helps."
        self.assertEqual(extract_svg(text), GOOD_SVG)

    def test_no_svg(self):
        self.assertIsNone(extract_svg("I cannot draw that."))

    def test_unclosed_svg_is_not_extracted(self):
        self.assertIsNone(extract_svg('<svg xmlns="x"><circle r="1"/>'))


class CheckTests(unittest.TestCase):
    def test_checks(self):
        root = parse_svg(GOOD_SVG)
        results = run_checks(
            root,
            [
                {"tag": "circle", "min": 1},
                {"tag": "rect", "min": 1},
                {"any_tag": ["circle", "rect"], "min": 1},
                {"text_contains": "200"},
                {"text_contains": "bolt"},
                {"root_attr": "viewBox"},
                {"min_elements": 3},
                {"min_elements": 4},
            ],
        )
        self.assertEqual([r["ok"] for r in results], [True, False, True, True, False, True, True, False])

    def test_number_near(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><text>fc = 159.2 Hz</text>'
               '<text>\u221228.3 MPa</text><text>1,250 N</text><text>x1</text></svg>')
        root = parse_svg(svg)
        results = run_checks(root, [
            {"number_near": 159.15},
            {"number_near": -28.31, "tol": 0.01},
            {"number_near": 1250},
            {"number_near": 300},
            {"number_near": 1, "tol": 0.01},
            {"number_near": [48182172, 48.18], "tol": 0.02},
        ])
        self.assertEqual([r["ok"] for r in results], [True, True, True, False, False, False])
        root2 = parse_svg('<svg xmlns="http://www.w3.org/2000/svg"><text>I = 48.2 x 10^6 mm4</text></svg>')
        self.assertTrue(run_checks(root2, [{"number_near": [48182172, 48.18]}])[0]["ok"])

    def test_unknown_check_rejected(self):
        with self.assertRaises(ValueError):
            run_checks(parse_svg(GOOD_SVG), [{"bogus": 1}])


class RunTests(unittest.TestCase):
    def test_failure_classification_and_outputs(self):
        cases = [GenerationCase(id=f"c{i}", prompt="p", checks=[{"tag": "circle", "min": 1}]) for i in range(5)]
        model = FakeModel(
            [
                (GOOD_SVG, "stop"),
                ("no drawing for you", "stop"),
                ("<svg xmlns='http://www.w3.org/2000/svg'><circle", "length"),
                ('<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"></svg>', "stop"),
                ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><rect width="1" height="1"/></svg>', "stop"),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_generation_eval(model, cases, tmp, render=False, price_in_per_m=10, price_out_per_m=50, log=lambda *_: None)
            records = [json.loads(line) for line in (Path(tmp) / "results.jsonl").read_text().splitlines()]
            self.assertTrue((Path(tmp) / "index.html").exists())
            self.assertTrue((Path(tmp) / "outputs" / "c0-0.svg").exists())
            self.assertFalse((Path(tmp) / "outputs" / "c1-0.svg").exists())
        self.assertEqual([r["failure"] for r in records], [None, "no_svg", "truncated", "parse_error", "checks_failed"])
        self.assertEqual(summary["ok"], 1)
        self.assertEqual(summary["failures"]["no_svg"], 1)
        self.assertEqual(summary["failed_ids"], ["c1#0", "c2#0", "c3#0", "c4#0"])
        self.assertAlmostEqual(summary["estimated_cost_usd"], 5 * (10 * 10 + 20 * 50) / 1e6, places=6)

    def test_summarize_empty(self):
        self.assertIsNone(summarize([], 0, 0)["ok_rate"])


if __name__ == "__main__":
    unittest.main()
