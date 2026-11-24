//! Strict numeric input boundary, banker's rounding, fixed formatting, and exact closeness.
//!
//! Mirrors `manual/engine/numeric.py` byte-for-byte with zero floating-point arithmetic.

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::CoreError;

/// Maximum permitted absolute decimal scale exponent (`|scale| <= 10_000`) to prevent OOM.
pub const MAX_ABS_DECIMAL_SCALE: i64 = 10_000;

/// Maximum permitted decimal places for fixed rounding/formatting.
pub const MAX_ROUNDING_DECIMALS: u32 = 10_000;

/// Parse a strict canonical integer string matching:
/// - `^(?:0|-?[1-9][0-9]*)$` when `allow_leading_plus == false`
/// - `^(?:0|[+-]?[1-9][0-9]*)$` when `allow_leading_plus == true`
pub fn parse_exact_int_str(token: &str, allow_leading_plus: bool) -> Result<BigInt, CoreError> {
    if token.is_empty() {
        return Err(CoreError::ValueError(
            "canonical integer token must not be empty".to_string(),
        ));
    }
    if token == "0" {
        return Ok(BigInt::zero());
    }
    let bytes = token.as_bytes();
    let (neg, digits) = match bytes[0] {
        b'-' => (true, &token[1..]),
        b'+' if allow_leading_plus => (false, &token[1..]),
        b'1'..=b'9' => (false, token),
        _ => {
            return Err(CoreError::ValueError(format!(
                "not a canonical integer token: {:?}",
                token
            )));
        }
    };
    let dbytes = digits.as_bytes();
    if dbytes.is_empty()
        || !(b'1'..=b'9').contains(&dbytes[0])
        || !dbytes.iter().all(|b| b.is_ascii_digit())
    {
        return Err(CoreError::ValueError(format!(
            "not a canonical integer token: {:?}",
            token
        )));
    }
    BigInt::from_ascii_digits(digits, neg)
}

/// Parse a printed decimal or rational string losslessly into `BigRat`.
///
/// Rejects empty strings, whitespace, non-finite spellings (`NaN`/`Inf`), zero denominators,
/// and scales with `|scale| > MAX_ABS_DECIMAL_SCALE`.
pub fn parse_printed_rational(
    token: &str,
    allow_fraction_slash: bool,
    allow_exponent: bool,
) -> Result<BigRat, CoreError> {
    if token.is_empty() {
        return Err(CoreError::ValueError(
            "printed rational token must not be empty".to_string(),
        ));
    }
    if token.chars().any(|ch| ch.is_whitespace()) {
        return Err(CoreError::ValueError(format!(
            "printed rational token must not contain whitespace: {:?}",
            token
        )));
    }

    if token.contains('/') {
        if !allow_fraction_slash {
            return Err(CoreError::ValueError(format!(
                "fraction slash syntax is not allowed: {:?}",
                token
            )));
        }
        let (left, den_s) = token.split_once('/').ok_or_else(|| {
            CoreError::ValueError(format!("invalid rational token: {:?}", token))
        })?;
        if den_s.contains('/') || den_s.is_empty() || !den_s.bytes().all(|b| b.is_ascii_digit()) {
            return Err(CoreError::ValueError(format!(
                "invalid rational denominator: {:?}",
                token
            )));
        }
        let (neg, num_s) = if let Some(rest) = left.strip_prefix('-') {
            (true, rest)
        } else if let Some(rest) = left.strip_prefix('+') {
            (false, rest)
        } else {
            (false, left)
        };
        if num_s.is_empty() || !num_s.bytes().all(|b| b.is_ascii_digit()) {
            return Err(CoreError::ValueError(format!(
                "invalid rational numerator: {:?}",
                token
            )));
        }
        let den = BigInt::from_ascii_digits(den_s, false)?;
        if !den.is_positive() {
            return Err(CoreError::ValueError(format!(
                "rational token must have a positive denominator: {:?}",
                token
            )));
        }
        let num = BigInt::from_ascii_digits(num_s, neg)?;
        return BigRat::new(num, den);
    }

    // Decimal spelling: ^([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$
    let (neg, rest) = if let Some(r) = token.strip_prefix('-') {
        (true, r)
    } else if let Some(r) = token.strip_prefix('+') {
        (false, r)
    } else {
        (false, token)
    };

    let (mantissa, exp_opt) = if let Some(pos) = rest.find(['e', 'E']) {
        if !allow_exponent {
            return Err(CoreError::ValueError(format!(
                "exponent syntax is not allowed in decimal token: {:?}",
                token
            )));
        }
        (&rest[..pos], Some(&rest[pos + 1..]))
    } else {
        (rest, None)
    };

    let (int_part, frac_part) = if let Some((ip, fp)) = mantissa.split_once('.') {
        if fp.contains('.') || fp.is_empty() || !fp.bytes().all(|b| b.is_ascii_digit()) {
            return Err(CoreError::ValueError(format!(
                "invalid decimal fractional part: {:?}",
                token
            )));
        }
        (ip, fp)
    } else {
        (mantissa, "")
    };

    if int_part.is_empty() || !int_part.bytes().all(|b| b.is_ascii_digit()) {
        return Err(CoreError::ValueError(format!(
            "invalid printed decimal token: {:?}",
            token
        )));
    }

    let exp_val: i128 = if let Some(exp_s) = exp_opt {
        let (exp_neg, exp_digits) = if let Some(r) = exp_s.strip_prefix('-') {
            (true, r)
        } else if let Some(r) = exp_s.strip_prefix('+') {
            (false, r)
        } else {
            (false, exp_s)
        };
        if exp_digits.is_empty() || !exp_digits.bytes().all(|b| b.is_ascii_digit()) {
            return Err(CoreError::ValueError(format!(
                "invalid decimal exponent: {:?}",
                token
            )));
        }
        let mut val: i128 = 0;
        for &b in exp_digits.as_bytes() {
            val = val
                .saturating_mul(10)
                .saturating_add((b - b'0') as i128);
            if val > (MAX_ABS_DECIMAL_SCALE as i128) + (frac_part.len() as i128) + 1 {
                return Err(CoreError::ValueError(format!(
                    "decimal scale exceeds limit {}: {:?}",
                    MAX_ABS_DECIMAL_SCALE, token
                )));
            }
        }
        if exp_neg {
            -val
        } else {
            val
        }
    } else {
        0
    };

    let scale: i128 = (frac_part.len() as i128) - exp_val;
    if scale.abs() > MAX_ABS_DECIMAL_SCALE as i128 {
        return Err(CoreError::ValueError(format!(
            "decimal scale {} exceeds limit {}",
            scale, MAX_ABS_DECIMAL_SCALE
        )));
    }

    let mut all_digits = String::with_capacity(int_part.len() + frac_part.len());
    all_digits.push_str(int_part);
    all_digits.push_str(frac_part);
    let digits = BigInt::from_ascii_digits(&all_digits, neg)?;

    if scale >= 0 {
        BigRat::new(digits, BigInt::pow10(scale as u32))
    } else {
        let mult = BigInt::pow10((-scale) as u32);
        BigRat::new(&digits * &mult, BigInt::one())
    }
}

/// Parse a canonical reduced rational pair `[num_str, den_str]`.
/// Rejects non-canonical integer tokens, non-positive denominators, and unreduced pairs.
pub fn parse_canonical_rational_pair(num_s: &str, den_s: &str) -> Result<BigRat, CoreError> {
    let num = parse_exact_int_str(num_s, false)?;
    let den = parse_exact_int_str(den_s, false)?;
    if !den.is_positive() {
        return Err(CoreError::ValueError(format!(
            "canonical rational denominator must be positive, got {}",
            den
        )));
    }
    let q = BigRat::new(num, den)?;
    let [canon_num, canon_den] = q.canonical_pair();
    if canon_num != num_s || canon_den != den_s {
        return Err(CoreError::ValueError(format!(
            "rational pair ({:?}, {:?}) is not in reduced canonical form (expected ({:?}, {:?}))",
            num_s, den_s, canon_num, canon_den
        )));
    }
    Ok(q)
}

/// Exact banker's rounding (round half to even) using pure integer arithmetic.
pub fn round_half_even(value: &BigRat, decimals: u32) -> Result<BigRat, CoreError> {
    if decimals > MAX_ROUNDING_DECIMALS {
        return Err(CoreError::ValueError(format!(
            "decimals {} exceeds limit {}",
            decimals, MAX_ROUNDING_DECIMALS
        )));
    }
    let scale = BigInt::pow10(decimals);
    let scaled = value * &BigRat::from_int(scale.clone());
    let num = scaled.num();
    let den = scaled.den();
    let neg = num.is_negative();
    let abs_num = num.abs();
    let (mut quot, rem) = abs_num.div_rem_trunc(den)?;
    let twice_rem = &rem + &rem;
    if twice_rem > *den || (twice_rem == *den && quot.is_odd()) {
        quot = &quot + &BigInt::one();
    }
    let signed_quot = if neg && !quot.is_zero() { -quot } else { quot };
    BigRat::new(signed_quot, scale)
}

/// Format an exact rational to a fixed-decimal string using exact half-to-even rounding.
/// Never emits `"-0"` or `"-0.000..."`.
pub fn format_fixed(value: &BigRat, decimals: u32) -> Result<String, CoreError> {
    let rounded = round_half_even(value, decimals)?;
    let scale = BigInt::pow10(decimals);
    let scaled = &rounded * &BigRat::from_int(scale.clone());
    if !scaled.den().is_one() {
        return Err(CoreError::ValueError(
            "rounded scaled value must be an exact integer".to_string(),
        ));
    }
    let scaled_int = scaled.num();
    let neg = scaled_int.is_negative();
    let mag = scaled_int.abs();
    let sign = if neg { "-" } else { "" };
    if decimals == 0 {
        return Ok(format!("{}{}", sign, mag.to_dec_string()));
    }
    let (int_part, frac_part) = mag.div_rem_trunc(&scale)?;
    let frac_raw = frac_part.to_dec_string();
    let dec_usize = decimals as usize;
    let pad = dec_usize.saturating_sub(frac_raw.len());
    let mut out = String::with_capacity(sign.len() + int_part.to_dec_string().len() + 1 + dec_usize);
    out.push_str(sign);
    out.push_str(&int_part.to_dec_string());
    out.push('.');
    for _ in 0..pad {
        out.push('0');
    }
    out.push_str(&frac_raw);
    Ok(out)
}

/// Exact rational closeness test mirroring `manual/engine/numeric.py:exact_isclose`.
pub fn exact_isclose(
    actual: &BigRat,
    expected: &BigRat,
    abs_tol: &BigRat,
    rel_tol: Option<&BigRat>,
) -> Result<bool, CoreError> {
    if abs_tol.is_negative() {
        return Err(CoreError::ValueError(
            "tol must be nonnegative".to_string(),
        ));
    }
    let rtol = rel_tol.unwrap_or(abs_tol);
    if rtol.is_negative() {
        return Err(CoreError::ValueError(
            "rel_tol must be nonnegative".to_string(),
        ));
    }
    let max_ab = actual.abs().max(expected.abs());
    let bound = (rtol * &max_ab).max(abs_tol.clone());
    Ok((actual - expected).abs() <= bound)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_exact_int_str() {
        assert_eq!(parse_exact_int_str("0", false).unwrap(), BigInt::zero());
        assert_eq!(parse_exact_int_str("-42", false).unwrap(), BigInt::from_i64(-42));
        assert!(parse_exact_int_str("-0", false).is_err());
        assert!(parse_exact_int_str("+1", false).is_err());
        assert_eq!(parse_exact_int_str("+1", true).unwrap(), BigInt::one());
        assert!(parse_exact_int_str("+0", true).is_err());
        assert!(parse_exact_int_str("01", false).is_err());
        assert!(parse_exact_int_str(" 1", false).is_err());
    }

    #[test]
    fn test_parse_printed_rational_and_rejections() {
        assert_eq!(
            parse_printed_rational("0.16", false, false).unwrap(),
            BigRat::from_i64_pair(4, 25).unwrap()
        );
        assert_eq!(
            parse_printed_rational("-0.05", false, false).unwrap(),
            BigRat::from_i64_pair(-1, 20).unwrap()
        );
        assert_eq!(
            parse_printed_rational("3/4", true, false).unwrap(),
            BigRat::from_i64_pair(3, 4).unwrap()
        );
        assert!(parse_printed_rational("3/4", false, false).is_err());
        assert_eq!(
            parse_printed_rational("1.25e-2", false, true).unwrap(),
            BigRat::from_i64_pair(1, 80).unwrap()
        );
        for bad in ["NaN", "Inf", "-inf", "Infinity", "1/0", " 1/2", "1.2.3", "", ".5", "5."] {
            assert!(
                matches!(
                    parse_printed_rational(bad, true, false),
                    Err(CoreError::ValueError(_))
                ),
                "expected ValueError for {:?}",
                bad
            );
        }
        assert!(parse_printed_rational("1e10001", false, true).is_err());
    }

    #[test]
    fn test_bankers_rounding_and_no_negative_zero() {
        // Half-to-even ties
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(1, 2).unwrap(), 0).unwrap(),
            "0"
        );
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(3, 2).unwrap(), 0).unwrap(),
            "2"
        );
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(-1, 2).unwrap(), 0).unwrap(),
            "0"
        );
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(-3, 2).unwrap(), 0).unwrap(),
            "-2"
        );
        // Very small negative value rounding to zero must NEVER emit "-0.000000"
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(-1, 10_000_000).unwrap(), 6).unwrap(),
            "0.000000"
        );
        // SD-004 exact check: -14/15 -> "-0.933333"
        assert_eq!(
            format_fixed(&BigRat::from_i64_pair(-14, 15).unwrap(), 6).unwrap(),
            "-0.933333"
        );
    }

    #[test]
    fn test_canonical_pair_rejects_unreduced() {
        assert_eq!(
            parse_canonical_rational_pair("1", "2").unwrap(),
            BigRat::from_i64_pair(1, 2).unwrap()
        );
        assert!(parse_canonical_rational_pair("2", "4").is_err());
        assert!(parse_canonical_rational_pair("0", "2").is_err());
        assert!(parse_canonical_rational_pair("1", "-2").is_err());
        assert!(parse_canonical_rational_pair("1", "0").is_err());
    }
}
