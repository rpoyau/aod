# Original Pasted `S1 -> S4` Typst-First Proposal (Verbatim Audit Snapshot)

Preserved verbatim for AF review provenance; do not execute unamended.

---

Switching **Typst first with zero text changes** (updating only the figures to clean native Typst vector graphics while verifying 100% round-trip parity with the current LaTeX anchor) is the strictest, highest-leverage engineering order.

Separating **format migration** from **content changes** guarantees a clean baseline: if you rewrite text or math while changing markup, diffs become unreadable. Locking an exact 1-to-1 Typst port (`Manual` and `Main`) + deterministic CI `typ2tex` converter first gives you a rock-solid, zero-drift platform before touching a single equation or worked example.

### Corrected Strict Sequence (`S1` -> `S4`)

| Stage | Exact Scope | Strict Invariant / Gate |
| --- | --- | --- |
| **Stage 1 (`S1`): Pure Typst Cutover (`0` Text Changes + Native Typst Figures + CI `typ2tex`)** | Port existing `Manual` (and `Main`) LaTeX prose, equations, tables, and `\label` anchors **verbatim** into modular `.typ` files (`manual/main.typ`, `main.typ`). Replace legacy Matplotlib/TikZ figures with native programmatic Typst figures (`CeTZ` / `Fletcher`, high-contrast colorblind-safe palette). Build `ci/typ2tex.py` so current LaTeX remains the verified CI output target. | **Zero semantic or prose diff** against current LaTeX; `100%` of `\label`, `\ref`, equation numbers, and table values preserved identically; both `typst compile` and CI-emitted LaTeX build cleanly. |
| **Stage 2 (`S2`): Reference Engine + Flagship `pp -> Tau` Rest-Energy & Sheddic Overhaul in `Manual`** | Stand up the canonical zero-float Python reference engine (`manual/engine/`, harvesting clean arithmetic/`Q_4`/GraphML machinery from `aod-dec` & `v3`–`v5`). Upgrade the **`pp` (`3:3:6` + `3:3:6`) -> `1:2:9yro` Tau rest-energy & ring/cavity example first**: `PAST (1..58) -> PRESENT (58) -> FUTURE (59..62)` duonic chiral-flip path-integral funnel, `2500`-denominator `(650, 703, 1147)/2500 -> (19/50, 31/50) | _Exo` adapter, `1:2:10` `0.45 -> 23/50` float-truncation fix, `3:4:6` wall tunnelling, Leprechaun 5-shell vs. LHC ablation, and quarantined `Decimal` `Q_ext` (`1776.86 MeV`). | |
| **Stage 3 (`S3`): Remaining `Manual` Worked Examples Overhaul** | Bring every remaining Manual section up to the exact same computational transparency standard as `pp -> Tau`: §2/M3 temporal chains (separate H-maser & `Cs-133` SI maps), §3 Awareness (`A0`–`A18`), §4–5 D.E.C. hinge-slide / tunnelling / double-slit FRG, §6.7 `3:3:7yro` Higgs trace score, §7 Hydrogen shells, §8–9 boundary/solar `O0` maps, §10.5–10.7 3D traces & SPARC controls, and §11 lensing. | Zero "originating recipe not supplied" or hand-copied static CSV tables left in `Manual`; every example reproducible via `python3 -m manual.engine --verify-all`. |
| **Stage 4 (`S4`): `Main` M3 Compaction & Optional Rust Core (`crates/aod-core/`)** | Apply reviewed M3 ontology compactions cleanly in Typst (automatically propagating to LaTeX via CI `typ2tex`), followed by optional `std`-Rust `t32`/`Ratio` acceleration validated against `manual/engine/` golden vectors. | Full anchor conservation + CI Typst/LaTeX dual-build green. |

### Proposed Antigravity Prompt for Stage 1 (`S1` Bundle)

Execute **Stage 1 (`S1`): Strict Verbatim Typst Cutover + Native Typst Figures + Deterministic CI `typ2tex` Converter** in `/home/antigravity/aod_s1_typst_cutover/` (sourced read-only from `/home/antigravity/rpoyau/aod` HEAD, packaged upon completion as `/home/antigravity/AOD_S1_TYPST_CUTOVER_BUNDLE_R01.zip`).

- Non-Negotiable Stage 1 Rules:
  1. ZERO Text or Mathematical Changes.
  2. Do NOT Mutate `/home/antigravity/rpoyau/aod` Working Tree.
  3. Current LaTeX Is the Frozen Parity Anchor (`ci/typ2tex.py` + `ci/verify_s1_parity.py`).
  4. Native Typst Figures (`figures_typst/`, CeTZ/Fletcher, reading directly from `manual/data/` CSV/JSON files, compiled to cropped vector `.pdf`).
- Deliverables: `typst_src/manual/`, `typst_src/main/`, `lib/aod_schema.typ`, `figures_typst/*.typ`, `ci/typ2tex.py`, `ci/verify_s1_parity.py`, `build/manual_typst.pdf`, `build/main_typst.pdf`, `build/latex_roundtrip/*.pdf`, `S1_PARITY_REPORT.json`, `AUDIT_CHECKS.txt`, `SHA256.txt`.
