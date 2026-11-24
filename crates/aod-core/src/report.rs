//! Deterministic canonical report builder (`aod.s4.rust.report.v1`),
//! host-path/timestamp error sanitizer, and portable-string validator.
//!
//! Guarantees zero timestamps, zero durations, zero absolute host paths,
//! zero temp-directory markers, zero volatile metadata, and zero floats.

use std::collections::BTreeMap;
use std::env;
use std::path::Path;

use crate::json::{to_canonical_json_pretty, JsonValue};
use crate::policy::PolicyAudit;
use crate::vectors::VectorsVerification;
use crate::{CoreError, BASE_COMMIT_BINDING, CRATE_NAME, CRATE_VERSION, REPORT_SCHEMA};

const FORBIDDEN_REPORT_KEYS: [&str; 20] = [
    "timestamp",
    "created_at",
    "started_at",
    "finished_at",
    "duration",
    "duration_s",
    "elapsed",
    "elapsed_s",
    "wall_clock",
    "pid",
    "hostname",
    "executable",
    "stdout",
    "stderr",
    "temp_dir",
    "rustc_version",
    "target_triple",
    "profile",
    "debug",
    "build_mode",
];

const UNIX_ABS_PREFIXES: [&str; 19] = [
    "home",
    "tmp",
    "var",
    "Users",
    "root",
    "opt",
    "usr",
    "etc",
    "private",
    "mnt",
    "srv",
    "proc",
    "sys",
    "workspace",
    "github",
    "app",
    "runner",
    "builds",
    "dev",
];

const TEMP_MARKERS: [&str; 4] = [
    "pytest-of-",
    "aod-anchor-scientific-replay-",
    "/tmp/",
    "\\Temp\\",
];

fn is_path_delim(b: u8) -> bool {
    matches!(
        b,
        b' ' | b'\t' | b'\r' | b'\n' | b'\'' | b'"' | b'(' | b'=' | b':' | b'[' | b'{' | b',' | b';'
    )
}

fn is_path_stop(b: u8) -> bool {
    matches!(
        b,
        b' ' | b'\t' | b'\r' | b'\n' | b'\'' | b'"' | b',' | b';' | b')' | b']' | b'}'
    )
}

fn is_iso_timestamp_start(bytes: &[u8], i: usize) -> bool {
    // YYYY-MM-DDTHH:MM:SS (19 bytes)
    if i + 19 > bytes.len() {
        return false;
    }
    if i > 0 && (bytes[i - 1].is_ascii_alphanumeric() || bytes[i - 1] == b'_') {
        return false;
    }
    bytes[i..i + 4].iter().all(|b| b.is_ascii_digit())
        && bytes[i + 4] == b'-'
        && bytes[i + 5..i + 7].iter().all(|b| b.is_ascii_digit())
        && bytes[i + 7] == b'-'
        && bytes[i + 8..i + 10].iter().all(|b| b.is_ascii_digit())
        && bytes[i + 10] == b'T'
        && bytes[i + 11..i + 13].iter().all(|b| b.is_ascii_digit())
        && bytes[i + 13] == b':'
        && bytes[i + 14..i + 16].iter().all(|b| b.is_ascii_digit())
        && bytes[i + 16] == b':'
        && bytes[i + 17..i + 19].iter().all(|b| b.is_ascii_digit())
}

fn is_win_abs_path_at(bytes: &[u8], i: usize) -> bool {
    if i + 3 > bytes.len() {
        return false;
    }
    if i > 0 && !is_path_delim(bytes[i - 1]) {
        return false;
    }
    bytes[i].is_ascii_alphabetic()
        && bytes[i + 1] == b':'
        && (bytes[i + 2] == b'\\' || bytes[i + 2] == b'/')
}

fn is_unix_abs_path_at(bytes: &[u8], i: usize) -> bool {
    if bytes.get(i) != Some(&b'/') {
        return false;
    }
    if i == 0 {
        // Leading `/` followed by path character or end
        return bytes.len() == 1 || !is_path_stop(bytes[1]);
    }
    if !is_path_delim(bytes[i - 1]) {
        return false;
    }
    let rest = &bytes[i + 1..];
    // Match known Unix root directory prefixes like `/home/...`, `/tmp/...`
    for prefix in UNIX_ABS_PREFIXES {
        let pb = prefix.as_bytes();
        if rest.starts_with(pb) {
            let after = rest.get(pb.len()).copied();
            if after.is_none() || after == Some(b'/') || after.map_or(false, is_path_stop) {
                return true;
            }
        }
    }
    // Match `/seg1/seg2` pattern
    let mut j = 0usize;
    while j < rest.len() && (rest[j].is_ascii_alphanumeric() || matches!(rest[j], b'.' | b'_' | b'-')) {
        j += 1;
    }
    if j > 0 && rest.get(j) == Some(&b'/') {
        let k = j + 1;
        if k < rest.len() && (rest[k].is_ascii_alphanumeric() || matches!(rest[k], b'.' | b'_' | b'-')) {
            return true;
        }
    }
    false
}

fn should_replace_raw_root(raw: &str) -> bool {
    let trimmed = raw.trim_end_matches(['/', '\\']);
    trimmed.len() >= 3 && (trimmed.contains('/') || trimmed.contains('\\'))
}

/// Scrub host absolute paths, executable paths, temp markers, and ISO timestamps from error text.
pub fn sanitize_error(message: &str, extra_roots: &[(&Path, &str)]) -> String {
    let mut replacements: Vec<(String, String)> = Vec::new();
    for &(path, label) in extra_roots {
        if let Ok(canon) = std::fs::canonicalize(path) {
            replacements.push((canon.to_string_lossy().into_owned(), label.to_string()));
        }
        let raw = path.to_string_lossy().into_owned();
        if should_replace_raw_root(&raw) {
            replacements.push((raw, label.to_string()));
        }
    }
    if let Ok(cwd) = env::current_dir() {
        if let Ok(canon) = std::fs::canonicalize(&cwd) {
            replacements.push((canon.to_string_lossy().into_owned(), "<CWD>".to_string()));
        }
        let raw = cwd.to_string_lossy().into_owned();
        if should_replace_raw_root(&raw) {
            replacements.push((raw, "<CWD>".to_string()));
        }
    }
    let tmp = env::temp_dir();
    if let Ok(canon) = std::fs::canonicalize(&tmp) {
        replacements.push((canon.to_string_lossy().into_owned(), "<TEMP_DIR>".to_string()));
    }
    let raw_tmp = tmp.to_string_lossy().into_owned();
    if should_replace_raw_root(&raw_tmp) {
        replacements.push((raw_tmp, "<TEMP_DIR>".to_string()));
    }
    if let Ok(exe) = env::current_exe() {
        if let Ok(canon) = std::fs::canonicalize(&exe) {
            replacements.push((canon.to_string_lossy().into_owned(), "<EXE>".to_string()));
        }
        let raw_exe = exe.to_string_lossy().into_owned();
        if should_replace_raw_root(&raw_exe) {
            replacements.push((raw_exe, "<EXE>".to_string()));
        }
    }

    // Replace longest non-trivial prefixes first.
    replacements.sort_by(|a, b| b.0.len().cmp(&a.0.len()).then(a.0.cmp(&b.0)));
    let mut sanitized = message.to_string();
    for (src, dst) in &replacements {
        let trimmed = src.trim_end_matches(['/', '\\']);
        if trimmed.len() < 3 || (!trimmed.contains('/') && !trimmed.contains('\\')) {
            continue;
        }
        if sanitized.contains(trimmed) {
            sanitized = sanitized.replace(trimmed, dst);
        }
    }

    // Scrub remaining temp markers, Windows/Unix absolute paths, and ISO timestamps.
    sanitized = scrub_patterns(&sanitized);
    let trimmed = sanitized.trim();
    if trimmed.is_empty() {
        "verification error".to_string()
    } else {
        trimmed.to_string()
    }
}

fn scrub_patterns(input: &str) -> String {
    let bytes = input.as_bytes();
    let mut out = String::with_capacity(input.len());
    let mut i = 0usize;
    while i < bytes.len() {
        if is_iso_timestamp_start(bytes, i) {
            out.push_str("<TIMESTAMP>");
            i += 19;
            // Optional fractional seconds & timezone suffix
            if i < bytes.len() && bytes[i] == b'.' {
                i += 1;
                while i < bytes.len() && bytes[i].is_ascii_digit() {
                    i += 1;
                }
            }
            if i < bytes.len() && bytes[i] == b'Z' {
                i += 1;
            } else if i + 3 <= bytes.len()
                && matches!(bytes[i], b'+' | b'-')
                && bytes[i + 1].is_ascii_digit()
                && bytes[i + 2].is_ascii_digit()
            {
                i += 3;
                if i < bytes.len() && bytes[i] == b':' {
                    i += 1;
                }
                if i + 2 <= bytes.len()
                    && bytes[i].is_ascii_digit()
                    && bytes[i + 1].is_ascii_digit()
                {
                    i += 2;
                }
            }
            continue;
        }

        let mut matched_temp = false;
        for marker in TEMP_MARKERS {
            if input[i..].starts_with(marker) {
                out.push_str("<TEMP_PATH>");
                i += marker.len();
                while i < bytes.len() && !is_path_stop(bytes[i]) {
                    i += 1;
                }
                matched_temp = true;
                break;
            }
        }
        if matched_temp {
            continue;
        }

        if is_win_abs_path_at(bytes, i) || is_unix_abs_path_at(bytes, i) {
            out.push_str("<HOST_PATH>");
            while i < bytes.len() && !is_path_stop(bytes[i]) {
                i += 1;
            }
            continue;
        }

        let ch = input[i..].chars().next().unwrap_or(' ');
        out.push(ch);
        i += ch.len_utf8();
    }
    out
}

fn check_portable_string(s: &str, path: &str) -> Result<(), CoreError> {
    let bytes = s.as_bytes();
    for i in 0..bytes.len() {
        if is_iso_timestamp_start(bytes, i) {
            return Err(CoreError::ValueError(format!(
                "timestamp leaked in canonical report at {}",
                path
            )));
        }
        if is_win_abs_path_at(bytes, i) {
            return Err(CoreError::ValueError(format!(
                "absolute Windows path leaked in canonical report at {}",
                path
            )));
        }
        if is_unix_abs_path_at(bytes, i) {
            return Err(CoreError::ValueError(format!(
                "absolute Unix path leaked in canonical report at {}",
                path
            )));
        }
    }
    for marker in TEMP_MARKERS {
        if s.contains(marker) {
            return Err(CoreError::ValueError(format!(
                "temporary directory marker leaked in canonical report at {}",
                path
            )));
        }
    }
    Ok(())
}

/// Recursively verify that a canonical report contains zero volatile keys,
/// zero absolute host paths, zero temp markers, and zero ISO timestamps.
pub fn validate_portable_report(value: &JsonValue, path: &str) -> Result<(), CoreError> {
    match value {
        JsonValue::Object(map) => {
            for (k, v) in map {
                if FORBIDDEN_REPORT_KEYS.contains(&k.as_str()) {
                    return Err(CoreError::ValueError(format!(
                        "forbidden volatile report key {:?} at {}",
                        k, path
                    )));
                }
                check_portable_string(k, &format!("{}.<key:{}>", path, k))?;
                validate_portable_report(v, &format!("{}.{}", path, k))?;
            }
        }
        JsonValue::Array(items) => {
            for (idx, item) in items.iter().enumerate() {
                validate_portable_report(item, &format!("{}[{}]", path, idx))?;
            }
        }
        JsonValue::Str(s) => {
            check_portable_string(s, path)?;
        }
        JsonValue::Null | JsonValue::Bool(_) | JsonValue::Int(_) => {}
    }
    Ok(())
}

fn not_requested_section() -> JsonValue {
    let mut m = BTreeMap::new();
    m.insert("status".to_string(), JsonValue::Str("NOT_REQUESTED".to_string()));
    JsonValue::Object(m)
}

/// Assemble and validate a deterministic canonical `aod.s4.rust.report.v1` JSON document.
pub fn build_report(
    vectors: Option<&VectorsVerification>,
    vectors_error: Option<&str>,
    policy: Option<&PolicyAudit>,
    policy_error: Option<&str>,
) -> Result<(JsonValue, bool), CoreError> {
    let mut any_fail = false;

    let vectors_json = if let Some(v) = vectors {
        if v.status != "PASS" {
            any_fail = true;
        }
        v.to_json()
    } else if let Some(err) = vectors_error {
        any_fail = true;
        let mut fail_rec = BTreeMap::new();
        fail_rec.insert("case_id".to_string(), JsonValue::Str("LOADER".to_string()));
        fail_rec.insert("error".to_string(), JsonValue::Str(err.to_string()));
        let mut digests = BTreeMap::new();
        digests.insert("error".to_string(), JsonValue::Str("0".repeat(64)));
        let mut m = BTreeMap::new();
        m.insert("status".to_string(), JsonValue::Str("FAIL".to_string()));
        m.insert("rational_core_count".to_string(), JsonValue::Int(crate::bigint::BigInt::zero()));
        m.insert("symbolic_and_display_count".to_string(), JsonValue::Int(crate::bigint::BigInt::zero()));
        m.insert("total_vectors".to_string(), JsonValue::Int(crate::bigint::BigInt::zero()));
        m.insert("passed_vectors".to_string(), JsonValue::Int(crate::bigint::BigInt::zero()));
        m.insert("failed_vectors".to_string(), JsonValue::Int(crate::bigint::BigInt::zero()));
        m.insert("file_digests".to_string(), JsonValue::Object(digests));
        m.insert("failures".to_string(), JsonValue::Array(vec![JsonValue::Object(fail_rec)]));
        JsonValue::Object(m)
    } else {
        not_requested_section()
    };

    let policy_json = if let Some(p) = policy {
        if p.status != "PASS" {
            any_fail = true;
        }
        p.to_json()
    } else if let Some(err) = policy_error {
        any_fail = true;
        let mut m = BTreeMap::new();
        m.insert("status".to_string(), JsonValue::Str("FAIL".to_string()));
        m.insert("error".to_string(), JsonValue::Str(err.to_string()));
        JsonValue::Object(m)
    } else {
        not_requested_section()
    };

    let overall_status = if any_fail { "FAIL" } else { "PASS" };

    let mut report = BTreeMap::new();
    report.insert("schema".to_string(), JsonValue::Str(REPORT_SCHEMA.to_string()));
    report.insert("crate_name".to_string(), JsonValue::Str(CRATE_NAME.to_string()));
    report.insert("crate_version".to_string(), JsonValue::Str(CRATE_VERSION.to_string()));
    report.insert(
        "base_commit_binding".to_string(),
        JsonValue::Str(BASE_COMMIT_BINDING.to_string()),
    );
    report.insert(
        "overall_status".to_string(),
        JsonValue::Str(overall_status.to_string()),
    );
    report.insert("vectors_verification".to_string(), vectors_json);
    report.insert("policy_audit".to_string(), policy_json);

    let root = JsonValue::Object(report);
    validate_portable_report(&root, "$")?;
    Ok((root, !any_fail))
}

pub fn serialize_report(report: &JsonValue) -> Result<String, CoreError> {
    validate_portable_report(report, "$")?;
    Ok(to_canonical_json_pretty(report))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sanitize_and_portable_guard() {
        let dirty = "failed at /home/alice/project/file.rs on 2026-11-24T05:37:35Z in /tmp/pytest-of-bob/x and C:\\Users\\alice\\x";
        let clean = sanitize_error(dirty, &[]);
        assert!(!clean.contains("/home/"));
        assert!(!clean.contains("/tmp/"));
        assert!(!clean.contains("pytest-of-"));
        assert!(!clean.contains("2026-11-24T"));
        assert!(!clean.contains("C:\\"));
        assert!(validate_portable_report(&JsonValue::Str(clean), "$").is_ok());

        // Hostile source_binding paths (standalone or semicolon-delimited) must be scrubbed cleanly
        let hostile = sanitize_error(
            "ValueError: absolute path forbidden in source_binding: \"/etc/passwd\"",
            &[],
        );
        assert!(!hostile.contains("/etc/passwd"));
        assert!(hostile.contains("<HOST_PATH>"));
        assert!(validate_portable_report(&JsonValue::Str(hostile), "$").is_ok());

        let hostile_semi = sanitize_error(
            "ValueError: empty component in \"a.csv;/etc/passwd;b.csv\"",
            &[],
        );
        assert!(!hostile_semi.contains("/etc/passwd"));
        assert!(validate_portable_report(&JsonValue::Str(hostile_semi), "$").is_ok());

        // Portable guard rejects leaks
        assert!(validate_portable_report(&JsonValue::Str("/home/alice/x".to_string()), "$").is_err());
        assert!(validate_portable_report(&JsonValue::Str("/etc/passwd".to_string()), "$").is_err());
        assert!(validate_portable_report(&JsonValue::Str("2026-11-24T05:37:35Z".to_string()), "$").is_err());
        let mut bad_obj = BTreeMap::new();
        bad_obj.insert("timestamp".to_string(), JsonValue::Str("now".to_string()));
        assert!(validate_portable_report(&JsonValue::Object(bad_obj), "$").is_err());
    }
}
