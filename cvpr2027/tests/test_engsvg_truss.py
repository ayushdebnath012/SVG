import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import engsvg_ir as ir
import engsvg_truss as truss


class CommonIrTests(unittest.TestCase):
    def test_valid_truss_round_trips_and_hashes(self):
        model = truss.example_model()
        self.assertEqual(ir.validate(model), model)
        self.assertEqual(ir.digest(model), ir.digest(copy.deepcopy(model)))
        recovered = truss.import_untagged(truss.render(model))
        self.assertEqual(ir.engineering_digest(model), ir.engineering_digest(recovered))

    def test_invalid_reference_is_rejected(self):
        model = truss.example_model()
        model["members"][0]["a"] = "missing"
        with self.assertRaises(ValueError):
            ir.validate(model)


class UntaggedTrussTests(unittest.TestCase):
    def setUp(self):
        self.reference = truss.example_model()
        self.svg = truss.render(self.reference)

    def test_fixture_has_no_semantic_geometry_tags(self):
        self.assertNotIn("data-member", self.svg)
        self.assertNotIn("data-dimension", self.svg)

    def test_geometry_connectivity_and_engineering_values_are_recovered(self):
        recovered = truss.import_untagged(self.svg)
        self.assertEqual(recovered["nodes"], self.reference["nodes"])
        self.assertEqual({m["id"] for m in recovered["members"]},
                         {m["id"] for m in self.reference["members"]})
        self.assertEqual(recovered["loads"], self.reference["loads"])
        self.assertEqual(recovered["supports"], self.reference["supports"])
        self.assertEqual(recovered["sections"], self.reference["sections"])
        self.assertEqual(recovered["materials"], self.reference["materials"])
        self.assertEqual(recovered["provenance"]["mode"], "detached_untagged_svg")

    def test_different_connected_topology_is_recovered(self):
        model = copy.deepcopy(self.reference)
        model["nodes"]["F"] = [2000, 0]
        names = ("AB", "BF", "FD", "DE", "AC", "BC", "CF", "CD", "CE")
        model["members"] = [{"id": name, "a": name[0], "b": name[1],
                             "section": "bar", "material": "steel"} for name in names]
        model = ir.validate(model)
        recovered = truss.import_untagged(truss.render(model))
        self.assertEqual(ir.engineering_digest(recovered), ir.engineering_digest(model))
        result = truss.solve(recovered)
        self.assertLess(max(abs(x) for x in result["equilibrium_residual_N_Nmm"]), 1e-6)

    def test_fem_equilibrium_and_symmetric_reactions(self):
        result = truss.solve(truss.import_untagged(self.svg))
        self.assertLess(max(abs(x) for x in result["equilibrium_residual_N_Nmm"]), 1e-6)
        self.assertAlmostEqual(result["reactions_N"]["A"][1], 10000, places=6)
        self.assertAlmostEqual(result["reactions_N"]["E"][1], 10000, places=6)
        self.assertLess(result["node_displacements_mm"]["C"][1], 0)

    def test_missing_engineering_annotation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing visible modulus"):
            truss.import_untagged(self.svg.replace("E: 200000 MPa", "material not stated"))

    def test_inconsistent_drawing_scale_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "inconsistent drawing scales"):
            truss.import_untagged(self.svg.replace(">1200 mm<", ">1500 mm<"))

    def test_executable_svg_is_rejected(self):
        unsafe = self.svg.replace("</svg>", "<script>alert(1)</script></svg>")
        with self.assertRaises(ValueError):
            truss.import_untagged(unsafe)


if __name__ == "__main__":
    unittest.main()
