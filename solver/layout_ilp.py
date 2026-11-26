"""Forge of Luminance layout optimiser on the 9-tile projection lattice.

Areas (projection targets) must lie inside the 65x65 build region -> inner
N x N lattice cells (N = 7). Forges may sit one ring outside. A forge projects
exactly one lattice step away: single forge in 1 of 4 directions, Bipolar in
an L (two perpendicular directions, 4 rotations). An area stacking k
projections of one type converts 150*chance(k)/min: 30k for k<=3, 150 at k=4.

Solves two layouts and prints both as lattice diagrams:
  1. the most output in the region (fewest forges as a tie-break);
  2. the best items per Xiragen (Dinkelbach iteration on output / forges),
     then the largest layout that reaches that ratio.

Usage: python layout_ilp.py [N=7] [bipolar|single] [out.json]
The JSON's "found" list holds them in that order.
"""
import sys, json
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

N = int(sys.argv[1]) if len(sys.argv) > 1 else 7
KIND = sys.argv[2] if len(sys.argv) > 2 else "bipolar"
OUT = sys.argv[3] if len(sys.argv) > 3 else None

DIRS = {"E": (1, 0), "W": (-1, 0), "N": (0, -1), "S": (0, 1)}
if KIND == "bipolar":
    ORIENTS = [("E", "S"), ("S", "W"), ("W", "N"), ("N", "E")]
else:
    ORIENTS = [("E",), ("S",), ("W",), ("N",)]

cells = [(x, y) for y in range(-1, N + 1) for x in range(-1, N + 1)]
inner = [(x, y) for (x, y) in cells if 0 <= x < N and 0 <= y < N]

idx = {}
def var(name):
    idx.setdefault(name, len(idx))
    return idx[name]

for c in cells:
    for o in range(len(ORIENTS)):
        var(("y", c, o))
for c in inner:
    var(("a", c)); var(("u", c)); var(("z", c))
nv = len(idx)

integrality = np.ones(nv)
lb = np.zeros(nv); ub = np.ones(nv)
for c in inner:
    ub[idx[("u", c)]] = 4

rows, lo, hi = [], [], []
def con(coefs, l, h):
    r = np.zeros(nv)
    for k, v in coefs.items():
        r[idx[k]] += v
    rows.append(r); lo.append(l); hi.append(h)

# one object per cell
inner_set = set(inner)
for c in cells:
    co = {("y", c, o): 1 for o in range(len(ORIENTS))}
    if c in inner_set:
        co[("a", c)] = 1
    con(co, 0, 1)
# useful projections into an area
for c in inner:
    co = {("u", c): 1}
    for f in cells:
        for o, ds in enumerate(ORIENTS):
            for d in ds:
                dx, dy = DIRS[d]
                if (f[0] + dx, f[1] + dy) == c:
                    co[("y", f, o)] = co.get(("y", f, o), 0) - 1
    con(co, -np.inf, 0)                       # u <= incoming
    con({("u", c): 1, ("a", c): -4}, -np.inf, 0)  # u <= 4a
    con({("z", c): 4, ("u", c): -1}, -np.inf, 0)  # 4z <= u

forge_row = {("y", c, o): 1 for c in cells for o in range(len(ORIENTS))}
c_obj = np.zeros(nv)
for c in inner:
    c_obj[idx[("u", c)]] = -30
    c_obj[idx[("z", c)]] = -30

A = np.array(rows)
base = LinearConstraint(A, lo, hi)
fr = np.zeros(nv)
for k in forge_row: fr[idx[k]] = 1

def solve(obj, extra=(), tl=300):
    res = milp(obj, constraints=[base, *extra], integrality=integrality,
               bounds=Bounds(lb, ub), options={"time_limit": tl, "mip_rel_gap": 0})
    if res.x is None:
        return None
    x = res.x
    out = float(-c_obj @ x)
    F = int(round(fr @ x))
    gap = getattr(res, "mip_gap", None)
    return out, F, x, res.status, gap

def extract(x):
    layout = {"forges": [], "areas": {}}
    for c in cells:
        for o, ds in enumerate(ORIENTS):
            if x[idx[("y", c, o)]] > 0.5:
                layout["forges"].append([c[0], c[1], "".join(ds)])
    for c in inner:
        if x[idx[("a", c)]] > 0.5:
            layout["areas"][f"{c[0]},{c[1]}"] = int(round(x[idx[("u", c)]]))
    return layout

ARROW = {"E": ">", "W": "<", "N": "^", "S": "v"}
def render(layout):
    """Lattice cells, 9 tiles apart; the outer ring is outside the 65x65."""
    g = [["  .  " for _ in range(N + 2)] for _ in range(N + 2)]
    for x, y, ds in layout["forges"]:
        g[y + 1][x + 1] = ("F" + "".join(ARROW[d] for d in ds)).center(5)
    for k, u in layout["areas"].items():
        x, y = map(int, k.split(","))
        g[y + 1][x + 1] = f"[T{u}]".center(5)
    return "\n".join("".join(row) for row in g)

def report(label, sol):
    out, F, x, st, gap = sol
    lay = extract(x)
    tiers = sorted(lay["areas"].values(), reverse=True)
    print(f"\n== {label}: {F} forges, {out:.0f} items/min, {out / (6 * F):.3f} items per Xiragen "
          f"({out / F:.2f}/forge), {F * 6} Xiragen/min, areas {tiers}  [status {st}, gap {gap}]")
    print(render(lay), flush=True)
    return {"label": label, "F": F, "out": out, "layout": lay}

print(f"kind={KIND} N={N} (areas inside {9 * (N - 1) + 5}x{9 * (N - 1) + 5}, forges may use the outer ring)", flush=True)
found = []
need_forge = LinearConstraint(fr.reshape(1, -1), 1, np.inf)

# 1) Most output, fewest forges for it (0.01 per forge < one 30/min step).
found.append(report("most output", solve(c_obj + 0.01 * fr, [need_forge])))

# 2) Best items per Xiragen (Dinkelbach on out/F), then the largest layout at that ratio.
lam = 0.0
while True:
    out, F, x, st, gap = solve(c_obj + lam * fr, [need_forge])
    if out - lam * F < 1e-6:
        break
    lam = out / F
    print(f"   dinkelbach: ratio {lam:.4f}/forge ({F} forges, {out:.0f})", flush=True)
row = (-c_obj - lam * fr).reshape(1, -1)
best = solve(c_obj + 0.01 * fr, [need_forge, LinearConstraint(row, -1e-6, np.inf)])
found.append(report("best efficiency, largest such layout", best))
if OUT:
    json.dump({"kind": KIND, "N": N, "found": found}, open(OUT, "w"))
