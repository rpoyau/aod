# AOD Notebooks / Executable Notebook Layer

This directory contains the executable notebook layer for the canonical source tree.

The notebook layer mirrors the package structure:
- Main note = compact native theorem line
- Supplement A = native worked examples and figure witnesses
- Supplement B = verification bindings and derived temporal-unit conversions

All notebooks are native-first. When conversion is needed, it appears only after the cited native row and only into seconds / hertz / \(\beta\) with \(c=1\).

---

## Regime map

The C-series regime notebooks now live under `supplement-c/notebooks/`.

| Regime | Notebook | Package role | Visual outputs |
|---|---|---|---|
| Theorem-line sanity | `E1-E3.ipynb` | main-note support | Q4 cut / closure visuals |
| Native rest / B* / collision | `E4-E6.ipynb` | Supplement A | rest-channel, B* ladder, collision/export diagrams |
| Confinement / family rows | `E7-E9-bindings.ipynb` | Supplement A | confinement / family / shell-signature visuals |
| Recurrent ring | `E10-E11D.ipynb` | Supplement B | recurrent-ring and temporal-conversion figures |

---

## Native-first rule
The native row is always recorded first. Each notebook uses: structural key, weighting policy, native operator chain, native output row, and hook/evidence.