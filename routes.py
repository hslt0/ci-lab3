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
            if not isinstance(ga_parameters, dict):
                raise ValueError("Параметр ga має бути JSON-об'єктом.")
            if not isinstance(sa_parameters, dict):
                raise ValueError("Параметр sa має бути JSON-об'єктом.")
            seed = payload.get("seed")
            if seed not in (None, ""):
                if isinstance(seed, bool):
                    raise ValueError("Seed має бути цілим числом.")
                try:
                    seed = int(seed)
                except (TypeError, ValueError):
                    raise ValueError("Seed має бути цілим числом.")
            else:
                seed = None

            if algorithm not in ("ga", "sa", "both"):
                raise ValueError("Параметр algorithm має бути ga, sa або both.")

            def integer_parameter(source, name, minimum, maximum=None):
                value = source.get(name)
                if value is None:
                    return None
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"Параметр {name} має бути цілим числом.")
                if value < minimum or (maximum is not None and value > maximum):
                    if maximum is None:
                        raise ValueError(f"Параметр {name} має бути не менше {minimum}.")
                    raise ValueError(f"Параметр {name} має бути від {minimum} до {maximum}.")
                return value

            def probability_parameter(source, name, default):
                value = source.get(name, default)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"Параметр {name} має бути числом від 0 до 1.")
                value = float(value)
                if value < 0 or value > 1:
                    raise ValueError(f"Параметр {name} має бути числом від 0 до 1.")
                return value

            ga_population = integer_parameter(ga_parameters, "population", 2)
            ga_generations = integer_parameter(ga_parameters, "generations", 1)
            ga_elitism = integer_parameter(ga_parameters, "elitism", 0)
            ga_crossover = probability_parameter(ga_parameters, "crossover", 0.9)
            ga_mutation = probability_parameter(ga_parameters, "mutation", 0.15)
            ga_population = ga_population if ga_population is not None else 60
            ga_generations = ga_generations if ga_generations is not None else 100
            ga_elitism = ga_elitism if ga_elitism is not None else 4
            if ga_elitism > ga_population:
                raise ValueError("Параметр elitism не може перевищувати розмір популяції.")

            sa_iterations = integer_parameter(sa_parameters, "iterations", 1)
            sa_iterations = sa_iterations if sa_iterations is not None else 3000
            initial_temperature = sa_parameters.get("initialTemperature", 50)
            final_temperature = sa_parameters.get("finalTemperature", 0.1)
            alpha = sa_parameters.get("alpha")
            if (isinstance(initial_temperature, bool) or
                    not isinstance(initial_temperature, (int, float)) or
                    initial_temperature <= 0):
                raise ValueError("Початкова температура має бути числом більше 0.")
            if (isinstance(final_temperature, bool) or
                    not isinstance(final_temperature, (int, float)) or
                    final_temperature <= 0):
                raise ValueError("Кінцева температура має бути числом більше 0.")
            initial_temperature = float(initial_temperature)
            final_temperature = float(final_temperature)
            if final_temperature >= initial_temperature:
                raise ValueError("Кінцева температура має бути менше початкової.")
            if alpha is not None:
                if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
                    raise ValueError("Параметр alpha має бути числом більше 0 і менше 1.")
                alpha = float(alpha)
                if alpha <= 0 or alpha >= 1:
                    raise ValueError("Параметр alpha має бути числом більше 0 і менше 1.")

            solver = ShipPlacementSolver(size, ships, reefs, seed)
            response = {
                "variant": {"field_size": size, "ships": ships,
                            "reefs": [[x, y] for x, y in sorted(reefs)]},
                "seed": seed,
            }

            if algorithm in ("ga", "both"):
                response["ga"] = solver.run_ga(
                    population_size=ga_population,
                    generations=ga_generations,
                    crossover_rate=ga_crossover,
                    mutation_rate=ga_mutation,
                    elitism=ga_elitism,
                )

            if algorithm in ("sa", "both"):
                sa_solver = ShipPlacementSolver(
                    size,
                    ships,
                    reefs,
                    None if seed is None else seed + 7919,
                )
                response["sa"] = sa_solver.run_sa(
                    max_iterations=sa_iterations,
                    initial_temperature=initial_temperature,
                    final_temperature=final_temperature,
                    alpha=alpha,
                )

            return jsonify(response)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            return jsonify({"error": str(exc)}), 400
