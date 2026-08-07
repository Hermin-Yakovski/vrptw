# GreedySolver: Nearest-Neighbor VRPTW Heuristic

## Overview

Implement the `GreedySolver` — a nearest-neighbor construction heuristic for the Vehicle Routing Problem with Time Windows (VRPTW). The solver builds routes greedily by always visiting the nearest feasible unvisited customer from the current position, returning to the depot when no more customers can be added to the current route.

## File Changed

`vrptw/algorithm/_solver/greedy_solver.py` (existing stub, implementation added)

## Pipeline Context

The `GreedySolver` runs as the first step in `UnifiedCapacityAlgorithm`:

1. **GreedySolver** — sets `Travel[Customer, Customer,]` decisions (binary arc selections)
2. **RouteExtractor** — reads `Travel` decisions, extracts routes via cycle detection, computes `Loaded` values

The LP-based `UnifiedCapacitySolver` is currently commented out and not in the active pipeline.

## Algorithm

### Initialization

- Collect all customer IDs from the register (excluding depot, customer 0) into an `unvisited` set.
- Compute depot ready time: `earliest[0] + service_time[0]`.

### Route Construction Loop

For each new route:
- Start at depot (customer 0), load = 0, time = depot ready time.
- Repeatedly find the nearest feasible customer:
  - **Distance:** Manhattan distance: `|x[current] - x[j]| + |y[current] - y[j]|`
  - **Arrival time:** `arrival_j = time + manhattan(current, j)`
  - **Feasibility checks:**
    1. **Capacity:** `load + demand[j] <= capacity`
    2. **Time window:** `arrival_j <= latest[j]`
- If a feasible customer is found:
  - Set `Travel[current, j] = True`
  - Update time with waiting post-processing: `time = max(arrival_j, earliest[j]) + service_time[j]`
  - Update load: `load += demand[j]`
  - Move current position to j, remove j from unvisited.
- If no feasible customer exists:
  - Set `Travel[current, 0] = True` (return to depot)
  - Reset time to depot ready time, close route, start next route.

### Termination

After all customers are served, close the last route: `Travel[current, 0] = True`.

## Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Distance metric | Manhattan (`|x_i - x_j| + |y_i - y_j|`) | Consistent with LP solver objective |
| Waiting behavior | `max(arrival, earliest[j]) + service_time[j]` | Standard VRPTW: vehicle waits if arriving early |
| Arrival time formula | `time + manhattan(current, j)` | Matches `CreateConstrCalculateArrival` constraint |
| Output scope | `Travel` only | Modular: RouteExtractor handles route extraction and `Loaded` |
| Capacity handling | `None` → `float('inf')` | Matches `CreateVarLoaded` pattern |
| Approach | Procedural (single `solve()` method) | Algorithm is ~30 lines; a helper class would be over-engineered |

## Edge Cases

- **No feasible customer from current route:** Close the route and start a fresh one from the depot.
- **Customer demand exceeds vehicle capacity:** Customer remains in `unvisited` indefinitely. After the main loop, any remaining unserved customers are logged via `print` warning.
- **Distance ties:** First feasible customer with minimum distance wins (deterministic by iteration order).
- **Depot time:** Uses `earliest[0] + service_time[0]` as the ready time for all route departures.

## Register API Usage

Reading from register:
- `data[Id][Customer,].keys()` — iterate customer IDs as `(c,)` tuples
- `data[X][Customer,][c,]`, `data[Y][Customer,][c,]` — coordinates
- `data[Demand][Customer,][c,]` — demand quantity
- `data[Earliest][Customer,][c,]`, `data[Latest][Customer,][c,]` — time windows
- `data[ServiceTime][Customer,][c,]` — service duration

Writing to register:
- `data[Travel][Customer, Customer,][i, j,] = True` — arc selection (boolean)

Return value:
- Returns the modified `data` register (matches `RouteExtractor` pattern)

## Constructor

```python
class GreedySolver(Solver):
    _capacity: float

    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        self._capacity = float('inf') if capacity is None else capacity
```

The `capacity` parameter is passed from `UnifiedCapacityAlgorithm`:
```python
self.append(GreedySolver, 'GreedySolver', capacity=capacity)
```
