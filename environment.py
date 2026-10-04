"""The simulated city: a grid of cells addressed as (row, column).

Layout characters:

    .   open road
    #   no road (permanently blocked)
    S   start
    D   destination

The environment only stores facts (traffic, signals, temporary closures).
Turning those facts into costs is done by ``rules.py``.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Deque, Dict, List, Optional, Set, Tuple

import rules

Cell = Tuple[int, int]

OPEN_ROAD = "."
BLOCKED_ROAD = "#"
START_CELL = "S"
DESTINATION_CELL = "D"


class Environment:
    def __init__(self, layout: List[str]) -> None:
        self.layout = [row.strip() for row in layout]
        if not self.layout:
            raise ValueError("The city layout cannot be empty.")

        self.rows = len(self.layout)
        self.cols = len(self.layout[0])
        if any(len(row) != self.cols for row in self.layout):
            raise ValueError("Every row of the city layout must have the same length.")

        self.start = self._find_unique(START_CELL)
        self.destination = self._find_unique(DESTINATION_CELL)

        self.traffic: Dict[Cell, int] = {}
        self.signals: Dict[Cell, str] = {}
        self.temporary_blocks: Set[Cell] = set()

    def _find_unique(self, symbol: str) -> Cell:
        found = [(r, c) for r in range(self.rows) for c in range(self.cols)
                 if self.layout[r][c] == symbol]
        if len(found) != 1:
            raise ValueError(f"The layout must contain exactly one '{symbol}' cell.")
        return found[0]

    # -- questions about the map ---------------------------------------
    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.rows and 0 <= cell[1] < self.cols

    def is_open_road(self, cell: Cell) -> bool:
        """A road that exists, ignoring temporary closures."""
        return self.in_bounds(cell) and self.layout[cell[0]][cell[1]] != BLOCKED_ROAD

    def is_blocked(self, cell: Cell) -> bool:
        return not self.is_open_road(cell) or cell in self.temporary_blocks

    def is_start(self, cell: Cell) -> bool:
        return cell == self.start

    def is_destination(self, cell: Cell) -> bool:
        return cell == self.destination

    def is_temporarily_blocked(self, cell: Cell) -> bool:
        return cell in self.temporary_blocks

    def get_neighbors(self, cell: Cell) -> List[Cell]:
        """Up, down, left and right neighbours that are not blocked."""
        row, col = cell
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return [c for c in candidates if self.in_bounds(c) and not self.is_blocked(c)]

    # -- costs and conditions ------------------------------------------
    def get_cost(self, cell: Cell) -> float:
        return rules.effective_road_cost(self, cell)

    def get_traffic_level(self, cell: Cell) -> int:
        return self.traffic.get(cell, rules.TRAFFIC_CLEAR)

    def get_signal(self, cell: Cell) -> Optional[str]:
        return self.signals.get(cell)

    # -- changing the city while the simulation runs -------------------
    def block_road(self, cell: Cell) -> None:
        if self.is_open_road(cell):
            self.temporary_blocks.add(cell)

    def unblock_road(self, cell: Cell) -> None:
        self.temporary_blocks.discard(cell)

    def set_traffic(self, cell: Cell, level: int) -> None:
        if not self.in_bounds(cell):
            return
        if level == rules.TRAFFIC_CLEAR:
            self.traffic.pop(cell, None)
        else:
            self.traffic[cell] = level

    def set_signal(self, cell: Cell, state: str) -> None:
        if self.in_bounds(cell):
            self.signals[cell] = state

    def cycle_signal(self, cell: Cell) -> Optional[str]:
        """Flip a signal between red and green; None if there is no signal."""
        current = self.get_signal(cell)
        if current is None:
            return None
        new_state = rules.SIGNAL_GREEN if current == rules.SIGNAL_RED else rules.SIGNAL_RED
        self.set_signal(cell, new_state)
        return new_state


def random_layout(rows: int, cols: int, start: Cell, destination: Cell,
                  blocked_ratio: float = 0.18, seed: Optional[int] = None) -> List[str]:
    """Random city that is guaranteed to have a route from start to destination."""
    rng = random.Random(seed)
    candidates = [(r, c) for r in range(rows) for c in range(cols)
                  if (r, c) not in (start, destination)]
    count = int(len(candidates) * blocked_ratio)

    while True:
        blocked = set(rng.sample(candidates, count))
        if _reachable(rows, cols, blocked, start, destination):
            break

    def symbol(cell: Cell) -> str:
        if cell == start:
            return START_CELL
        if cell == destination:
            return DESTINATION_CELL
        return BLOCKED_ROAD if cell in blocked else OPEN_ROAD

    return ["".join(symbol((r, c)) for c in range(cols)) for r in range(rows)]


def _reachable(rows: int, cols: int, blocked: Set[Cell],
               start: Cell, destination: Cell) -> bool:
    """Breadth-first check used only to validate generated cities."""
    frontier: Deque[Cell] = deque([start])
    seen = {start}
    while frontier:
        row, col = frontier.popleft()
        if (row, col) == destination:
            return True
        for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if (0 <= nxt[0] < rows and 0 <= nxt[1] < cols
                    and nxt not in blocked and nxt not in seen):
                seen.add(nxt)
                frontier.append(nxt)
    return False
