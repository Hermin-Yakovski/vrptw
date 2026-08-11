from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from or_algo import Solver

from ...dimension import *
from ...parameter import *
from .lp_solver.symbol import *

if TYPE_CHECKING:
    from or_register import Register, RegisterKey


class RouteExtractor(Solver):
    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        edges: list[tuple[int, int]] = [
            (i, j)
            for i, j in data[Travel][
                Customer,
                Customer,
            ].all
            if data[Travel][
                Customer,
                Customer,
            ][
                i,
                j,
            ]
        ]

        for r, sequence in enumerate(self.find_all_cycles(edges), start=1):
            data[Id][Route,][r,] = r
            data[Name][Route,][r,] = "->".join(str(c) for c in sequence)

            loaded: int = 0
            for c in sequence:
                loaded += data[Demand][Customer,][c,]  # type: ignore[operator]
                data[Loaded][
                    Customer,
                    Route,
                ][
                    c,
                    r,
                ] = loaded

        return data

    @staticmethod
    def find_all_cycles(edges: list[tuple[int, int]]) -> list[list[int]]:
        graph = defaultdict(list)
        for i, j in edges:
            graph[i].append(j)
        all_cycles = []
        seen = set()

        def dfs(node: int, path: list[int]) -> None:
            if node in path:
                idx = path.index(node)
                cycle = path[idx:]
                min_v = min(cycle)
                std_cycle = next(
                    cycle[k:] + cycle[:k] for k in range(len(cycle)) if cycle[k] == min_v
                )
                ct = tuple(std_cycle)
                if ct not in seen:
                    seen.add(ct)
                    all_cycles.append(std_cycle)
                return
            for nxt in graph.get(node, []):
                dfs(nxt, path + [node])

        nodes = {u for u, v in edges} | {v for u, v in edges}
        for start in sorted(nodes):
            dfs(start, [])
        return all_cycles
