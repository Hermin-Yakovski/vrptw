from typing import Any

from or_algo import Algorithm

from ._solver import UnifiedCapacitySolver, GreedyCppSolver, GreedySolver, RouteExtractor


class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args: Any, capacity: float, solver: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if solver == 'exact':
            self.append(UnifiedCapacitySolver, 'UnifiedCapacitySolver', capacity=capacity)
        elif solver == 'greedy':
            self.append(GreedySolver, "GreedySolver", capacity=capacity)
        elif solver == 'greedy_cpp':
            self.append(GreedyCppSolver, "GreedyCppSolver", capacity=capacity)
        else:
            raise ValueError(f'Unknown solver {solver}')

        self.append(RouteExtractor, "RouteExtractor")
