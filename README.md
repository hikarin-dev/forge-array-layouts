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

Belt and Xiragen pipe routing are not modelled; every projected tile is
assumed usable.
