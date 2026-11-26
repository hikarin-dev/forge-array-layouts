# Forge Array Layouts

Optimal Forge of Luminance and Bipolar Forge of Luminance layouts for one
65 × 65 build region in Arknights: Endfield, drawn to scale.

Each layout was solved exactly as an integer program on the 9-tile projection
lattice. Projection areas stay inside the region and forges may sit outside it.
Every forge burns 6 Xiragen/min, so efficiency is items produced per Xiragen.

| Layout | Forge | Forges | Output/min | Items per Xiragen |
|---|---|---|---|---|
| Single diagonal | Bipolar | 12 | 870 | 12.08 |
| Three diagonals | Bipolar | 24 | 1,710 | 11.88 |
| Dense grid | Bipolar | 44 | 2,550 | 9.66 |
| Plus shapes | Single | 40 | 1,500 | 6.25 |
| Packed singles | Single | 48 | 1,710 | 5.94 |

## Smaller builds

The best standalone layout for exactly 1 to 12 forges, each solved on its own
(no two builds share an area). With Bipolars, even counts form one diagonal
chain and an odd count hangs its extra forge off the end.

| Forges | Bipolar areas | Bipolar output/min | Bipolar items per Xiragen | Single areas | Single output/min | Single items per Xiragen |
|---|---|---|---|---|---|---|
| 1 | 2×T1 | 60 | 10.00 | T1 | 30 | 5.00 |
| 2 | 2×T2 | 120 | 10.00 | T2 | 60 | 5.00 |
| 3 | T3 T2 T1 | 180 | 10.00 | T3 | 90 | 5.00 |
| 4 | T4 2×T2 | 270 | 11.25 | T4 | 150 | 6.25 |
| 5 | T4 T3 T2 T1 | 330 | 11.00 | T4 T1 | 180 | 6.00 |
| 6 | 2×T4 2×T2 | 420 | 11.67 | T4 T2 | 210 | 5.83 |
| 7 | 2×T4 T3 T2 T1 | 480 | 11.43 | T4 T3 | 240 | 5.71 |
| 8 | 3×T4 2×T2 | 570 | 11.88 | 2×T4 | 300 | 6.25 |
| 9 | 3×T4 T3 T2 T1 | 630 | 11.67 | 2×T4 T1 | 330 | 6.11 |
| 10 | 4×T4 2×T2 | 720 | 12.00 | 2×T4 T2 | 360 | 6.00 |
| 11 | 4×T4 T3 T2 T1 | 780 | 11.82 | 2×T4 T3 | 390 | 5.91 |
| 12 | 5×T4 2×T2 | 870 | 12.08 | 3×T4 | 450 | 6.25 |

## Extras

Other layouts, for comparison.

| Layout | Forges | Output/min | Items per Xiragen | Note |
|---|---|---|---|---|
| Nine-area staircase | 16 Bipolar | 1,170 | 12.19 | Two end areas fall outside the 65 × 65 region |
| Capped diagonal | 16 Bipolar | 1,050 | 10.94 | Extra forges lift the chain's ends to T4, wasting a pole each |
| T3 ring | 12 Bipolar | 720 | 10.00 | Eight T3 areas, no wasted poles |

Belt and Xiragen pipe routing are not modelled; every projected tile is
assumed usable.

## Solver

Requires Python 3 with NumPy and SciPy (`scipy.optimize.milp`, HiGHS).

| Script | What it does |
|---|---|
| `solver/layout_ilp.py` | Solves the whole 65 × 65 region: the most output, and the best items per Xiragen (Dinkelbach iteration on output ÷ forges). |
| `solver/small_ilp.py` | Solves the best standalone layout for exactly 1 to 12 forges, Bipolar and single. |
| `solver/make_data.py` | Re-scores every layout from its forge positions, adds the extras, and writes `data/layouts.json` and `data/small.json`. |
| `solver/build_page.py` | Builds `index.html` from `template.html` and the data. |

The model: projection areas and forges are 5 × 5 squares on a lattice of
cells 9 tiles apart, since a projection lands exactly 9 tiles from its forge.
Areas use the inner 7 × 7 cells (59 tiles, inside 65); forges may also use
the ring of cells just outside. A single forge projects in one of four
directions, a Bipolar in two perpendicular directions. An area stacking k
projections converts 30k items/min up to T3 and 150/min at T4.

To regenerate from the repo root:

```sh
python solver/layout_ilp.py 7 bipolar data/raw/region_bipolar.json
python solver/layout_ilp.py 7 single data/raw/region_single.json
python solver/small_ilp.py data/raw/small.json
python solver/make_data.py
python solver/build_page.py
```

The region solves take a few minutes each; the small builds take a few
seconds per forge count.
