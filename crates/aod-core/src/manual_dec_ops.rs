//! Uniform Manual 1 D.E.C. & boundary-stack evaluators (`RC-033`..`RC-044`).
//!
//! Pure `std`-only, zero-`unsafe` exact `BigInt` / `BigRat` implementations
//! matching `manual/engine/sectors/manual_dec_examples.py`.

use std::collections::BTreeMap;

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::json::JsonValue;
use crate::numeric::{format_fixed, parse_canonical_rational_pair, parse_printed_rational};
use crate::ops::require_json_int;
use crate::CoreError;

const POPCOUNT_4BIT: [i64; 16] = [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4];

fn pair_json(q: &BigRat) -> JsonValue {
    let [n, d] = q.canonical_pair();
    JsonValue::Array(vec![JsonValue::Str(n), JsonValue::Str(d)])
}

fn int_json(v: i64) -> JsonValue {
    JsonValue::Int(BigInt::from_i64(v))
}

fn str_json(s: &str) -> JsonValue {
    JsonValue::Str(s.to_string())
}

fn bits4(v: usize) -> String {
    format!(
        "{}{}{}{}",
        (v >> 3) & 1,
        (v >> 2) & 1,
        (v >> 1) & 1,
        v & 1
    )
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

fn parse_i64_elem(val: &JsonValue, name: &str) -> Result<i64, CoreError> {
    let bi = require_json_int(val, name)?;
    bi.to_i64()
        .ok_or_else(|| CoreError::ValueError(format!("{} exceeds i64 bounds", name)))
}

fn parse_rat_pair_field(
    obj: &BTreeMap<String, JsonValue>,
    key: &str,
) -> Result<BigRat, CoreError> {
    let arr = require_array(obj, key)?;
    if arr.len() != 2 {
        return Err(CoreError::ValueError(format!(
            "{} must be a 2-element rational pair",
            key
        )));
    }
    let n_s = match &arr[0] {
        JsonValue::Str(s) => s.as_str(),
        other => {
            return Err(CoreError::TypeError(format!(
                "{}[0] must be str, got {}",
                key,
                other.type_name()
            )))
        }
    };
    let d_s = match &arr[1] {
        JsonValue::Str(s) => s.as_str(),
        other => {
            return Err(CoreError::TypeError(format!(
                "{}[1] must be str, got {}",
                key,
                other.type_name()
            )))
        }
    };
    parse_canonical_rational_pair(n_s, d_s)
}

fn isqrt_floor(n: i64) -> Result<i64, CoreError> {
    if n < 0 {
        return Err(CoreError::ValueError(format!(
            "negative integer in isqrt_floor: {}",
            n
        )));
    }
    if n < 2 {
        return Ok(n);
    }
    let mut lo: i64 = 1;
    let mut hi: i64 = n;
    while lo <= hi {
        let mid = lo + (hi - lo) / 2;
        let sq = mid.saturating_mul(mid);
        if sq == n {
            return Ok(mid);
        }
        if sq < n {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    Ok(hi)
}

fn isqrt_ceil(n: i64) -> Result<i64, CoreError> {
    let fl = isqrt_floor(n)?;
    if fl * fl == n {
        Ok(fl)
    } else {
        Ok(fl + 1)
    }
}

fn arctan_unit_enclosure(inv_x: i64, terms: usize) -> Result<(BigRat, BigRat), CoreError> {
    if inv_x < 2 || terms < 1 {
        return Err(CoreError::ValueError(
            "invalid arctan enclosure parameters".to_string(),
        ));
    }
    let mut acc = BigRat::zero();
    let x_sq = BigInt::from_i64(inv_x * inv_x);
    let mut p = BigInt::from_i64(inv_x);
    for k in 0..terms {
        let coeff = BigInt::from_usize(2 * k + 1);
        let den = &coeff * &p;
        let term = BigRat::new(BigInt::one(), den)?;
        if k % 2 == 0 {
            acc = &acc + &term;
        } else {
            acc = &acc - &term;
        }
        p = &p * &x_sq;
    }
    let next_den = &BigInt::from_usize(2 * terms + 1) * &p;
    let next_term = BigRat::new(BigInt::one(), next_den)?;
    if terms % 2 == 0 {
        Ok((acc.clone(), &acc + &next_term))
    } else {
        Ok((&acc - &next_term, acc))
    }
}

fn octant_3d(x: i64, y: i64, z: i64) -> usize {
    let b0 = if x < 0 { 1usize } else { 0usize };
    let b1 = if y < 0 { 2usize } else { 0usize };
    let b2 = if z < 0 { 4usize } else { 0usize };
    b0 | b1 | b2
}

// ---------------------------------------------------------------------------
// RC-033: dec_native_closure_wave_fold
// ---------------------------------------------------------------------------

pub fn op_dec_native_closure_wave_fold(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let dwell_m = require_i64(inputs, "dwell_m")?;
    if !(0..=16).contains(&dwell_m) {
        return Err(CoreError::ValueError("dwell_m out of range".to_string()));
    }
    let seps_arr = require_array(inputs, "beat_separations")?;
    if seps_arr.is_empty() {
        return Err(CoreError::ValueError(
            "beat_separations must be non-empty".to_string(),
        ));
    }
    let mut seps = Vec::with_capacity(seps_arr.len());
    for v in seps_arr {
        let s = parse_i64_elem(v, "beat_separation")?;
        if s < 2 {
            return Err(CoreError::ValueError(
                "beat separation must be >= 2".to_string(),
            ));
        }
        seps.push(s);
    }
    let sig_arr = require_array(inputs, "harmonic_signal")?;
    if sig_arr.len() != 4 {
        return Err(CoreError::ValueError(
            "harmonic_signal must have length 4".to_string(),
        ));
    }
    let mut sig = [0i64; 4];
    for (idx, v) in sig_arr.iter().enumerate() {
        sig[idx] = parse_i64_elem(v, "harmonic_signal[i]")?;
    }

    let v0: usize = 0;
    let v1: usize = v0 ^ 1;
    if POPCOUNT_4BIT[(v0 ^ v1) & 15] != 1 {
        return Err(CoreError::ValueError("non-H1 symmetric step".to_string()));
    }
    let v_end = v1 ^ 1;
    if v_end != v0 {
        return Err(CoreError::ValueError(
            "symmetric Monon failed retained-start return".to_string(),
        ));
    }

    let asym_v: [usize; 5] = [0, 1, 3, 1, 0];
    let mut asym_edges: i64 = 0;
    for i in 0..(asym_v.len() - 1) {
        if POPCOUNT_4BIT[(asym_v[i] ^ asym_v[i + 1]) & 15] != 1 {
            return Err(CoreError::ValueError("non-H1 asymmetric step".to_string()));
        }
        asym_edges += 1;
    }
    let leg_out: i64 = 1;
    let leg_back: i64 = 3;
    let equal_leg = if 2 * leg_out == asym_edges && 2 * leg_back == asym_edges {
        1
    } else {
        0
    };

    let closures = (seps.len() as i64) + 1;
    let beats = closures - 1;
    let cadence_span: i64 = seps.iter().sum();

    let mem_hi = BigRat::from_i64_pair(3, 4)?;
    let mem_lo = BigRat::from_i64_pair(1, 4)?;
    let afc_fwd = &mem_hi - &mem_lo;
    let afc_rev = &mem_lo - &mem_hi;
    let afc_eq = BigRat::zero();

    let mut re_hat = [0i64; 4];
    let mut im_hat = [0i64; 4];
    for k in 0..4usize {
        let mut r_acc = 0i64;
        let mut i_acc = 0i64;
        for (n, &x_n) in sig.iter().enumerate() {
            match (k * n) % 4 {
                0 => r_acc += x_n,
                1 => i_acc -= x_n,
                2 => r_acc -= x_n,
                _ => i_acc += x_n,
            }
        }
        re_hat[k] = r_acc;
        im_hat[k] = i_acc;
    }

    let mut resid_l1 = BigRat::zero();
    for n in 0..4usize {
        let mut r_sum = 0i64;
        let mut i_sum = 0i64;
        for k in 0..4usize {
            let rk = re_hat[k];
            let ik = im_hat[k];
            match (k * n) % 4 {
                0 => {
                    r_sum += rk;
                    i_sum += ik;
                }
                1 => {
                    r_sum -= ik;
                    i_sum += rk;
                }
                2 => {
                    r_sum -= rk;
                    i_sum -= ik;
                }
                _ => {
                    r_sum += ik;
                    i_sum -= rk;
                }
            }
        }
        if i_sum != 0 {
            return Err(CoreError::ValueError(
                "nonzero imaginary residue in Z4 inverse DFT".to_string(),
            ));
        }
        let rec_n = BigRat::from_i64_pair(r_sum, 4)?;
        let diff = (&rec_n - &BigRat::from_i64(sig[n])).abs();
        resid_l1 = &resid_l1 + &diff;
    }

    let mut out = BTreeMap::new();
    out.insert("sym_edges".to_string(), int_json(2));
    out.insert("sym_phases".to_string(), int_json(1));
    out.insert("dwell_burned_to".to_string(), int_json(0));
    out.insert("asym_edges".to_string(), int_json(asym_edges));
    out.insert("asym_phases".to_string(), int_json(1));
    out.insert("equal_leg_factorizable".to_string(), int_json(equal_leg));
    out.insert("closures".to_string(), int_json(closures));
    out.insert("beats".to_string(), int_json(beats));
    out.insert("cadence_span".to_string(), int_json(cadence_span));
    out.insert("single_field_nF".to_string(), int_json(1));
    out.insert("disoma_nF".to_string(), int_json(2));
    out.insert("fold_inner_cycles_preserved".to_string(), int_json(1));
    out.insert("afc_flux_fwd".to_string(), pair_json(&afc_fwd));
    out.insert("afc_flux_rev".to_string(), pair_json(&afc_rev));
    out.insert("afc_flux_eq".to_string(), pair_json(&afc_eq));
    out.insert(
        "z4_dft_re".to_string(),
        JsonValue::Array(re_hat.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert(
        "z4_dft_im".to_string(),
        JsonValue::Array(im_hat.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert("z4_recon_residual".to_string(), pair_json(&resid_l1));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-034: dec_awareness_matched_operativity
// ---------------------------------------------------------------------------

pub fn op_dec_awareness_matched_operativity(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let t_arr = require_array(inputs, "target_seps")?;
    let p_arr = require_array(inputs, "peer_seps")?;
    if t_arr.len() != 3 || p_arr.len() != 3 {
        return Err(CoreError::ValueError(
            "target_seps and peer_seps must have 3 elements".to_string(),
        ));
    }
    let mut t_sum = 0i64;
    for v in t_arr {
        t_sum += parse_i64_elem(v, "target_sep")?;
    }
    let mut p_sum = 0i64;
    for v in p_arr {
        p_sum += parse_i64_elem(v, "peer_sep")?;
    }

    let phi_rec = require_i64(inputs, "recurrent_flux")?;
    let phi_ind = require_i64(inputs, "independent_flux")?;
    let gain = require_i64(inputs, "gain")?;
    let q_act = require_i64(inputs, "active_query")?;
    let ps_arr = require_array(inputs, "pressures")?;
    if ps_arr.is_empty() {
        return Err(CoreError::ValueError(
            "pressures must be non-empty".to_string(),
        ));
    }
    let mut pressures = Vec::with_capacity(ps_arr.len());
    for v in ps_arr {
        let p = parse_i64_elem(v, "pressure")?;
        if p <= 0 {
            return Err(CoreError::ValueError(
                "pressure must be positive".to_string(),
            ));
        }
        pressures.push(p);
    }

    let cut_contact = p_sum + 2;
    let cut_retain = cut_contact + 1;
    let cut_boundary = t_sum + 3;
    let cut_response = cut_boundary + 1;
    let r_e = phi_rec - phi_ind;

    let mut families = Vec::with_capacity(pressures.len());
    for &p in &pressures {
        let j_ret = BigRat::from_i64_pair(gain * r_e, p)?;
        let j_rem = BigRat::zero();
        let diff = &j_ret - &j_rem;
        let v_ret = if j_ret.is_positive() {
            bits4(1)
        } else {
            bits4(2)
        };
        let v_rem = if j_rem.is_positive() {
            bits4(1)
        } else {
            bits4(2)
        };
        let op_w = if cut_response > cut_retain && v_ret != v_rem {
            1
        } else {
            0
        };
        let mut fm = BTreeMap::new();
        fm.insert("pressure".to_string(), int_json(p));
        fm.insert("J_retained".to_string(), pair_json(&j_ret));
        fm.insert("J_removed".to_string(), pair_json(&j_rem));
        fm.insert("delta_J".to_string(), pair_json(&diff));
        fm.insert("next_vertex_retained".to_string(), str_json(&v_ret));
        fm.insert("next_vertex_removed".to_string(), str_json(&v_rem));
        fm.insert("operativity_Op".to_string(), int_json(op_w));
        families.push(JsonValue::Object(fm));
    }

    let passive_delta = BigRat::zero();
    let j_active_p0 = BigRat::from_i64_pair(q_act + gain * r_e, pressures[0])?;

    let mut out = BTreeMap::new();
    out.insert("cut_contact".to_string(), int_json(cut_contact));
    out.insert("cut_retain".to_string(), int_json(cut_retain));
    out.insert("cut_boundary".to_string(), int_json(cut_boundary));
    out.insert("cut_response".to_string(), int_json(cut_response));
    out.insert("retained_rebalancing_r".to_string(), int_json(r_e));
    out.insert("pressure_families".to_string(), JsonValue::Array(families));
    out.insert("passive_readonly_delta".to_string(), pair_json(&passive_delta));
    out.insert("active_query_J_first_p".to_string(), pair_json(&j_active_p0));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-035: dec_cell_measures_staircase_fold
// ---------------------------------------------------------------------------

pub fn op_dec_cell_measures_staircase_fold(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let e_num = require_i64(inputs, "edge_num")?;
    let e_den = require_i64(inputs, "edge_den")?;
    let m_terms_i64 = require_i64(inputs, "machin_terms")?;
    if e_num <= 0 || e_den <= 0 || !(1..=64).contains(&m_terms_i64) {
        return Err(CoreError::ValueError(
            "invalid cell_measures parameters".to_string(),
        ));
    }
    let lvls_arr = require_array(inputs, "levels")?;
    if lvls_arr.is_empty() {
        return Err(CoreError::ValueError("levels must be non-empty".to_string()));
    }

    let a = BigRat::from_i64_pair(e_num, e_den)?;
    let a2 = &a * &a;
    let a3 = &a2 * &a;
    let v4 = &a2 * &a2;
    let b3 = &BigRat::from_i64(8) * &a3;

    let mut st_rows = Vec::with_capacity(lvls_arr.len());
    for v in lvls_arr {
        let n = parse_i64_elem(v, "level")?;
        if n < 1 {
            return Err(CoreError::ValueError("level must be >= 1".to_string()));
        }
        let n_sq = n * n;
        let mut u_sum = 0i64;
        let mut l_sum = 0i64;
        for i in 0..n {
            u_sum += isqrt_ceil(n_sq - i * i)?;
            let rem = n_sq - (i + 1) * (i + 1);
            if rem > 0 {
                l_sum += isqrt_floor(rem)?;
            }
        }
        let a_minus = BigRat::from_i64_pair(4 * l_sum, n_sq)?;
        let a_plus = BigRat::from_i64_pair(4 * u_sum, n_sq)?;
        let disc = &BigRat::from_i64(8) - &(&BigRat::from_i64(2) * &a_plus);
        let mut rm = BTreeMap::new();
        rm.insert("n".to_string(), int_json(n));
        rm.insert("A_minus".to_string(), pair_json(&a_minus));
        rm.insert("A_plus".to_string(), pair_json(&a_plus));
        rm.insert("C_axial".to_string(), int_json(8));
        rm.insert("Cr_minus_2Aplus".to_string(), pair_json(&disc));
        st_rows.push(JsonValue::Object(rm));
    }

    let (lo5, hi5) = arctan_unit_enclosure(5, m_terms_i64 as usize)?;
    let (lo239, hi239) = arctan_unit_enclosure(239, m_terms_i64 as usize)?;
    let c16 = BigRat::from_i64(16);
    let c4 = BigRat::from_i64(4);
    let pi_lo = &(&c16 * &lo5) - &(&c4 * &hi239);
    let pi_hi = &(&c16 * &hi5) - &(&c4 * &lo239);
    let axial_gap_lb = &BigRat::from_i64(8) - &(&BigRat::from_i64(2) * &pi_hi);
    if !axial_gap_lb.is_positive() {
        return Err(CoreError::ValueError(
            "axial perimeter gap lower bound not positive".to_string(),
        ));
    }

    let q4_counts = vec![
        int_json(16),
        int_json(32),
        int_json(24),
        int_json(8),
        int_json(1),
    ];
    let mut out = BTreeMap::new();
    out.insert("q4_cell_counts".to_string(), JsonValue::Array(q4_counts));
    out.insert("V4_exact".to_string(), pair_json(&v4));
    out.insert("B3_exact".to_string(), pair_json(&b3));
    out.insert("boundary_sq_zero".to_string(), int_json(1));
    out.insert("staircase".to_string(), JsonValue::Array(st_rows));
    out.insert("pi_lower".to_string(), pair_json(&pi_lo));
    out.insert("pi_upper".to_string(), pair_json(&pi_hi));
    out.insert("axial_gap_positive".to_string(), int_json(1));
    out.insert("fold_occupied_area".to_string(), int_json(2));
    out.insert("fold_image_area".to_string(), int_json(1));
    out.insert("fold_retained_multiplicity".to_string(), int_json(2));
    out.insert("fold_oriented_top_sum".to_string(), int_json(0));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-036: dec_typed_maps_exact_laws
// ---------------------------------------------------------------------------

fn three_point_moments(v0: &BigRat, v1: &BigRat, v2: &BigRat) -> Result<(BigRat, BigRat), CoreError> {
    let q14 = BigRat::from_i64_pair(1, 4)?;
    let q12 = BigRat::from_i64_pair(1, 2)?;
    let mean = &(&(&q14 * v0) + &(&q12 * v1)) + &(&q14 * v2);
    let d0 = v0 - &mean;
    let d1 = v1 - &mean;
    let d2 = v2 - &mean;
    let var = &(&(&q14 * &(&d0 * &d0)) + &(&q12 * &(&d1 * &d1))) + &(&q14 * &(&d2 * &d2));
    Ok((mean, var))
}

pub fn op_dec_typed_maps_exact_laws(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let x_in = require_i64(inputs, "x_in")?;
    let d_small_den = require_i64(inputs, "delta_small_den")?;
    let a_orig_den = require_i64(inputs, "a_orig_den")?;
    let eps_den = require_i64(inputs, "eps_den")?;
    let del_orig_den = require_i64(inputs, "del_orig_den")?;
    if d_small_den <= 1 || a_orig_den <= 1 || eps_den <= 1 || del_orig_den <= 1 {
        return Err(CoreError::ValueError(
            "denominators must exceed 1".to_string(),
        ));
    }

    let one = BigRat::one();
    let two = BigRat::from_i64(2);
    let composed_fg = 4 * x_in;

    let d = BigRat::from_i64_pair(1, d_small_den)?;
    let t_end = one.checked_div(&(&(&one - &d) * &(&one + &d)))?;
    let (t_mean, t_var) = three_point_moments(&t_end, &one, &t_end)?;
    let t_lin_var = BigRat::zero();

    let k_near = BigRat::from_i64_pair(999, 1000)?;
    let f0 = &(&one - &d) * &(&one + &(&k_near * &d));
    let f2 = &(&one + &d) * &(&one - &(&k_near * &d));
    let (f_mean, f_var) = three_point_moments(&f0, &one, &f2)?;
    let var_delta = (&d * &d).checked_div(&two)?;
    let f_deriv0 = &one - &k_near;
    let f_lin_var = &(&f_deriv0 * &f_deriv0) * &var_delta;
    let f_ratio = f_var.checked_div(&f_lin_var)?;

    let a = BigRat::from_i64_pair(1, a_orig_den)?;
    let u_neg = &one.checked_div(&(&one - &a))? - &a;
    let u_pos = &one.checked_div(&(&one + &a))? + &a;
    let u_mean = (&u_neg + &u_pos).checked_div(&two)?;
    let du_n = &u_neg - &u_mean;
    let du_p = &u_pos - &u_mean;
    let u_var = (&(&du_n * &du_n) + &(&du_p * &du_p)).checked_div(&two)?;
    let u_lin_var = BigRat::zero();

    let eps = BigRat::from_i64_pair(1, eps_den)?;
    let del_o = BigRat::from_i64_pair(1, del_orig_den)?;
    let b = &one - &del_o;
    let v0 = &(&one - &eps) * &(&one + &(&b * &eps));
    let v2 = &(&one + &eps) * &(&one - &(&b * &eps));
    let (v_mean, v_var) = three_point_moments(&v0, &one, &v2)?;
    let v_lin_var = (&(&del_o * &del_o) * &(&eps * &eps)).checked_div(&two)?;
    let v_ratio = v_var.checked_div(&v_lin_var)?;

    let lip_bound = &(&BigRat::from_i64(4) * &BigRat::from_i64_pair(1, 100)?)
        + &BigRat::from_i64_pair(1, 1000)?;

    let mut out = BTreeMap::new();
    out.insert("composed_fg_output".to_string(), int_json(composed_fg));
    out.insert("dedup_source_count".to_string(), int_json(1));
    out.insert("eval_role_rejected".to_string(), int_json(1));
    out.insert("T_mean".to_string(), pair_json(&t_mean));
    out.insert("T_var".to_string(), pair_json(&t_var));
    out.insert("T_lin_var".to_string(), pair_json(&t_lin_var));
    out.insert("F_mean".to_string(), pair_json(&f_mean));
    out.insert("F_var".to_string(), pair_json(&f_var));
    out.insert("F_lin_var".to_string(), pair_json(&f_lin_var));
    out.insert("F_var_over_lin".to_string(), pair_json(&f_ratio));
    out.insert("U_mean".to_string(), pair_json(&u_mean));
    out.insert("U_var".to_string(), pair_json(&u_var));
    out.insert("U_lin_var".to_string(), pair_json(&u_lin_var));
    out.insert("V_mean".to_string(), pair_json(&v_mean));
    out.insert("V_var".to_string(), pair_json(&v_var));
    out.insert("V_lin_var".to_string(), pair_json(&v_lin_var));
    out.insert("V_var_over_lin".to_string(), pair_json(&v_ratio));
    out.insert("lipschitz_composed_bound".to_string(), pair_json(&lip_bound));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-037: dec_temporal_si_bridge_bounds
// ---------------------------------------------------------------------------

pub fn op_dec_temporal_si_bridge_bounds(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let c_arr = require_array(inputs, "compared_cuts")?;
    let r_arr = require_array(inputs, "ref_cuts")?;
    if c_arr.len() < 2 || r_arr.len() < 2 {
        return Err(CoreError::ValueError(
            "compared_cuts and ref_cuts require >= 2 closures".to_string(),
        ));
    }
    for v in c_arr {
        let _ = parse_i64_elem(v, "c_cut")?;
    }
    for v in r_arr {
        let _ = parse_i64_elem(v, "r_cut")?;
    }
    let f_cs = require_i64(inputs, "f_cs_hz")?;
    let cal_ref = require_i64(inputs, "cal_ref")?;
    let fa = require_array(inputs, "field_a")?;
    let fb = require_array(inputs, "field_b")?;
    if fa.len() != 2 || fb.len() != 2 {
        return Err(CoreError::ValueError(
            "field_a and field_b must have 2 elements".to_string(),
        ));
    }
    let na_cal = parse_i64_elem(&fa[0], "na_cal")?;
    let na_val = parse_i64_elem(&fa[1], "na_val")?;
    let nb_cal = parse_i64_elem(&fb[0], "nb_cal")?;
    let nb_val = parse_i64_elem(&fb[1], "nb_val")?;
    if f_cs <= 0 || cal_ref <= 0 || na_cal <= 0 || nb_cal <= 0 {
        return Err(CoreError::ValueError(
            "positive temporal counts required".to_string(),
        ));
    }

    let n_c = (c_arr.len() as i64) - 1;
    let n_r = (r_arr.len() as i64) - 1;
    let biz_cr = BigRat::from_i64_pair(n_c, n_r)?;
    let biz_rc = BigRat::from_i64_pair(n_r, n_c)?;
    let lag_fwd = &BigRat::from_i64(n_c - n_r) + &BigRat::from_i64_pair(1, 2)?;
    let lag_rev = -&lag_fwd;

    let t_sec = BigRat::from_i64_pair(n_r, f_cs)?;
    let nu_bar = BigRat::from_i64(n_c).checked_div(&t_sec)?;

    let cal_rat = BigRat::from_i64(cal_ref);
    let pred_a = BigRat::from_i64_pair(cal_ref * na_val, na_cal)?;
    let rel_a = (&pred_a - &cal_rat).checked_div(&cal_rat)?;
    let pred_b = BigRat::from_i64_pair(cal_ref * nb_val, nb_cal)?;
    let rel_b = (&pred_b - &cal_rat).checked_div(&cal_rat)?;

    let mut out = BTreeMap::new();
    out.insert("delta_bip_compared".to_string(), int_json(n_c));
    out.insert("delta_bip_ref".to_string(), int_json(n_r));
    out.insert("biz_c_over_r".to_string(), pair_json(&biz_cr));
    out.insert("biz_r_over_c".to_string(), pair_json(&biz_rc));
    out.insert("lag_forward".to_string(), pair_json(&lag_fwd));
    out.insert("lag_reverse".to_string(), pair_json(&lag_rev));
    out.insert("T_seconds".to_string(), pair_json(&t_sec));
    out.insert("nu_bar_hz".to_string(), pair_json(&nu_bar));
    out.insert("transfer_A_pred".to_string(), pair_json(&pred_a));
    out.insert("transfer_A_rel_resid".to_string(), pair_json(&rel_a));
    out.insert("transfer_B_pred".to_string(), pair_json(&pred_b));
    out.insert("transfer_B_rel_resid".to_string(), pair_json(&rel_b));
    out.insert(
        "intervention_ratio_before".to_string(),
        pair_json(&BigRat::from_i64_pair(6, 5)?),
    );
    out.insert(
        "intervention_ratio_after".to_string(),
        pair_json(&BigRat::from_i64_pair(2, 5)?),
    );
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-038: dec_short_window_rcd_clipping
// ---------------------------------------------------------------------------

pub fn op_dec_short_window_rcd_clipping(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let w_arr = require_array(inputs, "windows")?;
    if w_arr.is_empty() {
        return Err(CoreError::ValueError("windows must be non-empty".to_string()));
    }
    let mut windows = Vec::with_capacity(w_arr.len());
    for v in w_arr {
        let w = parse_i64_elem(v, "window")?;
        if w < 1 {
            return Err(CoreError::ValueError("window must be >= 1".to_string()));
        }
        windows.push(w);
    }
    let c3 = require_i64(inputs, "c3")?;
    let c_close = require_i64(inputs, "c_close")?;
    if c3 <= 0 || c_close <= 0 {
        return Err(CoreError::ValueError(
            "c3 and c_close must be positive".to_string(),
        ));
    }

    let supports: [(&str, i64); 3] = [("1:2", 9), ("3:3", 61), ("3:4", 137)];
    let mut records = Vec::with_capacity(supports.len() * windows.len());
    for &(fam, rd) in &supports {
        for &w in &windows {
            let rho_w = if rd < w { rd } else { w };
            let p_d = c3 * rho_w;
            let over = if rd > w { rd - w } else { 0 };
            let q_d = c3 * over;
            if p_d + q_d != c3 * rd {
                return Err(CoreError::ValueError(
                    "short-window conservation violated".to_string(),
                ));
            }
            let x_sh = if p_d > c_close { p_d - c_close } else { 0 };
            let mut rm = BTreeMap::new();
            rm.insert("support".to_string(), str_json(fam));
            rm.insert("RD".to_string(), int_json(rd));
            rm.insert("window".to_string(), int_json(w));
            rm.insert("rho_omega".to_string(), int_json(rho_w));
            rm.insert("p_D".to_string(), int_json(p_d));
            rm.insert("Q_D".to_string(), int_json(q_d));
            rm.insert("X_shed_vs_Cclose".to_string(), int_json(x_sh));
            records.push(JsonValue::Object(rm));
        }
    }

    let mut out = BTreeMap::new();
    out.insert("c3".to_string(), int_json(c3));
    out.insert("c_close".to_string(), int_json(c_close));
    out.insert("total_pairs".to_string(), int_json(records.len() as i64));
    out.insert("all_conserved".to_string(), int_json(1));
    out.insert("records".to_string(), JsonValue::Array(records));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-039: dec_hydrogen_shell_wavelet_step
// ---------------------------------------------------------------------------

pub fn op_dec_hydrogen_shell_wavelet_step(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let tr_arr = require_array(inputs, "transitions")?;
    if tr_arr.is_empty() {
        return Err(CoreError::ValueError(
            "transitions must be non-empty".to_string(),
        ));
    }
    let mut rows_out = Vec::with_capacity(tr_arr.len());
    for item in tr_arr {
        let pair = match item {
            JsonValue::Array(v) if v.len() == 2 => v,
            _ => {
                return Err(CoreError::ValueError(
                    "transition must be [n, m]".to_string(),
                ))
            }
        };
        let n = parse_i64_elem(&pair[0], "n")?;
        let m = parse_i64_elem(&pair[1], "m")?;
        if n <= m || m < 1 {
            return Err(CoreError::ValueError(
                "require n > m >= 1 in shell transition".to_string(),
            ));
        }
        let dp = &BigRat::from_i64_pair(1, m * m)? - &BigRat::from_i64_pair(1, n * n)?;
        let m_base = m + 1;
        let dp_base =
            &BigRat::from_i64_pair(1, m * m)? - &BigRat::from_i64_pair(1, m_base * m_base)?;
        let r_series = dp.checked_div(&dp_base)?;
        let lam_ratio = BigRat::one().checked_div(&r_series)?;
        let series_name = match m {
            1 => "Lyman".to_string(),
            2 => "Balmer".to_string(),
            3 => "Paschen".to_string(),
            other => format!("m{}", other),
        };
        let mut rm = BTreeMap::new();
        rm.insert("n".to_string(), int_json(n));
        rm.insert("m".to_string(), int_json(m));
        rm.insert("series".to_string(), str_json(&series_name));
        rm.insert("r_n_over_r1".to_string(), int_json(n * n));
        rm.insert("r_m_over_r1".to_string(), int_json(m * m));
        rm.insert("delta_P_hat".to_string(), pair_json(&dp));
        rm.insert("R_to_series_base".to_string(), pair_json(&r_series));
        rm.insert("wavelength_over_base".to_string(), pair_json(&lam_ratio));
        rows_out.push(JsonValue::Object(rm));
    }

    let mut out = BTreeMap::new();
    out.insert(
        "transition_count".to_string(),
        int_json(rows_out.len() as i64),
    );
    out.insert("transitions".to_string(), JsonValue::Array(rows_out));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-040: dec_solar_o0_boundary_audit
// ---------------------------------------------------------------------------

pub fn op_dec_solar_o0_boundary_audit(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let recs = require_array(inputs, "records")?;
    if recs.len() != 3 {
        return Err(CoreError::ValueError(
            "records must have 3 O0 rows".to_string(),
        ));
    }
    let mut out_rows = Vec::with_capacity(3);
    for v in recs {
        let ro = require_obj(v, "solar_record")?;
        let rid = require_str(ro, "id")?;
        let ao_s = require_str(ro, "ao")?;
        let tg_s = require_str(ro, "target")?;
        let ao = parse_printed_rational(ao_s, false, false)?;
        let tg = parse_printed_rational(tg_s, false, false)?;
        if !tg.is_positive() {
            return Err(CoreError::ValueError(
                "solar target must be positive".to_string(),
            ));
        }
        let resid = &ao - &tg;
        let ape = (&resid.abs() * &BigRat::from_i64(100)).checked_div(&tg)?;
        let mut rm = BTreeMap::new();
        rm.insert("id".to_string(), str_json(rid));
        rm.insert("ao_exact".to_string(), pair_json(&ao));
        rm.insert("target_exact".to_string(), pair_json(&tg));
        rm.insert("residual_exact".to_string(), pair_json(&resid));
        rm.insert("abs_percent_error_exact".to_string(), pair_json(&ape));
        rm.insert(
            "abs_percent_error_7dp".to_string(),
            str_json(&format_fixed(&ape, 7)?),
        );
        out_rows.push(JsonValue::Object(rm));
    }

    let mut out = BTreeMap::new();
    out.insert("native_sadar_evaluated".to_string(), int_json(0));
    out.insert(
        "producer_gate_status".to_string(),
        str_json("HOLD_MISSING_NATIVE_SOLAR_PRODUCER"),
    );
    out.insert("records".to_string(), JsonValue::Array(out_rows));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-041: dec_run_tumble_q4_stepper
// ---------------------------------------------------------------------------

pub fn op_dec_run_tumble_q4_stepper(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let ticks = require_i64(inputs, "ticks")?;
    let sat_lim = require_i64(inputs, "run_saturation_limit")?;
    let beta_a = require_i64(inputs, "beta_a")?;
    if ticks != 20 || sat_lim != 2 || beta_a != 5 {
        return Err(CoreError::ValueError(
            "canonical 20-tick run-tumble parameters required".to_string(),
        ));
    }

    let base_legs: [(usize, i64); 8] = [
        (0, 1),
        (1, 1),
        (2, -1),
        (3, 1),
        (0, -1),
        (1, -1),
        (2, 1),
        (3, -1),
    ];

    let mut h = [0i64; 4];
    let mut phase_counts = [0i64; 5];
    let mut octant_counts = [0i64; 8];
    let mut sum_q3 = 0i64;
    let mut sum_q4 = 0i64;
    let mut closure_at_16 = 0i64;

    for t in 1..=20usize {
        let leg_idx = ((t - 1) / 2) % base_legs.len();
        let (axis, sigma) = base_legs[leg_idx];
        h[axis] += sigma;
        let (x, y, z) = (h[0], h[1], h[2]);
        let q3 = x * x + y * y + z * z;
        let q4 = q3 + h[3] * h[3];
        let theta = (q3.rem_euclid(5)) as usize;
        let oc = octant_3d(x, y, z);
        phase_counts[theta] += 1;
        octant_counts[oc] += 1;
        sum_q3 += q3;
        sum_q4 += q4;
        if t == 16 && h == [0, 0, 0, 0] {
            closure_at_16 = 1;
        }
    }

    if closure_at_16 != 1 {
        return Err(CoreError::ValueError(
            "Q4 run-tumble walk failed closure at tick 16".to_string(),
        ));
    }

    let mut out = BTreeMap::new();
    out.insert("active_ticks".to_string(), int_json(ticks));
    out.insert("closure_at_tick_16".to_string(), int_json(closure_at_16));
    out.insert(
        "final_h4".to_string(),
        JsonValue::Array(h.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert("sum_Q3".to_string(), int_json(sum_q3));
    out.insert("sum_Q4".to_string(), int_json(sum_q4));
    out.insert(
        "phase_counts".to_string(),
        JsonValue::Array(phase_counts.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert(
        "octant_counts".to_string(),
        JsonValue::Array(octant_counts.iter().map(|&v| int_json(v)).collect()),
    );
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-042: dec_lensing_ray_chiral_delta3
// ---------------------------------------------------------------------------

pub fn op_dec_lensing_ray_chiral_delta3(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let shells = require_array(inputs, "shells")?;
    if shells.is_empty() {
        return Err(CoreError::ValueError("shells must be non-empty".to_string()));
    }
    let mut shell_out = Vec::with_capacity(shells.len());
    let mut flips_total = 0i64;
    let mut total_m = 0i64;
    let mut chi_state = 1i64;

    for v in shells {
        let so = require_obj(v, "shell")?;
        let k = require_i64(so, "k")?;
        let t0 = require_i64(so, "s_base")?;
        let c_x = require_i64(so, "c_cross")?;
        let flip = require_i64(so, "chiral_flip")?;
        let comp = require_i64(so, "comparator")?;
        if flip != 0 && flip != 1 {
            return Err(CoreError::ValueError(
                "chiral_flip must be 0 or 1".to_string(),
            ));
        }
        if flip == 1 {
            chi_state = -chi_state;
            flips_total += 1;
        }
        let tx = t0 + c_x;
        let dz = tx - comp;
        let sgn = if dz > 0 {
            1
        } else if dz < 0 {
            -1
        } else {
            0
        };
        let mag = dz.abs();
        total_m += mag;

        let mut sm = BTreeMap::new();
        sm.insert("k".to_string(), int_json(k));
        sm.insert("T0".to_string(), int_json(t0));
        sm.insert("C_cross".to_string(), int_json(c_x));
        sm.insert("T_cross".to_string(), int_json(tx));
        sm.insert("post_chi".to_string(), int_json(chi_state));
        sm.insert("Delta_Z".to_string(), int_json(dz));
        sm.insert("delta3_sgn".to_string(), int_json(sgn));
        sm.insert("delta3_m".to_string(), int_json(mag));
        shell_out.push(JsonValue::Object(sm));
    }

    let mut out = BTreeMap::new();
    out.insert("shell_count".to_string(), int_json(shell_out.len() as i64));
    out.insert("chiral_flips_total".to_string(), int_json(flips_total));
    out.insert("final_chirality".to_string(), int_json(chi_state));
    out.insert("delta3_total_m".to_string(), int_json(total_m));
    out.insert("target_quarantined_before_freeze".to_string(), int_json(1));
    out.insert("shells".to_string(), JsonValue::Array(shell_out));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-043: dec_cycle_shedding_exact_summary
// ---------------------------------------------------------------------------

pub fn op_dec_cycle_shedding_exact_summary(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let eta = parse_rat_pair_field(inputs, "eta_ret")?;
    let gamma = parse_rat_pair_field(inputs, "gamma_span")?;
    let lam = parse_rat_pair_field(inputs, "lambda_reclose")?;
    let ticks = require_array(inputs, "ticks")?;
    if ticks.is_empty() {
        return Err(CoreError::ValueError("ticks must be non-empty".to_string()));
    }

    let one = BigRat::one();
    let one_minus_lam = &one - &lam;
    let mut prev_p = BigRat::zero();
    let mut sum_x = BigRat::zero();
    let mut sum_o = BigRat::zero();
    let mut sum_r = BigRat::zero();
    let mut steps_out = Vec::with_capacity(ticks.len());

    for (idx, v) in ticks.iter().enumerate() {
        let to = require_obj(v, "tick")?;
        let lead = parse_rat_pair_field(to, "lead")?;
        let lag = parse_rat_pair_field(to, "lag")?;
        let comp = parse_rat_pair_field(to, "comp")?;
        let span = (&lead - &lag).abs();
        let before = &(&eta * &prev_p) + &(&gamma * &span);
        let raw_exc = &before - &comp;
        let x_t = if raw_exc.is_positive() {
            raw_exc
        } else {
            BigRat::zero()
        };
        let p_t = &before - &x_t;
        let r_t = &lam * &x_t;
        let o_t = &one_minus_lam * &x_t;
        prev_p = p_t.clone();
        sum_x = &sum_x + &x_t;
        sum_o = &sum_o + &o_t;
        sum_r = &sum_r + &r_t;

        let mut sm = BTreeMap::new();
        sm.insert("tick".to_string(), int_json(idx as i64));
        sm.insert("span".to_string(), pair_json(&span));
        sm.insert("before_clip".to_string(), pair_json(&before));
        sm.insert("padar_burden".to_string(), pair_json(&p_t));
        sm.insert("shed_excess".to_string(), pair_json(&x_t));
        sm.insert("outward_O".to_string(), pair_json(&o_t));
        sm.insert("local_R".to_string(), pair_json(&r_t));
        steps_out.push(JsonValue::Object(sm));
    }

    let out_share = if sum_x.is_positive() {
        sum_o.checked_div(&sum_x)?
    } else {
        BigRat::zero()
    };
    let loc_share = if sum_x.is_positive() {
        sum_r.checked_div(&sum_x)?
    } else {
        BigRat::zero()
    };

    let mut out = BTreeMap::new();
    out.insert("tick_count".to_string(), int_json(steps_out.len() as i64));
    out.insert("total_shed_X".to_string(), pair_json(&sum_x));
    out.insert("total_outward_O".to_string(), pair_json(&sum_o));
    out.insert("total_local_R".to_string(), pair_json(&sum_r));
    out.insert("outward_share_on_shed".to_string(), pair_json(&out_share));
    out.insert("local_share_on_shed".to_string(), pair_json(&loc_share));
    out.insert("steps".to_string(), JsonValue::Array(steps_out));
    Ok(JsonValue::Object(out))
}

// ---------------------------------------------------------------------------
// RC-044: dec_coordinate_phase_3d_walk
// ---------------------------------------------------------------------------

pub fn op_dec_coordinate_phase_3d_walk(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let pts_arr = require_array(inputs, "points")?;
    let beta_a = require_i64(inputs, "beta_a")?;
    if pts_arr.len() < 2 || beta_a <= 0 {
        return Err(CoreError::ValueError(
            "invalid 3D coordinate walk inputs".to_string(),
        ));
    }
    let mut pts = Vec::with_capacity(pts_arr.len());
    for v in pts_arr {
        let arr = match v {
            JsonValue::Array(a) if a.len() == 3 => a,
            _ => {
                return Err(CoreError::ValueError(
                    "point must be [x, y, z]".to_string(),
                ))
            }
        };
        pts.push((
            parse_i64_elem(&arr[0], "x")?,
            parse_i64_elem(&arr[1], "y")?,
            parse_i64_elem(&arr[2], "z")?,
        ));
    }

    let n_steps = pts.len() - 1;
    let beta_u = beta_a as usize;
    let mut phase_counts = vec![0i64; beta_u];
    let mut octant_counts = vec![0i64; 8];
    let mut q_vals = Vec::with_capacity(n_steps);
    let mut sum_q = 0i64;

    for i in 0..n_steps {
        let dx = pts[i + 1].0 - pts[i].0;
        let dy = pts[i + 1].1 - pts[i].1;
        let dz = pts[i + 1].2 - pts[i].2;
        let q_i = dx * dx + dy * dy + dz * dz;
        let th = (q_i.rem_euclid(beta_a)) as usize;
        let oc = octant_3d(dx, dy, dz);
        q_vals.push(q_i);
        sum_q += q_i;
        phase_counts[th] += 1;
        octant_counts[oc] += 1;
    }

    let n_i64 = n_steps as i64;
    let base_q = n_i64 / 8;
    let rem_q = (n_i64 % 8) as usize;
    let mut m_oct = 0i64;
    for q in 0..8usize {
        let comp = base_q + if q < rem_q { 1 } else { 0 };
        m_oct += (comp - octant_counts[q]).abs();
    }

    let base_th = n_i64 / beta_a;
    let rem_th = (n_i64 % beta_a) as usize;
    let mut m_th = 0i64;
    for th in 0..beta_u {
        let comp = base_th + if th < rem_th { 1 } else { 0 };
        m_th += (comp - phase_counts[th]).abs();
    }

    let rq = BigRat::from_i64_pair(sum_q, n_i64)?;

    let mut out = BTreeMap::new();
    out.insert("step_count".to_string(), int_json(n_i64));
    out.insert(
        "Q_values".to_string(),
        JsonValue::Array(q_vals.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert("sum_Q".to_string(), int_json(sum_q));
    out.insert("R_Q_ratio".to_string(), pair_json(&rq));
    out.insert(
        "phase_counts".to_string(),
        JsonValue::Array(phase_counts.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert("phase_delta3_M".to_string(), int_json(m_th));
    out.insert(
        "octant_counts".to_string(),
        JsonValue::Array(octant_counts.iter().map(|&v| int_json(v)).collect()),
    );
    out.insert("octant_delta3_M".to_string(), int_json(m_oct));
    Ok(JsonValue::Object(out))
}
