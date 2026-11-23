import csv
import json
import time
from pathlib import Path

from solver import ShipPlacementSolver
from validation import validate_variant


BASE_DIR = Path(__file__).resolve().parent


def load_variant():
    data = json.loads((BASE_DIR / "variant04.json").read_text(encoding="utf-8"))
    size, ships, reefs = validate_variant(data)
    return size, ships, reefs


def ga_experiments(size, ships, reefs):
    rows = []
    for population in [30, 60, 90]:
        for mutation in [0.05, 0.15, 0.25]:
            successes = 0
            generations_to_solution = []
            for run in range(5):
                solver = ShipPlacementSolver(size, ships, reefs, seed=1000 + population + run * 10)
                result = solver.run_ga(population_size=population, generations=120,
                                       crossover_rate=0.9, mutation_rate=mutation, elitism=4)
                if result["solved"]:
                    successes += 1
                    generations_to_solution.append(len(result["history"]))
            average = (sum(generations_to_solution) / len(generations_to_solution)
                       if generations_to_solution else 0.0)
            rows.append({"population": population, "mutation": mutation,
                         "success_rate": successes / 5,
                         "average_generations": average})
    return rows


def sa_experiments(size, ships, reefs):
    rows = []
    for alpha in [0.995, 0.998, 0.999]:
        successes = 0
        iterations_to_solution = []
        for run in range(5):
            solver = ShipPlacementSolver(size, ships, reefs, seed=2000 + run)
            result = solver.run_sa(max_iterations=3000, initial_temperature=50,
                                   final_temperature=0.1, alpha=alpha)
            if result["solved"]:
                successes += 1
                iterations_to_solution.append(result["history"][-1]["iteration"])
        average = (sum(iterations_to_solution) / len(iterations_to_solution)
                   if iterations_to_solution else 0.0)
        rows.append({"alpha": alpha, "success_rate": successes / 5,
                     "average_iterations": average})
    return rows


def comparison_experiment(size, ships, reefs):
    ga_runs = []
    sa_runs = []
    for run in range(10):
        start = time.perf_counter()
        ga_solver = ShipPlacementSolver(size, ships, reefs, seed=3000 + run)
        ga_result = ga_solver.run_ga(population_size=60, generations=120,
                                     crossover_rate=0.9, mutation_rate=0.15, elitism=4)
        ga_runs.append((ga_result["solved"], time.perf_counter() - start,
                        ga_result["fitness_evaluations"]))

        start = time.perf_counter()
        sa_solver = ShipPlacementSolver(size, ships, reefs, seed=4000 + run)
        sa_result = sa_solver.run_sa(max_iterations=3000, initial_temperature=50,
                                     final_temperature=0.1)
        sa_runs.append((sa_result["solved"], time.perf_counter() - start,
                        sa_result["fitness_evaluations"]))
    return ga_runs, sa_runs


def write_csv(filename, fieldnames, rows):
    with (BASE_DIR / filename).open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_table(headers, rows):
    print("  ".join(headers))
    for row in rows:
        print("  ".join(str(row[header]) for header in headers))


def main():
    size, ships, reefs = load_variant()
    ga_rows = ga_experiments(size, ships, reefs)
    write_csv("ga_experiment.csv",
              ["population", "mutation", "success_rate", "average_generations"], ga_rows)
    print("GA: population/mutation")
    print_table(["population", "mutation", "success_rate", "average_generations"], ga_rows)

    sa_rows = sa_experiments(size, ships, reefs)
    write_csv("sa_experiment.csv",
              ["alpha", "success_rate", "average_iterations"], sa_rows)
    print("\nSA: cooling alpha")
    print_table(["alpha", "success_rate", "average_iterations"], sa_rows)

    ga_runs, sa_runs = comparison_experiment(size, ships, reefs)
    comparison = []
    for algorithm, runs in (("GA", ga_runs), ("SA", sa_runs)):
        comparison.append({
            "algorithm": algorithm,
            "success_rate": sum(1 for solved, _, _ in runs if solved) / len(runs),
            "average_time": sum(duration for _, duration, _ in runs) / len(runs),
            "average_fitness_evaluations":
                sum(evaluations for _, _, evaluations in runs) / len(runs),
        })
    write_csv("ga_sa_comparison.csv",
              ["algorithm", "success_rate", "average_time",
               "average_fitness_evaluations"], comparison)
    print("\nGA vs SA")
    print_table(["algorithm", "success_rate", "average_time",
                 "average_fitness_evaluations"], comparison)


if __name__ == "__main__":
    main()
