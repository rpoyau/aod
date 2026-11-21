# AOD `S1 -> S4` Typst-First Plan — AF Review & Corrected Dispatch Bundle (`R01`)

Compact, flat, SHA-256-verified review and revised dispatch package auditing the proposed `S1 -> S4` Typst-First Master Plan against live `rpoyau/aod@98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3` (tree `b4a667e3809e4a145580686d439811834b936343`).

## Summary Verdict

**`REVISE_PLAN_BEFORE_EXECUTION`** — Separating pure `.tex` → `.typ` format migration from content changes is a strong engineering decision, but the original pasted draft contains **2 P0** scientific/provenance defects (`aod-dec` import into canonical Manual; erroneous `0.45 -> 23/50` "float-truncation" diagnosis), **4 P1** blockers (M3 stack drift vs. completed Phase 0–2; 54 frozen figures in `CANONICAL_BINDINGS.json`; active vs. frozen TeX/figure inventory; missing local `typst`/`xelatex`/`latexmk` & unvendored Typst packages), and **1 P2** gap (`19` TeX-scanning `pytest` modules + compact packaging).

## Contents (8 Flat Files)

1. `ORIGINAL_PROPOSAL_SNAPSHOT.md` — Verbatim preserved snapshot of the pasted `S1 -> S4` proposal.
2. `PLAN_AF_REVIEW.md` — Full AF, AOD, and engineering review (`R01`–`R07`).
3. `FINDINGS.json` — Structured findings (`2 P0`, `4 P1`, `1 P2`) with smallest missing premises and exact fixes.
4. `CORRECTED_S1_S4_MASTER_PLAN.md` — Re-ordered, governance-compliant `S0 -> S4` roadmap splitting `S1a` (pure verbatim format cutover, zero frozen-hash breakage) from `S1b` (audited figure vectorization) and quarantining unauthenticated experimental models (`S3`).
5. `S1_TYPST_CUTOVER_REQUEST_REVISED.md` — Ready-to-dispatch `S1a` request once base commit and toolchain choice are confirmed.
6. `TOOLCHAIN_AND_ASSET_AUDIT.json` — Verified local VM toolchain and `rpoyau/aod@98ddfa0e` asset/contract counts.
7. `README.md` — This manifest guide.
8. `SHA256.txt` — SHA-256 checksums for the 7 other flat files (`sha256sum -c SHA256.txt`). Outer ZIP SHA-256 is reported separately.
