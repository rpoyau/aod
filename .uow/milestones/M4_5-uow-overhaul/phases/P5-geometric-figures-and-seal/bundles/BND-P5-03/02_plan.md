# Execution Plan — `BND-P5-03`

## Scope (`scope.write_set` — 23 files)
- `typst/lib/aod_schema.typ`, `typst/lib/main_registry.json`
- `scripts/verify_typst_parity.py`, `scripts/typ2tex.py`
- 17 Manual `.typ` files (14 sections + 3 appendices)
- `tests/qa_phase3_relational_time.py`, `tests/qa_phase4_manual_sadar.py`

---

## Step 1 — Trusted Declarative Helpers in `typst/lib/aod_schema.typ`
Append after `aod-uncaptioned-longtable` (~L328; DO NOT modify `aod-document` global `show raw` rule so Main PDF stays byte/page-identical):
- Private helpers:
  - `_aod-csv-path-re = regex("^/manual/data/boundary_sadar/[a-z0-9_]+\\.csv$")`
  - `_aod-wrap-text(s)` (zero-width breaks after `_`, `->`, `/`, `;`, `,` and before `(`)
  - `_aod-wrap-raw(s)` (zero-width breaks after `_`, `/`, `->`, `+`, `(`, `,`)
  - `_aod-fmt-signed(s)` (`0` -> `[0]`, `-x` -> `[\u{2212}x]`, `x` -> `[+x]`)
  - `_aod-render-csv-cell(r, spec, sub-size)` supporting string col shorthand AND dict kinds: `"plain"`, `"wrap"`, `"raw"`, `"raw-wrap"`, `"minus"`, `"signed"`, `"rat"`, `"vec"`, `"arrow"`, `"wrap-paren"`, `"stack"` (`"plain"` / `"raw-wrap"` / `"wrap-sub-paren"`), `"tuple"`, `"slot"`, `"sweep-shed"`, `"math-eq"`, `"union-cur"`, `"when"`.
- Public declarative helpers:
  - `#aod-raw-wrap(s)`: `context` scaling `raw` size to `max(6.2pt, text.size * 0.88)` + `raw(_aod-wrap-raw(s))`.
  - `#aod-nowrap(body)`: `box(body)` replacing raw `#box[...]` in content files.
  - `#aod-csv-table(csv-path, columns: (), align: (), headers: (), cells: (), size: 8.0pt, inset: (x: 3.0pt, y: 3.2pt), filter-col: none, filter-values: none)`: validates `csv-path` matches `_aod-csv-path-re`, loads live `csv(csv-path, row-type: dictionary)`, applies optional `filter-col`/`filter-values`, sets `text(size: size)`, `show raw: set text(size: eff-raw-size)`, `set par(justify: false, leading: eff-leading)`, renders booktabs `table(...)`.

---

## Step 2 — Gate A2 & Policy Updates in `scripts/verify_typst_parity.py`
1. Update `TRUSTED_TEMPLATE_SHA256["typst/lib/aod_schema.typ"]` to the new SHA-256 of `typst/lib/aod_schema.typ`.
2. Update `CONTENT_CALL_ALLOWLIST`:
   - Add `"aod-csv-table": frozenset({"align", "cells", "columns", "filter-col", "filter-values", "headers", "inset", "size"})`
   - Add `"aod-raw-wrap": frozenset()`
   - Add `"aod-nowrap": frozenset()`
   - Add `"figref": frozenset()`
   - Update `"table": frozenset({"align", "columns", "inset"})`
3. Update `CONTENT_TEXT_SIZES` to `frozenset({"7.0pt", "7.5pt", "8.0pt", "8.5pt", "9.5pt", "10pt", "12pt", "14pt", "17pt"})`.
4. **Fix `_typ_balanced` (L2840 & L3155)**: add `*, skip_math: bool = True` so `$...$` math spans are skipped when scanning outer `(...)` calls (fixing half-open `(0, 30]` in `03_temporal_observation.typ`), while passing `skip_math=False` inside `scan_typst_events -> math()`.
5. Add strict validation helpers wired into `_content_policy_violations`:
   - `_validate_table_inset`: positive literal `pt <= 12.0` or `(x: <pos pt>, y: <pos pt>)`.
   - `_validate_csv_table_policy`: enforces literal string path matching `^/manual/data/boundary_sadar/[a-z0-9_]+\.csv$`, `size in CONTENT_TEXT_SIZES`, valid `columns`/`align`/`headers`/`cells` arity & cell spec kinds/keys, optional valid `inset`/`filter-col`/`filter-values`.
   - `aod-raw-wrap`: enforces 1 literal string argument.
6. Token-extractor parity hygiene (`extract_tex_ordered` strips `\allowbreak{}` in `\texttt{...}`; `extract_typst_ordered` handles `aod-raw-wrap` as `CODE` and `aod-nowrap` as bracketed span).
7. Keep ALL negative controls (`show`, `let`, `csv`, `box`, `fill`, `hide`, `eval`, etc.) strictly rejected!

---

## Step 3 — Deterministic `#aod-csv-table` & Helper Support in `scripts/typ2tex.py`
1. Import `csv`; add `CSV_TABLE_PATH_RE`.
2. Update `escape_latex_text` for `\u200b` -> `\allowbreak{}` and `\u2212` -> `-` (in texttt) / `$-$` (in text); add `_format_wrap_text_latex` & `_format_raw_wrap_latex`; align `_font_size_cmd` and `#text(size: ...)` for `7.0pt/7.5pt` (`\scriptsize`) and `8.0pt/8.5pt` (`\footnotesize`).
3. Update `_parse_table_call` (L1228) to accept optional `inset:`; add `convert_body_cell=None` on `_render_table_latex`.
4. Track `used_csvs: set[str]` in `TypstToLatexConverter` & record each as `table_data_csv` input in `generate_latex_tree`.
5. Implement `_parse_csv_cell_spec`, `_render_csv_cell_latex` (1-to-1 mirror of all 17 `_aod-render-csv-cell` kinds, joining stacked lines with `\par `), and `_parse_csv_table_call` reading live CSV via `csv.DictReader` + optional filtering.
6. Wire `#aod-csv-table`, `#aod-raw-wrap`, and `#aod-nowrap` (`\mbox{...}`) into `_extract_code_block_table`, `_convert_hash`, and `_block_hash`.

---

## Step 4 — Migrate All 17 Manual `.typ` Units (Zero `#let`/`#show`/`#for`/`..`/`box()`/`csv()`)
- **5 Static/Inline files**:
  1. `00_scope.typ`: remove `let raw-wrap`/`show raw`/`leading`; `7.8pt -> 7.5pt`; `#raw-wrap(...) -> #aod-raw-wrap(...)` (keep `#raw("RC-...")`/`#raw("SD-...")` verbatim).
  2. `01_cell_measures.typ`: `@tab:... -> #tabref(...)`; `7.6pt -> 7.5pt`.
  3. `02_mapping_error.typ`: `@tab:... -> #tabref(...)`, `@fig:... -> #figref(...)`; `7.8pt -> 8.0pt`.
  4. `09_prediction_test_fixture_registry.typ`: L71 raw `\u{200b}` -> `#aod-raw-wrap(...)`; remove `let raw-wrap`/`show raw`/`leading`; `7.8pt -> 7.5pt`; `#raw-wrap -> #aod-raw-wrap` (keep `#raw("RC-...")`/`#raw("SD-...")` verbatim).
  5. `B_quarantined_external_comparison.typ`: `8.2pt -> 8.0pt`, remove `leading: 0.44em`.
- **12 Live-CSV files**:
  1. `00_native_closure_wave_temporal_fixtures.typ` (`8.4pt -> 8.5pt`; `native_closure_wave_dec_walk.csv`, `size: 7.5pt`)
  2. `00_awareness_fixtures.typ` (`awareness_operativity_dec_walk.csv`, `size: 7.0pt`)
  3. `03_temporal_observation.typ` (`temporal_si_bridge_dec_ledger.csv`, `size: 7.5pt`)
  4. `03_short_window_rcd_shedding_fixtures.typ` (`8.3pt -> 8.5pt`; `short_window_rcd_dec_ledger.csv`, `size: 8.0pt`)
  5. `01_rest_energy_prediction.typ` (`tau_five_boundary_sadar_trace.csv`, `size: 7.5pt`)
  6. `02_hydrogen_facing_shell_tests.typ` (`#box[Pa...] -> #aod-nowrap[Pa...]`; `hydrogen_shell_dec_transitions.csv`, `size: 8.5pt`)
  7. `04_boundary_current_applications.typ` (`scoped_wire_and_moving_boundary_walk.csv`, `size: 8.0pt`, conditional `when` cells)
  8. `05_solar_system_field_tests.typ` (`solar_o0_boundary_dec_audit.csv`, `size: 7.5pt`)
  9. `06_field_dynamics_applications.typ` (`run_tumble_q4_dec_walk.csv`, `size: 8.0pt`, `filter-col: "t", filter-values: ("0","2","3","5","7","8","16","20")`)
  10. `07_galactic_lensing_plan.typ` (`lensing_ray_chiral_dec_walk.csv`, `size: 8.5pt`)
  11. `A_simulation_fixtures_and_tau_prediction_context.typ` (`#box[#raw(...)] -> #aod-nowrap[#raw(...)]`; `cycle_shedding_exact_rational_summary.csv`, `size: 8.0pt`)
  12. `C_3d_coordinate_phase_cycle_delta3_fixture.typ` (`#box[#raw(...)] -> #aod-nowrap[#raw(...)]`; `coordinate_phase_3d_dec_walk.csv`, `size: 8.0pt`)

---

## Step 5 — Refresh `typst/lib/main_registry.json` & Update QA Live-CSV Helpers
1. Run `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub` to refresh `typst/lib/main_registry.json` (`main_sources_sha256` after `aod_schema.typ` edit; confirm 0 entry/page changes on Main), then verify `--check-registry`.
2. Update `tests/qa_phase3_relational_time.py` and `tests/qa_phase4_manual_sadar.py` with `_has_live_csv_binding` accepting `#aod-csv-table("<uri>", ...)` alongside `csv("<uri>", ...)` (zero bare asserts, zero floats).

---

## Step 6 — Validation, Negative Controls & 144 ppi Visual Inspection
1. Run ALL 6 validation commands in `00_bundle.toml`, plus negative-control probes on `_content_policy_violations` (rejecting arbitrary/traversal/variable `#aod-csv-table` paths, tiny sizes, `fill:`, negative `inset`, raw `csv()`, `box[]`) and `typ2tex.py --check --outdir _build/latex_check`.
2. Render and visually inspect 8 representative migrated tables in `_build/pub/manual.pdf` at 144 ppi (`§1`, `§3`, `§7`, `§9`, `§11`, `§13`, `§15`, `App. C`) via `pdftoppm` and `view_file` confirming crisp rendering, zero overlap, zero clipping, and zero margin overflow.
