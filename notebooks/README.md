# AOD Notebooks / Executable Notebook Layer

This directory contains the root notebook layer for the canonical source tree.

The notebook layer mirrors the package structure:
- Main note = compact native theorem line
- Supplement A = native worked examples and figure witnesses in `supplement-a/notebooks/`
- Supplement B = verification bindings and derived temporal-unit conversions in `supplement-b/notebooks/`
- Supplement C = additional native regime tests in `supplement-c/notebooks/`

All notebooks are native-first. When conversion is needed, it appears only after the cited native row and only into seconds / hertz / `\beta` with `c=1`.

---

## Regime map

| Regime | Notebook location | Package role | Visual outputs |
|---|---|---|---|
| Theorem-line sanity | `notebooks/E1-E3.ipynb` | main-note support | Q4 cut / closure visuals |
| Native rest / B* / collision | `supplement-a/notebooks/E4-E6.ipynb` | Supplement A | loss-channel, B* ladder, collision/export diagrams |
| Confinement / family rows | `supplement-a/notebooks/E7-E9-bindings.ipynb` | Supplement A | confinement / family / shell-signature visuals |
| Recurrent ring | `supplement-b/notebooks/E10-E11D.ipynb` | Supplement B | recurrent-ring and temporal-conversion figures |
| Supplement C regime notebooks | `supplement-c/notebooks/...` | Supplement C | grouped solar / hydrogen / nucleus / galactic / bacteria / saturn figures |

---

## Native-first rule
The native row is always recorded first. Each notebook uses: structural key, weighting policy, native operator chain, native output row, and hook/evidence.
