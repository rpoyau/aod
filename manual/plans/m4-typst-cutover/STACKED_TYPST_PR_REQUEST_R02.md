# Stacked Typst implementation PR — request R02

Status: prepared specification and PR description; no child PR has been created by this request.

## Stack

- Existing planning PR: rpoyau/aod#47, branch m4.
- Observed m4 head before the plan amendment: e028e12bb534bb347373214e0012d815bf84aee3.
- First apply or incorporate the R02 plan-only amendment, then record the resulting exact m4 head.
- Create the implementation branch m4-typst-s1a from that recorded parent.
- Target the child draft PR at m4.
- Retain 98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3 as the scientific comparison baseline unless an explicit rebind is recorded.
- Populate the actual candidate commit and PR URL after execution; do not invent them.

## Implementation objective

Execute OBJECTIVE_1_TYPST_PLAN_R02.md. Add the native Typst Main and Manual alongside the unchanged LaTeX publication. Keep original TeX, bibliographies, data and figures byte-identical. Verify native rendered content directly against that retained baseline.

Include the narrow engineering changes needed for Typst CI and reproducible source packaging. Preserve the scientific contract while updating only the explicitly identified engineering hash entries.

## Suggested title

M4 S1a: native Typst Main and Manual with unchanged LaTeX parity baseline

## PR description to use after populating execution evidence

### Why

M4 introduces a native Typst publication while retaining the existing LaTeX source as the scientific comparison baseline. The migration must preserve all prose, mathematics, data, figures and reference meaning.

### Changes

- Adds native Typst Main and Manual sources and shared AOD presentation helpers.
- Reuses existing figure and data bytes, including the six active immutable Manual table inputs.
- Adds direct native-publication parity checks and resolved Main/Manual references.
- Adds the CI and source-packaging support needed to reproduce both formats.
- Retains existing LaTeX and scientific interpretations.

### Source bindings

- Scientific baseline: 98ddfa0ebb38293adfa99c8c11da5a15cdd9eea3.
- Parent m4 commit: TO_BE_FILLED_FROM_EXECUTION.
- Candidate head and tree: TO_BE_FILLED_FROM_EXECUTION.
- Actual build/artifact URLs and hashes: TO_BE_FILLED_FROM_EXECUTION.

### Acceptance evidence

- [ ] Original TeX, bibliography, data and image bytes preserved.
- [ ] Complete active-source coverage, including all six immutable table inputs.
- [ ] Actual native Main and Manual builds pass.
- [ ] Retained LaTeX Main and Manual builds pass.
- [ ] Direct ordered prose/math/table/caption/citation/reference parity passes.
- [ ] Wrong-value, hidden-qualification, missing-input and wrong-reference controls fail as expected.
- [ ] All newly typeset pages reviewed and repairs checked.
- [ ] Required existing scientific checks preserve their stated behavior.
- [ ] Lint source-root and feature coverage reported explicitly.
- [ ] Engineering digest amendments limited to the named files.
- [ ] Source archive reconstructs both publication paths outside Git.
- [ ] R01 typ2tex compatibility status reported separately.
- [ ] Canonical source/release promotion has not been inferred from native-port acceptance.

### Scope

This PR performs the publication migration. Figure redesign, engine changes, new physical examples, SI-model amendments and Rust acceleration remain in later milestones.

## Publication discipline

Keep the PR draft while required migration evidence is incomplete. A proposed command or prepared checklist is not a passing result. Record actual results and retained limitations before changing the draft's status. This request does not authorize an unreviewed scientific edit or imply merge approval.

