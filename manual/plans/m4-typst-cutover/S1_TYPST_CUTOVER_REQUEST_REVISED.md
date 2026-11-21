# Revised Antigravity Dispatch Request — Stage 1a (`S1a`): Pure Verbatim Typst Cutover & Deterministic `typ2tex`

> **Prerequisite Gate:** Confirm whether Stage 1a should anchor on the current PR #46 head (`rpoyau/aod@98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3`, tree `b4a667e3809e4a145580686d439811834b936343`) or wait until PR #43 / PR #45 / PR #46 merge to `main`. Do not start from an unpinned `HEAD`.

## Objective

Execute **Stage 1a (`S1a`): Pure Verbatim Typst Cutover + Deterministic CI `typ2tex` Converter** inside an isolated workspace `/home/antigravity/aod_s1a_typst_cutover/` (read-only from the pinned `rpoyau/aod` commit; zero mutations to `/home/antigravity/rpoyau/aod`).

## Non-Negotiable `S1a` Rules

1. **Zero Text, Math, Data, or Figure Changes:**
   - Port only the **23 active Main `.tex` files** and **20 active Manual `.tex` files** into modular `.typ` files (`typst_src/main/`, `typst_src/manual/`, `typst_src/lib/aod_schema.typ`).
   - Strictly **exclude** the **11 frozen historical `.tex` snapshots** under `manual/data/temporal_anchor/`.
   - Keep **all 54 frozen figures** (`figures_jpg/`, `manual/figures/`) and **all 116 `manual/data/` files** byte-for-byte unchanged (figure vectorization is deferred to `S1b` with an explicit provenance manifest and contract amendment).
2. **Exact Macro & Anchor Conservation:**
   - Preserve 100% of **455 Main labels**, **227 Manual labels**, **198 Main / 20 Manual labelled display equations**, custom macros (`\mainequation`, `\mainsection`, `\mainappendix`, `\maintable`, `\aodprovenance`, `\AO`, `\SADARop`), and `xr-hyper` cross-document references (`../main.aux`, `../main.fls`).
3. **Deterministic `ci/typ2tex.py` + `ci/verify_s1a_parity.py`:**
   - Active under both normal `python3` and `python3 -O` (explicit `ValueError`/`TypeError`, zero bare `assert`).
   - Must verify:
     1. Zero normalized prose/math token drift between baseline `.tex` and `typ2tex`-emitted `.tex`.
     2. 100% label, equation, citation, and table-cell conservation.
     3. Passing `scripts/audit_scientific_sources.py` and all **19** TeX-inspecting `pytest` modules against the `typ2tex`-emitted tree.
4. **Honest Toolchain Verification:**
   - Provision user-space `typst` (if network/proxy permits) or report exact CI build recipe; do not require unvendored remote Typst Universe packages (`@preview/cetz`, `@preview/fletcher`) in `S1a`.
   - Verify round-tripped LaTeX against the repository's actual `latexmk -xelatex` build contract (`.github/workflows/build.yml`), never claiming `pdflatex` substitutes for XeLaTeX.
   - Run `rpoyau/aod-lint` (including its native `typst_ast.rs` checks where applicable), reporting `PARTIAL` coverage honestly.

## Compact Git-Bound Deliverables (`AOD_S1A_TYPST_CUTOVER_BUNDLE_R01.zip`)

Keep the review/dispatch archive compact and flat (`< 100` entries, `< 20 MB`, no nested ZIPs, no full PDFs if CI/Git holds them):
- `typst_src/` (or Git branch/commit pin + manifest)
- `ci/typ2tex.py` & `ci/verify_s1a_parity.py`
- `S1A_PARITY_REPORT.json` (normal + `-O` byte-identical digest, label/equation counts, `audit_scientific_sources.py` & 19 TeX-test results)
- `FIGURE_PROVENANCE_MANIFEST_FOR_S1B.json` (classifying all 28 active Manual + 6 active Main graphics to unblock `S1b`)
- `README.md` and `SHA256.txt` (outer ZIP SHA-256 reported separately)

## Deferred to Stage 1b (`S1b`) — Do NOT Bundle into `S1a`
- Native Typst vector figure replacements (`figures_typst/*.typ`), Okabe-Ito palette upgrades, and `CANONICAL_BINDINGS.json` figure-hash amendments.
