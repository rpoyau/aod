//! Arbitrary-precision signed integer (`BigInt`) in little-endian base 2^32.
//!
//! Representation invariants:
//! - `limbs` stores little-endian base `2^32` digits with no trailing zero limbs.
//! - Zero is uniquely represented as `neg == false` and `limbs.is_empty()`.
//! - Zero floating-point operations and zero fixed-width overflow ceilings.

use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Mul, Neg, Sub};

use crate::CoreError;

const DEC_CHUNK_BASE: u32 = 1_000_000_000;
const DEC_CHUNK_DIGITS: usize = 9;

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct BigInt {
    neg: bool,
    limbs: Vec<u32>,
}

impl BigInt {
    pub fn zero() -> Self {
        Self {
            neg: false,
            limbs: Vec::new(),
        }
    }

    pub fn one() -> Self {
        Self {
            neg: false,
            limbs: vec![1],
        }
    }

    pub fn from_u32(v: u32) -> Self {
        if v == 0 {
            Self::zero()
        } else {
            Self {
                neg: false,
                limbs: vec![v],
            }
        }
    }

    pub fn from_u64(v: u64) -> Self {
        if v == 0 {
            return Self::zero();
        }
        let lo = v as u32;
        let hi = (v >> 32) as u32;
        let limbs = if hi == 0 { vec![lo] } else { vec![lo, hi] };
        Self { neg: false, limbs }
    }

    pub fn from_i64(v: i64) -> Self {
        if v == 0 {
            return Self::zero();
        }
        let neg = v < 0;
        let mag = v.unsigned_abs();
        let mut out = Self::from_u64(mag);
        out.neg = neg;
        out
    }

    pub fn from_u128(mut v: u128) -> Self {
        if v == 0 {
            return Self::zero();
        }
        let mut limbs = Vec::with_capacity(4);
        while v != 0 {
            limbs.push(v as u32);
            v >>= 32;
        }
        Self { neg: false, limbs }
    }

    pub fn from_i128(v: i128) -> Self {
        if v == 0 {
            return Self::zero();
        }
        let neg = v < 0;
        let mag = v.unsigned_abs();
        let mut out = Self::from_u128(mag);
        out.neg = neg;
        out
    }

    pub fn from_usize(v: usize) -> Self {
        Self::from_u128(v as u128)
    }

    fn normalize(&mut self) {
        while self.limbs.last() == Some(&0) {
            self.limbs.pop();
        }
        if self.limbs.is_empty() {
            self.neg = false;
        }
    }

    fn from_parts(neg: bool, limbs: Vec<u32>) -> Self {
        let mut out = Self { neg, limbs };
        out.normalize();
        out
    }

    /// Parse a non-empty string of ASCII decimal digits with an explicit sign flag.
    pub fn from_ascii_digits(digits: &str, neg: bool) -> Result<Self, CoreError> {
        if digits.is_empty() || !digits.bytes().all(|b| b.is_ascii_digit()) {
            return Err(CoreError::ValueError(
                "invalid ASCII decimal digit sequence".to_string(),
            ));
        }
        let bytes = digits.as_bytes();
        let mut limbs: Vec<u32> = Vec::new();
        let mut idx = 0usize;
        while idx < bytes.len() {
            let end = (idx + DEC_CHUNK_DIGITS).min(bytes.len());
            let mut chunk_val: u32 = 0;
            let mut chunk_mul: u32 = 1;
            for &b in &bytes[idx..end] {
                chunk_val = chunk_val * 10 + (b - b'0') as u32;
                chunk_mul *= 10;
            }
            mul_u32_add_in_place(&mut limbs, chunk_mul, chunk_val);
            idx = end;
        }
        Ok(Self::from_parts(neg, limbs))
    }

    pub fn is_zero(&self) -> bool {
        self.limbs.is_empty()
    }

    pub fn is_negative(&self) -> bool {
        self.neg && !self.limbs.is_empty()
    }

    pub fn is_positive(&self) -> bool {
        !self.neg && !self.limbs.is_empty()
    }

    pub fn is_one(&self) -> bool {
        !self.neg && self.limbs.len() == 1 && self.limbs[0] == 1
    }

    pub fn is_even(&self) -> bool {
        self.limbs.first().map_or(true, |&lo| (lo & 1) == 0)
    }

    pub fn is_odd(&self) -> bool {
        !self.is_even()
    }

    pub fn signum_i8(&self) -> i8 {
        if self.limbs.is_empty() {
            0
        } else if self.neg {
            -1
        } else {
            1
        }
    }

    pub fn abs(&self) -> Self {
        Self {
            neg: false,
            limbs: self.limbs.clone(),
        }
    }

    pub fn to_u32(&self) -> Option<u32> {
        if self.neg {
            return None;
        }
        match self.limbs.as_slice() {
            [] => Some(0),
            [a] => Some(*a),
            _ => None,
        }
    }

    pub fn to_u64(&self) -> Option<u64> {
        if self.neg {
            return None;
        }
        match self.limbs.as_slice() {
            [] => Some(0),
            [a] => Some(*a as u64),
            [a, b] => Some((*a as u64) | ((*b as u64) << 32)),
            _ => None,
        }
    }

    pub fn to_i64(&self) -> Option<i64> {
        let mag = match self.limbs.as_slice() {
            [] => 0u64,
            [a] => *a as u64,
            [a, b] => (*a as u64) | ((*b as u64) << 32),
            _ => return None,
        };
        if !self.neg {
            i64::try_from(mag).ok()
        } else if mag == (i64::MAX as u64) + 1 {
            Some(i64::MIN)
        } else if mag <= i64::MAX as u64 {
            Some(-(mag as i64))
        } else {
            None
        }
    }

    pub fn to_usize(&self) -> Option<usize> {
        self.to_u64().and_then(|v| usize::try_from(v).ok())
    }

    pub fn bit_len(&self) -> usize {
        bit_len_mag(&self.limbs)
    }

    /// Number of set bits in the binary representation of `|self|` (matches Python `int.bit_count`).
    pub fn bit_count(&self) -> usize {
        self.limbs.iter().map(|&w| w.count_ones() as usize).sum()
    }

    /// Bitwise XOR of two nonnegative `BigInt` values.
    pub fn bit_xor(&self, rhs: &Self) -> Result<Self, CoreError> {
        if self.is_negative() || rhs.is_negative() {
            return Err(CoreError::ValueError(
                "bit_xor requires nonnegative BigInt operands".to_string(),
            ));
        }
        let max_len = self.limbs.len().max(rhs.limbs.len());
        let mut out = Vec::with_capacity(max_len);
        for idx in 0..max_len {
            let a = self.limbs.get(idx).copied().unwrap_or(0);
            let b = rhs.limbs.get(idx).copied().unwrap_or(0);
            out.push(a ^ b);
        }
        Ok(Self::from_parts(false, out))
    }

    /// Exact left shift of magnitude by `shift` bits, preserving sign (zero remains zero).
    pub fn shl_usize(&self, shift: usize) -> Self {
        if self.is_zero() || shift == 0 {
            return self.clone();
        }
        let limbs = shl_mag(&self.limbs, shift);
        Self::from_parts(self.neg, limbs)
    }

    /// Exact exponentiation (`0^0 == 1`).
    pub fn pow_u32(&self, mut exp: u32) -> Self {
        if exp == 0 {
            return Self::one();
        }
        if self.is_zero() {
            return Self::zero();
        }
        if self.is_one() {
            return Self::one();
        }
        let mut result = Self::one();
        let mut base = self.clone();
        while exp > 0 {
            if (exp & 1) == 1 {
                result = &result * &base;
            }
            exp >>= 1;
            if exp > 0 {
                base = &base * &base;
            }
        }
        result
    }

    pub fn pow10(exp: u32) -> Self {
        Self::from_u32(10).pow_u32(exp)
    }

    /// Truncating division and remainder: `self == q * rhs + r`, `|r| < |rhs|`,
    /// and `r` has the sign of `self` (when nonzero).
    pub fn div_rem_trunc(&self, rhs: &Self) -> Result<(Self, Self), CoreError> {
        if rhs.is_zero() {
            return Err(CoreError::DivisionByZero(
                "BigInt division by zero".to_string(),
            ));
        }
        if self.is_zero() {
            return Ok((Self::zero(), Self::zero()));
        }
        let (q_mag, r_mag) = div_rem_mag(&self.limbs, &rhs.limbs);
        let q = Self::from_parts(self.neg ^ rhs.neg, q_mag);
        let r = Self::from_parts(self.neg, r_mag);
        Ok((q, r))
    }

    /// Euclidean division and remainder: `self == q * rhs + r` with `0 <= r < |rhs|`.
    /// For `rhs > 0`, this matches Python `divmod(self, rhs)` identically.
    pub fn div_rem_euclid(&self, rhs: &Self) -> Result<(Self, Self), CoreError> {
        let (mut q, mut r) = self.div_rem_trunc(rhs)?;
        if r.is_negative() {
            if rhs.is_positive() {
                q = &q - &Self::one();
                r = &r + rhs;
            } else {
                q = &q + &Self::one();
                r = &r - rhs;
            }
        }
        Ok((q, r))
    }

    /// Exact nonnegative Euclidean remainder modulo a positive `u64` (matches Python `self % modulus`).
    pub fn rem_euclid_u64(&self, modulus: u64) -> Result<u64, CoreError> {
        if modulus == 0 {
            return Err(CoreError::DivisionByZero(
                "BigInt modulo zero".to_string(),
            ));
        }
        let m = modulus as u128;
        let mut rem: u128 = 0;
        for &limb in self.limbs.iter().rev() {
            rem = ((rem << 32) | (limb as u128)) % m;
        }
        let rem_u64 = rem as u64;
        if self.neg && rem_u64 != 0 {
            Ok(modulus - rem_u64)
        } else {
            Ok(rem_u64)
        }
    }

    /// Exact nonnegative greatest common divisor using Stein's binary GCD algorithm.
    pub fn gcd(a: &Self, b: &Self) -> Self {
        if a.is_zero() {
            return b.abs();
        }
        if b.is_zero() {
            return a.abs();
        }
        let mut u = a.limbs.clone();
        let mut v = b.limbs.clone();
        let shift_u = trailing_zeros_mag(&u);
        let shift_v = trailing_zeros_mag(&v);
        let common_shift = shift_u.min(shift_v);
        if shift_u > 0 {
            u = shr_mag(&u, shift_u);
        }
        if shift_v > 0 {
            v = shr_mag(&v, shift_v);
        }
        loop {
            match cmp_mag(&u, &v) {
                Ordering::Equal => break,
                Ordering::Greater => {
                    sub_mag_in_place(&mut u, &v);
                    let tz = trailing_zeros_mag(&u);
                    if tz > 0 {
                        u = shr_mag(&u, tz);
                    }
                }
                Ordering::Less => {
                    sub_mag_in_place(&mut v, &u);
                    let tz = trailing_zeros_mag(&v);
                    if tz > 0 {
                        v = shr_mag(&v, tz);
                    }
                }
            }
        }
        let out = if common_shift > 0 {
            shl_mag(&u, common_shift)
        } else {
            u
        };
        Self::from_parts(false, out)
    }

    pub fn to_dec_string(&self) -> String {
        if self.is_zero() {
            return "0".to_string();
        }
        let mut cur = self.limbs.clone();
        let mut chunks: Vec<u32> = Vec::new();
        while !cur.is_empty() {
            let (q, r) = div_rem_u32_mag(&cur, DEC_CHUNK_BASE);
            chunks.push(r);
            cur = q;
        }
        let mut out = String::with_capacity(chunks.len() * DEC_CHUNK_DIGITS + 1);
        if self.neg {
            out.push('-');
        }
        if let Some(&top) = chunks.last() {
            out.push_str(&top.to_string());
        }
        for &chunk in chunks.iter().rev().skip(1) {
            let s = format!("{:09}", chunk);
            out.push_str(&s);
        }
        out
    }
}

impl fmt::Display for BigInt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.to_dec_string())
    }
}

impl fmt::Debug for BigInt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "BigInt({})", self.to_dec_string())
    }
}

impl Ord for BigInt {
    fn cmp(&self, other: &Self) -> Ordering {
        match (self.neg, other.neg) {
            (true, false) => Ordering::Less,
            (false, true) => Ordering::Greater,
            (false, false) => cmp_mag(&self.limbs, &other.limbs),
            (true, true) => cmp_mag(&other.limbs, &self.limbs),
        }
    }
}

impl PartialOrd for BigInt {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Neg for &BigInt {
    type Output = BigInt;
    fn neg(self) -> BigInt {
        if self.is_zero() {
            BigInt::zero()
        } else {
            BigInt {
                neg: !self.neg,
                limbs: self.limbs.clone(),
            }
        }
    }
}

impl Neg for BigInt {
    type Output = BigInt;
    fn neg(mut self) -> BigInt {
        if !self.is_zero() {
            self.neg = !self.neg;
        }
        self
    }
}

impl Add for &BigInt {
    type Output = BigInt;
    fn add(self, rhs: &BigInt) -> BigInt {
        if self.is_zero() {
            return rhs.clone();
        }
        if rhs.is_zero() {
            return self.clone();
        }
        if self.neg == rhs.neg {
            BigInt::from_parts(self.neg, add_mag(&self.limbs, &rhs.limbs))
        } else {
            match cmp_mag(&self.limbs, &rhs.limbs) {
                Ordering::Equal => BigInt::zero(),
                Ordering::Greater => {
                    BigInt::from_parts(self.neg, sub_mag(&self.limbs, &rhs.limbs))
                }
                Ordering::Less => BigInt::from_parts(rhs.neg, sub_mag(&rhs.limbs, &self.limbs)),
            }
        }
    }
}

impl Add for BigInt {
    type Output = BigInt;
    fn add(self, rhs: BigInt) -> BigInt {
        &self + &rhs
    }
}

impl Sub for &BigInt {
    type Output = BigInt;
    fn sub(self, rhs: &BigInt) -> BigInt {
        if rhs.is_zero() {
            return self.clone();
        }
        if self.is_zero() {
            return -rhs;
        }
        if self.neg != rhs.neg {
            BigInt::from_parts(self.neg, add_mag(&self.limbs, &rhs.limbs))
        } else {
            match cmp_mag(&self.limbs, &rhs.limbs) {
                Ordering::Equal => BigInt::zero(),
                Ordering::Greater => {
                    BigInt::from_parts(self.neg, sub_mag(&self.limbs, &rhs.limbs))
                }
                Ordering::Less => BigInt::from_parts(!self.neg, sub_mag(&rhs.limbs, &self.limbs)),
            }
        }
    }
}

impl Sub for BigInt {
    type Output = BigInt;
    fn sub(self, rhs: BigInt) -> BigInt {
        &self - &rhs
    }
}

impl Mul for &BigInt {
    type Output = BigInt;
    fn mul(self, rhs: &BigInt) -> BigInt {
        if self.is_zero() || rhs.is_zero() {
            return BigInt::zero();
        }
        let limbs = mul_mag(&self.limbs, &rhs.limbs);
        BigInt::from_parts(self.neg ^ rhs.neg, limbs)
    }
}

impl Mul for BigInt {
    type Output = BigInt;
    fn mul(self, rhs: BigInt) -> BigInt {
        &self * &rhs
    }
}

// ---------------------------------------------------------------------------
// Unsigned little-endian base-2^32 magnitude helpers
// ---------------------------------------------------------------------------

fn trim_mag(limbs: &mut Vec<u32>) {
    while limbs.last() == Some(&0) {
        limbs.pop();
    }
}

fn cmp_mag(a: &[u32], b: &[u32]) -> Ordering {
    let len_ord = a.len().cmp(&b.len());
    if len_ord != Ordering::Equal {
        return len_ord;
    }
    for (&x, &y) in a.iter().rev().zip(b.iter().rev()) {
        let ord = x.cmp(&y);
        if ord != Ordering::Equal {
            return ord;
        }
    }
    Ordering::Equal
}

fn add_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    let max_len = a.len().max(b.len());
    let mut out = Vec::with_capacity(max_len + 1);
    let mut carry: u64 = 0;
    for idx in 0..max_len {
        let av = a.get(idx).copied().unwrap_or(0) as u64;
        let bv = b.get(idx).copied().unwrap_or(0) as u64;
        let sum = av + bv + carry;
        out.push(sum as u32);
        carry = sum >> 32;
    }
    if carry != 0 {
        out.push(carry as u32);
    }
    trim_mag(&mut out);
    out
}

/// Requires `cmp_mag(a, b) != Ordering::Less`.
fn sub_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    let mut out = a.to_vec();
    sub_mag_in_place(&mut out, b);
    out
}

/// Computes `a -= b` in place; requires `a >= b`.
fn sub_mag_in_place(a: &mut Vec<u32>, b: &[u32]) {
    let mut borrow: u64 = 0;
    for idx in 0..a.len() {
        let av = a[idx] as u64;
        let bv = b.get(idx).copied().unwrap_or(0) as u64;
        let sub = bv + borrow;
        if av >= sub {
            a[idx] = (av - sub) as u32;
            borrow = 0;
        } else {
            a[idx] = ((1u64 << 32) + av - sub) as u32;
            borrow = 1;
        }
        if borrow == 0 && idx >= b.len() {
            break;
        }
    }
    trim_mag(a);
}

fn mul_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0u32; a.len() + b.len()];
    for (i, &av) in a.iter().enumerate() {
        if av == 0 {
            continue;
        }
        let av64 = av as u64;
        let mut carry: u64 = 0;
        for (j, &bv) in b.iter().enumerate() {
            // Max value: (2^32-1) + (2^32-1)*(2^32-1) + (2^32-1) = 2^64 - 1 == u64::MAX
            let acc = (out[i + j] as u64) + av64 * (bv as u64) + carry;
            out[i + j] = acc as u32;
            carry = acc >> 32;
        }
        let mut pos = i + b.len();
        while carry != 0 {
            let acc = (out[pos] as u64) + carry;
            out[pos] = acc as u32;
            carry = acc >> 32;
            pos += 1;
        }
    }
    trim_mag(&mut out);
    out
}

fn mul_u32_add_in_place(limbs: &mut Vec<u32>, mul: u32, add: u32) {
    let mul64 = mul as u64;
    let mut carry = add as u64;
    for limb in limbs.iter_mut() {
        let acc = (*limb as u64) * mul64 + carry;
        *limb = acc as u32;
        carry = acc >> 32;
    }
    if carry != 0 {
        limbs.push(carry as u32);
    }
    trim_mag(limbs);
}

fn div_rem_u32_mag(a: &[u32], d: u32) -> (Vec<u32>, u32) {
    let d64 = d as u64;
    let mut q = vec![0u32; a.len()];
    let mut rem: u64 = 0;
    for (idx, &limb) in a.iter().enumerate().rev() {
        let cur = (rem << 32) | (limb as u64);
        q[idx] = (cur / d64) as u32;
        rem = cur % d64;
    }
    trim_mag(&mut q);
    (q, rem as u32)
}

fn bit_len_mag(a: &[u32]) -> usize {
    match a.last() {
        None => 0,
        Some(&top) => (a.len() - 1) * 32 + (32 - top.leading_zeros() as usize),
    }
}

fn trailing_zeros_mag(a: &[u32]) -> usize {
    let mut tz = 0usize;
    for &w in a {
        if w == 0 {
            tz += 32;
        } else {
            tz += w.trailing_zeros() as usize;
            break;
        }
    }
    tz
}

fn shl_mag(a: &[u32], shift: usize) -> Vec<u32> {
    if a.is_empty() || shift == 0 {
        return a.to_vec();
    }
    let word_shift = shift / 32;
    let bit_shift = shift % 32;
    let mut out = vec![0u32; word_shift + a.len() + 1];
    if bit_shift == 0 {
        out[word_shift..word_shift + a.len()].copy_from_slice(a);
    } else {
        let inv = 32 - bit_shift;
        let mut carry: u32 = 0;
        for (idx, &w) in a.iter().enumerate() {
            out[word_shift + idx] = (w << bit_shift) | carry;
            carry = w >> inv;
        }
        out[word_shift + a.len()] = carry;
    }
    trim_mag(&mut out);
    out
}

fn shr_mag(a: &[u32], shift: usize) -> Vec<u32> {
    if a.is_empty() || shift == 0 {
        return a.to_vec();
    }
    let word_shift = shift / 32;
    if word_shift >= a.len() {
        return Vec::new();
    }
    let bit_shift = shift % 32;
    let new_len = a.len() - word_shift;
    let mut out = vec![0u32; new_len];
    if bit_shift == 0 {
        out.copy_from_slice(&a[word_shift..]);
    } else {
        let inv = 32 - bit_shift;
        for idx in 0..new_len {
            let lo = a[word_shift + idx] >> bit_shift;
            let hi = if word_shift + idx + 1 < a.len() {
                a[word_shift + idx + 1] << inv
            } else {
                0
            };
            out[idx] = lo | hi;
        }
    }
    trim_mag(&mut out);
    out
}

fn shl1_add_bit_in_place(limbs: &mut Vec<u32>, bit: u32) {
    let mut carry = bit & 1;
    for w in limbs.iter_mut() {
        let next_carry = *w >> 31;
        *w = (*w << 1) | carry;
        carry = next_carry;
    }
    if carry != 0 {
        limbs.push(carry);
    }
}

/// Exact multi-limb unsigned division returning `(quotient, remainder)`.
/// Requires `!b.is_empty()`.
fn div_rem_mag(a: &[u32], b: &[u32]) -> (Vec<u32>, Vec<u32>) {
    match cmp_mag(a, b) {
        Ordering::Less => return (Vec::new(), a.to_vec()),
        Ordering::Equal => return (vec![1], Vec::new()),
        Ordering::Greater => {}
    }
    if b.len() == 1 {
        let (q, r) = div_rem_u32_mag(a, b[0]);
        let r_vec = if r == 0 { Vec::new() } else { vec![r] };
        return (q, r_vec);
    }

    let n_bits = bit_len_mag(a);
    let mut q = vec![0u32; a.len()];
    let mut rem: Vec<u32> = Vec::with_capacity(b.len() + 1);

    for bit_idx in (0..n_bits).rev() {
        let word_idx = bit_idx / 32;
        let in_word = bit_idx % 32;
        let bit = (a[word_idx] >> in_word) & 1;
        shl1_add_bit_in_place(&mut rem, bit);
        if cmp_mag(&rem, b) != Ordering::Less {
            sub_mag_in_place(&mut rem, b);
            q[word_idx] |= 1u32 << in_word;
        }
    }
    trim_mag(&mut q);
    trim_mag(&mut rem);
    (q, rem)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_zero_and_sign_normalization() {
        let z = BigInt::from_ascii_digits("0000", true).unwrap();
        assert!(z.is_zero());
        assert!(!z.is_negative());
        assert_eq!(z.to_string(), "0");
        assert_eq!(-z.clone(), BigInt::zero());
        let a = BigInt::from_i64(42);
        let diff = &a - &a;
        assert!(diff.is_zero());
        assert!(!diff.is_negative());
        assert_eq!(diff.to_string(), "0");
    }

    #[test]
    fn test_i128_exhaustive_arithmetic_and_divmod() {
        let samples: [i128; 13] = [
            0,
            1,
            -1,
            2,
            -2,
            7,
            -7,
            (1i128 << 32) - 1,
            1i128 << 32,
            -(1i128 << 32),
            (1i128 << 64) + 1234567890123456789,
            -((1i128 << 64) + 9876543210987654321),
            i128::MAX / 4,
        ];
        for &x in &samples {
            let bx = BigInt::from_i128(x);
            assert_eq!(bx.to_string(), x.to_string());
            for &y in &samples {
                let by = BigInt::from_i128(y);
                assert_eq!((&bx + &by).to_string(), (x + y).to_string());
                assert_eq!((&bx - &by).to_string(), (x - y).to_string());
                if x.abs() < (1i128 << 60) && y.abs() < (1i128 << 60) {
                    assert_eq!((&bx * &by).to_string(), (x * y).to_string());
                }
                if y != 0 {
                    let (qt, rt) = bx.div_rem_trunc(&by).unwrap();
                    assert_eq!(qt.to_string(), (x / y).to_string());
                    assert_eq!(rt.to_string(), (x % y).to_string());
                    assert_eq!(&(&qt * &by) + &rt, bx);

                    let (qe, re) = bx.div_rem_euclid(&by).unwrap();
                    assert_eq!(&(&qe * &by) + &re, bx);
                    assert!(!re.is_negative());
                    assert!(re < by.abs());
                    if y > 0 {
                        assert_eq!(qe.to_string(), x.div_euclid(y).to_string());
                        assert_eq!(re.to_string(), x.rem_euclid(y).to_string());
                    }
                }
            }
        }
    }

    #[test]
    fn test_beyond_i128_mul_div_gcd_and_pow10() {
        let a = BigInt::from_ascii_digits(
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
            false,
        )
        .unwrap();
        let b = BigInt::from_ascii_digits(
            "98765432109876543210987654321098765432109876543210",
            false,
        )
        .unwrap();
        let prod = &a * &b;
        let (q, r) = prod.div_rem_trunc(&b).unwrap();
        assert_eq!(q, a);
        assert!(r.is_zero());

        let shifted = &prod + &BigInt::from_i64(777);
        let (q2, r2) = shifted.div_rem_trunc(&b).unwrap();
        assert_eq!(q2, a);
        assert_eq!(r2, BigInt::from_i64(777));

        let g = BigInt::gcd(&(&a * &BigInt::from_i64(17)), &(&a * &BigInt::from_i64(23)));
        assert_eq!(g, a);

        let p100 = BigInt::pow10(100);
        let s = p100.to_string();
        assert_eq!(s.len(), 101);
        assert!(s.starts_with('1'));
        assert!(s[1..].bytes().all(|ch| ch == b'0'));
    }

    #[test]
    fn test_rem_euclid_u64_and_bit_ops() {
        assert_eq!(BigInt::from_i64(-1).rem_euclid_u64(12).unwrap(), 11);
        assert_eq!(BigInt::from_i64(-12).rem_euclid_u64(12).unwrap(), 0);
        assert_eq!(BigInt::from_i64(-13).rem_euclid_u64(12).unwrap(), 11);
        assert_eq!(BigInt::from_i64(25).rem_euclid_u64(12).unwrap(), 1);
        let v = BigInt::from_i64(5);
        let t = BigInt::from_i64(13);
        let x = v.bit_xor(&t).unwrap();
        assert_eq!(x, BigInt::from_i64(8));
        assert_eq!(x.bit_count(), 1);
        assert_eq!(BigInt::one().shl_usize(4), BigInt::from_i64(16));
        assert_eq!(BigInt::zero().pow_u32(0), BigInt::one());
    }
}
