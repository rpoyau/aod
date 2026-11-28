# BND-P5-04 Execution Plan (`02_plan.md`)

> Scope amendment applied before Role 3: `typst/lib/main_registry.json` moved from `scope.read_only` to `scope.write_set` because `scripts/build_typst.py:compute_main_sources_digest()` hashes `typst/figure_inventory.json` into `main_sources_sha256`.

## Execution DAG & Acyclic Cryptographic Order

1. **Step 1 — Historical `98ddfa0` Baseline Archive (`211/211`)**
   - Extract exact historical `98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3:manual/data/cell_measures/cells_geometry.json` (`58,548` bytes, SHA-256 `f941856c7bc86356bdb461e44ecaa34ae399597e7abb76ed61178b20b8232ef0`) into `archive/latex_baseline_98ddfa0/manual/data/cell_measures/cells_geometry.json` (mode `0o644`; leave live `manual/data/cell_measures/cells_geometry.json` untouched).
   - Update `archive/latex_baseline_98ddfa0/BASELINE_MANIFEST.json` entry for `manual/data/cell_measures/cells_geometry.json`: `retained_location` → `"archive/latex_baseline_98ddfa0/manual/data/cell_measures/cells_geometry.json"`, `role` → `"archived_baseline_data"`, and update `counts` (`archived_editorial_tex: 41`, `archived_baseline_data: 1`, `preserved_in_place: 169`, `by_role["archived_baseline_data"]: 1`, `by_role["preserved_shared_data"]: 105`) while keeping `original_path`, `sha256`, `bytes`, `mode`, `canonical_typst_owner`, `generated_latex_counterpart` byte-identical.
   - Update `scripts/materialize_latex_baseline.py`: define `ARCHIVED_ROLES = frozenset({"archived_editorial_tex", "archived_baseline_data"})` and validate `retained == f"{BASELINE_REL.as_posix()}/{orig}"` for archived roles and `retained == orig` for preserved-in-place roles using `_require(...)` (zero bare `assert`).
   - Verify `python3 -B scripts/materialize_latex_baseline.py --verify-only` exits 0 (`211/211`).

2. **Step 2 — Exclude `.uow/` in `scripts/build_release_bundle.py`**
   - Add `".uow"` to `EXCLUDE_DIR_NAMES`.
   - In `build_source_tree(stage_root)`, skip tracked paths where `rel.parts and rel.parts[0] == ".uow"` before calling `copy_source_file(rel, source_root)`. Leave `INCLUDE_TOP_LEVEL` and all fail-closed checks intact so `tests/test_ci_release_builder.py` passes unmodified.
   - Record `NEW_RELEASE_BUILDER_SHA = sha256_file("scripts/build_release_bundle.py")`.

3. **Step 3 — Sync Acyclic Contract SHA-256 Chain**
   - Update `contracts/scientific/CANONICAL_BINDINGS.json`: set `frozen_sha256["scripts/build_release_bundle.py"] = NEW_RELEASE_BUILDER_SHA` (leave all formulas, ownership, unique signatures, manual families, and other 191 `frozen_sha256` entries untouched).
   - Record `NEW_CANONICAL_BINDINGS_SHA = sha256_file("contracts/scientific/CANONICAL_BINDINGS.json")`.
   - Update `scripts/audit_ontology_compaction.py`: set `CONTRACT_SHA256["CANONICAL_BINDINGS.json"] = NEW_CANONICAL_BINDINGS_SHA`.

4. **Step 4 — Honest M4.5 Phase 1 → Current Ledger (`typst/representation_change_ledger.json`)**
   - Preserve `phase1_accepted_commit == "e6f20970c8ac63713c112000e3fe83b9695c7ffc"` and every Phase 1 `old_sha256` verbatim.
   - Append `contracts/scientific/CELL_MEASURE_SPEC.json` to `contract_amendments` with:
     - `"old_sha256"`: exact Phase 1 digest `"75fc35552c419d831d8fcd5dfe1ee1b46dffa4e862535d4b74029f3c2018c9ea"`
     - `"new_sha256"`: current disk digest `"3c3e495357606a73a9bb2a142ec08dd102472eaf455a74e4626960e464ca61c2"`
     - `"scope"`: `"m4_5_g6_tesseract_extension"`
     - `"scientific_substance_changed"`: `true` (100% honest — never falsely claiming `false` for opening G6!)
     - `"fields_amended"`: `["tesseract_4d_ball (opened G6 4D tesseract-to-pi declared verification model)", "scope_limits (explicitly scoped G6 verification-model boundary)"]`
   - Update `contract_amendments` entry for `contracts/scientific/CANONICAL_BINDINGS.json` (`new_sha256 = NEW_CANONICAL_BINDINGS_SHA`, preserving `old_sha256`).
   - Update `frozen_sha256_amendments` entry for `scripts/build_release_bundle.py` (`new_sha256 = NEW_RELEASE_BUILDER_SHA`, preserving Phase 1 `old_sha256`, updating `reason` to include `.uow/` exclusion).
   - Update `summary`: `contracts_amended: 8`, `contracts_untouched: 9`, `frozen_relocations: 6`, `frozen_additions: 26`, `frozen_amendments: 18`, `frozen_total_after: 192`.

5. **Step 5 — Deterministically Regenerate `latex/**` (`66` Exported Vector Figures)**
   - Run `SOURCE_DATE_EPOCH=0 PATH="$HOME/.local/bin:$PATH" python3 -B scripts/typ2tex.py --root . --outdir latex`.
   - Confirm `latex/figures/generated/FIGURE_MANIFEST.json` has `13` Main figures and `latex/manual/figures/generated/FIGURE_MANIFEST.json` has `53` Manual figures (`66` total, 0 rasters, 1 page each, extractable text).
   - Verify `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/typ2tex.py --root . --outdir latex --check` exits 0.

6. **Step 6 — Seal `typst/figure_inventory.json`, `typst/manifest.json`, and `typst/lib/main_registry.json`**
   - **`typst/figure_inventory.json`**:
     - Preserve all 34 `CONVERTED_VECTOR` historical `raster_path`/`raster_sha256`/`raster_bytes`/`raster_dimensions_px` byte-identically.
     - Append the 9 newly authored native vector figures (`conversion_status: "AUTHORED_NATIVE_VECTOR"`, `provenance_class: "CONCEPTUAL_SCHEMATIC"`, `raster_path: null`, `raster_sha256: null`, `raster_bytes: null`, `raster_dimensions_px: null`, `generator_script: null`, `generator_script_sha256: null`, `data_sources: []`, `raster_image_xobjects: 0`, `data_check_verified: false`, `visual_comparison_recorded: true`):
       1. `curl-to-duon-current-support` (`main`, `05_curl_closure_duon_current.typ`, `fig:curl-to-duon-current-support`)
       2. `closure-ladder` (`main`, `05_curl_closure_duon_current.typ`, `fig:closure-ladder`)
       3. `sadar-b-scoped-afc-flux` (`main`, `06_field.typ`, `fig:sadar-b-scoped-afc-flux`)
       4. `duon-current-boundary-accounting` (`main`, `06_field.typ`, `fig:v39-duon-current-boundary-accounting`)
       5. `sadar-boundary-relative-balance` (`main`, `06_field.typ`, `fig:sadar-boundary-relative-balance`)
       6. `fractal-calculus-spine` (`main`, `06_field.typ`, `fig:fractal-calculus-spine`)
       7. `cycle-wave-identity` (`main`, `06_field.typ`, `fig:cycle-wave-identity`)
       8. `field-count-scope` (`manual`, `00_native_closure_wave_temporal_fixtures.typ`, `fig:field-count`)
       9. `fractal-tesseract-beat-family` (`manual`, `00_native_closure_wave_temporal_fixtures.typ`, `fig:fractal-tesseract-beat-family`)
     - Refresh `typst_component_sha256`, `exported_pdf_sha256`, `exported_pdf_bytes`, `exported_page_points`, `caption_sha256`, `caption_excerpt`, and `data_sources[*].sha256` across all 62 figures from live disk and the two `FIGURE_MANIFEST.json` files (retaining existing non-CSV `typst/` provenance `data_sources` with refreshed SHA-256s where `test_s1b_vector_figures.py` checks them, and updating stale `provenance_notes` on `registry-engine-coverage-atlas` and `qext-quarantine-firewall` to remove `52-vector` / `RC-025`).
     - Update `summary`: `total_active_rasters: 34`, `main_rasters: 6`, `manual_rasters: 28`, `authored_native_vector: 28`, `total_vector_figures: 62`, `DATA_BACKED_VERIFIED: 39`, `CONCEPTUAL_SCHEMATIC: 23`, `UNRESOLVED_RETAINED: 0`, `converted_vector: 34`, `retained_raster: 0`.
   - **`typst/manifest.json`**:
     - Refresh `plots_library_sha256`, `figure_inventory_sha256`, `shared_library_files` (sorted, all 70 files including all 62 vector figures), `diagram_components` (4), `vector_figure_components` (all 62), and `active_source_map[*].typst_sha256` (all 48 units). Preserve `baseline_protected_sha256` (211) and `tex_sha256` untouched.
   - **`typst/lib/main_registry.json`**:
     - Run `SOURCE_DATE_EPOCH=0 PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub` to refresh `main_sources_sha256` (confirming `entry_count == 455` and `--check-registry` exits 0).

7. **Step 7 — Seal `scripts/verify_typst_parity.py` (Zero Bare `assert`; Use `require(...)`)**
   - **Gate A (`verify_baseline_immutability`)**:
     - Recognize `entry["role"] in ("archived_editorial_tex", "archived_baseline_data")` at line 2655, verifying `archived_rel_map` against `98ddfa0` via `git show` and reporting `archived_editorial_tex_files == 41`, `archived_baseline_data_files == 1`, `preserved_in_place_files == 169`.
     - Define `M4_5_SCIENTIFIC_CONTRACT_EXTENSIONS = frozenset({"contracts/scientific/CELL_MEASURE_SPEC.json"})`. At line 2832, enforce `rec.get("scientific_substance_changed") is True and rec.get("scope") == "m4_5_g6_tesseract_extension"` for paths in `M4_5_SCIENTIFIC_CONTRACT_EXTENSIONS`, and strictly enforce `rec.get("scientific_substance_changed") is False` for every other contract amendment!
   - **Gate A2 (`TRUSTED_TEMPLATE_SHA256`)**:
     - Update `TRUSTED_TEMPLATE_SHA256["typst/lib/aod_plots.typ"]` (and verify all 6 pinned template/driver digests match disk).
   - **Gate B (`POST_BASELINE_COMPACTED_MAIN_UNITS`, `POST_BASELINE_COMPACTED_MANUAL_UNITS`, figure counts)**:
     - Add `05_curl_closure_duon_current.typ` and `06_wave_state_relational_time.typ` to `POST_BASELINE_COMPACTED_MAIN_UNITS`, pin exact verified `POST_BASELINE_COMPACTED_MAIN_INLINE_MATH`, and compare baseline `IMG` order excluding `authored_pdf_rels`.
     - Partition compacted Manual units into `POST_BASELINE_COMPACTED_MANUAL_UNITS` with 6 fail-closed checks (all raising `ValueError("Ordered content/math parity mismatch in ...")`):
       1. Baseline `IMG` sequence match (excluding `authored_pdf_rels`) → preserves Control 14.
       2. Exact `FLOWCHART` AST match → preserves Controls 20a/20b.
       3. Exact pinned `POST_BASELINE_COMPACTED_MANUAL_INLINE_MATH` closure → preserves Control 7 & Control 19.
       4. Verbatim CLI `--flag` code tokens preserved → preserves `t_cli`.
       5. Exact `SCIENTIFIC_QUALIFIERS` word count lock (`POST_BASELINE_COMPACTED_MANUAL_QUALIFIER_COUNTS`) → preserves Control 6 (`no` → `a` short-negation rejection).
       6. Exact 1:1 Typst-vs-generated-LaTeX ordered parity & Gate C rendered prose clauses sourced from live `latex/<tex_rel>`.
     - Update exported counts: Main `6 → 13`, Manual `51 → 53`, figure_inventory `53 → 62`, `authored_cnt 19 → 28`.
   - **Gate D Negative Controls**:
     - Update Control 6 preimage in `02_mapping_error.typ` to `"because these examples supply no physical discrepancy model"` → `"because these examples supply a physical discrepancy model"`.
     - Update Controls 9, 15a, 15b, 16a, 21a, 21b preimages in `00_awareness_fixtures.typ` to live `"with no physical uncertainty model."` / `"no physical uncertainty model"`.
     - Update Control 11b expected substring to `"'fifth(+"` (if needed).
     - Update Control 22d (`22d_R1_undeclared_contract_transition`) from `CELL_MEASURE_SPEC.json` to untouched `contracts/scientific/ERROR_BUDGET.json`.

8. **Step 8 — Seal `tests/test_s1b_vector_figures.py` & `tests/test_typst_parity.py`**
   - **`tests/test_s1b_vector_figures.py`**:
     - Counts: `authored_native_vector: 28`, `total_vector_figures: 62`, `CONCEPTUAL_SCHEMATIC: 23`, `main: 13`, `manual: 49`, Main exported `13`, Manual exported `53`, `total_pdfs: 66`.
     - `new_dec_pdf_checks`: update tokens for `wire-moving-boundary-feynman.pdf` (`("RC-032", "13")`), `field-dynamics-boundary-feynman.pdf` (`("SD-008", "RC-041", "26.57055342", "209")`), `registry-engine-coverage-atlas.pdf` (`("RC-045", "53", "209")`), `qext-quarantine-firewall.pdf` (`("SD-007", "SD-004", "0.51099895069", "1776.86")`), and confirm `cell-staircase-fold-boundary.pdf` and `temporal-si-bridge-feynman.pdf` tokens match live PDFs.
   - **`tests/test_typst_parity.py`**:
     - Counts: `figure_image_bindings_verified == 62`, `vector_figure_components_pinned == 62`, `content_files_policy_checked == 110`, `len(m1["figures"]) == 53`, `len(rt1["figures"]) == 53`, `len(mm1["figures"]) == 13`, `len(m_png["figures"]) == 13`.
     - Update `t6` preimage on `02_mapping_error.typ` to `"because these examples supply no physical discrepancy model"` → `"because these examples supply a physical discrepancy model"`.
     - Update R1 untouched contract control (line 695) from `CELL_MEASURE_SPEC.json` to `contracts/scientific/ERROR_BUDGET.json`.

9. **Step 9 — Full Validation Matrix & Worktree Hygiene**
   - Execute all 7 validation commands from `00_bundle.toml` (including `verify_typst_parity.py` normal + `-O`, `build_release_bundle.py` smoke test, and zero-filter pytest across all 14 suites).
   - Remove `_build/` before reporting completion so `git status --short` contains ONLY `scope.write_set` files.
