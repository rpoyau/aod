# M2.5 repair evidence — PR41 follow-up

The original three commits implement M25-01 through M25-11 on branch `M2.5` against main `0f18cf5da316f27050c3dffd3838a39ccf13fca4`. One narrow follow-up resolves review findings F1/F2 and corrects the evidence. No merge, release metadata change or M3 implementation is included.

The reviewed head `ec085872719179ac2fa214365db6bde4c81e0aa5` failed with 558 passing tests and one report-schema failure (`reviewed-head-tests.txt`). Its recorded 559-pass result came from a local run before the raw report was persisted and did not validate that final tree. That claim is superseded by the successor's final `tests.txt` and exact-head CI/delivery records.

F1 gives `awareness.json` schema `aod.fixture-run-report.v1`, the exact runner path, and nested `runner_output`. The original raw result, engine hash and all 47 outcomes are preserved. Three new checks validate the full output against a fresh unchanged runner execution and reject a stale hash or altered result. The recursive active-binding validator and its exact specification inventory are unchanged.

F2 declares in Figure 8's caption that the schematic lag notation denotes the existing signed lag accessor on the declared boundary/window; the bars take its magnitude. The PNG bytes, placement, mathematical displays and semantic labels are unchanged. `SYMBOL_INVENTORY.json` now accounts separately for the embedded image occurrence. Clean Main/Manual builds contain 70/76 pages; only Main physical pages 35–36 change visually, and both plus the preceding page have been inspected.

The substantive hinge and source-removal proofs, engines, fixture inputs/expected outputs, historical M2 schemas and protected bindings are unchanged by this follow-up. The 83 closure/wave and 47 awareness results match the reviewed head exactly. `BINDING_SUCCESSOR.json` and its original baseline remain byte-identical.

`SOURCE_BINDINGS.json` preserves the original five local authoring-skill records. `FOLLOWUP_SKILL_REVIEW.json` separately binds the supplied AF/AFC/AOD/GM archive, four entrypoints, 59 files and reconstructed tree, identifies the reviewer and distinguishes fresh checks from prior-reviewer attestation. It makes no claim about a later private-repository revision.

The successor full suite passes all 562 tests, including the original 17 M2.5 controls and three report-schema checks. All JSON run reports and source changes were present before that run. After refreshing text evidence, the recursive active-binding test and report regressions are rerun on the assembled candidate. Final commit/tree, successful CI stages, patch replay, source/PDF hashes and manifests are recorded in the detached R02 delivery after commit. `ACCEPTANCE.csv` records the prior failure and current gates; PR acceptance remains separate from agent review, and M3 WP0 must bind the subsequently accepted head.
