"""ASCII map of the city and a few text-formatting helpers.

Each cell is three characters wide: a space, the main symbol, and a tag.

     V   vehicle        S   start          D   destination
     .   open road      #   no road        X   closed right now
     >   planned route (arrow = direction of travel)
     *   already driven
    ~ / %   tag: moderate / heavy traffic
    R / G   tag: red / green signal
"""

from __future__ import annotations

import textwrap
from typing import Dict, List, Optional

import rules
from environment import Cell, Environment

WIDTH = 64
ARROWS = {(-1, 0): "^", (1, 0): "v", (0, 1): ">", (0, -1): "<"}


def fmt_cell(cell: Cell) -> str:
    return f"({cell[0]},{cell[1]})"


def format_path(path: List[Cell], indent: int = 4) -> str:
    """Path as ``(0,0) -> (0,1) -> ...``, wrapped to the page width."""
    if not path:
        return "(no path)"
    text = " -> ".join(fmt_cell(c) for c in path)
    return textwrap.fill(text, WIDTH, initial_indent=" " * indent,
                         subsequent_indent=" " * indent, break_long_words=False)


def wrap(label: str, text: str, label_width: int = 9) -> str:
    """``label  text`` with continuation lines aligned under the text."""
    pad = " " * (2 + label_width)
    return textwrap.fill(text, WIDTH, initial_indent=f"  {label:<{label_width}}",
                         subsequent_indent=pad)


def route_arrows(route: List[Cell]) -> Dict[Cell, str]:
    arrows: Dict[Cell, str] = {}
    for here, nxt in zip(route, route[1:]):
        arrows[here] = ARROWS.get((nxt[0] - here[0], nxt[1] - here[1]), ".")
    return arrows


def _cell_text(env: Environment, cell: Cell, arrow: Optional[str],
               vehicle: Optional[Cell], trail: set) -> str:
    if cell == vehicle:
        return " V "
    if env.is_start(cell):
        return " S "
    if env.is_destination(cell):
        return " D "
    if env.is_temporarily_blocked(cell):
        return " X "
    if not env.is_open_road(cell):
        return " # "

    main = arrow or ("*" if cell in trail else ".")
    level = env.get_traffic_level(cell)
    if rules.signal_is_red(env, cell):
        tag = "R"
    elif env.get_signal(cell) == rules.SIGNAL_GREEN:
        tag = "G"
    elif level == rules.TRAFFIC_HEAVY:
        tag = "%"
    elif level == rules.TRAFFIC_MODERATE:
        tag = "~"
    else:
        tag = " "
    return f" {main}{tag}"


def render_city(env: Environment, route: Optional[List[Cell]] = None,
                vehicle: Optional[Cell] = None,
                trail: Optional[List[Cell]] = None) -> str:
    """Draw the city with row and column numbers."""
    arrows = route_arrows(route) if route else {}
    driven = set(trail or [])
    border = "    +" + "+".join("---" for _ in range(env.cols)) + "+"
    header = ("     " + " ".join(f"{c:^3}" for c in range(env.cols))).rstrip()

    lines = [header, border]
    for row in range(env.rows):
        cells = "|".join(_cell_text(env, (row, col), arrows.get((row, col)),
                                    vehicle, driven) for col in range(env.cols))
        lines.append(f"{row:>3} |{cells}|")
        lines.append(border)
    return "\n".join(lines)


def legend() -> str:
    t = rules.TRAFFIC_COST
    return "\n".join([
        "  V vehicle   S start   D destination   # no road   X closed now",
        "  > < ^ v planned route   * already driven",
        "  ~ moderate traffic   % heavy traffic   R red light   G green light",
        f"  cost per road: clear {t[rules.TRAFFIC_CLEAR]:g}, "
        f"moderate {t[rules.TRAFFIC_MODERATE]:g}, "
        f"heavy {t[rules.TRAFFIC_HEAVY]:g}, red light +{rules.SIGNAL_WAIT_COST:g}",
    ])


def render_rule_book() -> str:
    pairs = rules.rule_book()
    width = max(len(condition) for condition, _ in pairs)
    return "\n".join(f"  IF {condition:<{width}}  THEN {conclusion}"
                     for condition, conclusion in pairs)
