"""A* search, written by hand.

For every cell the search tracks:

    g(n)  actual cost from the start to n
    h(n)  estimated cost from n to the goal (Manhattan distance)
    f(n)  g(n) + h(n)

The open cell with the lowest f is expanded first. Manhattan distance
never overestimates, because every move costs at least 1 and the vehicle
can't move diagonally. So the first time the goal is popped, its path is
the cheapest one.
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from environment import Cell, Environment


@dataclass
class SearchResult:
    found: bool
    path: List[Cell] = field(default_factory=list)
    cost: float = float("inf")
    nodes_explored: int = 0
    elapsed_ms: float = 0.0

    @property
    def moves(self) -> int:
        return max(0, len(self.path) - 1)


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(env: Environment, start: Cell, goal: Cell,
          cost_function: Optional[Callable[[Cell], float]] = None) -> SearchResult:
    """Cheapest path from ``start`` to ``goal``.

    ``cost_function`` gives the cost of entering a cell. By default it is
    the environment's real cost (traffic and signals included).
    """
    cost_of = cost_function or env.get_cost
    began = time.perf_counter()

    best_cost: Dict[Cell, float] = {start: 0.0}
    came_from: Dict[Cell, Cell] = {}
    queue: List[Tuple[float, float, Cell]] = [(manhattan(start, goal), 0.0, start)]
    explored = 0

    while queue:
        _, cost_so_far, current = heapq.heappop(queue)

        # Skip stale queue entries for cells we've since reached more cheaply.
        if cost_so_far > best_cost.get(current, float("inf")):
            continue

        if current == goal:
            return SearchResult(True, rebuild_path(came_from, start, goal),
                                cost_so_far, explored, _ms_since(began))
        explored += 1

        for neighbour in env.get_neighbors(current):
            new_cost = cost_so_far + cost_of(neighbour)
            if new_cost < best_cost.get(neighbour, float("inf")):
                best_cost[neighbour] = new_cost
                came_from[neighbour] = current
                heapq.heappush(queue, (new_cost + manhattan(neighbour, goal),
                                       new_cost, neighbour))

    return SearchResult(False, nodes_explored=explored, elapsed_ms=_ms_since(began))


def rebuild_path(came_from: Dict[Cell, Cell], start: Cell, goal: Cell) -> List[Cell]:
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def _ms_since(began: float) -> float:
    return (time.perf_counter() - began) * 1000.0
