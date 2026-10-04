"""The emergency vehicle agent.

Each step it perceives, decides and acts:

    perceive  read position, route, roads ahead, signals
    decide    move, wait at a red light, re-plan, or stop
    act       drive one cell, or wait

It also keeps counters for the final report.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import astar
import rules
from astar import SearchResult
from environment import Cell, Environment

MOVE = "MOVE"
WAIT = "WAIT"
ARRIVE = "ARRIVE"
REPLAN = "REPLAN"


@dataclass
class Perception:
    """What the agent knows at one moment."""

    position: Cell
    next_cell: Optional[Cell]
    remaining_route: List[Cell]
    planned_cost: float
    blocking_cell: Optional[Cell]   # first unusable cell on the route, if any
    signal_ahead: Optional[Cell]    # next cell, if it has a red signal
    at_destination: bool

    @property
    def route_valid(self) -> bool:
        return self.blocking_cell is None


@dataclass
class Decision:
    kind: str
    target: Optional[Cell]
    reason: str


class EmergencyVehicleAgent:
    def __init__(self, env: Environment) -> None:
        self.env = env
        self.destination = env.destination
        self.position: Cell = env.start
        self.route: List[Cell] = []
        self.route_index = 0
        self.trail: List[Cell] = [env.start]   # cells driven so far

        # Counters for the final report.
        self.astar_calls = 0
        self.replans = 0
        self.distance_travelled = 0
        self.cost_paid = 0.0
        self.wait_events = 0
        self.nodes_explored = 0
        self.planning_time_ms = 0.0
        self.replan_time_ms = 0.0
        self.initial_route_cost = 0.0

    # -- perceive ------------------------------------------------------
    def perceive(self) -> Perception:
        remaining = self.remaining_route()
        next_cell = remaining[1] if len(remaining) > 1 else None
        signal_ahead = (next_cell if next_cell is not None
                        and rules.signal_is_red(self.env, next_cell) else None)
        return Perception(
            position=self.position,
            next_cell=next_cell,
            remaining_route=remaining,
            planned_cost=self.remaining_route_cost(),
            blocking_cell=rules.first_blocked_cell(self.env, remaining),
            signal_ahead=signal_ahead,
            at_destination=rules.has_reached(self.position, self.destination),
        )

    # -- planning ------------------------------------------------------
    def plan_route(self) -> SearchResult:
        """Run A* for the first time."""
        result = self._search()
        self.planning_time_ms += result.elapsed_ms
        self.initial_route_cost = result.cost
        return result

    def replan(self) -> SearchResult:
        """Run A* again from the current cell."""
        result = self._search()
        self.replans += 1
        self.replan_time_ms += result.elapsed_ms
        return result

    def _search(self) -> SearchResult:
        result = astar.astar(self.env, self.position, self.destination)
        self.astar_calls += 1
        self.nodes_explored += result.nodes_explored
        self.route = list(result.path)
        self.route_index = 0
        return result

    # -- decide --------------------------------------------------------
    def decide(self, p: Perception) -> Decision:
        if p.at_destination:
            return Decision(ARRIVE, self.position, "destination reached")
        if not self.route:
            return Decision(REPLAN, self.position, "no route planned yet")
        if not p.route_valid:
            return Decision(REPLAN, p.blocking_cell,
                            f"road {_fmt(p.blocking_cell)} on the route is closed")
        if p.signal_ahead is not None:
            return Decision(WAIT, p.signal_ahead,
                            f"red light at {_fmt(p.signal_ahead)}")
        if p.next_cell is not None and not self.env.is_blocked(p.next_cell):
            return Decision(MOVE, p.next_cell, "next road is open")
        return Decision(REPLAN, self.position, "next road cannot be entered")

    # -- act -----------------------------------------------------------
    def act(self, decision: Decision) -> None:
        if decision.kind == MOVE and decision.target is not None:
            self.cost_paid += self.env.get_cost(decision.target)
            self.distance_travelled += 1
            self.position = decision.target
            self.route_index += 1
            self.trail.append(self.position)
        elif decision.kind == WAIT:
            self.wait_events += 1

    # -- the current plan ----------------------------------------------
    def remaining_route(self) -> List[Cell]:
        return self.route[self.route_index:] if self.route else []

    def remaining_route_cost(self) -> float:
        return sum(self.env.get_cost(cell) for cell in self.remaining_route()[1:])

    def has_reached_destination(self) -> bool:
        return rules.has_reached(self.position, self.destination)


def _fmt(cell: Optional[Cell]) -> str:
    return "(none)" if cell is None else f"({cell[0]},{cell[1]})"
