//! Reduced canonical arbitrary-precision rational (`BigRat`).
//!
//! Representation invariants:
//! - `den > 0` always.
//! - `gcd(|num|, den) == 1` always.
//! - Zero is uniquely represented as `(0, 1)`.

use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Mul, Neg, Sub};

use crate::bigint::BigInt;
use crate::CoreError;

#[derive(Clone, PartialEq, Eq, Hash)]
pub struct BigRat {
    num: BigInt,
    den: BigInt,
}

impl BigRat {
    pub fn zero() -> Self {
        Self {
            num: BigInt::zero(),
            den: BigInt::one(),
        }
    }

    pub fn one() -> Self {
        Self {
            num: BigInt::one(),
            den: BigInt::one(),
        }
    }

    pub fn from_int(num: BigInt) -> Self {
        Self {
            num,
            den: BigInt::one(),
        }
    }

    pub fn from_i64(num: i64) -> Self {
        Self::from_int(BigInt::from_i64(num))
    }

    pub fn from_i64_pair(num: i64, den: i64) -> Result<Self, CoreError> {
        Self::new(BigInt::from_i64(num), BigInt::from_i64(den))
    }

    pub fn new(mut num: BigInt, mut den: BigInt) -> Result<Self, CoreError> {
        if den.is_zero() {
            return Err(CoreError::DivisionByZero(
                "rational denominator cannot be zero".to_string(),
            ));
        }
        if num.is_zero() {
            return Ok(Self::zero());
        }
        if den.is_negative() {
            num = -num;
            den = -den;
        }
        let g = BigInt::gcd(&num, &den);
        if !g.is_one() {
            let (qn, rn) = num.div_rem_trunc(&g)?;
            let (qd, rd) = den.div_rem_trunc(&g)?;
            if !rn.is_zero() || !rd.is_zero() {
                return Err(CoreError::ValueError(
                    "internal GCD reduction invariant violated".to_string(),
                ));
            }
            num = qn;
            den = qd;
        }
        Ok(Self { num, den })
    }

    pub fn num(&self) -> &BigInt {
        &self.num
    }

    pub fn den(&self) -> &BigInt {
        &self.den
    }

    pub fn is_zero(&self) -> bool {
        self.num.is_zero()
    }

    pub fn is_negative(&self) -> bool {
        self.num.is_negative()
    }

    pub fn is_positive(&self) -> bool {
        self.num.is_positive()
    }

    pub fn abs(&self) -> Self {
        Self {
            num: self.num.abs(),
            den: self.den.clone(),
        }
    }

    pub fn checked_div(&self, rhs: &Self) -> Result<Self, CoreError> {
        if rhs.is_zero() {
            return Err(CoreError::DivisionByZero(
                "rational division by zero".to_string(),
            ));
        }
        if self.is_zero() {
            return Ok(Self::zero());
        }
        let inv = if rhs.num.is_negative() {
            Self {
                num: -&rhs.den,
                den: rhs.num.abs(),
            }
        } else {
            Self {
                num: rhs.den.clone(),
                den: rhs.num.clone(),
            }
        };
        Ok(self * &inv)
    }

    pub fn pow_u32(&self, exp: u32) -> Self {
        if exp == 0 {
            return Self::one();
        }
        if self.is_zero() {
            return Self::zero();
        }
        // Since gcd(|num|, den) == 1, gcd(|num|^exp, den^exp) == 1 and den^exp > 0.
        Self {
            num: self.num.pow_u32(exp),
            den: self.den.pow_u32(exp),
        }
    }

    pub fn canonical_pair(&self) -> [String; 2] {
        [self.num.to_dec_string(), self.den.to_dec_string()]
    }

    pub fn canonical_str(&self) -> String {
        if self.den.is_one() {
            self.num.to_dec_string()
        } else {
            format!("{}/{}", self.num.to_dec_string(), self.den.to_dec_string())
        }
    }
}

impl fmt::Display for BigRat {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.canonical_str())
    }
}

impl fmt::Debug for BigRat {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "BigRat({})", self.canonical_str())
    }
}

impl Ord for BigRat {
    fn cmp(&self, other: &Self) -> Ordering {
        if self.den == other.den {
            self.num.cmp(&other.num)
        } else {
            let lhs = &self.num * &other.den;
            let rhs = &other.num * &self.den;
            lhs.cmp(&rhs)
        }
    }
}

impl PartialOrd for BigRat {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Neg for &BigRat {
    type Output = BigRat;
    fn neg(self) -> BigRat {
        BigRat {
            num: -&self.num,
            den: self.den.clone(),
        }
    }
}

impl Neg for BigRat {
    type Output = BigRat;
    fn neg(mut self) -> BigRat {
        self.num = -self.num;
        self
    }
}

fn add_sub_impl(a: &BigRat, b: &BigRat, subtract: bool) -> BigRat {
    if b.is_zero() {
        return a.clone();
    }
    if a.is_zero() {
        return if subtract { -b } else { b.clone() };
    }
    let g = BigInt::gcd(&a.den, &b.den);
    let (a_den_red, b_den_red) = if g.is_one() {
        (a.den.clone(), b.den.clone())
    } else {
        let (ad, _) = a.den.div_rem_trunc(&g).expect("gcd divides den");
        let (bd, _) = b.den.div_rem_trunc(&g).expect("gcd divides den");
        (ad, bd)
    };
    let lhs = &a.num * &b_den_red;
    let rhs = &b.num * &a_den_red;
    let num = if subtract { &lhs - &rhs } else { &lhs + &rhs };
    let den = &a.den * &b_den_red;
    BigRat::new(num, den).expect("product of positive denominators is positive")
}

impl Add for &BigRat {
    type Output = BigRat;
    fn add(self, rhs: &BigRat) -> BigRat {
        add_sub_impl(self, rhs, false)
    }
}

impl Add for BigRat {
    type Output = BigRat;
    fn add(self, rhs: BigRat) -> BigRat {
        &self + &rhs
    }
}

impl Sub for &BigRat {
    type Output = BigRat;
    fn sub(self, rhs: &BigRat) -> BigRat {
        add_sub_impl(self, rhs, true)
    }
}

impl Sub for BigRat {
    type Output = BigRat;
    fn sub(self, rhs: BigRat) -> BigRat {
        &self - &rhs
    }
}

impl Mul for &BigRat {
    type Output = BigRat;
    fn mul(self, rhs: &BigRat) -> BigRat {
        if self.is_zero() || rhs.is_zero() {
            return BigRat::zero();
        }
        // Cross-reduce before multiplying so intermediates stay minimal.
        let g1 = BigInt::gcd(&self.num, &rhs.den);
        let g2 = BigInt::gcd(&rhs.num, &self.den);
        let (a_num, b_den) = if g1.is_one() {
            (self.num.clone(), rhs.den.clone())
        } else {
            (
                self.num.div_rem_trunc(&g1).expect("gcd divides num").0,
                rhs.den.div_rem_trunc(&g1).expect("gcd divides den").0,
            )
        };
        let (b_num, a_den) = if g2.is_one() {
            (rhs.num.clone(), self.den.clone())
        } else {
            (
                rhs.num.div_rem_trunc(&g2).expect("gcd divides num").0,
                self.den.div_rem_trunc(&g2).expect("gcd divides den").0,
            )
        };
        BigRat {
            num: &a_num * &b_num,
            den: &a_den * &b_den,
        }
    }
}

impl Mul for BigRat {
    type Output = BigRat;
    fn mul(self, rhs: BigRat) -> BigRat {
        &self * &rhs
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reduction_and_canonical_forms() {
        let q = BigRat::from_i64_pair(-6, -8).unwrap();
        assert_eq!(q.canonical_pair(), ["3", "4"]);
        assert_eq!(q.canonical_str(), "3/4");

        let q2 = BigRat::from_i64_pair(6, -8).unwrap();
        assert_eq!(q2.canonical_pair(), ["-3", "4"]);
        assert_eq!(q2.canonical_str(), "-3/4");

        let z = BigRat::from_i64_pair(0, -99).unwrap();
        assert_eq!(z.canonical_pair(), ["0", "1"]);
        assert_eq!(z.canonical_str(), "0");

        let i = BigRat::from_i64_pair(-10, 5).unwrap();
        assert_eq!(i.canonical_pair(), ["-2", "1"]);
        assert_eq!(i.canonical_str(), "-2");

        assert!(matches!(
            BigRat::from_i64_pair(1, 0),
            Err(CoreError::DivisionByZero(_))
        ));
    }

    #[test]
    fn test_arithmetic_and_ordering() {
        let a = BigRat::from_i64_pair(1, 6).unwrap();
        let b = BigRat::from_i64_pair(1, 3).unwrap();
        assert_eq!(&a + &b, BigRat::from_i64_pair(1, 2).unwrap());
        assert_eq!(&a - &b, BigRat::from_i64_pair(-1, 6).unwrap());
        assert_eq!(&a * &b, BigRat::from_i64_pair(1, 18).unwrap());
        assert_eq!(a.checked_div(&b).unwrap(), BigRat::from_i64_pair(1, 2).unwrap());
        assert!(a < b);
        assert!(-&b < -&a);
        assert_eq!(BigRat::zero().pow_u32(0), BigRat::one());
        assert_eq!(BigRat::from_i64_pair(-2, 3).unwrap().pow_u32(3), BigRat::from_i64_pair(-8, 27).unwrap());
    }
}
