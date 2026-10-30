# M2.5 scientific cross-agent review

Reviewer: `/root/presentation_repairs` (Codex child agent).
Review type: separate cross-agent review of the proof author's work. This is not external human independent approval. The reviewer authored the presentation changes in the same milestone; the scientific proof/intervention changes were authored by another agent.

## Reviewed bindings

- Notation commit: `7976cb4f4f4a9082e90f8f779ccae3b304bf854f`.
- Proof/intervention commit: `cfaaafcd0d30d9c7e7410b7a64b69b9d293b20b7`.
- Also inspected the current working-tree refinements explicitly requiring `j_e=j` and compatible boundary/window/scale for all retained records, and excluding intervention verdicts from the outcome.
- Baseline: `0f18cf5da316f27050c3dffd3838a39ccf13fca4`.
- Contract: supplied M2.5 R01 plan, Sections 3–4 and acceptance requirements. The user's explicit execution request controls authorization.

## Disposition

No blocking scientific findings in the reviewed candidate. The two proof repairs implement the requested hypotheses without changing the response law, atomic kernel, closure admission or fixture expectations. This review does not certify the repository suite, final PDF layout, artifact hashes or PR acceptance; those require their separate evidence.

## Hinge-saturation reasoning

The admitted domain is explicitly finite, post-hinge and lawful. The preceding domain split distinguishes H1 atomic traversals from zero-base-traversal hinge-fibre continuations; the earlier hinge grammar retains mandatory `0_H` even at zero additional dwell. The new aliases do not normalize their union or redefine the atomic kernel.

The structural result now explicitly depends on `Adm^0 = empty`. Its branch-only conclusion follows from the remaining roles in the already-entered hinge grammar. The weighted result is exactly `sum(A_0) w = 0 iff A_0 intersect A_+ = empty`: nonnegativity proves both implications, while finiteness makes the displayed ordinary finite sum well-defined. The prose correctly avoids inferring structural emptiness.

The admitted dwell with weight zero and branch weights one and two is a valid exact counterexample to the old inference. Strict positivity of each admitted dwell is identified as an additional hypothesis, not silently added. Empty structural branch support and nonempty/all-zero support provide no branch normalization. Additional dwell retains zero base traversals and the mandatory hinge remains present.

The entropy bound is conditional on a declared normalized branch-role distribution with positive total branch mass. For `h(z)=-z log_3 z-(1-z)log_3(1-z)`, the interior derivative vanishes only at 1/2, the second derivative is negative, and the endpoints have value zero by continuity. Thus the maximum is `log_3 2`, independent of the number of rows realizing each role. No physical/channel-capacity bound is inferred.

As a supplementary finite diagnostic, all dwell weight families of lengths zero through five over `{0,1/2,1,2}` were enumerated: 1365 families satisfy the exact equivalence. Negative dwell weights `(1,-1)` give zero sum with nonempty positive support, confirming the need for the stated nonnegative domain. This finite enumeration supports the review but is not a replacement for the general argument.

## Retained-source intervention reasoning

The notation chain now explicitly binds individual `R_e` tuples, event identity, source and target, boundary/window, scale/lineage, committed cut, rational value and provenance; `R_k` is the family. All operative equations use the factored `S_k^+` consistently.

At fixed target and compatible scope, `R_{k,i}` selects exactly records whose source is `i`; `S_k^{+,-i}` changes only that retained coordinate. The one-record-per-source restriction makes removal coincide with the previously defined record-level intervention. The unchanged `validate_state()` rejects duplicate sources, and unchanged `operative()` removes exactly by the same source identity. The working-tree target/scope clarification prevents a reader from extending source grouping across unrelated targets.

The setup binds identical present coordinates, immutable closure memory, admitted world, response law, exogenous future and addressed randomness. The surrounding validity condition and invalid-retention exclusions remain active. Immutable commitments validate provenance but cannot reconstruct removed values; removal acts on a comparison copy and does not rewrite closure history. Restoration binds exact value and provenance.

The `H=1` source specialization is distinct from general record-level finite-horizon operativity. Strictly-later outcomes exclude retained coordinates, role labels and (in the current refinement) intervention verdicts. Unavailable sources can be inactive for the next transition yet have later effects. The criterion supplies no new closure or shedding premise.

The Manual's unchanged cancellation witness retains distinct source identities: total current zero for contributions `+1,-1`, but removing either produces respectively `-1,+1`. Absent retention, retained zero and cancelling nonzero records remain different states. The existing Main/Manual split is preserved: Main supplies the intervention definition and hypotheses; Manual supplies executable rational examples and controls.

## Preservation checks and limits

Read the full wave-state and awareness sections, hinge grammar and common-record definitions in the AFC section, the surrounding Manual setup/cancellation controls, and `validate_retention`, `validate_state`, `transition`, `outcome`, `matched`, `operative` in the executable model. A diff against the baseline confirms no changes to either native closure/wave or awareness engine. No code was altered during this review.

Current reviewed source SHA-256 bindings:

- `sections/06_wave_state_relational_time.tex`: `bbd265de629de74ae43be75ff5146406b5dda80c380bf02507725a98d233404d`
- `sections/08_awareness_learning_mindfulness.tex`: `310b4860c1710b8191725d9c40ff1fc05bd45a7ed818f0891e1fbd8fa58feae1`
- `manual/sections/00_awareness_fixtures.tex`: `7baab852287eb63efe635451fc00a92cbf5cba76cbddba19bec8d554fe4c3679`
- `manual/sections/00_dec_ledger.tex`: `99fac3efb652730f9240e35eb0a7c55779fa15630b16d2440cbd462e7c9479dc`
