from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from or_algo import Solver

from ...dimension import *
from ...parameter import *
from .lp_solver.symbol import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey

log = logging.getLogger(__name__)


class GreedySolver(Solver):
    """Nearest-neighbor construction heuristic for VRPTW.

    Builds routes by greedily visiting the nearest feasible customer (by
    Manhattan distance).  A customer is feasible if adding its demand does not
    exceed vehicle capacity and the vehicle can arrive before its latest time
    window.  The solver mutates the input register in-place, writing binary
    ``Travel`` decisions that ``RouteExtractor`` can later decompose into routes.
    """

    _capacity: float

    def __init__(self, *args: Any, capacity: float, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._capacity = float("inf") if capacity is None else capacity

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        """Run nearest-neighbor heuristic and write Travel decisions.

        Modifies *data* in-place and returns it.
        """
        # Collect all customer IDs except depot (0)
        unvisited: set[int] = {c for (c,) in data[Id][(Customer,)].keys() if c != 0}

        current = 0  # depot
        load: float = 0
        time: float = data[Earliest][(Customer,)][(0,)] + data[ServiceTime][(Customer,)][(0,)]  # type: ignore[operator]

        while unvisited:
            # Find nearest feasible customer
            best: int | None = None
            best_dist = float("inf")
            best_arrival = 0.0

            for j in unvisited:
                # Capacity check
                if load + data[Demand][(Customer,)][(j,)] > self._capacity:  # type: ignore[operator]
                    continue

                # Travel time (Manhattan distance)
                dist = abs(data[X][(Customer,)][(current,)] - data[X][(Customer,)][(j,)]) + abs(  # type: ignore[operator]
                    data[Y][(Customer,)][(current,)] - data[Y][(Customer,)][(j,)]  # type: ignore[operator]
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
                    best_arrival = arrival

            if best is not None:
                # Visit customer best
                data[Travel][
                    (
                        Customer,
                        Customer,
                    )
                ][
                    (
                        current,
                        best,
                    )
                ] = True

                time = (
                    max(best_arrival, data[Earliest][(Customer,)][(best,)])  # type: ignore[operator]
                    + data[ServiceTime][(Customer,)][(best,)]
                )
                load += data[Demand][(Customer,)][(best,)]  # type: ignore[operator]
                current = best
                unvisited.remove(best)
            else:
                if current == 0:
                    # Already at depot with no feasible customer — remaining
                    # customers are permanently unservable; break to avoid
                    # infinite loop.
                    break
                # Return to depot, start new route
                data[Travel][
                    (
                        Customer,
                        Customer,
                    )
                ][
                    (
                        current,
                        0,
                    )
                ] = True
                current = 0
                load = 0
                time = data[Earliest][(Customer,)][(0,)] + data[ServiceTime][(Customer,)][(0,)]  # type: ignore[operator]

        # Close last route
        if current != 0:
            data[Travel][
                (
                    Customer,
                    Customer,
                )
            ][
                (
                    current,
                    0,
                )
            ] = True

        # Warn about unserved customers
        if unvisited:
            log.warning(
                "%d customer(s) could not be served: %s",
                len(unvisited),
                sorted(unvisited),
            )

        return data
