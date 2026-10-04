"""Small tkinter front end for the planner.  Run: python gui.py

Pick a scenario, then press Step or Play. It uses the same Simulation as
the command line version. F11 toggles full screen, Escape leaves it.
"""

import tkinter as tk
from tkinter import ttk

import icons
import rules
from simulation import SCENARIOS, Simulation, random_scenario

DELAY_MS = 350
BG, ROAD, GROUND = "#e6eaee", "#f5f5f2", "#c9d1c3"
TRAFFIC = {rules.TRAFFIC_MODERATE: "#fbf0c0", rules.TRAFFIC_HEAVY: "#f8d3a8"}
CLOSED = "#f6d5d5"

LEGEND = "blue dashed = planned route    green = driven    traffic: 1 car = moderate, 2 cars = heavy"
STATS = ["Step", "Moves", "Cost paid", "Plan cost left", "Re-plans", "Red-light waits"]


class App:
    def __init__(self, root: tk.Tk) -> None:
        root.title("Emergency Vehicle Traffic Planner")
        root.geometry("1200x720")
        self.root = root
        self.playing = False
        self.done = False
        self.facing = 1
        self.cw, self.ch = 700, 560
        self.fullscreen = False

        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        bar = tk.Frame(root)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        self.choice = ttk.Combobox(
            bar, state="readonly", width=26, font=("Helvetica", 11),
            values=[s.name for s in SCENARIOS] + ["Random city"])
        self.choice.current(2)
        self.choice.bind("<<ComboboxSelected>>", lambda _: self.load())
        self.choice.pack(side="left")
        for text, command in (("Reset", self.load), ("Step", self.advance)):
            tk.Button(bar, text=text, width=7, command=command).pack(side="left", padx=4)
        self.play_button = tk.Button(bar, text="Play", width=7, command=self.toggle_play)
        self.play_button.pack(side="left")
        tk.Button(bar, text="Full screen (F11)", command=self.toggle_fullscreen).pack(side="right")

        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(8, 4))
        self.canvas.bind("<Configure>", self.on_resize)

        side = tk.Frame(root)
        side.grid(row=1, column=1, sticky="nsew", padx=(4, 8))
        self.status = tk.StringVar()
        tk.Label(side, textvariable=self.status, font=("Helvetica", 15, "bold"),
                 anchor="w").pack(fill="x")
        table = tk.Frame(side)
        table.pack(fill="x", pady=6)
        self.stats = {}
        for i, name in enumerate(STATS):
            self.stats[name] = tk.StringVar()
            tk.Label(table, text=name, anchor="w", fg="#555",
                     font=("Helvetica", 11)).grid(row=i, column=0, sticky="w")
            tk.Label(table, textvariable=self.stats[name], anchor="e",
                     font=("Helvetica", 12, "bold")).grid(row=i, column=1, sticky="e", padx=16)
        self.log = tk.Text(side, width=48, state="disabled", wrap="word",
                           font=("Courier", 11), bg="#fafafa")
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("alert", foreground="#b3261e")

        tk.Label(root, text=LEGEND, fg="#555", anchor="w").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6))

        root.bind("<F11>", lambda _: self.toggle_fullscreen())
        root.bind("<Escape>", lambda _: self.toggle_fullscreen(False))
        self.maximize()
        self.load()

    def maximize(self) -> None:
        for apply in (lambda: self.root.state("zoomed"),
                      lambda: self.root.attributes("-zoomed", True)):
            try:
                apply()
                return
            except tk.TclError:
                pass

    def toggle_fullscreen(self, on=None) -> None:
        self.fullscreen = (not self.fullscreen) if on is None else on
        self.root.attributes("-fullscreen", self.fullscreen)

    # -- scenario setup ------------------------------------------------
    def load(self) -> None:
        """(Re)start the chosen scenario. 'Random city' makes a new city each time."""
        self.playing = False
        self.play_button.config(text="Play")
        self.facing = 1
        index = self.choice.current()
        scenario = SCENARIOS[index] if index < len(SCENARIOS) else random_scenario()

        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

        self.sim = Simulation(scenario, show_map=False, stream=self.say)
        self.say(scenario.purpose)
        self.done = not self.sim.start()
        if self.done:
            self.sim.finish()
        self.draw()

    def say(self, text: str = "") -> None:
        """Log line from the simulation. Blank lines and rulers are dropped."""
        if not text.strip() or set(text.strip()) <= {"-", "="}:
            return
        alert = "alert" if "!!" in text or "[after" in text else ""
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", alert)
        self.log.see("end")
        self.log.config(state="disabled")

    # -- running -------------------------------------------------------
    def advance(self) -> None:
        if self.done:
            return
        if not self.sim.step():
            self.done = True
            self.sim.finish()
        self.draw()

    def toggle_play(self) -> None:
        self.playing = not self.playing and not self.done
        self.play_button.config(text="Pause" if self.playing else "Play")
        if self.playing:
            self.tick()

    def tick(self) -> None:
        if not self.playing:
            return
        self.advance()
        if self.done:
            self.toggle_play()
        else:
            self.root.after(DELAY_MS, self.tick)

    def on_resize(self, event) -> None:
        self.cw, self.ch = event.width, event.height
        self.draw()

    # -- drawing -------------------------------------------------------
    def draw(self) -> None:
        env, agent, c = self.sim.env, self.sim.agent, self.canvas
        s = max(16, int(min(self.cw / env.cols, self.ch / env.rows)))
        ox = (self.cw - s * env.cols) / 2
        oy = (self.ch - s * env.rows) / 2
        c.delete("all")

        for row in range(env.rows):
            for col in range(env.cols):
                self.draw_cell(env, (row, col), ox + col * s, oy + row * s, s)

        def center(cell):
            return ox + (cell[1] + .5) * s, oy + (cell[0] + .5) * s

        self.line([center(p) for p in agent.trail], "#2a9d4f", max(3, s // 12))
        self.line([center(p) for p in agent.remaining_route()], "#2477d6",
                  max(3, s // 14), dash=(6, 4))

        if len(agent.trail) > 1:
            dx = agent.trail[-1][1] - agent.trail[-2][1]
            self.facing = 1 if dx > 0 else -1 if dx < 0 else self.facing
        cx, cy = center(agent.position)
        icons.ambulance(c, cx, cy, s * .8, self.facing, self.sim.steps % 2 == 0)
        self.update_panel()

    def draw_cell(self, env, cell, x, y, s) -> None:
        c = self.canvas
        if not env.is_open_road(cell):
            c.create_rectangle(x, y, x + s, y + s, fill=GROUND, outline="#b3bcad")
            icons.building(c, x, y, s, (cell[0] * 3 + cell[1] * 5) % 3)
            return
        if env.is_temporarily_blocked(cell):
            fill = CLOSED
        else:
            fill = TRAFFIC.get(env.get_traffic_level(cell), ROAD)
        c.create_rectangle(x, y, x + s, y + s, fill=fill, outline="#cfcfcf")

        if env.is_temporarily_blocked(cell):
            icons.barrier(c, x, y, s)
        else:
            colors = icons.CAR_COLORS
            k = cell[0] * 7 + cell[1] * 3
            level = env.get_traffic_level(cell)
            if level == rules.TRAFFIC_MODERATE:
                icons.sedan(c, x + .5 * s, y + .74 * s, .5 * s, colors[k % 6])
            elif level == rules.TRAFFIC_HEAVY:
                icons.sedan(c, x + .32 * s, y + .30 * s, .42 * s, colors[k % 6])
                icons.sedan(c, x + .68 * s, y + .76 * s, .42 * s, colors[(k + 2) % 6])
        if env.is_destination(cell):
            icons.hospital(c, x, y, s)
        if env.is_start(cell):
            icons.start_badge(c, x, y, s)
        signal = env.get_signal(cell)
        if signal:
            icons.signal(c, x, y, s, signal)

    def line(self, points, color, width, dash=None) -> None:
        if len(points) > 1:
            flat = [value for point in points for value in point]
            self.canvas.create_line(*flat, fill=color, width=width, dash=dash,
                                    capstyle="round", joinstyle="round")

    def update_panel(self) -> None:
        agent, sim = self.sim.agent, self.sim
        self.status.set(sim.outcome.capitalize() if self.done else "Driving")
        values = [sim.steps, agent.distance_travelled, f"{agent.cost_paid:g}",
                  f"{agent.remaining_route_cost():g}", agent.replans, agent.wait_events]
        for name, value in zip(STATS, values):
            self.stats[name].set(str(value))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
