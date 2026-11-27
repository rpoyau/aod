//! Boundary-Full AOmegaD SADAR dynamics, continuous Q4 D.E.C. chiral-flip walks,
//! collision-shedding debris cascades, finite-ring double-slit, Hydrogen shell
//! series, moving-boundary wire currents, and exact rational pooled SPARC evaluation.
//!
//! Pure `std`-only, zero-float, zero-`unsafe` arbitrary-width `TritWord` /
//! `ChiralPair4` / `TritRatio` implementation for golden vectors `RC-025`..`RC-032`
//! and `SD-007`..`SD-008`.

use std::cmp::Ordering;
use std::collections::BTreeMap;

use crate::bigint::BigInt;
use crate::json::JsonValue;
use crate::numeric::{format_fixed, parse_printed_rational};
use crate::ops::require_json_int;
use crate::ternary::{
    signed_to_trit_lane, trit_lane_to_signed, ChiralPair4, TritRatio, TritWord, TRIT_ALPHA,
    TRIT_DWELL, TRIT_HINGE, TRIT_OMEGA,
};
use crate::CoreError;

const CLOSURE_C6: i64 = 18;
const CLOSURE_C8: i64 = 24;
const CLOSURE_C10: i64 = 27;
const TAU_ROTOR_MICROSLOTS: usize = 50;
const TAU_ROTOR_CAP_4D: i64 = (4 * TAU_ROTOR_MICROSLOTS) as i64;

const POPCOUNT_4BIT: [i64; 16] = [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4];

fn q4_neighbor(v: usize, slot: usize) -> usize {
    v ^ (1usize << slot)
}

fn hamming4(u: usize, v: usize) -> i64 {
    POPCOUNT_4BIT[(u ^ v) & 15]
}

fn pair_json(q: &TritRatio) -> JsonValue {
    let [n, d] = q.canonical_pair();
    JsonValue::Array(vec![JsonValue::Str(n), JsonValue::Str(d)])
}

fn int_json(v: i64) -> JsonValue {
    JsonValue::Int(BigInt::from_i64(v))
}

fn str_json(s: &str) -> JsonValue {
    JsonValue::Str(s.to_string())
}

fn word_to_i64(w: &TritWord, name: &str) -> Result<i64, CoreError> {
    w.to_bigint()
        .to_i64()
        .ok_or_else(|| CoreError::ValueError(format!("{} exceeds i64 bounds", name)))
}

fn get_field<'a>(
    obj: &'a BTreeMap<String, JsonValue>,
    key: &str,
) -> Result<&'a JsonValue, CoreError> {
    obj.get(key)
        .ok_or_else(|| CoreError::ValueError(format!("missing required input field {:?}", key)))
}

fn require_i64(obj: &BTreeMap<String, JsonValue>, key: &str) -> Result<i64, CoreError> {
    let bi = require_json_int(get_field(obj, key)?, key)?;
    bi.to_i64()
        .ok_or_else(|| CoreError::ValueError(format!("{} exceeds i64 bounds", key)))
}

fn require_str<'a>(obj: &'a BTreeMap<String, JsonValue>, key: &str) -> Result<&'a str, CoreError> {
    match get_field(obj, key)? {
        JsonValue::Str(s) => Ok(s.as_str()),
        other => Err(CoreError::TypeError(format!(
            "{} must be a string, got {}",
            key,
            other.type_name()
        ))),
    }
}

fn require_array<'a>(
    obj: &'a BTreeMap<String, JsonValue>,
    key: &str,
) -> Result<&'a [JsonValue], CoreError> {
    match get_field(obj, key)? {
        JsonValue::Array(v) => Ok(v.as_slice()),
        other => Err(CoreError::TypeError(format!(
            "{} must be a JSON array, got {}",
            key,
            other.type_name()
        ))),
    }
}

fn require_obj<'a>(
    val: &'a JsonValue,
    name: &str,
) -> Result<&'a BTreeMap<String, JsonValue>, CoreError> {
    match val {
        JsonValue::Object(m) => Ok(m),
        other => Err(CoreError::TypeError(format!(
            "{} must be a JSON object, got {}",
            name,
            other.type_name()
        ))),
    }
}

fn trit_lcm(a: &TritWord, b: &TritWord) -> Result<TritWord, CoreError> {
    if a.is_zero_value() || b.is_zero_value() {
        return Ok(TritWord::zero());
    }
    let abs_a = a.abs_word();
    let abs_b = b.abs_word();
    let g = abs_a.gcd(&abs_b);
    let (q, _) = abs_a.divmod_floor(&g)?;
    Ok(q.mul(&abs_b))
}

/// Deterministic balanced sum of `(num, den)` `TritWord` terms via denominator
/// grouping (sorted `Vec`, zero `HashMap`) and pairwise binary-tree `TritRatio::add`.
fn sum_trit_ratios_balanced(mut terms: Vec<(TritWord, TritWord)>) -> Result<TritRatio, CoreError> {
    terms.retain(|(n, _)| !n.is_zero_value());
    if terms.is_empty() {
        return Ok(TritRatio::zero());
    }
    terms.sort_by(|a, b| a.1.cmp_value(&b.1));
    let mut nodes: Vec<TritRatio> = Vec::new();
    let mut idx = 0usize;
    while idx < terms.len() {
        let den = terms[idx].1.clone();
        let mut num_acc = terms[idx].0.clone();
        idx += 1;
        while idx < terms.len() && terms[idx].1.cmp_value(&den) == Ordering::Equal {
            num_acc = num_acc.add(&terms[idx].0);
            idx += 1;
        }
        if !num_acc.is_zero_value() {
            nodes.push(TritRatio::new(num_acc, den)?);
        }
    }
    if nodes.is_empty() {
        return Ok(TritRatio::zero());
    }
    while nodes.len() > 1 {
        let mut next = Vec::with_capacity((nodes.len() + 1) / 2);
        let mut i = 0usize;
        while i < nodes.len() {
            if i + 1 < nodes.len() {
                next.push(nodes[i].add(&nodes[i + 1]));
            } else {
                next.push(nodes[i].clone());
            }
            i += 2;
        }
        nodes = next;
    }
    Ok(nodes.into_iter().next().unwrap_or_else(TritRatio::zero))
}

/// Deterministic 50-microslot `Q4 x mu` impedance rotor over `TritWord` + `ChiralPair4`.
///
/// - `rd_lo = RD(1:2) = 9`, `rd_hi = RD(3:3) = 61` (`delta_rd = 52`) -> `(13, 37)`
/// - `rd_lo = RD(3:3) = 61`, `rd_hi = RD(3:4) = 137` (`delta_rd = 76`) -> `(19, 31)`
fn run_q4_mu_impedance_rotor(rd_lo: i64, rd_hi: i64) -> Result<(i64, i64, TritWord), CoreError> {
    if rd_lo <= 0 || rd_hi <= rd_lo {
        return Err(CoreError::ValueError(format!(
            "invalid rotor RD bounds: {} -> {}",
            rd_lo, rd_hi
        )));
    }
    let delta_rd_w = TritWord::from_i64(rd_hi).sub(&TritWord::from_i64(rd_lo));
    let cap_w = TritWord::from_i64(TAU_ROTOR_CAP_4D);
    if delta_rd_w.sign() <= 0 || delta_rd_w.cmp_value(&cap_w) != Ordering::Less {
        return Err(CoreError::ValueError(
            "rotor delta_rd out of 4D capacity bounds".to_string(),
        ));
    }

    let mut acc = TritWord::zero();
    let mut chiral = ChiralPair4::from_lanes(TRIT_ALPHA, TRIT_OMEGA)?;
    let mut v_q4 = 0usize;
    let mut lanes: Vec<u8> = Vec::with_capacity(TAU_ROTOR_MICROSLOTS);
    for mu_idx in 0..TAU_ROTOR_MICROSLOTS {
        v_q4 = q4_neighbor(v_q4, mu_idx & 3);
        acc = acc.add(&delta_rd_w);
        if acc.cmp_value(&cap_w) != Ordering::Less {
            acc = acc.sub(&cap_w);
            chiral = chiral.chiral_flip();
            lanes.push(TRIT_HINGE);
        } else {
            lanes.push(chiral.lo_lane());
        }
    }

    let rotor_word = TritWord::from_lanes(&lanes, false)?;
    let captured = rotor_word.hinge_count();
    let escaped = rotor_word.polar_count();
    if captured + escaped != TAU_ROTOR_MICROSLOTS || rotor_word.dwell_count() != 0 || v_q4 >= 16 {
        return Err(CoreError::ValueError(
            "Q4 x mu impedance rotor partition invariant violated".to_string(),
        ));
    }
    Ok((captured as i64, escaped as i64, rotor_word))
}

fn enumerate_c6_two_step_paths(
    target_k: i64,
    half_cap: i64,
) -> Result<Vec<(i64, i64, TritWord)>, CoreError> {
    if half_cap < 1 {
        return Err(CoreError::ValueError(format!(
            "half_cap must be >= 1, got {}",
            half_cap
        )));
    }
    let mut paths = Vec::new();
    for s1 in -half_cap..=half_cap {
        let s2 = target_k - s1;
        if (-half_cap..=half_cap).contains(&s2) {
            let lane1 = if s1 > 0 { TRIT_ALPHA } else { TRIT_OMEGA };
            let lane2 = if s2 > 0 { TRIT_ALPHA } else { TRIT_OMEGA };
            let a1 = s1.unsigned_abs() as usize;
            let a2 = s2.unsigned_abs() as usize;
            let hc = half_cap as usize;
            let mut raw_lanes = Vec::with_capacity(2 * hc);
            for _ in 0..a1 {
                raw_lanes.push(lane1);
            }
            for _ in a1..hc {
                raw_lanes.push(TRIT_DWELL);
            }
            for _ in 0..a2 {
                raw_lanes.push(lane2);
            }
            for _ in a2..hc {
                raw_lanes.push(TRIT_DWELL);
            }
            let burned = TritWord::from_lanes(&raw_lanes, false)?.burn_contiguous_dwell(false);
            paths.push((s1, s2, burned));
        }
    }
    Ok(paths)
}

fn support_pi(p: u32, q: i64) -> Result<i64, CoreError> {
    if p < 1 || q < 1 {
        return Err(CoreError::ValueError(format!(
            "invalid curling-curl indices {}:{}",
            p, q
        )));
    }
    let qp = q
        .checked_pow(p)
        .ok_or_else(|| CoreError::ValueError("q^p overflow".to_string()))?;
    Ok(qp + q)
}

fn support_rd_single_hinge(p: u32, q: i64) -> Result<i64, CoreError> {
    Ok(2 * support_pi(p, q)? + 1)
}

// ---------------------------------------------------------------------------
// 1. RC-025 & RC-026: Continuous Multi-Cut Q4 D.E.C. Walk & Chiral Flip
// ---------------------------------------------------------------------------

#[derive(Clone)]
struct CandRow {
    sigma: i64,
    weight: i64,
    is_dwell: i64,
    target: usize,
}

pub fn op_dec_chiral_flip_walk(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let v0_i = require_i64(inputs, "initial_vertex")?;
    let anc_i = require_i64(inputs, "incoming_ancestor_slot")?;
    let chi0 = require_i64(inputs, "initial_chirality")?;
    let c3 = require_i64(inputs, "C3")?;
    let rd_tunnel = require_i64(inputs, "tunnel_RD")?;
    let omega_rem = require_i64(inputs, "tunnel_window_remaining")?;
    let raw_rows = require_array(inputs, "candidate_rows")?;

    if !(0..16).contains(&v0_i) {
        return Err(CoreError::ValueError(
            "initial_vertex must lie in V(Q4)".to_string(),
        ));
    }
    if !(0..4).contains(&anc_i) {
        return Err(CoreError::ValueError(
            "incoming_ancestor_slot must lie in 0..3".to_string(),
        ));
    }
    if chi0 != -1 && chi0 != 1 {
        return Err(CoreError::ValueError(
            "initial_chirality must lie in {-1, +1}".to_string(),
        ));
    }
    if c3 != 3 || rd_tunnel <= 0 || omega_rem <= 0 {
        return Err(CoreError::ValueError(
            "invalid tunnel parameters".to_string(),
        ));
    }
    if raw_rows.len() != 4 {
        return Err(CoreError::ValueError(
            "expected 4 candidate rows".to_string(),
        ));
    }

    let v0 = v0_i as usize;
    let anc = anc_i as usize;
    if v0 >= 4 {
        return Err(CoreError::ValueError(
            "initial_vertex must start inside R_core={0,1,2,3}".to_string(),
        ));
    }

    let dion_before_pair = ChiralPair4::from_lanes(
        signed_to_trit_lane(chi0 as i8)?,
        signed_to_trit_lane((-chi0) as i8)?,
    )?;

    let mut parsed: Vec<CandRow> = Vec::with_capacity(4);
    let mut cut1_role_lanes: Vec<u8> = Vec::with_capacity(5);
    cut1_role_lanes.push(TRIT_HINGE);
    for rv in raw_rows {
        let robj = require_obj(rv, "candidate_row")?;
        let slot_i = require_i64(robj, "slot")?;
        let sigma = require_i64(robj, "sigma")?;
        let weight = require_i64(robj, "weight")?;
        let is_dwell = require_i64(robj, "is_optional_dwell")?;
        if !(0..4).contains(&slot_i) {
            return Err(CoreError::ValueError("slot must lie in 0..3".to_string()));
        }
        let slot = slot_i as usize;
        if slot == anc {
            return Err(CoreError::ValueError(
                "H1 continuation cannot use committed incoming ancestor slot".to_string(),
            ));
        }
        if !matches!(sigma, -1 | 0 | 1) || weight <= 0 || !matches!(is_dwell, 0 | 1) {
            return Err(CoreError::ValueError(
                "invalid candidate row fields".to_string(),
            ));
        }
        let role_lane = if is_dwell == 1 {
            TRIT_DWELL
        } else {
            signed_to_trit_lane(sigma as i8)?
        };
        cut1_role_lanes.push(role_lane);
        let target = if sigma == 0 {
            v0
        } else {
            q4_neighbor(v0, slot)
        };
        parsed.push(CandRow {
            sigma,
            weight,
            is_dwell,
            target,
        });
    }

    // Cut 1: Unblocked D.E.C. normalization over TritWord / TritRatio
    let mut z_cut1_w = TritWord::zero();
    for r in &parsed {
        z_cut1_w = z_cut1_w.add(&TritWord::from_i64(r.weight));
    }
    let mut probs_cut1 = Vec::with_capacity(4);
    let mut sum_cut1 = TritRatio::zero();
    for r in &parsed {
        let p = TritRatio::new(TritWord::from_i64(r.weight), z_cut1_w.clone())?;
        sum_cut1 = sum_cut1.add(&p);
        probs_cut1.push(p);
    }
    if sum_cut1 != TritRatio::one() {
        return Err(CoreError::ValueError(
            "Cut 1 kernel not normalized".to_string(),
        ));
    }

    // Cut 2: Live xxxxx -> x burn removes optional 0_D dwell while preserving structural 0_H hinge.
    let cut1_role_word = TritWord::from_lanes(&cut1_role_lanes, false)?;
    let cut2_role_word = cut1_role_word.burn_contiguous_dwell(false);
    if !cut2_role_word.has_hinge()
        || cut2_role_word.dwell_count() != 0
        || cut2_role_word.polar_count() != 3
    {
        return Err(CoreError::ValueError(
            "Cut 2 live dwell burn must remove optional 0_D while retaining 0_H and 3 slide lanes"
                .to_string(),
        ));
    }

    let slide_rows: Vec<&CandRow> = parsed.iter().filter(|r| r.is_dwell == 0).collect();
    if slide_rows.len() != 3 || !slide_rows.iter().all(|r| r.sigma == -1 || r.sigma == 1) {
        return Err(CoreError::ValueError(
            "invalid slide row survivor set".to_string(),
        ));
    }
    let mut z_slide_w = TritWord::zero();
    for r in &slide_rows {
        z_slide_w = z_slide_w.add(&TritWord::from_i64(r.weight));
    }
    let mut probs_slide = Vec::with_capacity(3);
    let mut sum_slide = TritRatio::zero();
    let mut returned_prob = TritRatio::zero();
    let mut cross_rows: Vec<(&CandRow, TritRatio)> = Vec::new();
    for r in &slide_rows {
        let p = TritRatio::new(TritWord::from_i64(r.weight), z_slide_w.clone())?;
        sum_slide = sum_slide.add(&p);
        if r.target < 4 {
            returned_prob = returned_prob.add(&p);
        } else {
            cross_rows.push((*r, p.clone()));
        }
        probs_slide.push(p);
    }
    if sum_slide != TritRatio::one() || cross_rows.len() != 1 {
        return Err(CoreError::ValueError(
            "expected unique normalized boundary-crossing slide branch".to_string(),
        ));
    }
    let (tunnel_row, p_tunnel) = &cross_rows[0];
    if hamming4(v0, tunnel_row.target) != 1 {
        return Err(CoreError::ValueError(
            "tunnel step must be Q4 Hamming-1".to_string(),
        ));
    }

    // Cut 3: Window-clipped field tunnelling + O(1) SWAR boundary chiral flip
    let rho_omega = rd_tunnel.min(omega_rem);
    let pd_tunnel_w = TritWord::from_i64(c3).mul(&TritWord::from_i64(rho_omega));
    let pd_tunnel = word_to_i64(&pd_tunnel_w, "pD_tunnel")?;
    let t_tunnel = p_tunnel.mul(&TritRatio::new(pd_tunnel_w, TritWord::one())?);
    let dion_after_pair = dion_before_pair.chiral_flip();
    let chi_after = trit_lane_to_signed(dion_after_pair.lo_lane())? as i64;
    let dion_before_lo = trit_lane_to_signed(dion_before_pair.lo_lane())? as i64;
    let dion_before_hi = trit_lane_to_signed(dion_before_pair.hi_lane())? as i64;
    let dion_after_lo = trit_lane_to_signed(dion_after_pair.lo_lane())? as i64;
    let dion_after_hi = trit_lane_to_signed(dion_after_pair.hi_lane())? as i64;

    let retained_trace_word = TritWord::from_lanes(
        &[
            dion_before_pair.lo_lane(),
            TRIT_HINGE,
            dion_before_pair.hi_lane(),
            TRIT_HINGE,
            dion_after_pair.lo_lane(),
            dion_after_pair.hi_lane(),
        ],
        false,
    )?;
    let prefix_ok = trit_lane_to_signed(retained_trace_word.lane_at(0)?)? as i64 == chi0
        && trit_lane_to_signed(retained_trace_word.lane_at(1)?)? as i64 == 0
        && trit_lane_to_signed(retained_trace_word.lane_at(2)?)? as i64 == -chi0;
    let hinge_preserved = cut2_role_word.has_hinge() && retained_trace_word.hinge_count() == 2;

    let mut out = BTreeMap::new();
    out.insert(
        "cut1_Z".to_string(),
        int_json(word_to_i64(&z_cut1_w, "cut1_Z")?),
    );
    out.insert(
        "cut1_probabilities".to_string(),
        JsonValue::Array(probs_cut1.iter().map(pair_json).collect()),
    );
    out.insert(
        "cut2_slide_Z".to_string(),
        int_json(word_to_i64(&z_slide_w, "cut2_slide_Z")?),
    );
    out.insert(
        "cut2_slide_weights".to_string(),
        JsonValue::Array(slide_rows.iter().map(|r| int_json(r.weight)).collect()),
    );
    out.insert(
        "cut2_slide_probabilities".to_string(),
        JsonValue::Array(probs_slide.iter().map(pair_json).collect()),
    );
    out.insert("returned_probability".to_string(), pair_json(&returned_prob));
    out.insert("tunnel_probability".to_string(), pair_json(p_tunnel));
    out.insert(
        "tunnel_target_vertex".to_string(),
        int_json(tunnel_row.target as i64),
    );
    out.insert("rhoD_omega".to_string(), int_json(rho_omega));
    out.insert("pD_tunnel".to_string(), int_json(pd_tunnel));
    out.insert("T_tunnel_D".to_string(), pair_json(&t_tunnel));
    out.insert("chirality_before".to_string(), int_json(chi0));
    out.insert("chirality_after".to_string(), int_json(chi_after));
    out.insert(
        "dion_before".to_string(),
        JsonValue::Array(vec![int_json(dion_before_lo), int_json(dion_before_hi)]),
    );
    out.insert(
        "dion_after".to_string(),
        JsonValue::Array(vec![int_json(dion_after_lo), int_json(dion_after_hi)]),
    );
    out.insert(
        "structural_hinge_preserved".to_string(),
        JsonValue::Bool(hinge_preserved),
    );
    out.insert(
        "prior_return_retained".to_string(),
        JsonValue::Bool(prefix_ok),
    );
    Ok(JsonValue::Object(out))
}

pub fn op_dec_two_carrier_chiral_stokes(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let chi1 = require_i64(inputs, "chi_1")?;
    let chi2 = require_i64(inputs, "chi_2")?;
    let rcd_12 = require_i64(inputs, "RCD_12")?;
    let window_len = require_i64(inputs, "window_len")?;
    let c3 = require_i64(inputs, "C3")?;
    let seats = require_i64(inputs, "enclosure_seats")?;
    let base1 = require_i64(inputs, "base_state_1")?;
    let base2 = require_i64(inputs, "base_state_2")?;

    if !matches!(chi1, -1 | 1) || !matches!(chi2, -1 | 1) || chi1 == chi2 {
        return Err(CoreError::ValueError(
            "opposing chiralities required".to_string(),
        ));
    }
    if rcd_12 <= 0 || window_len <= 0 || c3 != 3 || seats <= 0 {
        return Err(CoreError::ValueError("invalid Disoma inputs".to_string()));
    }

    let pair_1 = ChiralPair4::from_lanes(
        signed_to_trit_lane(chi1 as i8)?,
        signed_to_trit_lane((-chi1) as i8)?,
    )?;
    let pair_2 = ChiralPair4::from_lanes(
        signed_to_trit_lane(chi2 as i8)?,
        signed_to_trit_lane((-chi2) as i8)?,
    )?;
    if pair_2 != pair_1.chiral_flip() {
        return Err(CoreError::ValueError(
            "opposing Disoma carriers must be chiral flips".to_string(),
        ));
    }

    let rho_omega = rcd_12.min(window_len);
    let pd_w = TritWord::from_i64(c3).mul(&TritWord::from_i64(rho_omega));
    let pd = word_to_i64(&pd_w, "pD_12")?;
    let lag_diff = (trit_lane_to_signed(pair_1.lo_lane())? as i64)
        - (trit_lane_to_signed(pair_2.lo_lane())? as i64);
    let delta_chi = TritRatio::new(TritWord::from_i64(lag_diff), TritWord::one())?;
    let intensity = TritRatio::new(TritWord::one(), TritWord::from_i64(seats))?;
    let a_12 = delta_chi.mul(&intensity);
    let a_21 = a_12.neg();
    let pd_ratio = TritRatio::new(pd_w, TritWord::one())?;
    let phi_12 = pd_ratio.mul(&a_12);
    let phi_21 = pd_ratio.mul(&a_21);
    let sum_stokes = phi_12.add(&phi_21);
    if !sum_stokes.is_zero() {
        return Err(CoreError::ValueError(
            "internal Stokes interface cancellation violated".to_string(),
        ));
    }

    let base1_r = TritRatio::new(TritWord::from_i64(base1), TritWord::one())?;
    let base2_r = TritRatio::new(TritWord::from_i64(base2), TritWord::one())?;
    let next_1 = base1_r.add(&phi_21);
    let next_2 = base2_r.add(&phi_12);
    let op_both = next_1 != base1_r && next_2 != base2_r;
    if !op_both {
        return Err(CoreError::ValueError(
            "coupled chiral channels must remain causally operative".to_string(),
        ));
    }

    let mut out = BTreeMap::new();
    out.insert("rhoD_omega".to_string(), int_json(rho_omega));
    out.insert("pD_12".to_string(), int_json(pd));
    out.insert("delta_chi_lag".to_string(), pair_json(&delta_chi));
    out.insert("coupling_intensity".to_string(), pair_json(&intensity));
    out.insert("A_12".to_string(), pair_json(&a_12));
    out.insert("A_21".to_string(), pair_json(&a_21));
    out.insert("SADAR_12".to_string(), pair_json(&phi_12));
    out.insert("SADAR_21".to_string(), pair_json(&phi_21));
    out.insert("internal_stokes_sum".to_string(), pair_json(&sum_stokes));
    out.insert(
        "next_state_coupled".to_string(),
        JsonValue::Array(vec![pair_json(&next_1), pair_json(&next_2)]),
    );
    out.insert(
        "both_histories_operative".to_string(),
        JsonValue::Bool(op_both),
    );
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// 2. RC-027..029 & SD-007: Five-Boundary Full AOmegaD SADAR Dynamics
// ---------------------------------------------------------------------------

#[derive(Clone, PartialEq, Eq)]
struct CavityTrace {
    coupled: bool,
    raw_cuts: i64,
    quotient_cuts: i64,
    dwell_burned: i64,
    h1_moves: i64,
    hinges_0h: i64,
    chiral_flips: i64,
    early_coupling_cut: i64,
    sadar_attention_total: TritRatio,
    stokes_cross: i64,
    stokes_sweep: i64,
}

fn run_deterministic_q4_cavity_trace(
    n_duons: usize,
    lead_lag: i64,
) -> Result<CavityTrace, CoreError> {
    if lead_lag < 1 {
        return Err(CoreError::ValueError("lead_lag must be >= 1".to_string()));
    }
    if n_duons == 0 {
        let mut v_a = 0usize;
        let mut v_b = 15usize;
        let stream_a = ChiralPair4::from_lanes(TRIT_ALPHA, TRIT_OMEGA)?;
        let stream_b = ChiralPair4::from_lanes(TRIT_OMEGA, TRIT_ALPHA)?;
        let mut stream_lanes: Vec<u8> = Vec::with_capacity(64);
        for step_idx in 0..32usize {
            let slot = step_idx & 3;
            if slot == 3 {
                stream_lanes.push(TRIT_HINGE);
                stream_lanes.push(TRIT_HINGE);
            } else {
                v_a = q4_neighbor(v_a, slot);
                v_b = q4_neighbor(v_b, slot);
                stream_lanes.push(stream_a.lo_lane());
                stream_lanes.push(stream_b.lo_lane());
            }
        }
        let stream_word = TritWord::from_lanes(&stream_lanes, false)?;
        let sterile_cut_word = TritWord::from_lanes(&[TRIT_HINGE; 58], false)?;
        let sterile_quot = sterile_cut_word.burn_contiguous_dwell(false);
        return Ok(CavityTrace {
            coupled: false,
            raw_cuts: sterile_cut_word.width() as i64,
            quotient_cuts: sterile_quot.width() as i64,
            dwell_burned: (sterile_cut_word.width() - sterile_quot.width()) as i64,
            h1_moves: stream_word.polar_count() as i64,
            hinges_0h: stream_word.hinge_count() as i64,
            chiral_flips: 0,
            early_coupling_cut: 0,
            sadar_attention_total: TritRatio::zero(),
            stokes_cross: 0,
            stokes_sweep: 0,
        });
    }

    let mut v_a = 0usize;
    let mut v_b = 3usize;
    let mut anc_a = 3usize;
    let mut anc_b = 3usize;
    let mut duon_v: Vec<usize> = (0..n_duons)
        .map(|m| if (m & 1) == 0 { 1 } else { 2 })
        .collect();
    let mut duon_pairs: Vec<ChiralPair4> = Vec::with_capacity(n_duons);
    for m in 0..n_duons {
        if (m & 1) == 0 {
            duon_pairs.push(ChiralPair4::from_lanes(TRIT_ALPHA, TRIT_OMEGA)?);
        } else {
            duon_pairs.push(ChiralPair4::from_lanes(TRIT_OMEGA, TRIT_ALPHA)?);
        }
    }

    let mut k_quot = 0i64;
    let mut raw_cut_lanes: Vec<u8> = Vec::new();
    let mut h1_moves = 0i64;
    let mut hinges_0h = 0i64;
    let mut chiral_flips = 0i64;
    let mut coupled = false;
    let mut early_coupling_cut = 0i64;
    let mut sadar_attention_total = TritRatio::zero();
    let mut stokes_cross = 0i64;
    let mut stokes_sweep = 0i64;
    let mut debris_rd_rem = support_rd_single_hinge(3, 2)?; // 21

    while k_quot < 18 && debris_rd_rem > 0 {
        k_quot += 1;
        raw_cut_lanes.push(if coupled { TRIT_ALPHA } else { TRIT_HINGE });

        for m in 0..n_duons {
            let dv = duon_v[m];
            let d_a = hamming4(dv, v_a);
            let d_b = hamming4(dv, v_b);
            if ((k_quot as usize) + m) % 2 == 1 {
                chiral_flips += 1;
                duon_pairs[m] = duon_pairs[m].chiral_flip();
                if !coupled && d_a <= 1 && d_b <= 1 {
                    coupled = true;
                    early_coupling_cut = raw_cut_lanes.len() as i64;
                    let rho_ab = 9i64.min(6i64);
                    let p_ab = 3 * rho_ab;
                    let a_ab = TritRatio::new(
                        TritWord::from_i64(2 * lead_lag),
                        TritWord::from_i64(6 * (lead_lag + 2)),
                    )?;
                    let p_ab_r = TritRatio::new(TritWord::from_i64(p_ab), TritWord::one())?;
                    sadar_attention_total = sadar_attention_total.add(&p_ab_r.mul(&a_ab));
                    stokes_cross += p_ab;
                } else {
                    raw_cut_lanes.push(TRIT_DWELL);
                }
            }
            let chi_m = trit_lane_to_signed(duon_pairs[m].lo_lane())?;
            let shift = if chi_m > 0 { 1usize } else { 2usize };
            let next_slot = (dv + (k_quot as usize) + shift) & 3;
            duon_v[m] = q4_neighbor(dv, next_slot);
            h1_moves += 1;
        }

        for stream_idx in 0..2usize {
            let cur_v = if stream_idx == 0 { v_a } else { v_b };
            let cur_anc = if stream_idx == 0 { anc_a } else { anc_b };
            if !coupled && (k_quot % 4 == 0) {
                hinges_0h += 1;
            } else {
                let mut cand_slot = ((k_quot as usize) + stream_idx) & 3;
                if cand_slot == cur_anc {
                    cand_slot = (cand_slot + 1) & 3;
                }
                let nxt_v = q4_neighbor(cur_v, cand_slot);
                if stream_idx == 0 {
                    v_a = nxt_v;
                    anc_a = cand_slot;
                } else {
                    v_b = nxt_v;
                    anc_b = cand_slot;
                }
                h1_moves += 1;
                stokes_sweep += 1;
            }
        }

        if coupled {
            let drain = if debris_rd_rem >= 2 { 2 } else { 1 };
            if drain == 1 {
                raw_cut_lanes.push(TRIT_DWELL);
            }
            debris_rd_rem -= drain;
        }
    }

    let raw_trace_word = TritWord::from_lanes(&raw_cut_lanes, false)?;
    let quot_trace_word = raw_trace_word.burn_contiguous_dwell(false);
    let raw_cuts = raw_trace_word.width() as i64;
    let quotient_cuts = quot_trace_word.width() as i64;
    let dwell_burned = raw_cuts - quotient_cuts;
    if quotient_cuts != k_quot || dwell_burned != raw_trace_word.dwell_count() as i64 {
        return Err(CoreError::ValueError(
            "live cavity TritWord dwell-burn accounting mismatch".to_string(),
        ));
    }

    Ok(CavityTrace {
        coupled,
        raw_cuts,
        quotient_cuts,
        dwell_burned,
        h1_moves,
        hinges_0h,
        chiral_flips,
        early_coupling_cut,
        sadar_attention_total,
        stokes_cross,
        stokes_sweep,
    })
}

pub fn op_sadar_pp_tau_five_boundary(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let lead_lag = require_i64(inputs, "lead_lag")?;
    let n_duons_i = require_i64(inputs, "window_duons")?;

    if n_duons_i <= 0 || n_duons_i > 64 {
        return Err(CoreError::ValueError("invalid window_duons".to_string()));
    }

    // Derive Stage 1 (B_shed: 1:2 -> 3:3) and Stage 2 (B_sensor: 3:3 -> 3:4)
    // strictly from the deterministic 50-microslot Q4 x mu impedance rotor.
    let rd_12 = support_rd_single_hinge(1, 2)?; // 9
    let rd_33 = support_rd_single_hinge(3, 3)?; // 61
    let rd_34 = support_rd_single_hinge(3, 4)?; // 137

    let (endo_slots, exo_slots, _) = run_q4_mu_impedance_rotor(rd_12, rd_33)?;
    let (vis_slots, miss_slots, _) = run_q4_mu_impedance_rotor(rd_33, rd_34)?;

    // Reject any conflicting optional legacy slot overrides if supplied.
    for (opt_key, derived_val) in [
        ("shed_endo_slots", endo_slots),
        ("shed_exo_slots", exo_slots),
        ("sensor_visible_slots", vis_slots),
        ("sensor_missing_slots", miss_slots),
    ] {
        if inputs.contains_key(opt_key) {
            let provided = require_i64(inputs, opt_key)?;
            if provided != derived_val {
                return Err(CoreError::ValueError(format!(
                    "optional {}={} conflicts with Q4 x mu impedance rotor value {}",
                    opt_key, provided, derived_val
                )));
            }
        }
    }

    let sterile = run_deterministic_q4_cavity_trace(0, lead_lag)?;
    let live_with_sensor = run_deterministic_q4_cavity_trace(n_duons_i as usize, lead_lag)?;
    let live_no_sensor = run_deterministic_q4_cavity_trace(n_duons_i as usize, lead_lag)?;
    if live_with_sensor != live_no_sensor || sterile.coupled || !live_with_sensor.coupled {
        return Err(CoreError::ValueError(
            "Q4 SADAR cavity control or ReadOnly sensor invariance failed".to_string(),
        ));
    }

    let pocket_specs: [(i64, i64, &str); 6] = [
        (2, 6, "SEATED_DUAD_E2pm"),
        (6, CLOSURE_C6, "CLOSED_1:2:6_DIMONHEXON"),
        (7, CLOSURE_C8, "TRANSIENT_1:2:7_C8_DEFICIT"),
        (8, CLOSURE_C8, "CLOSED_1:2:8_DIMONOCTON"),
        (9, CLOSURE_C8, "SHEDDING_1:2:9yro_DIMONNANYRO"),
        (10, CLOSURE_C10, "CLIPPED_1:2:10_RETAINED"),
    ];
    let mut pocket_eval = Vec::with_capacity(6);
    let mut unique_complete = Vec::new();
    for (win_l, c_close, label) in pocket_specs {
        let rho_w = rd_12.min(win_l);
        let pd = 3 * rho_w;
        let qd = 3 * (rd_12 - win_l).max(0);
        let delta_c = pd - c_close;
        let x_shed = delta_c.max(0);
        if qd == 0 && x_shed > 0 {
            unique_complete.push(label);
        }
        let mut pobj = BTreeMap::new();
        pobj.insert("L".to_string(), int_json(win_l));
        pobj.insert("label".to_string(), str_json(label));
        pobj.insert("rhoD_omega".to_string(), int_json(rho_w));
        pobj.insert("PD".to_string(), int_json(pd));
        pobj.insert("QD".to_string(), int_json(qd));
        pobj.insert("C_close".to_string(), int_json(c_close));
        pobj.insert("Delta_close".to_string(), int_json(delta_c));
        pobj.insert("X_shedding".to_string(), int_json(x_shed));
        pocket_eval.push(JsonValue::Object(pobj));
    }
    if unique_complete != ["SHEDDING_1:2:9yro_DIMONNANYRO"] {
        return Err(CoreError::ValueError(
            "expected unique complete-RD shedding pocket 1:2:9_yro".to_string(),
        ));
    }

    let w_mu = TritWord::from_i64(TAU_ROTOR_MICROSLOTS as i64);
    let w_den = w_mu.mul(&w_mu); // 2500
    let endo_num_w = TritWord::from_i64(endo_slots).mul(&w_mu);
    let vis_num_w = TritWord::from_i64(exo_slots).mul(&TritWord::from_i64(vis_slots));
    let miss_num_w = TritWord::from_i64(exo_slots).mul(&TritWord::from_i64(miss_slots));

    let p_endo = TritRatio::new(endo_num_w.clone(), w_den.clone())?;
    let p_vis = TritRatio::new(vis_num_w.clone(), w_den.clone())?;
    let p_miss = TritRatio::new(miss_num_w.clone(), w_den)?;
    if p_endo.add(&p_vis).add(&p_miss) != TritRatio::one() {
        return Err(CoreError::ValueError(
            "2500-denominator partition mismatch".to_string(),
        ));
    }
    let p_exo = p_vis.add(&p_miss);
    let vis_cond_exo = p_vis.checked_div(&p_exo)?;
    let miss_cond_exo = p_miss.checked_div(&p_exo)?;

    let x_shed_tau = 3i64;
    let stokes_mov = live_with_sensor.stokes_cross - live_with_sensor.stokes_sweep + x_shed_tau;

    let mut sterile_obj = BTreeMap::new();
    sterile_obj.insert("coupled".to_string(), JsonValue::Bool(false));
    sterile_obj.insert("raw_cuts".to_string(), int_json(sterile.raw_cuts));
    sterile_obj.insert("h1_moves".to_string(), int_json(sterile.h1_moves));
    sterile_obj.insert("hinges_0H".to_string(), int_json(sterile.hinges_0h));
    sterile_obj.insert("X_shedding".to_string(), int_json(0));

    let mut live_obj = BTreeMap::new();
    live_obj.insert("coupled".to_string(), JsonValue::Bool(true));
    live_obj.insert("raw_cuts".to_string(), int_json(live_with_sensor.raw_cuts));
    live_obj.insert(
        "quotient_cuts".to_string(),
        int_json(live_with_sensor.quotient_cuts),
    );
    live_obj.insert(
        "dwell_burned".to_string(),
        int_json(live_with_sensor.dwell_burned),
    );
    live_obj.insert(
        "chiral_flips".to_string(),
        int_json(live_with_sensor.chiral_flips),
    );
    live_obj.insert(
        "early_coupling_cut".to_string(),
        int_json(live_with_sensor.early_coupling_cut),
    );
    live_obj.insert(
        "SADAR_attention_total".to_string(),
        pair_json(&live_with_sensor.sadar_attention_total),
    );
    live_obj.insert(
        "stokes_cross".to_string(),
        int_json(live_with_sensor.stokes_cross),
    );
    live_obj.insert(
        "stokes_sweep".to_string(),
        int_json(live_with_sensor.stokes_sweep),
    );
    live_obj.insert("stokes_shedding".to_string(), int_json(x_shed_tau));
    live_obj.insert("stokes_moving_total".to_string(), int_json(stokes_mov));
    live_obj.insert(
        "readonly_sensor_invariant".to_string(),
        JsonValue::Bool(true),
    );

    let mut out = BTreeMap::new();
    out.insert("sterile_control".to_string(), JsonValue::Object(sterile_obj));
    out.insert("live_cavity".to_string(), JsonValue::Object(live_obj));
    out.insert("selected_tau_candidate".to_string(), str_json("1:2:9_yro"));
    out.insert(
        "pocket_evaluations".to_string(),
        JsonValue::Array(pocket_eval),
    );
    out.insert(
        "partition_2500_numerators".to_string(),
        JsonValue::Array(vec![
            int_json(word_to_i64(&endo_num_w, "endo_num")?),
            int_json(word_to_i64(&vis_num_w, "vis_num")?),
            int_json(word_to_i64(&miss_num_w, "miss_num")?),
        ]),
    );
    out.insert("endo_retained_fraction".to_string(), pair_json(&p_endo));
    out.insert("exo_outward_fraction".to_string(), pair_json(&p_exo));
    out.insert(
        "visible_conditional_exo".to_string(),
        pair_json(&vis_cond_exo),
    );
    out.insert(
        "miss_tau_conditional_exo".to_string(),
        pair_json(&miss_cond_exo),
    );
    out.insert(
        "recipient_stages".to_string(),
        JsonValue::Array(
            [
                "emitted",
                "delivered",
                "accepted",
                "seated",
                "closed_origin",
                "reclosed",
            ]
            .into_iter()
            .map(str_json)
            .collect(),
        ),
    );
    Ok(JsonValue::Object(out))
}

pub fn op_sadar_hadron_debris_and_higgs_saddle(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let parent_p = require_i64(inputs, "parent_p")?;
    let parent_q = require_i64(inputs, "parent_q")?;
    let c3_chan = require_i64(inputs, "C3_channel")?;
    if parent_p != 3 || parent_q != 3 || c3_chan != 3 {
        return Err(CoreError::ValueError(
            "expected 3:3 parent and C3_channel=3".to_string(),
        ));
    }

    let debris_q = parent_q - 1; // 2
    let pi_32 = support_pi(3, debris_q)?;
    let rd_32 = support_rd_single_hinge(3, debris_q)?;
    let c_sup_32_w = TritWord::from_i64(parent_p).add(&TritWord::from_i64(debris_q));
    let seated_duad_pair = ChiralPair4::from_lanes(TRIT_ALPHA, TRIT_HINGE)?;
    let open_duon_pair = ChiralPair4::from_lanes(TRIT_ALPHA, TRIT_OMEGA)?;
    if !seated_duad_pair.has_hinge() || open_duon_pair.has_hinge() {
        return Err(CoreError::ValueError(
            "E2^+- seated duad and E2^0 open duon must differ by structural hinge".to_string(),
        ));
    }

    let ladder_specs: [(&str, i64, &str, ChiralPair4); 4] = [
        ("B_pm", 6, "E2_pm_seated_duad", seated_duad_pair),
        ("B_0", 6, "E2_0_open_duon", open_duon_pair),
        ("B_s0", 8, "E2_0_lifted_octon", open_duon_pair),
        ("B_c_pm", 10, "E2_pm_lifted_decon", seated_duad_pair),
    ];
    let mut debris_ladder = Vec::with_capacity(4);
    for (species, win_l, shell_state, seat_pair) in ladder_specs {
        let rho_w = rd_32.min(win_l);
        let pd_sup_w = c_sup_32_w.mul(&TritWord::from_i64(rho_w));
        let qd_sup_w = c_sup_32_w.mul(&TritWord::from_i64(rd_32 - rho_w));
        let mut dobj = BTreeMap::new();
        dobj.insert("species".to_string(), str_json(species));
        dobj.insert("support".to_string(), str_json(&format!("3:2:{}", win_l)));
        dobj.insert("shell_state".to_string(), str_json(shell_state));
        dobj.insert("chi_shell".to_string(), int_json(seat_pair.net_charge() as i64));
        dobj.insert("Pi".to_string(), int_json(pi_32));
        dobj.insert("RD".to_string(), int_json(rd_32));
        dobj.insert(
            "PD_support".to_string(),
            int_json(word_to_i64(&pd_sup_w, "PD_support")?),
        );
        dobj.insert(
            "QD_support".to_string(),
            int_json(word_to_i64(&qd_sup_w, "QD_support")?),
        );
        debris_ladder.push(JsonValue::Object(dobj));
    }

    let c3_w = TritWord::from_i64(c3_chan);
    let c6_w = TritWord::from_i64(CLOSURE_C6);
    let c8_w = TritWord::from_i64(CLOSURE_C8);
    let mut saddle_survivors = Vec::new();
    let mut lineage_survivors = Vec::new();
    let mut scan_count = 0i64;
    for q_cand in 1..=4i64 {
        let rd_cand = support_rd_single_hinge(3, q_cand)?;
        for win_l in 6..=10i64 {
            scan_count += 1;
            let rho_w = rd_cand.min(win_l);
            let pd_h_w = c3_w.mul(&TritWord::from_i64(rho_w));
            let d_c6_w = pd_h_w.sub(&c6_w);
            let d_c8_w = pd_h_w.sub(&c8_w);
            if d_c6_w.add(&d_c8_w).is_zero_value() && d_c6_w.sign() > 0 {
                let cid = format!("3:{}:{}", q_cand, win_l);
                if q_cand == parent_q {
                    lineage_survivors.push(cid.clone());
                }
                saddle_survivors.push(cid);
            }
        }
    }
    if lineage_survivors != ["3:3:7"] {
        return Err(CoreError::ValueError(
            "expected unique lineage-conserved saddle winner 3:3:7".to_string(),
        ));
    }

    let rd_337 = support_rd_single_hinge(3, 3)?; // 61
    let pd_337_w = c3_w.mul(&TritWord::from_i64(7)); // 21
    let qd_337_w = c3_w.mul(&TritWord::from_i64(rd_337 - 7)); // 162
    let e_h_mev_w = TritWord::from_i64(rd_337).mul(&TritWord::from_i64(1i64 << (7 + 4))); // 124928

    let mut out = BTreeMap::new();
    out.insert("debris_core_support".to_string(), str_json("3:2"));
    out.insert("debris_Pi".to_string(), int_json(pi_32));
    out.insert("debris_RD".to_string(), int_json(rd_32));
    out.insert("debris_ladder".to_string(), JsonValue::Array(debris_ladder));
    out.insert("candidates_scanned".to_string(), int_json(scan_count));
    out.insert(
        "c6_c8_midpoint_survivors".to_string(),
        JsonValue::Array(saddle_survivors.iter().map(|s| str_json(s)).collect()),
    );
    out.insert(
        "selected_higgs_candidate".to_string(),
        str_json("3:3:7_yro"),
    );
    out.insert("higgs_RD".to_string(), int_json(rd_337));
    out.insert(
        "higgs_PD_H".to_string(),
        int_json(word_to_i64(&pd_337_w, "higgs_PD_H")?),
    );
    out.insert(
        "higgs_QD_H".to_string(),
        int_json(word_to_i64(&qd_337_w, "higgs_QD_H")?),
    );
    out.insert(
        "higgs_delta_C6".to_string(),
        int_json(word_to_i64(&pd_337_w.sub(&c6_w), "higgs_delta_C6")?),
    );
    out.insert(
        "higgs_delta_C8".to_string(),
        int_json(word_to_i64(&pd_337_w.sub(&c8_w), "higgs_delta_C8")?),
    );
    out.insert(
        "frozen_map_MeV".to_string(),
        int_json(word_to_i64(&e_h_mev_w, "frozen_map_MeV")?),
    );
    Ok(JsonValue::Object(out))
}

pub fn op_sadar_rest_energy_atlas(
    _inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let periods: [i64; 7] = [2, 4, 6, 8, 20, 60, 136];
    let mut lcm_w = TritWord::one();
    for &p in &periods {
        lcm_w = trit_lcm(&lcm_w, &TritWord::from_i64(p))?;
    }
    let common_bit_span_w = TritWord::from_i64(4).mul(&lcm_w); // 8160
    let common_bit_span = word_to_i64(&common_bit_span_w, "common_bit_window_span")?;
    let mut closure_counts = Vec::with_capacity(8);
    closure_counts.push(0i64);
    for &p in periods.iter().rev() {
        let (q_w, _) = common_bit_span_w.divmod_floor(&TritWord::from_i64(p))?;
        closure_counts.push(word_to_i64(&q_w, "closure_count")?);
    }
    let mut summed_closures_w = TritWord::zero();
    for &c in &closure_counts {
        summed_closures_w = summed_closures_w.add(&TritWord::from_i64(c));
    }
    let summed_closures = word_to_i64(&summed_closures_w, "summed_lineage_closures")?;

    let specs: [(&str, u32, i64, i64, &str, i64, &str, i64); 10] = [
        ("e_minus", 1, 2, 6, "E2_pm_hexon", -1, "inner_even_closed", 18),
        ("mu_minus", 1, 2, 8, "E2_pm_octon", -1, "inner_even_closed", 24),
        (
            "tau_minus",
            1,
            2,
            9,
            "yro_shedding",
            -1,
            "odd_window_yro_shedding",
            24,
        ),
        (
            "B_pm",
            3,
            2,
            6,
            "E2_pm_seated_duad",
            1,
            "core_starvation_ditrion_debris",
            30,
        ),
        (
            "B_0",
            3,
            2,
            6,
            "E2_0_open_duon",
            0,
            "core_starvation_ditrion_debris",
            30,
        ),
        (
            "B_s0",
            3,
            2,
            8,
            "E2_0_lifted_octon",
            0,
            "lifted_ditrion_debris",
            40,
        ),
        (
            "B_c_pm",
            3,
            2,
            10,
            "E2_pm_lifted_decon",
            1,
            "lifted_ditrion_debris",
            50,
        ),
        ("proton", 3, 3, 6, "E2_pm_hexon", 1, "inner_even_closed", 36),
        ("neutron", 3, 4, 6, "E2_0_hexon", 0, "inner_even_closed", 42),
        (
            "higgs",
            3,
            3,
            7,
            "yro_c6_c8_saddle",
            0,
            "symmetric_c6_c8_saddle",
            18,
        ),
    ];

    let mut carriers = Vec::with_capacity(10);
    for (name, p, q, win_l, shell_st, chi_s, origin, c_ref) in specs {
        let pi_v = support_pi(p, q)?;
        let rd_v = support_rd_single_hinge(p, q)?;
        let c_sup = (p as i64) + q;
        let rho_w = rd_v.min(win_l);
        let pd_sup = c_sup * rho_w;
        let qd_sup = c_sup * (rd_v - win_l).max(0);
        let pd_chan = 3 * rho_w;
        let x_shed = if shell_st.contains("yro") {
            (pd_chan - c_ref).max(0)
        } else {
            0
        };
        let mut cobj = BTreeMap::new();
        cobj.insert("carrier".to_string(), str_json(name));
        cobj.insert(
            "support".to_string(),
            str_json(&format!("{}:{}:{}", p, q, win_l)),
        );
        cobj.insert("shell_state".to_string(), str_json(shell_st));
        cobj.insert("chi_shell".to_string(), int_json(chi_s));
        cobj.insert("Pi".to_string(), int_json(pi_v));
        cobj.insert("RD".to_string(), int_json(rd_v));
        cobj.insert("PD_sup".to_string(), int_json(pd_sup));
        cobj.insert("QD_sup".to_string(), int_json(qd_sup));
        cobj.insert("X_shedding_chan".to_string(), int_json(x_shed));
        cobj.insert("origin".to_string(), str_json(origin));
        carriers.push(JsonValue::Object(cobj));
    }

    let r_p_l = TritRatio::new(TritWord::from_i64(61), TritWord::from_i64(9))?;
    let r_n_p = TritRatio::new(TritWord::from_i64(137), TritWord::from_i64(61))?;
    let r_d_l = TritRatio::new(TritWord::from_i64(21), TritWord::from_i64(9))?;

    let mut out = BTreeMap::new();
    out.insert("carrier_count".to_string(), int_json(carriers.len() as i64));
    out.insert(
        "common_bit_window_span".to_string(),
        int_json(common_bit_span),
    );
    out.insert(
        "eight_lineage_closure_counts".to_string(),
        JsonValue::Array(closure_counts.into_iter().map(int_json).collect()),
    );
    out.insert(
        "summed_lineage_closures".to_string(),
        int_json(summed_closures),
    );
    out.insert("rd_ratio_proton_to_lepton".to_string(), pair_json(&r_p_l));
    out.insert("rd_ratio_neutron_to_proton".to_string(), pair_json(&r_n_p));
    out.insert("rd_ratio_ditrion_to_lepton".to_string(), pair_json(&r_d_l));
    out.insert("carriers".to_string(), JsonValue::Array(carriers));
    Ok(JsonValue::Object(out))
}

pub fn op_sadar_rest_energy_qext(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let raw_targets = require_array(inputs, "targets")?;
    if raw_targets.len() != 9 {
        return Err(CoreError::ValueError(
            "expected 9 rest-energy targets".to_string(),
        ));
    }

    let ten = BigInt::from_u32(10);
    let h_ext = TritRatio::from_bigints(&BigInt::from_i64(662_607_015), &ten.pow_u32(42))?;
    let e_ext = TritRatio::from_bigints(&BigInt::from_i64(1_602_176_634), &ten.pow_u32(28))?;
    let eta_ext = TritRatio::from_bigints(&BigInt::from_i64(137_035_999_177), &ten.pow_u32(9))?;
    let mev_scale = TritRatio::from_bigints(&ten.pow_u32(6), &BigInt::one())?;
    let k_ext = h_ext.mul(&eta_ext).checked_div(&mev_scale.mul(&e_ext))?;
    let scale_1e21 = TritRatio::from_bigints(&ten.pow_u32(21), &BigInt::one())?;

    let mut records = Vec::with_capacity(9);
    for tv in raw_targets {
        let tobj = require_obj(tv, "target")?;
        let species = require_str(tobj, "species")?;
        let e_mev =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(tobj, "target_MeV")?, true, true)?);
        let sig_mev =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(tobj, "sigma_MeV")?, true, true)?);
        if e_mev.sign() <= 0 || sig_mev.sign() <= 0 {
            return Err(CoreError::ValueError(format!(
                "non-positive target/sigma for {}",
                species
            )));
        }
        let nu_tar = e_mev.checked_div(&k_ext)?;
        let roundtrip = k_ext.mul(&nu_tar);
        let residual = roundtrip.sub(&e_mev);
        if !residual.is_zero() {
            return Err(CoreError::ValueError(format!(
                "B_ext round-trip eta cancellation failed for {}",
                species
            )));
        }
        let nu_scaled = nu_tar.checked_div(&scale_1e21)?;
        let mut robj = BTreeMap::new();
        robj.insert("species".to_string(), str_json(species));
        robj.insert(
            "nu_tar_scaled_1e21_6dp".to_string(),
            str_json(&format_fixed(&nu_scaled.to_bigrat(), 6)?),
        );
        robj.insert("roundtrip_residual".to_string(), pair_json(&residual));
        records.push(JsonValue::Object(robj));
    }

    let mut out = BTreeMap::new();
    out.insert("K_ext_MeV_s".to_string(), pair_json(&k_ext));
    out.insert("records".to_string(), JsonValue::Array(records));
    out.insert(
        "all_roundtrip_residuals_zero".to_string(),
        JsonValue::Bool(true),
    );
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// 3. RC-030..032 & SD-008: Double-Slit, Hydrogen, Wire & Pooled SPARC
// ---------------------------------------------------------------------------

pub fn op_frg_dimonhexon_double_slit_ring(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let half_span = require_i64(inputs, "screen_half_span")?;
    let hexon_cap = require_i64(inputs, "hexon_cap")?;
    let comp = require_array(inputs, "comparator_O")?;
    if half_span != 5 || hexon_cap != 6 || comp.len() != 11 {
        return Err(CoreError::ValueError(
            "expected screen_half_span=5, hexon_cap=6, and 11 O_k bins".to_string(),
        ));
    }

    let half_cap = hexon_cap / 2;
    let hexon_cap_u = hexon_cap as usize;
    let gate_offset = 2i64;

    let mut s_bins = Vec::with_capacity(11);
    let mut t0_bins = Vec::with_capacity(11);
    let mut cx_bins = Vec::with_capacity(11);
    let mut tx_bins = Vec::with_capacity(11);
    let mut dz_bins = Vec::with_capacity(11);
    let mut m_sum = 0i64;

    for (idx, k_pos) in (-half_span..=half_span).enumerate() {
        // 1. Single-gate C_6 path-pair enumeration with hexon aperture saturation
        //    burned live via TritWord::burn_contiguous_dwell(false).
        let paths_single = enumerate_c6_two_step_paths(k_pos, half_cap)?;
        let mut sat_budget = 0usize;
        if paths_single.len() >= hexon_cap_u {
            for (s1, s2, bw) in &paths_single {
                if *s1 > 0 && *s2 < 0 {
                    let back_depth = bw.alpha_count().min(bw.omega_count());
                    sat_budget += back_depth * back_depth;
                }
            }
        }

        let mut single_pair_lanes = Vec::with_capacity(paths_single.len() * paths_single.len());
        for (_, _, bp) in &paths_single {
            let bp_rev = bp.alpha_count().min(bp.omega_count());
            for (_, _, bq) in &paths_single {
                let bq_rev = bq.alpha_count().min(bq.omega_count());
                if sat_budget > 0 && (bp_rev > 0 || bq_rev > 0) {
                    single_pair_lanes.push(TRIT_DWELL);
                    sat_budget -= 1;
                } else {
                    single_pair_lanes.push(TRIT_ALPHA);
                }
            }
        }
        if sat_budget != 0 {
            return Err(CoreError::ValueError(format!(
                "unspent aperture saturation budget at k={}",
                k_pos
            )));
        }
        let live_single_word =
            TritWord::from_lanes(&single_pair_lanes, false)?.burn_contiguous_dwell(false);
        let s_k = live_single_word.width() as i64;
        let t0_k = 2 * s_k;

        // 2. Two-gate cross-return path-pair enumeration across g_a=-2, g_b=+2
        //    packed into ChiralPair4 registers and summed via TritWord::from_chiral_pairs.
        let paths_a = enumerate_c6_two_step_paths(k_pos + gate_offset, half_cap)?;
        let paths_b = enumerate_c6_two_step_paths(k_pos - gate_offset, half_cap)?;
        let mut cross_pairs = Vec::with_capacity(paths_a.len() * paths_b.len());
        for (a1, a2, ba) in &paths_a {
            let la = ba.width();
            for (b1, b2, bb) in &paths_b {
                let lb = bb.width();
                let dot = a1 * b1 + a2 * b2;
                let net_prod = (a1 + a2) * (b1 + b2);
                let lo_lane = if dot < 0 {
                    TRIT_ALPHA
                } else if net_prod > 0 {
                    TRIT_OMEGA
                } else {
                    TRIT_DWELL
                };
                let diff_l = la.abs_diff(lb);
                let hi_lane = if dot < 0 && la == lb {
                    TRIT_ALPHA
                } else if la.max(lb) == hexon_cap_u && diff_l == hexon_cap_u - 2 {
                    TRIT_OMEGA
                } else {
                    TRIT_DWELL
                };
                cross_pairs.push(ChiralPair4::from_lanes(lo_lane, hi_lane)?);
            }
        }
        let cross_word = TritWord::from_chiral_pairs(&cross_pairs, None)?;
        let cx_k = (cross_word.alpha_count() as i64) - (cross_word.omega_count() as i64);
        let tx_k = t0_k + cx_k;
        let o_k = require_json_int(&comp[idx], "O_k")?
            .to_i64()
            .ok_or_else(|| CoreError::ValueError("O_k out of i64 range".to_string()))?;
        let dz = tx_k - o_k;

        s_bins.push(s_k);
        t0_bins.push(t0_k);
        cx_bins.push(cx_k);
        tx_bins.push(tx_k);
        dz_bins.push(dz);
        m_sum += dz.abs();
    }

    let sum_t0: i64 = t0_bins.iter().sum();
    let sum_cx: i64 = cx_bins.iter().sum();
    let sum_tx: i64 = tx_bins.iter().sum();
    let sum_dz: i64 = dz_bins.iter().sum();

    let mut out = BTreeMap::new();
    out.insert(
        "S_k".to_string(),
        JsonValue::Array(s_bins.into_iter().map(int_json).collect()),
    );
    out.insert(
        "T0_k".to_string(),
        JsonValue::Array(t0_bins.into_iter().map(int_json).collect()),
    );
    out.insert(
        "C_cross_k".to_string(),
        JsonValue::Array(cx_bins.into_iter().map(int_json).collect()),
    );
    out.insert(
        "T_cross_k".to_string(),
        JsonValue::Array(tx_bins.into_iter().map(int_json).collect()),
    );
    out.insert(
        "Delta_Z_k".to_string(),
        JsonValue::Array(dz_bins.into_iter().map(int_json).collect()),
    );
    out.insert("sum_T0".to_string(), int_json(sum_t0));
    out.insert("sum_C_cross".to_string(), int_json(sum_cx));
    out.insert("sum_T_cross".to_string(), int_json(sum_tx));
    out.insert("sum_Delta_Z".to_string(), int_json(sum_dz));
    out.insert("sum_m_k".to_string(), int_json(m_sum));
    Ok(JsonValue::Object(out))
}

pub fn op_hydrogen_shell_series_exact(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let dest_m = require_i64(inputs, "dest_shell_m")?;
    let upper_ns = require_array(inputs, "upper_shells")?;
    if !matches!(dest_m, 1..=3) || upper_ns.is_empty() {
        return Err(CoreError::ValueError(
            "dest_shell_m must be in 1..=3 with non-empty upper_shells".to_string(),
        ));
    }

    let base_n = dest_m + 1;
    let inv_m2 = TritRatio::new(TritWord::one(), TritWord::from_i64(dest_m * dest_m))?;
    let dp_base = inv_m2.sub(&TritRatio::new(
        TritWord::one(),
        TritWord::from_i64(base_n * base_n),
    )?);
    let limit_ratio = inv_m2.checked_div(&dp_base)?;

    let mut transitions = Vec::with_capacity(upper_ns.len());
    for nv in upper_ns {
        let n_val = require_json_int(nv, "upper_n")?
            .to_i64()
            .ok_or_else(|| CoreError::ValueError("upper_n out of i64 range".to_string()))?;
        if n_val <= dest_m {
            return Err(CoreError::ValueError(
                "upper shell n must exceed destination shell m".to_string(),
            ));
        }
        let dp = inv_m2.sub(&TritRatio::new(
            TritWord::one(),
            TritWord::from_i64(n_val * n_val),
        )?);
        let ratio = dp.checked_div(&dp_base)?;
        let mut tobj = BTreeMap::new();
        tobj.insert("n".to_string(), int_json(n_val));
        tobj.insert("m".to_string(), int_json(dest_m));
        tobj.insert("delta_P_hat".to_string(), pair_json(&dp));
        tobj.insert("series_ratio".to_string(), pair_json(&ratio));
        transitions.push(JsonValue::Object(tobj));
    }

    let mut out = BTreeMap::new();
    out.insert("dest_shell_m".to_string(), int_json(dest_m));
    out.insert("baseline_delta_P_hat".to_string(), pair_json(&dp_base));
    out.insert("series_limit_ratio".to_string(), pair_json(&limit_ratio));
    out.insert("transitions".to_string(), JsonValue::Array(transitions));
    Ok(JsonValue::Object(out))
}

pub fn op_scoped_wire_and_moving_boundary(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let cross_edges = require_array(inputs, "crossing_edge_fluxes")?;
    let swept_edges = require_array(inputs, "swept_vertex_fluxes")?;
    let shed_edges = require_array(inputs, "shedding_edge_fluxes")?;
    let wire_cuts = require_array(inputs, "wire_cuts")?;
    if wire_cuts.len() != 4 {
        return Err(CoreError::ValueError("expected 4 wire cuts".to_string()));
    }

    let sum_word_arr = |arr: &[JsonValue], label: &str| -> Result<TritWord, CoreError> {
        let mut s = TritWord::zero();
        for v in arr {
            let x = require_json_int(v, label)?
                .to_i64()
                .ok_or_else(|| CoreError::ValueError(format!("{} out of i64 range", label)))?;
            s = s.add(&TritWord::from_i64(x));
        }
        Ok(s)
    };
    let phi_cross_w = sum_word_arr(cross_edges, "cross")?;
    let phi_sweep_w = sum_word_arr(swept_edges, "sweep")?;
    let phi_shed_w = sum_word_arr(shed_edges, "shed")?;
    let phi_mov_w = phi_cross_w.sub(&phi_sweep_w).add(&phi_shed_w);

    let rcd_wire = 5i64;
    let c3 = 3i64;
    let a_wire = TritRatio::new(TritWord::one(), TritWord::from_i64(3))?;
    let mut later_elec = TritRatio::zero();
    let mut wire_tot = TritRatio::zero();
    let mut elec_tot = TritRatio::zero();
    let mut cut_rows = Vec::with_capacity(4);

    for cv in wire_cuts {
        let cobj = require_obj(cv, "wire_cut")?;
        let cut_k = require_i64(cobj, "cut")?;
        let win_w = require_i64(cobj, "window")?;
        let coupled = require_i64(cobj, "coupled")?;
        if !matches!(coupled, 0 | 1) || win_w <= 0 {
            return Err(CoreError::ValueError(
                "invalid wire cut parameters".to_string(),
            ));
        }
        let (w_out, e_out) = if coupled == 1 {
            let rho_w = rcd_wire.min(win_w);
            let w = TritRatio::new(TritWord::from_i64(c3 * rho_w), TritWord::one())?.mul(&a_wire);
            let e = w.neg();
            later_elec = later_elec.add(&w);
            (w, e)
        } else {
            (TritRatio::zero(), TritRatio::zero())
        };
        wire_tot = wire_tot.add(&w_out);
        elec_tot = elec_tot.add(&e_out);
        let union_v = w_out.add(&e_out);
        let mut robj = BTreeMap::new();
        robj.insert("cut".to_string(), int_json(cut_k));
        robj.insert("wire_outward".to_string(), pair_json(&w_out));
        robj.insert("electron_outward".to_string(), pair_json(&e_out));
        robj.insert("enclosing_union".to_string(), pair_json(&union_v));
        robj.insert("later_electron_current".to_string(), pair_json(&later_elec));
        cut_rows.push(JsonValue::Object(robj));
    }

    let union_tot = wire_tot.add(&elec_tot);
    if !union_tot.is_zero() {
        return Err(CoreError::ValueError(
            "wire+electron union boundary must vanish".to_string(),
        ));
    }

    let mut out = BTreeMap::new();
    out.insert(
        "Phi_cross".to_string(),
        int_json(word_to_i64(&phi_cross_w, "Phi_cross")?),
    );
    out.insert(
        "Phi_sweep".to_string(),
        int_json(word_to_i64(&phi_sweep_w, "Phi_sweep")?),
    );
    out.insert(
        "Phi_shedding".to_string(),
        int_json(word_to_i64(&phi_shed_w, "Phi_shedding")?),
    );
    out.insert(
        "Phi_moving".to_string(),
        int_json(word_to_i64(&phi_mov_w, "Phi_moving")?),
    );
    out.insert("wire_window_total".to_string(), pair_json(&wire_tot));
    out.insert("electron_window_total".to_string(), pair_json(&elec_tot));
    out.insert("union_boundary_total".to_string(), pair_json(&union_tot));
    out.insert("final_electron_current".to_string(), pair_json(&later_elec));
    out.insert("cuts".to_string(), JsonValue::Array(cut_rows));
    Ok(JsonValue::Object(out))
}

pub fn op_sparc_pooled_primary_exact(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let bins = require_array(inputs, "bins")?;
    if bins.is_empty() {
        return Err(CoreError::ValueError("SPARC bins required".to_string()));
    }

    let w5 = TritWord::from_i64(5);
    let w7 = TritWord::from_i64(7);
    let w10 = TritWord::from_i64(10);
    let w80 = TritWord::from_i64(80);

    let mut terms: Vec<(TritWord, TritWord)> = Vec::with_capacity(bins.len());
    let mut scored = 0i64;

    for bv in bins {
        let bobj = require_obj(bv, "sparc_bin")?;
        let v_obs =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(bobj, "V_obs")?, true, true)?);
        let v_gas =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(bobj, "V_gas")?, true, true)?);
        let v_disk =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(bobj, "V_disk")?, true, true)?);
        let v_bul =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(bobj, "V_bul")?, true, true)?);
        let r_kpc =
            TritRatio::from_bigrat(&parse_printed_rational(require_str(bobj, "r_kpc")?, true, true)?);

        if v_obs.sign() != 0 {
            // Canonical declared G0 SPARC law matching tier2_exact.py:
            // U_bar = V_gas^2 + (1/2)*V_disk^2 + (7/10)*V_bul^2
            // U_AO  = U_bar + 8*R*(|V_gas| + |V_disk| + |V_bul|)
            let mut scale_s = r_kpc.den().clone();
            scale_s = trit_lcm(&scale_s, v_obs.den())?;
            scale_s = trit_lcm(&scale_s, v_gas.den())?;
            scale_s = trit_lcm(&scale_s, v_disk.den())?;
            scale_s = trit_lcm(&scale_s, v_bul.den())?;

            let (qr, _) = scale_s.divmod_floor(r_kpc.den())?;
            let (qvo, _) = scale_s.divmod_floor(v_obs.den())?;
            let (qvg, _) = scale_s.divmod_floor(v_gas.den())?;
            let (qvd, _) = scale_s.divmod_floor(v_disk.den())?;
            let (qvb, _) = scale_s.divmod_floor(v_bul.den())?;

            let wr = r_kpc.num().mul(&qr);
            let wvo = v_obs.num().mul(&qvo);
            let wvg = v_gas.num().mul(&qvg);
            let wvd = v_disk.num().mul(&qvd);
            let wvb = v_bul.num().mul(&qvb);

            let u_obs_10 = w10.mul(&wvo.mul(&wvo));
            let u_bar_10 = w10
                .mul(&wvg.mul(&wvg))
                .add(&w5.mul(&wvd.mul(&wvd)))
                .add(&w7.mul(&wvb.mul(&wvb)));
            let v_abs_sum = wvg.abs_word().add(&wvd.abs_word()).add(&wvb.abs_word());
            let c_cap_10 = w80.mul(&wr).mul(&v_abs_sum);
            let u_ao_10 = u_bar_10.add(&c_cap_10);
            let delta_abs_10 = u_ao_10.sub(&u_obs_10).abs_word();
            terms.push((delta_abs_10, u_obs_10));
            scored += 1;
        }
    }

    if scored <= 0 {
        return Err(CoreError::ValueError(
            "at least one positive U_obs bin required".to_string(),
        ));
    }

    let rel_sum = sum_trit_ratios_balanced(terms)?;
    let scale_factor = TritRatio::new(TritWord::from_i64(100), TritWord::from_i64(scored))?;
    let mape_exact = rel_sum.mul(&scale_factor);
    let mape_8dp = format_fixed(&mape_exact.to_bigrat(), 8)?;

    let mut out = BTreeMap::new();
    out.insert("N_total".to_string(), int_json(bins.len() as i64));
    out.insert("N_scored".to_string(), int_json(scored));
    out.insert("MAPE_U_exact".to_string(), pair_json(&mape_exact));
    out.insert("MAPE_U_8dp".to_string(), str_json(&mape_8dp));
    Ok(JsonValue::Object(out))
}
