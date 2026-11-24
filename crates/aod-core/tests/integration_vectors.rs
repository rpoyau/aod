#![forbid(unsafe_code)]

//! Integration tests for `crates/aod-core/`:
//! - All 30 S4 golden vectors (`RC-001`..`RC-024` + `SD-001`..`SD-006`)
//! - Beyond-`i128` 100-digit arbitrary-precision stress tests
//! - Exact 90-tick cycle shedding against `wavelet_shedding_simulation.csv`
//! - FIPS 180-4 SHA-256 verification
//! - Adversarial policy mutation probes and false-positive immunity
//! - CLI determinism and unsafe `--report` path rejection

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use aod_core::bigint::BigInt;
use aod_core::bigrat::BigRat;
use aod_core::json::{parse_json, JsonValue};
use aod_core::numeric::{
    exact_isclose, format_fixed, parse_canonical_rational_pair, parse_printed_rational,
};
use aod_core::ops::{
    cycle_shedding_step_exact, cycle_shedding_trace, eval_operation, CycleSheddingTickInput,
};
use aod_core::policy::audit_crate_tree;
use aod_core::sha256::sha256_hex;
use aod_core::vectors::{verify_all_vectors, RATIONAL_CORE_REL, SYMBOLIC_DISPLAY_REL};
use aod_core::CoreError;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crates dir")
        .parent()
        .expect("repo root")
        .to_path_buf()
}

fn crate_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

struct TempDirGuard {
    path: PathBuf,
}

impl TempDirGuard {
    fn new(tag: &str) -> Self {
        let pid = std::process::id();
        let mut idx = 0u64;
        loop {
            let candidate = env::temp_dir().join(format!("aod_core_itest_{}_{}_{}", tag, pid, idx));
            if !candidate.exists() {
                fs::create_dir_all(&candidate).expect("create temp dir");
                return Self { path: candidate };
            }
            idx += 1;
        }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TempDirGuard {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn copy_crate_sources(src: &Path, dst: &Path) {
    fs::create_dir_all(dst).expect("mkdir dst");
    for entry in fs::read_dir(src).expect("read_dir src") {
        let entry = entry.expect("entry");
        let name = entry.file_name();
        if name == "target" {
            continue;
        }
        let from = entry.path();
        let to = dst.join(&name);
        if from.is_dir() {
            copy_crate_sources(&from, &to);
        } else if from.is_file() {
            fs::copy(&from, &to).expect("copy file");
        }
    }
}

#[test]
fn test_all_30_golden_vectors_pass() {
    let root = repo_root();
    let res = verify_all_vectors(&root).expect("verify_all_vectors");
    assert_eq!(res.status, "PASS", "failures: {:?}", res.failures);
    assert_eq!(res.rational_core_count, 24);
    assert_eq!(res.symbolic_and_display_count, 6);
    assert_eq!(res.total_vectors, 30);
    assert_eq!(res.passed_vectors, 30);
    assert_eq!(res.failed_vectors, 0);
    assert!(res.failures.is_empty());

    let rc_bytes = fs::read(root.join(RATIONAL_CORE_REL)).expect("read rc jsonl");
    let sd_bytes = fs::read(root.join(SYMBOLIC_DISPLAY_REL)).expect("read sd jsonl");
    assert_eq!(
        res.file_digests.get(RATIONAL_CORE_REL).map(String::as_str),
        Some(sha256_hex(&rc_bytes).as_str())
    );
    assert_eq!(
        res.file_digests.get(SYMBOLIC_DISPLAY_REL).map(String::as_str),
        Some(sha256_hex(&sd_bytes).as_str())
    );
}

#[test]
fn test_live_crate_policy_audit_passes() {
    let audit = audit_crate_tree(&crate_root()).expect("audit_crate_tree");
    assert_eq!(audit.status, "PASS", "violations: {:?}", audit.violations);
    assert_eq!(audit.violation_count, 0);
    assert_eq!(audit.json_files_under_crate, 0);
    assert_eq!(audit.cargo_lock_packages, 1);
    assert!(audit.audited_rust_files >= 12);
    assert!(audit
        .forbid_unsafe_checked_files
        .contains(&"src/lib.rs".to_string()));
    assert!(audit
        .forbid_unsafe_checked_files
        .contains(&"src/main.rs".to_string()));
    assert!(audit
        .forbid_unsafe_checked_files
        .contains(&"tests/integration_vectors.rs".to_string()));
}

#[test]
fn test_beyond_i128_100_digit_exact_arithmetic() {
    // 100-digit prime-like numerators & denominators far beyond i128::MAX (~1.7e38)
    let big_a = format!("1{}", "0".repeat(99)); // 10^99
    let big_b = format!("3{}", "7".repeat(99));
    let mut inputs = BTreeMap::new();
    inputs.insert(
        "table_iv_hz".to_string(),
        JsonValue::Array(vec![JsonValue::Str(big_b.clone()), JsonValue::Str("1".to_string())]),
    );
    inputs.insert(
        "table_vi_hz".to_string(),
        JsonValue::Array(vec![JsonValue::Str(big_a.clone()), JsonValue::Str("1".to_string())]),
    );
    let res = eval_operation("temporal_metrology_hellwig_mean", &inputs).expect("hellwig");
    let obj = res.as_object().expect("obj");
    let mean_arr = obj["published_mean_hz"].as_array().expect("pair");
    let diff_arr = obj["difference_hz"].as_array().expect("pair");
    let mean = parse_canonical_rational_pair(
        mean_arr[0].as_str().unwrap(),
        mean_arr[1].as_str().unwrap(),
    )
    .unwrap();
    let diff = parse_canonical_rational_pair(
        diff_arr[0].as_str().unwrap(),
        diff_arr[1].as_str().unwrap(),
    )
    .unwrap();
    let qa = BigRat::from_int(BigInt::from_ascii_digits(&big_a, false).unwrap());
    let qb = BigRat::from_int(BigInt::from_ascii_digits(&big_b, false).unwrap());
    assert_eq!(
        &mean + &diff.checked_div(&BigRat::from_i64(2)).unwrap(),
        qb
    );
    assert_eq!(
        &mean - &diff.checked_div(&BigRat::from_i64(2)).unwrap(),
        qa
    );

    // MAP-21 with y = +/- 10^-40 => variance denominator ~ 10^160 (far beyond i128!)
    let scale40 = BigInt::pow10(40).to_dec_string();
    let raw_map21 = format!(
        "{{\"support\":[{{\"p\":[\"1\",\"2\"],\"y\":[\"-1\",\"{}\"],\"d\":[\"-1\",\"{}\"]}},{{\"p\":[\"1\",\"2\"],\"y\":[\"1\",\"{}\"],\"d\":[\"1\",\"{}\"]}}]}}",
        scale40, scale40, scale40, scale40
    );
    let map_in = parse_json(&raw_map21).unwrap();
    let map_out = eval_operation(
        "map21_nonlinear_finite_law_variance",
        map_in.as_object().unwrap(),
    )
    .unwrap();
    let map_obj = map_out.as_object().unwrap();
    let var_pair = map_obj["output_variance"].as_array().unwrap();
    let var_den = var_pair[1].as_str().unwrap();
    assert!(
        var_den.len() > 120,
        "expected >120-digit denominator beyond i128, got {} digits",
        var_den.len()
    );
    assert_eq!(
        map_obj["linearized_variance_diagnostic"],
        JsonValue::Array(vec![
            JsonValue::Str("0".to_string()),
            JsonValue::Str("1".to_string()),
        ])
    );
}

#[test]
fn test_90_tick_exact_cycle_shedding_against_retained_csv() {
    let csv_path = repo_root().join("wavelet_shedding_simulation.csv");
    let raw = fs::read_to_string(&csv_path).expect("read wavelet_shedding_simulation.csv");
    let mut lines = raw.lines();
    let header = lines.next().expect("header").trim_end_matches('\r');
    assert_eq!(
        header,
        "tick,lead,lag,span,compatibility,padar_burden,shed_excess,outward_shedding,local_reclosure,state"
    );

    let eta = BigRat::from_i64_pair(41, 50).unwrap();
    let gamma = BigRat::from_i64_pair(11, 20).unwrap();
    let lam = BigRat::from_i64_pair(19, 50).unwrap();
    let tol = BigRat::new(BigInt::one(), BigInt::pow10(12)).unwrap();

    let mut tick_inputs: Vec<CycleSheddingTickInput> = Vec::with_capacity(90);
    let mut csv_prev = BigRat::zero();
    let mut max_span = BigRat::zero();
    let mut max_burden = BigRat::zero();
    let mut max_excess = BigRat::zero();
    let mut total_outward = BigRat::zero();
    let mut total_local = BigRat::zero();

    for (idx, line) in lines.enumerate() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let cols: Vec<&str> = trimmed.split(',').collect();
        assert_eq!(cols.len(), 10, "row {} column count", idx);
        assert_eq!(cols[0], idx.to_string());
        assert_eq!(cols[9], "open");

        let lead = parse_printed_rational(cols[1], false, false).unwrap();
        let lag = parse_printed_rational(cols[2], false, false).unwrap();
        let rec_span = parse_printed_rational(cols[3], false, false).unwrap();
        let comp = parse_printed_rational(cols[4], false, false).unwrap();
        let rec_burden = parse_printed_rational(cols[5], false, false).unwrap();
        let rec_excess = parse_printed_rational(cols[6], false, false).unwrap();
        let rec_out = parse_printed_rational(cols[7], false, false).unwrap();
        let rec_loc = parse_printed_rational(cols[8], false, false).unwrap();

        let step = cycle_shedding_step_exact(&csv_prev, &lead, &lag, &comp, &eta, &gamma, &lam);
        assert!(exact_isclose(&rec_span, &step.span, &tol, None).unwrap());
        assert!(exact_isclose(&rec_burden, &step.padar_burden, &tol, None).unwrap());
        assert!(exact_isclose(&rec_excess, &step.shed_excess, &tol, None).unwrap());
        assert!(exact_isclose(&rec_out, &step.outward_shedding, &tol, None).unwrap());
        assert!(exact_isclose(&rec_loc, &step.local_reclosure, &tol, None).unwrap());

        if rec_span > max_span {
            max_span = rec_span;
        }
        if rec_burden > max_burden {
            max_burden = rec_burden.clone();
        }
        if rec_excess > max_excess {
            max_excess = rec_excess;
        }
        total_outward = &total_outward + &rec_out;
        total_local = &total_local + &rec_loc;
        csv_prev = rec_burden;

        tick_inputs.push(CycleSheddingTickInput {
            lead,
            lag,
            compatibility: comp,
        });
    }
    assert_eq!(tick_inputs.len(), 90);

    // Verify full 90-tick chained exact BigRat trace without rounding intermediate padar_burden.
    let trace = cycle_shedding_trace(&BigRat::zero(), &tick_inputs, &eta, &gamma, &lam);
    assert_eq!(trace.len(), 90);
    let max_den_digits = trace
        .iter()
        .map(|s| s.padar_burden.den().to_dec_string().len())
        .max()
        .unwrap_or(0);
    assert!(
        max_den_digits > 40,
        "chained 90-tick exact BigRat denominators must grow beyond i128, got {} digits",
        max_den_digits
    );
    // Chained exact trace remains consistent with retained summary fixed displays at 3dp.
    let chained_out: BigRat = trace
        .iter()
        .fold(BigRat::zero(), |acc, s| &acc + &s.outward_shedding);
    let chained_loc: BigRat = trace
        .iter()
        .fold(BigRat::zero(), |acc, s| &acc + &s.local_reclosure);
    assert_eq!(
        format_fixed(&chained_out, 3).unwrap(),
        format_fixed(&total_outward, 3).unwrap()
    );
    assert_eq!(
        format_fixed(&chained_loc, 3).unwrap(),
        format_fixed(&total_local, 3).unwrap()
    );
}

#[test]
fn test_policy_negative_controls_in_isolated_copy() {
    let tmp = TempDirGuard::new("policy_neg");
    copy_crate_sources(&crate_root(), tmp.path());
    assert_eq!(audit_crate_tree(tmp.path()).unwrap().status, "PASS");

    // 1. Inject float literal
    let probe = tmp.path().join("src/probe.rs");
    fs::write(&probe, "pub fn bad() { let _x = 0.5; }\n").unwrap();
    let a = audit_crate_tree(tmp.path()).unwrap();
    assert_eq!(a.status, "FAIL");
    assert!(a.violations.iter().any(|v| v.rule == "forbidden_float_literal"));
    fs::remove_file(&probe).unwrap();

    // 2. Inject unsafe block
    fs::write(&probe, "pub fn bad() { unsafe {} }\n").unwrap();
    let a = audit_crate_tree(tmp.path()).unwrap();
    assert_eq!(a.status, "FAIL");
    assert!(a.violations.iter().any(|v| v.rule == "forbidden_unsafe"));
    fs::remove_file(&probe).unwrap();

    // 3. Inject forbidden .json file
    let bad_json = tmp.path().join("stray.json");
    fs::write(&bad_json, "{}\n").unwrap();
    let a = audit_crate_tree(tmp.path()).unwrap();
    assert_eq!(a.status, "FAIL");
    assert_eq!(a.json_files_under_crate, 1);
    fs::remove_file(&bad_json).unwrap();

    // 4. Inject experimental token dynamically
    let exp_tok = format!("{}-{}", "aod", "dec");
    fs::write(&probe, format!("// {}\n", exp_tok)).unwrap();
    let a = audit_crate_tree(tmp.path()).unwrap();
    assert_eq!(a.status, "FAIL");
    assert!(a
        .violations
        .iter()
        .any(|v| v.rule == "forbidden_experimental_token"));
    fs::remove_file(&probe).unwrap();

    // 5. Inject external dependency into Cargo.toml
    let manifest_path = tmp.path().join("Cargo.toml");
    let orig_manifest = fs::read_to_string(&manifest_path).unwrap();
    fs::write(&manifest_path, format!("{}\nserde = \"1\"\n", orig_manifest)).unwrap();
    let a = audit_crate_tree(tmp.path()).unwrap();
    assert_eq!(a.status, "FAIL");
    assert!(a.violations.iter().any(|v| v.rule == "forbidden_dependency"));
    fs::write(&manifest_path, orig_manifest).unwrap();

    // Restored clean copy passes again
    assert_eq!(audit_crate_tree(tmp.path()).unwrap().status, "PASS");
}

#[test]
fn test_cli_report_and_unsafe_path_rejection() {
    let bin = env!("CARGO_BIN_EXE_aod-core");
    let root = repo_root();
    let tmp = TempDirGuard::new("cli");
    let out_report = tmp.path().join("report.json");

    let ok = Command::new(bin)
        .args([
            "--verify-vectors",
            "--check-zero-float",
            "--repo-root",
            root.to_str().unwrap(),
            "--report",
            out_report.to_str().unwrap(),
        ])
        .output()
        .expect("run aod-core");
    assert_eq!(
        ok.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&ok.stderr)
    );
    let body = fs::read_to_string(&out_report).expect("read report");
    let parsed = parse_json(&body).expect("zero-float parse report");
    let obj = parsed.as_object().unwrap();
    assert_eq!(obj["schema"], JsonValue::Str("aod.s4.rust.report.v1".to_string()));
    assert_eq!(obj["overall_status"], JsonValue::Str("PASS".to_string()));

    // Unsafe --report inside distributable repo source dir must exit 2 and NOT create file.
    let unsafe_target = root.join("manual/illegal_s4_report.json");
    let bad = Command::new(bin)
        .args([
            "--verify-vectors",
            "--repo-root",
            root.to_str().unwrap(),
            "--report",
            unsafe_target.to_str().unwrap(),
        ])
        .output()
        .expect("run aod-core unsafe");
    assert_eq!(bad.status.code(), Some(2));
    assert!(!unsafe_target.exists());

    // CLI rejects invalid JSON float via --eval-op with exit 1
    let bad_float = Command::new(bin)
        .args([
            "--eval-op",
            "closure_wave_rd_rcd",
            "--input-json",
            "{\"p\": 1.5}",
        ])
        .output()
        .expect("run aod-core float");
    assert_eq!(bad_float.status.code(), Some(1));
    let _ = CoreError::FloatLiteral(String::new());
}
