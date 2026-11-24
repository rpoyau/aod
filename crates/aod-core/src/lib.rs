#![forbid(unsafe_code)]

//! Optional `std`-only, zero-float, zero-`unsafe` arbitrary-precision exact
//! arithmetic core for Alpha Omega Dynamics (Stage 4).
//!
//! This crate independently implements arbitrary-precision integers (`BigInt`),
//! reduced rationals (`BigRat`), exact Gaussian and cyclotomic rings, a strict
//! zero-float JSON parser and canonical serializer, pure-Rust SHA-256, all 40
//! S4 cross-language golden vector operations, a Rust lexical policy auditor,
//! and deterministic canonical report generation.

pub mod bigint;
pub mod bigrat;
pub mod json;
pub mod numeric;
pub mod ops;
pub mod policy;
pub mod report;
pub mod rings;
pub mod sadar_sim;
pub mod sha256;
pub mod vectors;

use std::fmt;

pub const CRATE_NAME: &str = "aod-core";
pub const CRATE_VERSION: &str = "0.1.0";
pub const REPORT_SCHEMA: &str = "aod.s4.rust.report.v1";
pub const VECTOR_SCHEMA: &str = "aod.s4.vector.v1";
pub const BASE_COMMIT_BINDING: &str = "e5c86af96cb78fec6905478a2cc421d08983afa2";

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoreError {
    TypeError(String),
    ValueError(String),
    FloatLiteral(String),
    DivisionByZero(String),
    JsonParse(String),
    Io(String),
    UnsafePath(String),
    PolicyViolation(String),
}

impl CoreError {
    pub fn kind_name(&self) -> &'static str {
        match self {
            CoreError::TypeError(_) => "TypeError",
            CoreError::ValueError(_) => "ValueError",
            CoreError::FloatLiteral(_) => "FloatLiteral",
            CoreError::DivisionByZero(_) => "DivisionByZero",
            CoreError::JsonParse(_) => "JsonParse",
            CoreError::Io(_) => "Io",
            CoreError::UnsafePath(_) => "UnsafePath",
            CoreError::PolicyViolation(_) => "PolicyViolation",
        }
    }

    pub fn message(&self) -> &str {
        match self {
            CoreError::TypeError(m)
            | CoreError::ValueError(m)
            | CoreError::FloatLiteral(m)
            | CoreError::DivisionByZero(m)
            | CoreError::JsonParse(m)
            | CoreError::Io(m)
            | CoreError::UnsafePath(m)
            | CoreError::PolicyViolation(m) => m,
        }
    }
}

impl fmt::Display for CoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.kind_name(), self.message())
    }
}

impl std::error::Error for CoreError {}

impl From<std::io::Error> for CoreError {
    fn from(err: std::io::Error) -> Self {
        CoreError::Io(err.to_string())
    }
}
