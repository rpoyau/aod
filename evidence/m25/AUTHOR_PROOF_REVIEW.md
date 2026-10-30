# M2.5 proof-author review

Reviewer: Codex subagent `/root/proof_repairs`, author of these repairs. This is author self-review, not independent review.

## Scope

Edited only `sections/06_wave_state_relational_time.tex`, `sections/08_awareness_learning_mindfulness.tex`, and short downstream clarifications in `manual/sections/00_awareness_fixtures.tex` and `manual/sections/00_dec_ledger.tex`. Original bytes are preserved under `/tmp/m25-proof-original/` with relative paths. M25-03-only intermediate source and patch are `/tmp/m25-notation-awareness.tex` and `/tmp/m25-notation.patch`.

## Hinge implication

The admitted continuation family is finite and weights remain nonnegative rational numbers. At the entered mandatory hinge, `A_0` names the existing additional-dwell family; `A_+` selects positive weights without defining a combined H1/fibre kernel. Structural saturation retains its original equation. Its structural branch-only implication is explicitly conditional on that equation. Weighted saturation is now the equivalence between zero dwell-weight sum and empty positive-weight dwell support.

The proof uses finiteness and nonnegativity: a finite nonnegative sum vanishes exactly when every summand vanishes. A weight-zero admitted dwell with branch weights one and two disproves the removed stronger structural inference. Strict positivity of every admitted dwell is stated as an additional hypothesis needed to recover structural equivalence. Empty structural branch support and nonempty all-zero-weight support remain distinct; no zero-total normalization is supplied. Branch-role entropy requires positive branch mass, is bounded by log_3(2), and is zero for one populated role. Atomic H1 kernel, mandatory hinge, zero-base-traversal fibre dwell, and closure law are unchanged.

## Retained relation and intervention

The source now explicitly names retained tuple `R_e` with immutable event identity, source, target, boundary/window, scale/lineage, commitment, value and provenance. Family notation is consistently `R_k`; factored state is consistently `S_k^+`. General record operativity uses the corresponding removal `S_k^{+,-e}` and retains the strictly-later finite-horizon criterion.

At fixed target `j`, each retained relation has `j_e=j` and compatible boundary/window and scale. The source subset is `R_{k,i}={R_e in R_k : i_e=i}`; intervention is `(X_k,M_k^C,R_k minus R_{k,i})`. At most one retained relation per source makes this the existing single-relation removal. Multiple records per source require a separate grouped intervention; cancellation prevents equating grouped and individual effects. The H=1 operative set compares `S_k^+` and `S_k^{+,-i}` under the same world, law, outcome and future inputs.

Present coordinates, closure memory, admitted witnesses, pressure, boundary and addressed random inputs stay fixed. Removal affects a comparison state, without erasing historical closure trace or rewriting events. Restoration includes exact value and provenance. A missing record, a retained zero and cancelling distinct-source nonzero records remain distinct. Outcome excludes retention itself, role labels and intervention verdicts. Availability at the next cut is distinguished from longer-horizon operativity. Operativity implies neither admission nor positive shedding surplus. Existing evaluated cancellation example and engine expectations remain unchanged.

## Validation performed here

- `git diff --check` passed.
- Direct label-set comparison found no removed label and exactly two additions: `eq:hinge-positive-support` and `eq:operative-source-removal`.
- Scientific audit reaches the expected frozen formula binding rejection at `eq:awareness-state-factorization` before successor bindings are updated; this is not a passing audit.
- No engine, fixture, schema, test or audit code was edited by this agent.
- Full tests, successor binding review, clean paired builds and visual checks are performed by the coordinating agent and are not claimed by this record.
