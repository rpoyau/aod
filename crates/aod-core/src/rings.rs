//! Exact algebraic rings: Gaussian rationals `Q(i)` and cyclotomic ring `Q[x]/(x^4 - x^2 + 1)`.
//!
//! Uses exclusively exact `BigInt` and `BigRat` arithmetic (zero floats, zero external CAS).

use std::ops::{Add, Mul, Neg, Sub};

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::CoreError;

/// Exact element `re + im * I` of the Gaussian rational field `Q(i)`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct GaussianRat {
    pub re: BigRat,
    pub im: BigRat,
}

impl GaussianRat {
    pub fn zero() -> Self {
        Self {
            re: BigRat::zero(),
            im: BigRat::zero(),
        }
    }

    pub fn one() -> Self {
        Self {
            re: BigRat::one(),
            im: BigRat::zero(),
        }
    }

    pub fn imag_unit() -> Self {
        Self {
            re: BigRat::zero(),
            im: BigRat::one(),
        }
    }

    pub fn from_rat(re: BigRat) -> Self {
        Self {
            re,
            im: BigRat::zero(),
        }
    }

    pub fn new(re: BigRat, im: BigRat) -> Self {
        Self { re, im }
    }

    /// Exact power `I^exp` for arbitrary signed integer exponent using `exp mod 4`.
    pub fn pow_i(exp: &BigInt) -> Self {
        let r = exp.rem_euclid_u64(4).expect("modulus 4 is nonzero");
        match r {
            0 => Self::new(BigRat::one(), BigRat::zero()),
            1 => Self::new(BigRat::zero(), BigRat::one()),
            2 => Self::new(BigRat::from_i64(-1), BigRat::zero()),
            _ => Self::new(BigRat::zero(), BigRat::from_i64(-1)),
        }
    }

    pub fn conj(&self) -> Self {
        Self {
            re: self.re.clone(),
            im: -&self.im,
        }
    }

    /// Exact squared norm `re^2 + im^2 = z * conj(z)` in `Q`.
    pub fn norm_sq(&self) -> BigRat {
        &(&self.re * &self.re) + &(&self.im * &self.im)
    }

    pub fn div_rat(&self, divisor: &BigRat) -> Result<Self, CoreError> {
        Ok(Self {
            re: self.re.checked_div(divisor)?,
            im: self.im.checked_div(divisor)?,
        })
    }

    /// Canonical string representation matching SymPy `str(sp.simplify(re + im*I))` identically.
    pub fn to_sympy_string(&self) -> String {
        fn fmt_pos_imag(mag: &BigRat) -> String {
            let num = mag.num();
            let den = mag.den();
            if num.is_one() && den.is_one() {
                "I".to_string()
            } else if num.is_one() {
                format!("I/{}", den.to_dec_string())
            } else if den.is_one() {
                format!("{}*I", num.to_dec_string())
            } else {
                format!("{}*I/{}", num.to_dec_string(), den.to_dec_string())
            }
        }

        if self.re.is_zero() && self.im.is_zero() {
            return "0".to_string();
        }
        if self.im.is_zero() {
            return self.re.canonical_str();
        }
        if self.re.is_zero() {
            let mag = fmt_pos_imag(&self.im.abs());
            return if self.im.is_negative() {
                format!("-{}", mag)
            } else {
                mag
            };
        }
        let re_s = self.re.canonical_str();
        let im_mag = fmt_pos_imag(&self.im.abs());
        if self.im.is_negative() {
            format!("{} - {}", re_s, im_mag)
        } else {
            format!("{} + {}", re_s, im_mag)
        }
    }
}

impl Neg for &GaussianRat {
    type Output = GaussianRat;
    fn neg(self) -> GaussianRat {
        GaussianRat {
            re: -&self.re,
            im: -&self.im,
        }
    }
}

impl Add for &GaussianRat {
    type Output = GaussianRat;
    fn add(self, rhs: &GaussianRat) -> GaussianRat {
        GaussianRat {
            re: &self.re + &rhs.re,
            im: &self.im + &rhs.im,
        }
    }
}

impl Sub for &GaussianRat {
    type Output = GaussianRat;
    fn sub(self, rhs: &GaussianRat) -> GaussianRat {
        GaussianRat {
            re: &self.re - &rhs.re,
            im: &self.im - &rhs.im,
        }
    }
}

impl Mul for &GaussianRat {
    type Output = GaussianRat;
    fn mul(self, rhs: &GaussianRat) -> GaussianRat {
        let re = &(&self.re * &rhs.re) - &(&self.im * &rhs.im);
        let im = &(&self.re * &rhs.im) + &(&self.im * &rhs.re);
        GaussianRat { re, im }
    }
}

/// Exact element of the 12th cyclotomic field `Q(zeta_12) ~= Q[x]/(x^4 - x^2 + 1)`.
///
/// Stored as `[c0, c1, c2, c3]` representing `c0 + c1*x + c2*x^2 + c3*x^3`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Cyclotomic12 {
    pub coeffs: [BigRat; 4],
}

impl Cyclotomic12 {
    pub fn zero() -> Self {
        Self {
            coeffs: [
                BigRat::zero(),
                BigRat::zero(),
                BigRat::zero(),
                BigRat::zero(),
            ],
        }
    }

    pub fn one() -> Self {
        Self {
            coeffs: [
                BigRat::one(),
                BigRat::zero(),
                BigRat::zero(),
                BigRat::zero(),
            ],
        }
    }

    /// Exact power `zeta_12^exponent` reduced modulo the 12th cyclotomic polynomial `x^4 - x^2 + 1`.
    pub fn zeta_pow(exponent: &BigInt) -> Self {
        let deg = exponent.rem_euclid_u64(12).expect("modulus 12 is nonzero") as usize;
        let len = deg.max(3) + 1;
        let mut poly = vec![BigRat::zero(); len];
        poly[deg] = BigRat::one();
        for power in (4..len).rev() {
            let lead = poly[power].clone();
            if !lead.is_zero() {
                poly[power] = BigRat::zero();
                poly[power - 2] = &poly[power - 2] + &lead;
                poly[power - 4] = &poly[power - 4] - &lead;
            }
        }
        Self {
            coeffs: [
                poly[0].clone(),
                poly[1].clone(),
                poly[2].clone(),
                poly[3].clone(),
            ],
        }
    }

    pub fn add_assign_ref(&mut self, other: &Self) {
        for idx in 0..4 {
            self.coeffs[idx] = &self.coeffs[idx] + &other.coeffs[idx];
        }
    }

    pub fn div_rat(&self, divisor: &BigRat) -> Result<Self, CoreError> {
        Ok(Self {
            coeffs: [
                self.coeffs[0].checked_div(divisor)?,
                self.coeffs[1].checked_div(divisor)?,
                self.coeffs[2].checked_div(divisor)?,
                self.coeffs[3].checked_div(divisor)?,
            ],
        })
    }

    pub fn is_rational(&self) -> bool {
        self.coeffs[1].is_zero() && self.coeffs[2].is_zero() && self.coeffs[3].is_zero()
    }

    pub fn rational_part(&self) -> &BigRat {
        &self.coeffs[0]
    }
}

impl Add for &Cyclotomic12 {
    type Output = Cyclotomic12;
    fn add(self, rhs: &Cyclotomic12) -> Cyclotomic12 {
        Cyclotomic12 {
            coeffs: [
                &self.coeffs[0] + &rhs.coeffs[0],
                &self.coeffs[1] + &rhs.coeffs[1],
                &self.coeffs[2] + &rhs.coeffs[2],
                &self.coeffs[3] + &rhs.coeffs[3],
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gaussian_rat_sympy_formatting() {
        let cases = [
            ((0, 1), (0, 1), "0"),
            ((1, 2), (0, 1), "1/2"),
            ((0, 1), (1, 1), "I"),
            ((0, 1), (-1, 1), "-I"),
            ((0, 1), (1, 2), "I/2"),
            ((0, 1), (-1, 2), "-I/2"),
            ((0, 1), (3, 4), "3*I/4"),
            ((0, 1), (-3, 4), "-3*I/4"),
            ((1, 2), (1, 2), "1/2 + I/2"),
            ((-1, 1), (-1, 1), "-1 - I"),
            ((1, 2), (-3, 4), "1/2 - 3*I/4"),
            ((-1, 12), (-1, 32), "-1/12 - I/32"),
        ];
        for ((rn, rd), (inm, idn), expected) in cases {
            let z = GaussianRat::new(
                BigRat::from_i64_pair(rn, rd).unwrap(),
                BigRat::from_i64_pair(inm, idn).unwrap(),
            );
            assert_eq!(z.to_sympy_string(), expected);
        }
    }

    #[test]
    fn test_cyclotomic12_identities() {
        // zeta_12^12 == 1 and zeta_12^6 == -1 and zeta_12^4 - zeta_12^2 + 1 == 0
        assert_eq!(Cyclotomic12::zeta_pow(&BigInt::from_i64(0)), Cyclotomic12::one());
        assert_eq!(Cyclotomic12::zeta_pow(&BigInt::from_i64(12)), Cyclotomic12::one());
        assert_eq!(Cyclotomic12::zeta_pow(&BigInt::from_i64(-12)), Cyclotomic12::one());
        let z6 = Cyclotomic12::zeta_pow(&BigInt::from_i64(6));
        assert!(z6.is_rational());
        assert_eq!(*z6.rational_part(), BigRat::from_i64(-1));

        // Sum of all 12 powers of zeta_12 is 0
        let mut sum = Cyclotomic12::zero();
        for k in 0..12 {
            sum.add_assign_ref(&Cyclotomic12::zeta_pow(&BigInt::from_i64(k)));
        }
        assert_eq!(sum, Cyclotomic12::zero());
    }
}
