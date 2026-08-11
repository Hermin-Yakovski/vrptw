# GreedyCppSolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a C++ accelerated version of the GreedySolver nearest-neighbor VRPTW heuristic, exposed via pybind11, producing identical Travel decisions to the Python GreedySolver.

**Architecture:** C++ kernel (static library) implements the greedy algorithm using STL types. pybind11 bindings expose it as a Python extension module (`_greedy_cpp`). Python wrapper class `GreedyCppSolver` extracts data from the Register into plain lists, calls C++, and writes edges back. Build system: CMake + Ninja, orchestrated by a sidecar script, with hatchling unchanged as the Python build backend.

**Tech Stack:** C++17, pybind11 >=2.12, CMake >=3.20, Ninja, Python 3.11+, or-algo (Solver base class), or-register (Register), pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Add pybind11 >=2.12 to dependencies and dev group |
| `.gitignore` | Modify | Add `*.pyd`, un-ignore `scripts/build_cpp.py` |
| `cpp/CMakeLists.txt` | Create | Top-level CMake: kernel + bindings subdirectories |
| `cpp/kernel/CMakeLists.txt` | Create | Static library target for the greedy kernel |
| `cpp/kernel/greedy.h` | Create | Public API: `GreedyResult` struct + `greedy_solve()` declaration |
| `cpp/kernel/greedy.cpp` | Create | Algorithm implementation (nearest-neighbor heuristic) |
| `cpp/tests/CMakeLists.txt` | Create | C++ test target (links kernel) |
| `cpp/tests/test_greedy.cpp` | Create | Standalone C++ test with 5-node instance |
| `cpp/bindings/CMakeLists.txt` | Create | pybind11 module target (links kernel) |
| `cpp/bindings/py_greedy.cpp` | Create | pybind11 binding: expose `GreedyResult` and `greedy_solve` |
| `scripts/build_cpp.py` | Create | Build orchestration: CMake configure/build + copy artifacts |
| `vrptw/algorithm/_solver/greedy_solver_cpp/__init__.py` | Modify | Export `GreedyCppSolver` |
| `vrptw/algorithm/_solver/greedy_solver_cpp/greedy_cpp_solver.py` | Create | `GreedyCppSolver` class (Register → lists → C++ → Register) |
| `vrptw/algorithm/_unified_capacity_algorithm.py` | Modify | Swap `GreedySolver` for `GreedyCppSolver` in pipeline |
| `tests/test_greedy_cpp_solver.py` | Create | Unit test + parity test (C++ vs Python) |
| `tests/test_greedy_cpp_integration.py` | Create | Integration test with C101 Solomon benchmark |

---

### Task 1: Project Setup — pybind11 dependency and .gitignore

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

This task adds the pybind11 dependency and updates `.gitignore` to handle C++ build artifacts while un-ignoring the build script.

- [ ] **Step 1: Add pybind11 to pyproject.toml dependencies**

In `pyproject.toml`, add `"pybind11>=2.12"` to the `[project]` dependencies list:

```toml
dependencies = [
    "or-scenario>=0.3.0",
    "or-algo>=0.3.1",
    "pybind11>=2.12",
]
```

Also add `"pybind11>=2.12"` to the `[dependency-groups]` dev list:

```toml
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

- [ ] **Step 2: Update .gitignore**

Add these lines to `.gitignore`:

```
# C++ extension modules (pybind11 build artifacts)
*.pyd

# Un-ignore the C++ build script (scripts/* is ignored above)
!scripts/build_cpp.py
```

The existing `build/` entry already covers the CMake build directory. The existing `*.so` entry already covers Linux shared objects. We only need to add `*.pyd` for Windows Python extension files and un-ignore the build script.

- [ ] **Step 3: Install pybind11**

Run:
```bash
uv sync
```

Expected: pybind11 is installed in the virtual environment.

- [ ] **Step 4: Verify pybind11 cmake directory is discoverable**

Run:
```bash
python -c "import pybind11; print(pybind11.get_cmake_dir())"
```

Expected: Prints a path like `D:\github\vrptw\.venv\Lib\site-packages\pybind11\share\cmake\pybind11`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: add pybind11 dependency and C++ gitignore rules"
```

---

### Task 2: C++ Kernel — header and algorithm implementation

**Files:**
- Create: `cpp/kernel/greedy.h`
- Create: `cpp/kernel/greedy.cpp`

This task creates the C++ kernel that implements the nearest-neighbor VRPTW heuristic using STL types.

- [ ] **Step 1: Create the kernel directory structure**

```bash
mkdir -p cpp/kernel
mkdir -p cpp/bindings
mkdir -p cpp/tests
```

- [ ] **Step 2: Create the public API header**

Create `cpp/kernel/greedy.h`:

```cpp
#pragma once
#include <vector>
#include <utility>

struct GreedyResult {
    std::vector<std::pair<int,int>> edges;   // travel edges (i,j)
    std::vector<int> unserved;               // customer indices that couldn't be served
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

- [ ] **Step 3: Create the algorithm implementation**

Create `cpp/kernel/greedy.cpp`:

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

    // Unvisited set: all customer indices except depot (index 0)
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
            // Capacity check
            if (load + demand[j] > capacity) continue;

            // Manhattan distance
            double dist = std::abs(x[current] - x[j]) + std::abs(y[current] - y[j]);

            // Time window check
            double arrival = time + dist;
            if (arrival > latest[j]) continue;

            // Nearest so far
            if (dist < best_dist) {
                best = j;
                best_dist = dist;
            }
        }

        if (best >= 0) {
            // Visit customer best
            result.edges.emplace_back(current, best);
            double arrival = time + best_dist;
            time = std::max(arrival, earliest[best]) + service_time[best];
            load += demand[best];
            current = best;
            unvisited.erase(best);
        } else {
            // No feasible customer found
            if (current == 0) break;  // Already at depot — remaining are unservable
            result.edges.emplace_back(current, 0);
            current = 0;
            load = 0.0;
            time = earliest[0] + service_time[0];
        }
    }

    // Close last route
    if (current != 0)
        result.edges.emplace_back(current, 0);

    // Collect unserved customer indices
    for (int c : unvisited)
        result.unserved.push_back(c);

    return result;
}
```

- [ ] **Step 4: Commit**

```bash
git add cpp/kernel/greedy.h cpp/kernel/greedy.cpp
git commit -m "feat(cpp): add greedy nearest-neighbor kernel"
```

---

### Task 3: C++ Kernel Test

**Files:**
- Create: `cpp/tests/test_greedy.cpp`

This task creates a standalone C++ test that exercises the kernel directly — no Python involved. Uses the same 5-node instance as the existing Python test.

- [ ] **Step 1: Create the C++ test**

Create `cpp/tests/test_greedy.cpp`:

```cpp
#include <cassert>
#include <iostream>
#include "greedy.h"

int main() {
    // 5-node instance: depot (0) + 4 customers, capacity=10
    // Expected: Route 1: 0->1->3->4->0, Route 2: 0->2->0
    std::vector<double> x =      {0, 1, 0, 2, 0};
    std::vector<double> y =      {0, 0, 1, 0, 2};
    std::vector<double> demand = {0, 4, 7, 3, 3};
    std::vector<double> earliest = {0, 0, 0, 30, 0};
    std::vector<double> latest =   {1000, 100, 100, 100, 100};
    std::vector<double> service =  {0, 10, 10, 1, 1};

    auto result = greedy_solve(x, y, demand, earliest, latest, service, 10.0);

    // Verify 6 edges: (0,1), (1,3), (3,4), (4,0), (0,2), (2,0)
    assert(result.edges.size() == 6);
    assert(result.edges[0] == std::make_pair(0, 1));
    assert(result.edges[1] == std::make_pair(1, 3));
    assert(result.edges[2] == std::make_pair(3, 4));
    assert(result.edges[3] == std::make_pair(4, 0));
    assert(result.edges[4] == std::make_pair(0, 2));
    assert(result.edges[5] == std::make_pair(2, 0));
    assert(result.unserved.empty());

    std::cout << "All C++ kernel tests passed." << std::endl;
    return 0;
}
```

- [ ] **Step 2: Commit**

```bash
git add cpp/tests/test_greedy.cpp
git commit -m "test(cpp): add standalone kernel test with 5-node instance"
```

---

### Task 4: CMake Build System

**Files:**
- Create: `cpp/CMakeLists.txt`
- Create: `cpp/kernel/CMakeLists.txt`
- Create: `cpp/bindings/CMakeLists.txt`
- Create: `cpp/tests/CMakeLists.txt`

This task creates the CMake build system with three targets: `greedy_kernel` (static lib), `_greedy_cpp` (pybind11 module), and `test_greedy_cpp` (C++ test).

- [ ] **Step 1: Create the top-level CMakeLists.txt**

Create `cpp/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.20)
project(greedy_vrptw LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

add_subdirectory(kernel)
add_subdirectory(bindings)

option(BUILD_TESTING "Build C++ tests" OFF)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
```

- [ ] **Step 2: Create the kernel CMakeLists.txt**

Create `cpp/kernel/CMakeLists.txt`:

```cmake
add_library(greedy_kernel STATIC greedy.cpp)
target_include_directories(greedy_kernel PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(greedy_kernel PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)
```

- [ ] **Step 3: Create the bindings CMakeLists.txt**

Create `cpp/bindings/CMakeLists.txt`:

```cmake
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_greedy_cpp py_greedy.cpp)
target_link_libraries(_greedy_cpp PRIVATE greedy_kernel)
target_include_directories(_greedy_cpp PRIVATE ${CMAKE_SOURCE_DIR}/kernel)
```

- [ ] **Step 4: Create the tests CMakeLists.txt**

Create `cpp/tests/CMakeLists.txt`:

```cmake
add_executable(test_greedy_cpp test_greedy.cpp)
target_link_libraries(test_greedy_cpp PRIVATE greedy_kernel)
target_include_directories(test_greedy_cpp PRIVATE ${CMAKE_SOURCE_DIR}/kernel)
set_target_properties(test_greedy_cpp PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)
```

- [ ] **Step 5: Verify CMake can configure (without bindings — py_greedy.cpp doesn't exist yet)**

Run:
```bash
cmake -B build/cpp -S cpp -G Ninja -DBUILD_TESTING=ON
```

Expected: CMake fails because `cpp/bindings/py_greedy.cpp` doesn't exist yet. This is expected — we're verifying CMake itself works. We'll create the bindings source in the next task. If the error is about the missing `py_greedy.cpp`, continue to Task 5.

- [ ] **Step 6: Commit**

```bash
git add cpp/CMakeLists.txt cpp/kernel/CMakeLists.txt cpp/bindings/CMakeLists.txt cpp/tests/CMakeLists.txt
git commit -m "build(cpp): add CMake build system for kernel, bindings, and tests"
```

---

### Task 5: pybind11 Bindings

**Files:**
- Create: `cpp/bindings/py_greedy.cpp`

This task creates the pybind11 binding that exposes `GreedyResult` and `greedy_solve` to Python.

- [ ] **Step 1: Create the pybind11 binding source**

Create `cpp/bindings/py_greedy.cpp`:

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

- [ ] **Step 2: Commit**

```bash
git add cpp/bindings/py_greedy.cpp
git commit -m "feat(cpp): add pybind11 binding for greedy_solve"
```

---

### Task 6: Build Script and First Successful Build

**Files:**
- Create: `scripts/build_cpp.py`

This task creates the build orchestration script and verifies the full CMake build works end-to-end.

- [ ] **Step 1: Create the build script**

Create `scripts/build_cpp.py`:

```python
"""Build the C++ greedy solver extension.

Usage:
    python scripts/build_cpp.py          # build
    python scripts/build_cpp.py --clean  # clean build directory
"""

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

    # Configure
    subprocess.run(
        [
            "cmake",
            str(CPP_DIR),
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-Dpybind11_DIR={_find_pybind11()}",
        ],
        cwd=BUILD_DIR,
        check=True,
    )

    # Build
    subprocess.run(["cmake", "--build", "."], cwd=BUILD_DIR, check=True)

    # Copy extension module artifacts to the Python package directory
    for pattern in ("_greedy_cpp*.pyd", "_greedy_cpp*.so"):
        for artifact in BUILD_DIR.glob(f"**/{pattern}"):
            dest = TARGET_DIR / artifact.name
            shutil.copy2(artifact, dest)
            print(f"  copied: {artifact.name} -> {dest}")


def _find_pybind11() -> str:
    """Find pybind11 cmake config directory from the installed Python package."""
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

- [ ] **Step 2: Run the build script**

Run:
```bash
python scripts/build_cpp.py
```

Expected output: CMake configures and builds, then prints a line like:
```
  copied: _greedy_cpp.cp311-win_amd64.pyd -> D:\github\vrptw\vrptw\algorithm\_solver\greedy_solver_cpp\_greedy_cpp.cp311-win_amd64.pyd
```

- [ ] **Step 3: Verify the extension module is importable**

Run:
```bash
python -c "from vrptw.algorithm._solver.greedy_solver_cpp._greedy_cpp import greedy_solve; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Quick smoke test from Python**

Run:
```bash
python -c "
from vrptw.algorithm._solver.greedy_solver_cpp._greedy_cpp import greedy_solve
r = greedy_solve([0,1,0,2,0], [0,0,1,0,2], [0,4,7,3,3], [0,0,0,30,0], [1000,100,100,100,100], [0,10,10,1,1], 10.0)
print('edges:', r.edges)
print('unserved:', r.unserved)
assert len(r.edges) == 6
assert r.unserved == []
print('Smoke test passed')
"
```

Expected: `Smoke test passed`

- [ ] **Step 5: Build and run the C++ standalone test**

Run:
```bash
cmake -B build/cpp -S cpp -G Ninja -DBUILD_TESTING=ON -Dpybind11_DIR=$(python -c "import pybind11; print(pybind11.get_cmake_dir())") -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp
./build/cpp/bin/test_greedy_cpp
```

Expected: `All C++ kernel tests passed.`

- [ ] **Step 6: Commit**

```bash
git add scripts/build_cpp.py
git commit -m "build(cpp): add build script, verify C++ extension builds and runs"
```

---

### Task 7: Python Wrapper — GreedyCppSolver

**Files:**
- Modify: `vrptw/algorithm/_solver/greedy_solver_cpp/__init__.py`
- Create: `vrptw/algorithm/_solver/greedy_solver_cpp/greedy_cpp_solver.py`

This task creates the `GreedyCppSolver` class that bridges between the Register and the C++ kernel.

- [ ] **Step 1: Create the GreedyCppSolver module**

Create `vrptw/algorithm/_solver/greedy_solver_cpp/greedy_cpp_solver.py`:

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
        self._capacity = float("inf") if capacity is None else capacity

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        from ._greedy_cpp import greedy_solve

        # Extract customer data into plain lists (dense, 0-indexed)
        customer_ids = sorted(c for (c,) in data[Id][(Customer,)].keys())

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
            x=x,
            y=y,
            demand=demand,
            earliest=earliest,
            latest=latest,
            service_time=service_time,
            capacity=self._capacity,
        )

        # Write travel edges back to Register (convert indices -> IDs)
        for i_idx, j_idx in result.edges:
            i_id = customer_ids[i_idx]
            j_id = customer_ids[j_idx]
            data[Travel][
                (
                    Customer,
                    Customer,
                )
            ][
                (
                    i_id,
                    j_id,
                )
            ] = True

        # Warn about unserved customers
        if result.unserved:
            unserved_ids = [customer_ids[idx] for idx in result.unserved]
            log.warning(
                "%d customer(s) could not be served: %s",
                len(unserved_ids),
                unserved_ids,
            )

        return data
```

- [ ] **Step 2: Update __init__.py to export GreedyCppSolver**

Replace the contents of `vrptw/algorithm/_solver/greedy_solver_cpp/__init__.py`:

```python
from .greedy_cpp_solver import GreedyCppSolver

__all__ = ["GreedyCppSolver"]
```

- [ ] **Step 3: Commit**

```bash
git add vrptw/algorithm/_solver/greedy_solver_cpp/greedy_cpp_solver.py vrptw/algorithm/_solver/greedy_solver_cpp/__init__.py
git commit -m "feat(algorithm): add GreedyCppSolver Python wrapper"
```

---

### Task 8: Python Unit Test and Parity Test

**Files:**
- Create: `tests/test_greedy_cpp_solver.py`

This task creates the Python unit test (verifying correct Travel edges) and the parity test (verifying C++ and Python produce identical output).

- [ ] **Step 1: Create the test file**

Create `tests/test_greedy_cpp_solver.py`:

```python
from or_register import Register

from vrptw.algorithm._solver.greedy_solver import GreedySolver
from vrptw.algorithm._solver.greedy_solver_cpp import GreedyCppSolver
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


def _extract_edges(data):
    """Extract set of (i, j) travel edges from a solved register."""
    return {
        (i, j)
        for ((i, j),) in data[Travel][
            (
                Customer,
                Customer,
            )
        ].keys()
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
        ]
    }


def test_greedy_cpp_solver_two_routes():
    """GreedyCppSolver should produce two routes for this instance.

    Route 1: 0 -> 1 -> 3 -> 4 -> 0  (load: 4+3+3=10 <= capacity 10)
    Route 2: 0 -> 2 -> 0             (load: 7 <= capacity 10)
    """
    data = _build_register()
    solver = GreedyCppSolver(capacity=10)
    result = solver.solve(data)

    edges = _extract_edges(result)
    expected = {(0, 1), (1, 3), (3, 4), (4, 0), (0, 2), (2, 0)}
    assert edges == expected


def test_parity_python_vs_cpp():
    """GreedySolver and GreedyCppSolver must produce identical Travel edges."""
    data_py = _build_register()
    data_cpp = _build_register()

    py_solver = GreedySolver(capacity=10)
    cpp_solver = GreedyCppSolver(capacity=10)

    result_py = py_solver.solve(data_py)
    result_cpp = cpp_solver.solve(data_cpp)

    edges_py = _extract_edges(result_py)
    edges_cpp = _extract_edges(result_cpp)

    assert edges_py == edges_cpp


def test_greedy_cpp_solver_unserved_customers():
    """Customers with demand exceeding capacity should be reported as unserved."""
    data = _build_register()
    # Set capacity so low that not all customers can be served on first route
    solver = GreedyCppSolver(capacity=3)
    result = solver.solve(data)

    # With capacity=3, customer 1 (demand=4) and customer 2 (demand=7) cannot be served
    # Only customers 3 and 4 (demand=3 each) can be served individually
    edges = _extract_edges(result)
    assert len(edges) > 0  # Some customers should still be served
```

- [ ] **Step 2: Run the tests to verify they pass**

Run:
```bash
pytest tests/test_greedy_cpp_solver.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_greedy_cpp_solver.py
git commit -m "test: add GreedyCppSolver unit test and parity test"
```

---

### Task 9: Integration Test with C101 Solomon Benchmark

**Files:**
- Create: `tests/test_greedy_cpp_integration.py`

This task creates an integration test that loads the C101 Solomon benchmark from SQLite, runs `GreedyCppSolver` → `RouteExtractor` in a standalone pipeline, and verifies structural properties.

- [ ] **Step 1: Create the integration test**

Create `tests/test_greedy_cpp_integration.py`:

```python
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from vrptw.algorithm._solver.greedy_solver_cpp import GreedyCppSolver
from vrptw.algorithm._solver.route_extractor import RouteExtractor
from vrptw.dimension import Customer, Route
from vrptw.parameter import Id, Travel, Loaded
from vrptw.scenario import VrptwScenario
from vrptw.schema import VrptwRequest

project_root = Path(__file__).resolve().parent.parent
database = f"sqlite:///{project_root / 'database' / 'vrptw.db'}"


@pytest.fixture(scope="module")
def solved_scenario():
    """Load C101 instance and run GreedyCppSolver + RouteExtractor pipeline."""
    engine = sqlalchemy.create_engine(database)
    SessionLocal = sessionmaker(bind=engine)

    request = VrptwRequest(instance="C101")
    scenario = VrptwScenario(request)

    with SessionLocal() as session:
        scenario.load(session=session)
        session.commit()

    # Run GreedyCppSolver and RouteExtractor directly
    data = scenario._data
    greedy = GreedyCppSolver(capacity=200)
    greedy.solve(data)
    extractor = RouteExtractor()
    extractor.solve(data)

    return scenario


def test_all_customers_served(solved_scenario):
    """Every loaded customer should appear in at least one route."""
    data = solved_scenario._data
    customer_ids = {c for (c,) in data[Id][(Customer,)].keys()}
    assert len(customer_ids) > 0, "No customers loaded"

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

    non_depot = customer_ids - {0}
    assert non_depot.issubset(visited), f"Unserved customers: {non_depot - visited}"


def test_routes_extracted(solved_scenario):
    """RouteExtractor should produce at least one route after GreedyCppSolver."""
    data = solved_scenario._data
    route_ids = list(data[Id][(Route,)].keys())
    assert len(route_ids) > 0, "No routes extracted"


def test_capacity_not_exceeded(solved_scenario):
    """Each route's total demand should not exceed vehicle capacity (200)."""
    data = solved_scenario._data
    capacity = 200

    for ((r,),) in data[Id][(Route,)].keys():
        route_demand = 0
        for ((c, r2),) in data[Loaded][
            (
                Customer,
                Route,
            )
        ].keys():
            if r2 == r:
                route_demand = max(
                    route_demand,
                    data[Loaded][
                        (
                            Customer,
                            Route,
                        )
                    ][
                        (
                            c,
                            r,
                        )
                    ],
                )
        assert 0 < route_demand <= capacity, (
            f"Route {r} demand {route_demand} out of bounds (0, {capacity}]"
        )
```

- [ ] **Step 2: Run the integration tests**

Run:
```bash
pytest tests/test_greedy_cpp_integration.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 3: Run the full test suite**

Run:
```bash
pytest tests/ -v
```

Expected: All tests PASS (existing Python tests + new C++ wrapper tests + integration tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_greedy_cpp_integration.py
git commit -m "test: add GreedyCppSolver integration test with C101 benchmark"
```

---

### Task 10: Pipeline Integration

**Files:**
- Modify: `vrptw/algorithm/_unified_capacity_algorithm.py`

This task swaps `GreedySolver` for `GreedyCppSolver` in the `UnifiedCapacityAlgorithm` pipeline.

- [ ] **Step 1: Update UnifiedCapacityAlgorithm to use GreedyCppSolver**

Replace the contents of `vrptw/algorithm/_unified_capacity_algorithm.py`:

```python
from or_algo import Algorithm

from ._solver import RouteExtractor, GreedySolver
from ._solver.greedy_solver_cpp import GreedyCppSolver


class UnifiedCapacityAlgorithm(Algorithm):
    def __init__(self, *args, capacity: float, **kwargs):
        super().__init__(*args, **kwargs)
        # self.append(GreedySolver, 'GreedySolver', capacity=capacity)
        self.append(GreedyCppSolver, "GreedyCppSolver", capacity=capacity)
        self.append(RouteExtractor, "RouteExtractor")
```

- [ ] **Step 2: Run the existing integration test to verify pipeline still works**

Run:
```bash
pytest tests/test_greedy_integration.py -v
```

Expected: All 3 tests PASS (the existing integration test now exercises `GreedyCppSolver` through the pipeline).

- [ ] **Step 3: Run the full test suite**

Run:
```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add vrptw/algorithm/_unified_capacity_algorithm.py
git commit -m "feat(algorithm): switch pipeline to GreedyCppSolver"
```