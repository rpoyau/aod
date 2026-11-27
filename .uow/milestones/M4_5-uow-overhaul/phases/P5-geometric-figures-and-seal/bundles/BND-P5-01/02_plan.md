# Execution Plan — `BND-P5-01` (Geometric Native Vector Figures & `#aod-figure-header`)

## Scope (`scope.write_set` — 16 files)
- `typst/lib/aod_plots.typ`
- 7 Main figures under `typst/lib/figures/main/`: `curl_to_duon_current_support.typ`, `closure_ladder.typ`, `sadar_b_scoped_afc_flux.typ`, `duon_current_boundary_accounting.typ`, `sadar_boundary_relative_balance.typ`, `fractal_calculus_spine.typ`, `cycle_wave_identity.typ`
- 2 Manual figures under `typst/lib/figures/manual/`: `field_count_scope.typ`, `fractal_tesseract_beat_family.typ`
- 3 section files: `typst/sections/05_curl_closure_duon_current.typ`, `typst/sections/06_field.typ`, `typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ`
- 3 SHA-256 contract files: `contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json`, `scripts/audit_ontology_compaction.py`, `typst/representation_change_ledger.json`

---

## Global Policy & Invariant Constraints
1. **Pure Built-In Typst Vector Standard**:
   - Every new figure component imports ONLY `#import "/typst/lib/aod_plots.typ": *`.
   - Zero `@preview/*`, zero `@local/*`, zero `csv(` (all 9 are `CONCEPTUAL_SCHEMATIC`), zero `#aod-panel(`, zero `#eqref`/`#eqnref`/`#secref`/`#main*`/`aod_schema.typ` macro shortcuts (must compile standalone via `scripts/export_typst_figures.py`!). Write raw Typst math (`$upright("SADAR")$`, `$frak(S)_B$`, `$A scripts(arrow.l.r)_mu Omega$`, `$sans("AO")_mu$`, `$sans("C")_6$`, `$Q_4$`, etc.).
   - Declare literal `#let fig-width-cm = <num>` and `#let fig-height-cm = <num>` and ONE `#aod-canvas(fig-width-cm, fig-height-cm)[...]` with zero extra top-level content so standalone export produces strictly 1 page matching `(fig-width-cm, fig-height-cm)` within `0.5 pt`.
2. **Gate C Print-Legibility & Font-Size Standard**:
   - 100% opaque `black` text (`#000000`, alpha `1.0`) everywhere on `white` or pale `aod-pal.tint-*` fills.
   - Explicit sizes `>= 7.2pt` for non-subscripted text and `>= 8.6pt` for subscripted/superscripted math (keeping 0.7x math scripts `>= 6.0pt`).
3. **Strict AOD Ontological Distinctions**:
   - `Dion != Dimonon`, `Duon (E_2^0) != seated Duad (E_2^+-)` (same `id`, same current), structural hinge `$0_H$` retained on EVERY rung/realization, lone Monon (`n_F = 0`, `bip = 0`) `!=` recurrent wave `!=` scoped field (`n_F >= 1`), integer cut `k -> k + 1` causal update order, typed flux firewall `phi^(AFC) != phi^(AOD)`.
4. **Zero Scientific/Registry Drift**:
   - Preserve ALL 455 Main labels, ALL 281 Manual labels, ALL 172 Manual `mainref_uses`, ALL 198 Main equations, ALL `M3_WAVELET_COMPACTION_BINDINGS.json` equations/anchors/relocated figures, and ALL `OWNERSHIP_AND_FIXTURES.json` anchors verbatim.

---

## Step 1 — Collision-Proof `#aod-figure-header` in `typst/lib/aod_plots.typ`
Append after line 1054 (modifying zero existing functions):
```typst
// =============================================================================
// Collision-Proof Figure Header (Native Vertical Stack, Opaque Black >= 6pt)
// =============================================================================
#let aod-figure-header(
  w-cm,
  title,
  subtitle: none,
  top-y: 0.16,
  pad-x: 0.35,
  title-size: 10.8pt,
  subtitle-size: 8.6pt,
  gap-cm: 0.16,
  title-leading: 0.36em,
  subtitle-leading: 0.38em,
  align-mode: center,
  rule: false,
  rule-stroke: 0.5pt + aod-pal.grid,
) = {
  let inner-w = calc.max(1.0, float(w-cm) - 2.0 * float(pad-x))
  let eff-title-size = if title-size < 6pt { 6pt } else { title-size }
  let eff-sub-size = if subtitle-size < 6pt { 6pt } else { subtitle-size }
  let items = (
    block(width: 100%, above: 0pt, below: 0pt)[
      #set align(align-mode)
      #set text(fill: black, size: eff-title-size, weight: "bold")
      #set par(leading: title-leading, spacing: 0pt, justify: false)
      #title
    ],
  )
  if subtitle != none {
    items.push(
      block(width: 100%, above: 0pt, below: 0pt)[
        #set align(align-mode)
        #set text(fill: black, size: eff-sub-size, weight: "regular")
        #set par(leading: subtitle-leading, spacing: 0pt, justify: false)
        #subtitle
      ]
    )
  }
  if rule {
    items.push(line(length: 100%, stroke: rule-stroke))
  }
  place(
    top + left,
    dx: float(pad-x) * 1cm,
    dy: float(top-y) * 1cm,
    box(width: inner-w * 1cm)[
      #stack(dir: ttb, spacing: float(gap-cm) * 1cm, ..items)
    ],
  )
}
```

---

## Step 2 — Author All 9 Native Geometric Vector Figures

1. **`typst/lib/figures/main/curl_to_duon_current_support.typ`** (`14.8 x 8.4 cm`, `<fig:curl-to-duon-current-support>`):
   - Two 3-panel rows linked horizontally + stepped inter-row connector (`pivot assembly: 2 x 3 x 2 = 12 variants`) + bottom invariant bar:
     (1) Branch–Hinge–Counterbranch (`+1 -> 0_H -> -1` with dashed `(0_D)^m` arc, `eps 0_H (0_D)^m (-eps)`),
     (2) Oriented Curl loop around `0_H` (`Pi^-`, `Pi^+`, `RD_gamma = Pi^- + H_mu + Pi^+`),
     (3) Dion dipole rows `D_alpha = (+1,-1)` / `D_Omega = (-1,+1)` around `0_H` (`Dion != Dimonon`),
     (4) Duon current `D_i mu_M D_j` via wavy arrows (`mu_M in {-1,0,+1}`, open `E_2^0` vs seated Duad `E_2^+-`),
     (5) Admitted Wave & Cadence (`k_0, k_1, k_2` cut axis, half-open `omega=(u,v]`, distinct return loops `C_0, C_1, C_2`, `W^(id)_(B,i)`),
     (6) Scoped Field Organization (hatched `partial_T F` walls enclosing coupled waves `W_1, W_2`, `F_(B,lambda)`).

2. **`typst/lib/figures/main/closure_ladder.typ`** (`14.8 x 9.0 cm`, `<fig:closure-ladder>`):
   - Continuous vertical gold structural-hinge rail (`0_H` nodes aligned to all 5 rungs) + 5 horizontal rung glyph+definition cards:
     (1) Monon (`Delta Phi = 1_C`, `bip = 0`, lone Monon != field),
     (2) Split glyph `Dion != Dimonon` (single shared `0_H` oriented pair vs two separate Monon loops),
     (3) Duon current `E_2^0` (`D_i mu_M D_j` open-seat dashed ring, 12 variants, `mu_M` never omits `0_H`),
     (4) Seated Duad `E_2^+-` (same wavy core inside solid `#aod-seat-ring`, `id(Seat(u)) = id(u)`),
     (5) Running Duon wave `W^(id)_(B,i)` (distinct compatible reclosures on `omega=(u,v]`).

3. **`typst/lib/figures/main/sadar_b_scoped_afc_flux.typ`** (`15.0 x 9.6 cm`, `<fig:sadar-b-scoped-afc-flux>`):
   - Double-hatched boundary frame `B = (partial F, omega)` with top typed-flux firewall banner (`phi^(AFC) != phi^(AOD)`).
   - Upper Magnitude branch: RCD & scalar duration `rho^D` -> Window clip `min(rho^D, |omega|)` (with bar-clip + overhang `Q^D` glyph) -> Count-domain magnitude `p^D_(ij) = C_(3,ij) rho^D_(omega,ij)`.
   - Lower Direction branch: Incidence cut `i in R | partial R | j not in R` (`phi_(ji) = -phi_(ij)`) -> Chiral lead-lag arc pair around `0_H` -> `A_(ij)(B) = Delta chi^(lag)_(ij) i_(ij)`.
   - Right product vertex `x` yielding `phi_(ij)(B) = p^D_(ij) A_(ij)` feeding bottom Finite Stokes / Attention Vector `A_F(B)` / Causal Motion `S^W_(k+1) = U_B^(SADAR)(...)`.

4. **`typst/lib/figures/main/duon_current_boundary_accounting.typ`** (`15.0 x 9.0 cm`, `<fig:v39-duon-current-boundary-accounting>`):
   - Cross-section across double-hatched retained boundary wall `partial R(t)` (with subtle dashed moving-boundary ghost wall):
     Interior `R` (concentric retained core loops around `0_H` + pending-return dashed arc over `omega`) vs Exterior/Shell `V \ R` (wavy orange exoshedding arrow crossing `partial R` into `#aod-seat-ring` `C_6` shell; curved green reflected return re-entering `R`; stacked window slice frames `t_1..t_m in omega`).
   - Bottom accounting formula band: `Phi^D_(partial R)(t; B|_t)`, `J^D_(partial R)(omega; B)`, magnitude partition `J^D_mag = J^D_in + J^D_out + J^D_pending`, and moving-boundary law `Phi^D_mov = Phi^D_cross - Phi^D_sweep + Phi^D_shedding`.

5. **`typst/lib/figures/main/sadar_boundary_relative_balance.typ`** (`15.0 x 9.0 cm`, `<fig:sadar-boundary-relative-balance>`):
   - Left nested scope geometry: Enclosing scope `B_12 = (partial F_12, omega_12)` stadium containing `F_1` on `B_1` (`ADAR_(1<-1)`, `A_(F_1)(B_1)`) and `F_2` on `B_2` (`ADAR_(2<-2)`, `A_(F_2)(B_2)`) linked by purple cross-return `ADAR_(2<-1)` / `ADAR_(1<-2)` curved arrows, with enclosing resultant `A_(F_1 || F_2)(B_12)`.
   - Right causal stack: Committed attention (`<= k`) -> Causal motion (`k -> k+1`) -> Wavy orange excess arrow to declared `SheddicPath in {E_2, C_6, C_8, ...}`.
   - Bottom projection guard bar.

6. **`typst/lib/figures/main/fractal_calculus_spine.typ`** (`15.0 x 9.2 cm`, `<fig:fractal-calculus-spine>`):
   - Left 3 geometric witness panels (`x > x = x` + true 16-vertex `#aod-tesseract-q4` scope; nested cycle `C_f[Sigma]` + `Pi_alpha -> H_mu -> Pi_Omega` triad; hatched boundary cut `partial_T R` crossed by directed flux arrows) paired by witness brackets with Right 6 numbered derivation cards (`Declared distinction` -> `Declared scope` -> `Certified closure/recurrence` -> `AO_mu(C)` -> `SADAR value` -> `Boundary accumulation`).

7. **`typst/lib/figures/main/cycle_wave_identity.typ`** (`14.8 x 8.4 cm`, `<fig:cycle-wave-identity>`):
   - Tier 1: Three chiral-package alternation stages `A <->_mu Omega` (`+1`) -> `Omega <->_mu A` (`-1`) -> `A <->_mu Omega` (`+1`) linked by `flip_mu` curved arrows.
   - Projection bridge (`frak(S)_(B|t)(C_t)` on `omega`) into Tier 2: signed discrete cut stem plot (`t_1..t_4 in omega=(u,v]`, alternating signs `A O = -O A` with `0_H` retained) paired with `v_B(W) = {(t, frak(S)_(B|t)(C_t)) : t in omega}` card and bottom admission guard bar.

8. **`typst/lib/figures/manual/field_count_scope.typ`** (`14.8 x 8.6 cm`, `<fig:field-count>`):
   - Three side-by-side geometric enclosure panels:
     Case 0 (Lone Monon: `N^C=1, bip=0, n_F=0`, crimson X non-recurrence marker),
     Case 1 (Single Recurrent Field: `F_1` with self-return `ADAR_(1<-1)`, 3 return dots, converging alias arrows -> `n_F=1, 1 log 1 = 0`),
     Case 2 (Two-Field Disoma inside `B_12`: `F_1`, `F_2` with self + cross returns -> `n_F=2, 2 log 2`),
     plus bottom count-pipeline & alias-resolution bar.

9. **`typst/lib/figures/manual/fractal_tesseract_beat_family.typ`** (`15.0 x 9.0 cm`, `<fig:fractal-tesseract-beat-family>`):
   - Four-column geometric pipeline:
     (1) Declared range `a`, grade `r`, `Sigma = (3:4, 3:3; C_6)`, `cycle<a,r>(Sigma)`,
     (2) True 16-vertex `#aod-tesseract-q4` with section slice `Sec^(r)_(T,ret)` and `N_support = |Sec^(r)| |Sigma_support|`,
     (3) Dual concentric `#aod-seat-ring` `C_6` support cards (`3:4`, `RD=137` and `3:3`, `RD=61`),
     (4) `frak(S)_B` coupling vertex + wavy coupled output + `T_sync = lcm(137, 61) = 8357` firewall card (`LCM alone never establishes coupling`),
     plus bottom invariant bar.

---

## Step 3 — Replace the 9 `#aod-panel` Bodies with `#include` Directives
Preserve EVERY `kind: image,`, `caption: [...]`, `<fig:...>`, equation, anchor, and prose line byte-for-byte:
- `typst/sections/05_curl_closure_duon_current.typ`:
  - `<fig:curl-to-duon-current-support>` -> `#include "../lib/figures/main/curl_to_duon_current_support.typ"`
  - `<fig:closure-ladder>` -> `#include "../lib/figures/main/closure_ladder.typ"`
- `typst/sections/06_field.typ`:
  - `<fig:sadar-b-scoped-afc-flux>` -> `#include "../lib/figures/main/sadar_b_scoped_afc_flux.typ"`
  - `<fig:v39-duon-current-boundary-accounting>` -> `#include "../lib/figures/main/duon_current_boundary_accounting.typ"`
  - `<fig:sadar-boundary-relative-balance>` -> `#include "../lib/figures/main/sadar_boundary_relative_balance.typ"`
  - `<fig:fractal-calculus-spine>` -> `#include "../lib/figures/main/fractal_calculus_spine.typ"`
  - `<fig:cycle-wave-identity>` -> `#include "../lib/figures/main/cycle_wave_identity.typ"`
- `typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ`:
  - `<fig:field-count>` -> `#include "../../lib/figures/manual/field_count_scope.typ"`
  - `<fig:fractal-tesseract-beat-family>` -> `#include "../../lib/figures/manual/fractal_tesseract_beat_family.typ"`

Confirm zero `#aod-panel` remaining in `typst/sections/*.typ`, `typst/appendices/*.typ`, and `typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ`.

---

## Step 4 & Step 5 — Acyclic SHA-256 Contract Sync
1. Compute `sha256` of `typst/sections/05_curl_closure_duon_current.typ` and `typst/sections/06_field.typ` -> update those 2 entries in `contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json` (`sources`).
2. Compute `sha256` of `contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json` -> update `CONTRACT_SHA256["M3_WAVELET_COMPACTION_BINDINGS.json"]` in `scripts/audit_ontology_compaction.py` and `new_sha256` for `M3_WAVELET_COMPACTION_BINDINGS.json` in `typst/representation_change_ledger.json`.

---

## Step 6 & Step 7 — Automated Validation, Gate C PDF Check & 144 ppi Visual QA
1. Run all 4 validation commands in `00_bundle.toml` (`audit_scientific_sources.py`, `build_publication.py --check-registry`, `export_typst_figures.py` for both `main` & `manual`, and targeted `pytest`).
2. Verify all 9 standalone exported PDFs under `_build/fig_check/{main,manual}/` have `1` page, `0` raster XObjects, `0` non-black/invisible text paints, and effective font sizes `>= 6.0pt`.
3. Render the exact pages of `_build/pub/main.pdf` and `_build/pub/manual.pdf` containing ALL 9 new figures at `144 ppi` via `pdftoppm -png -r 144` into `/tmp/p501_png/` and visually inspect EVERY SINGLE ONE via `view_file` (polishing coordinates/spacing if ANY overlap, touch, clipping, or tight fit is spotted until all 9 render impeccably!).
