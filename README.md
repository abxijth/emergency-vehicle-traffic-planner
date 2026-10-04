# Emergency Vehicle Traffic Planner

An emergency vehicle drives through a simulated city. It plans a route with
A* search, adjusts for traffic and red lights using a few simple rules, and
plans again if a road on its route gets closed.

Everything is classical AI (informed search plus rule-based reasoning), and the
project uses only the Python standard library.

## Team

| Name | Roll number |
| --- | --- |
| Sarayu | AM.SC.U4AIE25062 |
| Abhijith R Pillai | AM.SC.U4AIE25001 |
| Achyuth Narayana | AM.SC.U4AIE25030 |

## The problem

Getting an ambulance somewhere fast takes more than finding the shortest
road. A longer road with no traffic can be quicker, and a route that was
good a minute ago is useless once an accident closes part of it.

## How it works

The vehicle (`agent.py`) repeats three steps until it arrives:

1. **Perceive:** where am I, what is on the road ahead, is my route still usable?
2. **Decide:** move, wait at a red light, re-plan, or stop.
3. **Act:** drive one cell, or wait.

The city (`environment.py`) is a grid. Each cell has a traffic level (clear,
moderate, heavy), maybe a signal, and may be closed. The vehicle moves up,
down, left or right, never diagonally.

### Road costs (`rules.py`)

| Situation | Cost of entering the cell |
| --- | --- |
| clear road | 1 |
| moderate traffic | 3 |
| heavy traffic | 5 |
| red signal | +2 |
| blocked | not usable |

The rules are plain Python functions, so you can read them top to bottom.
There is no rule engine.

### A* search (`astar.py`)

A* is written by hand with `heapq`. It expands the cell with the lowest
`f = g + h`, where `g` is the cost so far and `h` is the Manhattan distance to
the goal.

Manhattan distance never overestimates here: each move costs at least 1 and
diagonal moves are not allowed, so no path can beat it. That makes the
heuristic admissible and the first route A* returns the cheapest one.

### Re-planning

If the road ahead closes, the agent notices on its next `perceive()`, sees
that its route contains a blocked cell, and runs A* again from where it is
standing.

## Running it

Python 3.8 or newer. Nothing to install.

```bash
python gui.py                  # window with the grid
```

In the window, pick a scenario (or "Random city"), then press **Step** to
advance one move or **Play** to watch it run. **Reset** starts the scenario
again, with a new city if "Random city" is selected. The window opens
maximised, the grid resizes with it, and **F11** toggles full screen
(**Esc** leaves it).

The map is drawn with small pictures: buildings and trees where there is no
road, a barrier and cones where an accident closed a road, cars for traffic
(one car moderate, two heavy), a traffic light for signals, a hospital cross
for the destination and an ambulance for the vehicle. The panel on the right
shows live counters and the same log the command line prints. On Linux,
`tkinter` may need `sudo apt install python3-tk` (Arch: `sudo pacman -S tk`).

Command line:

```bash
python main.py                 # menu
python main.py --scenario 3    # one scenario (3 is the main demo)
python main.py --all           # all four
python main.py --custom        # random city
python main.py --list          # describe the scenarios
python main.py --no-map        # text only
python main.py --map-every 3   # also draw the map every 3 steps
```

By default the map is drawn when a route is planned, when it is re-planned,
and at the end.

## Scenarios

| # | Name | What it shows |
| --- | --- | --- |
| 1 | Normal Traffic | plain A* on a quiet city |
| 2 | Heavy Traffic | a longer route wins because it avoids a jammed street |
| 3 | Dynamic Road Blockage | an accident closes the route; the agent re-plans and waits at a red light |
| 4 | Multiple Blockages | two accidents, two re-plans |

Scenario 2 compares the chosen route with the shortest one:

```
                         moves  real cost
  cost-aware (chosen)       12         12
  distance only             10         24
```

The shortest route is two moves shorter but costs twice as much once the
heavy traffic is counted.

## Reading the map

```
      0   1   2   3   4   5   6
    +---+---+---+---+---+---+---+
  0 | S | * | * | *~| * | . | # |
    +---+---+---+---+---+---+---+
  1 | . | . | # | . | V | # | . |
```

`V` vehicle, `S` start, `D` destination, `#` no road, `X` closed now,
`> < ^ v` planned route, `*` already driven, `~` moderate traffic,
`%` heavy traffic, `R` red light, `G` green light. Row and column numbers
match the `(row,col)` coordinates in the log.

## Results

Each run prints a summary. Typical numbers (times vary by machine):

| Scenario | Moves | Cost paid | A* runs | Cells searched | Re-plans | Waits |
| --- | --- | --- | --- | --- | --- | --- |
| 1 Normal Traffic | 11 | 11 | 1 | 23 | 0 | 0 |
| 2 Heavy Traffic | 12 | 12 | 1 | 12 | 0 | 0 |
| 3 Dynamic Blockage | 14 | 18 | 2 | 48 | 1 | 1 |
| 4 Multiple Blockages | 12 | 16 | 3 | 51 | 2 | 1 |

"Cost paid" can be a little lower than the cost of the plan. A red light adds
2 when planning, but in the simulation the light turns green after one wait,
so the cell then costs 1.

## Files

```
main.py            menu and command line
gui.py             tkinter window (same simulation, drawn on a grid)
icons.py           the pictures used by the window
environment.py     the city: grid, traffic, signals, closures
rules.py           road costs and the IF/THEN rules
astar.py           A* search and Manhattan heuristic
agent.py           the vehicle: perceive, decide, act, re-plan
simulation.py      scenarios, events, the step loop, the report
visualization.py   ASCII map and text formatting
```

## Possible extensions

* Re-plan when traffic gets worse, not only when a road closes.
* Costs that change over time.
* Several vehicles in one city.
* Compare A* with Dijkstra and greedy search on cells searched.
