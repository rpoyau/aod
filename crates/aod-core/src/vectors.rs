//! JSONL golden vector loader, `aod.s4.vector.v1` schema validator, and 30-vector runner.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;

use crate::bigint::BigInt;
use crate::json::{parse_json, JsonValue};
use crate::ops::{eval_operation, verify_reject_operation};
use crate::sha256::sha256_hex;
use crate::{CoreError, VECTOR_SCHEMA};

pub const RATIONAL_CORE_REL: &str = "manual/engine/vectors/rational_core.jsonl";
pub const SYMBOLIC_DISPLAY_REL: &str = "manual/engine/vectors/symbolic_and_display.jsonl";

const REQUIRED_VECTOR_KEYS: [&str; 11] = [
    "case_id",
    "domain",
    "evidence_role",
    "expected_outcome",
    "inputs",
    "integer_encoding",
    "operation",
    "oracle_basis",
    "schema_version",
    "scientific_status",
    "source_binding",
];

const VALID_SCIENTIFIC_STATUSES: [&str; 4] = [
    "AUTHENTICATED_EXACT",
    "CONFORMANT_DECLARED_FIXTURE",
    "RETAINED_DATA_CONFORMANT",
    "UNRESOLVED_PROVENANCE_QUARANTINED",
];

const VALID_RUST_INT_TYPES: [&str; 4] = ["i32", "i64", "i128", "BigInt"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VectorFailure {
    pub case_id: String,
    pub error: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VectorsVerification {
    pub status: String,
    pub rational_core_count: usize,
    pub symbolic_and_display_count: usize,
    pub total_vectors: usize,
    pub passed_vectors: usize,
    pub failed_vectors: usize,
    pub file_digests: BTreeMap<String, String>,
    pub failures: Vec<VectorFailure>,
}

impl VectorsVerification {
    pub fn to_json(&self) -> JsonValue {
        let mut digests = BTreeMap::new();
        for (k, v) in &self.file_digests {
            digests.insert(k.clone(), JsonValue::Str(v.clone()));
        }
        let failures = self
            .failures
            .iter()
            .map(|f| {
                let mut m = BTreeMap::new();
                m.insert("case_id".to_string(), JsonValue::Str(f.case_id.clone()));
                m.insert("error".to_string(), JsonValue::Str(f.error.clone()));
                JsonValue::Object(m)
            })
            .collect();
        let mut out = BTreeMap::new();
        out.insert("status".to_string(), JsonValue::Str(self.status.clone()));
        out.insert(
            "rational_core_count".to_string(),
            JsonValue::Int(BigInt::from_usize(self.rational_core_count)),
        );
        out.insert(
            "symbolic_and_display_count".to_string(),
            JsonValue::Int(BigInt::from_usize(self.symbolic_and_display_count)),
        );
        out.insert(
            "total_vectors".to_string(),
            JsonValue::Int(BigInt::from_usize(self.total_vectors)),
        );
        out.insert(
            "passed_vectors".to_string(),
            JsonValue::Int(BigInt::from_usize(self.passed_vectors)),
        );
        out.insert(
            "failed_vectors".to_string(),
            JsonValue::Int(BigInt::from_usize(self.failed_vectors)),
        );
        out.insert("file_digests".to_string(), JsonValue::Object(digests));
        out.insert("failures".to_string(), JsonValue::Array(failures));
        JsonValue::Object(out)
    }
}

fn read_repo_rel_no_symlink(repo_root: &Path, rel_posix: &str) -> Result<Vec<u8>, CoreError> {
    let mut cur = repo_root.to_path_buf();
    for seg in rel_posix.split('/') {
        if seg.is_empty() || seg == "." || seg == ".." {
            return Err(CoreError::UnsafePath(format!(
                "unsafe relative vector path: {:?}",
                rel_posix
            )));
        }
        cur.push(seg);
        let meta = fs::symlink_metadata(&cur).map_err(|_| {
            CoreError::Io(format!("vector file or parent missing: {}", rel_posix))
        })?;
        if meta.file_type().is_symlink() {
            return Err(CoreError::UnsafePath(format!(
                "symlink forbidden along vector path: {}",
                rel_posix
            )));
        }
    }
    let meta = fs::symlink_metadata(&cur)?;
    if !meta.is_file() {
        return Err(CoreError::Io(format!(
            "vector path is not a regular file: {}",
            rel_posix
        )));
    }
    Ok(fs::read(&cur)?)
}

fn require_non_empty_str<'a>(
    obj: &'a BTreeMap<String, JsonValue>,
    field: &str,
) -> Result<&'a str, CoreError> {
    match obj.get(field) {
        Some(JsonValue::Str(s)) if !s.is_empty() => Ok(s.as_str()),
        _ => Err(CoreError::ValueError(format!(
            "vector {} must be non-empty str",
            field
        ))),
    }
}

/// Strictly validate a single parsed JSONL record against `aod.s4.vector.v1`.
pub fn validate_vector_record(record: &JsonValue) -> Result<(), CoreError> {
    let obj = record
        .as_object()
        .ok_or_else(|| CoreError::ValueError("vector record must be a JSON object".to_string()))?;

    let expected_keys: BTreeSet<&str> = REQUIRED_VECTOR_KEYS.iter().copied().collect();
    let actual_keys: BTreeSet<&str> = obj.keys().map(String::as_str).collect();
    if actual_keys != expected_keys {
        let missing: Vec<&str> = expected_keys.difference(&actual_keys).copied().collect();
        let extra: Vec<&str> = actual_keys.difference(&expected_keys).copied().collect();
        return Err(CoreError::ValueError(format!(
            "vector record key mismatch: missing={:?}, extra={:?}",
            missing, extra
        )));
    }

    let sv = require_non_empty_str(obj, "schema_version")?;
    if sv != VECTOR_SCHEMA {
        return Err(CoreError::ValueError(format!(
            "unexpected vector schema_version: {:?}",
            sv
        )));
    }
    for field in [
        "case_id",
        "source_binding",
        "operation",
        "domain",
        "evidence_role",
        "oracle_basis",
    ] {
        let _ = require_non_empty_str(obj, field)?;
    }
    if obj.get("oracle_basis").and_then(JsonValue::as_str) == Some("candidate_snapshot") {
        return Err(CoreError::ValueError(
            "circular candidate_snapshot oracle_basis is forbidden".to_string(),
        ));
    }
    let sci = require_non_empty_str(obj, "scientific_status")?;
    if !VALID_SCIENTIFIC_STATUSES.contains(&sci) {
        return Err(CoreError::ValueError(format!(
            "invalid vector scientific_status: {:?}",
            sci
        )));
    }
    if obj.get("inputs").and_then(JsonValue::as_object).is_none() {
        return Err(CoreError::ValueError(
            "vector inputs must be a JSON object".to_string(),
        ));
    }

    let exp = obj
        .get("expected_outcome")
        .and_then(JsonValue::as_object)
        .ok_or_else(|| CoreError::ValueError("invalid expected_outcome".to_string()))?;
    match exp.get("status").and_then(JsonValue::as_str) {
        Some("OK") => {
            if !exp.contains_key("exact_value") {
                return Err(CoreError::ValueError(
                    "OK expected_outcome requires exact_value".to_string(),
                ));
            }
        }
        Some("REJECT") => {
            let _ = require_non_empty_str(exp, "expected_error_class")?;
            let _ = require_non_empty_str(exp, "expected_status")?;
        }
        _ => {
            return Err(CoreError::ValueError(
                "expected_outcome.status must be 'OK' or 'REJECT'".to_string(),
            ));
        }
    }

    let enc = obj
        .get("integer_encoding")
        .and_then(JsonValue::as_object)
        .ok_or_else(|| CoreError::ValueError("integer_encoding must be a JSON object".to_string()))?;
    let rust_ty = require_non_empty_str(enc, "rust_min_int_type")?;
    if !VALID_RUST_INT_TYPES.contains(&rust_ty) {
        return Err(CoreError::ValueError(format!(
            "invalid rust_min_int_type: {:?}",
            rust_ty
        )));
    }
    let digits = enc
        .get("max_abs_integer_digits")
        .and_then(JsonValue::as_int)
        .ok_or_else(|| {
            CoreError::TypeError("max_abs_integer_digits must be an exact int".to_string())
        })?;
    if !digits.is_positive() {
        return Err(CoreError::ValueError(
            "max_abs_integer_digits must be >= 1".to_string(),
        ));
    }
    let _ = require_non_empty_str(enc, "overflow_note")?;
    Ok(())
}

/// Load and validate one JSONL golden vector file with zero-float parsing and raw-byte SHA-256.
pub fn load_vector_file(
    repo_root: &Path,
    rel_posix: &str,
) -> Result<(String, Vec<BTreeMap<String, JsonValue>>), CoreError> {
    let raw_bytes = read_repo_rel_no_symlink(repo_root, rel_posix)?;
    let digest = sha256_hex(&raw_bytes);
    let text = String::from_utf8(raw_bytes).map_err(|_| {
        CoreError::ValueError(format!("non-UTF-8 bytes in vector file {}", rel_posix))
    })?;
    let mut records = Vec::new();
    for (idx, line) in text.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let parsed = parse_json(line).map_err(|e| {
            CoreError::ValueError(format!("{}:L{}: {}", rel_posix, idx + 1, e))
        })?;
        validate_vector_record(&parsed).map_err(|e| {
            CoreError::ValueError(format!("{}:L{}: {}", rel_posix, idx + 1, e))
        })?;
        if let JsonValue::Object(map) = parsed {
            records.push(map);
        } else {
            return Err(CoreError::ValueError(format!(
                "{}:L{}: record must be a JSON object",
                rel_posix,
                idx + 1
            )));
        }
    }
    Ok((digest, records))
}

/// Execute and verify a single validated golden vector record.
pub fn verify_single_vector(record: &BTreeMap<String, JsonValue>) -> Result<(), CoreError> {
    let case_id = require_non_empty_str(record, "case_id")?;
    let operation = require_non_empty_str(record, "operation")?;
    let inputs = record
        .get("inputs")
        .and_then(JsonValue::as_object)
        .ok_or_else(|| CoreError::ValueError("vector inputs must be an object".to_string()))?;
    let expected = record
        .get("expected_outcome")
        .and_then(JsonValue::as_object)
        .ok_or_else(|| CoreError::ValueError("expected_outcome must be an object".to_string()))?;

    match expected.get("status").and_then(JsonValue::as_str) {
        Some("REJECT") => {
            let err_cls = require_non_empty_str(expected, "expected_error_class")?;
            verify_reject_operation(operation, inputs, err_cls)
        }
        Some("OK") => {
            let expected_val = expected.get("exact_value").ok_or_else(|| {
                CoreError::ValueError("OK expected_outcome missing exact_value".to_string())
            })?;
            let actual = eval_operation(operation, inputs)?;
            if actual != *expected_val {
                return Err(CoreError::ValueError(format!(
                    "vector {} ({}) exact output mismatch",
                    case_id, operation
                )));
            }
            Ok(())
        }
        _ => Err(CoreError::ValueError(format!(
            "invalid expected_outcome.status on {}",
            case_id
        ))),
    }
}

/// Load and verify all 30 S4 golden vectors (`RC-001`..`RC-024` + `SD-001`..`SD-006`).
pub fn verify_all_vectors(repo_root: &Path) -> Result<VectorsVerification, CoreError> {
    let (rc_sha, rc_rows) = load_vector_file(repo_root, RATIONAL_CORE_REL)?;
    let (sd_sha, sd_rows) = load_vector_file(repo_root, SYMBOLIC_DISPLAY_REL)?;

    if rc_rows.len() != 24 {
        return Err(CoreError::ValueError(format!(
            "expected 24 rational_core vectors, got {}",
            rc_rows.len()
        )));
    }
    if sd_rows.len() != 6 {
        return Err(CoreError::ValueError(format!(
            "expected 6 symbolic_and_display vectors, got {}",
            sd_rows.len()
        )));
    }

    let expected_rc: Vec<String> = (1..=24).map(|i| format!("RC-{:03}", i)).collect();
    let actual_rc: Vec<String> = rc_rows
        .iter()
        .map(|r| {
            r.get("case_id")
                .and_then(JsonValue::as_str)
                .unwrap_or("")
                .to_string()
        })
        .collect();
    if actual_rc != expected_rc {
        return Err(CoreError::ValueError(format!(
            "unexpected rational_core IDs: {:?}",
            actual_rc
        )));
    }

    let expected_sd: Vec<String> = (1..=6).map(|i| format!("SD-{:03}", i)).collect();
    let actual_sd: Vec<String> = sd_rows
        .iter()
        .map(|r| {
            r.get("case_id")
                .and_then(JsonValue::as_str)
                .unwrap_or("")
                .to_string()
        })
        .collect();
    if actual_sd != expected_sd {
        return Err(CoreError::ValueError(format!(
            "unexpected symbolic_and_display IDs: {:?}",
            actual_sd
        )));
    }

    let mut failures = Vec::new();
    let mut passed = 0usize;
    for rec in rc_rows.iter().chain(sd_rows.iter()) {
        let cid = rec
            .get("case_id")
            .and_then(JsonValue::as_str)
            .unwrap_or("UNKNOWN")
            .to_string();
        match verify_single_vector(rec) {
            Ok(()) => passed += 1,
            Err(err) => failures.push(VectorFailure {
                case_id: cid,
                error: err.to_string(),
            }),
        }
    }

    let total = rc_rows.len() + sd_rows.len();
    let mut file_digests = BTreeMap::new();
    file_digests.insert(RATIONAL_CORE_REL.to_string(), rc_sha);
    file_digests.insert(SYMBOLIC_DISPLAY_REL.to_string(), sd_sha);

    Ok(VectorsVerification {
        status: if failures.is_empty() {
            "PASS".to_string()
        } else {
            "FAIL".to_string()
        },
        rational_core_count: rc_rows.len(),
        symbolic_and_display_count: sd_rows.len(),
        total_vectors: total,
        passed_vectors: passed,
        failed_vectors: failures.len(),
        file_digests,
        failures,
    })
}
