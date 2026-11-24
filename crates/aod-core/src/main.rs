#![forbid(unsafe_code)]

//! `aod-core` CLI entry point, argument parser, and pre-resolution runtime output path guard.
//!
//! Exit codes:
//! - `0`: PASS (or `--help` / `--version`)
//! - `1`: vector verification, policy audit, or `--eval-op` failure
//! - `2`: CLI argument usage error or unsafe `--report` path

use std::env;
use std::fs;
use std::io::{self, Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process::ExitCode;

use aod_core::json::{parse_json, to_canonical_json_pretty, JsonValue};
use aod_core::ops::eval_operation;
use aod_core::policy::audit_crate_tree;
use aod_core::report::{build_report, sanitize_error, serialize_report};
use aod_core::vectors::{verify_all_vectors, RATIONAL_CORE_REL};
use aod_core::{CoreError, CRATE_NAME, CRATE_VERSION};

const ALLOWED_IN_REPO_OUTPUT_ROOTS: [&str; 4] = ["_build", "build", "dist", "release"];

struct CliArgs {
    verify_vectors: bool,
    check_zero_float: bool,
    eval_op: Option<String>,
    input_json: Option<String>,
    input_stdin: bool,
    repo_root: Option<PathBuf>,
    crate_root: Option<PathBuf>,
    report: Option<PathBuf>,
    show_help: bool,
    show_version: bool,
}

fn usage_text() -> &'static str {
    "Usage: aod-core [OPTIONS]\n\
     \n\
     Options:\n\
       --verify-vectors      Verify all 30 S4 golden vectors (RC-001..RC-024 + SD-001..SD-006)\n\
       --check-zero-float    Run lexical zero-float / zero-unsafe / zero-dep crate policy audit\n\
       --eval-op <OP>        Evaluate a single exact operation against JSON inputs\n\
       --input-json <JSON>   Inline zero-float JSON object input for --eval-op\n\
       --input-stdin         Read zero-float JSON object input for --eval-op from stdin\n\
       --repo-root <PATH>    Repository root containing manual/engine/vectors/\n\
       --crate-root <PATH>   Crate root directory to audit (defaults to <repo-root>/crates/aod-core)\n\
       --report <PATH>       Write canonical JSON output (outside distributable repo dirs or under _build/)\n\
       -h, --help            Print help and exit 0\n\
       -V, --version         Print version and exit 0\n"
}

fn parse_cli_args(args: &[String]) -> Result<CliArgs, String> {
    let mut parsed = CliArgs {
        verify_vectors: false,
        check_zero_float: false,
        eval_op: None,
        input_json: None,
        input_stdin: false,
        repo_root: None,
        crate_root: None,
        report: None,
        show_help: false,
        show_version: false,
    };

    let mut i = 0usize;
    while i < args.len() {
        let arg = args[i].as_str();
        match arg {
            "-h" | "--help" => {
                parsed.show_help = true;
            }
            "-V" | "--version" => {
                parsed.show_version = true;
            }
            "--verify-vectors" => {
                parsed.verify_vectors = true;
            }
            "--check-zero-float" => {
                parsed.check_zero_float = true;
            }
            "--input-stdin" => {
                parsed.input_stdin = true;
            }
            "--eval-op" => {
                if parsed.eval_op.is_some() {
                    return Err("duplicate flag --eval-op".to_string());
                }
                i += 1;
                let val = args
                    .get(i)
                    .ok_or_else(|| "missing value for --eval-op".to_string())?;
                parsed.eval_op = Some(val.clone());
            }
            "--input-json" => {
                if parsed.input_json.is_some() {
                    return Err("duplicate flag --input-json".to_string());
                }
                i += 1;
                let val = args
                    .get(i)
                    .ok_or_else(|| "missing value for --input-json".to_string())?;
                parsed.input_json = Some(val.clone());
            }
            "--repo-root" => {
                if parsed.repo_root.is_some() {
                    return Err("duplicate flag --repo-root".to_string());
                }
                i += 1;
                let val = args
                    .get(i)
                    .ok_or_else(|| "missing value for --repo-root".to_string())?;
                parsed.repo_root = Some(PathBuf::from(val));
            }
            "--crate-root" => {
                if parsed.crate_root.is_some() {
                    return Err("duplicate flag --crate-root".to_string());
                }
                i += 1;
                let val = args
                    .get(i)
                    .ok_or_else(|| "missing value for --crate-root".to_string())?;
                parsed.crate_root = Some(PathBuf::from(val));
            }
            "--report" => {
                if parsed.report.is_some() {
                    return Err("duplicate flag --report".to_string());
                }
                i += 1;
                let val = args
                    .get(i)
                    .ok_or_else(|| "missing value for --report".to_string())?;
                parsed.report = Some(PathBuf::from(val));
            }
            other => {
                return Err(format!("unknown argument: {:?}", other));
            }
        }
        i += 1;
    }

    if parsed.show_help || parsed.show_version {
        return Ok(parsed);
    }

    if parsed.eval_op.is_some() {
        if parsed.verify_vectors || parsed.check_zero_float {
            return Err(
                "--eval-op cannot be combined with --verify-vectors or --check-zero-float"
                    .to_string(),
            );
        }
        if parsed.input_json.is_some() == parsed.input_stdin {
            return Err(
                "--eval-op requires exactly one of --input-json <JSON> or --input-stdin"
                    .to_string(),
            );
        }
    } else {
        if parsed.input_json.is_some() || parsed.input_stdin {
            return Err(
                "--input-json and --input-stdin require --eval-op <OP>".to_string(),
            );
        }
        if !parsed.verify_vectors && !parsed.check_zero_float {
            return Err(
                "specify at least one action (--verify-vectors, --check-zero-float, or --eval-op)"
                    .to_string(),
            );
        }
    }

    Ok(parsed)
}

fn find_repo_root_from(start: &Path) -> Option<PathBuf> {
    let mut cur = start.to_path_buf();
    loop {
        if cur.join(RATIONAL_CORE_REL).is_file() {
            return Some(cur);
        }
        if !cur.pop() {
            return None;
        }
    }
}

fn default_repo_root() -> Option<PathBuf> {
    if let Ok(cwd) = env::current_dir() {
        if let Some(found) = find_repo_root_from(&cwd) {
            return Some(found);
        }
    }
    if let Ok(exe) = env::current_exe() {
        if let Some(parent) = exe.parent() {
            if let Some(found) = find_repo_root_from(parent) {
                return Some(found);
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Pre-resolution symlink & distributable-repo runtime output path guard
// Mirrors manual/engine/cli.py:validate_runtime_output_path strictly.
// ---------------------------------------------------------------------------

fn lexical_normalize(path: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for comp in path.components() {
        match comp {
            Component::Prefix(p) => out.push(p.as_os_str()),
            Component::RootDir => out.push(comp.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                let can_pop = matches!(out.components().next_back(), Some(Component::Normal(_)));
                if can_pop {
                    out.pop();
                } else if !out.has_root() {
                    out.push("..");
                }
            }
            Component::Normal(seg) => out.push(seg),
        }
    }
    out
}

fn path_within_lexical(path: &Path, root: &Path) -> bool {
    let norm_path = lexical_normalize(path);
    let norm_root = lexical_normalize(root);
    norm_path.starts_with(&norm_root)
}

fn reject_pre_resolution_symlinks(
    raw_path: &Path,
    guarded_roots: &[PathBuf],
    cwd: &Path,
) -> Result<(), CoreError> {
    let lexical_abs = if raw_path.is_absolute() {
        raw_path.to_path_buf()
    } else {
        cwd.join(raw_path)
    };

    if let Ok(meta) = fs::symlink_metadata(&lexical_abs) {
        if meta.file_type().is_symlink() {
            return Err(CoreError::UnsafePath(
                "--report target must not be a symlink".to_string(),
            ));
        }
    }

    // Walk every lexical prefix BEFORE canonicalization so symlinks like _build/escape -> /tmp
    // are caught before resolution can leave the repository tree.
    let mut cur = PathBuf::new();
    for comp in lexical_abs.components() {
        match comp {
            Component::Prefix(p) => cur.push(p.as_os_str()),
            Component::RootDir => cur.push(comp.as_os_str()),
            Component::CurDir => continue,
            Component::ParentDir => {
                cur.pop();
                continue;
            }
            Component::Normal(seg) => {
                cur.push(seg);
                if let Ok(meta) = fs::symlink_metadata(&cur) {
                    if meta.file_type().is_symlink() {
                        let cur_in_resolved_parent = cur
                            .parent()
                            .and_then(|p| fs::canonicalize(p).ok())
                            .map(|rp| rp.join(seg));
                        let inside_guarded = guarded_roots.iter().any(|r| {
                            path_within_lexical(&cur, r)
                                || cur_in_resolved_parent
                                    .as_ref()
                                    .map_or(false, |cp| path_within_lexical(cp, r))
                        });
                        if inside_guarded {
                            return Err(CoreError::UnsafePath(format!(
                                "--report must not traverse symlink {:?} inside repository",
                                seg.to_string_lossy()
                            )));
                        }
                    }
                }
            }
        }
    }
    Ok(())
}

/// Resolve a path that may contain non-existent trailing components, matching Python `Path.resolve()`.
fn resolve_like_python(path: &Path) -> PathBuf {
    let mut resolved = PathBuf::new();
    for comp in path.components() {
        match comp {
            Component::Prefix(p) => resolved.push(p.as_os_str()),
            Component::RootDir => resolved.push(comp.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                let can_pop = matches!(resolved.components().next_back(), Some(Component::Normal(_)));
                if can_pop {
                    resolved.pop();
                }
            }
            Component::Normal(seg) => {
                resolved.push(seg);
                if fs::symlink_metadata(&resolved).is_ok() {
                    if let Ok(canon) = fs::canonicalize(&resolved) {
                        resolved = canon;
                    }
                }
            }
        }
    }
    resolved
}

fn validate_runtime_output_path(
    raw_path: &Path,
    guarded_roots: &[PathBuf],
) -> Result<PathBuf, CoreError> {
    if raw_path.as_os_str().is_empty() {
        return Err(CoreError::UnsafePath(
            "--report path must not be empty".to_string(),
        ));
    }
    let cwd = env::current_dir()?;
    let mut resolved_roots: Vec<PathBuf> = Vec::new();
    for r in guarded_roots {
        let canon = fs::canonicalize(r).unwrap_or_else(|_| lexical_normalize(r));
        if !resolved_roots.contains(&canon) {
            resolved_roots.push(canon);
        }
    }

    reject_pre_resolution_symlinks(raw_path, &resolved_roots, &cwd)?;

    let abs_input = if raw_path.is_absolute() {
        raw_path.to_path_buf()
    } else {
        cwd.join(raw_path)
    };
    let candidate = resolve_like_python(&abs_input);

    for guarded in &resolved_roots {
        if let Ok(rel) = candidate.strip_prefix(guarded) {
            let parts: Vec<String> = rel
                .components()
                .filter_map(|c| match c {
                    Component::Normal(s) => Some(s.to_string_lossy().into_owned()),
                    _ => None,
                })
                .collect();
            if parts.len() < 2
                || !ALLOWED_IN_REPO_OUTPUT_ROOTS.contains(&parts[0].as_str())
            {
                return Err(CoreError::UnsafePath(format!(
                    "--report target {:?} is inside a distributable repository directory; write outside the repository or under _build/",
                    parts.join("/")
                )));
            }
            // Re-check symlinks along resolved relative segments inside guarded root.
            let mut walk = guarded.clone();
            for part in &parts {
                walk.push(part);
                if let Ok(meta) = fs::symlink_metadata(&walk) {
                    if meta.file_type().is_symlink() {
                        return Err(CoreError::UnsafePath(
                            "--report must not traverse symlinks inside repository".to_string(),
                        ));
                    }
                }
            }
        }
    }

    if let Ok(meta) = fs::symlink_metadata(&candidate) {
        if meta.file_type().is_symlink() {
            return Err(CoreError::UnsafePath(
                "--report target must not be a symlink".to_string(),
            ));
        }
        if meta.is_dir() {
            return Err(CoreError::UnsafePath(
                "--report target already exists as a directory".to_string(),
            ));
        }
    }

    // Verify nearest existing ancestor is a directory (reject writing under a regular file).
    let mut anc = candidate.parent();
    while let Some(p) = anc {
        if let Ok(meta) = fs::symlink_metadata(p) {
            if !meta.is_dir() {
                return Err(CoreError::UnsafePath(
                    "--report parent path exists as a non-directory file".to_string(),
                ));
            }
            break;
        }
        anc = p.parent();
    }

    Ok(candidate)
}

fn write_output(report_path: Option<&Path>, content: &str) -> Result<(), CoreError> {
    if let Some(path) = report_path {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent)?;
            }
        }
        fs::write(path, content.as_bytes())?;
    } else {
        let mut stdout = io::stdout().lock();
        stdout.write_all(content.as_bytes())?;
        stdout.flush()?;
    }
    Ok(())
}

fn run() -> u8 {
    let raw_args: Vec<String> = env::args().skip(1).collect();
    let cli = match parse_cli_args(&raw_args) {
        Ok(c) => c,
        Err(msg) => {
            let _ = writeln!(io::stderr(), "error: {}", msg);
            return 2;
        }
    };

    if cli.show_help {
        let _ = write!(io::stdout(), "{}", usage_text());
        return 0;
    }
    if cli.show_version {
        let _ = writeln!(io::stdout(), "{} {}", CRATE_NAME, CRATE_VERSION);
        return 0;
    }

    let default_repo = default_repo_root();
    let repo_root = cli
        .repo_root
        .clone()
        .or_else(|| default_repo.clone())
        .unwrap_or_else(|| env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));

    let crate_root = cli
        .crate_root
        .clone()
        .unwrap_or_else(|| repo_root.join("crates").join("aod-core"));

    let mut guarded_roots: Vec<PathBuf> = vec![repo_root.clone()];
    if let Some(ref def) = default_repo {
        guarded_roots.push(def.clone());
    }
    if let Some(parent) = crate_root.parent().and_then(|p| p.parent()) {
        if parent.join(RATIONAL_CORE_REL).is_file() {
            guarded_roots.push(parent.to_path_buf());
        }
    }

    let report_path: Option<PathBuf> = match cli.report.as_deref() {
        Some(raw) => match validate_runtime_output_path(raw, &guarded_roots) {
            Ok(p) => Some(p),
            Err(err) => {
                let _ = writeln!(io::stderr(), "error: {}", err.message());
                return 2;
            }
        },
        None => None,
    };

    // Single-operation evaluation mode (`--eval-op`)
    if let Some(op_name) = cli.eval_op.as_deref() {
        let raw_json = if let Some(s) = cli.input_json {
            s
        } else {
            let mut buf = String::new();
            if let Err(err) = io::stdin().read_to_string(&mut buf) {
                let _ = writeln!(io::stderr(), "error (Io): {}", err);
                return 1;
            }
            buf
        };
        let parsed = match parse_json(&raw_json) {
            Ok(v) => v,
            Err(err) => {
                let _ = writeln!(io::stderr(), "error ({}): {}", err.kind_name(), err.message());
                return 1;
            }
        };
        let inputs = match parsed {
            JsonValue::Object(m) => m,
            other => {
                let _ = writeln!(
                    io::stderr(),
                    "error (TypeError): --eval-op input must be a JSON object, got {}",
                    other.type_name()
                );
                return 1;
            }
        };
        match eval_operation(op_name, &inputs) {
            Ok(result) => {
                let text = to_canonical_json_pretty(&result);
                if let Err(err) = write_output(report_path.as_deref(), &text) {
                    let _ = writeln!(io::stderr(), "error ({}): {}", err.kind_name(), err.message());
                    return 1;
                }
                return 0;
            }
            Err(err) => {
                let _ = writeln!(io::stderr(), "error ({}): {}", err.kind_name(), err.message());
                return 1;
            }
        }
    }

    let extra_roots: [(&Path, &str); 2] = [
        (repo_root.as_path(), "<REPO_ROOT>"),
        (crate_root.as_path(), "<CRATE_ROOT>"),
    ];

    // Vector verification
    let mut vec_ok = None;
    let mut vec_err: Option<String> = None;
    if cli.verify_vectors {
        match verify_all_vectors(&repo_root) {
            Ok(mut res) => {
                for f in &mut res.failures {
                    f.error = sanitize_error(&f.error, &extra_roots);
                }
                vec_ok = Some(res);
            }
            Err(err) => {
                vec_err = Some(sanitize_error(&err.to_string(), &extra_roots));
            }
        }
    }

    // Zero-float / policy audit
    let mut pol_ok = None;
    let mut pol_err: Option<String> = None;
    if cli.check_zero_float {
        match audit_crate_tree(&crate_root) {
            Ok(mut res) => {
                for v in &mut res.violations {
                    v.detail = sanitize_error(&v.detail, &extra_roots);
                }
                pol_ok = Some(res);
            }
            Err(err) => {
                pol_err = Some(sanitize_error(&err.to_string(), &extra_roots));
            }
        }
    }

    let (report_val, passed) = match build_report(
        vec_ok.as_ref(),
        vec_err.as_deref(),
        pol_ok.as_ref(),
        pol_err.as_deref(),
    ) {
        Ok(pair) => pair,
        Err(err) => {
            let clean = sanitize_error(&err.to_string(), &extra_roots);
            let _ = writeln!(io::stderr(), "error: failed to build portable report: {}", clean);
            return 1;
        }
    };

    let canonical_text = match serialize_report(&report_val) {
        Ok(s) => s,
        Err(err) => {
            let clean = sanitize_error(&err.to_string(), &extra_roots);
            let _ = writeln!(io::stderr(), "error: failed to serialize report: {}", clean);
            return 1;
        }
    };

    if let Err(err) = write_output(report_path.as_deref(), &canonical_text) {
        let clean = sanitize_error(&err.to_string(), &extra_roots);
        let _ = writeln!(io::stderr(), "error: failed to write report: {}", clean);
        return 1;
    }

    if !passed && report_path.is_some() {
        if let Some(ref e) = vec_err {
            let _ = writeln!(io::stderr(), "FAIL vectors: {}", e);
        } else if let Some(ref v) = vec_ok {
            if v.status != "PASS" {
                let _ = writeln!(
                    io::stderr(),
                    "FAIL vectors: {} of {} failed",
                    v.failed_vectors, v.total_vectors
                );
            }
        }
        if let Some(ref e) = pol_err {
            let _ = writeln!(io::stderr(), "FAIL policy: {}", e);
        } else if let Some(ref p) = pol_ok {
            if p.status != "PASS" {
                let _ = writeln!(
                    io::stderr(),
                    "FAIL policy: {} violations",
                    p.violation_count
                );
            }
        }
    }

    if passed {
        0
    } else {
        1
    }
}

fn main() -> ExitCode {
    ExitCode::from(run())
}
