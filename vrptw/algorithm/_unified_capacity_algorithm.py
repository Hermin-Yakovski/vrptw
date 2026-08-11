from or_algo import Algorithm

from ._solver import UnifiedCapacitySolver, RouteExtractor, GreedySolver, GreedyCppSolver


class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        # self.append(UnifiedCapacitySolver, 'UnifiedCapacitySolver', capacity=capacity)
        self.append(GreedyCppSolver, 'GreedySolver', capacity=capacity)
        self.append(RouteExtractor, 'RouteExtractor')
