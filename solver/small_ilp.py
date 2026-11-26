"""Best standalone layout for exactly F forges, F = 1..11, Bipolar and single.

Same lattice model as layout_ilp.py: areas inside the 7x7 inner cells (65x65
region), forges may use the outer ring; an area with k stacked projections
makes 30k/min for k<=3 and 150/min at k=4. Each F is solved on its own.
Tie-break: among layouts with the most output, prefer fewer areas (fewer belt
lines to build).
"""
import json, sys
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

N = 7
DIRS = {"E": (1, 0), "W": (-1, 0), "N": (0, -1), "S": (0, 1)}
ORIENTS = {
    "bipolar": [("E", "S"), ("S", "W"), ("W", "N"), ("N", "E")],
    "single": [("E",), ("S",), ("W",), ("N",)],
}

def model(kind):
    orients = ORIENTS[kind]
    cells = [(x, y) for y in range(-1, N + 1) for x in range(-1, N + 1)]
    inner = [(x, y) for (x, y) in cells if 0 <= x < N and 0 <= y < N]
    inner_set = set(inner)
    idx = {}
    for c in cells:
        for o in range(len(orients)):
            idx[("y", c, o)] = len(idx)
    for c in inner:
        for k in ("a", "u", "z"):
            idx[(k, c)] = len(idx)
    nv = len(idx)
    ub = np.ones(nv)
    for c in inner:
        ub[idx[("u", c)]] = 4
    rows, lo, hi = [], [], []
    def con(coefs, l, h):
        r = np.zeros(nv)
        for k, v in coefs.items():
            r[idx[k]] += v
        rows.append(r); lo.append(l); hi.append(h)
    for c in cells:
        co = {("y", c, o): 1 for o in range(len(orients))}
        if c in inner_set:
            co[("a", c)] = 1
        con(co, 0, 1)
    for c in inner:
        co = {("u", c): 1}
        for f in cells:
            for o, ds in enumerate(orients):
                for d in ds:
                    if (f[0] + DIRS[d][0], f[1] + DIRS[d][1]) == c:
                        co[("y", f, o)] = co.get(("y", f, o), 0) - 1
        con(co, -np.inf, 0)
        con({("u", c): 1, ("a", c): -4}, -np.inf, 0)
        con({("z", c): 4, ("u", c): -1}, -np.inf, 0)
    out = np.zeros(nv); fr = np.zeros(nv); ar = np.zeros(nv)
    for c in inner:
        out[idx[("u", c)]] = 30; out[idx[("z", c)]] = 30; ar[idx[("a", c)]] = 1
    for c in cells:
        for o in range(len(orients)):
            fr[idx[("y", c, o)]] = 1
    return dict(idx=idx, nv=nv, ub=ub, A=np.array(rows), lo=lo, hi=hi,
                out=out, fr=fr, ar=ar, cells=cells, inner=inner, orients=orients)

def solve(m, F):
    # maximise output; areas cost 0.01 each (< one 30/min step) as tie-break
    obj = -m["out"] + 0.01 * m["ar"]
    res = milp(obj, constraints=[LinearConstraint(m["A"], m["lo"], m["hi"]),
                                 LinearConstraint(m["fr"].reshape(1, -1), F, F)],
               integrality=np.ones(m["nv"]), bounds=Bounds(np.zeros(m["nv"]), m["ub"]),
               options={"time_limit": 120, "mip_rel_gap": 0})
    x = res.x
    idx = m["idx"]
    forges = [[c[0], c[1], "".join(ds)] for c in m["cells"]
              for o, ds in enumerate(m["orients"]) if x[idx[("y", c, o)]] > 0.5]
    areas = [[c[0], c[1], int(round(x[idx[("u", c)]]))] for c in m["inner"]
             if x[idx[("a", c)]] > 0.5 and x[idx[("u", c)]] > 0.5]
    return forges, areas, float(m["out"] @ x), res.status

results = {}
for kind in ("bipolar", "single"):
    m = model(kind)
    results[kind] = []
    for F in range(1, 12):
        forges, areas, out, st = solve(m, F)
        tiers = sorted((a[2] for a in areas), reverse=True)
        print(f"{kind:7s} F={F:2d} out={out:5.0f} per-forge={out / F:6.2f} items/Xiragen={out / (6 * F):6.3f} tiers={tiers} status={st}", flush=True)
        results[kind].append({"F": F, "forges": forges, "areas": areas, "out": out})
json.dump(results, open(sys.argv[1] if len(sys.argv) > 1 else "small.json", "w"))
