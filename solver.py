import copy
import math
import random


class ShipPlacementSolver:
    def __init__(self, size, ships, reefs, seed=None):
        self.size = size
        self.ships = list(ships)
        self.reefs = set(reefs)
        self.rng = random.Random(seed)
        self.ship_indices = sorted(
            range(len(self.ships)),
            key=lambda i: (-self.ships[i], i),
        )

    def candidates(self, ship_index):
        length = self.ships[ship_index]
        result = []
        for row in range(self.size):
            for col in range(self.size):
                if col + length <= self.size:
                    result.append((row, col, "H"))
                if row + length <= self.size:
                    result.append((row, col, "V"))
        return result

    def placement_cells(self, ship_index, placement):
        row, col, direction = placement
        length = self.ships[ship_index]
        if direction == "H":
            return {(row, col + offset) for offset in range(length)}
        return {(row + offset, col) for offset in range(length)}

    def allowed(self, ship_index, placement, occupied):
        cells = self.placement_cells(ship_index, placement)
        if any(cell in self.reefs for cell in cells):
            return False
        if any(cell in occupied for cell in cells):
            return False
        for cell in cells:
            row, col = cell
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (row + dr, col + dc) in occupied:
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
            for offset in range(len(candidates)):
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

    def greedy_random_state(self):
        occupied = set()
        placements = {}
        unplaced = []

        for ship_index in self.ship_indices:
            candidates = self.candidates(ship_index)
            self.rng.shuffle(candidates)
            selected = None
            for candidate in candidates:
                if self.allowed(ship_index, candidate, occupied):
                    selected = candidate
                    break
            if selected is None:
                unplaced.append(ship_index)
            else:
                placements[ship_index] = selected
                occupied.update(self.placement_cells(ship_index, selected))

        return placements, unplaced

    def fitness(self, placements, unplaced):
        placed = len(placements)
        satisfied = 0
        occupied = set()

        for ship_index, placement in placements.items():
            cells = self.placement_cells(ship_index, placement)
            occupied.update(cells)
            if all(0 <= row < self.size and 0 <= col < self.size for row, col in cells):
                satisfied += 1
            if not any(cell in self.reefs for cell in cells):
                satisfied += 1

        if len(occupied) == sum(len(self.placement_cells(i, p)) for i, p in placements.items()):
            satisfied += placed

        return 100 * placed - 100 * len(unplaced) + satisfied + self._boundary_score(placements)

    def _boundary_score(self, placements):
        if not placements:
            return 0.0
        all_cells = set()
        for ship_index, placement in placements.items():
            all_cells.update(self.placement_cells(ship_index, placement))
        rows = [row for row, _ in all_cells]
        cols = [col for _, col in all_cells]
        span = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        return max(0.0, 10.0 - span / (self.size * self.size))

    def run_ga(self, population_size=60, generations=100, crossover_rate=0.9,
               mutation_rate=0.15, elitism=4):
        population_size = max(12, int(population_size))
        generations = max(1, int(generations))
        gene_count = len(self.ship_indices)
        population = [
            [self.rng.randrange(self.size * self.size * 2) for _ in range(gene_count)]
            for _ in range(population_size)
        ]

        best_placements = {}
        best_unplaced = list(range(len(self.ships)))
        best_fitness = -math.inf
        history = []

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

        return {
            "placements": self.serialize_placements(best_placements),
            "unplaced": best_unplaced,
            "fitness": round(best_fitness, 4),
            "history": history,
        }

    def serialize_placements(self, placements):
        return [
            {
                "ship": ship_index,
                "length": self.ships[ship_index],
                "row": placements[ship_index][0],
                "col": placements[ship_index][1],
                "direction": placements[ship_index][2],
            }
            for ship_index in sorted(placements)
        ]

    def run_sa(self, max_iterations=3000, initial_temperature=50.0,
               final_temperature=0.1):
        max_iterations = max(1, int(max_iterations))
        initial_temperature = max(0.001, float(initial_temperature))
        final_temperature = max(0.0001, float(final_temperature))
        if final_temperature >= initial_temperature:
            final_temperature = initial_temperature / 100

        current, unplaced = self.greedy_random_state()
        current_fitness = self.fitness(current, unplaced)
        best = copy.deepcopy(current)
        best_unplaced = list(unplaced)
        best_fitness = current_fitness
        history = []

        for iteration in range(max_iterations):
            progress = iteration / max(1, max_iterations - 1)
            temperature = initial_temperature * (
                (final_temperature / initial_temperature) ** progress
            )
            neighbour = copy.deepcopy(current)
            neighbour_unplaced = list(unplaced)

            movable = list(neighbour.keys())
            if movable:
                ship_index = self.rng.choice(movable)
                occupied = set()
                for other_index, placement in neighbour.items():
                    if other_index != ship_index:
                        occupied.update(self.placement_cells(other_index, placement))

                candidates = self.candidates(ship_index)
                self.rng.shuffle(candidates)
                replaced = False
                for candidate in candidates:
                    if self.allowed(ship_index, candidate, occupied):
                        neighbour[ship_index] = candidate
                        replaced = True
                        break
                if not replaced:
                    neighbour.pop(ship_index, None)
                    neighbour_unplaced.append(ship_index)

            neighbour_fitness = self.fitness(neighbour, neighbour_unplaced)
            delta = neighbour_fitness - current_fitness
            if delta >= 0 or self.rng.random() < math.exp(delta / max(temperature, 1e-9)):
                current = neighbour
                unplaced = neighbour_unplaced
                current_fitness = neighbour_fitness

            if current_fitness > best_fitness:
                best = copy.deepcopy(current)
                best_unplaced = list(unplaced)
                best_fitness = current_fitness

            if (iteration + 1) % max(1, max_iterations // 100) == 0 or iteration == max_iterations - 1:
                history.append({
                    "iteration": iteration + 1,
                    "best": round(best_fitness, 4),
                    "temperature": round(temperature, 6),
                })

        return {
            "placements": self.serialize_placements(best),
            "unplaced": best_unplaced,
            "fitness": round(best_fitness, 4),
            "history": history,
        }
