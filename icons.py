"""Little pictures drawn on a tkinter canvas.

Everything is drawn from rectangles, ovals and polygons that scale with
the cell size ``s``, so it looks the same at any window size.
(x, y) is the top-left corner of a cell.
"""

BUILDING_COLORS = ["#7d8597", "#b08968", "#8d99ae"]
CAR_COLORS = ["#c0392b", "#2e86c1", "#27ae60", "#8e44ad", "#d68910", "#34495e"]


def building(c, x, y, s, variant):
    """Apartment block, or a tree for variant 2."""
    if variant == 2:
        return tree(c, x, y, s)
    body = BUILDING_COLORS[variant]
    c.create_rectangle(x + .15*s, y + .22*s, x + .85*s, y + .90*s, fill=body, outline="#333")
    c.create_rectangle(x + .10*s, y + .14*s, x + .90*s, y + .22*s, fill="#444", outline="#333")
    for i in range(3):
        for j in range(3):
            wx, wy = x + (.24 + .2*i)*s, y + (.30 + .17*j)*s
            c.create_rectangle(wx, wy, wx + .11*s, wy + .10*s, fill="#ffe9a8", outline="")
    c.create_rectangle(x + .43*s, y + .76*s, x + .57*s, y + .90*s, fill="#3d2b1f", outline="")


def tree(c, x, y, s):
    c.create_rectangle(x + .45*s, y + .60*s, x + .55*s, y + .88*s, fill="#6b4423", outline="")
    c.create_oval(x + .20*s, y + .12*s, x + .80*s, y + .70*s, fill="#4f9d5d", outline="#2f6b3a")
    c.create_oval(x + .32*s, y + .22*s, x + .52*s, y + .40*s, fill="#6fbf7c", outline="")


def barrier(c, x, y, s):
    """Striped barrier between two traffic cones: a closed road."""
    left, right, top, bottom = x + .08*s, x + .92*s, y + .30*s, y + .46*s
    n = 6
    for i in range(n):
        a = left + (right - left) * i / n
        b = left + (right - left) * (i + 1) / n
        c.create_rectangle(a, top, b, bottom, fill="#d62828" if i % 2 == 0 else "white",
                           outline="#333")
    for lx in (left + .1*s, right - .1*s):
        c.create_line(lx, bottom, lx, y + .62*s, fill="#333", width=max(2, s // 16))
    for cx in (x + .22*s, x + .78*s):
        cone(c, cx, y + .88*s, s)


def cone(c, cx, base_y, s):
    h, w = .32*s, .12*s
    c.create_polygon(cx - w, base_y, cx + w, base_y, cx, base_y - h,
                     fill="#ff7f11", outline="#333")
    c.create_rectangle(cx - .075*s, base_y - .17*s, cx + .075*s, base_y - .11*s,
                       fill="white", outline="")
    c.create_rectangle(cx - .15*s, base_y, cx + .15*s, base_y + .05*s,
                       fill="#333", outline="")


def sedan(c, cx, cy, w, color):
    h = w * .5
    c.create_polygon(cx - .28*w, cy, cx - .17*w, cy - .42*h, cx + .17*w, cy - .42*h,
                     cx + .28*w, cy, fill=color, outline="#222")
    c.create_polygon(cx - .22*w, cy, cx - .14*w, cy - .34*h, cx + .14*w, cy - .34*h,
                     cx + .22*w, cy, fill="#cfe8f7", outline="")
    c.create_rectangle(cx - w/2, cy, cx + w/2, cy + .45*h, fill=color, outline="#222")
    for wx in (cx - .3*w, cx + .3*w):
        c.create_oval(wx - .09*w, cy + .30*h, wx + .09*w, cy + .62*h, fill="#111", outline="")


def ambulance(c, cx, cy, w, facing, flash):
    """Side view ambulance. facing is 1 (right) or -1 (left)."""
    h = w * .55

    def fx(a):
        return cx + facing * a * w

    top, bottom = cy - .45*h, cy + .30*h
    c.create_rectangle(fx(-.5), top, fx(.2), bottom, fill="white", outline="#222")
    c.create_rectangle(fx(-.5), cy + .02*h, fx(.2), cy + .14*h, fill="#d62828", outline="")
    c.create_rectangle(fx(-.30), cy - .32*h, fx(-.22), cy - .02*h, fill="#d62828", outline="")
    c.create_rectangle(fx(-.38), cy - .21*h, fx(-.14), cy - .13*h, fill="#d62828", outline="")
    c.create_polygon(fx(.2), top + .2*h, fx(.40), top + .2*h, fx(.5), cy,
                     fx(.5), bottom, fx(.2), bottom, fill="white", outline="#222")
    c.create_polygon(fx(.24), top + .27*h, fx(.38), top + .27*h, fx(.45), cy - .05*h,
                     fx(.24), cy - .05*h, fill="#9fd3f0", outline="")
    c.create_oval(fx(.26) - .06*w, top + .02*h, fx(.26) + .06*w, top + .22*h,
                  fill="#e63946" if flash else "#1d6fe0", outline="#222")
    for a in (-.30, .30):
        c.create_oval(fx(a) - .10*w, bottom - .12*h, fx(a) + .10*w, bottom + .24*h,
                      fill="#111", outline="")
        c.create_oval(fx(a) - .04*w, bottom - .02*h, fx(a) + .04*w, bottom + .14*h,
                      fill="#aaa", outline="")


def signal(c, x, y, s, state):
    c.create_rectangle(x + .72*s, y + .06*s, x + .92*s, y + .42*s, fill="#222", outline="")
    for i, (name, lit, dim) in enumerate((("red", "#ff3b30", "#4a1f1f"),
                                           ("green", "#34c759", "#1f4a2a"))):
        cy = y + (.16 + .14*i) * s
        c.create_oval(x + .76*s, cy - .05*s, x + .88*s, cy + .07*s,
                      fill=lit if state == name else dim, outline="")


def hospital(c, x, y, s):
    c.create_rectangle(x + .10*s, y + .10*s, x + .90*s, y + .90*s,
                       fill="white", outline="#d62828", width=max(2, s // 16))
    c.create_rectangle(x + .42*s, y + .22*s, x + .58*s, y + .78*s, fill="#d62828", outline="")
    c.create_rectangle(x + .22*s, y + .42*s, x + .78*s, y + .58*s, fill="#d62828", outline="")


def start_badge(c, x, y, s):
    r = .15 * s
    c.create_oval(x + .05*s, y + .05*s, x + .05*s + 2*r, y + .05*s + 2*r,
                  fill="#2a9d4f", outline="white")
    c.create_text(x + .05*s + r, y + .05*s + r, text="S", fill="white",
                  font=("Helvetica", max(8, int(s * .15)), "bold"))
