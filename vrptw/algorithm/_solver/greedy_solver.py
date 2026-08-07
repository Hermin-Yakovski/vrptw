from __future__ import annotations

from typing import TYPE_CHECKING

from or_algo import Solver

from ...dimension import *
from ...parameter import *
from .lp_solver.symbol import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey


class GreedySolver(Solver):
    _capacity: float

    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        self._capacity = float('inf') if capacity is None else capacity

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        # Collect all customer IDs except depot (0)
        unvisited: set[int] = {
            c for c, in data[Id][(Customer,)].keys() if c != 0
        }

        current = 0  # depot
        load: float = 0
        time: float = (
            data[Earliest][(Customer,)][(0,)]
            + data[ServiceTime][(Customer,)][(0,)]
        )

        while unvisited:
            # Find nearest feasible customer
            best: int | None = None
            best_dist = float('inf')

            for j in unvisited:
                # Capacity check
                if load + data[Demand][(Customer,)][(j,)] > self._capacity:
                    continue

                # Travel time (Manhattan distance)
                dist = (
                    abs(data[X][(Customer,)][(current,)] - data[X][(Customer,)][(j,)])
                    + abs(data[Y][(Customer,)][(current,)] - data[Y][(Customer,)][(j,)])
                )

                # Arrival time at j
                arrival = time + dist

                # Time window check
                if arrival > data[Latest][(Customer,)][(j,)]:
                    continue

                # Nearest so far
                if dist < best_dist:
                    best = j
                    best_dist = dist

            if best is not None:
                # Visit customer best
                data[Travel][(Customer, Customer,)][(current, best,)] = True

                arrival = time + best_dist
                time = max(arrival, data[Earliest][(Customer,)][(best,)]) \
                    + data[ServiceTime][(Customer,)][(best,)]
                load += data[Demand][(Customer,)][(best,)]
                current = best
                unvisited.remove(best)
            else:
                # No feasible customer — return to depot, start new route
                data[Travel][(Customer, Customer,)][(current, 0,)] = True
                current = 0
                load = 0
                time = (
                    data[Earliest][(Customer,)][(0,)]
                    + data[ServiceTime][(Customer,)][(0,)]
                )

        # Close last route
        if current != 0:
            data[Travel][(Customer, Customer,)][(current, 0,)] = True

        # Warn about unserved customers
        if unvisited:
            print(f"Warning: {len(unvisited)} customer(s) could not be served: {unvisited}")

        return data
