from or_register import Register

from vrptw.algorithm._solver.greedy_solver import GreedySolver
from vrptw.dimension import Customer
from vrptw.parameter import (
    Id, X, Y, Demand, Earliest, Latest, ServiceTime, Travel,
)


def _build_register():
    """Build a small VRPTW instance: depot + 4 customers, requiring 2 routes."""
    data = Register()

    # Customer IDs (0 = depot)
    for c in range(5):
        data[Id][(Customer,)][(c,)] = c

    # Coordinates
    positions = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (2, 0), 4: (0, 2)}
    for c, (x, y) in positions.items():
        data[X][(Customer,)][(c,)] = x
        data[Y][(Customer,)][(c,)] = y

    # Demand
    demands = {0: 0, 1: 4, 2: 7, 3: 3, 4: 3}
    for c, d in demands.items():
        data[Demand][(Customer,)][(c,)] = d

    # Time windows
    earliest = {0: 0, 1: 0, 2: 0, 3: 30, 4: 0}
    latest = {0: 1000, 1: 100, 2: 100, 3: 100, 4: 100}
    for c in range(5):
        data[Earliest][(Customer,)][(c,)] = earliest[c]
        data[Latest][(Customer,)][(c,)] = latest[c]

    # Service times
    service = {0: 0, 1: 10, 2: 10, 3: 1, 4: 1}
    for c, s in service.items():
        data[ServiceTime][(Customer,)][(c,)] = s

    return data


def test_greedy_solver_two_routes():
    """Greedy solver should produce two routes for this instance.

    Route 1: 0 -> 1 -> 3 -> 4 -> 0  (load: 4+3+3=10 <= capacity 10)
    Route 2: 0 -> 2 -> 0             (load: 7 <= capacity 10)

    Customer 2 cannot join Route 1 at any point (demand 7 always exceeds
    remaining capacity after visiting customer 1).
    """
    data = _build_register()
    solver = GreedySolver(capacity=10)
    result = solver.solve(data)

    # Extract travel edges
    travel = {
        (i, j)
        for i, j in result[Travel][(Customer, Customer,)].keys()
        if result[Travel][(Customer, Customer,)][(i, j)]
    }

    expected = {(0, 1), (1, 3), (3, 4), (4, 0), (0, 2), (2, 0)}
    assert travel == expected
