# GreedySolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `GreedySolver` nearest-neighbor VRPTW heuristic that builds routes by greedily visiting the nearest feasible customer.

**Architecture:** Single `solve()` method in the existing `GreedySolver` stub. Uses Manhattan distance, respects capacity and time window constraints, and writes binary `Travel` decisions to the register. `RouteExtractor` (already in the pipeline) handles route extraction from the travel decisions.

**Tech Stack:** Python 3.11+, or-algo (Solver base class), or-register (Register data structure), pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `vrptw/algorithm/_solver/greedy_solver.py` | Modify | GreedySolver implementation (nearest-neighbor heuristic) |
| `tests/test_greedy_solver.py` | Create | Unit tests with a small hand-crafted VRPTW instance |
| `tests/test_greedy_integration.py` | Create | Integration test using C101 Solomon benchmark from SQLite |

---

### Task 1: Write the failing test

**Files:**
- Create: `tests/test_greedy_solver.py`

This test constructs a small VRPTW instance (5 nodes: depot + 4 customers) that requires exactly 2 routes, runs the greedy solver, and verifies the expected travel edges.

**Test instance:**
```
Node 0 (depot):    pos=(0,0),  demand=0,  earliest=0,  latest=1000, service=0
Node 1:            pos=(1,0),  demand=4,  earliest=0,  latest=100,  service=10
Node 2:            pos=(0,1),  demand=7,  earliest=0,  latest=100,  service=10
Node 3:            pos=(2,0),  demand=3,  earliest=30, latest=100,  service=1
Node 4:            pos=(0,2),  demand=3,  earliest=0,  latest=100,  service=1

Capacity = 10
```

**Expected trace (capacity=10):**
```
Route 1: 0 → 1 → 3 → 4 → 0  (load: 4+3+3=10)
  From 0: nearest is 1 (dist=1), load=4, time=max(1,0)+10=11
  From 1: 2 infeasible (load 4+7=11>10), 3 feasible (dist=1), load=7, time=max(12,30)+1=31
  From 3: 2 infeasible (load 7+7=14>10), 4 feasible (dist=4), load=10, time=max(35,0)+1=36
  From 4: 2 infeasible (load 10+7=17>10). Close route.
Route 2: 0 → 2 → 0  (load: 7)
  From 0: only 2 unvisited, feasible (dist=1, load=7). Close route.
```

Expected travel edges: `(0,1), (1,3), (3,4), (4,0), (0,2), (2,0)`

- [ ] **Step 1: Create test file with the full greedy test**

```python
from or_register import Register

from vrptw.algorithm._solver.greedy_solver import GreedySolver
from vrptw.dimension import Customer
from vrptw.parameter import (
    Id,
    X,
    Y,
    Demand,
    Earliest,
    Latest,
    ServiceTime,
    Travel,
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
        for ((i, j),) in result[Travel][
            (
                Customer,
                Customer,
            )
        ].keys()
        if result[Travel][
            (
                Customer,
                Customer,
            )
        ][
            (
                i,
                j,
            )
        ]
    }

    expected = {(0, 1), (1, 3), (3, 4), (4, 0), (0, 2), (2, 0)}
    assert travel == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_greedy_solver.py -v
```

Expected: FAIL — `solve()` returns `None` (the current stub has `pass`), so `result[Travel]` raises `TypeError`.

- [ ] **Step 3: Commit the test**

```bash
git add tests/test_greedy_solver.py
git commit -m "test: add greedy solver unit test (two-route scenario)"
```

---

### Task 2: Implement GreedySolver and make test pass

**Files:**
- Modify: `vrptw/algorithm/_solver/greedy_solver.py`

- [ ] **Step 1: Implement the full GreedySolver**

Replace the entire contents of `greedy_solver.py`:

```python
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
        self._capacity = float("inf") if capacity is None else capacity

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        # Collect all customer IDs except depot (0)
        unvisited: set[int] = {c for (c,) in data[Id][(Customer,)].keys() if c != 0}

        current = 0  # depot
        load: float = 0
        time: float = data[Earliest][(Customer,)][(0,)] + data[ServiceTime][(Customer,)][(0,)]

        while unvisited:
            # Find nearest feasible customer
            best: int | None = None
            best_dist = float("inf")

            for j in unvisited:
                # Capacity check
                if load + data[Demand][(Customer,)][(j,)] > self._capacity:
                    continue

                # Travel time (Manhattan distance)
                dist = abs(data[X][(Customer,)][(current,)] - data[X][(Customer,)][(j,)]) + abs(
                    data[Y][(Customer,)][(current,)] - data[Y][(Customer,)][(j,)]
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

                arrival = time + best_dist
                time = (
                    max(arrival, data[Earliest][(Customer,)][(best,)])
                    + data[ServiceTime][(Customer,)][(best,)]
                )
                load += data[Demand][(Customer,)][(best,)]
                current = best
                unvisited.remove(best)
            else:
                # No feasible customer — return to depot, start new route
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
                time = data[Earliest][(Customer,)][(0,)] + data[ServiceTime][(Customer,)][(0,)]

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
            print(f"Warning: {len(unvisited)} customer(s) could not be served: {unvisited}")

        return data
```

- [ ] **Step 2: Run test to verify it passes**

Run:
```bash
pytest tests/test_greedy_solver.py -v
```

Expected: PASS

- [ ] **Step 3: Commit the implementation**

```bash
git add vrptw/algorithm/_solver/greedy_solver.py
git commit -m "feat(algorithm): implement GreedySolver nearest-neighbor heuristic"
```

---

### Task 3: Add integration test with Solomon C101 benchmark

**Files:**
- Create: `tests/test_greedy_integration.py`

This test loads the C101 Solomon benchmark from the SQLite database, runs the full algorithm pipeline (GreedySolver → RouteExtractor), and verifies structural properties of the solution.

- [ ] **Step 1: Create integration test**

```python
import sys
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm import UnifiedCapacityAlgorithm
from vrptw.dimension import Customer, Route
from vrptw.parameter import (
    Id,
    Name,
    Demand,
    Earliest,
    Latest,
    ServiceTime,
    Travel,
    Loaded,
)
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest

project_root = Path(__file__).resolve().parent.parent
database = f"sqlite:///{project_root / 'database' / 'vrptw.db'}"


@pytest.fixture(scope="module")
def solved_scenario():
    """Load C101 instance and run the greedy algorithm pipeline."""
    engine = sqlalchemy.create_engine(database)
    SessionLocal = sessionmaker(bind=engine)

    request = VrptwRequest(instance="C101")
    scenario = VrptwScenario(request)

    with SessionLocal() as session:
        scenario.load(session=session)
        session.commit()

    scenario.set_algorithm(UnifiedCapacityAlgorithm, capacity=200)
    scenario.exec_algorithm()

    return scenario


def test_all_customers_served(solved_scenario):
    """Every loaded customer should appear in at least one route."""
    data = solved_scenario.data
    customer_ids = {c for (c,) in data[Id][(Customer,)].keys()}
    assert len(customer_ids) > 0, "No customers loaded"

    # Every customer (except depot) should have at least one incoming travel edge
    travel_keys = list(
        data[Travel][
            (
                Customer,
                Customer,
            )
        ].keys()
    )
    visited = set()
    for ((i, j),) in travel_keys:
        if data[Travel][
            (
                Customer,
                Customer,
            )
        ][
            (
                i,
                j,
            )
        ]:
            visited.add(j)

    # All non-depot customers must be visited
    non_depot = customer_ids - {0}
    assert non_depot.issubset(visited), f"Unserved customers: {non_depot - visited}"


def test_routes_extracted(solved_scenario):
    """RouteExtractor should produce at least one route after greedy solver."""
    data = solved_scenario.data
    route_ids = list(data[Id][(Route,)].keys())
    assert len(route_ids) > 0, "No routes extracted"


def test_capacity_not_exceeded(solved_scenario):
    """Each route's total demand should not exceed vehicle capacity (200)."""
    data = solved_scenario.data
    capacity = 200

    for ((r,),) in data[Id][(Route,)].keys():
        # Sum demand of all customers on this route
        route_demand = 0
        for ((c, r2),) in data[Loaded][
            (
                Customer,
                Route,
            )
        ].keys():
            if r2 == r:
                route_demand = data[Loaded][
                    (
                        Customer,
                        Route,
                    )
                ][
                    (
                        c,
                        r,
                    )
                ]
        # Loaded tracks cumulative demand; the last customer's loaded = total
        # This is a basic sanity check
        assert route_demand <= capacity, f"Route {r} exceeds capacity: {route_demand} > {capacity}"
```

- [ ] **Step 2: Run integration test**

Run:
```bash
pytest tests/test_greedy_integration.py -v
```

Expected: All 3 tests PASS

- [ ] **Step 3: Run full test suite**

Run:
```bash
pytest tests/ -v
```

Expected: All tests PASS (unit + integration)

- [ ] **Step 4: Commit integration tests**

```bash
git add tests/test_greedy_integration.py
git commit -m "test: add greedy solver integration test with C101 benchmark"
```
