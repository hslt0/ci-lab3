import csv
import json
import time
from pathlib import Path

from solver import ShipPlacementSolver
from validation import validate_variant


BASE_DIR = Path(__file__).resolve().parent
GA_RUNS = 5
SA_RUNS = 5
COMPARISON_RUNS = 10
DEFAULT_RATE_RUNS = 20


def load_variant(filename):
    data = json.loads((BASE_DIR / filename).read_text(encoding="utf-8"))
    size, ships, reefs = validate_variant(data)
    return size, ships, reefs


def run_ga(size, ships, reefs, seed, population=60, mutation=0.15):
    solver = ShipPlacementSolver(size, ships, reefs, seed=seed)
    started = time.perf_counter()
    result = solver.run_ga(
        population_size=population,
        generations=120,
        crossover_rate=0.9,
        mutation_rate=mutation,
        elitism=4,
    )
    return {
        "solved": result["solved"],
        "steps": len(result["history"]),
        "duration": time.perf_counter() - started,
        "evaluations": result["fitness_evaluations"],
    }


def run_sa(size, ships, reefs, seed, alpha=None):
    effective_alpha = alpha
    if effective_alpha is None:
        effective_alpha = (0.1 / 50) ** (1 / 2999)
    solver = ShipPlacementSolver(size, ships, reefs, seed=seed)
    started = time.perf_counter()
    result = solver.run_sa(
        max_iterations=3000,
        initial_temperature=50,
        final_temperature=0.1,
        alpha=alpha,
    )
    return {
        "solved": result["solved"],
        "steps": result["history"][-1]["iteration"],
        "duration": time.perf_counter() - started,
        "evaluations": result["fitness_evaluations"],
        "terminal_temperature": 50 * effective_alpha **
        (result["history"][-1]["iteration"] - 1),
    }


def ga_experiments(size, ships, reefs):
    rows = []
    for population in (20, 40, 80):
        for mutation in (0.02, 0.1, 0.3):
            results = [
                run_ga(size, ships, reefs, 1000 + run, population, mutation)
                for run in range(GA_RUNS)
            ]
            successful = [item["steps"] for item in results if item["solved"]]
            rows.append({
                "population": population,
                "mutation": mutation,
                "success_rate": len(successful) / GA_RUNS,
                "successful_runs": len(successful),
                "average_generations_to_solution":
                    round(sum(successful) / len(successful), 2) if successful else None,
            })
    return rows


def sa_experiments(size, ships, reefs):
    rows = []
    for alpha in (0.990, 0.995, 0.999):
        results = [
            run_sa(size, ships, reefs, 2000 + run, alpha)
            for run in range(SA_RUNS)
        ]
        successful = [item["steps"] for item in results if item["solved"]]
        rows.append({
            "alpha": alpha,
            "success_rate": len(successful) / SA_RUNS,
            "successful_runs": len(successful),
            "average_iterations_to_solution":
                round(sum(successful) / len(successful), 2) if successful else None,
            "average_terminal_temperature":
                sum(item["terminal_temperature"] for item in results) / SA_RUNS,
            "temperature_at_max_iterations": 50 * alpha ** 2999,
        })
    return rows


def default_runs(size, ships, reefs, runs, seed_base, sa_seed_base=None):
    if sa_seed_base is None:
        sa_seed_base = seed_base + 1000
    results = {"GA": [], "SA": []}
    for run in range(runs):
        results["GA"].append(run_ga(size, ships, reefs, seed_base + run))
        results["SA"].append(run_sa(size, ships, reefs, sa_seed_base + run))
    return results


def comparison_rows(results):
    rows = []
    for algorithm, runs in results.items():
        successful = [item for item in runs if item["solved"]]
        all_evaluations = sum(item["evaluations"] for item in runs)
        rows.append({
            "algorithm": algorithm,
            "runs": len(runs),
            "successful_runs": len(successful),
            "success_rate": len(successful) / len(runs),
            "average_time_all_runs":
                round(sum(item["duration"] for item in runs) / len(runs), 6),
            "average_time_successful_runs":
                round(sum(item["duration"] for item in successful) / len(successful), 6)
                if successful else None,
            "average_fitness_evaluations_successful":
                round(sum(item["evaluations"] for item in successful) / len(successful), 2)
                if successful else None,
            "average_fitness_evaluations_all_runs":
                round(all_evaluations / len(runs), 2),
            "total_fitness_evaluations_all_runs": all_evaluations,
        })
    return rows


def write_csv(filename, fieldnames, rows):
    with (BASE_DIR / filename).open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_table(headers, rows):
    print("  ".join(headers))
    for row in rows:
        print("  ".join("—" if row[header] is None else str(row[header])
                        for header in headers))


def run_suite(label, filenames, size, ships, reefs, default_results=None):
    ga_rows = ga_experiments(size, ships, reefs)
    write_csv(filenames["ga"],
              ["population", "mutation", "success_rate", "successful_runs",
               "average_generations_to_solution"], ga_rows)
    print(f"\n{label} — GA population/mutation")
    print_table(["population", "mutation", "success_rate", "successful_runs",
                 "average_generations_to_solution"], ga_rows)

    sa_rows = sa_experiments(size, ships, reefs)
    write_csv(filenames["sa"],
              ["alpha", "success_rate", "successful_runs",
               "average_iterations_to_solution", "average_terminal_temperature",
               "temperature_at_max_iterations"], sa_rows)
    print(f"\n{label} — SA cooling alpha")
    print_table(["alpha", "success_rate", "successful_runs",
                 "average_iterations_to_solution", "average_terminal_temperature",
                 "temperature_at_max_iterations"], sa_rows)

    if default_results is None:
        default_results = default_runs(
            size, ships, reefs, COMPARISON_RUNS, seed_base=3000,
        )
    comparison = comparison_rows({
        algorithm: runs[:COMPARISON_RUNS]
        for algorithm, runs in default_results.items()
    })
    write_csv(filenames["comparison"],
              ["algorithm", "runs", "successful_runs", "success_rate",
               "average_time_all_runs", "average_time_successful_runs",
               "average_fitness_evaluations_successful",
               "average_fitness_evaluations_all_runs",
               "total_fitness_evaluations_all_runs"], comparison)
    print(f"\n{label} — GA vs SA")
    print_table(["algorithm", "runs", "successful_runs", "success_rate",
                 "average_time_all_runs", "average_time_successful_runs",
                 "average_fitness_evaluations_successful",
                 "average_fitness_evaluations_all_runs",
                 "total_fitness_evaluations_all_runs"], comparison)


def main():
    hard_size, hard_ships, hard_reefs = load_variant("variant_hard.json")
    hard_defaults = default_runs(
        hard_size, hard_ships, hard_reefs, DEFAULT_RATE_RUNS,
        seed_base=7000, sa_seed_base=4000,
    )
    print("\nHard variant default-settings success rates (20 seeds each)")
    for algorithm, results in hard_defaults.items():
        successes = sum(item["solved"] for item in results)
        print(f"{algorithm}: {successes}/{len(results)} ({successes / len(results):.0%})")

    run_suite("Hard variant", {
        "ga": "ga_experiment_hard.csv",
        "sa": "sa_experiment_hard.csv",
        "comparison": "ga_sa_comparison_hard.csv",
    }, hard_size, hard_ships, hard_reefs, hard_defaults)

    base_size, base_ships, base_reefs = load_variant("variant04.json")
    run_suite("variant04 baseline", {
        "ga": "ga_experiment.csv",
        "sa": "sa_experiment.csv",
        "comparison": "ga_sa_comparison.csv",
    }, base_size, base_ships, base_reefs)


if __name__ == "__main__":
    main()
