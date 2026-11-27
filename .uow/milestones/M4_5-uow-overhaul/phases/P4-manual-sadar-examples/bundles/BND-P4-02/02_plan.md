# BND-P4-02 Execution Plan (`02_plan.md`)

## SCOPE GAPS & VERIFIED VECTOR BINDINGS
- **`scope.write_set` gaps**: None. All edits strictly confined to:
  1. `typst/manual/sections/01_rest_energy_prediction.typ` (§9)
  2. `typst/manual/sections/02_hydrogen_facing_shell_tests.typ` (§10)
- **Verified ground-truth vector IDs from `manual/engine/vectors/*.jsonl`:**
  - `RC-011`: `higgs_trace_score_and_freeze` (`higgs_internal_selection_and_freeze_map`)
  - `RC-027`: `sadar_pp_tau_five_boundary` (`tau_five_boundary_sadar_trace.csv`)
  - `RC-028`: `sadar_hadron_debris_and_higgs_saddle` (`higgs_baryon_overlap_saddle_scan.csv` & Ditrion debris nondegeneracy)
  - `RC-029`: `sadar_rest_energy_atlas` (`rest_energy_sadar_debris_atlas.csv`, 10 carriers, 8160 common span vs 9104 summed closures)
  - `RC-031`: `hydrogen_shell_series_exact` (`hydrogen_shell_exact_series.csv`)
  - `RC-039`: `dec_hydrogen_shell_wavelet_step` (`hydrogen_shell_dec_transitions.csv`)
  - `SD-004`, `SD-005`: `higgs_lhc_rounded_display` (`exact_rational_half_even_6dp_display`)
  - `SD-007`: `sadar_rest_energy_qext` (`quarantined_B_ext_exact_target_rate_and_roundtrip_eta_cancellation`)

## 1. Exact Locks (MUST Hold With Zero Drift)
- **Global**: `main_labels == 455`, `manual_labels == 281`, `manual_mainref_uses == 172`.
- **`01_rest_energy_prediction.typ` (§9)**:
  - **28 exact labels** (12 headings, 2 locked equations, 8 tables, 6 figures).
  - **2 BYTE-FOR-BYTE LOCKED equations (`OWNERSHIP_AND_FIXTURES.json`)**:
    - `$ 3":"4::3":"3::6 equiv (3":"4, 3":"3; C_6 ). $ <eq:double-colon-parse-example>`
    - `$ Pi (3":"4) = 4^3 + 4 = 68, wide R D(3":"4) = 2 dot.op 68 + 1 = 137. $ <app:rd:eq:three-four-rd>`
  - **5 other owned anchors** (`tab:ao-field-fractal-properties`, `app:ao-field-fractal-properties:accessors-table`, `subsec:shared-shell-path-declaration`, `subsec:nested-shell-stack-pattern`, `tab:cc-filled-shared-enclosures`).
  - **Exact 11 `#main*` calls** (`8` `#mainappendix` + `3` `#mainsection`, `0` `#mainequation`), **8 `#aod-cite`**, **2 `#secref`**, **7 `#tabref`**, **1 `#appref`**, **3 `#bare-ref`**.
- **`02_hydrogen_facing_shell_tests.typ` (§10)**:
  - **20 exact labels** (12 headings, 0 equations, 6 tables, 2 figures).
  - **Exact 0 `#main*` calls**, **3 `#aod-cite`**, **4 `#secref`**, **3 `#tabref`**, **3 `#appref`**.

## 2. Execution DAG
```text
[T1: Refactor 01_rest_energy_prediction.typ (§9)] ──┐
                                                    ├──> [T3: Static Pre-Flight] ──> [T4: 3 Validation Cmds] ──> [T5: 144 ppi PNG Visual QA]
[T2: Refactor 02_hydrogen_facing_shell_tests.typ (§10)] ┘
```

### T1 — `typst/manual/sections/01_rest_energy_prediction.typ` (§9)
1. **Fix ALL scrambled vector IDs (ZERO `RC-025` and ZERO `RC-026` anywhere in §9)**:
   - L259: `RC-025, RC-026, RC-027, SD-007` -> `RC-027, RC-028, RC-029, SD-007`.
   - L265: `RC-027` (debris atlas) -> `RC-028` and `RC-029`.
   - L308 (`<tab:manual-tau-five-boundary-trace>` caption): `RC-025` -> `RC-027`.
   - L477 (Higgs saddle scan): `RC-026` -> `RC-028`.
   - Cite `RC-011` on Higgs internal trace score/freeze, `SD-004`/`SD-005` on Higgs LHC rounded display, and `SD-007` on quarantined $B_{\mathrm{ext}}$ targets.
2. **Align Tau five-boundary SADAR narrative with BND-P1-03 `TritWord`/`TritRatio` engine (ZERO stale `raw count 26`)**:
   - $B_{\text{hard}}$: early coupling at cut `1`; `raw_cuts = 28 = 11 + 17` (`11` symmetry-quotient cuts after burning `17` optional `0_D` dwell lanes via `TritWord.burn_contiguous_dwell(keep_single_dwell=False)`); sterile negative control `duons = 0` remains uncoupled through cut `58` with $X_{\text{shedding}} = 0$.
   - $B_{\tau}$: complete $L \in \{2,6,7,8,9,10\}$ competition isolating $1:2:9_{\text{yro}}$ uniquely ($Q^D = 0$, $X_{\text{shedding}} = 27 - 24 = 3$).
   - $B_{\text{shed}} \to B_{\text{sensor}}$: derived $50$-microslot $Q_4 \times \mu$ impedance rotor (`RD = 9 -> 61 -> 137`, 4D capacity `200`) producing `(13/50, 37/50)` at $B_{\text{shed}}$ ($\Delta RD = 52$) and `(19/50, 31/50)` conditional on `_Exo` at passive `ReadOnly` $3:4:6$ $B_{\text{sensor}}$ ($\Delta RD = 76$, zero observer back-reaction), yielding the exact $2500$-slot joint product `(650/2500, 1850/2500)` and `(703/2500, 1147/2500)` ($\operatorname{miss}_{\tau} = 31/50$) along the witness-ordered recipient lattice.
3. **Bind `<tab:manual-tau-five-boundary-trace>` LIVE to CSV** (`csv("/manual/data/boundary_sadar/tau_five_boundary_sadar_trace.csv", row-type: dictionary)`, 7 rows, 10 proportional `fr` columns summing to `10.00fr`, `wrap-id` with `_\u{200b}`, `->\u{200b}`, `+\u{200b}`, `7.5pt` text).
4. **Tighten §9 prose into General Mechanics Setup–Derivation–Specialization–Falsification flow** and unify table math-minus typography across carried Higgs/measured tables while preserving all 28 labels, both locked equations byte-for-byte, and exact 11 `#main*` / 8 `#aod-cite`.

### T2 — `typst/manual/sections/02_hydrogen_facing_shell_tests.typ` (§10)
1. **Tighten calculation card & prose** into crisp General Mechanics Setup–Derivation–Specialization–Falsification flow: retire stale `"checks the stated arithmetic only"` narrowing clause by accurately integrating `RC-031` (`hydrogen_shell_exact_series.csv`) and `RC-039` (`hydrogen_shell_dec_transitions.csv`) for exact D0 rational shell ratios while keeping NIST-ASD / Hydrogen Handbook wavelength targets explicitly quarantined at $B_{\text{ext}} = \mathsf{Q}_{\text{ext}}$; fix L196 typo (`external frequency coordinate` -> `External frequency-coordinate`); explicitly connect `R_series(n -> m) = R_{n->m, AO} >= 1` and reciprocal `lambda_n / lambda_{m+1} = 1 / R_series <= 1`.
2. **Bind `<tab:manual-hydrogen-dec-transitions>` LIVE to CSV** (`csv("/manual/data/boundary_sadar/hydrogen_shell_dec_transitions.csv", row-type: dictionary)`, 9 rows, 7 proportional `fr` columns summing to `10.00fr`, `8.5pt` text).
3. Preserve all 20 labels, exact `0` `#main*` calls, `3` `#aod-cite`, `4` `#secref`, `3` `#tabref`, `3` `#appref`.

### T3–T5 — Static Pre-Flight, Validation Suite & 144 ppi PNG Visual QA
1. Static check: zero `RC-025`, `RC-026`, `raw count 26`; required tokens & CSV bindings present; exact labels (`28 + 20`), both locked equations byte-identical, exact `#main*` (`11 + 0`), `#aod-cite` (`8 + 3`).
2. Run all 3 validation commands in `00_bundle.toml` (`audit_scientific_sources.py`, `build_publication.py --outdir _build/pub --check-registry`, `pytest tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py`).
3. Rasterize ALL §9 and §10 pages of `_build/pub/manual.pdf` at `144 ppi` PNG into `/tmp/bnd_p4_02_qa/` via `pdftoppm`, visually inspect EVERY rendered PNG via `view_file` (tuning `fr` weights/wrapping if ANY collision or overflow occurs), then delete `_build/pub` and `/tmp/bnd_p4_02_qa` so `git status` lists ONLY the 2 `scope.write_set` files.
