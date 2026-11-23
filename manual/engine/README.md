# AOD Stage 2 Audited Zero-Float Reference Engine (`manual/engine/`)

This package implements the Stage 2 (`S2`) audited zero-float reference verification
engine for Alpha Omega Dynamics (`rpoyau/aod`), stacked directly on the accepted
Stage 1b baseline (`cea71a76f26c08b603866e746867b3982da6c88e`).

## Architecture & Three-Tier Coverage

`manual/engine/registry.py` maintains two separately auditable sets:
1. **16 named execution sectors** (`9` Tier 1 + `6` Tier 2 + `1` Tier 3), failing
   closed on any omitted, duplicated, unknown, empty, or vacuous check.
2. **All 17 `manual/data/` subdirectories (`116` regular files) plus root
   `wavelet_shedding_simulation.csv` and `cycle_shedding_summary.tex`**, audited
   by `verify_data_coverage()`.

| Tier | Sectors | Mechanism |
|---|---|---|
| **Tier 1 (`tier1_canonical_adapter`)** | `native_closure_wave`, `awareness`, `cell_measures`, `mapping_error`, `temporal_observation`, `temporal_metrology`, `experimental_comparison`, `temporal_anchor`, `wavelet_si_alignment` | Isolated read-only subprocess execution (`-B`, propagated `-O`, `PYTHONDONTWRITEBYTECODE=1`, pre/post SHA-256 immutability, structured non-vacuous predicates, absolute-path stripping). Never imports `manual.scripts.*` directly and never imports Group-B legacy scripts. |
| **Tier 2 (`tier2_exact_data_verifier`)** | `dec_ledger`, `higgs_trace`, `phase_delta3_3d`, `cycle_shedding`, `lensing_tallies`, `sparc_five_galaxy` | Pure zero-float `int`/`Fraction` data verifiers checking pinned `frozen_sha256` digests in `contracts/scientific/CANONICAL_BINDINGS.json` and explicit column roles (`exact_input`, `exact_result`, `rounded_display`, `retained_legacy_float_record`). |
| **Tier 3 (`tier3_provenance_guard`)** | `provenance_quarantine` | Pure zero-float guard verifying all 9 frozen SPARC/Tau provenance files, verbatim Tau sub-table equality, and exact `9/20` vs `~23/50` non-conflation (`1/100` rational difference). |

**Cross-`zlib` `temporal_anchor` verification:** `temporal_anchor` executes
`manual/scripts/aod_temporal_anchor.py --check-data` directly whenever host
`zlib` reproduces the committed `zlib 1.2.13` DEFLATE bitstream of
`cases/baseline.json.gz`. On hosts whose `zlib` implementation (such as
`zlib-ng` on Ubuntu 26.04) produces a different lossless DEFLATE stream for the
same canonical JSON, the adapter runs unmodified `aod_temporal_anchor.products()`
in an isolated `-B [-O]` child subprocess, enforcing exact raw byte equality on
`inputs.json`/`report.json`, exact decompressed canonical JSON byte equality on
all `cases/*.json.gz`, exact directory inventory, and unchanged bound-file
SHA-256 digests — preserving immutable `aod_temporal_anchor.py` and the
`code_sha256` pinned in `manual/data/temporal_anchor/inputs.json`.

## Zero-Float Policy & Inherited Transitive Scope

- **Inside `manual/engine/`:** `--check-zero-float` enforces an AST audit across all
  `manual/engine/**/*.py` files rejecting `float`/`complex` literals, `float()` /
  `complex()` / `eval()` / `exec()` calls, bare `assert` statements, forbidden
  float/experimental module imports (`math`, `cmath`, `numpy`, `scipy`, `pandas`,
  `matplotlib`, `decimal`, forbidden legacy experimental module namespaces, and
  `manual.scripts.*`). `sympy` is strictly allowlisted only inside
  `manual/engine/vectors.py:_verify_sympy_z4_dft` for `SD-001` and `SD-002`.
- **Runtime payload guard:** `require_no_floats()` and `loads_zero_float()` reject
  any Python or JSON floating-point value in reports and golden vectors.
- **Typed public input boundary:** All validators in `manual/engine/numeric.py`
  enforce explicit `TypeError`/`ValueError` checks (active under both `python3` and
  `python3 -O`), rejecting `bool`-as-`int`, `float`, `NaN`/`Inf`, and malformed tokens.
- **Transitive inherited roles outside `manual/engine/`:** Preserved unchanged and
  declared transparently: `aod_mapping_error.py` uses 50-digit `Decimal` for
  historical square-root presentation; `aod_native_closure_wave.py` uses exact
  `sympy` for finite Fourier characters; `aod_manual_wavelet_si_alignment.py`
  retains one deliberate negative-control literal outside the engine.

## Orthogonal Status Reporting (`aod.manual.engine.report.v1`)

Check execution outcomes (`outcomes_summary`: `PASS` / `FAIL`) are strictly
separated from scientific claim status (`scientific_status_summary`:
`AUTHENTICATED_EXACT`, `CONFORMANT_DECLARED_FIXTURE`, `RETAINED_DATA_CONFORMANT`,
`UNRESOLVED_PROVENANCE_QUARANTINED`). Passing `provenance_quarantine` records
`check_outcome: "PASS"` alongside `scientific_status: "UNRESOLVED_PROVENANCE_QUARANTINED"`
and never implies authentication of the unauthenticated SPARC carried controls or
Tau fractal-ring generator.

Canonical reports are serialized deterministically (`sort_keys=True`, UTF-8, LF)
with zero timestamps, durations, temp paths, absolute paths, or raw subprocess
streams, ensuring byte-identical output between normal and `-O` Python across
checkout paths.

## S4 Cross-Language Golden Vectors (`manual/engine/vectors/*.jsonl`)

- `manual/engine/vectors/rational_core.jsonl` — 24 independently-oracled pure
  integer/rational vectors (`RC-001`..`RC-024`) targeting `crates/aod-core/`.
- `manual/engine/vectors/symbolic_and_display.jsonl` — 6 separately scoped exact
  symbolic (`sympy`/cyclotomic) and exact rational rounded-display vectors
  (`SD-001`..`SD-006`).
- Zero `.json` files are created under `manual/` in compliance with the release
  source-inventory packaging contract.

## CLI Usage

```bash
# List all 16 registered sectors
python3 -B -m manual.engine --list-sectors

# Full verification (normal and -O) with zero-float audit and golden vectors
mkdir -p _build/s2
python3 -B -m manual.engine --verify-all --check-zero-float --verify-vectors --report _build/s2/engine_norm.json
python3 -B -O -m manual.engine --verify-all --check-zero-float --verify-vectors --report _build/s2/engine_opt.json
cmp _build/s2/engine_norm.json _build/s2/engine_opt.json

# Run selected sectors only
python3 -B -m manual.engine --sector dec_ledger --sector higgs_trace --sector provenance_quarantine
```

Runtime reports (`--report`) and raw diagnostics (`--diagnostics-dir`) must be
written outside distributable source directories (for example under `_build/s2/`
or an external temporary directory); paths inside `manual/`, `tests/`, `scripts/`,
`contracts/`, or the repository root are rejected with exit code `2`.
