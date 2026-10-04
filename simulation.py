"""Scenarios, the simulation loop, and the printed report.

The simulation sets up the city, lets it change while the vehicle drives,
and prints what happens. All decisions are made by the agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import random

import astar
import environment
import rules
import visualization
from agent import MOVE, REPLAN, WAIT, EmergencyVehicleAgent
from environment import Cell, Environment
from visualization import WIDTH, fmt_cell, wrap

LINE = "=" * WIDTH
THIN_LINE = "-" * WIDTH


@dataclass
class Event:
    """A change to the city, applied once ``step`` steps have been taken.

    kind is one of:
        block         close the road at ``cell``
        unblock       reopen the road at ``cell``
        traffic       set traffic at ``cell`` to ``value``
        signal        set the signal at ``cell`` to ``value``
        block_ahead   close the road ``steps_ahead`` cells ahead on the route
    """

    step: int
    kind: str
    message: str
    cell: Optional[Cell] = None
    steps_ahead: int = 2
    value: object = None


@dataclass
class Scenario:
    name: str
    subtitle: str
    purpose: str
    layout: List[str]
    traffic: Dict[Cell, int] = field(default_factory=dict)
    signals: Dict[Cell, str] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    compare_with_distance_only: bool = False


SCENARIOS: List[Scenario] = [
    Scenario(
        name="Normal Traffic",
        subtitle="basic A* search",
        purpose="A quiet city. A* finds the cheapest route and the vehicle "
                "drives it. Nothing goes wrong.",
        layout=[
            "S.......",
            "..#.....",
            "..#.....",
            "......#.",
            ".##...#.",
            "......D.",
        ],
        traffic={(0, 3): rules.TRAFFIC_MODERATE, (0, 4): rules.TRAFFIC_MODERATE},
        signals={(2, 6): rules.SIGNAL_GREEN},
    ),
    Scenario(
        name="Heavy Traffic",
        subtitle="cost-aware planning",
        purpose="The short street is jammed. A* weighs the cost of each road, "
                "not just its length, so the vehicle takes the longer ring "
                "road instead.",
        layout=[
            "S.......",
            ".######.",
            ".######.",
            ".######.",
            "......D.",
        ],
        traffic={(1, 0): rules.TRAFFIC_HEAVY,
                 (2, 0): rules.TRAFFIC_HEAVY,
                 (3, 0): rules.TRAFFIC_HEAVY,
                 (4, 4): rules.TRAFFIC_MODERATE},
        signals={(0, 4): rules.SIGNAL_GREEN},
        compare_with_distance_only=True,
    ),
    Scenario(
        name="Dynamic Road Blockage",
        subtitle="main demonstration",
        purpose="An accident closes a road on the planned route while the "
                "vehicle is driving. The agent notices, runs A* again and "
                "finishes on a new route.",
        layout=[
            "S.....#",
            "..#..#.",
            "..#....",
            "....#..",
            "##..#.D",
            ".......",
        ],
        traffic={(0, 3): rules.TRAFFIC_MODERATE,
                 (5, 3): rules.TRAFFIC_MODERATE},
        signals={(5, 5): rules.SIGNAL_RED},
        events=[Event(step=5, kind="block_ahead", steps_ahead=2,
                      message="an accident is reported ahead")],
    ),
    Scenario(
        name="Multiple Blockages",
        subtitle="a more constrained city",
        purpose="Many closed roads and two accidents during the trip. The "
                "agent has to re-plan twice.",
        layout=[
            "S...#....",
            "..#.#..#.",
            "..#.....#",
            "#...#....",
            "....#...D",
            "#..#.....",
            "......#..",
        ],
        traffic={(2, 4): rules.TRAFFIC_MODERATE,
                 (3, 6): rules.TRAFFIC_MODERATE},
        signals={(4, 6): rules.SIGNAL_RED},
        events=[
            Event(step=6, kind="block_ahead", steps_ahead=2,
                  message="road works have started"),
            Event(step=9, kind="block_ahead", steps_ahead=1,
                  message="a second accident happens right ahead"),
        ],
    ),
]


class Simulation:
    """Runs one scenario from the first plan to arrival (or failure)."""

    def __init__(self, scenario: Scenario, show_map: bool = True,
                 map_every: int = 0, stream=print) -> None:
        self.scenario = scenario
        self.show_map = show_map
        self.map_every = max(0, map_every)   # 0 = only at key moments
        self.write = stream

        self.env = Environment(scenario.layout)
        for cell, level in scenario.traffic.items():
            self.env.set_traffic(cell, level)
        for cell, state in scenario.signals.items():
            self.env.set_signal(cell, state)

        self.agent = EmergencyVehicleAgent(self.env)
        self.outcome = "not started"
        self.steps = 0
        self.max_steps = 4 * self.env.rows * self.env.cols

    # -- main loop -----------------------------------------------------
    def run(self) -> str:
        """Run the whole scenario, printing as it goes."""
        self._print_header()
        if self.start():
            while self.step():
                pass
        return self.finish()

    def start(self) -> bool:
        """Plan the first route. False if there is none."""
        self._section("Planning the first route")
        first = self.agent.plan_route()
        if not first.found:
            self.write("  No route exists. The mission cannot start.")
            self.outcome = "no route"
            return False
        self._print_plan("Route found", first)
        self._print_map()
        if self.scenario.compare_with_distance_only:
            self._compare_with_distance_only(first)
        self._section("Driving")
        return True

    def step(self) -> bool:
        """One perceive-decide-act cycle. False once the run is over."""
        agent = self.agent
        if agent.has_reached_destination():
            return False
        if self.steps >= self.max_steps:
            self.outcome = f"gave up after {self.max_steps} steps"
            return False

        self._apply_events(self.steps)
        perception = agent.perceive()
        decision = agent.decide(perception)

        if decision.kind == REPLAN:
            self.write(f"  !! {decision.reason.capitalize()}. Re-planning.")
            result = agent.replan()
            if not result.found:
                self.write("  No alternative route exists. Giving up.")
                self.outcome = "no route left"
                return False
            self._print_plan("New route", result)
            self._print_map()
            perception = agent.perceive()
            decision = agent.decide(perception)

        before = agent.position
        move_cost = (self.env.get_cost(decision.target)
                     if decision.kind == MOVE else 0.0)
        note = (rules.describe_cell(self.env, decision.target)
                if decision.kind == MOVE else "")
        agent.act(decision)
        self.steps += 1
        self._print_step(decision, before, move_cost, note)

        if (self.show_map and self.map_every and self.steps % self.map_every == 0
                and not agent.has_reached_destination()):
            self._print_map()
        return not agent.has_reached_destination()

    def finish(self) -> str:
        """Set the outcome, print the final map and the summary."""
        if self.agent.has_reached_destination():
            self.outcome = "destination reached"
            self.write(f"\n  Arrived at {fmt_cell(self.agent.position)}.\n")
        elif self.outcome == "not started":
            self.outcome = "stopped"
        self._print_map()
        self._print_report()
        return self.outcome

    # -- changes to the city -------------------------------------------
    def _apply_events(self, step: int) -> None:
        for event in self.scenario.events:
            if event.step != step:
                continue

            cell = event.cell
            if event.kind == "block_ahead":
                cell = self._cell_ahead(event.steps_ahead)
            if cell is None:
                continue

            prefix = f"  [after step {step}]"
            if event.kind in ("block", "block_ahead"):
                if self.env.is_destination(cell):
                    continue   # never close the destination itself
                self.env.block_road(cell)
                self.write(f"{prefix} {event.message}: road {fmt_cell(cell)} is closed")
            elif event.kind == "unblock":
                self.env.unblock_road(cell)
                self.write(f"{prefix} road {fmt_cell(cell)} is open again")
            elif event.kind == "traffic":
                level = int(event.value)
                self.env.set_traffic(cell, level)
                self.write(f"{prefix} road {fmt_cell(cell)} now has "
                           f"{rules.TRAFFIC_NAMES[level]} traffic")
            elif event.kind == "signal":
                self.env.set_signal(cell, str(event.value))
                self.write(f"{prefix} signal at {fmt_cell(cell)} is {event.value}")

    def _cell_ahead(self, steps_ahead: int) -> Optional[Cell]:
        route = self.agent.remaining_route()
        return route[steps_ahead] if steps_ahead < len(route) else None

    # -- printing ------------------------------------------------------
    def _print_header(self) -> None:
        s, env = self.scenario, self.env
        self.write(LINE)
        self.write(f"{s.name} ({s.subtitle})")
        self.write(LINE)
        self.write(wrap("Purpose", s.purpose))
        self.write(f"  {'Start':<9}{fmt_cell(env.start)}")
        self.write(f"  {'Goal':<9}{fmt_cell(env.destination)}")
        self.write(f"  {'City':<9}{env.rows} x {env.cols}")
        self.write(wrap("Traffic", _describe_traffic(s.traffic)))
        self.write(wrap("Signals", _describe_signals(s.signals)))
        self.write(wrap("Events", _describe_events(s.events)))
        self.write()
        if self.show_map:
            self.write(visualization.legend())
            self.write()

    def _section(self, title: str) -> None:
        self.write(THIN_LINE)
        self.write(title)
        self.write(THIN_LINE)

    def _print_map(self) -> None:
        if not self.show_map:
            return
        self.write(visualization.render_city(
            self.env, self.agent.remaining_route(), self.agent.position,
            self.agent.trail))
        self.write()

    def _print_plan(self, title: str, result: astar.SearchResult) -> None:
        self.write(f"  {title}: {result.moves} moves, cost {result.cost:g}, "
                   f"{result.nodes_explored} cells searched, "
                   f"{result.elapsed_ms:.2f} ms")
        self.write(visualization.format_path(result.path))
        self.write()

    def _print_step(self, decision, before: Cell, move_cost: float,
                    note: str) -> None:
        label = f"  Step {self.steps:>2}  "
        if decision.kind == MOVE:
            left = self.agent.remaining_route_cost()
            line = (f"{label}{fmt_cell(before)} -> {fmt_cell(decision.target)}"
                    f"  cost {move_cost:g}  paid {self.agent.cost_paid:g}"
                    f"  left {left:g}")
            self.write(f"{line}  {note}".rstrip())
        elif decision.kind == WAIT:
            new_state = self.env.cycle_signal(decision.target)
            self.write(f"{label}{fmt_cell(before)}  waiting: {decision.reason}, "
                       f"changes to {new_state}")
        else:
            self.write(f"{label}{fmt_cell(before)}  {decision.kind.lower()}: "
                       f"{decision.reason}")

    def _compare_with_distance_only(self, chosen: astar.SearchResult) -> None:
        """Show what a planner that ignores traffic would have chosen."""
        shortest = astar.astar(self.env, self.env.start, self.env.destination,
                               cost_function=lambda cell: 1.0)
        # Price the short route with the real traffic costs.
        real_cost = sum(self.env.get_cost(c) for c in shortest.path[1:])

        self.write("  Same search, ignoring traffic (distance only):")
        self.write(f"    {'':<22}{'moves':>6}{'real cost':>11}")
        self.write(f"    {'cost-aware (chosen)':<22}{chosen.moves:>6}{chosen.cost:>11g}")
        self.write(f"    {'distance only':<22}{shortest.moves:>6}{real_cost:>11g}")
        self.write(f"  The vehicle drives {chosen.moves - shortest.moves} extra "
                   f"moves to save {real_cost - chosen.cost:g} in cost.")
        self.write()

    def _print_report(self) -> None:
        a = self.agent
        rows = [
            ("Outcome", self.outcome),
            ("Steps (moves + waits)", self.steps),
            ("Moves", a.distance_travelled),
            ("Waits at red lights", a.wait_events),
            ("Travel cost paid", f"{a.cost_paid:g}"),
            ("First route cost", f"{a.initial_route_cost:g}"),
            ("A* runs", a.astar_calls),
            ("Re-plans", a.replans),
            ("Cells searched (total)", a.nodes_explored),
            ("First planning time", f"{a.planning_time_ms:.2f} ms"),
            ("Re-planning time", f"{a.replan_time_ms:.2f} ms"),
        ]
        self.write(LINE)
        self.write("Summary")
        self.write(THIN_LINE)
        for label, value in rows:
            self.write(f"  {label:<26}{value}")
        self.write(LINE)
        self.write()


def _describe_traffic(traffic: Dict[Cell, int]) -> str:
    if not traffic:
        return "none"
    return ", ".join(f"{fmt_cell(c)} {rules.TRAFFIC_NAMES[lvl]}"
                     for c, lvl in sorted(traffic.items()))


def _describe_signals(signals: Dict[Cell, str]) -> str:
    if not signals:
        return "none"
    return ", ".join(f"{fmt_cell(c)} {state}" for c, state in sorted(signals.items()))


def _describe_events(events: List[Event]) -> str:
    if not events:
        return "none"
    return "; ".join(f"after step {e.step}: {e.message}" for e in events)


def random_scenario() -> Scenario:
    """A random city with random traffic and signals, plus one accident."""
    rows, cols = random.randint(5, 7), random.randint(6, 9)
    start, goal = (0, 0), (rows - 1, cols - 1)
    layout = environment.random_layout(rows, cols, start, goal,
                                       blocked_ratio=random.uniform(0.10, 0.22))
    cells = [(r, c) for r in range(rows) for c in range(cols)
             if (r, c) not in (start, goal)]
    return Scenario(
        name="Random City",
        subtitle="random traffic and signals",
        purpose="A randomly generated city with one accident on the route.",
        layout=layout,
        traffic={c: random.choice([rules.TRAFFIC_MODERATE, rules.TRAFFIC_HEAVY])
                 for c in cells if random.random() < 0.25},
        signals={c: rules.SIGNAL_RED for c in cells if random.random() < 0.08},
        events=[Event(step=3, kind="block_ahead", steps_ahead=2,
                      message="an accident is reported ahead")],
    )
