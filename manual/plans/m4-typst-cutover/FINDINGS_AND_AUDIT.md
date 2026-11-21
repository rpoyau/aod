# Machine-Readable Findings, Asset Audit, and Bundle Manifest

This file preserves verbatim the non-Markdown records (`FINDINGS.json`, `TOOLCHAIN_AND_ASSET_AUDIT.json`, and `SHA256.txt`) from the verified review bundle `AOD_TYPST_S1_S4_PLAN_AF_REVIEW_BUNDLE_R01.zip` (`16,880` B, outer `SHA-256: 080dfe7d86628f49465ce6493e502798cab9ec16138869cc4d75adb477b5ab6b`), wrapped in Markdown so temporary planning files under `manual/plans/` stay strictly compliant with the frozen `SOURCE_DIRECTORY_TYPES["manual"]` contract in `tests/test_ci_release_builder.py` without modifying any protected file.

## `SHA256.txt` (inner bundle manifest)

```text
de33162e06fa1504b3d4f1da21003183f51f55e1d899bdee21ebb4492df07717  CORRECTED_S1_S4_MASTER_PLAN.md
12bf9d123d1b00d24c964afcce650b572cfbdfdabb41e584f72752ea774eb901  FINDINGS.json
62f0410ddfdbdc8618868eabb564bcfff41a2671a2391f1190220db1190472f6  ORIGINAL_PROPOSAL_SNAPSHOT.md
5b4c0d53f97474d8e11cb0be23ab614740bf1e804dad53f766dd40606170af90  PLAN_AF_REVIEW.md
e8e88071549d18335744c5af3f17040d2aba80e22c4320241c159f07ec26e079  README.md
b8b9a9cc8ed2598c9172e4fd107ab8d574169e8fce0758d0e33b6e0a5a73c1e0  S1_TYPST_CUTOVER_REQUEST_REVISED.md
c9fab463e2ed907b14ba128bf96aa7194444b35953446234c27ad13870425887  TOOLCHAIN_AND_ASSET_AUDIT.json
```

## `FINDINGS.json`

```json
{
  "schema": "aod.typst-cutover.plan-review-findings.v1",
  "verdict": "REVISE_PLAN_BEFORE_EXECUTION",
  "overall_assessment": "The core engineering instinct (separating pure format migration from content changes) is strong, but the pasted S1->S4 draft has 7 concrete scientific, governance, sequencing, and toolchain defects that must be corrected before dispatching Stage 1.",
  "findings": [
    {
      "id": "R01",
      "priority": "P0",
      "category": "Scientific governance & experimental quarantine (S2)",
      "location": "Stage 2 (S2) scope",
      "defect": "Proposes importing experimental aod-dec and v3-v5 machinery (2500-denominator (650,703,1147)/2500 -> (19/50, 31/50)|_Exo adapter, 3:4:6 wall tunnelling, Leprechaun 5-shell vs LHC ablation, 1776.86 MeV) directly into canonical rpoyau/aod Manual.",
      "smallest_missing_premise": "Independent AF authentication of any experimental aod-dec model and an explicit governance authorization amending canonical Manual scope; in current M3 contracts, aod-dec code/traces/results are strictly excluded and 19/50 is bounded to a declared 90-tick open finite-model fixture without certifying native reclosure or Exo identity.",
      "correction": "Quarantine experimental pp->Tau cavity/funnel prototypes outside canonical M3 until separately authenticated under an explicit AF review gate; never silently import aod-dec into manual/."
    },
    {
      "id": "R02",
      "priority": "P0",
      "category": "Factual / AF provenance contradiction (S2)",
      "location": "Stage 2 (S2): '1:2:10 0.45 -> 23/50 float-truncation fix'",
      "defect": "Mislabels the exact rational difference between manual/data/derived/tau_ring_diagnostic.csv (9/20 = 0.45) and manual/data/tau/aod_tau_fractal_ring_summary.csv (~23/50 = 0.46) as a 'float-truncation fix'.",
      "smallest_missing_premise": "Authenticated upstream generator code proving why the two frozen CSVs differ by 1/100; verified P2-13 audits establish that this is a genuine 1/100 rational discrepancy whose originating generator is UNRESOLVED_NOT_AUTHENTICATED_IN_REPO.",
      "correction": "Preserve both frozen CSVs and their explicit unresolved-provenance status until an authenticated historical generator is recovered; never 'fix' an unauthenticated discrepancy by speculation."
    },
    {
      "id": "R03",
      "priority": "P1",
      "category": "Repository state & stack ordering drift",
      "location": "Stage 4 (S4) and dispatch timing ('right after Phase 0 clears')",
      "defect": "Assumes Phase 0 is still active and places Main M3 Compaction last (S4), ignoring that Phase 0, Phase 1 (PR #45 at 42ab900f), and Phase 2 (PR #46 at 98ddfa0e, CI 1342 passed) are already implemented and stacked on PR #43 (m3).",
      "smallest_missing_premise": "Explicit immutable Git base pin for Stage 1 (either post-merge main after PR #43/#45/#46 land, or an explicitly pinned read-only snapshot of 98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3).",
      "correction": "Finish G2 sign-off on PR #46 first; re-sequence M3 completion ahead of the Typst cutover and pin S1 to an explicit immutable commit SHA."
    },
    {
      "id": "R04",
      "priority": "P1",
      "category": "Frozen contract conflict in S1 figure replacement",
      "location": "Stage 1 (S1): replacing legacy figures while claiming 'zero-drift drop-in replacement'",
      "defect": "contracts/scientific/CANONICAL_BINDINGS.json freezes 54 figure files (plus 12 TeX files and 55 manual/data files; 166 total frozen_sha256 digests). Replacing legacy raster figures in S1 contradicts 'zero drift' and fails scripts/audit_scientific_sources.py unless contracts are amended.",
      "smallest_missing_premise": "Separation of pure markup migration (S1a: keep existing frozen figures unchanged so zero contract hashes break) from figure vectorization (S1b: explicit additive vector figure lane + contract amendment).",
      "correction": "Split S1 into S1a (pure verbatim .tex -> .typ + deterministic typ2tex keeping all 54 frozen figures byte-identical) and S1b (opt-in native Typst vector figure upgrades with explicit visual & contract sign-off)."
    },
    {
      "id": "R05",
      "priority": "P1",
      "category": "False figure provenance premise (S1)",
      "location": "Stage 1 (S1) Rule 4: 'Figures 1-32 ... reading directly from existing manual/data/ CSV/JSON files'",
      "defect": "Actual repo has 28 unique active \\includegraphics targets in active Manual TeX (plus 6 in Main, and 11 frozen historical .tex files in manual/data/ that must never be touched). Many active figures are conceptual topological diagrams or unauthenticated derived plots with no CSV/JSON backing in manual/data/.",
      "smallest_missing_premise": "Per-figure classification manifest distinguishing (a) data-backed plots with authenticated CSV/JSON generators, (b) conceptual schematics, and (c) plots with unresolved generator provenance.",
      "correction": "Require a figure-classification manifest before vectorizing any figure in S1b; never fabricate data backing for conceptual or unauthenticated figures."
    },
    {
      "id": "R06",
      "priority": "P1",
      "category": "Environment & toolchain gap (S1)",
      "location": "Stage 1 (S1) build deliverables ('typst compile', CeTZ/Fletcher, pdflatex/xelatex)",
      "defect": "In this VM, typst, xelatex, and latexmk are NOT installed (only pdflatex is present, whereas CI requires latexmk -xelatex), and external Typst Universe packages (@preview/cetz, @preview/fletcher) cannot be assumed downloadable inside an offline/proxy-restricted sandbox.",
      "smallest_missing_premise": "Installed user-space typst binary, vendored local package cache (or zero-dependency native Typst drawing primitives), and hosted CI (or local XeLaTeX) verification for round-tripped LaTeX.",
      "correction": "Declare explicit toolchain provisioning in S1a/S1b: verify or install user-space typst (or run in CI), avoid unvendored remote Typst packages, and verify round-tripped LaTeX against .github/workflows/build.yml (latexmk -xelatex) + scripts/audit_scientific_sources.py."
    },
    {
      "id": "R07",
      "priority": "P2",
      "category": "Test/macro coupling & packaging discipline (S1)",
      "location": "Stage 1 (S1) deliverables & parity claims",
      "defect": "19 of 51 pytest modules directly inspect .tex syntax, xr-hyper cross-file links (../main.aux, ../main.fls), and custom macros (\\mainequation, \\aodprovenance, \\AO, \\SADARop). Also, embedding full compiled PDFs inside a review ZIP violates compact Git/CI-bound bundle discipline (<100 entries, no large binary PDFs/snapshots when Git/CI supplies them), and Google Drive is not connected in this VM.",
      "smallest_missing_premise": "Macro-faithful typ2tex contract passing all 19 TeX-inspecting pytest modules and scripts/audit_scientific_sources.py, plus compact Git-bound bundle packaging.",
      "correction": "Make 'all 1342+ pytest tests + audit_scientific_sources.py pass on typ2tex output' an explicit S1a gate, keep review bundles compact and Git/CI-bound, and note local vs. Drive delivery cleanly."
    }
  ]
}
```

## `TOOLCHAIN_AND_ASSET_AUDIT.json`

```json
{
  "schema": "aod.typst-cutover.plan-audit.v1",
  "audited_repo": "rpoyau/aod",
  "audited_branch": "m3-manual-si-alignment",
  "audited_head": "98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3",
  "audited_tree": "b4a667e3809e4a145580686d439811834b936343",
  "open_m3_stack": {
    "pr_43": {"branch": "m3", "base": "main", "commit": "dc1a434c8fc2b7b958e44d7da63277c7856a8d67"},
    "pr_45": {"branch": "m3-ontology-compaction", "base": "m3", "commit": "42ab900fcdd9478a7dfa5f5fac4fa318ea359834"},
    "pr_46": {"branch": "m3-manual-si-alignment", "base": "m3-ontology-compaction", "commit": "98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3", "hosted_ci_run": 44913132983, "pytest_passed": 1342, "pytest_skipped": 1}
  },
  "local_vm_toolchain": {
    "typst": "NOT_INSTALLED",
    "xelatex": "NOT_INSTALLED",
    "latexmk": "NOT_INSTALLED",
    "pdflatex": "/usr/bin/pdflatex",
    "pdfinfo": "/usr/bin/pdfinfo",
    "pdftotext": "/usr/bin/pdftotext",
    "cargo": "/usr/local/bin/cargo",
    "python3": "/usr/bin/python3",
    "ci_tex_engine": "latexmk -xelatex (from .github/workflows/build.yml)",
    "gdrive_plugin_connected": false,
    "github_plugin_connected": true
  },
  "repository_surface_counts": {
    "total_tracked_files": 320,
    "active_main_tex_files": 23,
    "active_manual_tex_files": 20,
    "frozen_historical_tex_files_in_manual_data": 11,
    "total_tracked_tex_files": 54,
    "active_main_includegraphics": 6,
    "active_manual_includegraphics": 28,
    "unique_manual_graphics_targets": 28,
    "total_tracked_figure_files": 49,
    "main_labels": 455,
    "manual_labels": 227,
    "pytest_modules_total": 51,
    "pytest_modules_scanning_tex_directly": 19,
    "canonical_bindings_frozen_sha256_total": 166,
    "canonical_bindings_frozen_figures": 54,
    "canonical_bindings_frozen_tex": 12,
    "canonical_bindings_frozen_manual_data": 55
  },
  "aod_lint_typst_readiness": {
    "repository": "rpoyau/aod-lint",
    "typst_source_files_present": ["digest.rs", "mod.rs", "typst_ast.rs", "main.rs"]
  }
}
```
