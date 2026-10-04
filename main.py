"""Emergency Vehicle Traffic Planner.

    python main.py                 menu
    python main.py --scenario 3    run one scenario
    python main.py --all           run all four
    python main.py --custom        random city
    python main.py --no-map        text only
"""

from __future__ import annotations

import argparse
from typing import List, Optional

import simulation
import visualization
from simulation import LINE, SCENARIOS, Simulation
from visualization import wrap


def print_intro() -> None:
    print(LINE)
    print("Emergency Vehicle Traffic Planner")
    print(LINE)
    print(wrap("", "An emergency vehicle plans a route with A* search, follows "
                   "simple rules about traffic and signals, and plans again "
                   "when a road on its route is closed.", label_width=0))
    print()
    print("Each step the vehicle perceives the city, decides (move, wait,")
    print("re-plan or stop) and acts. These are its rules:")
    print()
    print(visualization.render_rule_book())
    print()


def print_menu() -> None:
    print("Choose a scenario:")
    for index, scenario in enumerate(SCENARIOS, start=1):
        print(f"  {index}. {scenario.name} ({scenario.subtitle})")
    print(f"  {len(SCENARIOS) + 1}. Random city")
    print("  0. Exit")
    print()


def run_scenario(index: int, show_map: bool, map_every: int) -> None:
    print()
    Simulation(SCENARIOS[index - 1], show_map, map_every).run()


def run_custom(show_map: bool, map_every: int) -> None:
    print()
    Simulation(simulation.random_scenario(), show_map, map_every).run()


def ask(question: str) -> str:
    try:
        return input(question).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def interactive_loop(show_map: bool, map_every: int) -> None:
    random_choice = str(len(SCENARIOS) + 1)
    while True:
        print_menu()
        choice = ask("Select an option: ").lower()
        if choice in ("0", "q", "quit", "exit"):
            print("Goodbye.")
            return
        if choice.isdigit() and 1 <= int(choice) <= len(SCENARIOS):
            run_scenario(int(choice), show_map, map_every)
        elif choice == random_choice:
            run_custom(show_map, map_every)
        elif choice:
            print("Please type a number from the menu.\n")


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emergency Vehicle Traffic Planner")
    parser.add_argument("--scenario", type=int, metavar="N",
                        help=f"run scenario N (1-{len(SCENARIOS)})")
    parser.add_argument("--all", action="store_true", help="run every scenario")
    parser.add_argument("--list", action="store_true", help="list the scenarios")
    parser.add_argument("--custom", action="store_true", help="run a random city")
    parser.add_argument("--no-map", action="store_true", help="don't draw the map")
    parser.add_argument("--map-every", type=int, default=0, metavar="N",
                        help="also draw the map every N steps (default: off)")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_arguments(argv)
    show_map = not args.no_map

    if args.list:
        for index, scenario in enumerate(SCENARIOS, start=1):
            print(f"{index}. {scenario.name}")
            print(wrap("", scenario.purpose, label_width=3))
        return

    print_intro()

    if args.all:
        for index in range(1, len(SCENARIOS) + 1):
            run_scenario(index, show_map, args.map_every)
    elif args.scenario is not None:
        if not 1 <= args.scenario <= len(SCENARIOS):
            print(f"There is no scenario {args.scenario}. "
                  f"Choose 1 to {len(SCENARIOS)}.")
            return
        run_scenario(args.scenario, show_map, args.map_every)
    elif args.custom:
        run_custom(show_map, args.map_every)
    else:
        interactive_loop(show_map, args.map_every)


if __name__ == "__main__":
    main()
