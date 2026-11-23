import unittest

from solver import ShipPlacementSolver
from validation import validate_variant


class SolverTests(unittest.TestCase):
    def test_variant_is_loaded_and_validated(self):
        size, ships, reefs = validate_variant({
            "field_size": 8,
            "ships": [3, 2, 1],
            "reefs": [[0, 0]],
        })
        self.assertEqual(size, 8)
        self.assertEqual(ships, [3, 2, 1])
        self.assertEqual(reefs, {(0, 0)})

    def test_ga_can_place_variant(self):
        import json
        from pathlib import Path
        data = json.loads(Path("variant04.json").read_text(encoding="utf-8"))
        size, ships, reefs = validate_variant(data)
        solver = ShipPlacementSolver(size, ships, reefs, seed=42)
        result = solver.run_ga(population_size=40, generations=50)
        self.assertEqual(len(result["placements"]) + len(result["unplaced"]), len(ships))

    def test_sa_returns_all_ship_metadata(self):
        solver = ShipPlacementSolver(8, [3, 2, 1], {(0, 0)}, seed=42)
        result = solver.run_sa(max_iterations=500)
        self.assertIn("placements", result)
        self.assertIn("history", result)
        self.assertGreaterEqual(result["fitness"], 0)


if __name__ == "__main__":
    unittest.main()
