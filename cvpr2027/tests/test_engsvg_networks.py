import random
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import engsvg_networks as N  # noqa: E402


def _strip_ids(svg):
    return re.sub(r'\sid="[^"]*"', "", svg)


def _wrap(svg, transform="translate(13 7) scale(1.5)"):
    head, rest = svg.split(">", 1)
    body, tail = rest.rsplit("</svg>", 1)
    return f'{head}><g transform="{transform}">{body}</g></svg>{tail}'


def _shuffle(svg, seed=3):
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(svg)
    rng = random.Random(seed)
    for element in root.iter():
        children = list(element)
        rng.shuffle(children)
        for child in children:
            element.remove(child)
        element.extend(children)
    return ET.tostring(root, encoding="unicode")


def _resistor(name, value, x, y1, y2):
    """Vertical resistor between (x, y1) and (x, y2) with its body centred between them."""
    mid = (y1 + y2) / 2
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{mid - 28}"/>'
            f'<rect x="{x - 10}" y="{mid - 28}" width="20" height="56" fill="#fff2cc"/>'
            f'<line x1="{x}" y1="{mid + 28}" x2="{x}" y2="{y2}"/>'
            f'<text x="{x + 16}" y="{mid + 5}">{name} {value} Ω</text>')


def _hand_circuit(crossing_dot):
    # V1 (12 V, + at top) on the left; R1 and R2 tee into single long top and bottom wires;
    # R3's top lead crosses the top wire at (400, 100) and only joins it if a dot is drawn there.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" stroke="#172b4d" stroke-width="3">',
             '<line x1="100" y1="100" x2="500" y2="100"/>', '<line x1="100" y1="300" x2="500" y2="300"/>',
             '<line x1="100" y1="100" x2="100" y2="178"/>', '<circle cx="100" cy="200" r="22" fill="white"/>',
             '<line x1="100" y1="222" x2="100" y2="300"/>',
             '<text x="100" y="195.1" stroke="none">+</text>', '<text x="130" y="205" stroke="none">V1 12 V</text>',
             _resistor("R1", 100, 300, 100, 300), _resistor("R2", 300, 500, 100, 300),
             '<line x1="400" y1="60" x2="400" y2="150"/>',
             '<rect x="390" y="150" width="20" height="56" fill="#fff2cc"/>',
             '<line x1="400" y1="206" x2="400" y2="300"/>', '<text x="416" y="183">R3 60 Ω</text>',
             '<text x="20" y="380">All resistors rated 5 W; supply fuses 2 A</text>']
    if crossing_dot:
        parts.append('<circle cx="400" cy="100" r="5" fill="#172b4d"/>')
    return "".join(parts) + "</svg>"


class NetworkControls(unittest.TestCase):
    def test_analytical_controls(self):
        for row in N.controls():
            self.assertTrue(row["pass"], row)


class RoundTrip(unittest.TestCase):
    def test_generated_designs_and_edits_recover_to_their_models(self):
        rng = random.Random(2)
        for family, (make, edits, render, report, recover, netlist, compare) in N.FAMILIES.items():
            for index in range(15):
                model = make(rng, index)
                for target in [model] + [t for _, t, _ in edits(model, rng)]:
                    result = compare(netlist(target), recover(render(target)))
                    self.assertTrue(result["topology_equal"] and result["physics_equal"], (family, index, result))

    def test_recovery_ignores_ids_order_and_transforms(self):
        rng = random.Random(4)
        for family, (make, _, render, _, recover, netlist, compare) in N.FAMILIES.items():
            for index in range(5):
                model = make(rng, index)
                svg = render(model)
                variants = (_strip_ids(svg), _wrap(svg), _wrap(svg, "scale(4)"), _wrap(svg, "scale(0.25)"),
                            _shuffle(svg), _wrap(_shuffle(_strip_ids(svg)), "translate(-40 90) scale(2.5)"))
                for variant in variants:
                    result = compare(netlist(model), recover(variant))
                    self.assertTrue(result["topology_equal"] and result["physics_equal"], (family, index, result))

    def test_newton_and_hardy_cross_agree_on_generated_networks(self):
        rng = random.Random(9)
        for index in range(15):
            net = N.pipe_netlist(N.pipe_model(rng, index))
            newton, loops = N.solve_pipes(net), N.hardy_cross(net)
            gap = max(abs(newton["pipes"][n]["flow_m3_s"] - loops["flows_m3_s"][n]) for n in newton["pipes"])
            self.assertLess(gap, 1e-9)
            self.assertLess(newton["mass_balance_residual_m3_s"], 1e-12)


class DraftingConventions(unittest.TestCase):
    def test_tees_join_and_undotted_crossings_do_not(self):
        plain = N.solve_circuit(N.recover_circuit(_hand_circuit(crossing_dot=False)))
        self.assertAlmostEqual(plain["sources"]["V1"]["current_A"], 12 / 100 + 12 / 300, places=12)
        self.assertAlmostEqual(plain["resistors"]["R3"]["current_A"], 0.0, places=15)
        dotted = N.solve_circuit(N.recover_circuit(_hand_circuit(crossing_dot=True)))
        self.assertAlmostEqual(dotted["sources"]["V1"]["current_A"], 12 / 100 + 12 / 300 + 12 / 60, places=12)

    def test_polarity_comes_from_the_plus_mark(self):
        # Moving only the '+' mark to the other terminal reverses every resistor current; a lone
        # source still delivers the same (positive) current.
        svg = _hand_circuit(crossing_dot=False)
        flipped = svg.replace('y="195.1" stroke="none">+', 'y="215.1" stroke="none">+')
        self.assertNotEqual(svg, flipped)
        before, after = (N.solve_circuit(N.recover_circuit(item)) for item in (svg, flipped))
        self.assertAlmostEqual(before["resistors"]["R1"]["current_A"], 12 / 100, places=12)
        self.assertAlmostEqual(after["resistors"]["R1"]["current_A"], -12 / 100, places=12)
        self.assertAlmostEqual(after["sources"]["V1"]["current_A"], 12 / 100 + 12 / 300, places=12)

    def test_off_grid_endpoint_breaks_the_connection(self):
        rng = random.Random(1)
        model = N.circuit_model(rng)
        svg = N.render_circuit(model)
        name = next(e["name"] for e in model["edges"] if e["kind"] == "resistor")
        moved = re.sub(rf'(<line id="{name}-a" x1=")([\d.]+)',
                       lambda m: m.group(1) + f"{float(m.group(2)) + 0.01:.6g}", svg)
        self.assertNotEqual(moved, svg)
        result = N.physics_match(moved, "dc_network", model)
        self.assertFalse(result.get("topology_equal", False) and result["physics_equal"], result)

    def test_elbows_are_counted_from_the_drawing(self):
        rng = random.Random(6)
        for index in range(30):
            model = N.pipe_model(rng, index)
            recovered = {p["name"]: p for p in N.recover_pipes(N.render_pipes(model))["pipes"]}
            for pipe in N.pipe_netlist(model)["pipes"]:
                self.assertEqual(recovered[pipe["name"]]["elbows"], pipe["elbows"])
                self.assertAlmostEqual(recovered[pipe["name"]]["minor_K"], 0.9 * pipe["elbows"])

    def test_physics_match_scores_edited_drawings(self):
        rng = random.Random(8)
        model = N.pipe_model(rng)
        _, target, _ = N.pipe_edits(model, rng)[0]
        self.assertTrue(N.physics_match(_strip_ids(N.render_pipes(target)), "pipe_network", target)["physics_equal"])
        self.assertFalse(N.physics_match(N.render_pipes(model), "pipe_network", target)["physics_equal"])


class TrainerPhysicsScore(unittest.TestCase):
    def test_gold_patches_score_and_changed_values_do_not(self):
        import copy
        import json
        import train_crossdomain_svg_patcher as trainer
        from engsvg_network_dataset import _make_row
        rng = random.Random(12)
        for family in N.FAMILIES:
            make, edits = N.FAMILIES[family][:2]
            source = make(rng)
            for index, (instruction, target, kind) in enumerate(edits(source, rng), 1):
                row = _make_row(family, "test", 0, index, source, target, instruction, kind)
                self.assertTrue(trainer.score(row, json.dumps(row["target_patch"]))["physics_equal"])
                patch = copy.deepcopy(row["target_patch"])
                texts = [op for op in patch["operations"] if op["op"] == "set_text" and re.search(r"\d", op["text"])]
                if texts:
                    texts[0]["text"] = re.sub(r"(\d+(?:\.\d+)?)(?!.*\d)",
                                              lambda m: f"{float(m.group(1)) + 1:g}", texts[0]["text"])
                    self.assertFalse(trainer.score(row, json.dumps(patch))["physics_equal"], texts[0])


if __name__ == "__main__":
    unittest.main()
