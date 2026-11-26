"""Turn the solver outputs in data/raw/ into the page data in data/.

Every layout is re-scored here from its forge positions and orientations, so
the numbers on the page always match the drawn layout:

  - an area with k stacked projections makes 30k items/min for k <= 3 and
    150/min at k = 4 (150 rolls/min x the tier's chance);
  - every forge burns 6 Xiragen/min.

Lattice cells are 9 tiles apart; cells 0..6 lie inside the 65 x 65 region.

Usage: python solver/make_data.py   (from the repo root)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
DIRS = {"E": (1, 0), "W": (-1, 0), "N": (0, -1), "S": (0, 1)}
N = 7  # inner lattice cells per side


def pack(name, kind, forges, area_cells, note, extra=False):
    """Score a layout. forges: [(x, y, "SW"), ...]; area_cells: [(x, y), ...]."""
    hits = {tuple(a): 0 for a in area_cells}
    poles = []
    for x, y, ds in forges:
        for d in ds:
            t = (x + DIRS[d][0], y + DIRS[d][1])
            ok = t in hits
            if ok:
                hits[t] += 1
            poles.append([x, y, d, ok])
    areas = [[x, y, k] for (x, y), k in sorted(hits.items()) if k > 0]
    out = sum(150 if k == 4 else 30 * k for _, _, k in areas)
    outside = sum(1 for x, y, _ in areas if not (0 <= x < N and 0 <= y < N))
    F = len(forges)
    return {"name": name, "kind": kind, "note": note, "extra": extra,
            "forges": [list(f) for f in forges], "areas": areas, "poles": poles,
            "F": F, "out": out, "xiragen": 6 * F, "ipx": round(out / (6 * F), 3),
            "outside": outside}


def from_region(path, which):
    """'most output' is found[0], 'best efficiency' is found[1] in layout_ilp.py output."""
    lay = json.load(open(path))["found"][which]["layout"]
    forges = [tuple(f) for f in lay["forges"]]
    areas = [tuple(map(int, k.split(","))) for k, u in lay["areas"].items() if u > 0]
    return forges, areas


def diagonal_chain(cells):
    """Bipolars between consecutive diagonal areas: one facing S+W, one N+E."""
    forges = []
    for (x, y), _ in zip(cells, cells[1:]):
        forges += [(x + 1, y, "SW"), (x, y + 1, "NE")]
    return forges


def capped_chain(cells):
    """Diagonal chain plus forges outside each end that lift the ends to T4."""
    forges = diagonal_chain(cells)
    (x0, y0), (x1, y1) = cells[0], cells[-1]
    forges += [(x0, y0 - 1, "SW"), (x0 - 1, y0, "NE"),   # into the first area
               (x1 + 1, y1, "SW"), (x1, y1 + 1, "NE")]   # into the last area
    return forges


def main():
    bip = os.path.join(RAW, "region_bipolar.json")
    sgl = os.path.join(RAW, "region_single.json")

    diag7 = [(i, i) for i in range(N)]
    three = []
    for s in (0, 3, -3):
        three.append([(x, x - s) for x in range(N) if 0 <= x - s < N])

    layouts = [
        pack("Single diagonal", "bipolar", *from_region(bip, 1),
             "Best items per Xiragen. Your staircase, cut to the 7 diagonal cells that fit."),
        pack("Three diagonals", "bipolar", sum((diagonal_chain(c) for c in three), []),
             sum(three, []),
             "Twice the output for a small efficiency cost: three independent chains side by side."),
        pack("Dense grid", "bipolar", *from_region(bip, 0),
             "Most output in the region. Every area is T4, but end caps waste a pole each."),
        pack("Plus shapes", "single", *from_region(sgl, 1),
             "Best for single forges: four forges around each area always reach T4."),
        pack("Packed singles", "single", *from_region(sgl, 0),
             "Most output from single forges; the leftover gaps take T1 to T3 areas."),
    ]

    # Extras: layouts that came up along the way, for comparison.
    stair = [(i, i) for i in range(-1, N + 1)]          # 9 areas, ends outside
    ring_forges = [(1, 0, "ES"), (3, 0, "SW"), (0, 1, "ES"), (4, 1, "SW"),
                   (0, 3, "NE"), (4, 3, "WN"), (1, 4, "NE"), (3, 4, "WN"),
                   (2, 1, "WN"), (1, 2, "SW"), (3, 2, "NE"), (2, 3, "ES")]
    ring_areas = [(2, 0), (1, 1), (3, 1), (0, 2), (4, 2), (1, 3), (3, 3), (2, 4)]
    shift = lambda pts: [(p[0] + 1, p[1] + 1, *p[2:]) for p in pts]
    layouts += [
        pack("Nine-area staircase", "bipolar", diagonal_chain(stair), stair,
             "The original staircase. Slightly more efficient than the 7-area chain, "
             "but its two end areas fall outside the 65 × 65 region.", extra=True),
        pack("Capped diagonal", "bipolar", capped_chain(diag7), diag7,
             "The 7-area chain with four extra Bipolars outside the region lifting both "
             "ends to T4. Each extra forge wastes a pole, so efficiency drops.", extra=True),
        pack("T3 ring", "bipolar", shift(ring_forges), [p[:2] for p in shift(ring_areas)],
             "Twelve Bipolars around eight T3 areas. No pole is wasted, but T3 earns "
             "only 30 per projection, below a T4 stack.", extra=True),
    ]

    small = {}
    for kind, rows in json.load(open(os.path.join(RAW, "small.json"))).items():
        small[kind] = []
        for r in rows:
            F = r["F"]
            lay = pack(f"{F} {'Bipolar' if kind == 'bipolar' else 'single'} forge{'s' if F > 1 else ''}",
                       kind, [tuple(f) for f in r["forges"]], [tuple(a[:2]) for a in r["areas"]], "")
            assert abs(lay["out"] - r["out"]) < 1e-6, (kind, F, lay["out"], r["out"])
            small[kind].append(lay)

    json.dump(layouts, open(os.path.join(ROOT, "data", "layouts.json"), "w"), separators=(",", ":"))
    json.dump(small, open(os.path.join(ROOT, "data", "small.json"), "w"), separators=(",", ":"))
    for l in layouts:
        print(f"{l['name']:22s} {l['F']:3d} forges {l['out']:6.0f}/min {l['ipx']:6.3f} items/Xiragen"
              f"{'  (' + str(l['outside']) + ' areas outside region)' if l['outside'] else ''}")


if __name__ == "__main__":
    main()
