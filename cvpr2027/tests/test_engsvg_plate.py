import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import engsvg_ir as ir
import engsvg_plate as plate


class UntaggedPlateTests(unittest.TestCase):
    def setUp(self):
        self.reference = plate.example_model()
        self.svg = plate.render(self.reference)

    def test_fixture_has_no_semantic_attributes(self):
        self.assertNotIn("data-", self.svg)
        self.assertIn('transform="translate(12 8)"', self.svg)

    def test_transformed_geometry_and_dimensions_are_recovered(self):
        recovered = plate.import_untagged(self.svg)
        self.assertEqual(ir.engineering_digest(recovered), ir.engineering_digest(self.reference))
        self.assertEqual(recovered["provenance"]["mode"], "detached_untagged_svg")

    def test_geometry_and_manufacturing_checks(self):
        result = plate.check_geometry(plate.import_untagged(self.svg))
        self.assertTrue(result["pass"])
        self.assertEqual(result["minimum_edge_distance_mm"], 20)
        self.assertEqual(result["minimum_ligament_mm"], 120)
        expected = 300 * 200 - 4 * math.pi * 10**2
        self.assertAlmostEqual(result["net_area_mm2"], expected)
        self.assertAlmostEqual(result["volume_mm3"], expected * 10)

    def test_boundary_and_ligament_failures_are_reported(self):
        model = copy.deepcopy(self.reference)
        model["holes"][0]["center_mm"] = [5, 5]
        result = plate.check_geometry(model)
        self.assertFalse(result["pass"])
        self.assertTrue(any("crosses the plate boundary" in item for item in result["violations"]))

    def test_inconsistent_scale_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "inconsistent drawing scales"):
            plate.import_untagged(self.svg.replace(">300 mm<", ">330 mm<"))

    def test_hole_count_disagreement_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "hole count disagrees"):
            plate.import_untagged(self.svg.replace("4x Ø20", "3x Ø20"))

    def test_executable_content_is_rejected(self):
        unsafe = self.svg.replace("</svg>", "<script>alert(1)</script></svg>")
        with self.assertRaises(ValueError):
            plate.import_untagged(unsafe)


if __name__ == "__main__":
    unittest.main()
