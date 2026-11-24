//! Strict zero-float `std`-only RFC 8259 JSON parser and deterministic canonical serializer.
//!
//! Structural guarantees:
//! - `JsonValue` has NO floating-point variant.
//! - Rejects JSON float literals (`.`/`e`/`E`) and non-finite constants (`NaN`/`Infinity`) with `CoreError::FloatLiteral`.
//! - Rejects duplicate object keys, nesting depth > 64, trailing non-whitespace bytes,
//!   unescaped control characters, and lone/invalid UTF-16 surrogates.
//! - Serializes with sorted keys (`BTreeMap`), 2-space indent, ASCII `\uXXXX` escaping,
//!   and trailing LF matching Python `json.dumps(..., sort_keys=True, indent=2, ensure_ascii=True) + "\n"`.

use std::collections::BTreeMap;

use crate::bigint::BigInt;
use crate::CoreError;

pub const MAX_JSON_DEPTH: usize = 64;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JsonValue {
    Null,
    Bool(bool),
    Int(BigInt),
    Str(String),
    Array(Vec<JsonValue>),
    Object(BTreeMap<String, JsonValue>),
}

impl JsonValue {
    pub fn as_object(&self) -> Option<&BTreeMap<String, JsonValue>> {
        match self {
            JsonValue::Object(m) => Some(m),
            _ => None,
        }
    }

    pub fn as_array(&self) -> Option<&[JsonValue]> {
        match self {
            JsonValue::Array(v) => Some(v),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            JsonValue::Str(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_int(&self) -> Option<&BigInt> {
        match self {
            JsonValue::Int(i) => Some(i),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            JsonValue::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn type_name(&self) -> &'static str {
        match self {
            JsonValue::Null => "null",
            JsonValue::Bool(_) => "bool",
            JsonValue::Int(_) => "int",
            JsonValue::Str(_) => "str",
            JsonValue::Array(_) => "array",
            JsonValue::Object(_) => "object",
        }
    }
}

struct Parser<'a> {
    bytes: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            bytes: input.as_bytes(),
            pos: 0,
        }
    }

    fn peek(&self) -> Option<u8> {
        self.bytes.get(self.pos).copied()
    }

    fn skip_ws(&mut self) {
        while let Some(b) = self.peek() {
            if matches!(b, b' ' | b'\t' | b'\r' | b'\n') {
                self.pos += 1;
            } else {
                break;
            }
        }
    }

    fn starts_with(&self, literal: &[u8]) -> bool {
        self.bytes[self.pos..].starts_with(literal)
    }

    fn parse_value(&mut self, depth: usize) -> Result<JsonValue, CoreError> {
        self.skip_ws();
        let b = self.peek().ok_or_else(|| {
            CoreError::JsonParse("unexpected end of JSON input".to_string())
        })?;
        match b {
            b'{' => self.parse_object(depth + 1),
            b'[' => self.parse_array(depth + 1),
            b'"' => self.parse_string().map(JsonValue::Str),
            b't' => self.parse_literal(b"true", JsonValue::Bool(true)),
            b'f' => self.parse_literal(b"false", JsonValue::Bool(false)),
            b'n' => self.parse_literal(b"null", JsonValue::Null),
            b'N' if self.starts_with(b"NaN") => Err(CoreError::FloatLiteral(
                "non-finite JSON literal NaN is forbidden".to_string(),
            )),
            b'I' if self.starts_with(b"Infinity") => Err(CoreError::FloatLiteral(
                "non-finite JSON literal Infinity is forbidden".to_string(),
            )),
            b'-' if self.starts_with(b"-Infinity") => Err(CoreError::FloatLiteral(
                "non-finite JSON literal -Infinity is forbidden".to_string(),
            )),
            b'-' | b'0'..=b'9' => self.parse_integer(),
            _ => Err(CoreError::JsonParse(format!(
                "unexpected byte 0x{:02x} at offset {}",
                b, self.pos
            ))),
        }
    }

    fn parse_literal(&mut self, lit: &[u8], val: JsonValue) -> Result<JsonValue, CoreError> {
        if self.starts_with(lit) {
            self.pos += lit.len();
            Ok(val)
        } else {
            Err(CoreError::JsonParse(format!(
                "invalid JSON literal at offset {}",
                self.pos
            )))
        }
    }

    fn parse_object(&mut self, depth: usize) -> Result<JsonValue, CoreError> {
        if depth > MAX_JSON_DEPTH {
            return Err(CoreError::JsonParse(format!(
                "JSON nesting depth exceeds maximum {}",
                MAX_JSON_DEPTH
            )));
        }
        self.pos += 1; // consume '{'
        self.skip_ws();
        let mut map = BTreeMap::new();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(JsonValue::Object(map));
        }
        loop {
            self.skip_ws();
            if self.peek() != Some(b'"') {
                return Err(CoreError::JsonParse(format!(
                    "expected JSON object key string at offset {}",
                    self.pos
                )));
            }
            let key = self.parse_string()?;
            self.skip_ws();
            if self.peek() != Some(b':') {
                return Err(CoreError::JsonParse(format!(
                    "expected ':' after JSON object key at offset {}",
                    self.pos
                )));
            }
            self.pos += 1;
            let val = self.parse_value(depth)?;
            if map.contains_key(&key) {
                return Err(CoreError::JsonParse(format!(
                    "duplicate JSON object key: {:?}",
                    key
                )));
            }
            map.insert(key, val);
            self.skip_ws();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                }
                Some(b'}') => {
                    self.pos += 1;
                    return Ok(JsonValue::Object(map));
                }
                _ => {
                    return Err(CoreError::JsonParse(format!(
                        "expected ',' or '}}' in JSON object at offset {}",
                        self.pos
                    )));
                }
            }
        }
    }

    fn parse_array(&mut self, depth: usize) -> Result<JsonValue, CoreError> {
        if depth > MAX_JSON_DEPTH {
            return Err(CoreError::JsonParse(format!(
                "JSON nesting depth exceeds maximum {}",
                MAX_JSON_DEPTH
            )));
        }
        self.pos += 1; // consume '['
        self.skip_ws();
        let mut items = Vec::new();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(JsonValue::Array(items));
        }
        loop {
            let item = self.parse_value(depth)?;
            items.push(item);
            self.skip_ws();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                }
                Some(b']') => {
                    self.pos += 1;
                    return Ok(JsonValue::Array(items));
                }
                _ => {
                    return Err(CoreError::JsonParse(format!(
                        "expected ',' or ']' in JSON array at offset {}",
                        self.pos
                    )));
                }
            }
        }
    }

    fn parse_integer(&mut self) -> Result<JsonValue, CoreError> {
        let neg = if self.peek() == Some(b'-') {
            self.pos += 1;
            true
        } else {
            false
        };
        let digits_start = self.pos;
        match self.peek() {
            Some(b'0') => {
                self.pos += 1;
                if matches!(self.peek(), Some(b'0'..=b'9')) {
                    return Err(CoreError::JsonParse(format!(
                        "leading zero forbidden in JSON number at offset {}",
                        digits_start
                    )));
                }
            }
            Some(b'1'..=b'9') => {
                self.pos += 1;
                while matches!(self.peek(), Some(b'0'..=b'9')) {
                    self.pos += 1;
                }
            }
            _ => {
                return Err(CoreError::JsonParse(format!(
                    "expected digit in JSON number at offset {}",
                    self.pos
                )));
            }
        }
        let digits_end = self.pos;
        if matches!(self.peek(), Some(b'.' | b'e' | b'E')) {
            return Err(CoreError::FloatLiteral(
                "floating-point JSON literal is forbidden in zero-float payload".to_string(),
            ));
        }
        let digits = std::str::from_utf8(&self.bytes[digits_start..digits_end]).map_err(|_| {
            CoreError::JsonParse("invalid UTF-8 in JSON integer".to_string())
        })?;
        let val = BigInt::from_ascii_digits(digits, neg)?;
        Ok(JsonValue::Int(val))
    }

    fn parse_hex4(&mut self) -> Result<u16, CoreError> {
        if self.pos + 4 > self.bytes.len() {
            return Err(CoreError::JsonParse(
                "truncated \\uXXXX escape in JSON string".to_string(),
            ));
        }
        let mut val: u16 = 0;
        for _ in 0..4 {
            let b = self.bytes[self.pos];
            self.pos += 1;
            let nibble = match b {
                b'0'..=b'9' => (b - b'0') as u16,
                b'a'..=b'f' => (b - b'a' + 10) as u16,
                b'A'..=b'F' => (b - b'A' + 10) as u16,
                _ => {
                    return Err(CoreError::JsonParse(format!(
                        "invalid hex digit in \\uXXXX escape at offset {}",
                        self.pos - 1
                    )));
                }
            };
            val = (val << 4) | nibble;
        }
        Ok(val)
    }

    fn parse_string(&mut self) -> Result<String, CoreError> {
        if self.peek() != Some(b'"') {
            return Err(CoreError::JsonParse(format!(
                "expected '\"' at offset {}",
                self.pos
            )));
        }
        self.pos += 1;
        let mut out = String::new();
        while self.pos < self.bytes.len() {
            let b = self.bytes[self.pos];
            if b == b'"' {
                self.pos += 1;
                return Ok(out);
            }
            if b < 0x20 {
                return Err(CoreError::JsonParse(format!(
                    "unescaped control character 0x{:02x} in JSON string at offset {}",
                    b, self.pos
                )));
            }
            if b == b'\\' {
                self.pos += 1;
                let esc = self.peek().ok_or_else(|| {
                    CoreError::JsonParse("unterminated escape sequence in JSON string".to_string())
                })?;
                self.pos += 1;
                match esc {
                    b'"' => out.push('"'),
                    b'\\' => out.push('\\'),
                    b'/' => out.push('/'),
                    b'b' => out.push('\u{0008}'),
                    b'f' => out.push('\u{000c}'),
                    b'n' => out.push('\n'),
                    b'r' => out.push('\r'),
                    b't' => out.push('\t'),
                    b'u' => {
                        let code = self.parse_hex4()?;
                        if (0xD800..=0xDBFF).contains(&code) {
                            // High surrogate MUST be immediately followed by \uXXXX low surrogate.
                            if !self.starts_with(b"\\u") {
                                return Err(CoreError::JsonParse(
                                    "lone high UTF-16 surrogate in JSON string".to_string(),
                                ));
                            }
                            self.pos += 2;
                            let low = self.parse_hex4()?;
                            if !(0xDC00..=0xDFFF).contains(&low) {
                                return Err(CoreError::JsonParse(
                                    "invalid low UTF-16 surrogate after high surrogate".to_string(),
                                ));
                            }
                            let cp = 0x10000u32
                                + (((code as u32) - 0xD800) << 10)
                                + ((low as u32) - 0xDC00);
                            let ch = char::from_u32(cp).ok_or_else(|| {
                                CoreError::JsonParse("invalid Unicode scalar from surrogate pair".to_string())
                            })?;
                            out.push(ch);
                        } else if (0xDC00..=0xDFFF).contains(&code) {
                            return Err(CoreError::JsonParse(
                                "unexpected lone low UTF-16 surrogate in JSON string".to_string(),
                            ));
                        } else {
                            let ch = char::from_u32(code as u32).ok_or_else(|| {
                                CoreError::JsonParse("invalid Unicode scalar in \\uXXXX".to_string())
                            })?;
                            out.push(ch);
                        }
                    }
                    _ => {
                        return Err(CoreError::JsonParse(format!(
                            "invalid JSON escape \\{} at offset {}",
                            esc as char,
                            self.pos - 1
                        )));
                    }
                }
            } else {
                // Consume valid UTF-8 scalar value from the input &str slice.
                let rest = std::str::from_utf8(&self.bytes[self.pos..]).map_err(|_| {
                    CoreError::JsonParse("invalid UTF-8 in JSON string".to_string())
                })?;
                let ch = rest.chars().next().ok_or_else(|| {
                    CoreError::JsonParse("unexpected end of JSON string".to_string())
                })?;
                out.push(ch);
                self.pos += ch.len_utf8();
            }
        }
        Err(CoreError::JsonParse(
            "unterminated JSON string literal".to_string(),
        ))
    }
}

/// Parse a strict RFC 8259 zero-float JSON document.
pub fn parse_json(input: &str) -> Result<JsonValue, CoreError> {
    let mut parser = Parser::new(input);
    let val = parser.parse_value(0)?;
    parser.skip_ws();
    if parser.pos != parser.bytes.len() {
        return Err(CoreError::JsonParse(format!(
            "trailing non-whitespace data after JSON root at offset {}",
            parser.pos
        )));
    }
    Ok(val)
}

fn push_escaped_str(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{0008}' => out.push_str("\\b"),
            '\u{000c}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c if (c as u32) <= 0x7E => {
                out.push(c);
            }
            c => {
                let code = c as u32;
                if code <= 0xFFFF {
                    out.push_str(&format!("\\u{:04x}", code));
                } else {
                    let v = code - 0x10000;
                    let hi = 0xD800 + (v >> 10);
                    let lo = 0xDC00 + (v & 0x3FF);
                    out.push_str(&format!("\\u{:04x}\\u{:04x}", hi, lo));
                }
            }
        }
    }
    out.push('"');
}

fn write_pretty(value: &JsonValue, indent: usize, out: &mut String) {
    match value {
        JsonValue::Null => out.push_str("null"),
        JsonValue::Bool(true) => out.push_str("true"),
        JsonValue::Bool(false) => out.push_str("false"),
        JsonValue::Int(i) => out.push_str(&i.to_dec_string()),
        JsonValue::Str(s) => push_escaped_str(s, out),
        JsonValue::Array(items) => {
            if items.is_empty() {
                out.push_str("[]");
                return;
            }
            out.push_str("[\n");
            let child_indent = indent + 2;
            for (idx, item) in items.iter().enumerate() {
                for _ in 0..child_indent {
                    out.push(' ');
                }
                write_pretty(item, child_indent, out);
                if idx + 1 < items.len() {
                    out.push(',');
                }
                out.push('\n');
            }
            for _ in 0..indent {
                out.push(' ');
            }
            out.push(']');
        }
        JsonValue::Object(map) => {
            if map.is_empty() {
                out.push_str("{}");
                return;
            }
            out.push_str("{\n");
            let child_indent = indent + 2;
            let len = map.len();
            for (idx, (k, v)) in map.iter().enumerate() {
                for _ in 0..child_indent {
                    out.push(' ');
                }
                push_escaped_str(k, out);
                out.push_str(": ");
                write_pretty(v, child_indent, out);
                if idx + 1 < len {
                    out.push(',');
                }
                out.push('\n');
            }
            for _ in 0..indent {
                out.push(' ');
            }
            out.push('}');
        }
    }
}

/// Deterministic canonical JSON serializer matching Python
/// `json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"`.
pub fn to_canonical_json_pretty(value: &JsonValue) -> String {
    let mut out = String::new();
    write_pretty(value, 0, &mut out);
    out.push('\n');
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rejects_floats_dups_trailing_depth_surrogates() {
        assert!(matches!(
            parse_json("{\"x\": 0.1}"),
            Err(CoreError::FloatLiteral(_))
        ));
        assert!(matches!(
            parse_json("1e5"),
            Err(CoreError::FloatLiteral(_))
        ));
        assert!(matches!(
            parse_json("NaN"),
            Err(CoreError::FloatLiteral(_))
        ));
        assert!(matches!(
            parse_json("{\"a\": 1, \"a\": 2}"),
            Err(CoreError::JsonParse(_))
        ));
        assert!(matches!(
            parse_json("{\"a\": 1} trailing"),
            Err(CoreError::JsonParse(_))
        ));
        assert!(matches!(
            parse_json("\"\\uD800\""),
            Err(CoreError::JsonParse(_))
        ));
        assert!(matches!(
            parse_json("\"\\uDC00\""),
            Err(CoreError::JsonParse(_))
        ));
        assert!(matches!(
            parse_json("\"a\nb\""),
            Err(CoreError::JsonParse(_))
        ));

        // Valid surrogate pair U+1F600
        let smiley = parse_json("\"\\uD83D\\uDE00\"").unwrap();
        assert_eq!(smiley, JsonValue::Str("\u{1F600}".to_string()));
        assert_eq!(to_canonical_json_pretty(&smiley), "\"\\ud83d\\ude00\"\n");

        // Depth 64 succeeds, depth 65 fails
        let ok_deep = format!("{}{}", "[".repeat(64), "]".repeat(64));
        assert!(parse_json(&ok_deep).is_ok());
        let too_deep = format!("{}{}", "[".repeat(65), "]".repeat(65));
        assert!(matches!(parse_json(&too_deep), Err(CoreError::JsonParse(_))));
    }

    #[test]
    fn test_canonical_serialization_and_bigint_roundtrip() {
        let big = "999999999999999999999999999999999999999999999999999999999999";
        let raw = format!("{{\"b\": {}, \"a\": [], \"c\": {{}}}}", big);
        let val = parse_json(&raw).unwrap();
        let ser = to_canonical_json_pretty(&val);
        let expected = format!("{{\n  \"a\": [],\n  \"b\": {},\n  \"c\": {{}}\n}}\n", big);
        assert_eq!(ser, expected);
        assert_eq!(parse_json(&ser).unwrap(), val);
    }
}
