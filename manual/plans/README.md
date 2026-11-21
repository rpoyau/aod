# Temporary M4 Planning Surface (`manual/plans/`)

> **Temporary staging directory — scheduled for cleanup.**  
> This directory stages working M4 planning and AF review records on the initial `m4` stacked draft PR. It is **not** scientific source or a publication input and should be removed (`git rm -r manual/plans`) once moved to a dedicated plans repository or before any M4 release freeze.
>
> **Why `manual/plans/*.md`?** Both `scripts/build_release_bundle.py` and `tests/test_ci_release_builder.py` are SHA-256-frozen in `contracts/scientific/CANONICAL_BINDINGS.json`. Staging temporary plans as `.md` files under `manual/plans/` keeps all 166 protected files, scientific contracts, Main TeX, Manual TeX, and release-builder checks 100% untouched and green without modifying frozen build guards.

## Stack Placement

| Layer | Branch | PR Base | Head Commit |
| --- | --- | --- | --- |
| M3 root | `m3` (PR #43) | `main` | `dc1a434c8fc2b7b958e44d7da63277c7856a8d67` |
| M3 Phase 1 / G1 | `m3-ontology-compaction` (PR #45, Draft) | `m3` | `42ab900fcdd9478a7dfa5f5fac4fa318ea359834` |
| M3 Phase 2 / G2 | `m3-manual-si-alignment` (PR #46, Draft) | `m3-ontology-compaction` | `98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3` |
| **M4 initial plan** | **`m4` (Draft PR)** | `m3-manual-si-alignment` | Staged here |

## Staged Plan Bundle (`m4-typst-cutover/`)

Unpacked from `AOD_TYPST_S1_S4_PLAN_AF_REVIEW_BUNDLE_R01.zip` (`16,880` B, outer `SHA-256: 080dfe7d86628f49465ce6493e502798cab9ec16138869cc4d75adb477b5ab6b`, archived in private repo `rpoyau/aod-bundles` at `ca5170fbf99a23ce14630644f892fa9a76039bc2`):

- [`m4-typst-cutover/README.md`](m4-typst-cutover/README.md) — bundle overview and verdict summary
- [`m4-typst-cutover/ORIGINAL_PROPOSAL_SNAPSHOT.md`](m4-typst-cutover/ORIGINAL_PROPOSAL_SNAPSHOT.md) — verbatim snapshot of the original `S1 -> S4` Typst-First proposal
- [`m4-typst-cutover/PLAN_AF_REVIEW.md`](m4-typst-cutover/PLAN_AF_REVIEW.md) — AF/AOD/engineering review (`2` P0, `4` P1, `1` P2 findings)
- [`m4-typst-cutover/CORRECTED_S1_S4_MASTER_PLAN.md`](m4-typst-cutover/CORRECTED_S1_S4_MASTER_PLAN.md) — corrected `S0 -> S4` master roadmap preserving M3 stack discipline, zero-float ontology boundaries, and frozen provenance
- [`m4-typst-cutover/S1_TYPST_CUTOVER_REQUEST_REVISED.md`](m4-typst-cutover/S1_TYPST_CUTOVER_REQUEST_REVISED.md) — bounded `S1a` Typst pilot dispatch request
- [`m4-typst-cutover/FINDINGS_AND_AUDIT.md`](m4-typst-cutover/FINDINGS_AND_AUDIT.md) — verbatim `SHA256.txt`, `FINDINGS.json`, and `TOOLCHAIN_AND_ASSET_AUDIT.json` from the verified R01 bundle


## Current first objective — R02

The owner clarification of 21 November 2026 makes the first M4 objective the plan and stacked PR for a native Typst Main/Manual migration, keeping the existing LaTeX source unchanged as the scientific comparison baseline.

- [Objective 1 Typst plan R02](m4-typst-cutover/OBJECTIVE_1_TYPST_PLAN_R02.md) governs the immediate migration scope, preserved baseline and parity gates.
- [Stacked Typst implementation PR request R02](m4-typst-cutover/STACKED_TYPST_PR_REQUEST_R02.md) specifies the proposed `m4-typst-s1a` child branch and PR targeting `m4`.

The R01 proposal/review files and their embedded manifest remain unchanged historical records. R02 narrows the first dispatch; later figure, engine, model and acceleration work remains in the broader roadmap. No new child PR or implementation result is implied by this planning amendment.
