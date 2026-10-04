"""Rules: how road conditions turn into costs and decisions.

Each rule is a small function that reads one fact and returns a result,
so the logic can be read straight from the code.

    road blocked          -> unusable (infinite cost)
    traffic moderate      -> cost 3
    traffic heavy         -> cost 5
    signal red            -> add 2 for the wait
    route has blocked road-> re-plan
    destination reached   -> stop
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from environment import Cell, Environment

TRAFFIC_CLEAR = 0
TRAFFIC_MODERATE = 1
TRAFFIC_HEAVY = 2

TRAFFIC_COST = {TRAFFIC_CLEAR: 1.0, TRAFFIC_MODERATE: 3.0, TRAFFIC_HEAVY: 5.0}
TRAFFIC_NAMES = {TRAFFIC_CLEAR: "clear", TRAFFIC_MODERATE: "moderate",
                 TRAFFIC_HEAVY: "heavy"}

SIGNAL_RED = "red"
SIGNAL_GREEN = "green"
SIGNAL_WAIT_COST = 2.0

BLOCKED_COST = float("inf")


def effective_road_cost(env: "Environment", cell: "Cell") -> float:
    """Cost of driving into ``cell`` under current conditions."""
    if env.is_blocked(cell):
        return BLOCKED_COST
    cost = TRAFFIC_COST.get(env.get_traffic_level(cell), TRAFFIC_COST[TRAFFIC_CLEAR])
    if signal_is_red(env, cell):
        cost += SIGNAL_WAIT_COST
    return cost


def describe_cell(env: "Environment", cell: "Cell") -> str:
    """Short note about a road, e.g. ``heavy traffic, red light``."""
    level = env.get_traffic_level(cell)
    parts = []
    if level != TRAFFIC_CLEAR:
        parts.append(f"{TRAFFIC_NAMES[level]} traffic")
    signal = env.get_signal(cell)
    if signal:
        parts.append(f"{signal} light")
    return ", ".join(parts)


def first_blocked_cell(env: "Environment", route: List["Cell"]) -> Optional["Cell"]:
    """First cell of ``route`` that can no longer be used, or None."""
    for cell in route:
        if env.is_blocked(cell):
            return cell
    return None


def signal_is_red(env: "Environment", cell: "Cell") -> bool:
    return env.get_signal(cell) == SIGNAL_RED


def has_reached(position: "Cell", destination: "Cell") -> bool:
    return position == destination


def rule_book() -> List[Tuple[str, str]]:
    """(condition, conclusion) pairs, printed at start-up."""
    return [
        ("road is blocked", "road is unusable (cost = infinity)"),
        ("traffic is clear", f"road cost = {TRAFFIC_COST[TRAFFIC_CLEAR]:g}"),
        ("traffic is moderate", f"road cost = {TRAFFIC_COST[TRAFFIC_MODERATE]:g}"),
        ("traffic is heavy", f"road cost = {TRAFFIC_COST[TRAFFIC_HEAVY]:g}"),
        ("signal is red", f"add waiting cost {SIGNAL_WAIT_COST:g}"),
        ("route contains a blocked road", "re-plan with A*"),
        ("next road has a red signal", "wait until it changes"),
        ("vehicle is at the destination", "stop"),
    ]
