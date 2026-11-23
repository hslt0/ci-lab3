import json
import random
from pathlib import Path

from solver import ShipPlacementSolver


BASE_DIR = Path(__file__).resolve().parent
FIELD_SIZE = 10
SHIPS = [2] * 15 + [1] * 5
REEF_SEED = 0
REEF_COUNT = 48


def build_variant():
    empty_solver = ShipPlacementSolver(FIELD_SIZE, SHIPS, set(), seed=REEF_SEED)
    planted = {}
    ship_index = 0
    for y in range(0, FIELD_SIZE, 2):
        for x in (0, 3, 6):
            planted[ship_index] = (x, y, "H")
            ship_index += 1
    for y in range(0, FIELD_SIZE, 2):
        planted[ship_index] = (9, y, "H")
        ship_index += 1

    occupied = set()
    for index in empty_solver.ship_indices:
        placement = planted[index]
        if not empty_solver.allowed(index, placement, occupied):
            raise RuntimeError(f"Planted placement for ship {index} is not valid.")
        occupied.update(empty_solver.placement_cells(index, placement))

    available_cells = [
        (x, y)
        for x in range(FIELD_SIZE)
        for y in range(FIELD_SIZE)
        if (x, y) not in occupied
    ]
    random.Random(REEF_SEED).shuffle(available_cells)
    reefs = set(available_cells[:REEF_COUNT])

    final_solver = ShipPlacementSolver(FIELD_SIZE, SHIPS, reefs, seed=REEF_SEED)
    occupied.clear()
    for index in final_solver.ship_indices:
        placement = planted[index]
        if not final_solver.allowed(index, placement, occupied):
            raise RuntimeError(f"Reef placement invalidated ship {index}.")
        occupied.update(final_solver.placement_cells(index, placement))

    return {
        "field_size": FIELD_SIZE,
        "ships": SHIPS,
        "reefs": [[x, y] for x, y in sorted(reefs)],
    }


if __name__ == "__main__":
    variant = build_variant()
    destination = BASE_DIR / "variant_hard.json"
    destination.write_text(
        json.dumps(variant, indent=4) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination.name} with {len(variant['reefs'])} reefs.")
