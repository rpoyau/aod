# AOD Notebooks / Executable Notebook Layer

This directory contains the **root notebook layer** for the canonical source tree.

The notebook layer mirrors the package structure:
- Main note = compact native theorem line (`notebooks/`)
- Supplement A = native worked examples and figure witnesses (`supplement-a/notebooks/`)
- Supplement B = verification bindings and derived temporal-unit conversions (`supplement-b/notebooks/`)
- Supplement C = grouped native regime notebooks (`supplement-c/notebooks/`)

All notebooks are native-first. When conversion is needed, it appears only after the cited native row and only into seconds / hertz / `\beta` with `c=1`.

---

## Regime map

| Regime | Notebook location | Package role | Visual outputs |
|---|---|---|---|
| Theorem-line sanity | `notebooks/E1-E3.ipynb` | main-note support | Q4 cut / closure visuals |
| Native loss / B* / collision | `supplement-a/notebooks/E4-E6.ipynb` | Supplement A | loss-channel, B* ladder, collision/export diagrams |
| Confinement / family rows | `supplement-a/notebooks/E7-E9-bindings.ipynb` | Supplement A | confinement / family / shell-signature visuals |
| Recurrent ring / temporal conversion | `supplement-b/notebooks/E10-E11D.ipynb` | Supplement B | recurrent-ring and converted-rendering figures |
| Supplement C regime notebooks | `supplement-c/notebooks/solar/`, `hydrogen/`, `nucleus/`, `galactic/`, `bacteria/`, `saturn/` | Supplement C | grouped regime figures and rendered witness charts |

---

## Native-first rule
The native row is always recorded first. Each notebook uses: structural key, weighting policy, native operator chain, native output row, and hook/evidence.
