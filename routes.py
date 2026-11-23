import json
from pathlib import Path

from flask import jsonify, render_template, request

from solver import ShipPlacementSolver
from validation import validate_variant


BASE_DIR = Path(__file__).resolve().parent


def register_routes(app):
    @app.route("/")
    def index():
        default_variant = {}
        variant_path = BASE_DIR / "variant04.json"
        if variant_path.exists():
            default_variant = json.loads(variant_path.read_text(encoding="utf-8"))
        return render_template("index.html", default_variant=default_variant)

    @app.post("/api/run")
    def run():
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Порожній або некоректний JSON-запит."}), 400

        try:
            size, ships, reefs = validate_variant(payload["variant"])
            algorithm = payload.get("algorithm", "both")
            ga_parameters = payload.get("ga", {})
            sa_parameters = payload.get("sa", {})
            seed = payload.get("seed")
            seed = int(seed) if seed not in (None, "") else None

            solver = ShipPlacementSolver(size, ships, reefs, seed)
            response = {
                "variant": {"field_size": size, "ships": ships, "reefs": sorted(reefs)},
                "seed": seed,
            }

            if algorithm in ("ga", "both"):
                response["ga"] = solver.run_ga(
                    population_size=ga_parameters.get("population", 60),
                    generations=ga_parameters.get("generations", 100),
                    crossover_rate=ga_parameters.get("crossover", 0.9),
                    mutation_rate=ga_parameters.get("mutation", 0.15),
                    elitism=ga_parameters.get("elitism", 4),
                )

            if algorithm in ("sa", "both"):
                sa_solver = ShipPlacementSolver(
                    size,
                    ships,
                    reefs,
                    None if seed is None else seed + 7919,
                )
                response["sa"] = sa_solver.run_sa(
                    max_iterations=sa_parameters.get("iterations", 3000),
                    initial_temperature=sa_parameters.get("initialTemperature", 50),
                    final_temperature=sa_parameters.get("finalTemperature", 0.1),
                )

            return jsonify(response)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            return jsonify({"error": str(exc)}), 400
