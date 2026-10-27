# M2.5 conservation-audit review

Reviewer: Codex subagent `/root/proof_repairs`. This agent authored the M2.5 proof prose but did not author or modify the reviewed audit implementation or successor evidence. This is a separate-agent review of those implementation changes, not an external scientific review. The reviewer authored only the added `tests/test_m25_conservation.py` mutation controls.

## Reviewed bindings

- Audit source SHA-256: `90c0db366466f0b18e4e3834fea1eea51bd27ca865bdc5103738cfd9333e86a5`.
- Successor SHA-256: `1d2a3b1926c1f581b8db402762d67127ae23ae351842ee6540d2a86485833abb`.
- Baseline binding SHA-256: `3d460c81201ba4a3793269ce2ba2a5f484f6dbb020e39533167aa27e4e73430b`.
- Bound original commit: `0f18cf5da316f27050c3dffd3838a39ccf13fca4`.

## Findings and disposition

No remaining actionable audit defect identified in the reviewed version. The M2.5 guard pins the exact baseline and successor JSON bytes. It reconstructs the candidate contract by advancing exactly five canonical formula bodies and requires equality of every remaining contract field. The successor also binds three changed formulas outside the historical canonical list and two new formulas, including their active document and file owner. Two narrowly specified uniqueness patterns consume the equivalent state notation. Historical M2 schemas, engine bytes, fixture rows and original frozen-file hash inventory remain intact.

The frozen source-test successor verifies its full new bytes before replacing them with its stored old bytes for the historical conservation check. Stored old contents of both changed tests match `git show` at the bound original commit exactly. Both new test contents match current files and their stated SHA-256 values. `test_pr39_format_style.py` was not historically frozen; its recorded successor preserves the heading/anchor check, and adds exactly the three new Main-equation reference consumers rather than weakening the reference-inventory comparison. The baseline JSON file is byte-for-byte identical to the bound original commit.

The initial placement of exact-contract validation before historical owner/dependency checks changed the failure diagnostics of existing hostile tests. The coordinating agent moved the successor call after those existing checks and before signature processing. The exact-contract invariant remains mandatory for successful completion. Existing diagnostic specificity is preserved without widening an exception.

## Mutation evidence

`tests/test_m25_conservation.py` copies the tracked source inventory plus pending M2.5 JSON/test sources, excludes generated builds, and first verifies that the unchanged copy passes. Each mutation then runs the actual scientific-source audit on its disposable copy:

1. An unrelated odd-support-index formula changes from `2 ell + 1` to `2 ell + 3`: canonical mathematical statement rejected.
2. An unrelated byte is appended to the native closure/wave engine: frozen-file check rejects it.
3. An unrelated byte is appended to an unchanged frozen test: frozen-file check rejects it.
4. An unrelated byte is appended to the reviewed frozen test successor: exact M2.5 test-byte check rejects it.
5. A newline is appended to baseline JSON: baseline byte pin rejects it.
6. The native engine is removed from the contract's frozen-hash inventory: exact contract check rejects it.
7. The successor attempts to change its own approved operative-self formula: successor byte pin rejects it.

The eighth test verifies the positive successor inventory, exactly five changed canonical formulas, unchanged nonformula fields, and full old/new test-byte hashes.

Validation: all 8 new conservation tests passed. Existing ontology and active-source controls passed (21 tests). A combined final check also covers concept-ownership diagnostics and format/style integration; its exact result is appended below when complete. Full repository and publication-build results belong to the coordinating agent's separate evidence.

Final combined command: `/tmp/m25-venv/bin/python -m pytest -q tests/test_m25_conservation.py tests/test_main_manual_concept_ownership.py tests/test_pr39_format_style.py` — **54 passed in 53.14s**. This includes the O05 backwards-dependency and wrong-document-owner diagnostics after the audit-order repair, plus the three new typed Main-reference consumers. `git diff --check` passed.
