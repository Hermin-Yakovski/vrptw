# GreedyCppSolver: C++ Accelerated VRPTW Heuristic via pybind11

## Overview

Implement `GreedyCppSolver` — a C++ accelerated version of the `GreedySolver` nearest-neighbor construction heuristic for VRPTW. The core algorithm is implemented in C++ and exposed to Python via pybind11 bindings. `GreedyCppSolver` produces identical `Travel` decisions to the Python `GreedySolver`, but executes the greedy loop in compiled C++.

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Build backend | hatchling (unchanged) | Existing uv-based CI/CD depends on hatchling |
| C++ build tool | CMake + Ninja | Industry standard, follows fibonacci_cpp reference |
| Build orchestration | `scripts/build_cpp.py` sidecar script | Runs CMake, copies artifacts to package directory |
| Binding mechanism | pybind11 | Type-safe, automatic Python ↔ C++ conversion |
| C++ kernel API | STL types (`std::vector`, `std::pair`) | pybind11 auto-converts; kernel is independently testable |
| C++ structure | Separate kernel (static lib) + bindings target | Kernel testable without Python; static linking avoids DLL loading issues |
| Data passing | Plain arrays in, edge list out | Decouples C++ from or-register framework |
| Packaging | In-tree subpackage within vrptw repo | Single repo, single pipeline |

## Directory Structure

```
vrptw/
├── algorithm/
│   └── _solver/
│       └── greedy_solver_cpp/
│           ├── __init__.py              # MODIFY: export GreedyCppSolver
│           └── greedy_cpp_solver.py     # NEW: GreedyCppSolver class
├── cpp/                                 # NEW: C++ source tree
│   ├── CMakeLists.txt                   # Top-level CMake
│   ├── kernel/
│   │   ├── CMakeLists.txt               # Kernel static library target
│   │   ├── greedy.h                     # Public API header
│   │   └── greedy.cpp                   # Algorithm implementation
│   └── bindings/
│       ├── CMakeLists.txt               # pybind11 module target
│       └── py_greedy.cpp                # pybind11 binding code
├── scripts/
│   └── build_cpp.py                     # NEW: dev script to run CMake build
├── tests/
│   ├── test_greedy_cpp_solver.py        # NEW: unit tests for C++ solver
│   └── test_greedy_cpp_integration.py   # NEW: integration test with C101
├── pyproject.toml                       # MODIFY: add pybind11 dep
└── .gitignore                           # MODIFY: ignore .pyd/.so/.dll artifacts
```

Build artifacts (`.pyd`, `.so`) land in `greedy_solver_cpp/` and are git-ignored.

## C++ Kernel

### Public API — `cpp/kernel/greedy.h`

```cpp
#pragma once
#include <vector>
#include <utility>

struct GreedyResult {
    std::vector<std::pair<int,int>> edges;   // travel edges (i,j)
    std::vector<int> unserved;               // customer IDs that couldn't be served
};

GreedyResult greedy_solve(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& demand,
    const std::vector<double>& earliest,
    const std::vector<double>& latest,
    const std::vector<double>& service_time,
    double capacity);
```

### Algorithm — `cpp/kernel/greedy.cpp`

The algorithm is identical to the Python `GreedySolver`:

1. Collect all customer indices except depot (index 0) into `std::set<int> unvisited`.
2. Start at depot, load = 0, time = `earliest[0] + service_time[0]`.
3. Loop while unvisited customers remain:
   - Find the nearest feasible customer by Manhattan distance.
   - Feasibility: `load + demand[j] <= capacity` AND `time + dist <= latest[j]`.
   - If found: record edge `(current, best)`, update time/load/position, remove from unvisited.
   - If not found: record edge `(current, 0)`, reset to depot for new route.
   - If at depot with no feasible customer: break (remaining customers are unservable).
4. Close last route: edge `(current, 0)` if not at depot.
5. Return edges and list of unserved customer indices.

```cpp
#include "greedy.h"
#include <cmath>
#include <set>
#include <limits>

GreedyResult greedy_solve(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& demand,
    const std::vector<double>& earliest,
    const std::vector<double>& latest,
    const std::vector<double>& service_time,
    double capacity)
{
    int n = static_cast<int>(x.size());

    std::set<int> unvisited;
    for (int c = 1; c < n; ++c)
        unvisited.insert(c);

    GreedyResult result;
    int current = 0;
    double load = 0.0;
    double time = earliest[0] + service_time[0];

    while (!unvisited.empty()) {
        int best = -1;
        double best_dist = std::numeric_limits<double>::infinity();

        for (int j : unvisited) {
            if (load + demand[j] > capacity) continue;

            double dist = std::abs(x[current] - x[j]) + std::abs(y[current] - y[j]);
            double arrival = time + dist;
            if (arrival > latest[j]) continue;

            if (dist < best_dist) {
                best = j;
                best_dist = dist;
            }
        }

        if (best >= 0) {
            result.edges.emplace_back(current, best);
            double arrival = time + best_dist;
            time = std::max(arrival, earliest[best]) + service_time[best];
            load += demand[best];
            current = best;
            unvisited.erase(best);
        } else {
            if (current == 0) break;
            result.edges.emplace_back(current, 0);
            current = 0;
            load = 0.0;
            time = earliest[0] + service_time[0];
        }
    }

    if (current != 0)
        result.edges.emplace_back(current, 0);

    for (int c : unvisited)
        result.unserved.push_back(c);

    return result;
}
```

**Key details:**
- Customer indices are dense 0-based (Python maps Register IDs → indices before calling).
- Depot is always index 0.
- `std::set<int>` gives deterministic iteration order (matching Python for distance ties).
- Manhattan distance: `|x[i] - x[j]| + |y[i] - y[j]|`.
- Capacity of `float('inf')` converts to `std::numeric_limits<double>::infinity()` via pybind11.

## pybind11 Binding Layer

### `cpp/bindings/py_greedy.cpp`

```cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "greedy.h"

namespace py = pybind11;

PYBIND11_MODULE(_greedy_cpp, m) {
    m.doc() = "C++ greedy nearest-neighbor VRPTW solver";

    py::class_<GreedyResult>(m, "GreedyResult")
        .def_readonly("edges", &GreedyResult::edges)
        .def_readonly("unserved", &GreedyResult::unserved);

    m.def("greedy_solve", &greedy_solve,
        "Run nearest-neighbor VRPTW heuristic.",
        py::arg("x"),
        py::arg("y"),
        py::arg("demand"),
        py::arg("earliest"),
        py::arg("latest"),
        py::arg("service_time"),
        py::arg("capacity"));
}
```

Compiles to `_greedy_cpp.pyd` (Windows) or `_greedy_cpp.cpython-311-x86_64-linux-gnu.so` (Linux). The leading underscore convention marks it as an internal C extension.

**Auto-conversions** (via `pybind11/stl.h`):

| Python type | C++ type |
|---|---|
| `list[float]` | `std::vector<double>` |
| `float` | `double` |
| `list[tuple[int,int]]` | `std::vector<std::pair<int,int>>` |
| `list[int]` | `std::vector<int>` |

## Python Wrapper — `GreedyCppSolver`

### `vrptw/algorithm/_solver/greedy_solver_cpp/greedy_cpp_solver.py`

```python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from or_algo import Solver

from ...dimension import *
from ...parameter import *
from ..lp_solver.symbol import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey

log = logging.getLogger(__name__)


class GreedyCppSolver(Solver):
    """C++ accelerated nearest-neighbor VRPTW heuristic.

    Same algorithm as GreedySolver, but the core loop runs in C++
    via pybind11.  Data is extracted from the Register into plain
    lists, passed to C++, and travel edges are written back.
    """

    _capacity: float

    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        self._capacity = float('inf') if capacity is None else capacity

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        from ._greedy_cpp import greedy_solve

        # Extract customer data into plain lists (dense, 0-indexed)
        customer_ids = sorted(c for c, in data[Id][(Customer,)].keys())

        n = len(customer_ids)
        x = [0.0] * n
        y = [0.0] * n
        demand = [0.0] * n
        earliest = [0.0] * n
        latest = [0.0] * n
        service_time = [0.0] * n

        for idx, c in enumerate(customer_ids):
            x[idx] = data[X][(Customer,)][(c,)]
            y[idx] = data[Y][(Customer,)][(c,)]
            demand[idx] = data[Demand][(Customer,)][(c,)]
            earliest[idx] = data[Earliest][(Customer,)][(c,)]
            latest[idx] = data[Latest][(Customer,)][(c,)]
            service_time[idx] = data[ServiceTime][(Customer,)][(c,)]

        # Call C++ kernel
        result = greedy_solve(
            x=x, y=y, demand=demand,
            earliest=earliest, latest=latest,
            service_time=service_time,
            capacity=self._capacity,
        )

        # Write travel edges back to Register (convert indices -> IDs)
        for i_idx, j_idx in result.edges:
            i_id = customer_ids[i_idx]
            j_id = customer_ids[j_idx]
            data[Travel][(Customer, Customer,)][(i_id, j_id,)] = True

        # Warn about unserved customers
        if result.unserved:
            unserved_ids = [customer_ids[idx] for idx in result.unserved]
            log.warning(
                "%d customer(s) could not be served: %s",
                len(unserved_ids), unserved_ids,
            )

        return data
```

### `vrptw/algorithm/_solver/greedy_solver_cpp/__init__.py`

```python
from .greedy_cpp_solver import GreedyCppSolver

__all__ = ['GreedyCppSolver']
```

### Pipeline Integration

In `UnifiedCapacityAlgorithm`, swap `GreedySolver` for `GreedyCppSolver`:

```python
from ._solver import RouteExtractor, GreedySolver
from ._solver.greedy_solver_cpp import GreedyCppSolver

class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        # Choose one:
        # self.append(GreedySolver, 'GreedySolver', capacity=capacity)
        self.append(GreedyCppSolver, 'GreedyCppSolver', capacity=capacity)
        self.append(RouteExtractor, 'RouteExtractor')
```

Both solvers produce identical `Travel` decisions consumed by `RouteExtractor`.

### Design Decisions

| Aspect | Decision | Rationale |
|---|---|---|
| ID mapping | `sorted()` customer IDs → dense 0-based indices | Register IDs may be sparse; C++ expects dense 0-based |
| Import location | Lazy import inside `solve()` | Avoids ImportError if `.pyd` not built yet |
| Sorted extraction | Deterministic ordering | Same IDs always map to same indices |
| Capacity | `None` → `float('inf')` | Consistent with `GreedySolver` |

## Build System

### CMake

**`cpp/CMakeLists.txt` (top-level):**

```cmake
cmake_minimum_required(VERSION 3.20)
project(greedy_vrptw LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(kernel)
add_subdirectory(bindings)

option(BUILD_TESTING "Build C++ tests" OFF)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
```

**`cpp/kernel/CMakeLists.txt`:**

```cmake
add_library(greedy_kernel STATIC greedy.cpp)
target_include_directories(greedy_kernel PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(greedy_kernel PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)
```

**`cpp/bindings/CMakeLists.txt`:**

```cmake
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_greedy_cpp py_greedy.cpp)
target_link_libraries(_greedy_cpp PRIVATE greedy_kernel)
target_include_directories(_greedy_cpp PRIVATE ${CMAKE_SOURCE_DIR}/kernel)
```

### Build Script — `scripts/build_cpp.py`

```python
"""Build the C++ greedy solver extension."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CPP_DIR = ROOT / "cpp"
BUILD_DIR = ROOT / "build" / "cpp"
TARGET_DIR = ROOT / "vrptw" / "algorithm" / "_solver" / "greedy_solver_cpp"


def build():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["cmake", str(CPP_DIR), "-G", "Ninja",
         "-DCMAKE_BUILD_TYPE=Release",
         f"-Dpybind11_DIR={_find_pybind11()}"],
        cwd=BUILD_DIR,
        check=True,
    )
    subprocess.run(["cmake", "--build", "."], cwd=BUILD_DIR, check=True)

    for pattern in ("_greedy_cpp*.pyd", "_greedy_cpp*.so"):
        for artifact in BUILD_DIR.glob(f"**/{pattern}"):
            dest = TARGET_DIR / artifact.name
            shutil.copy2(artifact, dest)
            print(f"  copied: {artifact.name} -> {dest}")


def _find_pybind11() -> str:
    import pybind11
    return str(Path(pybind11.get_cmake_dir()))


def clean():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"Removed {BUILD_DIR}")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        build()
```

### pyproject.toml Changes

```toml
[project]
dependencies = [
    "or-scenario>=0.3.0",
    "or-algo>=0.3.1",
    "pybind11>=2.12",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
    "mypy>=1.10",
    "pytest-cov>=7.1.0",
    "pandas-stubs>=2.0",
    "pybind11>=2.12",
]
```

### .gitignore Additions

```
# C++ build artifacts
build/cpp/
vrptw/algorithm/_solver/greedy_solver_cpp/*.pyd
vrptw/algorithm/_solver/greedy_solver_cpp/*.so
```

### Developer Workflow

```bash
pip install pybind11              # one-time
python scripts/build_cpp.py       # build C++ extension
pytest tests/ -v                  # run all tests
python scripts/build_cpp.py --clean && python scripts/build_cpp.py  # clean rebuild
```

## Testing Strategy

### Layer 1: C++ Unit Test (standalone, optional)

File: `cpp/tests/test_greedy.cpp`

Exercises the kernel directly using the same 5-node hand-crafted instance as the Python unit test. Built only with `BUILD_TESTING=ON`.

```cpp
#include <cassert>
#include <iostream>
#include "greedy.h"

int main() {
    std::vector<double> x =     {0, 1, 0, 2, 0};
    std::vector<double> y =     {0, 0, 1, 0, 2};
    std::vector<double> demand = {0, 4, 7, 3, 3};
    std::vector<double> earliest = {0, 0, 0, 30, 0};
    std::vector<double> latest =  {1000, 100, 100, 100, 100};
    std::vector<double> service = {0, 10, 10, 1, 1};

    auto result = greedy_solve(x, y, demand, earliest, latest, service, 10.0);

    assert(result.edges.size() == 6);
    assert(result.edges[0] == std::make_pair(0, 1));
    assert(result.edges[1] == std::make_pair(1, 3));
    assert(result.edges[2] == std::make_pair(3, 4));
    assert(result.edges[3] == std::make_pair(4, 0));
    assert(result.edges[4] == std::make_pair(0, 2));
    assert(result.edges[5] == std::make_pair(2, 0));
    assert(result.unserved.empty());

    std::cout << "All C++ tests passed.\n";
}
```

### Layer 2: Python Unit Test

File: `tests/test_greedy_cpp_solver.py`

Tests `GreedyCppSolver` with the same 5-node instance, verifying correct `Travel` edges are written to the Register.

### Layer 3: Parity Test

File: `tests/test_greedy_cpp_solver.py` (same file)

Runs both `GreedySolver` and `GreedyCppSolver` on the same instance and asserts identical output. This is the primary correctness guarantee.

### Layer 4: Integration Test

File: `tests/test_greedy_cpp_integration.py`

Loads C101 Solomon benchmark from SQLite, runs `GreedyCppSolver` → `RouteExtractor` pipeline, verifies:
- All customers served
- At least one route extracted
- No route exceeds vehicle capacity

### Test Summary

| Test | Validates | When |
|---|---|---|
| C++ unit test | Kernel algorithm | Manual (CMake with `BUILD_TESTING=ON`) |
| Python unit test | Register integration | `pytest` |
| Parity test | C++ ≡ Python output | `pytest` |
| Integration test | Full pipeline + real data | `pytest` |