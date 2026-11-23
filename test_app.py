import json
import unittest
from pathlib import Path

from app import app
from solver import ShipPlacementSolver
from validation import validate_variant


class SolverTests(unittest.TestCase):
    def load_variant(self):
        data = json.loads(Path("variant04.json").read_text(encoding="utf-8"))
        return validate_variant(data)

    def test_variant_uses_xy_coordinates(self):
        size, ships, reefs = validate_variant({
            "field_size": 8,
            "ships": [3, 2, 1],
            "reefs": [[5, 2]],
        })
        solver = ShipPlacementSolver(size, ships, reefs, seed=1)
        self.assertIn((5, 2), solver.reefs)
        self.assertEqual(solver.placement_cells(0, (1, 4, "H")),
                         {(1, 4), (2, 4), (3, 4)})

    def test_rule_checker_orientation(self):
        solver = ShipPlacementSolver(8, [2], set(), seed=1)
        violations = solver.check_placements({0: (0, 0, "X")})
        self.assertTrue(any(v["rule"] == "orientation" for v in violations))

    def test_rule_checker_out_of_bounds(self):
        solver = ShipPlacementSolver(8, [3], set(), seed=1)
        violations = solver.check_placements({0: (7, 7, "H")})
        self.assertTrue(any(v["rule"] == "out_of_bounds" for v in violations))

    def test_rule_checker_reef_overlap(self):
        solver = ShipPlacementSolver(8, [2], {(1, 3)}, seed=1)
        violations = solver.check_placements({0: (1, 3, "H")})
        self.assertTrue(any(v["rule"] == "reef_overlap" for v in violations))

    def test_rule_checker_ship_overlap(self):
        solver = ShipPlacementSolver(8, [2, 2], set(), seed=1)
        violations = solver.check_placements({
            0: (1, 1, "H"),
            1: (1, 1, "V"),
        })
        self.assertTrue(any(v["rule"] == "ship_overlap" for v in violations))

    def test_rule_checker_ship_touching(self):
        solver = ShipPlacementSolver(8, [1, 1], set(), seed=1)
        violations = solver.check_placements({
            0: (2, 2, "H"),
            1: (3, 3, "V"),
        })
        self.assertTrue(any(v["rule"] == "ship_touching" for v in violations))

    def test_fitness_zero_only_for_valid_complete_placement(self):
        solver = ShipPlacementSolver(8, [2, 1], {(7, 7)}, seed=1)
        valid = {0: (0, 0, "H"), 1: (3, 3, "V")}
        self.assertEqual(solver.fitness(valid, []), 0)
        self.assertLess(solver.fitness(valid, [1]), 0)
        invalid = {0: (0, 0, "H"), 1: (1, 1, "V")}
        self.assertLess(solver.fitness(invalid, []), 0)

    def test_sa_places_initially_unplaced_ship(self):
        solver = ShipPlacementSolver(8, [2], set(), seed=7)
        solver.greedy_random_state = lambda: ({}, [0])
        result = solver.run_sa(max_iterations=300)
        self.assertTrue(result["solved"])
        self.assertEqual(result["unplaced"], [])

    def test_ga_solves_variant_with_fixed_seed(self):
        size, ships, reefs = self.load_variant()
        result = ShipPlacementSolver(size, ships, reefs, seed=42).run_ga(
            population_size=60, generations=120,
            crossover_rate=0.9, mutation_rate=0.15, elitism=4,
        )
        self.assertTrue(result["solved"])
        self.assertEqual(result["fitness"], 0)

    def test_sa_solves_variant_with_fixed_seed(self):
        size, ships, reefs = self.load_variant()
        result = ShipPlacementSolver(size, ships, reefs, seed=42).run_sa(
            max_iterations=3000, initial_temperature=50,
            final_temperature=0.1,
        )
        self.assertTrue(result["solved"])
        self.assertEqual(result["fitness"], 0)

    def test_duplicate_reef_and_bool_rejected(self):
        with self.assertRaises(ValueError):
            validate_variant({"field_size": 8, "ships": [2],
                              "reefs": [[1, 2], [1, 2]]})
        with self.assertRaises(ValueError):
            validate_variant({"field_size": True, "ships": [2], "reefs": []})
        with self.assertRaises(ValueError):
            validate_variant({"field_size": 8, "ships": [True], "reefs": []})


class RouteAndParameterTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.variant = json.loads(Path("variant04.json").read_text(encoding="utf-8"))

    def test_api_returns_solved_xy_output(self):
        response = self.client.post("/api/run", json={
            "variant": self.variant,
            "algorithm": "both",
            "seed": 42,
            "ga": {"population": 60, "generations": 120,
                   "crossover": 0.9, "mutation": 0.15, "elitism": 4},
            "sa": {"iterations": 3000, "initialTemperature": 50,
                   "finalTemperature": 0.1},
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ga"]["solved"])
        self.assertTrue(data["sa"]["solved"])
        self.assertEqual(data["ga"]["fitness"], 0)
        self.assertEqual(data["sa"]["fitness"], 0)
        self.assertIn("x", data["ga"]["placements"][0])
        self.assertIn("y", data["ga"]["placements"][0])

    def test_invalid_ga_parameters_return_400(self):
        cases = [
            {"population": 1, "generations": 20},
            {"population": 20, "generations": 0},
            {"population": True, "generations": 20},
            {"population": 20, "generations": 20, "mutation": 1.2},
            {"population": 20, "generations": 20, "elitism": 21},
        ]
        for ga in cases:
            response = self.client.post("/api/run", json={
                "variant": self.variant, "algorithm": "ga", "seed": 42, "ga": ga,
            })
            self.assertEqual(response.status_code, 400)

    def test_invalid_sa_parameters_return_400(self):
        cases = [
            {"iterations": 0},
            {"iterations": True},
            {"iterations": 3000, "initialTemperature": 0,
             "finalTemperature": 0.1},
            {"iterations": 3000, "initialTemperature": 1,
             "finalTemperature": 2},
            {"iterations": 3000, "alpha": 1},
        ]
        for sa in cases:
            response = self.client.post("/api/run", json={
                "variant": self.variant, "algorithm": "sa", "seed": 42, "sa": sa,
            })
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
