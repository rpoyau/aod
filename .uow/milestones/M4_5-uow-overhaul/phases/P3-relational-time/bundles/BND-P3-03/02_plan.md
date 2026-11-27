# BND-P3-03 Execution Plan (`02_plan.md`)

## SCOPE GAPS & HIDDEN PINS AUDIT

1. **Out-of-scope generated figure/LaTeX pins (deferred cleanly to `BND-P5-03` bulk seal):**
   - `typst/figure_inventory.json`, `latex/manual/figures/generated/temporal-si-bridge-feynman.pdf`, `FIGURE_MANIFEST.json`, `GENERATION_MANIFEST.json`, and `latex/manual/sections/*.tex` are outside `scope.write_set` and must NOT be touched in `BND-P3-03`.
   - `tests/test_main_manual_references.py` asserts `set(gen_references) == set(references)` against `latex/manual/sections/00_native_closure_wave_temporal_fixtures.tex`, so `00_native_closure_wave_temporal_fixtures.typ` MUST preserve the EXACT set (and count) of `#mainequation` and `#mainsection` targets.
2. **Confirmed ZERO SHA-256 pins in `contracts/scientific/` for all 3 `write_set` files.**
   - `OWNERSHIP_AND_FIXTURES.json` binds 3 anchors in `00_native_closure_wave_temporal_fixtures.typ` (`fig:fractal-tesseract-beat-family`, `fig:field-count`, `subsec:disoma-declaration`); `CANONICAL_BINDINGS.json` binds `manual:m1-native-fixtures`.
3. **Third scientific discrepancy caught in `temporal_si_bridge_feynman.typ` (line 49):**
   - Line 49 previously stated `Pre-cut k <= 40 invariant`; the true committed prefix invariant is **`k <= 39`** (`k = 40` is the intervention cut; `k = 41` is the first divergent response cut). Fix alongside the `N_{0,val} = 32` and `Hydrogen hyperfine (1420.4 MHz)` fixes.
4. **Exact Registry & Reference-Count Locks (MUST hold with zero drift):**
   - Global: `455` Main labels, `281` Manual labels, `172` Manual `mainref_uses`.
   - `00_native_closure_wave_temporal_fixtures.typ`: exact **8 labels** (`manual:m1-native-fixtures`, `subsec:disoma-declaration` via `#aod-anchor`, `fig:field-count`, `fig:fractal-tesseract-beat-family`, `manual:wavelet-continuation-fixtures`, `manual:m1:dec-closure-walk`, `fig:manual-native-closure-q4-walk`, `tab:manual-native-closure-dec-walk`), exact **48 `#main*` uses** (`24` body + `24` `#aod-provenance`: `46` `#mainequation` across the exact 29 keys + `1` `#mainsection("main:subsec:aod-wavelet-continuation")` + `1` `#mainappendix("main:app:rd-tests:corollaries")`), `1` `#secref("manual:calculation-spine")`.
   - `03_temporal_observation.typ`: exact **11 labels** (`manual:m3-temporal`, `eq:manual-m3-cycle-bridge`, `tab:manual-m3-anchor-transfer`, `manual:m3-metrology`, `eq:manual-m3-observed-advance`, `eq:manual-m3-accumulated-si`, `eq:manual-m3-hydrogen-reduction`, `eq:manual-m3-residual-dependence`, `manual:m3-temporal:dec-si-bridge`, `fig:manual-temporal-si-bridge-feynman`, `tab:manual-temporal-dec-bridge`), exact **30 `#main*` uses** (`19` body + `11` `#aod-provenance`: `28` `#mainequation` across exact 10 keys + `2` `#mainsection("main:subsec:m3-conditional-si-interface")`), exact **5 `#aod-cite` keys** (`hellwig-hydrogen-1970`, `heavner-nist-f2-2014`, `nist-tn1297-comparison`, `bipm-second`, `nist-fountain`), `2` `#eqref("eq:manual-m3-observed-advance")`.

---

## EXECUTION DAG

```text
T1 (temporal_si_bridge_feynman.typ) ──┐
T2 (03_temporal_observation.typ) ─────┼──▶ T4 (Static Invariant Checks) ──▶ T5 (Bundle Validation) ──▶ T6 (144 ppi PNG Visual QA)
T3 (00_native_closure_wave_...typ) ───┘
```

### T1 — Upgrade `typst/lib/figures/manual/temporal_si_bridge_feynman.typ`
- Single `#import "/typst/lib/aod_plots.typ": *`; single literal `csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)`; zero backticks outside comments; zero LaTeX spacing escapes (`\,`, `\;`, `\:`, `\!`); opaque black text >= `6.6pt`.
- Canvas `15.0 cm x 9.4 cm` reading ALL 9 live CSV rows `rows.at(0..8)` (`r-pair`, `r-lag`, `r-cs`, `r-trA`, `r-trB`, `r-cut`, `r-rcd`, `r-adv`, `r-hos`):
  - **Panel (a) (`x in [0.36, 5.72]`, `y in [1.34, 8.20]`):** coupled lineages `i` (4 `C` nodes) & `j` (3 `R` nodes) on `B_pair(0, 30]`, Sub-box 1 (`T1, T2, T7, T8`: `biz`, lag, directional RCD `5, 7`, observed advance `7/17`, signed `-1/2`), Sub-box 2 (`T6, T9`: **FIX #3: shared prefix `k <= 39`**, intervention at `k = 40`, response strictly at `k = 41` `(6,5)->(2,5)` `6/5 -> 2/5`, hostile disconnect rejected at T9).
  - **Panel (b) (`x in [6.20, 10.30]`):** Cs-133 chain (`9,192,631,770` Hz plain text, `1/4596315885` s, `13788947655` Hz) + **FIX #2: `Hydrogen hyperfine (1420.4 MHz) chain`** (Hellwig 1970 21 cm maser heterodyne reduction; separate residual budget; zero `1S-2S`).
  - **Panel (c) (`x in [10.78, 14.64]`):** Field A (`cal=58,val=48`, **FIX #1A: `Held-out ref N_(0,upright("val")) = 32`**, pred `768/29`, resid `-5/29 != 0`) and Field B (`cal=151,val=102`, **FIX #1B: `Held-out ref N_(0,upright("val")) = 32`**, pred `3264/151`, resid `-49/151 != 0`). Zero `Held-out obs = 26` or `21`.
  - **Bottom invariant bar (`y = 8.38, h = 0.72`):** live summary containing `"RC-037"`, `T1–T9`, `-5/29`, `-49/151`.

### T2 — Refactor `typst/manual/sections/03_temporal_observation.typ` In Place
- Compact 434-line dense prose wall into ~290–320 crisp lines in General Mechanics Setup–Derivation–Specialization–Falsification blocks.
- Eliminate ALL `[1, 30]` occurrences (replace with half-open `(0, 30]`).
- Preserve ALL 5 numbered equations (`eq:manual-m3-cycle-bridge`, `eq:manual-m3-observed-advance`, `eq:manual-m3-accumulated-si`, `eq:manual-m3-hydrogen-reduction`, `eq:manual-m3-residual-dependence`) verbatim, ALL 11 labels, exact 30 `#main*` calls, and all 5 `#aod-cite` keys.
- Explicitly distinguish (1) self-contained `RC-037` causal cut-40 simulator (`k <= 39` shared prefix, cut-40 drop -> cut-41 `(6,5)->(2,5)`, hostile disconnect rejected) from (2) separately bound Matter I v2 `--consumer-root` replay.
- Bind `<tab:manual-temporal-dec-bridge>` LIVE via `csv("/manual/data/boundary_sadar/temporal_si_bridge_dec_ledger.csv", row-type: dictionary)` rendering all 9 stages `T1..T9` cleanly with `"\u{200b}"` break-opportunity wrapping and balanced `fr` columns `(1.55fr, 1.55fr, 2.40fr, 1.35fr, 1.40fr, 1.75fr)` so zero horizontal overflow occurs.

### T3 — Refactor `typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ` In Place
- Consolidate dense paragraphs into crisp General Mechanics Setup–Derivation–Specialization–Falsification blocks (`Setup and calculation card`, `Derivation: reflected legs, flux controls, and prefix binding`, `Specialization: field count, periodic support, and directional cadence`, `Wavelet continuation, recipient stages and harmonic scope`, `Five-boundary Q4 D.E.C. closure, beat, and fold walk`).
- Preserve ALL 8 labels (including Phase 5 anchors `<fig:field-count>` and `<fig:fractal-tesseract-beat-family>` intact), exact 48 `#main*` calls (exact 29 `#mainequation` + 1 `#mainsection` set matching `test_main_manual_references.py`), and `1` `#secref("manual:calculation-spine")`.
- Bind `<tab:manual-native-closure-dec-walk>` LIVE via `csv("/manual/data/boundary_sadar/native_closure_wave_dec_walk.csv", row-type: dictionary)` with `"\u{200b}"` wrapping and balanced `fr` columns `(1.55fr, 1.15fr, 1.35fr, 1.65fr, 0.60fr, 0.85fr, 2.85fr)` rendering all 8 stages `M1_leg_out..M6_z4_harmonic` cleanly.

### T4, T5 & T6 — Static Checks, Bundle Validation, and 144 ppi PNG Visual QA
1. Static pre-flight verification of forbidden tokens (`[1, 30]`, `Held-out obs = 26/21`, `1S-2S`, `k <= 40`, backticks/LaTeX escapes in figure), exact label counts (`8` + `11`), exact `#main*` counts (`48` + `30`), and 5 byte-identical numbered equations.
2. Run all 3 commands in `00_bundle.toml`:
   - `python3 -B scripts/audit_scientific_sources.py .`
   - `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub --check-registry`
   - `python3 -B -m pytest -q tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py tests/test_main_manual_references.py`
3. Rasterize ALL Manual §2 and Manual §7 pages of `_build/pub/manual.pdf` at `144 ppi` PNG into `/tmp/bnd_p3_03_qa/` via `pdftoppm -png -r 144`, visually inspect EVERY rendered PNG with `view_file` (iterating geometry/column widths until ZERO collisions, ZERO clipping, ZERO margin overflows), then delete `_build/pub` and `/tmp/bnd_p3_03_qa` so `git status` shows ONLY the 3 `scope.write_set` files.
