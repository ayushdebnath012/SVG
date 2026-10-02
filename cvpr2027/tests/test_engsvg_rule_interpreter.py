import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import engsvg_rule_interpreter as rule
import engsvg_detached_importer as detached
import structured_engsvg as core
import structured_engsvg_hard_eval as hard


class QuantityTests(unittest.TestCase):
    def test_canonical_units(self):
        self.assertEqual(rule.length_mm("1.4", "m"), 1400)
        self.assertEqual(rule.length_mm("85", "cm"), 850)
        self.assertEqual(rule.force_N("0.15", "kn"), 150)
        self.assertEqual(rule.modulus_mpa("200", "gpa"), 200000)

    def test_complete_missing_set_is_returned_in_schema_order(self):
        action = rule.interpret("Make a 1200 mm wide, 800 mm tall frame.")
        self.assertEqual(action, {"action": "clarify", "missing": [
            "section_b_mm", "section_h_mm", "E_mpa",
            "vertical_load_N", "horizontal_load_N",
        ]})

    def test_text_request_rebuilds_svg_with_canonical_metadata_and_fem(self):
        request = ("A 1.4 m wide and 85 cm tall table side frame uses a 5 cm by 9 cm "
                   "rectangular section, E 200 GPa, a 1.2 kN downward load and "
                   "0.15 kN rightward load.")
        result, svg = core.process_request(request)
        self.assertEqual(result["design"]["width_mm"], 1400)
        self.assertEqual(result["design"]["horizontal_load_N"], 150)
        self.assertEqual(core.extract_embedded_design(svg)["parameters"], result["design"])
        residual = result["engineering"]["analysis"]["equilibrium_residual_N_Nmm"]
        self.assertLess(max(abs(value) for value in residual), 1e-3)


class CorrectedHardBenchmarkTests(unittest.TestCase):
    def test_prompts_are_not_self_contradictory(self):
        for item in hard.hard_cases():
            self.assertNotIn("Supplied canonical values", item["request"])
            self.assertIn("target", item)

    def test_rule_layer_solves_all_individual_cases(self):
        for item in hard.hard_cases():
            with self.subTest(case=item["id"]):
                action = rule.interpret(item["request"], item["source"])
                self.assertEqual(action, item["target"])
                self.assertEqual(core.execute(item["source"], action), item["expected"])

    def test_rule_layer_solves_all_stateful_rollouts(self):
        for name, initial, steps in hard.trajectories():
            state = initial.copy()
            for index, (request, changes) in enumerate(steps, 1):
                with self.subTest(trajectory=name, step=index):
                    action = rule.interpret(request, state)
                    self.assertEqual(action, {"action": "edit", "changes": changes})
                    state = core.execute(state, action)

    def test_saved_rule_evaluation_is_complete_and_auditable(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            metrics = hard.evaluate_rule(output)
            self.assertEqual(metrics["create"], {"n": 6, "success": 6})
            self.assertEqual(metrics["edit"], {"n": 10, "success": 10})
            self.assertEqual(metrics["clarify"], {"n": 6, "success": 6})
            self.assertEqual(metrics["rollout_steps"], {"n": 9, "success": 9})
            self.assertEqual(metrics["complete_trajectories"], {"n": 3, "success": 3})
            predictions = json.loads((output / "hard-rule-predictions.json").read_text())
            self.assertTrue(all(row["success"] for row in predictions))
            self.assertTrue(all("target" in row and "expected" in row for row in predictions))


class DetachedSvgTests(unittest.TestCase):
    def setUp(self):
        self.design = {
            "width_mm": 1400, "height_mm": 850, "section_b_mm": 50,
            "section_h_mm": 90, "E_mpa": 200000,
            "vertical_load_N": 1200, "horizontal_load_N": 150,
        }
        _, self.svg = core.artifact(self.design)
        self.detached = re.sub(r"<metadata\b[^>]*>.*?</metadata>", "", self.svg,
                               flags=re.DOTALL)

    def test_visible_evidence_recovers_detached_design(self):
        result = detached.import_svg(self.detached)
        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["mode"], "detached_visible_evidence")
        self.assertEqual(result["design"], self.design)
        self.assertTrue(result["topology"]["connected"])

    def test_detached_edit_rebuilds_and_reanalyses(self):
        result, svg = core.process_detached_svg(
            self.detached, "Make it 0.2 m wider and remove the lateral load."
        )
        self.assertEqual(result["edit"]["design"]["width_mm"], 1600)
        self.assertEqual(result["edit"]["design"]["horizontal_load_N"], 0)
        self.assertEqual(core.extract_embedded_design(svg)["parameters"],
                         result["edit"]["design"])

    def test_missing_visible_physics_requests_clarification(self):
        old = re.sub(r"<text data-parameter=.*?</text>", "", self.detached)
        result = detached.import_svg(old)
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["missing"], ["E_mpa", "vertical_load_N", "horizontal_load_N"])
        supplied = {"E_mpa": 200000, "vertical_load_N": 1200, "horizontal_load_N": 150}
        self.assertEqual(detached.import_svg(old, supplied)["design"], self.design)

    def test_conflicting_visible_sections_are_ambiguous(self):
        conflict = self.detached.replace("right: 50 × 90", "right: 60 × 90")
        result = detached.import_svg(conflict)
        self.assertEqual(result["status"], "needs_clarification")
        self.assertTrue(any(item["field"] == "section_b_mm" for item in result["ambiguities"]))

    def test_embedded_metadata_is_preferred(self):
        result = detached.import_svg(self.svg)
        self.assertEqual(result["mode"], "embedded_metadata")
        self.assertEqual(result["design"], self.design)

    def test_external_or_scripted_svg_is_rejected(self):
        unsafe = self.detached.replace("</svg>", '<script>alert(1)</script></svg>')
        with self.assertRaises(ValueError):
            detached.import_svg(unsafe)


if __name__ == "__main__":
    unittest.main()
