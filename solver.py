import copy
import math
import random


SA_LOCAL_MOVE_PROBABILITY = 0.7
# Keep gene preferences meaningful instead of repairing across every candidate.
GA_DECODE_ATTEMPTS = 40


class ShipPlacementSolver:
    def __init__(self, size, ships, reefs, seed=None):
        self.size = size
        self.ships = list(ships)
        # The working convention is (x, y): x is the column and y is the row.
        self.reefs = set(reefs)
        self.rng = random.Random(seed)
        self.ship_indices = sorted(
            range(len(self.ships)),
            key=lambda i: (-self.ships[i], i),
        )
        self.fitness_evaluations = 0

    def candidates(self, ship_index):
        length = self.ships[ship_index]
        result = []
        for y in range(self.size):
            for x in range(self.size):
                if x + length <= self.size:
                    result.append((x, y, "H"))
                if y + length <= self.size:
                    result.append((x, y, "V"))
        return result

    def placement_cells(self, ship_index, placement):
        x, y, direction = placement
        length = self.ships[ship_index]
        if direction == "H":
            return {(x + offset, y) for offset in range(length)}
        return {(x, y + offset) for offset in range(length)}

    def allowed(self, ship_index, placement, occupied):
        cells = self.placement_cells(ship_index, placement)
        if any(cell in self.reefs for cell in cells):
            return False
        if any(cell in occupied for cell in cells):
            return False
        for x, y in cells:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) in occupied:
                        return False
        return True

    def decode(self, chromosome):
        occupied = set()
        placements = {}
        unplaced = []

        for position, ship_index in enumerate(self.ship_indices):
            candidates = self.candidates(ship_index)
            if not candidates:
                unplaced.append(ship_index)
                continue
            start = chromosome[position] % len(candidates)
            selected = None
            for offset in range(min(GA_DECODE_ATTEMPTS, len(candidates))):
                candidate = candidates[(start + offset) % len(candidates)]
                if self.allowed(ship_index, candidate, occupied):
                    selected = candidate
                    break
            if selected is None:
                unplaced.append(ship_index)
            else:
                placements[ship_index] = selected
                occupied.update(self.placement_cells(ship_index, selected))

        return placements, unplaced

    def check_placements(self, placements):
        violations = []

        for ship_index, placement in placements.items():
            if not (isinstance(placement, tuple) and len(placement) == 3):
                violations.append({"rule": "orientation", "ships": [ship_index],
                                   "cells": []})
                continue
            x, y, direction = placement
            if direction not in ("H", "V"):
                violations.append({"rule": "orientation", "ships": [ship_index],
                                   "cells": [[x, y]]})

            cells = self.placement_cells(ship_index, placement)
            outside = [[cx, cy] for cx, cy in sorted(cells)
                       if cx < 0 or cy < 0 or cx >= self.size or cy >= self.size]
            if outside:
                violations.append({"rule": "out_of_bounds", "ships": [ship_index],
                                   "cells": outside})

            reef_cells = [[cx, cy] for cx, cy in sorted(cells) if (cx, cy) in self.reefs]
            if reef_cells:
                violations.append({"rule": "reef_overlap", "ships": [ship_index],
                                   "cells": reef_cells})

        ship_ids = sorted(placements)
        for position, first in enumerate(ship_ids):
            first_cells = self.placement_cells(first, placements[first])
            for second in ship_ids[position + 1:]:
                second_cells = self.placement_cells(second, placements[second])
                overlap = sorted(first_cells & second_cells)
                if overlap:
                    violations.append({
                        "rule": "ship_overlap",
                        "ships": [first, second],
                        "cells": [[x, y] for x, y in overlap],
                    })
                    continue

                touching = sorted({
                    (x, y)
                    for x, y in first_cells
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                    if (x + dx, y + dy) in second_cells
                })
                if touching:
                    violations.append({
                        "rule": "ship_touching",
                        "ships": [first, second],
                        "cells": [[x, y] for x, y in touching],
                    })

        return violations

    def fitness(self, placements, unplaced):
        violations = self.check_placements(placements)
        weights = {
            "orientation": 10,
            "out_of_bounds": 20,
            "reef_overlap": 15,
            "ship_overlap": 25,
            "ship_touching": 20,
        }
        penalty = sum(weights.get(item["rule"], 10) for item in violations)
        penalty += 30 * len(unplaced)
        self.fitness_evaluations += 1
        return -penalty

    def run_ga(self, population_size=60, generations=100, crossover_rate=0.9,
               mutation_rate=0.15, elitism=4):
        population_size = int(population_size)
        if population_size < 2:
            raise ValueError("population_size must be at least 2.")
        generations = max(1, int(generations))
        elitism = min(max(0, int(elitism)), population_size)
        gene_count = len(self.ship_indices)
        population = [
            [self.rng.randrange(self.size * self.size * 2) for _ in range(gene_count)]
            for _ in range(population_size)
        ]

        best_placements = {}
        best_unplaced = list(range(len(self.ships)))
        best_fitness = -math.inf
        history = []
        self.fitness_evaluations = 0

        for generation in range(generations):
            scored = []
            for chromosome in population:
                placements, unplaced = self.decode(chromosome)
                value = self.fitness(placements, unplaced)
                scored.append((value, chromosome, placements, unplaced))

            scored.sort(key=lambda item: item[0], reverse=True)
            current = scored[0]
            if current[0] > best_fitness:
                best_fitness = current[0]
                best_placements = copy.deepcopy(current[2])
                best_unplaced = list(current[3])
            history.append({
                "generation": generation + 1,
                "best": round(best_fitness, 4),
                "average": round(sum(item[0] for item in scored) / len(scored), 4),
            })

            if best_fitness == 0:
                break

            elite_count = min(elitism, population_size)
            next_population = [copy.deepcopy(item[1]) for item in scored[:elite_count]]
            minimum = min(item[0] for item in scored)
            fitnesses = [max(0.0001, item[0] - minimum + 0.0001) for item in scored]
            total_fitness = sum(fitnesses)

            def roulette_parent():
                pick = self.rng.uniform(0, total_fitness)
                cumulative = 0.0
                for index, weight in enumerate(fitnesses):
                    cumulative += weight
                    if cumulative >= pick:
                        return scored[index][1]
                return scored[-1][1]

            while len(next_population) < population_size:
                first = copy.deepcopy(roulette_parent())
                second = copy.deepcopy(roulette_parent())
                child = first
                if self.rng.random() < crossover_rate:
                    point = self.rng.randint(1, gene_count - 1) if gene_count > 1 else 1
                    child = first[:point] + second[point:]
                for position in range(gene_count):
                    if self.rng.random() < mutation_rate:
                        child[position] = self.rng.randrange(self.size * self.size * 2)
                next_population.append(child)

            population = next_population

        violations = self.check_placements(best_placements)
        if best_unplaced:
            violations.extend({
                "rule": "unplaced_ship",
                "ships": [ship_index],
                "length": self.ships[ship_index],
                "cells": [],
            } for ship_index in best_unplaced)

        return {
            "placements": self.serialize_placements(best_placements),
            "unplaced": [self.ships[index] for index in best_unplaced],
            "fitness": best_fitness,
            "solved": best_fitness == 0,
            "violations": violations,
            "fitness_evaluations": self.fitness_evaluations,
            "history": history,
        }

    def serialize_placements(self, placements):
        return [
            {
                "ship": ship_index,
                "length": self.ships[ship_index],
                "x": placements[ship_index][0],
                "y": placements[ship_index][1],
                "direction": placements[ship_index][2],
            }
            for ship_index in sorted(placements)
        ]

    def random_chromosome(self):
        return [self.rng.randrange(self.size * self.size * 2)
                for _ in range(len(self.ship_indices))]

    def neighbour_chromosome(self, chromosome):
        """Change one gene: small shift of the start index or a random new value."""
        neighbour = list(chromosome)
        position = self.rng.randrange(len(neighbour))
        if self.rng.random() < SA_LOCAL_MOVE_PROBABILITY:
            neighbour[position] += self.rng.choice((-1, 1, -self.size, self.size))
            neighbour[position] %= self.size * self.size * 2
        else:
            neighbour[position] = self.rng.randrange(self.size * self.size * 2)
        return neighbour

    def run_sa(self, max_iterations=3000, initial_temperature=50.0,
               final_temperature=0.1, alpha=None):
        """Simulated annealing over the same chromosome as the GA.

        State: gene vector (decoded to a placement by the repairing decoder).
        Energy: E = -fitness = weighted rule violations + unplaced ships (0 = solved).
        Move: change one gene. Acceptance: Metropolis, exp(-dE / T).
        Cooling: T_k = T0 * alpha^k.
        """
        max_iterations = max(1, int(max_iterations))
        initial_temperature = max(0.001, float(initial_temperature))
        final_temperature = max(0.0001, float(final_temperature))
        if alpha is None:
            alpha = (final_temperature / initial_temperature) ** (1 / max(1, max_iterations - 1))
        alpha = float(alpha)

        self.fitness_evaluations = 0
        current = self.random_chromosome()
        current_placements, current_unplaced = self.decode(current)
        current_fitness = self.fitness(current_placements, current_unplaced)
        best = dict(current_placements)
        best_unplaced = list(current_unplaced)
        best_fitness = current_fitness
        history = []
        accepted_window = 0
        iterations_in_window = 0

        for iteration in range(max_iterations):
            iterations_in_window += 1
            temperature = initial_temperature * (alpha ** iteration)
            neighbour = self.neighbour_chromosome(current)
            placements, unplaced = self.decode(neighbour)
            neighbour_fitness = self.fitness(placements, unplaced)
            delta = neighbour_fitness - current_fitness
            if delta >= 0 or self.rng.random() < math.exp(delta / max(temperature, 1e-9)):
                current = neighbour
                current_fitness = neighbour_fitness
                accepted_window += 1
                if current_fitness > best_fitness:
                    best = dict(placements)
                    best_unplaced = list(unplaced)
                    best_fitness = current_fitness

            if (best_fitness == 0 or (iteration + 1) % 30 == 0 or iteration == 0
                    or iteration == max_iterations - 1):
                history.append({
                    "iteration": iteration + 1,
                    "current": round(current_fitness, 4),
                    "best": round(best_fitness, 4),
                    "temperature": round(temperature, 6),
                    "acceptance": round(accepted_window / iterations_in_window, 4),
                })
                accepted_window = 0
                iterations_in_window = 0
            if best_fitness == 0:
                break

        violations = self.check_placements(best)
        if best_unplaced:
            violations.extend({
                "rule": "unplaced_ship",
                "ships": [ship_index],
                "length": self.ships[ship_index],
                "cells": [],
            } for ship_index in best_unplaced)

        return {
            "placements": self.serialize_placements(best),
            "unplaced": [self.ships[index] for index in best_unplaced],
            "fitness": best_fitness,
            "solved": best_fitness == 0,
            "violations": violations,
            "fitness_evaluations": self.fitness_evaluations,
            "history": history,
        }
