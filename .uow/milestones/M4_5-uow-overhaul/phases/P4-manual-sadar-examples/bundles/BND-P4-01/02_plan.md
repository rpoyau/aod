# Execution Plan: `BND-P4-01` (Manual §3, §4, §8 Refactoring & Live CSV Binding)

- **Bundle**: `BND-P4-01` (`M4_5-uow-overhaul` / `P4-manual-sadar-examples`)
- **Worktree**: `/home/antigravity/rpoyau/wt-BND-P4-01`
- **Base commit**: `b732b84baae7afcac86a0ab05e7e2d9922acbf69` (`uow/BND-P3-03`)
- **Write Set (strict)**:
  1. `typst/manual/sections/00_dec_ledger.typ` (§4)
  2. `typst/manual/sections/00_awareness_fixtures.typ` (§3)
  3. `typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ` (§8)

## SCOPE GAPS & CLARIFICATIONS
- **Write-set scope gaps**: None.
- **CSV clarification**: `chiral_stokes_disoma_exchange.csv` does not exist; both `RC-025` (cuts 1–2: `B_flip|1`, `B_flip|2`) and `RC-026` (cut 3: `B_disoma|3`) reside in `manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv`. Do NOT reference `chiral_stokes_disoma_exchange.csv`.
- **Zero `.typ` SHA-256 pins** in `contracts/scientific/`.

## 1. Exact Locks (MUST Hold With Zero Drift)
- **Global**: `455` Main labels, `281` Manual labels, `172` Manual `mainref_uses`.
- **Labels (59 total across 3 files)**:
  - `00_awareness_fixtures.typ` (§3): exact **19 labels** (9 headings, 1 `#aod-anchor(<man:temporal-awareness-controls>)`, 7 numbered equations, 2 figures `fig:manual-awareness-matched-feynman`, `tab:manual-awareness-dec-ledger`).
  - `00_dec_ledger.typ` (§4): exact **19 labels** (12 headings, 5 table figures, 2 image figures).
  - `03_short_window_rcd_shedding_fixtures.typ` (§8): exact **21 labels** (13 headings, 4 table figures, 4 image figures).
- **7 Verbatim SHA-256 Locked Equations in `00_awareness_fixtures.typ` (DO NOT alter 1 byte of L51, L61, L72, L213, L284, L296, L366)**:
  - `eq:sadar-rational-response`, `eq:awareness-response`, `eq:awareness-causal-difference`, `eq:action-return-retention`, `eq:awareness-shedding-bridge`, `eq:awareness-conditioned-shedding`, `eq:mindfulness-stability`.
  - Keep `S_(24)^+ = ...` inline (never a display equation matching a Main `unique_signatures`).
- **Exact `#main*` and citation counts**:
  - `00_awareness_fixtures.typ`: exact **32 `#mainequation`** (19 unique keys), **17 `#eqref`** (all 7 moved keys), **2 `#secref`** (`manual:calculation-spine`, `sec:m2-awareness-ladder`).
  - `00_dec_ledger.typ`: exact **4 `#mainequation`** + **5 `#mainsection`** = **9 `#main*`**, **3 `#aod-cite`** (`norrisMarkov`, `levinPeresWilmer`, `lawlerLimic`), **5 `#secref`**, **1 `#tabref`**.
  - `03_short_window_rcd_shedding_fixtures.typ`: exact **10 `#mainequation`** + **2 `#mainsection`** = **12 `#main*`**, **3 `#secref`**.

## 2. Execution DAG
```text
[Node 1: 00_dec_ledger.typ (§4)] ──┐
[Node 2: 00_awareness_fixtures.typ (§3)] ──┼──> [Node 4: Static Pre-Flight] ──> [Node 5: 3 Validation Cmds] ──> [Node 6: 144 ppi PNG Visual QA]
[Node 3: 03_short_window_rcd_shedding_fixtures.typ (§8)] ──┘
```

### Node 1 — `typst/manual/sections/00_dec_ledger.typ` (§4)
1. Tighten prose into crisp General Mechanics Setup–Derivation–Specialization–Falsification flow while keeping all 19 labels, all 9 `#main*` calls, all 3 `#aod-cite`, all 5 `#secref`, `#tabref`, and all 7 floats intact.
2. Cite `#raw("RC-045")` (`#raw("ternary_swar_and_trit_ratio")`) in §4.1 (`manual:dec-ledger:row-format`), §4.5 (`manual:dec-ledger:hinge-slide`), and closing `#aod-paragraph[Atomic leg and hinge role.]` for the exact 2-bit ternary encoding (`00 = 0_D` dwell, `01 = +1`, `10 = -1`, `11 = 0_H` preserved structural hinge).
3. Replace ALL 18 occurrences of `B bar.v t` (L227, L229, L233, L237 ×6, L243 ×2, L246 ×3, L250 ×3, L287) with `B bar.v k` (zero remaining `B bar.v t` in §4).
4. Fix §4.8 (L326): replace `RC-028` and `RC-029` with `#raw("RC-025")` (`#raw("dec_chiral_flip_walk")`, cuts 1–2) and `#raw("RC-026")` (`#raw("dec_two_carrier_chiral_stokes")`, cut 3), cross-referenced with `#raw("RC-045")`, all in `#raw("manual/data/boundary_sadar/dec_chiral_flip_continuous_walk.csv")`. Confirm ZERO `RC-028` or `RC-029` remain in §4.

### Node 2 — `typst/manual/sections/00_awareness_fixtures.typ` (§3)
1. Preserve all 7 locked numbered equations byte-for-byte, all 19 labels, `#aod-anchor(<man:temporal-awareness-controls>)`, all 32 `#mainequation` (19 unique keys), all 17 `#eqref`, both `#secref`, inline table, A0–A18 longtable, and `<fig:manual-awareness-matched-feynman>`.
2. Tighten prose into crisp General Mechanics structure integrating `RC-034` seamlessly.
3. Replace `<tab:manual-awareness-dec-ledger>` with live CSV table reading `csv("/manual/data/boundary_sadar/awareness_operativity_dec_walk.csv", row-type: dictionary)` (columns: `cut_k`, `branch_mode`, `state_S`, `vertex_v`, `edge_e`, `target_ve`, `current_J`, `adm`, `route_outcome`) using fractional `fr` column widths and `s.replace("_", "_\u{200b}")` break-opportunity wrapping so zero horizontal overflow occurs.

### Node 3 — `typst/manual/sections/03_short_window_rcd_shedding_fixtures.typ` (§8)
1. Keep bound discrete-window dummy index `t in omega` / `B bar.v t` on L50 & L101 (distinct from target-bin index `k in K_bin`; clarify explicitly in prose).
2. Retire the contradictory sentence `"The application still needs a frozen nested-path generator..."` (L203): state accurately that `#raw("RC-030")` (`dimonhexon_double_slit_ring_paths.csv`) genuinely executes the finite `C_6` (`(V_6, E_6)`) two-step path-pair generator in exact zero-float `TritWord`/`TritRatio` arithmetic (`410 + 38 = 448`, `sum Delta^Z = 0`, `sum m_k = 6`), while keeping external physical detector/exposure probability laws explicitly separated.
3. Fix L393: replace `verified alongside #raw("RC-029")` with `verified alongside #raw("RC-030")` (keeping `#raw("RC-038")` primary; zero remaining `RC-029` in §8).
4. Replace `<tab:manual-short-window-dec-ledger>` with live CSV table reading `csv("/manual/data/boundary_sadar/short_window_rcd_dec_ledger.csv", row-type: dictionary)` (columns: `support`, `RD`, `window_len`, `rho_omega`, `p_D`, `Q_D`, `C_close`, `X_shedding`, `total_3RD`).
5. Tighten prose cleanly preserving all 21 labels, all 12 `#main*` calls, all 3 `#secref`, and all 8 floats.

### Nodes 4–6 — Static Pre-Flight, Bundle Validation & 144 ppi PNG Visual QA
1. Run static check verifying forbidden tokens absent, required tokens present, exact labels (`19, 19, 21`), exact `#main*` (`32, 9, 12`), and 7 byte-identical locked equations.
2. Run all 3 validation commands in `00_bundle.toml`:
   - `python3 -B scripts/audit_scientific_sources.py .`
   - `PATH="$HOME/.local/bin:$PATH" python3 -B scripts/build_publication.py --outdir _build/pub --check-registry`
   - `python3 -B -m pytest -q tests/test_active_scientific_sources.py tests/test_mathematical_bindings.py tests/test_main_manual_references.py tests/test_main_manual_concept_ownership.py`
3. Rasterize modified §3, §4, and §8 pages of `_build/pub/manual.pdf` at `144 ppi` PNG into `/tmp/bnd_p4_01_qa/` via `pdftoppm`, visually inspect EVERY modified table and section page via `view_file` (iterating column `fr` weights/wrapping until ZERO overlaps, clipping, or margin overflows), then delete `_build/pub` and `/tmp/bnd_p4_01_qa`.
