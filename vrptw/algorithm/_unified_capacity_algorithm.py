from typing import Any

from or_algo import Algorithm

from ._solver import GreedyCppSolver, RouteExtractor


class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args: Any, capacity: float, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # self.append(UnifiedCapacitySolver, 'UnifiedCapacitySolver', capacity=capacity)
        self.append(GreedyCppSolver, "GreedySolver", capacity=capacity)
        self.append(RouteExtractor, "RouteExtractor")
