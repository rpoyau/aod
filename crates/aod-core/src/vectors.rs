//! JSONL golden vector loader, `aod.s4.vector.v1` schema validator, and 40-vector runner.

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

fn is_win_drive_prefix(path: &str) -> bool {
    let bytes = path.as_bytes();
    bytes.len() >= 2 && bytes[0].is_ascii_alphabetic() && bytes[1] == b':'
}

fn read_repo_rel_no_symlink(repo_root: &Path, rel_posix: &str) -> Result<Vec<u8>, CoreError> {
    if rel_posix.is_empty()
        || rel_posix.contains('\\')
        || rel_posix.starts_with('/')
        || is_win_drive_prefix(rel_posix)
    {
        return Err(CoreError::UnsafePath(format!(
            "unsafe relative path: {:?}",
            rel_posix
        )));
    }
    let parts: Vec<&str> = rel_posix.split('/').collect();
    if parts.is_empty() || parts.iter().any(|s| s.is_empty() || *s == "." || *s == "..") {
        return Err(CoreError::UnsafePath(format!(
            "unsafe relative path: {:?}",
            rel_posix
        )));
    }

    let mut cur = repo_root.to_path_buf();
    for (idx, seg) in parts.iter().enumerate() {
        cur.push(seg);
        let meta = fs::symlink_metadata(&cur).map_err(|_| {
            CoreError::Io(format!("bound file or parent missing: {}", rel_posix))
        })?;
        if meta.file_type().is_symlink() {
            return Err(CoreError::UnsafePath(format!(
                "symlink forbidden along repo path: {}",
                rel_posix
            )));
        }
        let is_last = idx + 1 == parts.len();
        if is_last {
            if !meta.is_file() {
                return Err(CoreError::Io(format!(
                    "bound path is not a regular file: {}",
                    rel_posix
                )));
            }
        } else if !meta.is_dir() {
            return Err(CoreError::Io(format!(
                "bound parent is not a directory: {}",
                rel_posix
            )));
        }
    }

    if let (Ok(canon_root), Ok(canon_target)) = (fs::canonicalize(repo_root), fs::canonicalize(&cur))
    {
        if !canon_target.starts_with(&canon_root) {
            return Err(CoreError::UnsafePath(format!(
                "bound path escapes repo_root: {}",
                rel_posix
            )));
        }
    }

    Ok(fs::read(&cur)?)
}

fn file_suffix(rel_posix: &str) -> Option<&str> {
    let name = rel_posix.rsplit('/').next().unwrap_or(rel_posix);
    let dot = name.rfind('.')?;
    if dot == 0 {
        None
    } else {
        Some(&name[dot..])
    }
}

fn is_valid_typst_label(selector: &str) -> bool {
    !selector.is_empty()
        && selector
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'_' | b'.' | b':' | b'-'))
}

/// Strip Typst line comments (`//`), nested block comments (`/* ... */`), double-quoted
/// strings (with `\"` escapes), escaped delimiters (`\"`, `\\`, `\/`, `\<`, `\>`, `` \` ``),
/// and raw backtick literals (empty `` `` ``, inline `` `...` ``, and fenced `run_len >= 3`
/// blocks advancing past all `close_len` closing backticks), replacing stripped characters
/// with ASCII spaces while preserving `\n`.
fn strip_typst_comments_and_strings(text: &str) -> String {
    let chars: Vec<char> = text.chars().collect();
    let n = chars.len();
    let mut out = String::with_capacity(text.len());
    let mut i = 0usize;
    let mut block_depth = 0usize;
    let mut in_string = false;

    while i < n {
        let ch = chars[i];
        let nxt = if i + 1 < n { Some(chars[i + 1]) } else { None };

        if block_depth > 0 {
            if ch == '/' && nxt == Some('*') {
                block_depth += 1;
                out.push_str("  ");
                i += 2;
            } else if ch == '*' && nxt == Some('/') {
                block_depth -= 1;
                out.push_str("  ");
                i += 2;
            } else {
                out.push(if ch == '\n' { '\n' } else { ' ' });
                i += 1;
            }
            continue;
        }

        if in_string {
            if ch == '\\' && i + 1 < n {
                out.push_str("  ");
                i += 2;
            } else if ch == '"' {
                in_string = false;
                out.push(' ');
                i += 1;
            } else {
                out.push(if ch == '\n' { '\n' } else { ' ' });
                i += 1;
            }
            continue;
        }

        if ch == '\\' && matches!(nxt, Some('"' | '\\' | '/' | '<' | '>' | '`')) {
            out.push_str("  ");
            i += 2;
            continue;
        }

        if ch == '/' && nxt == Some('/') {
            while i < n && chars[i] != '\n' {
                out.push(' ');
                i += 1;
            }
            continue;
        }

        if ch == '/' && nxt == Some('*') {
            block_depth = 1;
            out.push_str("  ");
            i += 2;
            continue;
        }

        if ch == '"' {
            in_string = true;
            out.push(' ');
            i += 1;
            continue;
        }

        if ch == '`' {
            let mut run_len = 0usize;
            while i + run_len < n && chars[i + run_len] == '`' {
                run_len += 1;
            }
            for _ in 0..run_len {
                out.push(' ');
            }
            i += run_len;
            if run_len == 2 {
                continue;
            }
            if run_len == 1 {
                while i < n {
                    if chars[i] == '`' {
                        out.push(' ');
                        i += 1;
                        break;
                    }
                    out.push(if chars[i] == '\n' { '\n' } else { ' ' });
                    i += 1;
                }
                continue;
            }
            // Fenced raw block (run_len >= 3): advance past all `close_len` closing backticks.
            while i < n {
                if chars[i] == '`' {
                    let mut close_len = 0usize;
                    while i + close_len < n && chars[i + close_len] == '`' {
                        close_len += 1;
                    }
                    for _ in 0..close_len {
                        out.push(' ');
                    }
                    i += close_len;
                    if close_len >= run_len {
                        break;
                    }
                    continue;
                }
                out.push(if chars[i] == '\n' { '\n' } else { ' ' });
                i += 1;
            }
            continue;
        }

        out.push(ch);
        i += 1;
    }

    out
}

fn ends_with_typst_ref_call(prefix: &str) -> bool {
    let trimmed = prefix.trim_end_matches(|c: char| c.is_whitespace());
    let Some(before_paren) = trimmed.strip_suffix('(') else {
        return false;
    };
    let before_ws = before_paren.trim_end_matches(|c: char| c.is_whitespace());
    for kw in ["ref", "link", "cite", "query", "selector"] {
        if let Some(head) = before_ws.strip_suffix(kw) {
            let boundary_ok = match head.chars().next_back() {
                None => true,
                Some(prev) => !(prev.is_alphanumeric() || prev == '_'),
            };
            if boundary_ok {
                return true;
            }
        }
    }
    false
}

fn has_defining_typst_label(text: &str, label: &str) -> bool {
    let stripped = strip_typst_comments_and_strings(text);
    let needle = format!("<{}>", label);
    let bytes = stripped.as_bytes();
    let mut search_from = 0usize;
    while search_from < stripped.len() {
        let Some(rel_pos) = stripped[search_from..].find(&needle) else {
            break;
        };
        let pos = search_from + rel_pos;
        let end = pos + needle.len();
        let prev_ok = pos == 0 || bytes[pos - 1] != b'<';
        let next_ok = end == bytes.len() || bytes[end] != b'>';
        if prev_ok && next_ok && !ends_with_typst_ref_call(&stripped[..pos]) {
            return true;
        }
        search_from = pos + 1;
    }
    false
}

fn is_canonical_pos_int(s: &str) -> bool {
    let bytes = s.as_bytes();
    !bytes.is_empty() && bytes[0] != b'0' && bytes.iter().all(|b| b.is_ascii_digit())
}

fn parse_py_line_range(selector: &str) -> Option<(usize, usize)> {
    let rest = selector.strip_prefix('L')?;
    let (start_s, end_s) = rest.split_once('-')?;
    if !is_canonical_pos_int(start_s) || !is_canonical_pos_int(end_s) {
        return None;
    }
    let start = start_s.parse::<usize>().ok()?;
    let end = end_s.parse::<usize>().ok()?;
    Some((start, end))
}

fn is_py_ident(s: &str) -> bool {
    let bytes = s.as_bytes();
    !bytes.is_empty()
        && (bytes[0].is_ascii_alphabetic() || bytes[0] == b'_')
        && bytes[1..]
            .iter()
            .all(|b| b.is_ascii_alphanumeric() || *b == b'_')
}

fn line_defines_top_level_py_func(line: &str, ident: &str) -> bool {
    let after_def = if let Some(rest) = line.strip_prefix("def") {
        if !rest.starts_with([' ', '\t']) {
            return false;
        }
        rest.trim_start_matches([' ', '\t'])
    } else if let Some(rest) = line.strip_prefix("async") {
        if !rest.starts_with([' ', '\t']) {
            return false;
        }
        let rest = rest.trim_start_matches([' ', '\t']);
        let Some(after_d) = rest.strip_prefix("def") else {
            return false;
        };
        if !after_d.starts_with([' ', '\t']) {
            return false;
        }
        after_d.trim_start_matches([' ', '\t'])
    } else {
        return false;
    };

    let Some(after_ident) = after_def.strip_prefix(ident) else {
        return false;
    };
    after_ident.trim_start_matches([' ', '\t']).starts_with('(')
}

fn is_noncanonical_csv_row_selector(selector: &str) -> bool {
    let Some(rest) = selector.strip_prefix("row") else {
        return false;
    };
    let digits = match rest.split_once('_') {
        Some((d, _)) => d,
        None => rest,
    };
    digits.len() >= 2
        && digits.as_bytes()[0] == b'0'
        && digits.bytes().all(|b| b.is_ascii_digit())
}

fn parse_csv_row_selector(selector: &str) -> Option<(usize, Option<&str>)> {
    let rest = selector.strip_prefix("row")?;
    let (digits, token) = match rest.split_once('_') {
        Some((d, tok)) => {
            if tok.is_empty() {
                return None;
            }
            (d, Some(tok))
        }
        None => (rest, None),
    };
    let canonical = digits == "0" || is_canonical_pos_int(digits);
    if !canonical {
        return None;
    }
    let idx = digits.parse::<usize>().ok()?;
    Some((idx, token))
}

/// RFC 4180 quote-aware CSV parser (handles quoted commas, escaped `""`, and embedded newlines).
fn parse_csv_records(text: &str) -> Result<Vec<Vec<String>>, CoreError> {
    let chars: Vec<char> = text.chars().collect();
    let n = chars.len();
    let mut i = 0usize;
    let mut rows: Vec<Vec<String>> = Vec::new();

    while i < n {
        let mut row: Vec<String> = Vec::new();
        loop {
            let mut field = String::new();
            if i < n && chars[i] == '"' {
                i += 1;
                let mut closed = false;
                while i < n {
                    if chars[i] == '"' {
                        if i + 1 < n && chars[i + 1] == '"' {
                            field.push('"');
                            i += 2;
                        } else {
                            i += 1;
                            closed = true;
                            break;
                        }
                    } else {
                        field.push(chars[i]);
                        i += 1;
                    }
                }
                if !closed {
                    return Err(CoreError::ValueError(
                        "unterminated quoted CSV field".to_string(),
                    ));
                }
                if i < n && chars[i] != ',' && chars[i] != '\r' && chars[i] != '\n' {
                    return Err(CoreError::ValueError(
                        "unexpected trailing character after quoted CSV field".to_string(),
                    ));
                }
            } else {
                while i < n && chars[i] != ',' && chars[i] != '\r' && chars[i] != '\n' {
                    field.push(chars[i]);
                    i += 1;
                }
            }
            row.push(field);

            if i < n && chars[i] == ',' {
                i += 1;
                continue;
            }
            if i < n && chars[i] == '\r' {
                i += 1;
                if i < n && chars[i] == '\n' {
                    i += 1;
                }
            } else if i < n && chars[i] == '\n' {
                i += 1;
            }
            break;
        }
        rows.push(row);
    }

    Ok(rows)
}

/// Validate every `;`-separated `path[#selector]` component in `source_binding`
/// across all five finite selector forms (whole file, `.typ#<label>`, `.py#L<start>-<end>`
/// or `.py#<ident>`, `.json#<dot.key.path>`, and `.csv#<selector>`).
pub fn validate_source_binding(repo_root: &Path, source_binding: &str) -> Result<(), CoreError> {
    if source_binding.is_empty() || source_binding != source_binding.trim() {
        return Err(CoreError::ValueError(format!(
            "source_binding must be a non-empty trimmed string: {:?}",
            source_binding
        )));
    }

    for comp in source_binding.split(';') {
        if comp.is_empty() || comp != comp.trim() {
            return Err(CoreError::ValueError(format!(
                "empty or whitespace-padded source_binding component in {:?}",
                source_binding
            )));
        }
        if comp.matches('#').count() > 1 {
            return Err(CoreError::ValueError(format!(
                "multiple '#' selectors forbidden in source_binding component: {:?}",
                comp
            )));
        }
        let (rel_path, selector_opt) = match comp.split_once('#') {
            Some((p, s)) => (p, Some(s)),
            None => (comp, None),
        };
        if rel_path.is_empty() {
            return Err(CoreError::ValueError(format!(
                "missing relative path in source_binding component: {:?}",
                comp
            )));
        }
        if rel_path.contains('\\') {
            return Err(CoreError::ValueError(format!(
                "backslash forbidden in source_binding path: {:?}",
                rel_path
            )));
        }
        if rel_path.starts_with('/') || is_win_drive_prefix(rel_path) {
            return Err(CoreError::ValueError(format!(
                "absolute path forbidden in source_binding: {:?}",
                rel_path
            )));
        }
        if rel_path
            .split('/')
            .any(|seg| seg.is_empty() || seg == "." || seg == "..")
        {
            return Err(CoreError::ValueError(format!(
                "unsafe relative path segment in source_binding: {:?}",
                rel_path
            )));
        }
        if let Some(sel) = selector_opt {
            if sel.is_empty() {
                return Err(CoreError::ValueError(format!(
                    "empty selector after '#' in source_binding: {:?}",
                    comp
                )));
            }
        }

        let raw_bytes = read_repo_rel_no_symlink(repo_root, rel_path)?;
        let Some(selector) = selector_opt else {
            continue;
        };

        let text = String::from_utf8(raw_bytes).map_err(|_| {
            CoreError::ValueError(format!(
                "non-UTF-8 bytes in source_binding target {}",
                rel_path
            ))
        })?;

        match file_suffix(rel_path) {
            Some(".typ") => {
                if !is_valid_typst_label(selector) {
                    return Err(CoreError::ValueError(format!(
                        "invalid Typst label selector {:?} in {:?}",
                        selector, comp
                    )));
                }
                if !has_defining_typst_label(&text, selector) {
                    return Err(CoreError::ValueError(format!(
                        "defining Typst label <{}> not found in {}",
                        selector, rel_path
                    )));
                }
            }
            Some(".py") => {
                if let Some((start, end)) = parse_py_line_range(selector) {
                    let line_count = text.lines().count();
                    if start < 1 || start > end || end > line_count {
                        return Err(CoreError::ValueError(format!(
                            "Python line range {:?} out of bounds for {} (1..{})",
                            selector, rel_path, line_count
                        )));
                    }
                } else if is_py_ident(selector) {
                    let found = text
                        .lines()
                        .any(|line| line_defines_top_level_py_func(line, selector));
                    if !found {
                        return Err(CoreError::ValueError(format!(
                            "top-level function {:?} not found in {}",
                            selector, rel_path
                        )));
                    }
                } else {
                    return Err(CoreError::ValueError(format!(
                        "unsupported Python selector {:?} in {:?}",
                        selector, comp
                    )));
                }
            }
            Some(".json") => {
                let doc = parse_json(&text).map_err(|e| {
                    CoreError::ValueError(format!(
                        "failed to parse JSON source_binding {}: {}",
                        rel_path, e
                    ))
                })?;
                let segments: Vec<&str> = selector.split('.').collect();
                if segments.is_empty() || segments.iter().any(|s| s.is_empty()) {
                    return Err(CoreError::ValueError(format!(
                        "empty JSON key segment in selector {:?} for {}",
                        selector, rel_path
                    )));
                }
                let mut cur = &doc;
                for seg in segments {
                    match cur {
                        JsonValue::Object(map) => {
                            cur = map.get(seg).ok_or_else(|| {
                                CoreError::ValueError(format!(
                                    "JSON key path {:?} missing segment {:?} in {}",
                                    selector, seg, rel_path
                                ))
                            })?;
                        }
                        _ => {
                            return Err(CoreError::ValueError(format!(
                                "JSON key path {:?} missing object at segment {:?} in {}",
                                selector, seg, rel_path
                            )));
                        }
                    }
                }
            }
            Some(".csv") => {
                if is_noncanonical_csv_row_selector(selector) {
                    return Err(CoreError::ValueError(format!(
                        "non-canonical CSV row selector {:?} in {:?}",
                        selector, comp
                    )));
                }
                let rows = parse_csv_records(&text).map_err(|e| {
                    CoreError::ValueError(format!(
                        "failed to parse CSV source_binding {}: {}",
                        rel_path, e
                    ))
                })?;
                let header_len = rows.first().map_or(0, Vec::len);
                let data_rows: &[Vec<String>] = if rows.len() > 1 { &rows[1..] } else { &[] };
                if let Some((idx, token_opt)) = parse_csv_row_selector(selector) {
                    if idx >= data_rows.len() {
                        return Err(CoreError::ValueError(format!(
                            "CSV row selector {:?} out of bounds for {} (rows={})",
                            selector,
                            rel_path,
                            data_rows.len()
                        )));
                    }
                    if let Some(token) = token_opt {
                        let matched = data_rows[idx]
                            .iter()
                            .take(header_len)
                            .any(|cell| cell == token);
                        if !matched {
                            return Err(CoreError::ValueError(format!(
                                "CSV row {} in {} does not contain token {:?}",
                                idx, rel_path, token
                            )));
                        }
                    }
                } else {
                    let matched = data_rows.iter().any(|row| {
                        row.iter()
                            .take(header_len)
                            .any(|cell| cell == selector)
                    });
                    if !matched {
                        return Err(CoreError::ValueError(format!(
                            "CSV cell token {:?} not found in {}",
                            selector, rel_path
                        )));
                    }
                }
            }
            other => {
                return Err(CoreError::ValueError(format!(
                    "unsupported source_binding selector suffix {:?} in {:?}",
                    other.unwrap_or(""),
                    comp
                )));
            }
        }
    }

    Ok(())
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

/// Execute and verify a single validated golden vector record (arithmetic / REJECT check).
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

/// Execute and verify a single validated golden vector record AND resolve its `source_binding`
/// against `repo_root` (validating source bindings after exact arithmetic / REJECT verification).
pub fn verify_single_vector_with_root(
    record: &BTreeMap<String, JsonValue>,
    repo_root: &Path,
) -> Result<(), CoreError> {
    verify_single_vector(record)?;
    let source_binding = require_non_empty_str(record, "source_binding")?;
    validate_source_binding(repo_root, source_binding)?;
    Ok(())
}

/// Load and verify all 40 S4 golden vectors (`RC-001`..`RC-032` + `SD-001`..`SD-008`).
pub fn verify_all_vectors(repo_root: &Path) -> Result<VectorsVerification, CoreError> {
    let (rc_sha, rc_rows) = load_vector_file(repo_root, RATIONAL_CORE_REL)?;
    let (sd_sha, sd_rows) = load_vector_file(repo_root, SYMBOLIC_DISPLAY_REL)?;

    if rc_rows.len() != 32 {
        return Err(CoreError::ValueError(format!(
            "expected 32 rational_core vectors, got {}",
            rc_rows.len()
        )));
    }
    if sd_rows.len() != 8 {
        return Err(CoreError::ValueError(format!(
            "expected 8 symbolic_and_display vectors, got {}",
            sd_rows.len()
        )));
    }

    let expected_rc: Vec<String> = (1..=32).map(|i| format!("RC-{:03}", i)).collect();
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

    let expected_sd: Vec<String> = (1..=8).map(|i| format!("SD-{:03}", i)).collect();
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
        match verify_single_vector_with_root(rec, repo_root) {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_typst_strip_and_defining_label_detection() {
        // Real defining label passes
        assert!(has_defining_typst_label("$ x = 1 $ <eq:real>\n", "eq:real"));
        // Comments, strings, escaped delimiters, inline/fenced raw backticks rejected
        assert!(!has_defining_typst_label("// <eq:fake>\n", "eq:fake"));
        assert!(!has_defining_typst_label("/* outer /* <eq:fake> */ still */\n", "eq:fake"));
        assert!(!has_defining_typst_label("#eqref(\"<eq:fake>\")\n", "eq:fake"));
        assert!(!has_defining_typst_label("\\<eq:fake\\>\n", "eq:fake"));
        assert!(!has_defining_typst_label("inline `<eq:fake>` raw\n", "eq:fake"));
        assert!(!has_defining_typst_label("```typ\n<eq:fake>\n```\n", "eq:fake"));
        // Fenced raw block closed by more backticks advances past all close_len backticks,
        // so a real defining label immediately after it is NOT swallowed by a leftover backtick.
        assert!(has_defining_typst_label(
            "```typ\n<eq:fake>\n````\n$ y = 2 $ <eq:after>\n",
            "eq:after"
        ));
        assert!(!has_defining_typst_label(
            "```typ\n<eq:fake>\n````\n$ y = 2 $ <eq:after>\n",
            "eq:fake"
        ));
        // Empty double-backtick literal does not swallow subsequent real label
        assert!(has_defining_typst_label("`` $ y = 2 $ <eq:real>\n", "eq:real"));
        // Native Typst reference calls rejected
        assert!(!has_defining_typst_label("#ref(<eq:refonly>)\n", "eq:refonly"));
        assert!(!has_defining_typst_label("#link( <eq:refonly> )\n", "eq:refonly"));
        assert!(!has_defining_typst_label("#cite(<eq:refonly>)\n", "eq:refonly"));
        assert!(!has_defining_typst_label("#query(<eq:refonly>)\n", "eq:refonly"));
        assert!(!has_defining_typst_label("#selector(<eq:refonly>)\n", "eq:refonly"));
        // Double angle brackets rejected
        assert!(!has_defining_typst_label("<<eq:double>>\n", "eq:double"));
    }

    #[test]
    fn test_csv_rfc4180_and_canonical_row_selectors() {
        let csv = "id,note,tag\n0,\"hello, \"\"world\"\"\",A\n1,\"line1\nline2\",B\n";
        let rows = parse_csv_records(csv).expect("parse csv");
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[1], vec!["0", "hello, \"world\"", "A"]);
        assert_eq!(rows[2], vec!["1", "line1\nline2", "B"]);

        assert!(is_noncanonical_csv_row_selector("row00"));
        assert!(is_noncanonical_csv_row_selector("row078"));
        assert!(is_noncanonical_csv_row_selector("row078_NGC3198"));
        assert!(!is_noncanonical_csv_row_selector("row0"));
        assert!(!is_noncanonical_csv_row_selector("row78_NGC3198"));

        assert_eq!(parse_csv_row_selector("row0"), Some((0, None)));
        assert_eq!(
            parse_csv_row_selector("row78_NGC3198"),
            Some((78, Some("NGC3198")))
        );
        assert_eq!(parse_csv_row_selector("row0_"), None);
        assert_eq!(parse_csv_row_selector("M1-harmonic-01"), None);
    }

    #[test]
    fn test_py_selectors() {
        assert_eq!(parse_py_line_range("L22-73"), Some((22, 73)));
        assert_eq!(parse_py_line_range("L01-10"), None);
        assert_eq!(parse_py_line_range("L1-02"), None);
        assert!(line_defines_top_level_py_func("def transition(x):", "transition"));
        assert!(line_defines_top_level_py_func("async def fetch_data(a):", "fetch_data"));
        assert!(!line_defines_top_level_py_func("    def transition(x):", "transition"));
        assert!(!line_defines_top_level_py_func("def transition_v2(x):", "transition"));
    }
}
