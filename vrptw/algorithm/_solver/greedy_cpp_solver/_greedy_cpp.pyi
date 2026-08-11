from collections.abc import Sequence
from typing import TypeAlias

_Numeric: TypeAlias = float | int

class GreedyResult:
    edges: list[tuple[int, int]]
    unserved: list[int]

def greedy_solve(
    x: Sequence[_Numeric],
    y: Sequence[_Numeric],
    demand: Sequence[_Numeric],
    earliest: Sequence[_Numeric],
    latest: Sequence[_Numeric],
    service_time: Sequence[_Numeric],
    capacity: _Numeric,
) -> GreedyResult: ...
