from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from or_algo import Solver

from ....dimension import *
from ....parameter import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey

log = logging.getLogger(__name__)


class GreedyCppSolver(Solver):
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
        from ._greedy_cpp import greedy_solve

        # Collect customer IDs (depot = 0) and build flat arrays for C++
        customers = sorted(c for (c,) in data[Id][(Customer,)].keys())

        x = [float(data[X][Customer,][c,]) for c in customers]
        y = [float(data[Y][Customer,][c,]) for c in customers]
        demand = [float(data[Demand][Customer,][c,]) for c in customers]
        earliest = [float(data[Earliest][Customer,][c,]) for c in customers]
        latest = [float(data[Latest][Customer,][c,]) for c in customers]
        service_time = [float(data[ServiceTime][Customer,][c,]) for c in customers]

        result = greedy_solve(x, y, demand, earliest, latest, service_time, self._capacity)

        # Write edges back as Travel decisions
        for i, j in result.edges:
            data[Travel][
                Customer,
                Customer,
            ][
                customers[i],
                customers[j],
            ] = True

        if result.unserved:
            unserved_ids = [customers[c] for c in result.unserved]
            log.warning(
                "%d customer(s) could not be served: %s",
                len(unserved_ids),
                sorted(unserved_ids),
            )

        return data
