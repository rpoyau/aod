# `aod-core` (Stage 4 Optional `std`-Only Rust Exact Core)

`crates/aod-core/` is an **optional**, strictly `std`-only, zero-float, zero-`unsafe` Rust exact-arithmetic core for Alpha Omega Dynamics (AOD).

## Optionality & Independence Boundary

- **100% Optional for Python/Typst Builds:** The canonical Typst publication build (`scripts/build_publication.py`), scientific source audit (`scripts/audit_scientific_sources.py`), and Stage 2 Python reference engine (`manual/engine/`) do **not** import, invoke, or require Rust or `crates/aod-core/`.
- **Zero External Dependencies:** `Cargo.toml` contains an empty `[dependencies]` section and `Cargo.lock` pins strictly the single local `aod-core` package. All builds and tests run cleanly with `--offline --locked`.
- **Zero Floats & Zero `unsafe`:** `#![forbid(unsafe_code)]` is enforced across `src/lib.rs`, `src/main.rs`, and `tests/*.rs`. No floating-point types (`f16`/`f32`/`f64`/`f128`), float literals, `unsafe` blocks, or `extern` blocks appear in active Rust code.
- **Arbitrary-Precision Exact Arithmetic:** All calculations run in sign-magnitude base-2^32 `BigInt`, canonical reduced `BigRat`, `GaussianRat` (`Q(i)`), and `Cyclotomic12` (`Q[x]/(x^4 - x^2 + 1)`).

## Offline Verification Commands

Always direct Cargo build output outside `crates/aod-core/target/` (e.g. `CARGO_TARGET_DIR=_build/cargo-target`) so the source tree remains clean:

```bash
CARGO_TARGET_DIR=_build/cargo-target cargo test --manifest-path crates/aod-core/Cargo.toml --offline --locked
CARGO_TARGET_DIR=_build/cargo-target cargo test --manifest-path crates/aod-core/Cargo.toml --offline --locked --release

mkdir -p _build/s4
CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked -- \
  --verify-vectors --check-zero-float --report _build/s4/rust_report_debug.json
CARGO_TARGET_DIR=_build/cargo-target cargo run --manifest-path crates/aod-core/Cargo.toml --offline --locked --release -- \
  --verify-vectors --check-zero-float --report _build/s4/rust_report_release.json
cmp _build/s4/rust_report_debug.json _build/s4/rust_report_release.json
```

## CLI Flags

- `--verify-vectors`: Verify all 40 S4 golden vectors (`manual/engine/vectors/rational_core.jsonl` and `manual/engine/vectors/symbolic_and_display.jsonl`).
- `--check-zero-float`: Run the built-in Rust lexical and packaging policy auditor over `crates/aod-core/`.
- `--eval-op <OP>` with `--input-json <JSON>` or `--input-stdin`: Evaluate a single exact operation and emit canonical zero-float JSON.
- `--repo-root <PATH>` / `--crate-root <PATH>`: Override repository or crate roots (useful when auditing a detached `source.zip` checkout).
- `--report <PATH>`: Write deterministic canonical JSON (`aod.s4.rust.report.v1`) outside distributable repository directories or under `_build/` (rejects symlinks and unsafe paths with exit code `2`).
- Exit codes: `0` (PASS), `1` (verification/evaluation failure), `2` (CLI usage error or unsafe `--report` path).
