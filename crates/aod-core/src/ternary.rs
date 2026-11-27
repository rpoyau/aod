//! Canonical 2-bit and 4-bit Trit-on-Binary SWAR arithmetic and exact `TritRatio`.
//!
//! Implements the Alpha Omega Dynamics (AOD) 2-bit ternary lane encoding preserving
//! `0b11` (`0_H` structural hinge / saturation / carry-barrier) alongside
//! `0b00` (`0_D` dwell), `0b01` (`+1` alpha), and `0b10` (`-1` omega):
//! - Packed arbitrary-width little-endian `Vec<u64>` limbs (32 lanes per limb)
//! - O(1)-per-limb SWAR lane-swap negation preserving `00 -> 00` and `11 -> 11`
//! - O(1)-per-limb SWAR lane mask extraction (`hinge`, `dwell`, `alpha`, `omega`, `polar`)
//! - Live contiguous dwell compaction (`burn_contiguous_dwell`)
//! - Fast `BigInt` balanced base-3 codec via radix `3^16` / `3^32`
//! - Pure-SWAR bit-plane arithmetic (3-to-2 CSA, Karatsuba > 64 trits, non-restoring
//!   balanced division, O(1) factor-of-3 stripping GCD, and carry-barrier addition)
//! - 4-bit `ChiralPair4`, 2-trit `Trit2MicroRatio`, and exact `TritRatio` backed
//!   strictly by `(TritWord, TritWord)` with preserved hinge metadata masks.

use std::cmp::Ordering;
use std::fmt;
use std::hash::{Hash, Hasher};

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::CoreError;

// ---------------------------------------------------------------------------
// Canonical 2-Bit Lane & Packed Limb Constants
// ---------------------------------------------------------------------------

pub const TRIT_DWELL: u8 = 0b00;
pub const TRIT_ALPHA: u8 = 0b01;
pub const TRIT_OMEGA: u8 = 0b10;
pub const TRIT_HINGE: u8 = 0b11;

pub const TRIT_LANE_MASK: u8 = 0b11;
pub const TRIT_LANE_BITS: usize = 2;
pub const LANES_PER_LIMB: usize = 32;

pub const MASK_01: u64 = 0x5555_5555_5555_5555;
pub const MASK_10: u64 = 0xAAAA_AAAA_AAAA_AAAA;
pub const MASK_11: u64 = 0xFFFF_FFFF_FFFF_FFFF;

const RADIX4: u32 = 81;
const HALF_RADIX4: i32 = 40;
const RADIX16: u32 = 43_046_721; // 3^16
const HALF_RADIX16: u32 = (RADIX16 - 1) / 2; // 21_523_360
const RADIX32: u64 = (RADIX16 as u64) * (RADIX16 as u64); // 3^32
const KARATSUBA_THRESHOLD: usize = 64;

const BAL4_TO_BYTE: [u8; 81] = build_bal4_to_byte();
const BYTE_TO_BAL4: [i8; 256] = build_byte_to_bal4();

const fn build_bal4_to_byte() -> [u8; 81] {
    let mut table = [0u8; 81];
    let mut idx = 0usize;
    while idx < 81 {
        let mut x = (idx as i32) - HALF_RADIX4;
        let mut byte_val = 0u8;
        let mut lane_i = 0usize;
        while lane_i < 4 {
            let shifted = x + 1;
            let q = shifted.div_euclid(3);
            let r = shifted.rem_euclid(3);
            let digit = r - 1;
            x = q;
            let lane = if digit == 1 {
                TRIT_ALPHA
            } else if digit == -1 {
                TRIT_OMEGA
            } else {
                TRIT_DWELL
            };
            byte_val |= lane << (2 * lane_i);
            lane_i += 1;
        }
        table[idx] = byte_val;
        idx += 1;
    }
    table
}

const fn build_byte_to_bal4() -> [i8; 256] {
    let mut table = [0i8; 256];
    let mut byte_val = 0usize;
    while byte_val < 256 {
        let d0 = ((byte_val & 1) as i8) - (((byte_val >> 1) & 1) as i8);
        let d1 = (((byte_val >> 2) & 1) as i8) - (((byte_val >> 3) & 1) as i8);
        let d2 = (((byte_val >> 4) & 1) as i8) - (((byte_val >> 5) & 1) as i8);
        let d3 = (((byte_val >> 6) & 1) as i8) - (((byte_val >> 7) & 1) as i8);
        table[byte_val] = d0 + 3 * d1 + 9 * d2 + 27 * d3;
        byte_val += 1;
    }
    table
}

// ---------------------------------------------------------------------------
// Lane-Level Primitives
// ---------------------------------------------------------------------------

/// Validate that `lane` is a canonical 2-bit trit lane in `0..=3` (preserving `0b11`).
pub fn validate_trit_lane(lane: u8) -> Result<u8, CoreError> {
    if lane <= TRIT_LANE_MASK {
        Ok(lane)
    } else {
        Err(CoreError::ValueError(format!(
            "trit lane must be in 0..=3, got {}",
            lane
        )))
    }
}

/// Decode a 2-bit lane to signed value `lo - hi` (`00 -> 0, 01 -> +1, 10 -> -1, 11 -> 0`).
pub fn trit_lane_to_signed(lane: u8) -> Result<i8, CoreError> {
    let v = validate_trit_lane(lane)?;
    Ok(((v & 1) as i8) - (((v >> 1) & 1) as i8))
}

/// Encode a signed balanced trit in `{-1, 0, +1}` into a canonical 2-bit lane.
pub fn signed_to_trit_lane(value: i8) -> Result<u8, CoreError> {
    match value {
        0 => Ok(TRIT_DWELL),
        1 => Ok(TRIT_ALPHA),
        -1 => Ok(TRIT_OMEGA),
        other => Err(CoreError::ValueError(format!(
            "signed trit value must be in {{-1, 0, 1}}, got {}",
            other
        ))),
    }
}

/// Swap polarity bits of a 2-bit lane, preserving `00 -> 00` and `11 -> 11`.
pub fn negate_trit_lane(lane: u8) -> Result<u8, CoreError> {
    let v = validate_trit_lane(lane)?;
    Ok(((v & 0b01) << 1) | ((v >> 1) & 0b01))
}

/// Return canonical single-character symbol (`'0'`, `'+'`, `'-'`, `'H'`).
pub fn trit_lane_symbol(lane: u8) -> Result<char, CoreError> {
    match validate_trit_lane(lane)? {
        TRIT_DWELL => Ok('0'),
        TRIT_ALPHA => Ok('+'),
        TRIT_OMEGA => Ok('-'),
        TRIT_HINGE => Ok('H'),
        _ => unreachable!(),
    }
}

/// Parse canonical single-character trit symbol into its 2-bit lane value.
pub fn symbol_to_trit_lane(symbol: char) -> Result<u8, CoreError> {
    match symbol {
        '0' => Ok(TRIT_DWELL),
        '+' => Ok(TRIT_ALPHA),
        '-' => Ok(TRIT_OMEGA),
        'H' => Ok(TRIT_HINGE),
        other => Err(CoreError::ValueError(format!(
            "invalid trit lane symbol: {:?}",
            other
        ))),
    }
}

// ---------------------------------------------------------------------------
// Per-Limb O(1) SWAR Primitives
// ---------------------------------------------------------------------------

#[inline]
pub fn limb_mask_11(lanes: usize) -> u64 {
    if lanes == 0 {
        0
    } else if lanes >= LANES_PER_LIMB {
        MASK_11
    } else {
        (1u64 << (2 * lanes)) - 1
    }
}

#[inline]
pub fn limb_mask_01(lanes: usize) -> u64 {
    MASK_01 & limb_mask_11(lanes)
}

#[inline]
pub fn limb_mask_10(lanes: usize) -> u64 {
    MASK_10 & limb_mask_11(lanes)
}

/// O(1) per-limb SWAR lane-swap negation preserving `00 -> 00` and `11 -> 11`.
#[inline]
pub fn swar_negate_limb(limb: u64) -> u64 {
    ((limb & MASK_01) << 1) | ((limb >> 1) & MASK_01)
}

/// O(1) per-limb SWAR extraction of `0b11` (`0_H`) hinge lanes.
#[inline]
pub fn swar_hinge_mask_limb(limb: u64) -> u64 {
    (limb & (limb >> 1)) & MASK_01
}

/// O(1) per-limb SWAR extraction of `0b01` (`+1` alpha) lanes.
#[inline]
pub fn swar_alpha_mask_limb(limb: u64) -> u64 {
    (limb & !(limb >> 1)) & MASK_01
}

/// O(1) per-limb SWAR extraction of `0b10` (`-1` omega) lanes.
#[inline]
pub fn swar_omega_mask_limb(limb: u64) -> u64 {
    ((!limb) & (limb >> 1)) & MASK_01
}

/// O(1) per-limb SWAR extraction of polar (`01` or `10`) lanes.
#[inline]
pub fn swar_polar_mask_limb(limb: u64) -> u64 {
    (limb ^ (limb >> 1)) & MASK_01
}

/// O(1) per-limb SWAR extraction of `0b00` (`0_D` dwell) lanes within `active_lanes`.
#[inline]
pub fn swar_dwell_mask_limb(limb: u64, active_lanes: usize) -> u64 {
    (!(limb | (limb >> 1))) & limb_mask_01(active_lanes)
}

/// Expand a 01-aligned per-limb hit mask to cover both bits of every hit 2-bit lane.
#[inline]
pub fn swar_double_lane_mask_limb(mask_01: u64) -> u64 {
    mask_01 | (mask_01 << 1)
}

// ---------------------------------------------------------------------------
// Internal Multi-Limb Helpers & BigInt <-> Vec<u64> Conversion
// ---------------------------------------------------------------------------

#[inline]
fn get_limb(limbs: &[u64], idx: usize) -> u64 {
    limbs.get(idx).copied().unwrap_or(0)
}

fn trim_u64(limbs: &mut Vec<u64>) {
    while limbs.last() == Some(&0) {
        limbs.pop();
    }
}

fn limbs_bit_len(limbs: &[u64]) -> usize {
    match limbs.last() {
        None => 0,
        Some(&top) => (limbs.len() - 1) * 64 + (64 - top.leading_zeros() as usize),
    }
}

fn limbs_to_bigint(limbs: &[u64]) -> BigInt {
    let mut acc = BigInt::zero();
    for &w in limbs.iter().rev() {
        acc = &acc.shl_usize(64) + &BigInt::from_u64(w);
    }
    acc
}

fn bigint_to_u64_limbs(value: &BigInt) -> Result<Vec<u64>, CoreError> {
    if value.is_negative() {
        return Err(CoreError::ValueError(
            "packed ternary register or lane mask must be nonnegative".to_string(),
        ));
    }
    if value.is_zero() {
        return Ok(Vec::new());
    }
    let chunk_base = BigInt::from_u32(65_536);
    let mut cur = value.clone();
    let mut limbs: Vec<u64> = Vec::with_capacity((value.bit_len() + 63) / 64);
    let mut limb_acc = 0u64;
    let mut shift = 0usize;
    while !cur.is_zero() {
        let (q, r) = cur.div_rem_trunc(&chunk_base)?;
        let part = r.to_u32().unwrap_or(0) as u64;
        limb_acc |= part << shift;
        shift += 16;
        if shift == 64 {
            limbs.push(limb_acc);
            limb_acc = 0;
            shift = 0;
        }
        cur = q;
    }
    if shift > 0 {
        limbs.push(limb_acc);
    }
    trim_u64(&mut limbs);
    Ok(limbs)
}

fn active_lanes_in_limb(width: usize, limb_idx: usize) -> usize {
    let start = limb_idx * LANES_PER_LIMB;
    if start >= width {
        0
    } else {
        (width - start).min(LANES_PER_LIMB)
    }
}

fn limb_count_for_width(width: usize) -> usize {
    (width + LANES_PER_LIMB - 1) / LANES_PER_LIMB
}

// ---------------------------------------------------------------------------
// Arbitrary-Width 01-Aligned LaneMask & BigInt SWAR Helpers
// ---------------------------------------------------------------------------

/// Arbitrary-width 01-aligned lane mask (`limbs` trimmed of trailing zero words).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct LaneMask {
    limbs: Vec<u64>,
}

impl LaneMask {
    pub fn zero() -> Self {
        Self { limbs: Vec::new() }
    }

    pub fn from_limbs(mut limbs: Vec<u64>) -> Result<Self, CoreError> {
        for &w in &limbs {
            if (w & !MASK_01) != 0 {
                return Err(CoreError::ValueError(
                    "lane mask must only set 01-aligned even lane bits".to_string(),
                ));
            }
        }
        trim_u64(&mut limbs);
        Ok(Self { limbs })
    }

    pub fn from_u64(mask: u64) -> Result<Self, CoreError> {
        if (mask & !MASK_01) != 0 {
            return Err(CoreError::ValueError(format!(
                "lane mask must only set 01-aligned even lane bits, got {:#b}",
                mask
            )));
        }
        if mask == 0 {
            Ok(Self::zero())
        } else {
            Ok(Self { limbs: vec![mask] })
        }
    }

    pub fn from_bigint(mask: &BigInt) -> Result<Self, CoreError> {
        let limbs = bigint_to_u64_limbs(mask)?;
        Self::from_limbs(limbs)
    }

    fn from_limbs_unchecked(mut limbs: Vec<u64>) -> Self {
        trim_u64(&mut limbs);
        Self { limbs }
    }

    pub fn limbs(&self) -> &[u64] {
        &self.limbs
    }

    pub fn is_zero(&self) -> bool {
        self.limbs.is_empty()
    }

    pub fn count(&self) -> usize {
        self.limbs.iter().map(|&w| w.count_ones() as usize).sum()
    }

    pub fn has_lane(&self, lane_idx: usize) -> bool {
        let limb_idx = lane_idx / LANES_PER_LIMB;
        let bit = (lane_idx % LANES_PER_LIMB) * TRIT_LANE_BITS;
        ((get_limb(&self.limbs, limb_idx) >> bit) & 1) != 0
    }

    pub fn bit_or(&self, other: &Self) -> Self {
        let n = self.limbs.len().max(other.limbs.len());
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            out.push(get_limb(&self.limbs, i) | get_limb(&other.limbs, i));
        }
        Self::from_limbs_unchecked(out)
    }

    pub fn bit_and(&self, other: &Self) -> Self {
        let n = self.limbs.len().min(other.limbs.len());
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            out.push(self.limbs[i] & other.limbs[i]);
        }
        Self::from_limbs_unchecked(out)
    }

    pub fn to_bigint(&self) -> BigInt {
        limbs_to_bigint(&self.limbs)
    }

    pub fn to_doubled_bigint(&self) -> BigInt {
        let doubled: Vec<u64> = self
            .limbs
            .iter()
            .map(|&w| swar_double_lane_mask_limb(w))
            .collect();
        limbs_to_bigint(&doubled)
    }
}

pub fn swar_mask_01_bigint(width: usize) -> BigInt {
    if width == 0 {
        return BigInt::zero();
    }
    let n = limb_count_for_width(width);
    let mut limbs = Vec::with_capacity(n);
    for i in 0..n {
        limbs.push(limb_mask_01(active_lanes_in_limb(width, i)));
    }
    limbs_to_bigint(&limbs)
}

pub fn swar_mask_10_bigint(width: usize) -> BigInt {
    if width == 0 {
        return BigInt::zero();
    }
    let n = limb_count_for_width(width);
    let mut limbs = Vec::with_capacity(n);
    for i in 0..n {
        limbs.push(limb_mask_10(active_lanes_in_limb(width, i)));
    }
    limbs_to_bigint(&limbs)
}

pub fn swar_mask_11_bigint(width: usize) -> BigInt {
    if width == 0 {
        return BigInt::zero();
    }
    let n = limb_count_for_width(width);
    let mut limbs = Vec::with_capacity(n);
    for i in 0..n {
        limbs.push(limb_mask_11(active_lanes_in_limb(width, i)));
    }
    limbs_to_bigint(&limbs)
}

pub fn swar_double_lane_mask_bigint(mask_01: &BigInt) -> Result<BigInt, CoreError> {
    let lm = LaneMask::from_bigint(mask_01)?;
    Ok(lm.to_doubled_bigint())
}

pub fn swar_negate_bigint(packed: &BigInt, width: usize) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    Ok(word.neg().to_packed_bigint())
}

pub fn swar_hinge_mask_bigint(
    packed: &BigInt,
    width: usize,
    doubled: bool,
) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    let mask = word.hinge_mask();
    Ok(if doubled {
        mask.to_doubled_bigint()
    } else {
        mask.to_bigint()
    })
}

pub fn swar_alpha_mask_bigint(
    packed: &BigInt,
    width: usize,
    doubled: bool,
) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    let mask = word.alpha_mask();
    Ok(if doubled {
        mask.to_doubled_bigint()
    } else {
        mask.to_bigint()
    })
}

pub fn swar_omega_mask_bigint(
    packed: &BigInt,
    width: usize,
    doubled: bool,
) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    let mask = word.omega_mask();
    Ok(if doubled {
        mask.to_doubled_bigint()
    } else {
        mask.to_bigint()
    })
}

pub fn swar_polar_mask_bigint(
    packed: &BigInt,
    width: usize,
    doubled: bool,
) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    let mask = word.polar_mask();
    Ok(if doubled {
        mask.to_doubled_bigint()
    } else {
        mask.to_bigint()
    })
}

pub fn swar_dwell_mask_bigint(
    packed: &BigInt,
    width: usize,
    doubled: bool,
) -> Result<BigInt, CoreError> {
    let word = TritWord::from_packed_bigint(packed, width)?;
    let mask = word.dwell_mask();
    Ok(if doubled {
        mask.to_doubled_bigint()
    } else {
        mask.to_bigint()
    })
}

// ---------------------------------------------------------------------------
// Pure-SWAR Multi-Limb Bit-Plane Balanced Base-3 Arithmetic Kernels
// ---------------------------------------------------------------------------

#[inline]
fn planes_is_zero(a: &[u64], o: &[u64]) -> bool {
    a.is_empty() && o.is_empty()
}

#[inline]
fn planes_is_one(a: &[u64], o: &[u64]) -> bool {
    a.len() == 1 && a[0] == 1 && o.is_empty()
}

fn planes_width(a: &[u64], o: &[u64]) -> usize {
    let max_len = a.len().max(o.len());
    if max_len == 0 {
        return 0;
    }
    let top_u = get_limb(a, max_len - 1) | get_limb(o, max_len - 1);
    (max_len - 1) * LANES_PER_LIMB + ((63 - top_u.leading_zeros() as usize) >> 1) + 1
}

fn planes_sign(a: &[u64], o: &[u64]) -> i8 {
    let max_len = a.len().max(o.len());
    if max_len == 0 {
        return 0;
    }
    let idx = max_len - 1;
    let ta = get_limb(a, idx);
    let to = get_limb(o, idx);
    let u = ta | to;
    let top_bit = 63 - u.leading_zeros() as usize;
    if ((ta >> top_bit) & 1) != 0 {
        1
    } else {
        -1
    }
}

fn planes_cmp(a1: &[u64], o1: &[u64], a2: &[u64], o2: &[u64]) -> Ordering {
    let max_len = a1.len().max(o1.len()).max(a2.len()).max(o2.len());
    for idx in (0..max_len).rev() {
        let p1 = get_limb(a1, idx) | (get_limb(o1, idx) << 1);
        let p2 = get_limb(a2, idx) | (get_limb(o2, idx) << 1);
        let diff = p1 ^ p2;
        if diff != 0 {
            let shift = (63 - diff.leading_zeros() as usize) & !1usize;
            let l1 = (p1 >> shift) & 0b11;
            let l2 = (p2 >> shift) & 0b11;
            let v1 = ((l1 & 1) as i8) - ((l1 >> 1) as i8);
            let v2 = ((l2 & 1) as i8) - ((l2 >> 1) as i8);
            return v1.cmp(&v2);
        }
    }
    Ordering::Equal
}

fn shl_plane(p: &[u64], trit_shift: usize) -> Vec<u64> {
    if p.is_empty() || trit_shift == 0 {
        return p.to_vec();
    }
    let limb_shift = trit_shift / LANES_PER_LIMB;
    let bit_shift = (trit_shift % LANES_PER_LIMB) * TRIT_LANE_BITS;
    if bit_shift == 0 {
        let mut out = vec![0u64; limb_shift + p.len()];
        out[limb_shift..limb_shift + p.len()].copy_from_slice(p);
        return out;
    }
    let inv = 64 - bit_shift;
    let mut out = vec![0u64; limb_shift + p.len() + 1];
    let mut carry = 0u64;
    for (idx, &w) in p.iter().enumerate() {
        out[limb_shift + idx] = (w << bit_shift) | carry;
        carry = w >> inv;
    }
    out[limb_shift + p.len()] = carry;
    trim_u64(&mut out);
    out
}

fn shr_plane(p: &[u64], trit_shift: usize) -> Vec<u64> {
    if p.is_empty() || trit_shift == 0 {
        return p.to_vec();
    }
    let limb_shift = trit_shift / LANES_PER_LIMB;
    if limb_shift >= p.len() {
        return Vec::new();
    }
    let bit_shift = (trit_shift % LANES_PER_LIMB) * TRIT_LANE_BITS;
    if bit_shift == 0 {
        return p[limb_shift..].to_vec();
    }
    let inv = 64 - bit_shift;
    let new_len = p.len() - limb_shift;
    let mut out = vec![0u64; new_len];
    for idx in 0..new_len {
        let lo = p[limb_shift + idx] >> bit_shift;
        let hi = if limb_shift + idx + 1 < p.len() {
            p[limb_shift + idx + 1] << inv
        } else {
            0
        };
        out[idx] = lo | hi;
    }
    trim_u64(&mut out);
    out
}

fn low_trits_plane(p: &[u64], trits: usize) -> Vec<u64> {
    if p.is_empty() || trits == 0 {
        return Vec::new();
    }
    let full = trits / LANES_PER_LIMB;
    let rem = trits % LANES_PER_LIMB;
    let take_full = full.min(p.len());
    let mut out = Vec::with_capacity(take_full + usize::from(rem > 0));
    out.extend_from_slice(&p[..take_full]);
    if rem > 0 && p.len() > full {
        out.push(p[full] & limb_mask_11(rem));
    }
    trim_u64(&mut out);
    out
}

fn planes_shl_trits(a: &[u64], o: &[u64], trits: usize) -> (Vec<u64>, Vec<u64>) {
    (shl_plane(a, trits), shl_plane(o, trits))
}

fn planes_shr_trits(a: &[u64], o: &[u64], trits: usize) -> (Vec<u64>, Vec<u64>) {
    (shr_plane(a, trits), shr_plane(o, trits))
}

fn planes_trailing_zero_trits(a: &[u64], o: &[u64]) -> usize {
    let max_len = a.len().max(o.len());
    for idx in 0..max_len {
        let u = get_limb(a, idx) | get_limb(o, idx);
        if u != 0 {
            return idx * LANES_PER_LIMB + ((u.trailing_zeros() as usize) >> 1);
        }
    }
    0
}

/// Zero-loop O(1) per-limb SWAR 3-to-2 balanced ternary carry-save adder (unshifted carry).
#[inline]
pub fn swar_csa3_limb_unshifted(
    a1: u64,
    o1: u64,
    a2: u64,
    o2: u64,
    a3: u64,
    o3: u64,
) -> (u64, u64, u64, u64) {
    let c12_a = a1 & a2;
    let c12_o = o1 & o2;
    let ax12 = a1 ^ a2;
    let ox12 = o1 ^ o2;
    let k12 = ax12 & ox12;
    let s12_a = (ax12 ^ k12) | c12_o;
    let s12_o = (ox12 ^ k12) | c12_a;

    let c2_a = s12_a & a3;
    let c2_o = s12_o & o3;
    let ax = s12_a ^ a3;
    let ox = s12_o ^ o3;
    let k2 = ax & ox;
    let sa = (ax ^ k2) | c2_o;
    let so = (ox ^ k2) | c2_a;

    let ca_raw = c12_a | c2_a;
    let co_raw = c12_o | c2_o;
    let c_cancel = ca_raw & co_raw;
    let ca = ca_raw ^ c_cancel;
    let co = co_raw ^ c_cancel;
    (sa, so, ca, co)
}

/// Multi-limb 3-to-2 balanced ternary SWAR carry-save adder (carry shifted left 1 trit).
fn swar_csa3_planes(
    a1: &[u64],
    o1: &[u64],
    a2: &[u64],
    o2: &[u64],
    a3: &[u64],
    o3: &[u64],
) -> (Vec<u64>, Vec<u64>, Vec<u64>, Vec<u64>) {
    let n = a1
        .len()
        .max(o1.len())
        .max(a2.len())
        .max(o2.len())
        .max(a3.len())
        .max(o3.len());
    if n == 0 {
        return (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    }
    let mut sum_a = Vec::with_capacity(n);
    let mut sum_o = Vec::with_capacity(n);
    let mut car_a = Vec::with_capacity(n + 1);
    let mut car_o = Vec::with_capacity(n + 1);
    let mut prev_ca_hi = 0u64;
    let mut prev_co_hi = 0u64;

    for i in 0..n {
        let (sa, so, ca, co) = swar_csa3_limb_unshifted(
            get_limb(a1, i),
            get_limb(o1, i),
            get_limb(a2, i),
            get_limb(o2, i),
            get_limb(a3, i),
            get_limb(o3, i),
        );
        sum_a.push(sa);
        sum_o.push(so);
        car_a.push((ca << 2) | prev_ca_hi);
        car_o.push((co << 2) | prev_co_hi);
        prev_ca_hi = ca >> 62;
        prev_co_hi = co >> 62;
    }
    if prev_ca_hi != 0 {
        car_a.push(prev_ca_hi);
    }
    if prev_co_hi != 0 {
        car_o.push(prev_co_hi);
    }
    trim_u64(&mut sum_a);
    trim_u64(&mut sum_o);
    trim_u64(&mut car_a);
    trim_u64(&mut car_o);
    (sum_a, sum_o, car_a, car_o)
}

/// Exact multi-limb pure-SWAR carry-propagating addition on 01-aligned disjoint planes.
fn swar_add_planes(a1: &[u64], o1: &[u64], a2: &[u64], o2: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let n = a1.len().max(o1.len()).max(a2.len()).max(o2.len());
    if n == 0 {
        return (Vec::new(), Vec::new());
    }
    let mut out_a = Vec::with_capacity(n + 1);
    let mut out_o = Vec::with_capacity(n + 1);
    let mut cin_a = 0u64;
    let mut cin_o = 0u64;

    for i in 0..n {
        let (mut s_a, mut s_o, ca_u, co_u) = swar_csa3_limb_unshifted(
            get_limb(a1, i),
            get_limb(o1, i),
            get_limb(a2, i),
            get_limb(o2, i),
            cin_a,
            cin_o,
        );
        let mut cout: i8 = ((ca_u >> 62) as i8) - ((co_u >> 62) as i8);
        let mut c_a = ca_u << 2;
        let mut c_o = co_u << 2;
        while (c_a | c_o) != 0 {
            let ca = s_a & c_a;
            let co = s_o & c_o;
            let ax = s_a ^ c_a;
            let ox = s_o ^ c_o;
            let cancel = ax & ox;
            s_a = (ax ^ cancel) | co;
            s_o = (ox ^ cancel) | ca;
            cout += ((ca >> 62) as i8) - ((co >> 62) as i8);
            c_a = ca << 2;
            c_o = co << 2;
        }
        out_a.push(s_a);
        out_o.push(s_o);
        if cout > 0 {
            cin_a = 1;
            cin_o = 0;
        } else if cout < 0 {
            cin_a = 0;
            cin_o = 1;
        } else {
            cin_a = 0;
            cin_o = 0;
        }
    }
    if cin_a != 0 {
        out_a.push(cin_a);
    }
    if cin_o != 0 {
        out_o.push(cin_o);
    }
    trim_u64(&mut out_a);
    trim_u64(&mut out_o);
    (out_a, out_o)
}

/// Multiply two balanced plane pairs using 3-to-2 SWAR CSA accumulation.
fn swar_mul_csa_leaf(a1: &[u64], o1: &[u64], a2: &[u64], o2: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let w1 = planes_width(a1, o1);
    let w2 = planes_width(a2, o2);
    if w1 == 0 || w2 == 0 {
        return (Vec::new(), Vec::new());
    }
    let (a_mul, o_mul, a_big, o_big) = if w1 < w2 {
        (a1, o1, a2, o2)
    } else {
        (a2, o2, a1, o1)
    };

    let mul_limbs = a_mul.len().max(o_mul.len());
    let mut sum_a: Vec<u64> = Vec::new();
    let mut sum_o: Vec<u64> = Vec::new();
    let mut car_a: Vec<u64> = Vec::new();
    let mut car_o: Vec<u64> = Vec::new();

    for limb_idx in 0..mul_limbs {
        let ma = get_limb(a_mul, limb_idx);
        let mo = get_limb(o_mul, limb_idx);
        let mut rem = ma | mo;
        while rem != 0 {
            let tz = rem.trailing_zeros() as usize;
            let lsb = 1u64 << tz;
            rem ^= lsb;
            let trit_shift = limb_idx * LANES_PER_LIMB + (tz >> 1);
            let (pa, po) = if (ma & lsb) != 0 {
                planes_shl_trits(a_big, o_big, trit_shift)
            } else {
                planes_shl_trits(o_big, a_big, trit_shift)
            };
            let (na, no, nca, nco) = swar_csa3_planes(&sum_a, &sum_o, &car_a, &car_o, &pa, &po);
            sum_a = na;
            sum_o = no;
            car_a = nca;
            car_o = nco;
        }
    }
    swar_add_planes(&sum_a, &sum_o, &car_a, &car_o)
}

/// Exact balanced base-3 SWAR multiplication (CSA leaves `<= 64` trits + Karatsuba `> 64` trits).
fn swar_mul_planes(a1: &[u64], o1: &[u64], a2: &[u64], o2: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let w1 = planes_width(a1, o1);
    let w2 = planes_width(a2, o2);
    if w1 == 0 || w2 == 0 {
        return (Vec::new(), Vec::new());
    }
    if w1 <= KARATSUBA_THRESHOLD || w2 <= KARATSUBA_THRESHOLD {
        return swar_mul_csa_leaf(a1, o1, a2, o2);
    }

    let m = w1.max(w2) >> 1;
    let a1_lo = low_trits_plane(a1, m);
    let o1_lo = low_trits_plane(o1, m);
    let (a1_hi, o1_hi) = planes_shr_trits(a1, o1, m);

    let a2_lo = low_trits_plane(a2, m);
    let o2_lo = low_trits_plane(o2, m);
    let (a2_hi, o2_hi) = planes_shr_trits(a2, o2, m);

    let (z0_a, z0_o) = swar_mul_planes(&a1_lo, &o1_lo, &a2_lo, &o2_lo);
    let (z2_a, z2_o) = swar_mul_planes(&a1_hi, &o1_hi, &a2_hi, &o2_hi);

    let (s1_a, s1_o) = swar_add_planes(&a1_lo, &o1_lo, &a1_hi, &o1_hi);
    let (s2_a, s2_o) = swar_add_planes(&a2_lo, &o2_lo, &a2_hi, &o2_hi);
    let (z1_full_a, z1_full_o) = swar_mul_planes(&s1_a, &s1_o, &s2_a, &s2_o);

    let (t_a, t_o, tc_a, tc_o) =
        swar_csa3_planes(&z1_full_a, &z1_full_o, &z0_o, &z0_a, &z2_o, &z2_a);
    let (z1_a, z1_o) = swar_add_planes(&t_a, &t_o, &tc_a, &tc_o);

    let (z1s_a, z1s_o) = planes_shl_trits(&z1_a, &z1_o, m);
    let (z2s_a, z2s_o) = planes_shl_trits(&z2_a, &z2_o, 2 * m);
    let (r_a, r_o, rc_a, rc_o) =
        swar_csa3_planes(&z0_a, &z0_o, &z1s_a, &z1s_o, &z2s_a, &z2s_o);
    swar_add_planes(&r_a, &r_o, &rc_a, &rc_o)
}

/// Balanced non-restoring trit-by-trit division for `U > 0, V > 0`.
/// Returns `(qa, qo, ra, ro)` satisfying `U = Q * V + R` and `0 <= R < V`.
fn swar_divmod_pos_planes(
    ua: &[u64],
    uo: &[u64],
    va: &[u64],
    vo: &[u64],
) -> (Vec<u64>, Vec<u64>, Vec<u64>, Vec<u64>) {
    match planes_cmp(ua, uo, va, vo) {
        Ordering::Less => return (Vec::new(), Vec::new(), ua.to_vec(), uo.to_vec()),
        Ordering::Equal => return (vec![1], Vec::new(), Vec::new(), Vec::new()),
        Ordering::Greater => {}
    }

    let wu = planes_width(ua, uo);
    let wv = planes_width(va, vo);
    let k = wu - wv + 1;

    let mut ra = ua.to_vec();
    let mut ro = uo.to_vec();
    let (mut tra, mut tro) = swar_add_planes(ua, uo, ua, uo);
    let (tva, tvo) = swar_add_planes(va, vo, va, vo);
    let q_limbs = (k / LANES_PER_LIMB) + 1;
    let mut qa = vec![0u64; q_limbs];
    let mut qo = vec![0u64; q_limbs];

    for i in (0..=k).rev() {
        let (sva, svo) = planes_shl_trits(va, vo, i);
        if planes_cmp(&tra, &tro, &sva, &svo) == Ordering::Greater {
            qa[i / LANES_PER_LIMB] |= 1u64 << ((i % LANES_PER_LIMB) * TRIT_LANE_BITS);
            let (nra, nro) = swar_add_planes(&ra, &ro, &svo, &sva);
            ra = nra;
            ro = nro;
            let (stva, stvo) = planes_shl_trits(&tva, &tvo, i);
            let (ntra, ntro) = swar_add_planes(&tra, &tro, &stvo, &stva);
            tra = ntra;
            tro = ntro;
        } else if planes_cmp(&tra, &tro, &svo, &sva) == Ordering::Less {
            qo[i / LANES_PER_LIMB] |= 1u64 << ((i % LANES_PER_LIMB) * TRIT_LANE_BITS);
            let (nra, nro) = swar_add_planes(&ra, &ro, &sva, &svo);
            ra = nra;
            ro = nro;
            let (stva, stvo) = planes_shl_trits(&tva, &tvo, i);
            let (ntra, ntro) = swar_add_planes(&tra, &tro, &stva, &stvo);
            tra = ntra;
            tro = ntro;
        }
    }

    trim_u64(&mut qa);
    trim_u64(&mut qo);
    if planes_sign(&ra, &ro) < 0 {
        let (nra, nro) = swar_add_planes(&ra, &ro, va, vo);
        ra = nra;
        ro = nro;
        let (nqa, nqo) = swar_add_planes(&qa, &qo, &[], &[1]);
        qa = nqa;
        qo = nqo;
    }
    (qa, qo, ra, ro)
}

/// Balanced remainder magnitude `|R| <= V / 2` for `U > 0, V > 0`.
fn swar_bal_rem_pos_planes(ua: &[u64], uo: &[u64], va: &[u64], vo: &[u64]) -> (Vec<u64>, Vec<u64>) {
    match planes_cmp(ua, uo, va, vo) {
        Ordering::Equal => return (Vec::new(), Vec::new()),
        Ordering::Less => {
            let (tra, tro) = swar_add_planes(ua, uo, ua, uo);
            if planes_cmp(&tra, &tro, va, vo) == Ordering::Greater {
                return swar_add_planes(va, vo, uo, ua);
            }
            return (ua.to_vec(), uo.to_vec());
        }
        Ordering::Greater => {}
    }

    let wu = planes_width(ua, uo);
    let wv = planes_width(va, vo);
    let k = wu - wv + 1;

    let mut ra = ua.to_vec();
    let mut ro = uo.to_vec();
    let (mut tra, mut tro) = swar_add_planes(ua, uo, ua, uo);
    let (tva, tvo) = swar_add_planes(va, vo, va, vo);

    for i in (0..=k).rev() {
        let (sva, svo) = planes_shl_trits(va, vo, i);
        if planes_cmp(&tra, &tro, &sva, &svo) == Ordering::Greater {
            let (nra, nro) = swar_add_planes(&ra, &ro, &svo, &sva);
            ra = nra;
            ro = nro;
            let (stva, stvo) = planes_shl_trits(&tva, &tvo, i);
            let (ntra, ntro) = swar_add_planes(&tra, &tro, &stvo, &stva);
            tra = ntra;
            tro = ntro;
        } else if planes_cmp(&tra, &tro, &svo, &sva) == Ordering::Less {
            let (nra, nro) = swar_add_planes(&ra, &ro, &sva, &svo);
            ra = nra;
            ro = nro;
            let (stva, stvo) = planes_shl_trits(&tva, &tvo, i);
            let (ntra, ntro) = swar_add_planes(&tra, &tro, &stva, &stvo);
            tra = ntra;
            tro = ntro;
        }
    }

    if planes_sign(&ra, &ro) < 0 {
        (ro, ra)
    } else {
        (ra, ro)
    }
}

/// Exact pure-SWAR GCD using O(1) factor-of-3 stripping and balanced remainders.
fn swar_gcd_planes(a1_in: &[u64], o1_in: &[u64], a2_in: &[u64], o2_in: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let (mut a1, mut o1) = if planes_sign(a1_in, o1_in) < 0 {
        (o1_in.to_vec(), a1_in.to_vec())
    } else {
        (a1_in.to_vec(), o1_in.to_vec())
    };
    let (mut a2, mut o2) = if planes_sign(a2_in, o2_in) < 0 {
        (o2_in.to_vec(), a2_in.to_vec())
    } else {
        (a2_in.to_vec(), o2_in.to_vec())
    };

    if planes_is_zero(&a1, &o1) {
        return (a2, o2);
    }
    if planes_is_zero(&a2, &o2) {
        return (a1, o1);
    }

    let tz1 = planes_trailing_zero_trits(&a1, &o1);
    let tz2 = planes_trailing_zero_trits(&a2, &o2);
    let common_trits = tz1.min(tz2);
    if tz1 > 0 {
        let (na1, no1) = planes_shr_trits(&a1, &o1, tz1);
        a1 = na1;
        o1 = no1;
    }
    if tz2 > 0 {
        let (na2, no2) = planes_shr_trits(&a2, &o2, tz2);
        a2 = na2;
        o2 = no2;
    }

    while !planes_is_zero(&a2, &o2) {
        let (ra, ro) = swar_bal_rem_pos_planes(&a1, &o1, &a2, &o2);
        a1 = a2;
        o1 = o2;
        if !planes_is_zero(&ra, &ro) {
            let tz = planes_trailing_zero_trits(&ra, &ro);
            if tz > 0 {
                let (na2, no2) = planes_shr_trits(&ra, &ro, tz);
                a2 = na2;
                o2 = no2;
            } else {
                a2 = ra;
                o2 = ro;
            }
        } else {
            a2 = Vec::new();
            o2 = Vec::new();
        }
    }

    planes_shl_trits(&a1, &o1, common_trits)
}

/// Exact division of signed `X` by positive divisor `G > 0` with zero remainder.
fn swar_div_exact_pos_planes(
    xa: &[u64],
    xo: &[u64],
    ga: &[u64],
    go: &[u64],
) -> Result<(Vec<u64>, Vec<u64>), CoreError> {
    if planes_is_zero(xa, xo) {
        return Ok((Vec::new(), Vec::new()));
    }
    if planes_is_one(ga, go) {
        return Ok((xa.to_vec(), xo.to_vec()));
    }
    let sx = planes_sign(xa, xo);
    let (ua, uo) = if sx < 0 { (xo, xa) } else { (xa, xo) };
    let (qa, qo, ra, ro) = swar_divmod_pos_planes(ua, uo, ga, go);
    if !planes_is_zero(&ra, &ro) {
        return Err(CoreError::ValueError(
            "exact balanced ternary division produced non-zero remainder".to_string(),
        ));
    }
    if sx < 0 {
        Ok((qo, qa))
    } else {
        Ok((qa, qo))
    }
}

fn planes_to_canonical_word(a: &[u64], o: &[u64]) -> TritWord {
    let n = a.len().max(o.len());
    if n == 0 {
        return TritWord::zero();
    }
    let mut limbs = Vec::with_capacity(n);
    for i in 0..n {
        limbs.push(get_limb(a, i) | (get_limb(o, i) << 1));
    }
    trim_u64(&mut limbs);
    if limbs.is_empty() {
        return TritWord::zero();
    }
    let top = *limbs.last().unwrap();
    let width = (limbs.len() - 1) * LANES_PER_LIMB + ((63 - top.leading_zeros() as usize) >> 1) + 1;
    TritWord { limbs, width }
}

// ---------------------------------------------------------------------------
// 4-Bit Chiral-Hinge Lane Container
// ---------------------------------------------------------------------------

/// Immutable 4-bit chiral-hinge container holding two 2-bit trit lanes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ChiralPair4 {
    lo_lane: u8,
    hi_lane: u8,
}

impl ChiralPair4 {
    pub fn from_lanes(lo_lane: u8, hi_lane: u8) -> Result<Self, CoreError> {
        Ok(Self {
            lo_lane: validate_trit_lane(lo_lane)?,
            hi_lane: validate_trit_lane(hi_lane)?,
        })
    }

    pub fn from_bits(bits: u8) -> Result<Self, CoreError> {
        if bits > 0b1111 {
            return Err(CoreError::ValueError(format!(
                "ChiralPair4 bits must be in 0..=15, got {}",
                bits
            )));
        }
        Ok(Self {
            lo_lane: bits & TRIT_LANE_MASK,
            hi_lane: (bits >> TRIT_LANE_BITS) & TRIT_LANE_MASK,
        })
    }

    pub fn lo_lane(self) -> u8 {
        self.lo_lane
    }

    pub fn hi_lane(self) -> u8 {
        self.hi_lane
    }

    pub fn raw4(self) -> u8 {
        (self.hi_lane << TRIT_LANE_BITS) | self.lo_lane
    }

    pub fn to_bits(self) -> u8 {
        self.raw4()
    }

    pub fn net_charge(self) -> i8 {
        let lo = ((self.lo_lane & 1) as i8) - (((self.lo_lane >> 1) & 1) as i8);
        let hi = ((self.hi_lane & 1) as i8) - (((self.hi_lane >> 1) & 1) as i8);
        lo + hi
    }

    pub fn has_hinge(self) -> bool {
        self.lo_lane == TRIT_HINGE || self.hi_lane == TRIT_HINGE
    }

    pub fn is_saturated(self) -> bool {
        self.lo_lane == TRIT_HINGE && self.hi_lane == TRIT_HINGE
    }

    /// O(1) SWAR lane polarity flip preserving `0_D` (`00`) and `0_H` (`11`).
    pub fn chiral_flip(self) -> Self {
        let flipped = swar_negate_limb(self.raw4() as u64) as u8;
        Self {
            lo_lane: flipped & TRIT_LANE_MASK,
            hi_lane: (flipped >> TRIT_LANE_BITS) & TRIT_LANE_MASK,
        }
    }

    pub fn to_trit_word(self) -> TritWord {
        let raw = self.raw4() as u64;
        let limbs = if raw == 0 { Vec::new() } else { vec![raw] };
        TritWord { limbs, width: 2 }
    }

    pub fn from_trit_word(word: &TritWord) -> Result<Self, CoreError> {
        if word.width > 2 {
            return Err(CoreError::ValueError(format!(
                "TritWord width must be <= 2 to convert to ChiralPair4, got {}",
                word.width
            )));
        }
        let bits = (get_limb(&word.limbs, 0) & 0b1111) as u8;
        Self::from_bits(bits)
    }
}

impl std::ops::Neg for ChiralPair4 {
    type Output = ChiralPair4;
    fn neg(self) -> ChiralPair4 {
        self.chiral_flip()
    }
}

impl std::ops::Neg for &ChiralPair4 {
    type Output = ChiralPair4;
    fn neg(self) -> ChiralPair4 {
        self.chiral_flip()
    }
}

// ---------------------------------------------------------------------------
// Arbitrary-Width Packed 2-Bit Word & Barrier Add Result
// ---------------------------------------------------------------------------

/// Result of carry-barrier addition preserving `0_H` (`11`) structural hinges.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BarrierAddResult {
    pub result: TritWord,
    pub hinge_mask: LaneMask,
    pub blocked_alpha_mask: LaneMask,
    pub blocked_omega_mask: LaneMask,
}

impl BarrierAddResult {
    pub fn blocked_carry_mask(&self) -> LaneMask {
        self.blocked_alpha_mask.bit_or(&self.blocked_omega_mask)
    }

    pub fn had_blocked_carry(&self) -> bool {
        !self.blocked_alpha_mask.is_zero() || !self.blocked_omega_mask.is_zero()
    }
}

/// Immutable arbitrary-width packed 2-bit Trit-on-Binary register.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TritWord {
    limbs: Vec<u64>,
    width: usize,
}

impl TritWord {
    // --- Constructors ------------------------------------------------------

    pub fn zero() -> Self {
        Self {
            limbs: Vec::new(),
            width: 1,
        }
    }

    pub fn zero_with_width(width: usize) -> Self {
        Self {
            limbs: Vec::new(),
            width,
        }
    }

    pub fn one() -> Self {
        Self {
            limbs: vec![TRIT_ALPHA as u64],
            width: 1,
        }
    }

    pub fn neg_one() -> Self {
        Self {
            limbs: vec![TRIT_OMEGA as u64],
            width: 1,
        }
    }

    pub fn from_limbs(mut limbs: Vec<u64>, width: usize) -> Result<Self, CoreError> {
        trim_u64(&mut limbs);
        if limbs_bit_len(&limbs) > 2 * width {
            return Err(CoreError::ValueError(format!(
                "packed limbs exceed width {} ({} bits)",
                width,
                2 * width
            )));
        }
        Ok(Self { limbs, width })
    }

    pub fn from_packed_u64(packed: u64, width: usize) -> Result<Self, CoreError> {
        let limbs = if packed == 0 {
            Vec::new()
        } else {
            vec![packed]
        };
        Self::from_limbs(limbs, width)
    }

    pub fn from_packed_bigint(packed: &BigInt, width: usize) -> Result<Self, CoreError> {
        if packed.is_negative() {
            return Err(CoreError::ValueError(
                "packed TritWord value must be nonnegative".to_string(),
            ));
        }
        if packed.bit_len() > 2 * width {
            return Err(CoreError::ValueError(format!(
                "packed value exceeds width {} ({} bits)",
                width,
                2 * width
            )));
        }
        let limbs = bigint_to_u64_limbs(packed)?;
        Ok(Self { limbs, width })
    }

    /// Encode any arbitrary-precision `BigInt` into minimal canonical balanced base-3 `TritWord`.
    pub fn from_bigint(value: &BigInt) -> Self {
        if value.is_zero() {
            return Self::zero();
        }
        if value.is_one() {
            return Self::one();
        }
        if value.to_i64() == Some(-1) {
            return Self::neg_one();
        }

        let radix16_big = BigInt::from_u32(RADIX16);
        let half16_big = BigInt::from_u32(HALF_RADIX16);
        let mut cur = value.clone();
        let mut limbs: Vec<u64> = Vec::new();
        let mut chunk_idx = 0usize;

        while !cur.is_zero() {
            let shifted = &cur + &half16_big;
            let (q, r_big) = shifted
                .div_rem_euclid(&radix16_big)
                .expect("RADIX16 is positive");
            let mut r = r_big.to_u32().expect("remainder < RADIX16 fits in u32");

            let b0 = BAL4_TO_BYTE[(r % RADIX4) as usize] as u32;
            r /= RADIX4;
            let b1 = BAL4_TO_BYTE[(r % RADIX4) as usize] as u32;
            r /= RADIX4;
            let b2 = BAL4_TO_BYTE[(r % RADIX4) as usize] as u32;
            r /= RADIX4;
            let b3 = BAL4_TO_BYTE[(r % RADIX4) as usize] as u32;
            let half_limb = (b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)) as u64;

            if (chunk_idx & 1) == 0 {
                limbs.push(half_limb);
            } else if let Some(last) = limbs.last_mut() {
                *last |= half_limb << 32;
            }
            chunk_idx += 1;
            cur = q;
        }

        trim_u64(&mut limbs);
        if limbs.is_empty() {
            return Self::zero();
        }
        let top = *limbs.last().unwrap();
        let width =
            (limbs.len() - 1) * LANES_PER_LIMB + ((63 - top.leading_zeros() as usize) >> 1) + 1;
        Self { limbs, width }
    }

    pub fn from_i64(value: i64) -> Self {
        Self::from_bigint(&BigInt::from_i64(value))
    }

    pub fn from_lanes(lanes: &[u8], msb_first: bool) -> Result<Self, CoreError> {
        let width = lanes.len();
        let mut limbs = vec![0u64; limb_count_for_width(width)];
        for idx in 0..width {
            let raw_lane = if msb_first {
                lanes[width - 1 - idx]
            } else {
                lanes[idx]
            };
            let v = validate_trit_lane(raw_lane)? as u64;
            limbs[idx / LANES_PER_LIMB] |= v << ((idx % LANES_PER_LIMB) * TRIT_LANE_BITS);
        }
        trim_u64(&mut limbs);
        Ok(Self { limbs, width })
    }

    pub fn from_symbols(text: &str, msb_first: bool) -> Result<Self, CoreError> {
        let chars: Vec<char> = text.chars().collect();
        let width = chars.len();
        let mut limbs = vec![0u64; limb_count_for_width(width)];
        for idx in 0..width {
            let ch = if msb_first {
                chars[width - 1 - idx]
            } else {
                chars[idx]
            };
            let v = symbol_to_trit_lane(ch)? as u64;
            limbs[idx / LANES_PER_LIMB] |= v << ((idx % LANES_PER_LIMB) * TRIT_LANE_BITS);
        }
        trim_u64(&mut limbs);
        Ok(Self { limbs, width })
    }

    pub fn from_chiral_pairs(
        pairs: &[ChiralPair4],
        width: Option<usize>,
    ) -> Result<Self, CoreError> {
        let w = width.unwrap_or(2 * pairs.len());
        let mut limbs = vec![0u64; limb_count_for_width(2 * pairs.len())];
        for (idx, pair) in pairs.iter().enumerate() {
            let lane_base = 2 * idx;
            let limb_idx = lane_base / LANES_PER_LIMB;
            let bit_shift = (lane_base % LANES_PER_LIMB) * TRIT_LANE_BITS;
            limbs[limb_idx] |= (pair.raw4() as u64) << bit_shift;
        }
        Self::from_limbs(limbs, w)
    }

    // --- Accessors & O(1)-Per-Limb SWAR Masks ------------------------------

    pub fn width(&self) -> usize {
        self.width
    }

    pub fn limbs(&self) -> &[u64] {
        &self.limbs
    }

    pub fn to_packed_bigint(&self) -> BigInt {
        limbs_to_bigint(&self.limbs)
    }

    pub fn dwell_mask(&self) -> LaneMask {
        let n = limb_count_for_width(self.width);
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            out.push(swar_dwell_mask_limb(
                get_limb(&self.limbs, i),
                active_lanes_in_limb(self.width, i),
            ));
        }
        LaneMask::from_limbs_unchecked(out)
    }

    pub fn alpha_mask(&self) -> LaneMask {
        let out: Vec<u64> = self.limbs.iter().map(|&w| swar_alpha_mask_limb(w)).collect();
        LaneMask::from_limbs_unchecked(out)
    }

    pub fn omega_mask(&self) -> LaneMask {
        let out: Vec<u64> = self.limbs.iter().map(|&w| swar_omega_mask_limb(w)).collect();
        LaneMask::from_limbs_unchecked(out)
    }

    pub fn polar_mask(&self) -> LaneMask {
        let out: Vec<u64> = self.limbs.iter().map(|&w| swar_polar_mask_limb(w)).collect();
        LaneMask::from_limbs_unchecked(out)
    }

    pub fn hinge_mask(&self) -> LaneMask {
        let out: Vec<u64> = self.limbs.iter().map(|&w| swar_hinge_mask_limb(w)).collect();
        LaneMask::from_limbs_unchecked(out)
    }

    pub fn has_hinge(&self) -> bool {
        self.limbs.iter().any(|&w| swar_hinge_mask_limb(w) != 0)
    }

    pub fn dwell_count(&self) -> usize {
        self.dwell_mask().count()
    }

    pub fn alpha_count(&self) -> usize {
        self.limbs
            .iter()
            .map(|&w| swar_alpha_mask_limb(w).count_ones() as usize)
            .sum()
    }

    pub fn omega_count(&self) -> usize {
        self.limbs
            .iter()
            .map(|&w| swar_omega_mask_limb(w).count_ones() as usize)
            .sum()
    }

    pub fn polar_count(&self) -> usize {
        self.limbs
            .iter()
            .map(|&w| swar_polar_mask_limb(w).count_ones() as usize)
            .sum()
    }

    pub fn hinge_count(&self) -> usize {
        self.limbs
            .iter()
            .map(|&w| swar_hinge_mask_limb(w).count_ones() as usize)
            .sum()
    }

    fn to_planes(&self) -> (Vec<u64>, Vec<u64>) {
        let mut a = Vec::with_capacity(self.limbs.len());
        let mut o = Vec::with_capacity(self.limbs.len());
        for &w in &self.limbs {
            let w1 = w >> 1;
            a.push((w & !w1) & MASK_01);
            o.push(((!w) & w1) & MASK_01);
        }
        trim_u64(&mut a);
        trim_u64(&mut o);
        (a, o)
    }

    // --- O(1)-Per-Limb SWAR Operations & Live Dwell Compaction -------------

    /// O(1)-per-limb SWAR lane-swap negation preserving `00 -> 00`, `11 -> 11`, and `width`.
    pub fn neg(&self) -> Self {
        let mut limbs: Vec<u64> = self.limbs.iter().map(|&w| swar_negate_limb(w)).collect();
        trim_u64(&mut limbs);
        Self {
            limbs,
            width: self.width,
        }
    }

    /// Exact balanced base-3 sign in `{-1, 0, +1}`.
    pub fn sign(&self) -> i8 {
        for &w in self.limbs.iter().rev() {
            let p = swar_polar_mask_limb(w);
            if p != 0 {
                let top_bit = 63 - p.leading_zeros() as usize;
                return if ((w >> top_bit) & 1) != 0 { 1 } else { -1 };
            }
        }
        0
    }

    pub fn is_zero_value(&self) -> bool {
        self.sign() == 0
    }

    /// O(1)-per-limb SWAR magnitude word preserving `0_H` hinges and `width`.
    pub fn abs_word(&self) -> Self {
        if self.sign() < 0 {
            self.neg()
        } else {
            self.clone()
        }
    }

    /// Exact balanced base-3 numeric comparison (`0_H` contributes 0).
    pub fn cmp_value(&self, other: &Self) -> Ordering {
        let max_len = self.limbs.len().max(other.limbs.len());
        for idx in (0..max_len).rev() {
            let w1 = get_limb(&self.limbs, idx);
            let p1 = swar_polar_mask_limb(w1);
            let c1 = w1 & swar_double_lane_mask_limb(p1);
            let w2 = get_limb(&other.limbs, idx);
            let p2 = swar_polar_mask_limb(w2);
            let c2 = w2 & swar_double_lane_mask_limb(p2);
            let diff = c1 ^ c2;
            if diff != 0 {
                let shift = (63 - diff.leading_zeros() as usize) & !1usize;
                let l1 = (c1 >> shift) & 0b11;
                let l2 = (c2 >> shift) & 0b11;
                let v1 = ((l1 & 1) as i8) - ((l1 >> 1) as i8);
                let v2 = ((l2 & 1) as i8) - ((l2 >> 1) as i8);
                return v1.cmp(&v2);
            }
        }
        Ordering::Equal
    }

    pub fn same_value(&self, other: &Self) -> bool {
        self.cmp_value(other) == Ordering::Equal
    }

    /// Minimal canonical balanced base-3 word (clears `0_H` and leading `0_D`).
    pub fn to_canonical(&self) -> Self {
        let mut limbs: Vec<u64> = self
            .limbs
            .iter()
            .map(|&w| {
                let p = swar_polar_mask_limb(w);
                w & swar_double_lane_mask_limb(p)
            })
            .collect();
        trim_u64(&mut limbs);
        if limbs.is_empty() {
            return Self::zero();
        }
        let top = *limbs.last().unwrap();
        let width =
            (limbs.len() - 1) * LANES_PER_LIMB + ((63 - top.leading_zeros() as usize) >> 1) + 1;
        Self { limbs, width }
    }

    /// Live contiguous dwell compaction (`xxxxx -> x`) retaining all `0_H` hinges and polar lanes.
    pub fn burn_contiguous_dwell(&self, keep_single_dwell: bool) -> Self {
        if self.width == 0 {
            return self.clone();
        }
        let num_limbs = limb_count_for_width(self.width);
        let mut dwell_limbs = Vec::with_capacity(num_limbs);
        let mut any_dwell = false;
        for i in 0..num_limbs {
            let d = swar_dwell_mask_limb(
                get_limb(&self.limbs, i),
                active_lanes_in_limb(self.width, i),
            );
            if d != 0 {
                any_dwell = true;
            }
            dwell_limbs.push(d);
        }
        if !any_dwell {
            return self.clone();
        }

        let mut keep_limbs = Vec::with_capacity(num_limbs);
        if keep_single_dwell {
            let mut any_redundant = false;
            let mut prev_top_dwell = 0u64;
            for i in 0..num_limbs {
                let d = dwell_limbs[i];
                let d_shifted = (d << 2) | prev_top_dwell;
                let redundant = d & d_shifted;
                if redundant != 0 {
                    any_redundant = true;
                }
                let active_m01 = limb_mask_01(active_lanes_in_limb(self.width, i));
                keep_limbs.push((!redundant) & active_m01);
                prev_top_dwell = d >> 62;
            }
            if !any_redundant {
                return self.clone();
            }
        } else {
            for i in 0..num_limbs {
                let active_m01 = limb_mask_01(active_lanes_in_limb(self.width, i));
                keep_limbs.push((!dwell_limbs[i]) & active_m01);
            }
        }

        let mut out_limbs: Vec<u64> = Vec::new();
        let mut out_width = 0usize;
        for i in 0..num_limbs {
            let mut rem = keep_limbs[i];
            let src = get_limb(&self.limbs, i);
            while rem != 0 {
                let tz = rem.trailing_zeros() as usize;
                rem &= rem - 1;
                let lane = (src >> tz) & 0b11;
                let out_limb_idx = out_width / LANES_PER_LIMB;
                let out_shift = (out_width % LANES_PER_LIMB) * TRIT_LANE_BITS;
                if out_limb_idx >= out_limbs.len() {
                    out_limbs.push(0);
                }
                out_limbs[out_limb_idx] |= lane << out_shift;
                out_width += 1;
            }
        }
        trim_u64(&mut out_limbs);
        Self {
            limbs: out_limbs,
            width: out_width,
        }
    }

    // --- Fast Balanced Base-3 Decode ---------------------------------------

    /// Decode packed word into exact arbitrary-precision `BigInt` (`0_D` and `0_H` contribute 0).
    pub fn to_bigint(&self) -> BigInt {
        if self.limbs.is_empty() {
            return BigInt::zero();
        }
        let radix32_big = BigInt::from_u64(RADIX32);
        let mut acc = BigInt::zero();
        for &limb in self.limbs.iter().rev() {
            let mut limb_val: i64 = 0;
            for byte_idx in (0..8).rev() {
                let byte = ((limb >> (8 * byte_idx)) & 0xFF) as usize;
                limb_val = limb_val * (RADIX4 as i64) + (BYTE_TO_BAL4[byte] as i64);
            }
            if !acc.is_zero() {
                acc = &acc * &radix32_big;
            }
            acc = &acc + &BigInt::from_i64(limb_val);
        }
        acc
    }

    // --- Pure-SWAR Exact Arithmetic & Carry-Barrier Addition ---------------

    pub fn add(&self, other: &Self) -> Self {
        let (a1, o1) = self.to_planes();
        let (a2, o2) = other.to_planes();
        let (sa, so) = swar_add_planes(&a1, &o1, &a2, &o2);
        planes_to_canonical_word(&sa, &so)
    }

    pub fn sub(&self, other: &Self) -> Self {
        let (a1, o1) = self.to_planes();
        let (a2, o2) = other.to_planes();
        let (sa, so) = swar_add_planes(&a1, &o1, &o2, &a2);
        planes_to_canonical_word(&sa, &so)
    }

    /// Add two words while blocking carries across `0_H` (`11`) structural hinges.
    pub fn add_hinge_barrier(&self, other: &Self) -> BarrierAddResult {
        let h_mask = self.hinge_mask().bit_or(&other.hinge_mask());
        let (a1, o1) = self.to_planes();
        let (a2, o2) = other.to_planes();

        if h_mask.is_zero() {
            let (sa, so) = swar_add_planes(&a1, &o1, &a2, &o2);
            return BarrierAddResult {
                result: planes_to_canonical_word(&sa, &so),
                hinge_mask: LaneMask::zero(),
                blocked_alpha_mask: LaneMask::zero(),
                blocked_omega_mask: LaneMask::zero(),
            };
        }

        let hm_limbs = h_mask.limbs();
        let init_len = a1
            .len()
            .max(o1.len())
            .max(a2.len())
            .max(o2.len())
            .max(hm_limbs.len());
        let mut cur_a = Vec::with_capacity(init_len);
        let mut cur_o = Vec::with_capacity(init_len);
        let mut add_a = Vec::with_capacity(init_len);
        let mut add_o = Vec::with_capacity(init_len);
        let mut blocked_a = Vec::with_capacity(init_len);
        let mut blocked_o = Vec::with_capacity(init_len);

        for i in 0..init_len {
            let hm = get_limb(hm_limbs, i);
            let nh = !hm;
            let a1_i = get_limb(&a1, i);
            let o1_i = get_limb(&o1, i);
            let a2_i = get_limb(&a2, i);
            let o2_i = get_limb(&o2, i);
            blocked_a.push((a1_i | a2_i) & hm);
            blocked_o.push((o1_i | o2_i) & hm);
            cur_a.push(a1_i & nh);
            cur_o.push(o1_i & nh);
            add_a.push(a2_i & nh);
            add_o.push(o2_i & nh);
        }
        trim_u64(&mut cur_a);
        trim_u64(&mut cur_o);
        trim_u64(&mut add_a);
        trim_u64(&mut add_o);

        while !add_a.is_empty() || !add_o.is_empty() {
            let n = cur_a.len().max(cur_o.len()).max(add_a.len()).max(add_o.len());
            let mut next_cur_a = Vec::with_capacity(n);
            let mut next_cur_o = Vec::with_capacity(n);
            let mut carry_a = Vec::with_capacity(n + 1);
            let mut carry_o = Vec::with_capacity(n + 1);
            let mut prev_ca_hi = 0u64;
            let mut prev_co_hi = 0u64;

            for i in 0..n {
                let ca1 = get_limb(&cur_a, i);
                let co1 = get_limb(&cur_o, i);
                let aa2 = get_limb(&add_a, i);
                let ao2 = get_limb(&add_o, i);
                let ca = ca1 & aa2;
                let co = co1 & ao2;
                let ax = ca1 ^ aa2;
                let ox = co1 ^ ao2;
                let cancel = ax & ox;
                next_cur_a.push((ax ^ cancel) | co);
                next_cur_o.push((ox ^ cancel) | ca);
                carry_a.push((ca << 2) | prev_ca_hi);
                carry_o.push((co << 2) | prev_co_hi);
                prev_ca_hi = ca >> 62;
                prev_co_hi = co >> 62;
            }
            if prev_ca_hi != 0 {
                carry_a.push(prev_ca_hi);
            }
            if prev_co_hi != 0 {
                carry_o.push(prev_co_hi);
            }

            let m = carry_a.len().max(carry_o.len()).max(hm_limbs.len());
            if blocked_a.len() < m {
                blocked_a.resize(m, 0);
            }
            if blocked_o.len() < m {
                blocked_o.resize(m, 0);
            }
            for i in 0..m {
                let hm = get_limb(hm_limbs, i);
                let nh = !hm;
                let ca_i = get_limb(&carry_a, i);
                let co_i = get_limb(&carry_o, i);
                blocked_a[i] |= ca_i & hm;
                blocked_o[i] |= co_i & hm;
                if i < carry_a.len() {
                    carry_a[i] = ca_i & nh;
                }
                if i < carry_o.len() {
                    carry_o[i] = co_i & nh;
                }
            }
            trim_u64(&mut next_cur_a);
            trim_u64(&mut next_cur_o);
            trim_u64(&mut carry_a);
            trim_u64(&mut carry_o);
            cur_a = next_cur_a;
            cur_o = next_cur_o;
            add_a = carry_a;
            add_o = carry_o;
        }

        let res_len = cur_a.len().max(cur_o.len()).max(hm_limbs.len());
        let mut res_limbs = Vec::with_capacity(res_len);
        for i in 0..res_len {
            let hm = get_limb(hm_limbs, i);
            res_limbs.push(get_limb(&cur_a, i) | (get_limb(&cur_o, i) << 1) | hm | (hm << 1));
        }
        trim_u64(&mut res_limbs);
        let res_width = if res_limbs.is_empty() {
            1
        } else {
            let top = *res_limbs.last().unwrap();
            (res_limbs.len() - 1) * LANES_PER_LIMB + ((63 - top.leading_zeros() as usize) >> 1) + 1
        };

        BarrierAddResult {
            result: TritWord {
                limbs: res_limbs,
                width: res_width,
            },
            hinge_mask: h_mask,
            blocked_alpha_mask: LaneMask::from_limbs_unchecked(blocked_a),
            blocked_omega_mask: LaneMask::from_limbs_unchecked(blocked_o),
        }
    }

    pub fn mul(&self, other: &Self) -> Self {
        let (a1, o1) = self.to_planes();
        let (a2, o2) = other.to_planes();
        let (pa, po) = swar_mul_planes(&a1, &o1, &a2, &o2);
        planes_to_canonical_word(&pa, &po)
    }

    /// Exact floor division and modulo agreeing with Python `divmod(a, b)`.
    pub fn divmod_floor(&self, other: &Self) -> Result<(Self, Self), CoreError> {
        let (da, do_p) = other.to_planes();
        let sd = planes_sign(&da, &do_p);
        if sd == 0 {
            return Err(CoreError::DivisionByZero(
                "TritWord division or modulo by zero".to_string(),
            ));
        }

        let (na, no) = self.to_planes();
        let sn = planes_sign(&na, &no);
        if sn == 0 {
            return Ok((Self::zero(), Self::zero()));
        }

        let (ua, uo) = if sn < 0 { (&no, &na) } else { (&na, &no) };
        let (va, vo) = if sd < 0 { (&do_p, &da) } else { (&da, &do_p) };
        let (qa, qo, ra, ro) = swar_divmod_pos_planes(ua, uo, va, vo);

        if sn > 0 && sd > 0 {
            return Ok((
                planes_to_canonical_word(&qa, &qo),
                planes_to_canonical_word(&ra, &ro),
            ));
        }
        if sn < 0 && sd < 0 {
            return Ok((
                planes_to_canonical_word(&qa, &qo),
                planes_to_canonical_word(&ro, &ra),
            ));
        }
        if planes_is_zero(&ra, &ro) {
            return Ok((planes_to_canonical_word(&qo, &qa), Self::zero()));
        }

        let (q1a, q1o) = swar_add_planes(&qa, &qo, &[1], &[]);
        let q_word = planes_to_canonical_word(&q1o, &q1a);
        let (r_a, r_o) = if sn > 0 {
            swar_add_planes(&ra, &ro, vo, va)
        } else {
            swar_add_planes(va, vo, &ro, &ra)
        };
        Ok((q_word, planes_to_canonical_word(&r_a, &r_o)))
    }

    /// Exact nonnegative greatest common divisor via pure-SWAR balanced base-3 GCD.
    pub fn gcd(&self, other: &Self) -> Self {
        let (a1, o1) = self.to_planes();
        let (a2, o2) = other.to_planes();
        let (ga, go) = swar_gcd_planes(&a1, &o1, &a2, &o2);
        planes_to_canonical_word(&ga, &go)
    }

    // --- Lane & Symbol Serialization ---------------------------------------

    pub fn lane_at(&self, index: usize) -> Result<u8, CoreError> {
        if index >= self.width {
            return Err(CoreError::ValueError(format!(
                "lane index {} out of range for width {}",
                index, self.width
            )));
        }
        let limb = get_limb(&self.limbs, index / LANES_PER_LIMB);
        let shift = (index % LANES_PER_LIMB) * TRIT_LANE_BITS;
        Ok(((limb >> shift) & 0b11) as u8)
    }

    pub fn lanes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(self.width);
        for idx in 0..self.width {
            let limb = get_limb(&self.limbs, idx / LANES_PER_LIMB);
            let shift = (idx % LANES_PER_LIMB) * TRIT_LANE_BITS;
            out.push(((limb >> shift) & 0b11) as u8);
        }
        out
    }

    pub fn to_msb_lanes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(self.width);
        for idx in (0..self.width).rev() {
            let limb = get_limb(&self.limbs, idx / LANES_PER_LIMB);
            let shift = (idx % LANES_PER_LIMB) * TRIT_LANE_BITS;
            out.push(((limb >> shift) & 0b11) as u8);
        }
        out
    }

    pub fn to_symbols(&self, msb_first: bool) -> String {
        let lane_vec = if msb_first {
            self.to_msb_lanes()
        } else {
            self.lanes()
        };
        let mut s = String::with_capacity(self.width);
        for lane in lane_vec {
            let ch = match lane {
                TRIT_DWELL => '0',
                TRIT_ALPHA => '+',
                TRIT_OMEGA => '-',
                TRIT_HINGE => 'H',
                _ => unreachable!(),
            };
            s.push(ch);
        }
        s
    }

    pub fn to_chiral_pairs(&self) -> Vec<ChiralPair4> {
        let pair_count = (self.width + 1) >> 1;
        let mut out = Vec::with_capacity(pair_count);
        for idx in 0..pair_count {
            let lane_base = 2 * idx;
            let limb = get_limb(&self.limbs, lane_base / LANES_PER_LIMB);
            let shift = (lane_base % LANES_PER_LIMB) * TRIT_LANE_BITS;
            let raw4 = ((limb >> shift) & 0b1111) as u8;
            out.push(ChiralPair4::from_bits(raw4).expect("4-bit slice valid"));
        }
        out
    }
}

impl std::ops::Neg for &TritWord {
    type Output = TritWord;
    fn neg(self) -> TritWord {
        TritWord::neg(self)
    }
}

impl std::ops::Neg for TritWord {
    type Output = TritWord;
    fn neg(self) -> TritWord {
        TritWord::neg(&self)
    }
}

impl std::ops::Add for &TritWord {
    type Output = TritWord;
    fn add(self, rhs: &TritWord) -> TritWord {
        TritWord::add(self, rhs)
    }
}

impl std::ops::Add for TritWord {
    type Output = TritWord;
    fn add(self, rhs: TritWord) -> TritWord {
        TritWord::add(&self, &rhs)
    }
}

impl std::ops::Sub for &TritWord {
    type Output = TritWord;
    fn sub(self, rhs: &TritWord) -> TritWord {
        TritWord::sub(self, rhs)
    }
}

impl std::ops::Sub for TritWord {
    type Output = TritWord;
    fn sub(self, rhs: TritWord) -> TritWord {
        TritWord::sub(&self, &rhs)
    }
}

impl std::ops::Mul for &TritWord {
    type Output = TritWord;
    fn mul(self, rhs: &TritWord) -> TritWord {
        TritWord::mul(self, rhs)
    }
}

impl std::ops::Mul for TritWord {
    type Output = TritWord;
    fn mul(self, rhs: TritWord) -> TritWord {
        TritWord::mul(&self, &rhs)
    }
}

// ---------------------------------------------------------------------------
// 2-Trit Micro-Ratio
// ---------------------------------------------------------------------------

/// Immutable 2-trit micro-ratio preserving `0b11` (`0_H`) hinge/saturation lanes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Trit2MicroRatio {
    num_lane: u8,
    den_lane: u8,
}

impl Trit2MicroRatio {
    pub fn new(num_lane: u8, den_lane: u8) -> Result<Self, CoreError> {
        Ok(Self {
            num_lane: validate_trit_lane(num_lane)?,
            den_lane: validate_trit_lane(den_lane)?,
        })
    }

    pub fn from_bits(bits: u8) -> Result<Self, CoreError> {
        if bits > 0b1111 {
            return Err(CoreError::ValueError(format!(
                "Trit2MicroRatio bits must be in 0..=15, got {}",
                bits
            )));
        }
        Ok(Self {
            num_lane: bits & TRIT_LANE_MASK,
            den_lane: (bits >> TRIT_LANE_BITS) & TRIT_LANE_MASK,
        })
    }

    pub fn num_lane(self) -> u8 {
        self.num_lane
    }

    pub fn den_lane(self) -> u8 {
        self.den_lane
    }

    pub fn raw4(self) -> u8 {
        (self.den_lane << TRIT_LANE_BITS) | self.num_lane
    }

    pub fn to_bits(self) -> u8 {
        self.raw4()
    }

    pub fn num_signed(self) -> i8 {
        ((self.num_lane & 1) as i8) - (((self.num_lane >> 1) & 1) as i8)
    }

    pub fn den_signed(self) -> i8 {
        ((self.den_lane & 1) as i8) - (((self.den_lane >> 1) & 1) as i8)
    }

    pub fn num_is_hinge(self) -> bool {
        self.num_lane == TRIT_HINGE
    }

    pub fn den_is_hinge(self) -> bool {
        self.den_lane == TRIT_HINGE
    }

    pub fn has_hinge(self) -> bool {
        self.num_is_hinge() || self.den_is_hinge()
    }

    pub fn is_saturated(self) -> bool {
        self.num_is_hinge() && self.den_is_hinge()
    }

    pub fn is_defined(self) -> bool {
        self.den_signed() != 0
    }

    pub fn is_singular(self) -> bool {
        self.den_signed() == 0
    }

    pub fn to_chiral_pair(self) -> ChiralPair4 {
        ChiralPair4 {
            lo_lane: self.num_lane,
            hi_lane: self.den_lane,
        }
    }

    pub fn from_chiral_pair(pair: ChiralPair4) -> Self {
        Self {
            num_lane: pair.lo_lane,
            den_lane: pair.hi_lane,
        }
    }

    pub fn neg(self) -> Self {
        Self {
            num_lane: ((self.num_lane & 0b01) << 1) | ((self.num_lane >> 1) & 0b01),
            den_lane: self.den_lane,
        }
    }

    pub fn reciprocal(self) -> Self {
        Self {
            num_lane: self.den_lane,
            den_lane: self.num_lane,
        }
    }

    pub fn exact_bigrat(self) -> Result<BigRat, CoreError> {
        if self.is_singular() {
            return Err(CoreError::DivisionByZero(
                "singular Trit2MicroRatio has zero denominator (0_D or 0_H)".to_string(),
            ));
        }
        BigRat::from_i64_pair(self.num_signed() as i64, self.den_signed() as i64)
    }

    pub fn to_trit_ratio(self) -> Result<TritRatio, CoreError> {
        if self.is_singular() {
            return Err(CoreError::DivisionByZero(
                "singular Trit2MicroRatio cannot convert to defined TritRatio".to_string(),
            ));
        }
        TritRatio::new(
            TritWord::from_packed_u64(self.num_lane as u64, 1)?,
            TritWord::from_packed_u64(self.den_lane as u64, 1)?,
        )
    }
}

impl std::ops::Neg for Trit2MicroRatio {
    type Output = Trit2MicroRatio;
    fn neg(self) -> Trit2MicroRatio {
        Trit2MicroRatio::neg(self)
    }
}

impl std::ops::Neg for &Trit2MicroRatio {
    type Output = Trit2MicroRatio;
    fn neg(self) -> Trit2MicroRatio {
        Trit2MicroRatio::neg(*self)
    }
}

// ---------------------------------------------------------------------------
// Exact Arbitrary-Width Ternary Rational: TritRatio
// ---------------------------------------------------------------------------

/// Immutable exact rational backed strictly by coprime `TritWord` registers
/// plus preserved `0_H` hinge metadata masks (never wrapping `BigRat`).
#[derive(Debug, Clone)]
pub struct TritRatio {
    num: TritWord,
    den: TritWord,
    num_hinge_mask: LaneMask,
    den_hinge_mask: LaneMask,
}

impl TritRatio {
    pub fn zero() -> Self {
        Self {
            num: TritWord::zero(),
            den: TritWord::one(),
            num_hinge_mask: LaneMask::zero(),
            den_hinge_mask: LaneMask::zero(),
        }
    }

    pub fn one() -> Self {
        Self {
            num: TritWord::one(),
            den: TritWord::one(),
            num_hinge_mask: LaneMask::zero(),
            den_hinge_mask: LaneMask::zero(),
        }
    }

    pub fn new(num: TritWord, den: TritWord) -> Result<Self, CoreError> {
        Self::new_with_masks(num, den, LaneMask::zero(), LaneMask::zero())
    }

    pub fn new_with_masks(
        num: TritWord,
        den: TritWord,
        num_hinge_mask: LaneMask,
        den_hinge_mask: LaneMask,
    ) -> Result<Self, CoreError> {
        let nh = num.hinge_mask().bit_or(&num_hinge_mask);
        let dh = den.hinge_mask().bit_or(&den_hinge_mask);

        let (mut da, mut do_p) = den.to_planes();
        let ds = planes_sign(&da, &do_p);
        if ds == 0 {
            return Err(CoreError::DivisionByZero(
                "TritRatio denominator must be non-zero".to_string(),
            ));
        }

        let (mut na, mut no) = num.to_planes();
        if ds < 0 {
            std::mem::swap(&mut na, &mut no);
            std::mem::swap(&mut da, &mut do_p);
        }

        if planes_is_zero(&na, &no) {
            return Ok(Self {
                num: TritWord::zero(),
                den: TritWord::one(),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            });
        }

        let (ga, go) = swar_gcd_planes(&na, &no, &da, &do_p);
        if !planes_is_one(&ga, &go) {
            let (nna, nno) = swar_div_exact_pos_planes(&na, &no, &ga, &go)?;
            let (nda, ndo) = swar_div_exact_pos_planes(&da, &do_p, &ga, &go)?;
            na = nna;
            no = nno;
            da = nda;
            do_p = ndo;
        }

        Ok(Self {
            num: planes_to_canonical_word(&na, &no),
            den: planes_to_canonical_word(&da, &do_p),
            num_hinge_mask: nh,
            den_hinge_mask: dh,
        })
    }

    pub fn from_bigints(num: &BigInt, den: &BigInt) -> Result<Self, CoreError> {
        Self::from_bigints_with_masks(num, den, LaneMask::zero(), LaneMask::zero())
    }

    pub fn from_bigints_with_masks(
        num: &BigInt,
        den: &BigInt,
        num_hinge_mask: LaneMask,
        den_hinge_mask: LaneMask,
    ) -> Result<Self, CoreError> {
        if den.is_zero() {
            return Err(CoreError::DivisionByZero(
                "TritRatio denominator must be non-zero".to_string(),
            ));
        }
        Self::new_with_masks(
            TritWord::from_bigint(num),
            TritWord::from_bigint(den),
            num_hinge_mask,
            den_hinge_mask,
        )
    }

    pub fn from_i64_pair(num: i64, den: i64) -> Result<Self, CoreError> {
        Self::from_bigints(&BigInt::from_i64(num), &BigInt::from_i64(den))
    }

    pub fn from_bigrat(q: &BigRat) -> Self {
        Self::from_bigrat_with_masks(q, LaneMask::zero(), LaneMask::zero())
    }

    pub fn from_bigrat_with_masks(
        q: &BigRat,
        num_hinge_mask: LaneMask,
        den_hinge_mask: LaneMask,
    ) -> Self {
        Self {
            num: TritWord::from_bigint(q.num()),
            den: TritWord::from_bigint(q.den()),
            num_hinge_mask,
            den_hinge_mask,
        }
    }

    pub fn num(&self) -> &TritWord {
        &self.num
    }

    pub fn den(&self) -> &TritWord {
        &self.den
    }

    pub fn num_hinge_mask(&self) -> &LaneMask {
        &self.num_hinge_mask
    }

    pub fn den_hinge_mask(&self) -> &LaneMask {
        &self.den_hinge_mask
    }

    pub fn has_hinge(&self) -> bool {
        !self.num_hinge_mask.is_zero() || !self.den_hinge_mask.is_zero()
    }

    pub fn sign(&self) -> i8 {
        self.num.sign()
    }

    pub fn is_zero(&self) -> bool {
        self.num.is_zero_value()
    }

    pub fn to_bigint_pair(&self) -> (BigInt, BigInt) {
        (self.num.to_bigint(), self.den.to_bigint())
    }

    pub fn to_bigrat(&self) -> BigRat {
        let (n, d) = self.to_bigint_pair();
        BigRat::new(n, d).expect("canonical TritRatio has positive denominator")
    }

    pub fn canonical_pair(&self) -> [String; 2] {
        let (n, d) = self.to_bigint_pair();
        [n.to_dec_string(), d.to_dec_string()]
    }

    pub fn canonical_str(&self) -> String {
        let [n_s, d_s] = self.canonical_pair();
        if d_s == "1" {
            n_s
        } else {
            format!("{}/{}", n_s, d_s)
        }
    }

    pub fn structural_eq(&self, other: &Self) -> bool {
        self.num == other.num
            && self.den == other.den
            && self.num_hinge_mask == other.num_hinge_mask
            && self.den_hinge_mask == other.den_hinge_mask
    }

    pub fn with_cleared_metadata(&self) -> Self {
        Self {
            num: self.num.clone(),
            den: self.den.clone(),
            num_hinge_mask: LaneMask::zero(),
            den_hinge_mask: LaneMask::zero(),
        }
    }

    // --- Exact Arithmetic --------------------------------------------------

    pub fn neg(&self) -> Self {
        Self {
            num: self.num.neg(),
            den: self.den.clone(),
            num_hinge_mask: self.num_hinge_mask.clone(),
            den_hinge_mask: self.den_hinge_mask.clone(),
        }
    }

    pub fn abs_ratio(&self) -> Self {
        Self {
            num: self.num.abs_word(),
            den: self.den.clone(),
            num_hinge_mask: self.num_hinge_mask.clone(),
            den_hinge_mask: self.den_hinge_mask.clone(),
        }
    }

    pub fn reciprocal(&self) -> Result<Self, CoreError> {
        let ns = self.num.sign();
        if ns == 0 {
            return Err(CoreError::DivisionByZero(
                "cannot take reciprocal of zero TritRatio".to_string(),
            ));
        }
        let (new_num, new_den) = if ns > 0 {
            (self.den.clone(), self.num.clone())
        } else {
            (self.den.neg(), self.num.neg())
        };
        Ok(Self {
            num: new_num,
            den: new_den,
            num_hinge_mask: self.den_hinge_mask.clone(),
            den_hinge_mask: self.num_hinge_mask.clone(),
        })
    }

    /// Exact rational addition using Henrici pre-reduction on `TritWord` registers.
    pub fn add(&self, other: &Self) -> Self {
        let nh = self.num_hinge_mask.bit_or(&other.num_hinge_mask);
        let dh = self.den_hinge_mask.bit_or(&other.den_hinge_mask);

        let (aa, ao) = self.num.to_planes();
        let (ba, bo) = self.den.to_planes();
        let (ca, co) = other.num.to_planes();
        let (da, do_p) = other.den.to_planes();

        if planes_is_zero(&aa, &ao) {
            return Self {
                num: other.num.clone(),
                den: other.den.clone(),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            };
        }
        if planes_is_zero(&ca, &co) {
            return Self {
                num: self.num.clone(),
                den: self.den.clone(),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            };
        }

        let (ga, go) = swar_gcd_planes(&ba, &bo, &da, &do_p);
        if planes_is_one(&ga, &go) {
            let (p1a, p1o) = swar_mul_planes(&aa, &ao, &da, &do_p);
            let (p2a, p2o) = swar_mul_planes(&ca, &co, &ba, &bo);
            let (na, no) = swar_add_planes(&p1a, &p1o, &p2a, &p2o);
            if planes_is_zero(&na, &no) {
                return Self {
                    num: TritWord::zero(),
                    den: TritWord::one(),
                    num_hinge_mask: nh,
                    den_hinge_mask: dh,
                };
            }
            let (den_a, den_o) = swar_mul_planes(&ba, &bo, &da, &do_p);
            return Self {
                num: planes_to_canonical_word(&na, &no),
                den: planes_to_canonical_word(&den_a, &den_o),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            };
        }

        let (b1a, b1o) =
            swar_div_exact_pos_planes(&ba, &bo, &ga, &go).expect("gcd divides denominator");
        let (d1a, d1o) =
            swar_div_exact_pos_planes(&da, &do_p, &ga, &go).expect("gcd divides denominator");
        let (p1a, p1o) = swar_mul_planes(&aa, &ao, &d1a, &d1o);
        let (p2a, p2o) = swar_mul_planes(&ca, &co, &b1a, &b1o);
        let (ta, to) = swar_add_planes(&p1a, &p1o, &p2a, &p2o);
        if planes_is_zero(&ta, &to) {
            return Self {
                num: TritWord::zero(),
                den: TritWord::one(),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            };
        }

        let (g2a, g2o) = swar_gcd_planes(&ta, &to, &ga, &go);
        let (na, no, den_a, den_o) = if planes_is_one(&g2a, &g2o) {
            let (dna, dno) = swar_mul_planes(&b1a, &b1o, &da, &do_p);
            (ta, to, dna, dno)
        } else {
            let (nna, nno) =
                swar_div_exact_pos_planes(&ta, &to, &g2a, &g2o).expect("g2 divides numerator");
            let (d2a, d2o) =
                swar_div_exact_pos_planes(&da, &do_p, &g2a, &g2o).expect("g2 divides denominator");
            let (dna, dno) = swar_mul_planes(&b1a, &b1o, &d2a, &d2o);
            (nna, nno, dna, dno)
        };
        Self {
            num: planes_to_canonical_word(&na, &no),
            den: planes_to_canonical_word(&den_a, &den_o),
            num_hinge_mask: nh,
            den_hinge_mask: dh,
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        self.add(&other.neg())
    }

    /// Exact rational multiplication using pre-multiply cross-cancellation.
    pub fn mul(&self, other: &Self) -> Self {
        let nh = self.num_hinge_mask.bit_or(&other.num_hinge_mask);
        let dh = self.den_hinge_mask.bit_or(&other.den_hinge_mask);

        let (mut aa, mut ao) = self.num.to_planes();
        let (mut ca, mut co) = other.num.to_planes();
        if planes_is_zero(&aa, &ao) || planes_is_zero(&ca, &co) {
            return Self {
                num: TritWord::zero(),
                den: TritWord::one(),
                num_hinge_mask: nh,
                den_hinge_mask: dh,
            };
        }

        let (mut ba, mut bo) = self.den.to_planes();
        let (mut da, mut do_p) = other.den.to_planes();

        let (g1a, g1o) = swar_gcd_planes(&aa, &ao, &da, &do_p);
        if !planes_is_one(&g1a, &g1o) {
            let (naa, nao) =
                swar_div_exact_pos_planes(&aa, &ao, &g1a, &g1o).expect("g1 divides num");
            let (nda, ndo) =
                swar_div_exact_pos_planes(&da, &do_p, &g1a, &g1o).expect("g1 divides den");
            aa = naa;
            ao = nao;
            da = nda;
            do_p = ndo;
        }

        let (g2a, g2o) = swar_gcd_planes(&ca, &co, &ba, &bo);
        if !planes_is_one(&g2a, &g2o) {
            let (nca, nco) =
                swar_div_exact_pos_planes(&ca, &co, &g2a, &g2o).expect("g2 divides num");
            let (nba, nbo) =
                swar_div_exact_pos_planes(&ba, &bo, &g2a, &g2o).expect("g2 divides den");
            ca = nca;
            co = nco;
            ba = nba;
            bo = nbo;
        }

        let (na, no) = swar_mul_planes(&aa, &ao, &ca, &co);
        let (den_a, den_o) = swar_mul_planes(&ba, &bo, &da, &do_p);
        Self {
            num: planes_to_canonical_word(&na, &no),
            den: planes_to_canonical_word(&den_a, &den_o),
            num_hinge_mask: nh,
            den_hinge_mask: dh,
        }
    }

    pub fn checked_div(&self, other: &Self) -> Result<Self, CoreError> {
        let inv = other.reciprocal()?;
        Ok(self.mul(&inv))
    }
}

impl PartialEq for TritRatio {
    fn eq(&self, other: &Self) -> bool {
        self.num == other.num && self.den == other.den
    }
}

impl Eq for TritRatio {}

impl Hash for TritRatio {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.num.hash(state);
        self.den.hash(state);
    }
}

impl Ord for TritRatio {
    fn cmp(&self, other: &Self) -> Ordering {
        let s1 = self.num.sign();
        let s2 = other.num.sign();
        if s1 != s2 {
            return s1.cmp(&s2);
        }
        if s1 == 0 {
            return Ordering::Equal;
        }
        if self.den == other.den {
            return self.num.cmp_value(&other.num);
        }
        let lhs = self.num.mul(&other.den);
        let rhs = other.num.mul(&self.den);
        lhs.cmp_value(&rhs)
    }
}

impl PartialOrd for TritRatio {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl fmt::Display for TritRatio {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.canonical_str())
    }
}

impl std::ops::Neg for &TritRatio {
    type Output = TritRatio;
    fn neg(self) -> TritRatio {
        TritRatio::neg(self)
    }
}

impl std::ops::Neg for TritRatio {
    type Output = TritRatio;
    fn neg(self) -> TritRatio {
        TritRatio::neg(&self)
    }
}

impl std::ops::Add for &TritRatio {
    type Output = TritRatio;
    fn add(self, rhs: &TritRatio) -> TritRatio {
        TritRatio::add(self, rhs)
    }
}

impl std::ops::Add for TritRatio {
    type Output = TritRatio;
    fn add(self, rhs: TritRatio) -> TritRatio {
        TritRatio::add(&self, &rhs)
    }
}

impl std::ops::Sub for &TritRatio {
    type Output = TritRatio;
    fn sub(self, rhs: &TritRatio) -> TritRatio {
        TritRatio::sub(self, rhs)
    }
}

impl std::ops::Sub for TritRatio {
    type Output = TritRatio;
    fn sub(self, rhs: TritRatio) -> TritRatio {
        TritRatio::sub(&self, &rhs)
    }
}

impl std::ops::Mul for &TritRatio {
    type Output = TritRatio;
    fn mul(self, rhs: &TritRatio) -> TritRatio {
        TritRatio::mul(self, rhs)
    }
}

impl std::ops::Mul for TritRatio {
    type Output = TritRatio;
    fn mul(self, rhs: TritRatio) -> TritRatio {
        TritRatio::mul(&self, &rhs)
    }
}

// ---------------------------------------------------------------------------
// Comprehensive Unit Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::hash_map::DefaultHasher;

    fn hash_of<T: Hash>(v: &T) -> u64 {
        let mut h = DefaultHasher::new();
        v.hash(&mut h);
        h.finish()
    }

    fn ref_burn_lanes(lanes: &[u8], keep_single_dwell: bool) -> Vec<u8> {
        let mut out = Vec::new();
        let mut prev_dwell = false;
        for &lane in lanes {
            if lane == TRIT_DWELL {
                if keep_single_dwell && !prev_dwell {
                    out.push(TRIT_DWELL);
                }
                prev_dwell = true;
            } else {
                out.push(lane);
                prev_dwell = false;
            }
        }
        out
    }

    #[test]
    fn test_lane_primitives_and_chiral_pair4_all_16_states() {
        let expected_signed = [0i8, 1, -1, 0];
        let expected_neg = [TRIT_DWELL, TRIT_OMEGA, TRIT_ALPHA, TRIT_HINGE];
        let expected_sym = ['0', '+', '-', 'H'];

        for lane in 0u8..4 {
            assert_eq!(validate_trit_lane(lane).unwrap(), lane);
            assert_eq!(trit_lane_to_signed(lane).unwrap(), expected_signed[lane as usize]);
            assert_eq!(negate_trit_lane(lane).unwrap(), expected_neg[lane as usize]);
            assert_eq!(negate_trit_lane(negate_trit_lane(lane).unwrap()).unwrap(), lane);
            let sym = trit_lane_symbol(lane).unwrap();
            assert_eq!(sym, expected_sym[lane as usize]);
            assert_eq!(symbol_to_trit_lane(sym).unwrap(), lane);
        }
        assert!(validate_trit_lane(4).is_err());
        assert_eq!(signed_to_trit_lane(-1).unwrap(), TRIT_OMEGA);
        assert_eq!(signed_to_trit_lane(0).unwrap(), TRIT_DWELL);
        assert_eq!(signed_to_trit_lane(1).unwrap(), TRIT_ALPHA);
        assert!(signed_to_trit_lane(2).is_err());
        assert!(symbol_to_trit_lane('x').is_err());

        let mut hinge_count = 0usize;
        let mut sat_count = 0usize;
        for bits in 0u8..16 {
            let lo = bits & 0b11;
            let hi = (bits >> 2) & 0b11;
            let p = ChiralPair4::from_bits(bits).unwrap();
            assert_eq!(p, ChiralPair4::from_lanes(lo, hi).unwrap());
            assert_eq!(p.raw4(), bits);
            assert_eq!(p.to_bits(), bits);
            assert_eq!(
                p.net_charge(),
                trit_lane_to_signed(lo).unwrap() + trit_lane_to_signed(hi).unwrap()
            );
            if p.has_hinge() {
                hinge_count += 1;
            }
            if p.is_saturated() {
                sat_count += 1;
            }
            let flipped = p.chiral_flip();
            assert_eq!(flipped, -p);
            assert_eq!(flipped.chiral_flip(), p);
            assert_eq!(flipped.net_charge(), -p.net_charge());
            assert_eq!(flipped.has_hinge(), p.has_hinge());
            assert_eq!(flipped.is_saturated(), p.is_saturated());
            assert_eq!(flipped.lo_lane(), negate_trit_lane(lo).unwrap());
            assert_eq!(flipped.hi_lane(), negate_trit_lane(hi).unwrap());

            let w = p.to_trit_word();
            assert_eq!(ChiralPair4::from_trit_word(&w).unwrap(), p);
            assert_eq!(flipped.to_trit_word(), w.neg());
        }
        assert_eq!(hinge_count, 7);
        assert_eq!(sat_count, 1);
        assert!(ChiralPair4::from_bits(16).is_err());
        assert!(ChiralPair4::from_trit_word(&TritWord::zero_with_width(3)).is_err());
    }

    #[test]
    fn test_swar_masks_multi_limb_and_burn_contiguous_dwell() {
        // Exhaustive 4-lane check (all 256 states)
        for raw in 0u64..256 {
            let w = TritWord::from_packed_u64(raw, 4).unwrap();
            let lanes = w.lanes();
            assert_eq!(lanes.len(), 4);
            let mut exp_val = 0i64;
            let mut pow3 = 1i64;
            for &l in &lanes {
                exp_val += (trit_lane_to_signed(l).unwrap() as i64) * pow3;
                pow3 *= 3;
            }
            assert_eq!(w.to_bigint(), BigInt::from_i64(exp_val));
            assert_eq!(w.sign(), exp_val.signum() as i8);
            assert_eq!(
                w.dwell_count() + w.alpha_count() + w.omega_count() + w.hinge_count(),
                4
            );
            assert_eq!(w.polar_count(), w.alpha_count() + w.omega_count());

            let nw = w.neg();
            assert_eq!(nw.to_bigint(), BigInt::from_i64(-exp_val));
            assert_eq!(nw.hinge_mask(), w.hinge_mask());
            assert_eq!(nw.dwell_mask(), w.dwell_mask());
            assert_eq!(nw.neg(), w);

            let canon = w.to_canonical();
            assert_eq!(canon, TritWord::from_i64(exp_val));
            assert!(w.same_value(&canon));
            assert!(!canon.has_hinge());

            let b_keep = w.burn_contiguous_dwell(true);
            assert_eq!(b_keep.lanes(), ref_burn_lanes(&lanes, true));
            assert_eq!(b_keep.burn_contiguous_dwell(true), b_keep);

            let b_drop = w.burn_contiguous_dwell(false);
            assert_eq!(b_drop.lanes(), ref_burn_lanes(&lanes, false));
            assert_eq!(b_drop.burn_contiguous_dwell(false), b_drop);
            assert_eq!(b_drop.dwell_count(), 0);
        }

        // Multi-limb SWAR coverage across widths 0..=100 (crossing 32, 64, 96 lane boundaries)
        let pattern = [TRIT_DWELL, TRIT_ALPHA, TRIT_OMEGA, TRIT_HINGE, TRIT_DWELL, TRIT_DWELL];
        for width in 0usize..=100 {
            let lanes: Vec<u8> = (0..width).map(|i| pattern[i % pattern.len()]).collect();
            let w = TritWord::from_lanes(&lanes, false).unwrap();
            assert_eq!(w.width(), width);
            assert_eq!(w.lanes(), lanes);
            assert_eq!(
                w.dwell_count() + w.alpha_count() + w.omega_count() + w.hinge_count(),
                width
            );
            let packed = w.to_packed_bigint();
            assert_eq!(TritWord::from_packed_bigint(&packed, width).unwrap(), w);
            assert_eq!(
                swar_negate_bigint(&packed, width).unwrap(),
                w.neg().to_packed_bigint()
            );
            assert_eq!(
                swar_hinge_mask_bigint(&packed, width, false).unwrap(),
                w.hinge_mask().to_bigint()
            );
            assert_eq!(
                swar_dwell_mask_bigint(&packed, width, false).unwrap(),
                w.dwell_mask().to_bigint()
            );
            assert_eq!(
                swar_alpha_mask_bigint(&packed, width, true).unwrap(),
                w.alpha_mask().to_doubled_bigint()
            );
            assert_eq!(
                swar_omega_mask_bigint(&packed, width, true).unwrap(),
                w.omega_mask().to_doubled_bigint()
            );
            assert_eq!(
                swar_polar_mask_bigint(&packed, width, false).unwrap(),
                w.polar_mask().to_bigint()
            );
            assert_eq!(
                w.burn_contiguous_dwell(true).lanes(),
                ref_burn_lanes(&lanes, true)
            );
            assert_eq!(
                w.burn_contiguous_dwell(false).lanes(),
                ref_burn_lanes(&lanes, false)
            );
        }

        // Cross-limb all-dwell compaction (70 dwell lanes -> single dwell lane)
        let all_dwell_70 = TritWord::from_symbols(&"0".repeat(70), true).unwrap();
        assert_eq!(all_dwell_70.burn_contiguous_dwell(true), TritWord::zero());
        assert_eq!(
            all_dwell_70.burn_contiguous_dwell(false),
            TritWord::zero_with_width(0)
        );
    }

    #[test]
    fn test_cross_limb_carry_chains_and_add_hinge_barrier() {
        // Carry chains across limb boundaries (k = 31, 32, 33, 64, 65)
        let one = BigInt::one();
        let three = BigInt::from_u32(3);
        for k in [1u32, 2, 16, 31, 32, 33, 64, 65, 96] {
            let p3 = three.pow_u32(k);
            let max_k = (&p3 - &one).div_rem_trunc(&BigInt::from_u32(2)).unwrap().0;
            let min_k = -&max_k;
            let w_max = TritWord::from_bigint(&max_k);
            let w_min = TritWord::from_bigint(&min_k);
            assert_eq!((&w_max + &TritWord::one()).to_bigint(), &max_k + &one);
            assert_eq!((&w_min - &TritWord::one()).to_bigint(), &min_k - &one);
            assert_eq!((&w_max + &w_max).to_bigint(), &max_k + &max_k);
        }

        // Opposite-sign carry-cancel across limb 0->1 boundary:
        // lane 31 = +, lanes 0..30 = - (twice, plus -1 carry from lower)
        let p3_31 = three.pow_u32(31);
        let low_31 = (&p3_31 - &one).div_rem_trunc(&BigInt::from_u32(2)).unwrap().0;
        let special = &p3_31 - &low_31;
        let a_big = &(&special * &three.pow_u32(32)) - &low_31;
        let b_big = &(&special * &three.pow_u32(32)) - &low_31;
        let wa = TritWord::from_bigint(&a_big);
        let wb = TritWord::from_bigint(&b_big);
        assert_eq!((&wa + &wb).to_bigint(), &a_big + &b_big);

        // Multi-barrier addition with alpha & omega blocks
        let a2 = TritWord::from_symbols("+H++H---", true).unwrap();
        let b2 = TritWord::from_symbols("+H0+H00-", true).unwrap();
        let res2 = a2.add_hinge_barrier(&b2);
        assert_eq!(res2.result.to_symbols(true), "+-H--H+++");
        assert_eq!(res2.hinge_mask.to_bigint(), BigInt::from_u64((1 << 6) | (1 << 12)));
        assert_eq!(res2.blocked_omega_mask.to_bigint(), BigInt::from_u64(1 << 6));
        assert_eq!(res2.blocked_alpha_mask.to_bigint(), BigInt::from_u64(1 << 12));
        assert!(res2.had_blocked_carry());
        assert_eq!(res2.result.hinge_mask(), res2.hinge_mask);

        // Cross-limb hinge barrier at lane 32 (bit 0 of limb 1)
        let mut sym_a = String::from("+H");
        sym_a.push_str(&"+".repeat(32));
        let mut sym_b = String::from("+0");
        sym_b.push_str(&"0".repeat(31));
        sym_b.push('+');
        let wa_cl = TritWord::from_symbols(&sym_a, true).unwrap();
        let wb_cl = TritWord::from_symbols(&sym_b, true).unwrap();
        let res_cl = wa_cl.add_hinge_barrier(&wb_cl);
        assert!(res_cl.hinge_mask.has_lane(32));
        assert!(res_cl.blocked_alpha_mask.has_lane(32));
        assert!(res_cl.blocked_omega_mask.is_zero());
        assert_eq!(res_cl.result.hinge_mask(), res_cl.hinge_mask);
        // Low 32 lanes overflowed from +++...+ + 1 -> ---...- with carry blocked at lane 32!
        let expected_cl = format!("+-H{}", "-".repeat(32));
        assert_eq!(res_cl.result.to_symbols(true), expected_cl);
    }

    #[test]
    fn test_arithmetic_grid_and_230_digit_483_trit_exactness() {
        for a in -30i64..=30 {
            let wa = TritWord::from_i64(a);
            assert_eq!(wa.to_bigint(), BigInt::from_i64(a));
            for b in -30i64..=30 {
                let wb = TritWord::from_i64(b);
                assert_eq!((&wa + &wb).to_bigint(), BigInt::from_i64(a + b));
                assert_eq!((&wa - &wb).to_bigint(), BigInt::from_i64(a - b));
                assert_eq!((&wa * &wb).to_bigint(), BigInt::from_i64(a * b));
                assert_eq!(wa.cmp_value(&wb), a.cmp(&b));
                assert_eq!(
                    wa.gcd(&wb).to_bigint(),
                    BigInt::gcd(&BigInt::from_i64(a), &BigInt::from_i64(b))
                );
                if b != 0 {
                    let (qw, rw) = wa.divmod_floor(&wb).unwrap();
                    let qb = qw.to_bigint();
                    let rb = rw.to_bigint();
                    let ba = BigInt::from_i64(a);
                    let bb = BigInt::from_i64(b);
                    assert_eq!(&(&qb * &bb) + &rb, ba);
                    if b > 0 {
                        assert!(!rb.is_negative() && rb < bb);
                    } else {
                        assert!(!rb.is_positive() && rb > bb);
                    }
                }
            }
        }

        // 230-digit (~483-trit) Karatsuba mul, divmod, gcd, and unbalanced 200x65 Karatsuba
        let big_a = &BigInt::pow10(230) + &BigInt::from_i64(17);
        let big_b = &BigInt::pow10(230) - &BigInt::from_i64(29);
        let wa = TritWord::from_bigint(&big_a);
        let wb = TritWord::from_bigint(&big_b);
        assert!(wa.width() >= 480 && wb.width() >= 480);
        assert_eq!(wa.to_bigint(), big_a);
        assert_eq!(wb.to_bigint(), big_b);

        let prod = &wa * &wb;
        assert_eq!(prod.to_bigint(), &big_a * &big_b);
        let (q_h, r_h) = prod.divmod_floor(&wa).unwrap();
        assert_eq!(q_h, wb);
        assert_eq!(r_h, TritWord::zero());

        let g_factor = &BigInt::from_u32(3).pow_u32(25) * &BigInt::from_u32(137);
        let ga_in = &g_factor * &(&BigInt::pow10(60) + &BigInt::one());
        let gb_in = -&(&g_factor * &(&BigInt::pow10(60) + &BigInt::from_u32(2)));
        let wga = TritWord::from_bigint(&ga_in);
        let wgb = TritWord::from_bigint(&gb_in);
        assert_eq!(wga.gcd(&wgb).to_bigint(), g_factor);

        // Unbalanced Karatsuba (200 trits x 65 trits)
        let u_big = &(&BigInt::from_u32(3).pow_u32(199)
            + &(&BigInt::from_u32(17) * &BigInt::from_u32(3).pow_u32(100)))
            - &BigInt::from_u32(54_321);
        let u_mid = -&(&BigInt::from_u32(3).pow_u32(64) + &BigInt::from_u32(123_456_789));
        let wu_big = TritWord::from_bigint(&u_big);
        let wu_mid = TritWord::from_bigint(&u_mid);
        assert_eq!(wu_big.width(), 200);
        assert_eq!(wu_mid.width(), 65);
        assert_eq!((&wu_big * &wu_mid).to_bigint(), &u_big * &u_mid);
        assert_eq!((&wu_mid * &wu_big).to_bigint(), &u_mid * &u_big);
    }

    #[test]
    fn test_trit2_micro_ratio_all_16_states() {
        let mut defined = 0usize;
        let mut singular = 0usize;
        let mut hinges = 0usize;
        let mut saturated = 0usize;

        for bits in 0u8..16 {
            let m = Trit2MicroRatio::from_bits(bits).unwrap();
            assert_eq!(m.raw4(), bits);
            assert_eq!(m.to_bits(), bits);
            assert_eq!(m.is_defined(), !m.is_singular());
            if m.is_defined() {
                defined += 1;
            } else {
                singular += 1;
            }
            if m.has_hinge() {
                hinges += 1;
            }
            if m.is_saturated() {
                saturated += 1;
            }
            let cp = m.to_chiral_pair();
            assert_eq!(Trit2MicroRatio::from_chiral_pair(cp), m);
            assert_eq!((-m).neg(), m);
            assert_eq!(m.reciprocal().reciprocal(), m);

            if m.is_defined() {
                let br = m.exact_bigrat().unwrap();
                assert_eq!(
                    br,
                    BigRat::from_i64_pair(m.num_signed() as i64, m.den_signed() as i64).unwrap()
                );
                let tr = m.to_trit_ratio().unwrap();
                assert_eq!(tr.to_bigrat(), br);
                let exp_nh = if m.num_is_hinge() {
                    LaneMask::from_u64(1).unwrap()
                } else {
                    LaneMask::zero()
                };
                assert_eq!(*tr.num_hinge_mask(), exp_nh);
                assert!(tr.den_hinge_mask().is_zero());
            } else {
                assert!(matches!(m.exact_bigrat(), Err(CoreError::DivisionByZero(_))));
                assert!(matches!(m.to_trit_ratio(), Err(CoreError::DivisionByZero(_))));
            }
        }
        assert_eq!(defined, 8);
        assert_eq!(singular, 8);
        assert_eq!(hinges, 7);
        assert_eq!(saturated, 1);
    }

    #[test]
    fn test_trit_ratio_field_laws_and_metadata_preservation() {
        let pairs: [(i64, i64); 12] = [
            (0, 1),
            (1, 1),
            (-1, 1),
            (1, 2),
            (-2, 3),
            (5, 6),
            (7, 10),
            (3, 10),
            (-7, 12),
            (11, 15),
            (14, 27),
            (-25, 36),
        ];
        let trs: Vec<TritRatio> = pairs
            .iter()
            .map(|&(n, d)| TritRatio::from_i64_pair(n, d).unwrap())
            .collect();
        let brs: Vec<BigRat> = pairs
            .iter()
            .map(|&(n, d)| BigRat::from_i64_pair(n, d).unwrap())
            .collect();

        for (ra, fa) in trs.iter().zip(brs.iter()) {
            assert_eq!(TritRatio::from_bigrat(fa), *ra);
            assert_eq!(ra.to_bigrat(), *fa);
            assert_eq!((-ra).to_bigrat(), -fa);
            assert_eq!(ra.abs_ratio().to_bigrat(), fa.abs());
            assert_eq!(ra.den().sign(), 1);
            assert_eq!(ra.num().gcd(ra.den()), TritWord::one());
            if !fa.is_zero() {
                assert_eq!((ra * &ra.reciprocal().unwrap()), TritRatio::one());
            } else {
                assert!(matches!(ra.reciprocal(), Err(CoreError::DivisionByZero(_))));
            }
            for (rb, fb) in trs.iter().zip(brs.iter()) {
                assert_eq!((ra + rb).to_bigrat(), fa + fb);
                assert_eq!((ra - rb).to_bigrat(), fa - fb);
                assert_eq!((ra * rb).to_bigrat(), fa * fb);
                assert_eq!(ra.cmp(rb), fa.cmp(fb));
                if !fb.is_zero() {
                    assert_eq!(ra.checked_div(rb).unwrap().to_bigrat(), fa.checked_div(fb).unwrap());
                } else {
                    assert!(matches!(ra.checked_div(rb), Err(CoreError::DivisionByZero(_))));
                }
            }
        }

        // Hinge metadata preservation, value equality vs structural_eq, and reciprocal swap
        let w_num_hinge = TritWord::from_symbols("+H+", true).unwrap(); // +10, hinge at lane 1 (0b0100)
        let w_den_hinge = TritWord::from_symbols("H++", true).unwrap(); // +4, hinge at lane 2 (0b010000)
        let rh1 = TritRatio::new(w_num_hinge, w_den_hinge).unwrap();
        assert_eq!(rh1.canonical_pair(), ["5", "2"]);
        assert_eq!(rh1.num_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00));
        assert_eq!(rh1.den_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00_00));
        assert!(rh1.has_hinge());

        let clean = rh1.with_cleared_metadata();
        assert!(!clean.has_hinge());
        assert_eq!(rh1, clean);
        assert_eq!(hash_of(&rh1), hash_of(&clean));
        assert!(!rh1.structural_eq(&clean));
        assert!(rh1.structural_eq(&rh1));

        let rh_rec = rh1.reciprocal().unwrap();
        assert_eq!(rh_rec.canonical_pair(), ["2", "5"]);
        assert_eq!(rh_rec.num_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00_00));
        assert_eq!(rh_rec.den_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00));
        assert!(rh_rec.reciprocal().unwrap().structural_eq(&rh1));

        let rh2 = TritRatio::from_bigints_with_masks(
            &BigInt::from_i64(3),
            &BigInt::from_i64(4),
            LaneMask::from_u64(0b01).unwrap(),
            LaneMask::from_u64(0b01_00).unwrap(),
        )
        .unwrap();
        let rh_sum = &rh1 + &rh2;
        assert_eq!(rh_sum.canonical_pair(), ["13", "4"]);
        assert_eq!(rh_sum.num_hinge_mask().to_bigint(), BigInt::from_u64(0b01_01));
        assert_eq!(rh_sum.den_hinge_mask().to_bigint(), BigInt::from_u64(0b01_01_00));

        let rh_div = rh1.checked_div(&rh2).unwrap();
        assert_eq!(rh_div.canonical_pair(), ["10", "3"]);
        assert_eq!(rh_div.num_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00));
        assert_eq!(rh_div.den_hinge_mask().to_bigint(), BigInt::from_u64(0b01_00_01));

        // 230-digit TritRatio field check
        let big_ra = TritRatio::from_bigints(
            &(&BigInt::pow10(230) + &BigInt::from_i64(17)),
            &(&BigInt::pow10(229) + &BigInt::from_i64(13)),
        )
        .unwrap();
        let big_rb = TritRatio::from_bigints(
            &-&(&BigInt::pow10(228) + &BigInt::from_i64(19)),
            &(&BigInt::from_u32(3).pow_u32(40) * &(&BigInt::pow10(180) + &BigInt::from_i64(7))),
        )
        .unwrap();
        let big_fa = big_ra.to_bigrat();
        let big_fb = big_rb.to_bigrat();
        assert_eq!((&big_ra + &big_rb).to_bigrat(), &big_fa + &big_fb);
        assert_eq!((&big_ra * &big_rb).to_bigrat(), &big_fa * &big_fb);
        assert_eq!(
            big_ra.checked_div(&big_rb).unwrap().to_bigrat(),
            big_fa.checked_div(&big_fb).unwrap()
        );
    }
}
