# AF Derivation Map - Bundle Cycle v40.03r07.3.4

## Setup

The embedded authorized stable payload for the r08 authoring seed is the project-owner GO successor `v40.03r07.3.4`, descended from `bundle-v40.03r07.3.4-go.zip`. The root bundle records are concrete digest-bound instances; records inside `source.zip` carrying `record_scope = source_template` are noncanonical build templates that avoid self-referential hashes.

## Derivation

AF distinguishes the stable payload, ordered delta, candidate payload, review evidence, feedback state, transition authority, and successor identity. AFC supplies the procedural relation: stable plus delta materializes the candidate; review addresses that fixed candidate; feedback returns a bounded correction relation; GO may cross the boundary only when every blocking relation is verified closed and the required authority is present.

## Specialization

The present specialization is release infrastructure. It does not introduce an AOD scientific axiom, infer a Hydrogen transition, or open RD/RCD, SADAR, SI, target, residual, or score lanes.

## Calibration

No scientific or metric calibration occurs. Calibration here means byte-level reconciliation of manifests, schemas, hashes, tests, and deterministic ZIP output.

## Falsification

The construction fails if stable plus delta does not reproduce the candidate, an exact schema accepts an unknown field, a lock omits required release material, a feedback or transition hash chain breaks, an open blocker crosses GO, or a successor ZIP is not deterministic.

## Provenance

Canonical paths: `cycle/CYCLE_POLICY.json`, `cycle/CYCLE_STATE.json`, `cycle/FEEDBACK_LEDGER.csv`, `cycle/TRANSITION_LEDGER.jsonl`, `governance/AF_PROTOCOL_PROFILE.json`, `governance/AFC_PROCEDURAL_DYNAMICS.json`, `governance/GENERAL_MECHANICS_STYLE_PROFILE.json`, `governance/UPSTREAM_RELEASE_POLICY.json`, and `delta/SOURCE_TREE_DELTA_MANIFEST.csv`.

## Literature note

AF, AFC, and General Mechanics bootstrap artifacts remain embedded and hash-locked as explicit non-latest fallbacks. Every AUTHORING cycle attempts the GitHub latest-release refresh; a successful result is frozen for that candidate, while an unavailable refresh does not block REVIEW or GO.


## Upstream release refresh semantics

Latest release endpoints are resolved at AUTHORING start. The resolved snapshot is candidate-scoped; an explicit unavailable-refresh fallback is nonblocking and does not claim current-latest status.
