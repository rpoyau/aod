# M4 Objective 1 — Typst migration with a retained LaTeX baseline

Revision: R02  
Date: 21 November 2026 (Europe/Zurich)  
Status: plan and stacked-PR specification prepared; implementation not started.

## 1. Owner objective

The immediate objective is the migration plan and the stacked PR for changing the publication to Typst. Keep the existing LaTeX source as the comparison baseline and verify that the Typst publication introduces no text changes.

This R02 makes that objective concrete. It governs the first M4 implementation PR. The broader S1b–S4 roadmap remains later work. The original R01 proposal, review, and inner manifest remain unchanged historical records.

## 2. Source and stack binding

| Role | Binding |
| --- | --- |
| Repository | rpoyau/aod |
| Scientific comparison baseline | PR #46, commit 98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3 |
| Baseline tree | b4a667e3809e4a145580686d439811834b936343 |
| Existing plan PR | #47 |
| Existing plan branch | m4 |
| Observed plan head before R02 | e028e12bb534bb347373214e0012d815bf84aee3 |
| Observed plan tree | a8472c6ea9764abb959e4cb63cf59f1f0c5528f2 |
| Proposed implementation branch | m4-typst-s1a |
| Proposed implementation PR base | m4 |
| Parent commit for implementation | Exact m4 head containing this R02 plan amendment; record it at execution |
| Implementation PR number and candidate SHA | Not yet assigned |

The observed plan head differs from the scientific baseline only by seven Markdown files under manual/plans/. Their existing scientific sources are identical.

Apply the plan-only amendment to the existing planning work, then record the resulting m4 SHA before branching. The future child PR compares its implementation against m4, so its diff contains the Typst migration rather than the complete M3 stack.

A pinned additive migration can be developed while the parent stack remains open. If parent scientific content changes, explicitly rebind the baseline, regenerate the affected inventory and repeat the affected comparisons. A branch retarget or merge must not silently replace the scientific baseline.

## 3. First-PR objective and authority

Add native Typst Main and Manual sources and actual rendered PDFs alongside the retained LaTeX publication. Establish that the new publication preserves the baseline's scientific content.

During this stage:

- Existing LaTeX source and bibliography remain byte-identical to the scientific baseline.
- Existing data files and figures remain byte-identical.
- LaTeX remains the authoritative scientific comparison baseline.
- Typst is the candidate publication representation being checked.
- Acceptance of the native port does not automatically delete LaTeX or change the canonical release source.
- Any later promotion of Typst to canonical authoring is recorded separately while retaining the baseline as historical comparison evidence.

“No text changes” includes titles, abstract, body prose, headings, qualifications, footnotes, captions, table contents, bibliography content, mathematical statements, and cross-reference meaning. Preserve the scientific definition order and Main/Manual ownership.

Whitespace, line wrapping, page breaks, and typesetting syntax may differ under the stated layout policy. Those differences must not hide, reorder misleadingly, or alter scientific content.

Keep accepted Tau notation and symbol roles. This migration is not a global replacement of every pi/Pi symbol or an opportunity to alter an equation.

## 4. Included work

1. Inventory the complete active Main and Manual publication graphs.
2. Add a bounded AOD Typst schema/template mapping the actual baseline macros and scientific structures.
3. Port the complete active Main and Manual content.
4. Reuse the existing figure bytes and data records.
5. Implement native Main-to-Manual reference resolution with source identity, target type, numbering/tag and correct PDF destination.
6. Build the untouched LaTeX pair and the candidate Typst pair.
7. Compare the native Typst publication directly with the baseline.
8. Add meaningful parity controls and inspect every newly typeset page.
9. Add the CI and packaging support required to reproduce and distribute the additive Typst sources.
10. Prepare the stacked implementation PR with exact source bindings, build artifacts and coverage.

R01's typ2tex compatibility work remains separately tracked. Any regenerated TeX must be emitted into a separate build tree; it must never overwrite the retained baseline. Its result is supplementary evidence. The native Typst publication must be compared directly against the baseline regardless of the inverse converter's status. Report that compatibility item's status explicitly instead of silently dropping it or treating it as the sole oracle.

## 5. Scope boundary for the first PR

Figure redesign/vectorization, scientific rewriting, new physical examples, D.E.C. engine consolidation or replacement, pp-to-Tau revisions, metrology amendments, removal of scientific holds, and Rust acceleration remain in subsequent work.

Existing examples and limitations still appear in the port and must be preserved. Their presence does not authorize changing their models or interpretations.

This is a document migration. It executes no new simulation and adds no kernel or motif-generation rule.

## 6. Correct source inventory

The bound tree contains 54 TeX files:

| Role | Count |
| --- | ---: |
| Main TeX files outside manual/ | 23 |
| Manual editorial/driver files outside manual/data/ | 20 |
| Active immutable Manual table inputs | 6 |
| Historical TeX snapshots | 5 |

Resolve the active include graph and compare it with actual build records. The Main tree count is an inventory value, not a substitute for that graph.

The six active immutable tables must appear in the Typst Manual:

- manual/data/run_tumble/run_tumble_trace_table.tex
- manual/data/derived/sparc_summary_table.tex
- manual/data/lensing/sparc5_medium_diagnostic_summary_table.tex
- manual/data/lensing/swells_k0_target_tallies_table.tex
- manual/data/lensing/swells_k1_k2_k3_comparison_table.tex
- manual/data/lensing/k4_3d_timeflow_input_gate_table.tex

Their original bytes remain unchanged. Their Typst counterparts or adapters must be checked against the source cells, headers, units, captions and labels.

The five historical snapshots comprise four temporal-anchor source files and one historical-metrology source file. Preserve them as evidence, not as current authoring inputs.

Other baseline inventories:

- 49 image files: 44 PNG and 5 JPG.
- 116 files under manual/data/.
- 166 protected files in the original frozen map, including 49 images, 43 CSVs and 12 TeX files.
- 455 Main labels and 227 Manual labels reported by the bound source audit.

Preserve exact member lists and identities. Counts alone do not establish conservation.

## 7. Candidate layout and engineering changes

Use a canonical document layout within a dedicated Typst root:

    typst/main.typ
    typst/preamble.typ
    typst/sections/
    typst/appendices/
    typst/manual/main.typ
    typst/manual/preamble.typ
    typst/manual/sections/
    typst/manual/appendices/
    typst/lib/

Resolve source counterparts and table adapters in the implementation manifest. Run lint from the declared Typst root or supply an equivalent explicit mapping, so Main, Manual and Appendix source roles are recognized. Identify shared template/library files separately.

The current release builder does not admit a top-level Typst directory, and its expected inventory has no .typ suffix. The first integrated implementation must therefore include the necessary engineering changes explicitly:

- Extend scripts/build_release_bundle.py to package the new authoritative candidate inputs alongside the retained source.
- Extend tests/test_ci_release_builder.py to independently expect the added source surface and verify reconstruction outside Git.
- Update only the corresponding engineering-file digest entries in contracts/scientific/CANONICAL_BINDINGS.json.
- Add a dedicated Typst build/parity workflow and scoped helper scripts.
- Update build instructions for both publication paths.

The two existing frozen engineering files named above are the planned hash amendments. Keep every other original frozen entry unchanged, together with all existing LaTeX, bibliography, data and image bytes. Contract ownership, formulas, scientific dependencies, and scientific values remain unchanged.

Enumerate any further engineering change before applying it and explain why the listed path set is insufficient. Do not hide new source files under an accepted extension to evade the packaging contract.

## 8. Implementation milestones

| ID | Milestone | Exit evidence |
| --- | --- | --- |
| M4-T01 | Freeze the comparison | Baseline and parent SHAs; source hashes; active graph; exact asset and reference inventories |
| M4-T02 | Representative native pilot | Actual Typst build covering difficult math, tagged equation, table, figure, bibliography and Main/Manual references |
| M4-T03 | Complete Main and Manual port | Every active scientific unit accounted for, including six immutable tables and Main appendices D–J |
| M4-T04 | Execute both build paths | Successful baseline XeLaTeX and candidate Typst builds, pinned toolchain and font/package inputs, artifact hashes |
| M4-T05 | Establish publication parity | Direct content/reference comparisons, meaningful negative controls, complete rendered review |
| M4-T06 | Validate integration and delivery | Existing required checks, declared normal/optimized coverage, exact source packaging, fresh non-Git rebuild |
| M4-T07 | Present the stacked PR | Exact head/parent/baseline, focused diff, linked build artifacts, coverage and remaining compatibility status |

## 9. Parity contract

### A. Baseline immutability

Compare all original TeX, bibliography, data and image paths with the pinned baseline. Missing paths, byte changes or replacement by generated content fail this gate.

The narrowly enumerated engineering hash changes are recorded separately. Do not describe the entire original 166-file map as unchanged after updating those two engineering digests.

### B. Scientific content

Compare ordered scientific records from the baseline and native Typst publication:

- Exact prose and qualifications, allowing only declared typography normalization.
- Mathematical structure, grouping, operators, signs, indices and exponents.
- Exact numbers, rational values, units, table headers and cell associations.
- Captions, figure identities and placement relative to their discussion.
- Citation keys and bibliography content.
- Semantic IDs, target types, resolved numbers/tags and actual PDF destinations.
- Definition order, Main/Manual ownership and Provenance/Literature-note roles.

Matching token counts or label counts alone does not pass.

### C. Evaluated and rendered output

Build and inspect the actual Typst Main and Manual. A source parser or regenerated TeX can miss show-rule transformations, hidden text and wrong rendering.

Inspect every newly typeset page during the first full port. Record page coverage and defects, then verify repaired pages. Pagination and line wrapping may differ without changing scientific content.

### D. Negative controls

Require the checker to reject at least:

1. A changed sign, exponent or exact table value.
2. A removed scientific qualification.
3. One omitted active table or source unit.
4. A wrong reference destination or target type.
5. A stale Main registry consumed by Manual.
6. A native-only rendered change that leaves regenerated TeX unchanged, when that compatibility path is present.

These controls test the claimed preservation boundary; they do not implement or test a new physical law.

### E. Actual execution evidence

A command recipe is not a successful build. Record the actual candidate, commands, exits, tools, fonts/packages, logs, artifact hashes and lint coverage. Preserve inherited skips and limitations explicitly. Compare deterministic result payloads separately from timestamps and timings.

All required baseline scientific checks retain their stated meaning. A partial lint report stays partial.

## 10. Acceptance and handoff

The implementation PR may claim native Typst parity only after all required migration gates pass. The handoff includes:

- Candidate and parent commits, retained scientific baseline, and source manifest.
- Both native Typst PDFs and both baseline LaTeX PDFs, or immutable retrievable artifact references with hashes.
- Exact text/math/table/reference comparison results.
- Rendered-review coverage.
- Baseline byte-conservation record.
- Existing test and new parity-test results, including normal/optimized scope and skip reasons.
- Packaging and clean-rebuild evidence.
- Explicit typ2tex compatibility status.
- A statement that canonical authoring/release promotion is separate from this additive migration.

The immediate plan amendment is prepared as a detached three-file Markdown patch. It does not contain a Typst implementation, an actual new child PR, a completed parity result, or a repository mutation.

## Source references

- Plan PR: https://github.com/rpoyau/aod/pull/47
- Scientific baseline PR: https://github.com/rpoyau/aod/pull/46
- Bound source contract: https://github.com/rpoyau/aod/blob/98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3/contracts/scientific/CANONICAL_BINDINGS.json
- Bound release builder: https://github.com/rpoyau/aod/blob/98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3/scripts/build_release_bundle.py
- Bound source inventory: https://github.com/rpoyau/aod/blob/98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3/tests/test_ci_release_builder.py
- R01 source snapshot: https://github.com/rpoyau/aod/tree/e028e12bb534bb347373214e0012d815bf84aee3/manual/plans/m4-typst-cutover

