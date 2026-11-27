# Execution Plan: `BND-P2-02` (`P2-tesseract-volume-pi` / `M4_5-uow-overhaul`)

## Scope Verification
Write-set (strictly bounded to 7 files):
- `typst/lib/figures/manual/cell_staircase_fold_boundary.typ`
- `typst/manual/sections/01_cell_measures.typ`
- `typst/manual/sections/02_mapping_error.typ`
- `contracts/scientific/CELL_MAPPING_MATHEMATICAL_BINDINGS.json`
- `scripts/audit_ontology_compaction.py`
- `typst/representation_change_ledger.json`
- `typst/figure_inventory.json`

Read-only locks: `typst/preamble.typ`, `typst/manual/preamble.typ`, `typst/lib/aod_plots.typ`, `manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv`, `manual/data/cell_measures/cells_geometry.json`, `contracts/scientific/CELL_MEASURE_SPEC.json`, `contracts/scientific/CANONICAL_BINDINGS.json`. Do NOT touch `latex/manual/figures/generated/*` (deferred to Phase 5 PDF export).

## Execution DAG

### T1. Upgrade `typst/lib/figures/manual/cell_staircase_fold_boundary.typ`
- `#import "/typst/lib/aod_plots.typ": *`; literal `#let fig-width-cm = 15.0` and `#let fig-height-cm = 9.2`; single `#aod-canvas(fig-width-cm, fig-height-cm)[...]`; zero `#set page(...)`; opaque black text; `min_font_size >= 6.5pt`.
- Live CSV parsing (`csv("/manual/data/boundary_sadar/cell_measures_staircase_fold_dec.csv", row-type: dictionary)` + `parse-rat(s)` helper; zero hardcoded numeric arrays).
- 4-panel layout (`15.0 cm x 9.2 cm`) with explicit vertical clearance (zero title-on-subtitle collisions, zero curve-on-legend overlaps):
  - Panel (a) top-left: Projected 4D Schlegel tesseract `[-1,1]^4` wireframe + stepped microcell envelope + inner 4-ball core ($V_{4,n}^- \subset B^4 \subset V_{4,n}^+ \subset [-1,1]^4$).
  - Panel (b) top-middle: Pure 4D $\pi_{\mathrm{4D},n}^{\pm}$ & 2D $A_{2,n}^{\pm}$ dyadic convergence (`n = 1..32`, manual above-plot legend strip, dashed $\pi$ reference).
  - Panel (c) bottom-left: $4 V_{4,n}^{\pm} \to 2\pi^2$ vs exposed 4D staircase $B_{3,\mathrm{stair},n}^+ = 8 V_{3,n}^+ \to 32\pi/3$ and bounding box $B_{3,\mathrm{box}} = 64$ (manual above-plot legend strip, right-margin asymptotic labels with $\ge 0.40\text{ cm}$ clearance).
  - Panel (d) right: Explicit two-square cellular fold chain map $K_2 = Q_L \cup Q_R \xrightarrow{F} L_2 = Q_*$ (CCW orientation arcs, canceled seam $+1-1=0$, reversed orientation $F_2(Q_R) = -Q_*$, boundary wall, and compact 4-point falsifier audit card).
  - Bottom invariant bar summarizing live `RC-035` (`n = 32`) exact fractions.

### T2. In-Place Refactor of `typst/manual/sections/01_cell_measures.typ`
- General Mechanics Setup -> Derivation -> Specialization -> Falsification flow.
- Delete the old unlabelled duplicate 2D `n = 1..32` table completely; present **EXACTLY ONE** unified 2D+4D table (`<tab:manual-cell-boundary-fold-ledger>`) with proportional `fr` column widths fitting cleanly inside page margins.
- Integrate opened `G6` 4D tesseract-to-$\pi$ derivation (`(2n)^4` microcells, $V_{4,n}^{\pm} \to \pi^2/2$ with gap $\le 64/n$, pure finite-4-cube integer-root $\pi_{\mathrm{4D},n}^{\pm}$ and cross-dimensional $\pi_{\times,n}^{\pm}$ without Machin in $B_{\mathrm{core}}$, Machin strictly quarantined to $B_{\mathrm{ext}}$, exposed 4D staircase 3-boundary $B_{3,\mathrm{stair},n}^+ = 8 V_{3,n}^+ \to 32\pi/3 \neq 2\pi^2$ explicitly distinguished from bounding 4-cube $B_{3,\mathrm{box}} = 64$, and genuine matrix-evaluated cellular fold commutation $B_d^L F_d = F_{d-1} B_d^K$ + 12 negative controls).
- Preserve EVERY defining label (`manual:m3-cells`, `prop:m3-staircase`, `eq:m3-disk-enclosure`, `manual:m3-cells:dec-staircase-fold`, `fig:manual-cell-staircase-fold`, `tab:manual-cell-boundary-fold-ledger`), Main cross-references, and verbatim contract-bound equation `<eq:m3-disk-enclosure>`. All new display equations unnumbered (`numbering: none`).

### T3. In-Place Refactor of `typst/manual/sections/02_mapping_error.typ`
- General Mechanics Setup -> Derivation -> Specialization -> Falsification flow seamlessly integrating the five-boundary stack $B_{\mathrm{src}} \to B_{\mathrm{map}} \to B_{\mathrm{joint}} \to B_{\mathrm{role}} \to B_{\mathrm{ext}}$ and `RC-036` joint-law variance ledger without bolted-on tone or dropped scientific statements.
- Preserve every defining label, verbatim numbered equations `<eq:manual-m3-original-interval>` & `<eq:manual-m3-original-product>`, `#aod-cite("hellwig-hydrogen-1970")`, verbatim `<fig:manual-typed-map-variance-feynman>` caption, and make `<tab:manual-typed-map-joint-laws>` margin-safe with proportional `fr` widths and stacked `$frac(num, den)$`.

### T4. Acyclic SHA-256 Contract & Inventory Sync
1. Compute `H_sec01 = sha256(01_cell_measures.typ)`, `H_fig = sha256(cell_staircase_fold_boundary.typ)`, `H_csv = sha256(cell_measures_staircase_fold_dec.csv)`.
2. Update `contracts/scientific/CELL_MAPPING_MATHEMATICAL_BINDINGS.json` (`sources["typst/manual/sections/01_cell_measures.typ"] = H_sec01`), compute `H_bindings`.
3. Update `scripts/audit_ontology_compaction.py` (`CONTRACT_SHA256["CELL_MAPPING_MATHEMATICAL_BINDINGS.json"] = H_bindings`).
4. Update `typst/representation_change_ledger.json` (`CELL_MAPPING_MATHEMATICAL_BINDINGS.json` `new_sha256 = H_bindings`).
5. Update `typst/figure_inventory.json` (`cell-staircase-fold-boundary` `typst_component_sha256`, `data_sources[0].sha256`, `caption_sha256` via verified canonicalizer, `caption_excerpt`, `figure_subtype`, `provenance_notes`; leave existing on-disk PDF metadata untouched until Phase 5 export).

### T5. Validation & 144 ppi Visual QA
1. `python3 -B scripts/audit_scientific_sources.py .`
2. `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub --check-registry`
3. `mkdir -p _build/png && PATH="$HOME/.local/bin:$PATH" typst compile --root . --format png --ppi 144 typst/lib/figures/manual/cell_staircase_fold_boundary.typ _build/png/cell_staircase_fold_boundary.png`
4. Render Manual §5 and §6 pages from `_build/pub/manual.pdf` via `pdftoppm -png -r 144` and visually inspect EVERY rendered PNG (standalone figure + §5/§6 pages) with `view_file` to verify ZERO text overlaps, ZERO clipped labels, and ZERO right-margin table overflows!
5. `python3 -B -m pytest -q tests/test_cells.py tests/test_tesseract_pi.py tests/test_mathematical_bindings.py` (normal and `-O`).
