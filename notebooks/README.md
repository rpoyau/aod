# AOD Notebooks / Executable Notebook Layer

This directory contains the **root notebook layer** for the canonical source tree.

The notebook layer mirrors the package structure:
- Main note = compact native theorem line (`notebooks/`)
- Supplement A = worked examples and figure witnesses (`supplement-a/notebooks/`)
- Supplement B = verification bindings and derived temporal-unit conversions (`supplement-b/notebooks/`)
- Supplement C = grouped native regime notebooks (`supplement-c/notebooks/solar/`, `hydrogen/`, `nucleus/`, `galactic/`, `bacteria/`, `saturn/`)

All notebooks are cited-row-first. Where SI reporting is needed, it follows the cited row and is limited to seconds / hertz / `\beta` with `c=1`.

---

## Regime map

| Regime | Notebook location | Package role | Visual outputs |
|---|---|---|---|
| Theorem-line sanity | `notebooks/examples-01-03.ipynb` | main-note support | Q4 cut / closure visuals |
| Native loss / B* / collision | `supplement-a/notebooks/E4-E6.ipynb` | Supplement A | loss-channel, B* ladder, collision/export diagrams |
| Confinement / family rows | `supplement-a/notebooks/E7-E9-bindings.ipynb` | Supplement A | confinement / family / shell-signature visuals |
| Recurrent ring / derived temporal-unit conversion | `supplement-b/notebooks/E10-E11D.ipynb` | Supplement B | recurrent-ring and converted-rendering figures |
| Supplement C regime notebooks | `supplement-c/notebooks/solar/`, `hydrogen/`, `nucleus/`, `galactic/`, `bacteria/`, `saturn/` | Supplement C | grouped regime figures and rendered witness charts |

---

## Native-first rule
The cited row is always recorded first. Each notebook uses: structural key, weighting policy, operator chain, output row, and hook/evidence.
