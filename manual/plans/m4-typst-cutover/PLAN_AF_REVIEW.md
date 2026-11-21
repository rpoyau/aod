# AF, AOD & Engineering Review — Proposed `S1 -> S4` Typst-First Master Plan

**Verdict: REVISE_PLAN_BEFORE_EXECUTION.**

The core engineering instinct in the pasted proposal—**separating pure format migration (`.tex` → `.typ`) from scientific/content changes**—is sound and high-leverage. However, auditing the proposal against the live state of `rpoyau/aod` (`m3-manual-si-alignment@98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`, tree `b4a667e3809e4a145580686d439811834b936343`) exposes **two P0 scientific-governance defects**, **four P1 sequencing/contract/toolchain blockers**, and **one P2 test-coupling/packaging gap** that must be corrected before dispatching Stage 1.

---

## 1. P0 Findings (Scientific Governance & AF Provenance)

### `R01` (P0) — `S2` imports unauthenticated experimental `aod-dec` / `v3–v5` claims into canonical `Manual`
- **Proposal text:** *"Stand up the canonical zero-float Python reference engine (`manual/engine/`, harvesting clean arithmetic/`Q_4`/GraphML machinery from `aod-dec` & `v3`–`v5`). Upgrade the `pp` (`3:3:6` + `3:3:6`) → `1:2:9yro` Tau rest-energy & ring/cavity example first: ... `2500`-denominator `(650, 703, 1147)/2500 -> (19/50, 31/50)|_Exo` adapter ... `3:4:6` wall tunnelling, Leprechaun 5-shell vs. LHC ablation, and quarantined `Decimal` `Q_ext` (`1776.86 MeV`)."*
- **Conflict with verified AOD/AF rules:**
  1. Experimental `aod-dec` code, traces, and results are strictly excluded from canonical `rpoyau/aod` M3 milestones without separate AF authentication.
  2. Verified `P2-13` audits establish that `lambda_reclose = 19/50` in `wavelet_shedding_simulation.csv` is bounded to a declared 90-tick open finite-model fixture and does **not** certify native reclosure or an authenticated `_Exo` identity.
  3. Importing unauthenticated `pp -> Tau` cavity models into canonical `Manual` smuggles unproved external premises into the core publication.
- **Required fix:** Keep experimental `aod-dec` / `v3–v5` cavity models strictly in a separate experimental/proposal lane until each mathematical claim passes independent AF review; harvest only audited zero-float helpers explicitly admitted into canonical contracts.

### `R02` (P0) — `S2` misdiagnoses `1:2:10` (`0.45` vs. `23/50`) as a "float-truncation fix"
- **Proposal text:** *"`1:2:10` `0.45 -> 23/50` float-truncation fix."*
- **Conflict with verified exact arithmetic:**
  - `manual/data/derived/tau_ring_diagnostic.csv` records `9/20 = 0.45`.
  - `manual/data/tau/aod_tau_fractal_ring_summary.csv` records depth-indexed decimals near `23/50 = 0.46` (`2299999999999999/5000000000000000`, etc.).
  - Their difference is an exact **`1/100`** rational gap—not a binary floating-point truncation artifact—and the originating generator is verified as **`UNRESOLVED_NOT_AUTHENTICATED_IN_REPO`**.
- **Required fix:** Record the unresolved provenance honestly instead of relabelling it a "float-truncation fix" or silently mutating frozen historical CSVs.

---

## 2. P1 Findings (Sequencing, Contracts, Figure Provenance & Toolchain)

### `R03` (P1) — Stack & phase-ordering drift
- The pasted draft assumes Phase 0 is still clearing and schedules *"Stage 4 (`S4`): `Main` M3 Compaction"* at the end.
- **Actual live repo state:** Phase 0, Phase 1 ([PR #45](https://github.com/rpoyau/aod/pull/45), `42ab900fcdd9478a7dfa5f5fac4fa318ea359834`), and Phase 2 ([PR #46](https://github.com/rpoyau/aod/pull/46), `98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`, hosted CI [run `44913132983`](https://github.com/rpoyau/aod/actions/runs/44913132983): `1342 passed, 1 skipped`) are **already built** on top of [PR #43](https://github.com/rpoyau/aod/pull/43) (`m3`).
- **Required fix:** Complete G2 review/sign-off on PR #46 first; re-pin Stage 1 to an explicit immutable commit (`98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3` or post-merge `main`) instead of an unspecified `HEAD`.

### `R04` (P1) — `S1` mixes pure format cutover with mutating 54 frozen figure digests
- `contracts/scientific/CANONICAL_BINDINGS.json` pins **166** `frozen_sha256` entries, including **54** figure files, **12** `.tex` files, and **55** `manual/data/` files.
- Replacing figures during `S1` breaks the "zero-drift parity anchor" invariant and fails `scripts/audit_scientific_sources.py` unless contracts are explicitly amended.
- **Required fix:** Split `S1` into:
  - **`S1a` (Pure Verbatim Format Cutover):** `.tex` → `.typ` + deterministic `ci/typ2tex.py`, keeping **all 54 frozen figures untouched** (`0` contract hash changes, `100%` `pytest` + `audit_scientific_sources.py` parity).
  - **`S1b` (Additive Native Typst Vector Figures):** Upgrade figures only after `S1a` parity is locked, backed by a per-figure provenance manifest and an explicit contract-amendment step.

### `R05` (P1) — Active TeX/figure inventory differs from the proposal's claims
- Actual repo counts at `98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`:
  - **23** active Main `.tex` files (**6** active `\includegraphics` calls in `figures_jpg/`).
  - **20** active Manual `.tex` files (**28** unique active `\includegraphics` targets, including 1 shared `../figures_jpg/cycle_disturbance_shedding_fixture.png`).
  - **11** frozen historical `.tex` snapshots under `manual/data/temporal_anchor/...` that **must never be ported or mutated**.
- Many of the 28 active Manual figures (and all 6 Main figures) are conceptual schematics or derived plots without raw CSV/JSON generators in `manual/data/`.
- **Required fix:** Scope `S1a` explicitly to the 23 active Main + 20 active Manual `.tex` files (strictly excluding `manual/data/`), and require a figure-classification manifest before vectorizing any figure in `S1b`.

### `R06` (P1) — Unverified local VM toolchain & external Typst Universe package dependencies
- Audited VM binaries:
  - `typst`: **NOT_INSTALLED**
  - `xelatex`: **NOT_INSTALLED** (required by `.github/workflows/build.yml`: `latexmk -xelatex`)
  - `latexmk`: **NOT_INSTALLED**
  - `pdflatex`: `/usr/bin/pdflatex` (does not match CI's XeLaTeX build!)
- External Typst Universe packages (`@preview/cetz`, `@preview/fletcher`) require network download or explicit vendoring, which may be blocked in a proxy-restricted VM.
- **Required fix:** Make toolchain provisioning an explicit prerequisite of `S1a`/`S1b`: install user-space `typst` (or run Typst compilation in CI), vendor any Typst plotting packages locally (or use zero-dependency native Typst drawing primitives), and verify round-tripped LaTeX using CI's `latexmk -xelatex` pipeline.

---

## 3. P2 Finding (Test/Macro Coupling & Delivery Packaging)

### `R07` (P2) — `19` TeX-inspecting `pytest` modules, `xr-hyper` coupling, and bundle size/Drive delivery
- **19 of 51** `pytest` modules directly scan `.tex` files for exact macros (`\mainequation`, `\mainsection`, `\mainappendix`, `\maintable`, `\aodprovenance`, `\AO`, `\SADARop`), table grammar, and `xr-hyper` `../main.aux` / `../main.fls` couplings. Note that `rpoyau/aod-lint` already contains a Typst AST parser (`typst_ast.rs`, `digest.rs`).
- Embedding full `main_typst.pdf`, `manual_typst.pdf`, and `latex_roundtrip/*.pdf` inside a dispatch/review ZIP contradicts compact Git/CI-bound bundle rules, and Google Drive is not connected in this VM (`Connected plugins: github.`).
- **Required fix:** Make passing `scripts/audit_scientific_sources.py` + all `pytest` suites on `typ2tex`-emitted LaTeX an explicit `S1a` gate, and keep review bundles compact and Git/CI-bound (delivering local SHA-256-verified ZIPs unless Google Drive is explicitly connected).
