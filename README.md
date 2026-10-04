# Emergency Vehicle Traffic Planner

An emergency vehicle that finds the cheapest route through a city, accounts
for traffic and red lights, and plans again when an accident closes a road
on its way.

It is classical AI: informed search (A*) plus simple rule-based decisions.
No dependencies beyond the Python standard library.

## Features

* A* search written from scratch, with an admissible Manhattan-distance heuristic
* Cost-aware routing: traffic and red lights change what the "best" route is
* Dynamic re-planning when a road on the route is closed mid-trip
* Four ready-made scenarios and a random city generator
* Desktop GUI (`tkinter`) and a text interface that share the same simulation

## Quick start

You need Python 3.8 or newer. Download or clone the repository, open a
terminal in the project folder, and run:

```bash
python gui.py
```

Pick a scenario, then press **Step** to move one cell or **Play** to watch the
whole trip. On Linux, `tkinter` may need installing first
(Debian/Ubuntu: `sudo apt install python3-tk`, Arch: `sudo pacman -S tk`).

## Usage

### GUI

| Control | What it does |
| --- | --- |
| Dropdown | choose one of the four scenarios, or "Random city" |
| Reset | restart the scenario (a new city for "Random city") |
| Step / Play | advance one move / animate the trip |
| F11, Esc | toggle full screen, leave full screen |

The grid resizes with the window. The panel on the right shows live counters
and a log of what the vehicle decides.

| Picture | Meaning |
| --- | --- |
| Buildings, trees | no road |
| Barrier and cones | road closed by an accident |
| One car / two cars | moderate / heavy traffic |
| Traffic light | signal (red light adds waiting cost) |
| Hospital cross | destination |
| Ambulance | the vehicle |
| Green line / blue dashed line | where it has driven / where it plans to go |

### Command line

```bash
python main.py                 # menu
python main.py --scenario 3    # one scenario (3 is the main demo)
python main.py --all           # all four
python main.py --custom        # random city
python main.py --list          # describe the scenarios
python main.py --no-map        # text only
python main.py --map-every 3   # also draw the map every 3 steps
```

By default the ASCII map is drawn when a route is planned, when it is
re-planned, and at the end. Symbols: `V` vehicle, `S` start, `D` destination,
`#` no road, `X` closed, `> < ^ v` planned route, `*` driven, `~` moderate
traffic, `%` heavy traffic, `R` / `G` red / green light. Row and column
numbers on the map match the `(row,col)` coordinates in the log.

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

### Example run (scenario 3)

```
Route found: 10 moves, cost 12, 26 cells searched, 0.14 ms
    (0,0) -> (0,1) -> (0,2) -> (0,3) -> (0,4) -> (1,4) -> (2,4)
    -> (2,5) -> (2,6) -> (3,6) -> (4,6)
  Step  4  (0,3) -> (0,4)  cost 1  paid 6  left 6
  Step  5  (0,4) -> (1,4)  cost 1  paid 7  left 5
  [after step 5] an accident is reported ahead: road (2,5) is closed
  !! Road (2,5) on the route is closed. Re-planning.
  New route: 9 moves, cost 13, 22 cells searched, 0.10 ms
    (1,4) -> (2,4) -> (2,3) -> (3,3) -> (4,3) -> (5,3) -> (5,4)
    -> (5,5) -> (4,5) -> (4,6)
  Step 12  (5,4)  waiting: red light at (5,5), changes to green
  Step 15  (4,5) -> (4,6)  cost 1  paid 18  left 0
  Arrived at (4,6).
```

## How it works

The vehicle (`agent.py`) repeats three steps until it arrives:

1. **Perceive:** where am I, what is ahead, is my route still usable?
2. **Decide:** move, wait at a red light, re-plan, or stop.
3. **Act:** drive one cell, or wait.

The city (`environment.py`) is a grid. Each cell has a traffic level, maybe a
signal, and may be closed. The vehicle moves up, down, left or right.

**Road costs** (`rules.py`):

| Situation | Cost of entering the cell |
| --- | --- |
| clear road | 1 |
| moderate traffic | 3 |
| heavy traffic | 5 |
| red signal | +2 |
| blocked | not usable |

The rules are plain Python functions, so they can be read top to bottom.

**A\* search** (`astar.py`) expands the cell with the lowest `f = g + h`, where
`g` is the cost so far and `h` is the Manhattan distance to the goal. Each move
costs at least 1 and diagonal moves are not allowed, so `h` never overestimates.
That makes it admissible, and the first route A* returns is the cheapest.

**Re-planning:** if a road ahead closes, the agent sees on its next
`perceive()` that its route contains a blocked cell and runs A* again from where
it is standing.

## Results

Numbers printed in each run's summary (times vary by machine):

| Scenario | Moves | Cost paid | A* runs | Cells searched | Re-plans | Waits |
| --- | --- | --- | --- | --- | --- | --- |
| 1 Normal Traffic | 11 | 11 | 1 | 23 | 0 | 0 |
| 2 Heavy Traffic | 12 | 12 | 1 | 12 | 0 | 0 |
| 3 Dynamic Blockage | 14 | 18 | 2 | 48 | 1 | 1 |
| 4 Multiple Blockages | 12 | 16 | 3 | 51 | 2 | 1 |

A red light adds 2 to the plan, but in the simulation it turns green after one
wait, so the cell then costs 1. That is why "cost paid" can be slightly below
the planned cost.

## Project structure

```
main.py            menu and command line
gui.py             tkinter window
icons.py           pictures used by the window
environment.py     the city: grid, traffic, signals, closures
rules.py           road costs and the IF/THEN rules
astar.py           A* search and Manhattan heuristic
agent.py           the vehicle: perceive, decide, act, re-plan
simulation.py      scenarios, events, step loop, report
visualization.py   ASCII map and text formatting
```

## Team

| Name | Roll number |
| --- | --- |
| Sarayu | AM.SC.U4AIE25062 |
| Abhijith R Pillai | AM.SC.U4AIE25001 |
| Achyuth Narayana | AM.SC.U4AIE25030 |

## Ideas for extending it

* Re-plan when traffic gets worse, not only when a road closes
* Costs that change over time
* Several vehicles in one city
* Compare A* with Dijkstra and greedy search on cells searched
