#![forbid(unsafe_code)]

//! Integration tests for `crates/aod-core/`:
//! - All 40 S4 golden vectors (`RC-001`..`RC-032` + `SD-001`..`SD-008`)
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
use aod_core::json::{parse_json, to_canonical_json_pretty, JsonValue};
use aod_core::numeric::{
    exact_isclose, format_fixed, parse_canonical_rational_pair, parse_printed_rational,
};
use aod_core::ops::{
    cycle_shedding_step_exact, cycle_shedding_trace, eval_operation, CycleSheddingTickInput,
};
use aod_core::policy::audit_crate_tree;
use aod_core::report::validate_portable_report;
use aod_core::sha256::sha256_hex;
use aod_core::vectors::{
    load_vector_file, validate_source_binding, verify_all_vectors, verify_single_vector,
    verify_single_vector_with_root, RATIONAL_CORE_REL, SYMBOLIC_DISPLAY_REL,
};
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
fn test_all_40_golden_vectors_pass() {
    let root = repo_root();
    let res = verify_all_vectors(&root).expect("verify_all_vectors");
    assert_eq!(res.status, "PASS", "failures: {:?}", res.failures);
    assert_eq!(res.rational_core_count, 45);
    assert_eq!(res.symbolic_and_display_count, 8);
    assert_eq!(res.total_vectors, 53);
    assert_eq!(res.passed_vectors, 53);
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
fn test_boundary_sadar_tau_and_higgs_invariants() {
    let tau_in = parse_json(r#"{"lead_lag":8,"window_duons":3}"#).expect("parse tau_in");
    let tau_out = eval_operation("sadar_pp_tau_five_boundary", tau_in.as_object().unwrap())
        .expect("eval sadar_pp_tau_five_boundary");
    let tobj = tau_out.as_object().unwrap();
    assert_eq!(tobj["selected_tau_candidate"].as_str(), Some("1:2:9_yro"));
    assert_eq!(
        tobj["miss_tau_conditional_exo"],
        JsonValue::Array(vec![
            JsonValue::Str("31".to_string()),
            JsonValue::Str("50".to_string())
        ])
    );

    let higgs_in = parse_json(r#"{"parent_p":3,"parent_q":3,"C3_channel":3}"#).expect("parse higgs");
    let higgs_out = eval_operation(
        "sadar_hadron_debris_and_higgs_saddle",
        higgs_in.as_object().unwrap(),
    )
    .expect("eval sadar_hadron_debris_and_higgs_saddle");
    let hobj = higgs_out.as_object().unwrap();
    assert_eq!(
        hobj["selected_higgs_candidate"].as_str(),
        Some("3:3:7_yro")
    );
    assert_eq!(hobj["frozen_map_MeV"], JsonValue::Int(BigInt::from_i64(124_928)));
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

    // Reject trailing `/.`, `/`, and normalized symlink targets with exit 2 without touching target.
    #[cfg(unix)]
    {
        use std::os::unix::fs::symlink;
        let real_outside = tmp.path().join("real_outside.json");
        let sym_target = tmp.path().join("sym_target");
        symlink(&real_outside, &sym_target).expect("create symlink");
        let sub_dir = tmp.path().join("sub");
        fs::create_dir_all(&sub_dir).expect("mkdir sub");

        let bypass_probes = [
            format!("{}/.", sym_target.to_str().unwrap()),
            format!("{}/", sym_target.to_str().unwrap()),
            format!("{}/../sym_target", sub_dir.to_str().unwrap()),
        ];
        for probe in &bypass_probes {
            let res = Command::new(bin)
                .args([
                    "--verify-vectors",
                    "--repo-root",
                    root.to_str().unwrap(),
                    "--report",
                    probe.as_str(),
                ])
                .output()
                .expect("run aod-core symlink probe");
            assert_eq!(res.status.code(), Some(2), "expected exit 2 for {}", probe);
        }
        assert!(!real_outside.exists(), "symlink target must remain untouched");

        // Symlinked crate_root must be rejected cleanly by audit_crate_tree.
        let sym_crate = tmp.path().join("sym_crate");
        symlink(crate_root(), &sym_crate).expect("symlink crate_root");
        assert!(matches!(
            audit_crate_tree(&sym_crate),
            Err(CoreError::UnsafePath(_))
        ));
    }

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

fn populate_bound_repo_copy(src_root: &Path, dst_root: &Path, include_crate: bool) {
    let (_, rc_rows) = load_vector_file(src_root, RATIONAL_CORE_REL).expect("load rc");
    let (_, sd_rows) = load_vector_file(src_root, SYMBOLIC_DISPLAY_REL).expect("load sd");
    for rel in [RATIONAL_CORE_REL, SYMBOLIC_DISPLAY_REL, "typst/main.typ"] {
        let from = src_root.join(rel);
        let to = dst_root.join(rel);
        if let Some(p) = to.parent() {
            fs::create_dir_all(p).expect("mkdir parent");
        }
        fs::copy(&from, &to).expect("copy core file");
    }
    for rec in rc_rows.iter().chain(sd_rows.iter()) {
        let binding = rec["source_binding"].as_str().expect("source_binding");
        for comp in binding.split(';') {
            let rel_path = comp.split('#').next().unwrap_or(comp);
            let from = src_root.join(rel_path);
            let to = dst_root.join(rel_path);
            if let Some(p) = to.parent() {
                fs::create_dir_all(p).expect("mkdir bound parent");
            }
            if !to.exists() {
                fs::copy(&from, &to).expect("copy bound source file");
            }
        }
    }
    if include_crate {
        copy_crate_sources(
            &src_root.join("crates/aod-core"),
            &dst_root.join("crates/aod-core"),
        );
    }
}

fn write_jsonl_records(path: &Path, records: &[BTreeMap<String, JsonValue>]) {
    let mut out = String::new();
    for rec in records {
        let single_line = to_canonical_json_pretty(&JsonValue::Object(rec.clone()))
            .lines()
            .map(str::trim)
            .collect::<Vec<_>>()
            .join("");
        out.push_str(&single_line);
        out.push('\n');
    }
    fs::write(path, out).expect("write jsonl");
}

#[test]
fn test_s4_f1_external_hardlink_leaves_protected_source_untouched_and_overwrite_works() {
    let bin = env!("CARGO_BIN_EXE_aod-core");
    let tmp = TempDirGuard::new("s4_f1_hardlink");
    let detached_repo = tmp.path().join("detached_repo");
    populate_bound_repo_copy(&repo_root(), &detached_repo, true);

    let protected_main = detached_repo.join("typst/main.typ");
    let orig_bytes = fs::read(&protected_main).expect("read typst/main.typ");
    let orig_sha = sha256_hex(&orig_bytes);

    let ext_dir = tmp.path().join("external_out");
    fs::create_dir_all(&ext_dir).expect("mkdir ext");
    let ext_report = ext_dir.join("report.json");
    fs::hard_link(&protected_main, &ext_report).expect("create external hard link");

    #[cfg(unix)]
    let orig_ino = {
        use std::os::unix::fs::MetadataExt;
        let meta_src = fs::symlink_metadata(&protected_main).expect("stat src");
        let meta_ext = fs::symlink_metadata(&ext_report).expect("stat ext");
        assert_eq!(meta_src.ino(), meta_ext.ino());
        assert_eq!(meta_src.nlink(), 2);
        meta_src.ino()
    };

    let run1 = Command::new(bin)
        .args([
            "--verify-vectors",
            "--check-zero-float",
            "--repo-root",
            detached_repo.to_str().unwrap(),
            "--report",
            ext_report.to_str().unwrap(),
        ])
        .output()
        .expect("run aod-core hardlink");
    assert_eq!(
        run1.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&run1.stderr)
    );

    // Protected source file must be 100% untouched on original inode with nlink == 1
    let after_bytes = fs::read(&protected_main).expect("read typst/main.typ after");
    assert_eq!(after_bytes, orig_bytes);
    assert_eq!(sha256_hex(&after_bytes), orig_sha);

    let rep1_bytes = fs::read(&ext_report).expect("read report 1");
    let rep1_parsed = parse_json(&String::from_utf8(rep1_bytes.clone()).expect("utf8"))
        .expect("parse report 1");
    assert_eq!(
        rep1_parsed.as_object().unwrap()["overall_status"],
        JsonValue::Str("PASS".to_string())
    );

    #[cfg(unix)]
    {
        use std::os::unix::fs::MetadataExt;
        let meta_src = fs::symlink_metadata(&protected_main).expect("stat src after");
        let meta_ext = fs::symlink_metadata(&ext_report).expect("stat ext after");
        assert_eq!(meta_src.ino(), orig_ino, "protected source inode changed");
        assert_eq!(meta_src.nlink(), 1, "protected source link count must drop back to 1");
        assert_ne!(meta_ext.ino(), orig_ino, "report must be installed on a new inode");
        assert_eq!(meta_ext.nlink(), 1);
    }

    // No stray temporary files left behind in external_out
    let leftovers: Vec<String> = fs::read_dir(&ext_dir)
        .expect("read ext_dir")
        .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|name| name.starts_with(".aod-core-tmp-"))
        .collect();
    assert!(leftovers.is_empty(), "leftover tmp files: {:?}", leftovers);

    // Ordinary repeated overwrite to the same report path succeeds with byte-identical output
    let run2 = Command::new(bin)
        .args([
            "--verify-vectors",
            "--check-zero-float",
            "--repo-root",
            detached_repo.to_str().unwrap(),
            "--report",
            ext_report.to_str().unwrap(),
        ])
        .output()
        .expect("run aod-core overwrite");
    assert_eq!(
        run2.status.code(),
        Some(0),
        "stderr: {}",
        String::from_utf8_lossy(&run2.stderr)
    );
    assert_eq!(fs::read(&ext_report).expect("read report 2"), rep1_bytes);
}

#[test]
fn test_s2_f3_source_binding_negative_regressions_and_sanitized_hostile_report() {
    let root = repo_root();

    // Live repo negative controls covering all 5 selector forms
    let bad_live_bindings = [
        "manual/data/does_not_exist.csv",
        "typst/sections/04_cut_running_fractal_tesseract.typ#eq:atomic-h1",
        "typst/sections/05_curl_closure_duon_current.typ#eq:afc-stokes-used",
        "typst/sections/06_field.typ#eq:nonexistent-label",
        "manual/data/derived/sparc_five_galaxy_per_bin.csv#row00",
        "manual/data/derived/sparc_five_galaxy_per_bin.csv#row078_NGC3198",
        "manual/data/derived/sparc_five_galaxy_per_bin.csv#row99999",
        "manual/data/derived/sparc_five_galaxy_per_bin.csv#NONEXISTENT_GALAXY",
        "manual/scripts/aod_awareness.py#nonexistent_func",
        "manual/scripts/generate_cycle_shedding_fixture.py#L1-999999",
        "manual/scripts/generate_cycle_shedding_fixture.py#L01-10",
        "manual/data/mapping_error/mapping_error.json#original_historical_laws.cases.MISSING",
        "manual/data/higgs/higgs_trace_score_formula.md#sec1",
        "manual/data/dec/dec_one_node_ledger_example.csv#",
        "manual/data/dec/dec_one_node_ledger_example.csv;",
        "/etc/passwd",
        "../typst/main.typ",
        "typst\\main.typ",
    ];
    for binding in bad_live_bindings {
        assert!(
            validate_source_binding(&root, binding).is_err(),
            "expected validate_source_binding to reject {:?}",
            binding
        );
    }

    // Synthetic Typst traps (inline raw, fenced raw, #ref, #link, symlinked bound file)
    let tmp = TempDirGuard::new("s2_f3_traps");
    let fake_root = tmp.path().join("repo");
    fs::create_dir_all(fake_root.join("typst")).expect("mkdir typst");
    fs::write(
        fake_root.join("typst/traps.typ"),
        "// <eq:comment>\n\
         /* nested /* <eq:block> */ */\n\
         inline `<eq:inline-raw>` text\n\
         ```typ\n<eq:fenced-raw>\n```\n\
         #ref(<eq:ref-only>)\n\
         #link(<eq:link-only>)\n\
         #cite(<eq:cite-only>)\n\
         #query(<eq:query-only>)\n\
         #selector(<eq:selector-only>)\n\
         $ x = 1 $ <eq:real-anchor>\n",
    )
    .expect("write traps.typ");

    assert!(validate_source_binding(&fake_root, "typst/traps.typ#eq:real-anchor").is_ok());
    for trap in [
        "typst/traps.typ#eq:comment",
        "typst/traps.typ#eq:block",
        "typst/traps.typ#eq:inline-raw",
        "typst/traps.typ#eq:fenced-raw",
        "typst/traps.typ#eq:ref-only",
        "typst/traps.typ#eq:link-only",
        "typst/traps.typ#eq:cite-only",
        "typst/traps.typ#eq:query-only",
        "typst/traps.typ#eq:selector-only",
    ] {
        assert!(
            validate_source_binding(&fake_root, trap).is_err(),
            "Typst trap {:?} should be rejected",
            trap
        );
    }

    #[cfg(unix)]
    {
        use std::os::unix::fs::symlink;
        let outside_file = tmp.path().join("outside.csv");
        fs::write(&outside_file, "a,b\n1,2\n").expect("write outside");
        symlink(&outside_file, fake_root.join("sym.csv")).expect("symlink bound file");
        assert!(matches!(
            validate_source_binding(&fake_root, "sym.csv"),
            Err(CoreError::UnsafePath(_))
        ));
    }

    // End-to-end CLI test: hostile "/etc/passwd" source_binding produces sanitized portable FAIL report
    let hostile_repo = tmp.path().join("hostile_repo");
    populate_bound_repo_copy(&root, &hostile_repo, false);
    let (_, mut rc_rows) = load_vector_file(&hostile_repo, RATIONAL_CORE_REL).expect("load rc");
    rc_rows[0].insert(
        "source_binding".to_string(),
        JsonValue::Str("/etc/passwd".to_string()),
    );
    write_jsonl_records(&hostile_repo.join(RATIONAL_CORE_REL), &rc_rows);

    let fail_report = tmp.path().join("hostile_fail.json");
    let bin = env!("CARGO_BIN_EXE_aod-core");
    let out = Command::new(bin)
        .args([
            "--verify-vectors",
            "--repo-root",
            hostile_repo.to_str().unwrap(),
            "--report",
            fail_report.to_str().unwrap(),
        ])
        .output()
        .expect("run aod-core hostile");
    assert_eq!(out.status.code(), Some(1));
    let body = fs::read_to_string(&fail_report).expect("read hostile fail report");
    assert!(
        !body.contains("/etc/passwd"),
        "hostile absolute path leaked in report: {}",
        body
    );
    let parsed = parse_json(&body).expect("parse hostile report");
    validate_portable_report(&parsed, "$").expect("portable report guard");
    let vv = parsed.as_object().unwrap()["vectors_verification"]
        .as_object()
        .unwrap();
    assert_eq!(vv["status"], JsonValue::Str("FAIL".to_string()));
    assert_eq!(vv["failed_vectors"], JsonValue::Int(BigInt::from_usize(1)));
}

#[test]
fn test_s2_f2_boolean_int_type_substitutions_rejected() {
    let root = repo_root();
    let (_, rc_rows) = load_vector_file(&root, RATIONAL_CORE_REL).expect("load rc");

    // 1. RC-005: hamming_distance 1 -> true
    let mut rc005 = rc_rows[4].clone();
    assert_eq!(rc005["case_id"], JsonValue::Str("RC-005".to_string()));
    if let Some(JsonValue::Object(exp)) = rc005.get_mut("expected_outcome") {
        if let Some(JsonValue::Object(ev)) = exp.get_mut("exact_value") {
            ev.insert("hamming_distance".to_string(), JsonValue::Bool(true));
        }
    }
    assert!(verify_single_vector(&rc005).is_err());
    assert!(verify_single_vector_with_root(&rc005, &root).is_err());

    // 2. RC-009: selected_slot 0 -> false
    let mut rc009 = rc_rows[8].clone();
    assert_eq!(rc009["case_id"], JsonValue::Str("RC-009".to_string()));
    if let Some(JsonValue::Object(exp)) = rc009.get_mut("expected_outcome") {
        if let Some(JsonValue::Object(ev)) = exp.get_mut("exact_value") {
            ev.insert("selected_slot".to_string(), JsonValue::Bool(false));
        }
    }
    assert!(verify_single_vector(&rc009).is_err());
    assert!(verify_single_vector_with_root(&rc009, &root).is_err());

    // 3. RC-010: no_delay_stable_at_one true -> 1
    let mut rc010 = rc_rows[9].clone();
    assert_eq!(rc010["case_id"], JsonValue::Str("RC-010".to_string()));
    if let Some(JsonValue::Object(exp)) = rc010.get_mut("expected_outcome") {
        if let Some(JsonValue::Object(ev)) = exp.get_mut("exact_value") {
            ev.insert(
                "no_delay_stable_at_one".to_string(),
                JsonValue::Int(BigInt::one()),
            );
        }
    }
    assert!(verify_single_vector(&rc010).is_err());
    assert!(verify_single_vector_with_root(&rc010, &root).is_err());

    // End-to-end verify_all_vectors rejects all 3 in detached copy
    let tmp = TempDirGuard::new("s2_f2_bool_int");
    let detached = tmp.path().join("repo");
    populate_bound_repo_copy(&root, &detached, false);
    let mut mutated = rc_rows;
    mutated[4] = rc005;
    mutated[8] = rc009;
    mutated[9] = rc010;
    write_jsonl_records(&detached.join(RATIONAL_CORE_REL), &mutated);

    let res = verify_all_vectors(&detached).expect("verify_all_vectors");
    assert_eq!(res.status, "FAIL");
    assert_eq!(res.failed_vectors, 3);
    let failed_ids: Vec<&str> = res.failures.iter().map(|f| f.case_id.as_str()).collect();
    assert_eq!(failed_ids, vec!["RC-005", "RC-009", "RC-010"]);
}

#[test]
fn test_rc045_ternary_swar_and_trit_ratio_integration() {
    let root = repo_root();
    let (_, rc_rows) = load_vector_file(&root, RATIONAL_CORE_REL).expect("load rc");
    assert_eq!(rc_rows.len(), 45);
    let rc045 = &rc_rows[44];
    assert_eq!(rc045["case_id"], JsonValue::Str("RC-045".to_string()));
    assert_eq!(
        rc045["operation"],
        JsonValue::Str("ternary_swar_and_trit_ratio".to_string())
    );
    verify_single_vector_with_root(rc045, &root).expect("RC-045 must verify cleanly");

    let inputs = rc045["inputs"].as_object().expect("RC-045 inputs");
    let out = eval_operation("ternary_swar_and_trit_ratio", inputs).expect("eval RC-045");
    let obj = out.as_object().expect("RC-045 output object");
    let swar = obj["swar"].as_object().expect("swar object");
    assert_eq!(swar["neg_symbols"], JsonValue::Str("H-0+000H+-".to_string()));
    assert_eq!(swar["hinge_preserved_under_neg"], JsonValue::Bool(true));
    assert_eq!(
        swar["burned_keep_single_symbols"],
        JsonValue::Str("H+0-0H-+".to_string())
    );

    let barrier = obj["barrier_add"].as_object().expect("barrier_add object");
    assert_eq!(
        barrier["result_symbols"],
        JsonValue::Str("+-H+0H0-".to_string())
    );
    assert_eq!(barrier["had_blocked_carry"], JsonValue::Bool(true));

    let big_w = obj["big_word"].as_object().expect("big_word object");
    assert_eq!(big_w["gcd"], JsonValue::Str("297".to_string()));
    assert_eq!(big_w["divmod_q"], JsonValue::Str("-10".to_string()));
    assert_eq!(big_w["divmod_r"], JsonValue::Str("-5643".to_string()));

    let tr = obj["trit_ratio"].as_object().expect("trit_ratio object");
    assert_eq!(
        tr["add_pair"],
        JsonValue::Array(vec![
            JsonValue::Str("17".to_string()),
            JsonValue::Str("42".to_string())
        ])
    );
    assert_eq!(
        tr["div_pair"],
        JsonValue::Array(vec![
            JsonValue::Str("-28".to_string()),
            JsonValue::Str("45".to_string())
        ])
    );
    assert_eq!(tr["value_eq_cleared"], JsonValue::Bool(true));
    assert_eq!(tr["structural_eq_cleared"], JsonValue::Bool(false));
}

#[test]
fn test_derived_tau_rotor_and_conflicting_slot_rejection() {
    let tau_in = parse_json(r#"{"lead_lag":8,"window_duons":3}"#).expect("parse tau_in");
    let tau_out = eval_operation("sadar_pp_tau_five_boundary", tau_in.as_object().unwrap())
        .expect("eval sadar_pp_tau_five_boundary");
    let tobj = tau_out.as_object().unwrap();

    let sterile = tobj["sterile_control"].as_object().unwrap();
    assert_eq!(sterile["coupled"], JsonValue::Bool(false));

    let live = tobj["live_cavity"].as_object().unwrap();
    assert_eq!(live["coupled"], JsonValue::Bool(true));
    assert_eq!(live["raw_cuts"], JsonValue::Int(BigInt::from_i64(28)));
    assert_eq!(live["quotient_cuts"], JsonValue::Int(BigInt::from_i64(11)));
    assert_eq!(live["dwell_burned"], JsonValue::Int(BigInt::from_i64(17)));
    assert_eq!(live["readonly_sensor_invariant"], JsonValue::Bool(true));

    assert_eq!(
        tobj["partition_2500_numerators"],
        JsonValue::Array(vec![
            JsonValue::Int(BigInt::from_i64(650)),
            JsonValue::Int(BigInt::from_i64(703)),
            JsonValue::Int(BigInt::from_i64(1147)),
        ])
    );
    assert_eq!(
        tobj["endo_retained_fraction"],
        JsonValue::Array(vec![
            JsonValue::Str("13".to_string()),
            JsonValue::Str("50".to_string()),
        ])
    );
    assert_eq!(
        tobj["exo_outward_fraction"],
        JsonValue::Array(vec![
            JsonValue::Str("37".to_string()),
            JsonValue::Str("50".to_string()),
        ])
    );
    assert_eq!(
        tobj["visible_conditional_exo"],
        JsonValue::Array(vec![
            JsonValue::Str("19".to_string()),
            JsonValue::Str("50".to_string()),
        ])
    );
    assert_eq!(
        tobj["miss_tau_conditional_exo"],
        JsonValue::Array(vec![
            JsonValue::Str("31".to_string()),
            JsonValue::Str("50".to_string()),
        ])
    );

    // Negative control: conflicting legacy slot override must be rejected with ValueError
    let bad_endo = parse_json(r#"{"lead_lag":8,"window_duons":3,"shed_endo_slots":12}"#)
        .expect("parse bad_endo");
    let err_endo = eval_operation("sadar_pp_tau_five_boundary", bad_endo.as_object().unwrap());
    assert!(
        matches!(err_endo, Err(CoreError::ValueError(_))),
        "expected CoreError::ValueError for conflicting shed_endo_slots=12, got {:?}",
        err_endo
    );

    let bad_miss = parse_json(r#"{"lead_lag":8,"window_duons":3,"sensor_missing_slots":30}"#)
        .expect("parse bad_miss");
    let err_miss = eval_operation("sadar_pp_tau_five_boundary", bad_miss.as_object().unwrap());
    assert!(
        matches!(err_miss, Err(CoreError::ValueError(_))),
        "expected CoreError::ValueError for conflicting sensor_missing_slots=30, got {:?}",
        err_miss
    );
}

#[test]
fn test_rc030_genuine_c6_double_slit_enumerator() {
    let inputs = parse_json(
        r#"{"screen_half_span":5,"hexon_cap":6,"comparator_O":[8,11,19,59,79,95,80,58,21,10,8]}"#,
    )
    .expect("parse RC-030 inputs");
    let out = eval_operation(
        "frg_dimonhexon_double_slit_ring",
        inputs.as_object().unwrap(),
    )
    .expect("eval RC-030");
    let obj = out.as_object().unwrap();

    let to_i64_arr = |vals: &[i64]| -> JsonValue {
        JsonValue::Array(
            vals.iter()
                .map(|&v| JsonValue::Int(BigInt::from_i64(v)))
                .collect(),
        )
    };

    assert_eq!(
        obj["S_k"],
        to_i64_arr(&[4, 9, 16, 25, 31, 35, 31, 25, 16, 9, 4])
    );
    assert_eq!(
        obj["T0_k"],
        to_i64_arr(&[8, 18, 32, 50, 62, 70, 62, 50, 32, 18, 8])
    );
    assert_eq!(
        obj["C_cross_k"],
        to_i64_arr(&[0, -8, -12, 8, 18, 26, 18, 8, -12, -8, 0])
    );
    assert_eq!(
        obj["T_cross_k"],
        to_i64_arr(&[8, 10, 20, 58, 80, 96, 80, 58, 20, 10, 8])
    );
    assert_eq!(
        obj["Delta_Z_k"],
        to_i64_arr(&[0, -1, 1, -1, 1, 1, 0, 0, -1, 0, 0])
    );
    assert_eq!(obj["sum_T0"], JsonValue::Int(BigInt::from_i64(410)));
    assert_eq!(obj["sum_C_cross"], JsonValue::Int(BigInt::from_i64(38)));
    assert_eq!(obj["sum_T_cross"], JsonValue::Int(BigInt::from_i64(448)));
    assert_eq!(obj["sum_Delta_Z"], JsonValue::Int(BigInt::from_i64(0)));
    assert_eq!(obj["sum_m_k"], JsonValue::Int(BigInt::from_i64(6)));

    // Static check: no hardcoded lookup tables in sadar_sim.rs
    let sim_src =
        fs::read_to_string(crate_root().join("src/sadar_sim.rs")).expect("read sadar_sim.rs");
    assert!(
        !sim_src.contains("cross_map"),
        "sadar_sim.rs must not contain hardcoded cross_map"
    );
    assert!(
        !sim_src.contains("sat_clip"),
        "sadar_sim.rs must not contain hardcoded sat_clip"
    );
}

#[test]
fn test_sd008_declared_g0_sparc_exact() {
    // 1. Synthetic declared G0 bins: negative V_gas uses |V_gas| and V_gas^2, zero V_obs is skipped.
    // Bin 1: r=2, V_obs=10, V_gas=-3, V_disk=4, V_bul=0 => U_obs=100, U_bar=17, U_AO=129, err=29/100
    // Bin 2: V_obs=0 => skipped
    // Bin 3: r=1, V_obs=10, V_gas=0, V_disk=0, V_bul=10 => U_obs=100, U_bar=70, U_AO=150, err=50/100
    // MAPE = 100 * ((29/100 + 50/100) / 2) = 79/2 = 39.50000000
    let syn_neg = parse_json(
        r#"{"bins":[
            {"r_kpc":"2","V_obs":"10","V_gas":"-3","V_disk":"4","V_bul":"0"},
            {"r_kpc":"5","V_obs":"0","V_gas":"-5","V_disk":"2","V_bul":"10"},
            {"r_kpc":"1","V_obs":"10","V_gas":"0","V_disk":"0","V_bul":"10"}
        ]}"#,
    )
    .expect("parse syn_neg");
    let out_neg = eval_operation("sparc_pooled_primary_exact", syn_neg.as_object().unwrap())
        .expect("eval syn_neg");
    let obj_neg = out_neg.as_object().unwrap();
    assert_eq!(obj_neg["N_total"], JsonValue::Int(BigInt::from_i64(3)));
    assert_eq!(obj_neg["N_scored"], JsonValue::Int(BigInt::from_i64(2)));
    assert_eq!(
        obj_neg["MAPE_U_exact"],
        JsonValue::Array(vec![
            JsonValue::Str("79".to_string()),
            JsonValue::Str("2".to_string()),
        ])
    );
    assert_eq!(
        obj_neg["MAPE_U_8dp"],
        JsonValue::Str("39.50000000".to_string())
    );

    // Flipping V_gas sign (-3 -> +3) yields identical exact MAPE_U
    let syn_pos = parse_json(
        r#"{"bins":[
            {"r_kpc":"2","V_obs":"10","V_gas":"3","V_disk":"4","V_bul":"0"},
            {"r_kpc":"5","V_obs":"0","V_gas":"5","V_disk":"2","V_bul":"10"},
            {"r_kpc":"1","V_obs":"10","V_gas":"0","V_disk":"0","V_bul":"10"}
        ]}"#,
    )
    .expect("parse syn_pos");
    let out_pos = eval_operation("sparc_pooled_primary_exact", syn_pos.as_object().unwrap())
        .expect("eval syn_pos");
    assert_eq!(out_pos, out_neg);

    // All-zero V_obs bins must fail with ValueError
    let all_zero = parse_json(
        r#"{"bins":[{"r_kpc":"1","V_obs":"0","V_gas":"3","V_disk":"4","V_bul":"0"}]}"#,
    )
    .expect("parse all_zero");
    let err_zero = eval_operation("sparc_pooled_primary_exact", all_zero.as_object().unwrap());
    assert!(matches!(err_zero, Err(CoreError::ValueError(_))));

    // 2. Full 209-bin SD-008 golden vector check
    let root = repo_root();
    let (_, sd_rows) = load_vector_file(&root, SYMBOLIC_DISPLAY_REL).expect("load sd");
    let sd008 = sd_rows
        .iter()
        .find(|r| r.get("case_id") == Some(&JsonValue::Str("SD-008".to_string())))
        .expect("SD-008 present");
    verify_single_vector_with_root(sd008, &root).expect("SD-008 must verify cleanly");

    let out = eval_operation(
        "sparc_pooled_primary_exact",
        sd008["inputs"].as_object().unwrap(),
    )
    .expect("eval SD-008");
    let obj = out.as_object().unwrap();
    assert_eq!(obj["N_total"], JsonValue::Int(BigInt::from_i64(209)));
    assert_eq!(obj["N_scored"], JsonValue::Int(BigInt::from_i64(209)));
    assert_eq!(
        obj["MAPE_U_8dp"],
        JsonValue::Str("26.57055342".to_string())
    );
    let exact_pair = obj["MAPE_U_exact"].as_array().unwrap();
    assert_eq!(exact_pair.len(), 2);
    assert_eq!(exact_pair[0].as_str().unwrap().len(), 230);
    assert_eq!(exact_pair[1].as_str().unwrap().len(), 228);
    assert_eq!(
        obj["MAPE_U_exact"],
        sd008["expected_outcome"].as_object().unwrap()["exact_value"]
            .as_object()
            .unwrap()["MAPE_U_exact"]
    );
}

