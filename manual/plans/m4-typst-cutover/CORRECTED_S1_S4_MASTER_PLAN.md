# Corrected Governance-Compliant `S0 -> S4` Typst-First Master Plan

Re-anchored to the live state of `rpoyau/aod` (`m3-manual-si-alignment@98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`, tree `b4a667e3809e4a145580686d439811834b936343`), preserving all AF / AOD conservation boundaries and `CANONICAL_BINDINGS.json` invariants.

---

## Corrected Sequence (`S0` → `S4`)

| Stage | Exact Scope | Strict Invariant / Gate |
| --- | --- | --- |
| **Stage 0 (`S0`): Freeze & Close Active M3 Stack (`PR #43`, `#45`, `#46`)** | Complete G2 review of open Draft PR [#46](https://github.com/rpoyau/aod/pull/46) (`98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`, CI `1342 passed, 1 skipped`). Lock an explicit immutable Git base SHA before starting format migration. | Zero moving-target merge drift; M3 Main ontology compaction (`PR #45`) and Manual alignment (`PR #46`) already baked in before `.tex` → `.typ` cutover. |
| **Stage 1a (`S1a`): Pure Verbatim Typst Cutover + Deterministic `ci/typ2tex.py` (`0` Text Changes, `0` Figure Changes)** | Port the **23 active Main** + **20 active Manual** `.tex` files (strictly excluding the **11 frozen historical `.tex` snapshots** under `manual/data/`) verbatim into modular `.typ` sources + `lib/aod_schema.typ`. Keep all **54 frozen figures** byte-identical. Build `ci/typ2tex.py` and `ci/verify_s1_parity.py` (normal + `-O`, zero bare `assert`). | **Zero prose/math diff**; **455 Main / 227 Manual labels** 100% conserved; `typ2tex` output passes `scripts/audit_scientific_sources.py`, all **19** TeX-inspecting `pytest` modules, full `1342+` hosted CI (`latexmk -xelatex`), and `typst compile` + `aod-lint` Typst AST checks. |
| **Stage 1b (`S1b`): Audited Native Typst Vector Figures (`figures_typst/`)** | First publish a per-figure provenance manifest classifying all **28** unique active Manual + **6** active Main graphics into *(a) authenticated data-backed plots*, *(b) conceptual schematics*, and *(c) unresolved-provenance derived plots*. Vectorize approved figures using zero-dependency native Typst (or explicitly vendored local packages), keeping historical frozen rasters preserved or amended via an explicit `CANONICAL_BINDINGS.json` contract PR. | Zero fabricated CSV backing for conceptual or unresolved plots; visual page diff verified; `CANONICAL_BINDINGS.json` amended explicitly only for authorized figure replacements. |
| **Stage 2 (`S2`): Audited Zero-Float Reference Engine (`manual/engine/`) for Already-Authenticated Manual Sectors** | Consolidate existing *canonical* `manual/scripts/` exact `int`/`Fraction` verifiers (`aod_native_closure_wave.py`, `aod_awareness.py`, `aod_temporal_metrology.py`, `aod_temporal_observation.py`, `aod_manual_wavelet_si_alignment.py`, D.E.C. / SPARC / lensing verifiers) into a unified reproducible entry point (`python3 -m manual.engine --verify-all`) with zero new physical postulates. | Zero experimental `aod-dec` imports; every frozen CSV digest (`166/166`) preserved unless formally amended; separate H-maser / Cs-fountain chains, `MAP-07`/`MAP-28`, and physical-SI validation hold intact. |
| **Stage 3 (`S3`): Independent AF Authentication Gate for Proposed Experimental Models (`pp -> Tau` Cavity, etc.)** | Evaluate experimental prototypes (`aod-dec`, `v3`–`v5` `pp -> Tau` cavity funnel, `19/50` `_Exo` proposals, unresolved `9/20` vs. `~23/50` Tau ring provenance) in a **quarantined external review branch/bundle**—never silently merged into `Manual`. Only claims passing independent AF derivation + provenance verification may graduate into canonical `Manual`. | Unresolved `1:2:10` (`9/20` vs. `~23/50`) never falsely relabelled "float-truncation"; `19/50` finite-model boundary never promoted without proof; quarantined `Q_ext` boundary preserved. |
| **Stage 4 (`S4`): Optional `std`-Rust Exact Core (`crates/aod-core/`)** | Implement optional `std`-only Rust exact integer/rational acceleration validated bit-for-bit against `manual/engine/` exact golden vectors and CI dual Typst/LaTeX builds. | Zero float operands; exact cross-language golden parity under `cargo test` and `python3`/`python3 -O`. |

---

## Key Improvements Over the Original Draft

1. **Eliminates P0 scientific violations:** Quarantines `aod-dec` / `v3–v5` `pp -> Tau` prototypes behind an explicit AF gate (`S3`) and removes the erroneous `0.45 -> 23/50` "float-truncation" claim.
2. **Eliminates contract breakage during format cutover:** Splits pure markup cutover (`S1a`, `0` frozen-hash changes) from figure vectorization (`S1b`, explicit manifest + contract amendment).
3. **Aligns with real Git history:** Anchors to the already-completed Phase 0–2 M3 stack instead of re-running Phase 1 compaction at the end.
4. **Matches real build & test constraints:** Enforces compatibility with `latexmk -xelatex`, `xr-hyper`, `scripts/audit_scientific_sources.py`, `aod-lint` Typst AST support, and all 19 TeX-inspecting `pytest` modules.
