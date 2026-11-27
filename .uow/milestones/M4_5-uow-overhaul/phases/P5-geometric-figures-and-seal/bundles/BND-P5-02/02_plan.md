# Execution Plan — `BND-P5-02` (Manual Vector Figures Overhaul, Header Migration & Stale-Claim Remediation)

## Scope (`scope.write_set` — 17 Manual Vector Figure Files)
All 17 legacy `y=0.54/0.94` boundary-SADAR figures under `typst/lib/figures/manual/`:
1. `five_boundary_calculation_spine.typ` (`CONCEPTUAL_SCHEMATIC`, 0 CSVs)
2. `native_closure_q4_dec_walk.typ` (1 CSV)
3. `awareness_matched_operativity_feynman.typ` (1 CSV)
4. `dec_hinge_slide_chiral_vertex.typ` (1 CSV)
5. `chiral_flip_boundary_stokes.typ` (`CONCEPTUAL_SCHEMATIC`, 0 CSVs)
6. `typed_map_variance_feynman.typ` (1 CSV)
7. `temporal_si_bridge_feynman.typ` (1 CSV)
8. `short_window_boundary_feynman.typ` (1 CSV)
9. `tau_five_boundary_sadar_setup.typ` (1 CSV)
10. `collision_shedding_debris_feynman.typ` (`CONCEPTUAL_SCHEMATIC`, 0 CSVs)
11. `hydrogen_shell_wavelet_atlas.typ` (1 CSV)
12. `wire_moving_boundary_feynman.typ` (1 CSV)
13. `solar_boundary_scopes_feynman.typ` (1 CSV)
14. `field_dynamics_boundary_feynman.typ` (2 CSVs)
15. `lensing_ray_boundary_feynman.typ` (1 CSV)
16. `registry_engine_coverage_atlas.typ` (2 CSVs)
17. `qext_quarantine_firewall.typ` (1 CSV)

---

## Global Policy & Structural Invariants
1. **Gate A2 (`_vector_figure_policy_violations`)**:
   - Single import `#import "/typst/lib/aod_plots.typ": *`; ZERO `@preview/*`, `@local/*`, `std.*`.
   - Strictly **ZERO `#set`**, `#show`, `#include`, `raw`, `image`, `label`, `link`, `state`, `counter`, `measure`, `layout`, `query` anywhere. Use `leading:` named argument on `aod-box`/`aod-box-tl` only!
   - Literal `#let fig-width-cm = <float>` and `#let fig-height-cm = <float>` and ONE `#aod-canvas(fig-width-cm, fig-height-cm)[...]`.
   - Use `#let y-off = <float>` to shift diagram body cleanly below `#aod-figure-header`.
2. **CSV Provenance Lock**:
   - Keep 0 `csv(` in the 3 `CONCEPTUAL_SCHEMATIC` figures (`five_boundary_calculation_spine`, `chiral_flip_boundary_stokes`, `collision_shedding_debris_feynman`).
   - Preserve exact `csv("/manual/data/boundary_sadar/...", row-type: dictionary)` calls in all 14 `DATA_BACKED_VERIFIED` figures.
3. **Header Migration (`#aod-figure-header`)**:
   - Replace every legacy `0.54`/`0.94` (and `0.44`/`0.80` in `temporal_si_bridge_feynman`) header pair with `#aod-figure-header(fig-width-cm, [...], subtitle: [...], top-y: ..., pad-x: 0.35, title-size: ..., subtitle-size: ..., gap-cm: ...)` (unbolded title content since helper sets `weight: "bold"`).
   - Outer frame height = `fig-height-cm - 0.30` (or `- 0.28` in `temporal_si_bridge_feynman`).
4. **Zero Bare Enum Prefixes & Minimum `$0_H$` Radius**:
   - Replace every line-leading `1. `, `2. `, `3. `.. inside boxes with `*(1)* `, `*(2)* `, `*(3)* `.. (`align-mode: left + horizon, inset: 4.5pt, leading: 0.36em`), and normalize `*1. `..`*4. ` headers to `*(1) ...*`.
   - Every `$0_H$` `#aod-chiral-vertex` MUST have `r >= 0.27` (`0.27`–`0.28`).
5. **Gate C**: 1 page, 0 rasters, 0 non-black/invisible text paints, `min_font >= 4.0pt` (body text `>= 6.6pt`).

---

## Wave A — 7 Figures with Stale Vector IDs / Numeric Claims (+ Header & Layout Fixes)
1. **`five_boundary_calculation_spine.typ`** (`15.0 x 8.8`, `y-off = 0.25`, `top-y: 0.28, gap-cm: 0.14`, `9.8pt/7.4pt`):
   - Bump `$0_H$` in Stage 2 from `r: 0.24` to `r: 0.28` with balanced box clearance; Stage 5 `inset: 3.5pt, leading: 0.36em`.
   - Bottom bar (`y: 7.47, h: 0.90`): update `52/52` (`RC-001..RC-044`) -> `53/53` cross-language golden vectors `RC-001..RC-045 + SD-001..SD-008`, including `TritWord/TritRatio SWAR`.
2. **`short_window_boundary_feynman.typ`** (`15.0 x 9.4`, `y-off = 0.76`, `top-y: 0.26, gap-cm: 0.12`, `9.4pt/7.2pt`):
   - Fix bare `1. `/`2. `/`3. ` -> `*(1)* `..`*(3)* `; give `$B_omega$` clean air below Panel A heading.
   - Bottom bar (`y: 8.10, h: 0.88`): bind BOTH `RC-030` (finite `C_6` double-slit cross-return ring `sum T_0 = 410, sum T^x = 448, delta_3 = (0, 6)`) AND `RC-038` (`rho^D_omega = min(RD, |omega|)`, `p^D + Q^D = 3 RD`, `X_shedding = #r-yro.X_shedding` at `(1:2, 9)`).
3. **`tau_five_boundary_sadar_setup.typ`** (`15.0 x 10.1`, `y-off = 0.76`, `top-y: 0.26, gap-cm: 0.12`, `9.4pt/7.2pt`):
   - Fix L27 Live cavity box: stale `raw 26` -> `Live cavity (RC-027): early coupling cut 1, raw 28 = 11 + 17, quotient 11 (17 dwell)`.
   - Bottom conservation bar (`y: 8.61, h: 1.06`): cite `(RC-027, 50-microslot rotor)` alongside exact `650/2500 + 703/2500 + 1147/2500 = 1`, `(19/50, 31/50)`, and recipient lattice.
4. **`wire_moving_boundary_feynman.typ`** (`15.0 x 9.1`, `y-off = 0.54`, `top-y: 0.28, gap-cm: 0.14`, `9.4pt/7.2pt`):
   - Separate Panel A crossing/sweep/shedding arrows & labels cleanly (`Delta R` box, `Phi_cross`, `-Phi_sweep`, `+Phi_shed`).
   - Fix bare `1. `/`2. ` -> `*(1)* `/`*(2)* `.
   - Bottom bar (`y: 7.88, h: 0.76`): fix stale `Engine vectors RC-030 & RC-031:` -> `Engine vector RC-032:`.
5. **`field_dynamics_boundary_feynman.typ`** (`15.0 x 9.4`, `y-off = 0.76`, `top-y: 0.26, gap-cm: 0.12`, `9.4pt/7.2pt`):
   - Compute live `#let sp-num-digits = sp0.MAPE_U_num.len()` (`230`) and `#let sp-den-digits = sp0.MAPE_U_den.len()` (`228`).
   - Fix L76 stale `840-digit` -> `$#sp-num-digits slash #sp-den-digits$-digit num/den`.
   - Fix L87 stale `64.70291920 %` -> `$#sp0.MAPE_U_display_8dp$ %` (`26.57055342 %` live from CSV!).
   - Fix L96 stale `RC-032 & RC-041` -> `Engine vectors SD-008 & RC-041: ... (RC-041) and exact 209-bin rational SPARC audit ($#sp0.MAPE_U_display_8dp$ %; SD-008).`.
6. **`registry_engine_coverage_atlas.typ`** (`15.0 x 9.2`, `y-off = 0.74`, `top-y: 0.26, gap-cm: 0.12`, `9.4pt/7.2pt`):
   - Update ALL `52` -> `53`, `44` -> `45`, `RC-001..RC-044` -> `RC-001..RC-045`, tier `(3, [Manual $33..45$])`, `ys: (24.0, 8.0, 13.0, 8.0)`, `value-labels: ([$24$], [$8$], [$13$], [$8$])`, and bump `ylim: (0.0, 26.5)` so `$24$` clears top frame!
   - Fix bare `1. `/`2. `/`3. ` -> `*(1)* `..`*(3)* `.
7. **`qext_quarantine_firewall.typ`** (`15.0 x 9.6`, `y-off = 1.02`, `top-y: 0.26, gap-cm: 0.12`, `9.4pt/7.2pt`):
   - Shift `$B_ext = Q_ext$` label (`1.18 + y-off = 2.20`) and all body boxes by `+ y-off`.
   - Break long box (b) `$e^-$` 6-tuple cleanly across 2 lines (`size: 6.6pt`, `inset: 4.5pt, leading: 0.34em`) with generous right-border clearance.
   - Fix L92 stale `SD-007 & RC-025` -> `Engine vectors SD-007, SD-004/SD-005 & RC-027..RC-029: ...`.

## Wave B & Wave C — Remaining 10 Figures (Header Migration, Bare Enum, `$0_H$` Radius & Polish)
- **`native_closure_q4_dec_walk.typ`** (`15.0 x 8.8`, `y-off = 0.36`): header + bare `1..3.` -> `*(1)*..*(3)*`.
- **`awareness_matched_operativity_feynman.typ`** (`15.0 x 8.9`, `y-off = 0.42`): header + bare `1..3.` -> `*(1)*..*(3)*` + clean `Cut 33 B_match` label clearance.
- **`dec_hinge_slide_chiral_vertex.typ`** (`14.8 x 9.5`, `y-off = 0.76`): header + `$0_H$` `r: 0.23 -> 0.28` (adjust wavy arrows to meet `0.28`) + box breathing.
- **`chiral_flip_boundary_stokes.typ`** (`14.8 x 8.5`, `y-off = 0.55`): header + both `$0_H$` `r: 0.26 -> 0.28` + bare `1..4.` -> `*(1)*..*(4)*`.
- **`lensing_ray_boundary_feynman.typ`** (`15.0 x 9.3`, `y-off = 0.76`): header + three `$0_H$` `r: 0.21 -> 0.27` & `$0$` `r: 0.20 -> 0.24` + raise flip-sequence text cleanly above `r: 0.27`.
- **`typed_map_variance_feynman.typ`** (`15.0 x 9.1`, `y-off = 0.56`): header + bare `1..3.` -> `*(1)*..*(3)*`.
- **`temporal_si_bridge_feynman.typ`** (`15.0 x 10.1`, `y-off = 0.60`): header + shift `B_bridge`/`B_val` wall labels + `$C$`/`$R$` `0.17 -> 0.19` + `leading: 0.35em`.
- **`collision_shedding_debris_feynman.typ`** (`15.0 x 9.8`, `y-off = 0.46`): header + bare `1..6.` -> `*(1)*..*(6)*` & `*1. `..`*4. ` -> `*(1) ...*`.
- **`hydrogen_shell_wavelet_atlas.typ`** (`15.0 x 9.3`, `y-off = 0.76`): header + `leading: 0.35em` polish.
- **`solar_boundary_scopes_feynman.typ`** (`15.0 x 9.3`, `y-off = 0.76`): header + shift `B_red climb` `3.82 -> 3.98` clearing dashed `B_Hg` orbit + normalize `*1.`..`*3.` -> `*(1)`..`*(3)`.

---

## Wave D — Verification, Gate A2, Gate C & 144 ppi Visual QA
1. Static audit verifying `#aod-figure-header`, CSV locks, zero forbidden stale tokens, zero bare enum prefixes, zero `#set`, and `$0_H$` `r >= 0.27` across all 17 figures.
2. Run ALL 4 bundle validation commands (`audit_scientific_sources.py`, `build_publication.py --outdir _build/pub --check-registry`, `export_typst_figures.py --surface manual --outdir _build/fig_check/manual`, Gate A2 `_vector_figure_policy_violations`).
3. Gate C PDF audit on all 17 exported PDFs (`1p, 0 rasters, 0 non-black/invisible text paints, min_font >= 4.0pt`).
4. Render ALL 17 standalone PDFs AND their embedded `_build/pub/manual.pdf` pages at `144 ppi` via `pdftoppm -png -r 144` into `/tmp/p502_png/` and visually inspect EVERY SINGLE ONE via `view_file` until 17/17 pass with zero overlaps, zero clipping, and zero border touching.
