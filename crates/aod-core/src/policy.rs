//! Rust source-tree policy auditor for `crates/aod-core/`.
//!
//! Deterministically walks the crate directory (skipping only a real non-symlink
//! top-level `target/` directory) and enforces:
//! - Zero symlinks and zero `.json` files anywhere under the crate.
//! - Zero forbidden experimental namespace tokens (case-insensitive).
//! - Strictly empty dependency sections and no `[workspace]` / `[patch]` in `Cargo.toml`.
//! - Single-package `Cargo.lock` (`aod-core` only, zero `source`/`checksum`/`dependencies`).
//! - Active `#![forbid(unsafe_code)]` attribute in `src/lib.rs`, `src/main.rs`, and `tests/*.rs`.
//! - Zero float types (`f16`/`f32`/`f64`/`f128`), zero float literals, zero `unsafe`,
//!   and zero `extern` tokens anywhere in active Rust code.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use crate::bigint::BigInt;
use crate::json::JsonValue;
use crate::CoreError;

const EXP_PREFIX: &[u8] = b"aod";
const EXP_SUFFIX: &[u8] = b"dec";

const FORBIDDEN_FLOAT_TYPES: [&str; 4] = ["f16", "f32", "f64", "f128"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyViolation {
    pub file: String,
    pub line: usize,
    pub rule: String,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyAudit {
    pub status: String,
    pub audited_rust_files: usize,
    pub audited_text_files: usize,
    pub cargo_lock_packages: usize,
    pub forbid_unsafe_checked_files: Vec<String>,
    pub json_files_under_crate: usize,
    pub violation_count: usize,
    pub violations: Vec<PolicyViolation>,
}

impl PolicyAudit {
    pub fn to_json(&self) -> JsonValue {
        let violations = self
            .violations
            .iter()
            .map(|v| {
                let mut m = BTreeMap::new();
                m.insert("file".to_string(), JsonValue::Str(v.file.clone()));
                m.insert("line".to_string(), JsonValue::Int(BigInt::from_usize(v.line)));
                m.insert("rule".to_string(), JsonValue::Str(v.rule.clone()));
                m.insert("detail".to_string(), JsonValue::Str(v.detail.clone()));
                JsonValue::Object(m)
            })
            .collect();
        let checked = self
            .forbid_unsafe_checked_files
            .iter()
            .map(|s| JsonValue::Str(s.clone()))
            .collect();
        let mut out = BTreeMap::new();
        out.insert("status".to_string(), JsonValue::Str(self.status.clone()));
        out.insert(
            "audited_rust_files".to_string(),
            JsonValue::Int(BigInt::from_usize(self.audited_rust_files)),
        );
        out.insert(
            "audited_text_files".to_string(),
            JsonValue::Int(BigInt::from_usize(self.audited_text_files)),
        );
        out.insert(
            "cargo_lock_packages".to_string(),
            JsonValue::Int(BigInt::from_usize(self.cargo_lock_packages)),
        );
        out.insert(
            "forbid_unsafe_checked_files".to_string(),
            JsonValue::Array(checked),
        );
        out.insert(
            "json_files_under_crate".to_string(),
            JsonValue::Int(BigInt::from_usize(self.json_files_under_crate)),
        );
        out.insert(
            "violation_count".to_string(),
            JsonValue::Int(BigInt::from_usize(self.violation_count)),
        );
        out.insert("violations".to_string(), JsonValue::Array(violations));
        JsonValue::Object(out)
    }
}

fn contains_forbidden_experimental_token(line: &str) -> bool {
    let bytes = line.as_bytes();
    let plen = EXP_PREFIX.len();
    let slen = EXP_SUFFIX.len();
    let need = plen + 1 + slen;
    if bytes.len() < need {
        return false;
    }
    for i in 0..=bytes.len() - need {
        let mut ok = true;
        for j in 0..plen {
            if bytes[i + j].to_ascii_lowercase() != EXP_PREFIX[j] {
                ok = false;
                break;
            }
        }
        if !ok {
            continue;
        }
        let sep = bytes[i + plen];
        if sep != b'-' && sep != b'_' {
            continue;
        }
        for j in 0..slen {
            if bytes[i + plen + 1 + j].to_ascii_lowercase() != EXP_SUFFIX[j] {
                ok = false;
                break;
            }
        }
        if ok {
            return true;
        }
    }
    false
}

fn walk_crate_tree(
    crate_root: &Path,
    dir: &Path,
    rel_prefix: &str,
    files: &mut Vec<(String, std::path::PathBuf)>,
    violations: &mut Vec<PolicyViolation>,
) -> Result<(), CoreError> {
    let mut entries: Vec<(String, std::path::PathBuf)> = Vec::new();
    for entry_res in fs::read_dir(dir)? {
        let entry = entry_res?;
        let name = entry.file_name().to_string_lossy().into_owned();
        entries.push((name, entry.path()));
    }
    entries.sort_by(|a, b| a.0.cmp(&b.0));

    for (name, path) in entries {
        let rel = if rel_prefix.is_empty() {
            name.clone()
        } else {
            format!("{}/{}", rel_prefix, name)
        };
        let meta = fs::symlink_metadata(&path)?;
        if meta.file_type().is_symlink() {
            violations.push(PolicyViolation {
                file: rel,
                line: 0,
                rule: "forbidden_symlink".to_string(),
                detail: "symlinks are forbidden inside crates/aod-core".to_string(),
            });
            continue;
        }
        if meta.is_dir() {
            // Skip ONLY top-level non-symlink target/ directory.
            if rel_prefix.is_empty() && name == "target" {
                continue;
            }
            walk_crate_tree(crate_root, &path, &rel, files, violations)?;
        } else if meta.is_file() {
            files.push((rel, path));
        }
    }
    let _ = crate_root;
    Ok(())
}

// ---------------------------------------------------------------------------
// Cargo.toml & Cargo.lock policy checks
// ---------------------------------------------------------------------------

fn strip_toml_comment(line: &str) -> &str {
    let bytes = line.as_bytes();
    let mut in_dq = false;
    let mut in_sq = false;
    let mut i = 0usize;
    while i < bytes.len() {
        let b = bytes[i];
        if in_dq {
            if b == b'\\' && i + 1 < bytes.len() {
                i += 2;
                continue;
            }
            if b == b'"' {
                in_dq = false;
            }
        } else if in_sq {
            if b == b'\'' {
                in_sq = false;
            }
        } else if b == b'"' {
            in_dq = true;
        } else if b == b'\'' {
            in_sq = true;
        } else if b == b'#' {
            return &line[..i];
        }
        i += 1;
    }
    line
}

fn is_dependency_section_header(section: &str) -> (bool, bool) {
    // Returns (is_dep_table, is_immediately_forbidden_subtable_or_patch)
    let trimmed = section.trim();
    if trimmed == "workspace" || trimmed.starts_with("workspace.") {
        return (false, true);
    }
    if trimmed == "patch"
        || trimmed.starts_with("patch.")
        || trimmed == "replace"
        || trimmed.starts_with("replace.")
    {
        return (true, true);
    }
    if matches!(
        trimmed,
        "dependencies" | "dev-dependencies" | "build-dependencies"
    ) {
        return (true, false);
    }
    if trimmed.starts_with("dependencies.")
        || trimmed.starts_with("dev-dependencies.")
        || trimmed.starts_with("build-dependencies.")
    {
        return (true, true);
    }
    if trimmed.starts_with("target.") {
        if trimmed.ends_with(".dependencies")
            || trimmed.ends_with(".dev-dependencies")
            || trimmed.ends_with(".build-dependencies")
        {
            return (true, false);
        }
        if trimmed.contains(".dependencies.")
            || trimmed.contains(".dev-dependencies.")
            || trimmed.contains(".build-dependencies.")
        {
            return (true, true);
        }
    }
    (false, false)
}

fn audit_cargo_toml(rel: &str, text: &str, violations: &mut Vec<PolicyViolation>) {
    let mut current_section = String::new();
    let mut in_dep_section = false;

    for (idx, raw_line) in text.lines().enumerate() {
        let lineno = idx + 1;
        let code = strip_toml_comment(raw_line).trim();
        if code.is_empty() {
            continue;
        }
        if code.starts_with('[') && code.ends_with(']') {
            let inner = code
                .trim_start_matches('[')
                .trim_end_matches(']')
                .trim()
                .to_string();
            let (is_dep, forbidden_immediately) = is_dependency_section_header(&inner);
            if forbidden_immediately {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: lineno,
                    rule: "forbidden_cargo_toml_section".to_string(),
                    detail: format!("forbidden Cargo.toml section [{}]", inner),
                });
            }
            in_dep_section = is_dep;
            current_section = inner;
            continue;
        }

        if in_dep_section {
            violations.push(PolicyViolation {
                file: rel.to_string(),
                line: lineno,
                rule: "forbidden_dependency".to_string(),
                detail: format!("external dependency entry forbidden in [{}]", current_section),
            });
        } else if current_section.is_empty() {
            if let Some((lhs, _)) = code.split_once('=') {
                let key = lhs.trim();
                if matches!(
                    key,
                    "dependencies" | "dev-dependencies" | "build-dependencies" | "patch" | "replace"
                ) {
                    violations.push(PolicyViolation {
                        file: rel.to_string(),
                        line: lineno,
                        rule: "forbidden_dependency".to_string(),
                        detail: format!("inline dependency key {:?} is forbidden", key),
                    });
                }
            }
        }
    }
}

fn audit_cargo_lock(rel: &str, text: &str, violations: &mut Vec<PolicyViolation>) -> usize {
    let mut pkg_count = 0usize;
    let mut in_pkg = false;
    let mut pkg_names: Vec<(usize, String)> = Vec::new();

    for (idx, raw_line) in text.lines().enumerate() {
        let lineno = idx + 1;
        let code = strip_toml_comment(raw_line).trim();
        if code.is_empty() {
            continue;
        }
        if code == "[[package]]" {
            pkg_count += 1;
            in_pkg = true;
            continue;
        }
        if code.starts_with('[') {
            in_pkg = false;
            continue;
        }
        if let Some((lhs, rhs)) = code.split_once('=') {
            let key = lhs.trim();
            let val = rhs.trim();
            if matches!(key, "source" | "checksum" | "dependencies") {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: lineno,
                    rule: "forbidden_lockfile_field".to_string(),
                    detail: format!("forbidden Cargo.lock field {:?}", key),
                });
            } else if in_pkg && key == "name" {
                let unquoted = val.trim_matches('"').to_string();
                pkg_names.push((lineno, unquoted));
            }
        }
    }

    if pkg_count != 1 {
        violations.push(PolicyViolation {
            file: rel.to_string(),
            line: 1,
            rule: "forbidden_lockfile_packages".to_string(),
            detail: format!("Cargo.lock must contain strictly 1 [[package]], found {}", pkg_count),
        });
    }
    for (lineno, name) in &pkg_names {
        if name != "aod-core" {
            violations.push(PolicyViolation {
                file: rel.to_string(),
                line: *lineno,
                rule: "forbidden_lockfile_package".to_string(),
                detail: format!("unexpected package {:?} in Cargo.lock", name),
            });
        }
    }
    if pkg_count == 1 && pkg_names.len() != 1 {
        violations.push(PolicyViolation {
            file: rel.to_string(),
            line: 1,
            rule: "invalid_lockfile".to_string(),
            detail: "Cargo.lock [[package]] missing name = \"aod-core\"".to_string(),
        });
    }
    pkg_count
}

// ---------------------------------------------------------------------------
// Full Rust lexical scanner (comments, raw strings, char vs lifetime, tuple index)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq)]
enum TokKind {
    Ident(String),
    RawIdent(String),
    IntLit,
    TupleIndex,
    FloatLit(String),
    Dot,
    DotDot,
    Hash,
    Bang,
    LBracket,
    RBracket,
    LParen,
    RParen,
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Token {
    kind: TokKind,
    line: usize,
}

fn is_ident_start(b: u8) -> bool {
    b.is_ascii_alphabetic() || b == b'_'
}

fn is_ident_continue(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

fn lex_rust_source(rel: &str, src: &str, violations: &mut Vec<PolicyViolation>) -> Vec<Token> {
    let bytes = src.as_bytes();
    let len = bytes.len();
    let mut pos = 0usize;
    let mut line = 1usize;
    let mut tokens: Vec<Token> = Vec::new();

    let mut prev_can_tuple_index = false;
    let mut prev_is_tuple_dot = false;

    while pos < len {
        let b = bytes[pos];

        // 1. Whitespace
        if b.is_ascii_whitespace() {
            if b == b'\n' {
                line += 1;
            }
            pos += 1;
            continue;
        }

        // 2. Line comment `//...`
        if b == b'/' && pos + 1 < len && bytes[pos + 1] == b'/' {
            pos += 2;
            while pos < len && bytes[pos] != b'\n' {
                pos += 1;
            }
            continue;
        }

        // 3. Nested block comment `/* ... */`
        if b == b'/' && pos + 1 < len && bytes[pos + 1] == b'*' {
            let start_line = line;
            pos += 2;
            let mut depth = 1usize;
            while pos < len && depth > 0 {
                if bytes[pos] == b'\n' {
                    line += 1;
                    pos += 1;
                } else if bytes[pos] == b'/' && pos + 1 < len && bytes[pos + 1] == b'*' {
                    depth += 1;
                    pos += 2;
                } else if bytes[pos] == b'*' && pos + 1 < len && bytes[pos + 1] == b'/' {
                    depth -= 1;
                    pos += 2;
                } else {
                    pos += 1;
                }
            }
            if depth != 0 {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: start_line,
                    rule: "lex_error".to_string(),
                    detail: "unterminated block comment".to_string(),
                });
            }
            continue;
        }

        // 4. Raw strings (`r#"..."#`, `br#"..."#`, `cr#"..."#`) and raw idents (`r#ident`)
        if let Some((prefix_len, hashes)) = match_raw_string_start(bytes, pos) {
            let start_line = line;
            pos += prefix_len + hashes + 1; // skip prefix + #'s + opening '"'
            let mut closed = false;
            while pos < len {
                if bytes[pos] == b'\n' {
                    line += 1;
                    pos += 1;
                } else if bytes[pos] == b'"' {
                    let mut h = 0usize;
                    while h < hashes && pos + 1 + h < len && bytes[pos + 1 + h] == b'#' {
                        h += 1;
                    }
                    if h == hashes {
                        pos += 1 + hashes;
                        closed = true;
                        break;
                    }
                    pos += 1;
                } else {
                    pos += 1;
                }
            }
            if !closed {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: start_line,
                    rule: "lex_error".to_string(),
                    detail: "unterminated raw string literal".to_string(),
                });
            }
            prev_can_tuple_index = false;
            prev_is_tuple_dot = false;
            continue;
        }

        // Raw identifier `r#<ident>`
        if b == b'r'
            && pos + 2 < len
            && bytes[pos + 1] == b'#'
            && is_ident_start(bytes[pos + 2])
        {
            let tok_line = line;
            pos += 2;
            let start = pos;
            while pos < len && is_ident_continue(bytes[pos]) {
                pos += 1;
            }
            let ident = std::str::from_utf8(&bytes[start..pos])
                .unwrap_or("")
                .to_string();
            tokens.push(Token {
                kind: TokKind::RawIdent(ident),
                line: tok_line,
            });
            prev_can_tuple_index = true;
            prev_is_tuple_dot = false;
            continue;
        }

        // 5. Regular / byte / C string literals (`"..."`, `b"..."`, `c"..."`)
        if b == b'"'
            || ((b == b'b' || b == b'c') && pos + 1 < len && bytes[pos + 1] == b'"')
        {
            let start_line = line;
            if b != b'"' {
                pos += 1;
            }
            pos += 1; // skip opening '"'
            let mut closed = false;
            while pos < len {
                let c = bytes[pos];
                if c == b'\\' {
                    if pos + 1 < len {
                        if bytes[pos + 1] == b'\n' {
                            line += 1;
                        }
                        pos += 2;
                    } else {
                        pos += 1;
                    }
                } else if c == b'"' {
                    pos += 1;
                    closed = true;
                    break;
                } else {
                    if c == b'\n' {
                        line += 1;
                    }
                    pos += 1;
                }
            }
            if !closed {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: start_line,
                    rule: "lex_error".to_string(),
                    detail: "unterminated string literal".to_string(),
                });
            }
            prev_can_tuple_index = false;
            prev_is_tuple_dot = false;
            continue;
        }

        // 6. Byte character literal `b'...'`
        if b == b'b' && pos + 1 < len && bytes[pos + 1] == b'\'' {
            pos += 2;
            consume_char_literal_body(bytes, &mut pos, &mut line);
            prev_can_tuple_index = false;
            prev_is_tuple_dot = false;
            continue;
        }

        // 7. Character literal `'x'` / `'\n'` vs Lifetime `'a` / `'_`
        if b == b'\'' {
            if let Some(after_char) = match_char_literal(src, pos) {
                for &ch in &bytes[pos..after_char] {
                    if ch == b'\n' {
                        line += 1;
                    }
                }
                pos = after_char;
            } else {
                // Lifetime or label: consume `'` and identifier chars only (never scan to next `'`).
                pos += 1;
                if pos < len && is_ident_start(bytes[pos]) {
                    while pos < len && is_ident_continue(bytes[pos]) {
                        pos += 1;
                    }
                }
            }
            prev_can_tuple_index = false;
            prev_is_tuple_dot = false;
            continue;
        }

        // 8. Identifiers
        if is_ident_start(b) {
            let tok_line = line;
            let start = pos;
            while pos < len && is_ident_continue(bytes[pos]) {
                pos += 1;
            }
            let ident = std::str::from_utf8(&bytes[start..pos])
                .unwrap_or("")
                .to_string();
            tokens.push(Token {
                kind: TokKind::Ident(ident),
                line: tok_line,
            });
            prev_can_tuple_index = true;
            prev_is_tuple_dot = false;
            continue;
        }

        // 9. Numeric literals (including tuple index disambiguation)
        if b.is_ascii_digit() {
            let tok_line = line;
            if prev_is_tuple_dot {
                let start = pos;
                while pos < len && bytes[pos].is_ascii_digit() {
                    pos += 1;
                }
                // Check for invalid float suffix/exponent immediately attached to digits
                if pos < len && matches!(bytes[pos], b'e' | b'E' | b'f' | b'F' | b'_') {
                    // Fall back to full numeric classification from `start`.
                    pos = start;
                    let tok = lex_number_token(bytes, &mut pos, tok_line);
                    let can_idx = matches!(tok.kind, TokKind::TupleIndex);
                    tokens.push(tok);
                    prev_can_tuple_index = can_idx;
                    prev_is_tuple_dot = false;
                } else {
                    tokens.push(Token {
                        kind: TokKind::TupleIndex,
                        line: tok_line,
                    });
                    prev_can_tuple_index = true;
                    prev_is_tuple_dot = false;
                }
                continue;
            }

            let tok = lex_number_token(bytes, &mut pos, tok_line);
            tokens.push(tok);
            prev_can_tuple_index = false;
            prev_is_tuple_dot = false;
            continue;
        }

        // 10. Punctuation
        let tok_line = line;
        match b {
            b'.' => {
                if pos + 1 < len && bytes[pos + 1] == b'.' {
                    pos += 2;
                    tokens.push(Token {
                        kind: TokKind::DotDot,
                        line: tok_line,
                    });
                    prev_can_tuple_index = false;
                    prev_is_tuple_dot = false;
                } else {
                    pos += 1;
                    tokens.push(Token {
                        kind: TokKind::Dot,
                        line: tok_line,
                    });
                    prev_is_tuple_dot = prev_can_tuple_index;
                    prev_can_tuple_index = false;
                }
            }
            b'#' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::Hash,
                    line: tok_line,
                });
                prev_can_tuple_index = false;
                prev_is_tuple_dot = false;
            }
            b'!' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::Bang,
                    line: tok_line,
                });
                prev_can_tuple_index = false;
                prev_is_tuple_dot = false;
            }
            b'[' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::LBracket,
                    line: tok_line,
                });
                prev_can_tuple_index = false;
                prev_is_tuple_dot = false;
            }
            b']' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::RBracket,
                    line: tok_line,
                });
                prev_can_tuple_index = true;
                prev_is_tuple_dot = false;
            }
            b'(' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::LParen,
                    line: tok_line,
                });
                prev_can_tuple_index = false;
                prev_is_tuple_dot = false;
            }
            b')' => {
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::RParen,
                    line: tok_line,
                });
                prev_can_tuple_index = true;
                prev_is_tuple_dot = false;
            }
            _ => {
                // Skip non-ASCII UTF-8 bytes or other ASCII punctuation cleanly.
                pos += 1;
                tokens.push(Token {
                    kind: TokKind::Other,
                    line: tok_line,
                });
                prev_can_tuple_index = false;
                prev_is_tuple_dot = false;
            }
        }
    }

    tokens
}

fn match_raw_string_start(bytes: &[u8], pos: usize) -> Option<(usize, usize)> {
    let prefix_len = if bytes[pos] == b'r' {
        1
    } else if (bytes[pos] == b'b' || bytes[pos] == b'c')
        && pos + 1 < bytes.len()
        && bytes[pos + 1] == b'r'
    {
        2
    } else {
        return None;
    };
    let mut scan = pos + prefix_len;
    let mut hashes = 0usize;
    while scan < bytes.len() && bytes[scan] == b'#' {
        hashes += 1;
        scan += 1;
    }
    if scan < bytes.len() && bytes[scan] == b'"' {
        Some((prefix_len, hashes))
    } else {
        None
    }
}

fn consume_char_literal_body(bytes: &[u8], pos: &mut usize, line: &mut usize) {
    let len = bytes.len();
    while *pos < len {
        let c = bytes[*pos];
        if c == b'\\' {
            *pos = (*pos + 2).min(len);
        } else if c == b'\'' {
            *pos += 1;
            break;
        } else {
            if c == b'\n' {
                *line += 1;
            }
            *pos += 1;
        }
    }
}

/// If `src[pos..]` begins a Rust character literal (`'a'`, `'\n'`, `'\u{...}'`), returns
/// the byte offset immediately after the closing `'`. Returns `None` for lifetimes (`'a`, `'_`).
fn match_char_literal(src: &str, pos: usize) -> Option<usize> {
    let bytes = src.as_bytes();
    if bytes.get(pos) != Some(&b'\'') {
        return None;
    }
    let next = pos + 1;
    if next >= bytes.len() {
        return None;
    }
    if bytes[next] == b'\\' {
        // Escaped character literal: consume until unescaped closing `'` on same line.
        let mut scan = next + 1;
        if scan < bytes.len() {
            scan += 1; // skip escaped char
        }
        while scan < bytes.len() && bytes[scan] != b'\'' && bytes[scan] != b'\n' {
            scan += 1;
        }
        if scan < bytes.len() && bytes[scan] == b'\'' {
            return Some(scan + 1);
        }
        return None;
    }
    if bytes[next] == b'\'' || bytes[next] == b'\n' {
        return None;
    }
    // Single Unicode scalar followed immediately by `'`
    let rest = &src[next..];
    let ch = rest.chars().next()?;
    let after = next + ch.len_utf8();
    if bytes.get(after) == Some(&b'\'') {
        Some(after + 1)
    } else {
        None
    }
}

fn lex_number_token(bytes: &[u8], pos: &mut usize, line: usize) -> Token {
    let len = bytes.len();
    let start = *pos;

    // Non-decimal integer literals: 0x..., 0b..., 0o...
    if bytes[*pos] == b'0' && *pos + 1 < len {
        match bytes[*pos + 1] {
            b'x' | b'X' => {
                *pos += 2;
                while *pos < len && (bytes[*pos].is_ascii_hexdigit() || bytes[*pos] == b'_') {
                    *pos += 1;
                }
                let suf_start = *pos;
                while *pos < len && is_ident_continue(bytes[*pos]) {
                    *pos += 1;
                }
                let suf = std::str::from_utf8(&bytes[suf_start..*pos])
                    .unwrap_or("")
                    .trim_start_matches('_');
                if FORBIDDEN_FLOAT_TYPES.contains(&suf) {
                    let raw = std::str::from_utf8(&bytes[start..*pos]).unwrap_or("");
                    return Token {
                        kind: TokKind::FloatLit(raw.to_string()),
                        line,
                    };
                }
                return Token {
                    kind: TokKind::IntLit,
                    line,
                };
            }
            b'b' | b'B' => {
                *pos += 2;
                while *pos < len && matches!(bytes[*pos], b'0' | b'1' | b'_') {
                    *pos += 1;
                }
                let suf_start = *pos;
                while *pos < len && is_ident_continue(bytes[*pos]) {
                    *pos += 1;
                }
                let suf = std::str::from_utf8(&bytes[suf_start..*pos])
                    .unwrap_or("")
                    .trim_start_matches('_');
                if FORBIDDEN_FLOAT_TYPES.contains(&suf) {
                    let raw = std::str::from_utf8(&bytes[start..*pos]).unwrap_or("");
                    return Token {
                        kind: TokKind::FloatLit(raw.to_string()),
                        line,
                    };
                }
                return Token {
                    kind: TokKind::IntLit,
                    line,
                };
            }
            b'o' | b'O' => {
                *pos += 2;
                while *pos < len && (matches!(bytes[*pos], b'0'..=b'7' | b'_')) {
                    *pos += 1;
                }
                let suf_start = *pos;
                while *pos < len && is_ident_continue(bytes[*pos]) {
                    *pos += 1;
                }
                let suf = std::str::from_utf8(&bytes[suf_start..*pos])
                    .unwrap_or("")
                    .trim_start_matches('_');
                if FORBIDDEN_FLOAT_TYPES.contains(&suf) {
                    let raw = std::str::from_utf8(&bytes[start..*pos]).unwrap_or("");
                    return Token {
                        kind: TokKind::FloatLit(raw.to_string()),
                        line,
                    };
                }
                return Token {
                    kind: TokKind::IntLit,
                    line,
                };
            }
            _ => {}
        }
    }

    // Decimal literal: digits & underscores
    while *pos < len && (bytes[*pos].is_ascii_digit() || bytes[*pos] == b'_') {
        *pos += 1;
    }

    let mut is_float = false;

    // Check fractional decimal point (excluding `..` ranges and `.method()` calls)
    if *pos < len && bytes[*pos] == b'.' {
        let after_dot = bytes.get(*pos + 1).copied();
        match after_dot {
            Some(b'.') => {
                // Range operator `0..10` or `0..=10`: NOT a float literal.
            }
            Some(c) if is_ident_start(c) => {
                // Method call on integer literal like `10.abs()`: NOT a float literal.
            }
            Some(c) if c.is_ascii_digit() => {
                is_float = true;
                *pos += 1; // consume '.'
                while *pos < len && (bytes[*pos].is_ascii_digit() || bytes[*pos] == b'_') {
                    *pos += 1;
                }
            }
            _ => {
                // Trailing decimal point `1.` followed by `;`, `,`, `)`, whitespace, op, EOF -> Rust float literal!
                is_float = true;
                *pos += 1;
            }
        }
    }

    // Check scientific exponent `e`/`E`
    if *pos < len && matches!(bytes[*pos], b'e' | b'E') {
        is_float = true;
        *pos += 1;
        if *pos < len && matches!(bytes[*pos], b'+' | b'-') {
            *pos += 1;
        }
        while *pos < len && (bytes[*pos].is_ascii_digit() || bytes[*pos] == b'_') {
            *pos += 1;
        }
    }

    // Check suffix (`u32`, `i64`, `f64`, `_f32`, etc.)
    let suf_start = *pos;
    while *pos < len && is_ident_continue(bytes[*pos]) {
        *pos += 1;
    }
    let suf = std::str::from_utf8(&bytes[suf_start..*pos])
        .unwrap_or("")
        .trim_start_matches('_');
    if FORBIDDEN_FLOAT_TYPES.contains(&suf) {
        is_float = true;
    }

    if is_float {
        let raw = std::str::from_utf8(&bytes[start..*pos]).unwrap_or("");
        Token {
            kind: TokKind::FloatLit(raw.to_string()),
            line,
        }
    } else {
        Token {
            kind: TokKind::IntLit,
            line,
        }
    }
}

fn has_active_forbid_unsafe_code(tokens: &[Token]) -> bool {
    if tokens.len() < 8 {
        return false;
    }
    for win in tokens.windows(8) {
        if win[0].kind == TokKind::Hash
            && win[1].kind == TokKind::Bang
            && win[2].kind == TokKind::LBracket
            && matches!(&win[3].kind, TokKind::Ident(s) if s == "forbid")
            && win[4].kind == TokKind::LParen
            && matches!(&win[5].kind, TokKind::Ident(s) if s == "unsafe_code")
            && win[6].kind == TokKind::RParen
            && win[7].kind == TokKind::RBracket
        {
            return true;
        }
    }
    false
}

fn audit_rust_tokens(
    rel: &str,
    tokens: &[Token],
    require_forbid_unsafe: bool,
    violations: &mut Vec<PolicyViolation>,
) {
    for tok in tokens {
        match &tok.kind {
            TokKind::Ident(s) | TokKind::RawIdent(s) => {
                if FORBIDDEN_FLOAT_TYPES.contains(&s.as_str()) {
                    violations.push(PolicyViolation {
                        file: rel.to_string(),
                        line: tok.line,
                        rule: "forbidden_float_type".to_string(),
                        detail: format!("floating-point type token {:?} is forbidden", s),
                    });
                } else if s == "unsafe" {
                    violations.push(PolicyViolation {
                        file: rel.to_string(),
                        line: tok.line,
                        rule: "forbidden_unsafe".to_string(),
                        detail: "unsafe keyword is forbidden in crates/aod-core".to_string(),
                    });
                } else if s == "extern" {
                    violations.push(PolicyViolation {
                        file: rel.to_string(),
                        line: tok.line,
                        rule: "forbidden_extern".to_string(),
                        detail: "extern keyword is forbidden in crates/aod-core".to_string(),
                    });
                }
            }
            TokKind::FloatLit(raw) => {
                violations.push(PolicyViolation {
                    file: rel.to_string(),
                    line: tok.line,
                    rule: "forbidden_float_literal".to_string(),
                    detail: format!("floating-point literal {:?} is forbidden", raw),
                });
            }
            _ => {}
        }
    }

    if require_forbid_unsafe && !has_active_forbid_unsafe_code(tokens) {
        violations.push(PolicyViolation {
            file: rel.to_string(),
            line: 1,
            rule: "missing_forbid_unsafe_code".to_string(),
            detail: "missing active #![forbid(unsafe_code)] attribute".to_string(),
        });
    }
}

/// Audit a crate root directory against all S4 zero-float, zero-unsafe, zero-dep, and hygiene rules.
pub fn audit_crate_tree(crate_root: &Path) -> Result<PolicyAudit, CoreError> {
    if !crate_root.is_dir() {
        return Err(CoreError::ValueError(
            "crate root directory does not exist".to_string(),
        ));
    }
    let mut files: Vec<(String, std::path::PathBuf)> = Vec::new();
    let mut violations: Vec<PolicyViolation> = Vec::new();
    walk_crate_tree(crate_root, crate_root, "", &mut files, &mut violations)?;
    files.sort_by(|a, b| a.0.cmp(&b.0));

    let mut audited_rust_files = 0usize;
    let mut audited_text_files = 0usize;
    let mut json_files_under_crate = 0usize;
    let mut cargo_lock_packages = 0usize;
    let mut saw_cargo_toml = false;
    let mut saw_cargo_lock = false;
    let mut saw_lib_rs = false;
    let mut saw_main_rs = false;
    let mut forbid_unsafe_checked_files: Vec<String> = Vec::new();

    for (rel, path) in &files {
        if rel.ends_with(".json") {
            json_files_under_crate += 1;
            violations.push(PolicyViolation {
                file: rel.clone(),
                line: 0,
                rule: "forbidden_json_under_crate".to_string(),
                detail: ".json files are forbidden under crates/aod-core".to_string(),
            });
            continue;
        }

        let raw_bytes = fs::read(path)?;
        let text = match String::from_utf8(raw_bytes) {
            Ok(s) => s,
            Err(_) => {
                violations.push(PolicyViolation {
                    file: rel.clone(),
                    line: 0,
                    rule: "non_utf8_file".to_string(),
                    detail: "unexpected non-UTF-8 file inside crates/aod-core".to_string(),
                });
                continue;
            }
        };
        audited_text_files += 1;

        for (idx, line) in text.lines().enumerate() {
            if contains_forbidden_experimental_token(line) {
                violations.push(PolicyViolation {
                    file: rel.clone(),
                    line: idx + 1,
                    rule: "forbidden_experimental_token".to_string(),
                    detail: "forbidden experimental namespace token detected".to_string(),
                });
            }
        }

        if rel == "Cargo.toml" {
            saw_cargo_toml = true;
            audit_cargo_toml(rel, &text, &mut violations);
        } else if rel == "Cargo.lock" {
            saw_cargo_lock = true;
            cargo_lock_packages = audit_cargo_lock(rel, &text, &mut violations);
        } else if rel.ends_with(".rs") {
            audited_rust_files += 1;
            if rel == "src/lib.rs" {
                saw_lib_rs = true;
            }
            if rel == "src/main.rs" {
                saw_main_rs = true;
            }
            let require_forbid = rel == "src/lib.rs"
                || rel == "src/main.rs"
                || (rel.starts_with("tests/") && rel.ends_with(".rs"));
            if require_forbid {
                forbid_unsafe_checked_files.push(rel.clone());
            }
            let tokens = lex_rust_source(rel, &text, &mut violations);
            audit_rust_tokens(rel, &tokens, require_forbid, &mut violations);
        }
    }

    if !saw_cargo_toml {
        violations.push(PolicyViolation {
            file: "Cargo.toml".to_string(),
            line: 0,
            rule: "missing_manifest".to_string(),
            detail: "Cargo.toml is missing".to_string(),
        });
    }
    if !saw_cargo_lock {
        violations.push(PolicyViolation {
            file: "Cargo.lock".to_string(),
            line: 0,
            rule: "missing_lockfile".to_string(),
            detail: "Cargo.lock is missing".to_string(),
        });
    }
    if !saw_lib_rs {
        violations.push(PolicyViolation {
            file: "src/lib.rs".to_string(),
            line: 0,
            rule: "missing_lib_rs".to_string(),
            detail: "src/lib.rs is missing".to_string(),
        });
    }
    if !saw_main_rs {
        violations.push(PolicyViolation {
            file: "src/main.rs".to_string(),
            line: 0,
            rule: "missing_main_rs".to_string(),
            detail: "src/main.rs is missing".to_string(),
        });
    }

    forbid_unsafe_checked_files.sort();
    violations.sort_by(|a, b| {
        a.file
            .cmp(&b.file)
            .then(a.line.cmp(&b.line))
            .then(a.rule.cmp(&b.rule))
            .then(a.detail.cmp(&b.detail))
    });

    Ok(PolicyAudit {
        status: if violations.is_empty() {
            "PASS".to_string()
        } else {
            "FAIL".to_string()
        },
        audited_rust_files,
        audited_text_files,
        cargo_lock_packages,
        forbid_unsafe_checked_files,
        json_files_under_crate,
        violation_count: violations.len(),
        violations,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn audit_snippet(src: &str, require_forbid: bool) -> Vec<PolicyViolation> {
        let mut violations = Vec::new();
        let tokens = lex_rust_source("probe.rs", src, &mut violations);
        audit_rust_tokens("probe.rs", &tokens, require_forbid, &mut violations);
        violations
    }

    #[test]
    fn test_false_positive_immunity() {
        let benign = r##"
#![forbid(unsafe_code)]
// Comment with f64, 1.0, unsafe, extern
/* Nested /* block comment f32 0.5 unsafe */ still comment 1e5 */
pub fn demo<'a>(s: &'a str, pair: ((u32, u32), u32)) -> &'a str {
    let _msg = "f64 1.0 unsafe extern";
    let _raw = r#"f32 0.5 "unsafe" extern"#;
    let _c = 'a';
    let _esc = '\'';
    let _bs = b"f64";
    let _hex = 0x1e5 + 0x1f32;
    let _rng = 0..10;
    let _rng_eq = 0..=10;
    let _pow = 10u32.pow(2);
    let _abs = 10i64.abs();
    let _t0 = pair.0;
    let _t01 = pair.0.1;
    let _t1 = pair.1;
    s
}
"##;
        let v = audit_snippet(benign, true);
        assert!(v.is_empty(), "unexpected violations: {:?}", v);
    }

    #[test]
    fn test_adversarial_rust_probes_caught() {
        assert!(!audit_snippet("fn a(x: f64) {}", false).is_empty());
        assert!(!audit_snippet("fn a(x: f32) {}", false).is_empty());
        assert!(!audit_snippet("fn a() { let x = 1.0; }", false).is_empty());
        assert!(!audit_snippet("fn a() { let x = 1e5; }", false).is_empty());
        assert!(!audit_snippet("fn a() { let x = 1_f64; }", false).is_empty());
        assert!(!audit_snippet("fn a() { let x = 1.; }", false).is_empty());
        assert!(!audit_snippet("fn a<'a>(s: &'a str) { let x: f64 = 0.5; }", false).is_empty());
        assert!(!audit_snippet("fn a() { unsafe {} }", false).is_empty());
        assert!(!audit_snippet("extern \"C\" fn a() {}", false).is_empty());
        assert!(!audit_snippet("fn a() { let r#f64 = 1; }", false).is_empty());
        assert!(!audit_snippet("// #![forbid(unsafe_code)]\nfn a() {}", true).is_empty());
    }

    #[test]
    fn test_experimental_token_detection() {
        let probe_dash = format!("{}-{}", "aod", "dec");
        let probe_under = format!("{}_{}", "AOD", "DEC");
        assert!(contains_forbidden_experimental_token(&probe_dash));
        assert!(contains_forbidden_experimental_token(&probe_under));
        assert!(!contains_forbidden_experimental_token("aod-core"));
    }
}
