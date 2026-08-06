from or_algo import Algorithm

from ._solver import UnifiedCapacitySolver


class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        self.append(UnifiedCapacitySolver, 'UnifiedCapacitySolver', capacity=capacity)
