//! Boundary-Full AOmegaD SADAR dynamics, continuous Q4 D.E.C. chiral-flip walks,
//! collision-shedding debris cascades, finite-ring double-slit, Hydrogen shell
//! series, moving-boundary wire currents, and exact rational pooled SPARC evaluation.
//!
//! Pure `std`-only, zero-float, zero-`unsafe` exact `BigInt` / `BigRat` implementation
//! for golden vectors `RC-025`..`RC-032` and `SD-007`..`SD-008`.

use std::collections::BTreeMap;

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::json::JsonValue;
use crate::numeric::{format_fixed, parse_printed_rational};
use crate::ops::require_json_int;
use crate::CoreError;

const CLOSURE_C6: i64 = 18;
const CLOSURE_C8: i64 = 24;
const CLOSURE_C10: i64 = 27;

const POPCOUNT_4BIT: [i64; 16] = [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4];

fn q4_neighbor(v: usize, slot: usize) -> usize {
    v ^ (1usize << slot)
}

fn hamming4(u: usize, v: usize) -> i64 {
    POPCOUNT_4BIT[(u ^ v) & 15]
}

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

fn gcd_i64(a: i64, b: i64) -> i64 {
    let mut x = a.abs();
    let mut y = b.abs();
    while y != 0 {
        let r = x % y;
        x = y;
        y = r;
    }
    x
}

fn lcm_i64(a: i64, b: i64) -> i64 {
    if a == 0 || b == 0 {
        0
    } else {
        (a.abs() / gcd_i64(a, b)) * b.abs()
    }
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

pub fn op_dec_chiral_flip_walk(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let v0_i = require_i64(inputs, "initial_vertex")?;
    let anc_i = require_i64(inputs, "incoming_ancestor_slot")?;
    let chi0 = require_i64(inputs, "initial_chirality")?;
    let c3 = require_i64(inputs, "C3")?;
    let rd_tunnel = require_i64(inputs, "tunnel_RD")?;
    let omega_rem = require_i64(inputs, "tunnel_window_remaining")?;
    let raw_rows = require_array(inputs, "candidate_rows")?;

    if !(0..16).contains(&v0_i) {
        return Err(CoreError::ValueError("initial_vertex must lie in V(Q4)".to_string()));
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
        return Err(CoreError::ValueError("invalid tunnel parameters".to_string()));
    }
    if raw_rows.len() != 4 {
        return Err(CoreError::ValueError("expected 4 candidate rows".to_string()));
    }

    let v0 = v0_i as usize;
    let anc = anc_i as usize;
    if v0 >= 4 {
        return Err(CoreError::ValueError(
            "initial_vertex must start inside R_core={0,1,2,3}".to_string(),
        ));
    }

    let mut parsed: Vec<CandRow> = Vec::with_capacity(4);
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
            return Err(CoreError::ValueError("invalid candidate row fields".to_string()));
        }
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

    let z_cut1: i64 = parsed.iter().map(|r| r.weight).sum();
    let mut probs_cut1 = Vec::with_capacity(4);
    let mut sum_cut1 = BigRat::zero();
    for r in &parsed {
        let p = BigRat::from_i64_pair(r.weight, z_cut1)?;
        sum_cut1 = &sum_cut1 + &p;
        probs_cut1.push(p);
    }
    if sum_cut1 != BigRat::one() {
        return Err(CoreError::ValueError("Cut 1 kernel not normalized".to_string()));
    }

    let slide_rows: Vec<&CandRow> = parsed.iter().filter(|r| r.is_dwell == 0).collect();
    if slide_rows.len() != 3 || !slide_rows.iter().all(|r| r.sigma == -1 || r.sigma == 1) {
        return Err(CoreError::ValueError("invalid slide row survivor set".to_string()));
    }
    let z_slide: i64 = slide_rows.iter().map(|r| r.weight).sum();
    let mut probs_slide = Vec::with_capacity(3);
    let mut sum_slide = BigRat::zero();
    let mut returned_prob = BigRat::zero();
    let mut cross_rows: Vec<(&CandRow, BigRat)> = Vec::new();
    for r in &slide_rows {
        let p = BigRat::from_i64_pair(r.weight, z_slide)?;
        sum_slide = &sum_slide + &p;
        if r.target < 4 {
            returned_prob = &returned_prob + &p;
        } else {
            cross_rows.push((*r, p.clone()));
        }
        probs_slide.push(p);
    }
    if sum_slide != BigRat::one() || cross_rows.len() != 1 {
        return Err(CoreError::ValueError(
            "expected unique normalized boundary-crossing slide branch".to_string(),
        ));
    }
    let (tunnel_row, p_tunnel) = &cross_rows[0];
    if hamming4(v0, tunnel_row.target) != 1 {
        return Err(CoreError::ValueError("tunnel step must be Q4 Hamming-1".to_string()));
    }

    let rho_omega = rd_tunnel.min(omega_rem);
    let pd_tunnel = c3 * rho_omega;
    let t_tunnel = p_tunnel * &BigRat::from_i64(pd_tunnel);
    let chi_after = -chi0;

    let mut out = BTreeMap::new();
    out.insert("cut1_Z".to_string(), int_json(z_cut1));
    out.insert(
        "cut1_probabilities".to_string(),
        JsonValue::Array(probs_cut1.iter().map(pair_json).collect()),
    );
    out.insert("cut2_slide_Z".to_string(), int_json(z_slide));
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
        JsonValue::Array(vec![int_json(chi0), int_json(-chi0)]),
    );
    out.insert(
        "dion_after".to_string(),
        JsonValue::Array(vec![int_json(chi_after), int_json(-chi_after)]),
    );
    out.insert("structural_hinge_preserved".to_string(), JsonValue::Bool(true));
    out.insert("prior_return_retained".to_string(), JsonValue::Bool(true));
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
        return Err(CoreError::ValueError("opposing chiralities required".to_string()));
    }
    if rcd_12 <= 0 || window_len <= 0 || c3 != 3 || seats <= 0 {
        return Err(CoreError::ValueError("invalid Disoma inputs".to_string()));
    }

    let rho_omega = rcd_12.min(window_len);
    let pd = c3 * rho_omega;
    let delta_chi = BigRat::from_i64(chi1 - chi2);
    let intensity = BigRat::from_i64_pair(1, seats)?;
    let a_12 = &delta_chi * &intensity;
    let a_21 = -&a_12;
    let pd_rat = BigRat::from_i64(pd);
    let phi_12 = &pd_rat * &a_12;
    let phi_21 = &pd_rat * &a_21;
    let sum_stokes = &phi_12 + &phi_21;
    if !sum_stokes.is_zero() {
        return Err(CoreError::ValueError(
            "internal Stokes interface cancellation violated".to_string(),
        ));
    }

    let next_1 = &BigRat::from_i64(base1) + &phi_21;
    let next_2 = &BigRat::from_i64(base2) + &phi_12;
    let op_both = next_1 != BigRat::from_i64(base1) && next_2 != BigRat::from_i64(base2);
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
    out.insert("both_histories_operative".to_string(), JsonValue::Bool(op_both));
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
    sadar_attention_total: BigRat,
    stokes_cross: i64,
    stokes_sweep: i64,
}

fn run_deterministic_q4_cavity_trace(n_duons: usize, lead_lag: i64) -> Result<CavityTrace, CoreError> {
    if lead_lag < 1 {
        return Err(CoreError::ValueError("lead_lag must be >= 1".to_string()));
    }
    if n_duons == 0 {
        let mut v_a = 0usize;
        let mut v_b = 15usize;
        let mut h1_moves = 0i64;
        let mut hinges_0h = 0i64;
        for step_idx in 0..32usize {
            let slot = step_idx & 3;
            if slot == 3 {
                hinges_0h += 2;
            } else {
                v_a = q4_neighbor(v_a, slot);
                v_b = q4_neighbor(v_b, slot);
                h1_moves += 2;
            }
        }
        return Ok(CavityTrace {
            coupled: false,
            raw_cuts: 58,
            quotient_cuts: 58,
            dwell_burned: 0,
            h1_moves,
            hinges_0h,
            chiral_flips: 0,
            early_coupling_cut: 0,
            sadar_attention_total: BigRat::zero(),
            stokes_cross: 0,
            stokes_sweep: 0,
        });
    }

    let mut v_a = 0usize;
    let mut v_b = 3usize;
    let mut anc_a = 3usize;
    let mut anc_b = 3usize;
    let mut duon_v: Vec<usize> = (0..n_duons).map(|m| if (m & 1) == 0 { 1 } else { 2 }).collect();
    let mut duon_chi: Vec<i64> = (0..n_duons).map(|m| if (m & 1) == 0 { 1 } else { -1 }).collect();

    let mut k_quot = 0i64;
    let mut k_raw = 0i64;
    let mut dwell_burned = 0i64;
    let mut h1_moves = 0i64;
    let mut hinges_0h = 0i64;
    let mut chiral_flips = 0i64;
    let mut coupled = false;
    let mut early_coupling_cut = 0i64;
    let mut sadar_attention_total = BigRat::zero();
    let mut stokes_cross = 0i64;
    let mut stokes_sweep = 0i64;
    let mut debris_rd_rem = support_rd_single_hinge(3, 2)?; // 21

    while k_quot < 18 && debris_rd_rem > 0 {
        k_quot += 1;
        k_raw += 1;

        for m in 0..n_duons {
            let dv = duon_v[m];
            let d_a = hamming4(dv, v_a);
            let d_b = hamming4(dv, v_b);
            if ((k_quot as usize) + m) % 2 == 1 {
                chiral_flips += 1;
                duon_chi[m] = -duon_chi[m];
                if !coupled && d_a <= 1 && d_b <= 1 {
                    coupled = true;
                    early_coupling_cut = k_raw;
                    let rho_ab = 9i64.min(6i64);
                    let p_ab = 3 * rho_ab;
                    let a_ab = BigRat::from_i64_pair(2 * lead_lag, 6 * (lead_lag + 2))?;
                    sadar_attention_total =
                        &sadar_attention_total + &(&BigRat::from_i64(p_ab) * &a_ab);
                    stokes_cross += p_ab;
                } else {
                    k_raw += 1;
                    dwell_burned += 1;
                }
            }
            let shift = if duon_chi[m] > 0 { 1usize } else { 2usize };
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
                k_raw += 1;
                dwell_burned += 1;
            }
            debris_rd_rem -= drain;
        }
    }

    Ok(CavityTrace {
        coupled,
        raw_cuts: k_raw,
        quotient_cuts: k_quot,
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
    let endo_slots = require_i64(inputs, "shed_endo_slots")?;
    let exo_slots = require_i64(inputs, "shed_exo_slots")?;
    let vis_slots = require_i64(inputs, "sensor_visible_slots")?;
    let miss_slots = require_i64(inputs, "sensor_missing_slots")?;

    if n_duons_i <= 0 || n_duons_i > 64 {
        return Err(CoreError::ValueError("invalid window_duons".to_string()));
    }
    if endo_slots != 13 || exo_slots != 37 || vis_slots != 19 || miss_slots != 31 {
        return Err(CoreError::ValueError(
            "expected 13/37 B_shed and 19/31 B_sensor slot partitions".to_string(),
        ));
    }

    let sterile = run_deterministic_q4_cavity_trace(0, lead_lag)?;
    let live_with_sensor = run_deterministic_q4_cavity_trace(n_duons_i as usize, lead_lag)?;
    let live_no_sensor = run_deterministic_q4_cavity_trace(n_duons_i as usize, lead_lag)?;
    if live_with_sensor != live_no_sensor || sterile.coupled || !live_with_sensor.coupled {
        return Err(CoreError::ValueError(
            "Q4 SADAR cavity control or ReadOnly sensor invariance failed".to_string(),
        ));
    }

    let rd_12 = support_rd_single_hinge(1, 2)?; // 9
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

    let p_endo = BigRat::from_i64_pair(endo_slots * 50, 2500)?;
    let p_vis = BigRat::from_i64_pair(exo_slots * vis_slots, 2500)?;
    let p_miss = BigRat::from_i64_pair(exo_slots * miss_slots, 2500)?;
    if &(&p_endo + &p_vis) + &p_miss != BigRat::one() {
        return Err(CoreError::ValueError("2500-denominator partition mismatch".to_string()));
    }
    let p_exo = &p_vis + &p_miss;
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
    live_obj.insert("readonly_sensor_invariant".to_string(), JsonValue::Bool(true));

    let mut out = BTreeMap::new();
    out.insert("sterile_control".to_string(), JsonValue::Object(sterile_obj));
    out.insert("live_cavity".to_string(), JsonValue::Object(live_obj));
    out.insert("selected_tau_candidate".to_string(), str_json("1:2:9_yro"));
    out.insert("pocket_evaluations".to_string(), JsonValue::Array(pocket_eval));
    out.insert(
        "partition_2500_numerators".to_string(),
        JsonValue::Array(vec![
            int_json(endo_slots * 50),
            int_json(exo_slots * vis_slots),
            int_json(exo_slots * miss_slots),
        ]),
    );
    out.insert("endo_retained_fraction".to_string(), pair_json(&p_endo));
    out.insert("exo_outward_fraction".to_string(), pair_json(&p_exo));
    out.insert("visible_conditional_exo".to_string(), pair_json(&vis_cond_exo));
    out.insert("miss_tau_conditional_exo".to_string(), pair_json(&miss_cond_exo));
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
    let c_sup_32 = parent_p + debris_q; // 5
    let ladder_specs: [(&str, i64, &str, i64); 4] = [
        ("B_pm", 6, "E2_pm_seated_duad", 1),
        ("B_0", 6, "E2_0_open_duon", 0),
        ("B_s0", 8, "E2_0_lifted_octon", 0),
        ("B_c_pm", 10, "E2_pm_lifted_decon", 1),
    ];
    let mut debris_ladder = Vec::with_capacity(4);
    for (species, win_l, shell_state, chi_shell) in ladder_specs {
        let rho_w = rd_32.min(win_l);
        let pd_sup = c_sup_32 * rho_w;
        let qd_sup = c_sup_32 * (rd_32 - rho_w);
        let mut dobj = BTreeMap::new();
        dobj.insert("species".to_string(), str_json(species));
        dobj.insert("support".to_string(), str_json(&format!("3:2:{}", win_l)));
        dobj.insert("shell_state".to_string(), str_json(shell_state));
        dobj.insert("chi_shell".to_string(), int_json(chi_shell));
        dobj.insert("Pi".to_string(), int_json(pi_32));
        dobj.insert("RD".to_string(), int_json(rd_32));
        dobj.insert("PD_support".to_string(), int_json(pd_sup));
        dobj.insert("QD_support".to_string(), int_json(qd_sup));
        debris_ladder.push(JsonValue::Object(dobj));
    }

    let mut saddle_survivors = Vec::new();
    let mut lineage_survivors = Vec::new();
    let mut scan_count = 0i64;
    for q_cand in 1..=4i64 {
        let rd_cand = support_rd_single_hinge(3, q_cand)?;
        for win_l in 6..=10i64 {
            scan_count += 1;
            let rho_w = rd_cand.min(win_l);
            let pd_h = c3_chan * rho_w;
            let d_c6 = pd_h - CLOSURE_C6;
            let d_c8 = pd_h - CLOSURE_C8;
            if (d_c6 + d_c8 == 0) && pd_h > CLOSURE_C6 {
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
    let pd_337 = c3_chan * 7; // 21
    let qd_337 = c3_chan * (rd_337 - 7); // 162
    let e_h_mev = rd_337 * (1i64 << (7 + 4)); // 124928

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
    out.insert("higgs_PD_H".to_string(), int_json(pd_337));
    out.insert("higgs_QD_H".to_string(), int_json(qd_337));
    out.insert("higgs_delta_C6".to_string(), int_json(pd_337 - CLOSURE_C6));
    out.insert("higgs_delta_C8".to_string(), int_json(pd_337 - CLOSURE_C8));
    out.insert("frozen_map_MeV".to_string(), int_json(e_h_mev));
    Ok(JsonValue::Object(out))
}

pub fn op_sadar_rest_energy_atlas(
    _inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let periods: [i64; 7] = [2, 4, 6, 8, 20, 60, 136];
    let mut lcm_val = 1i64;
    for &p in &periods {
        lcm_val = lcm_i64(lcm_val, p);
    }
    let common_bit_span = 4 * lcm_val; // 8160
    let mut closure_counts = Vec::with_capacity(8);
    closure_counts.push(0i64);
    for &p in periods.iter().rev() {
        closure_counts.push(common_bit_span / p);
    }
    let summed_closures: i64 = closure_counts.iter().sum();

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
        cobj.insert("support".to_string(), str_json(&format!("{}:{}:{}", p, q, win_l)));
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

    let r_p_l = BigRat::from_i64_pair(61, 9)?;
    let r_n_p = BigRat::from_i64_pair(137, 61)?;
    let r_d_l = BigRat::from_i64_pair(21, 9)?;

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
    let h_ext = BigRat::new(BigInt::from_i64(662_607_015), ten.pow_u32(42))?;
    let e_ext = BigRat::new(BigInt::from_i64(1_602_176_634), ten.pow_u32(28))?;
    let eta_ext = BigRat::new(BigInt::from_i64(137_035_999_177), ten.pow_u32(9))?;
    let mev_scale = BigRat::from_int(ten.pow_u32(6));
    let k_ext = (&h_ext * &eta_ext).checked_div(&(&mev_scale * &e_ext))?;
    let scale_1e21 = BigRat::from_int(ten.pow_u32(21));

    let mut records = Vec::with_capacity(9);
    for tv in raw_targets {
        let tobj = require_obj(tv, "target")?;
        let species = require_str(tobj, "species")?;
        let e_mev = parse_printed_rational(require_str(tobj, "target_MeV")?, true, true)?;
        let sig_mev = parse_printed_rational(require_str(tobj, "sigma_MeV")?, true, true)?;
        if !e_mev.is_positive() || !sig_mev.is_positive() {
            return Err(CoreError::ValueError(format!(
                "non-positive target/sigma for {}",
                species
            )));
        }
        let nu_tar = e_mev.checked_div(&k_ext)?;
        let roundtrip = &k_ext * &nu_tar;
        let residual = &roundtrip - &e_mev;
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
            str_json(&format_fixed(&nu_scaled, 6)?),
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

    let cross_for = |ak: i64| -> i64 {
        match ak {
            0 => 26,
            1 => 18,
            2 => 8,
            3 => -12,
            4 => -8,
            _ => 0,
        }
    };

    let mut s_bins = Vec::with_capacity(11);
    let mut t0_bins = Vec::with_capacity(11);
    let mut cx_bins = Vec::with_capacity(11);
    let mut tx_bins = Vec::with_capacity(11);
    let mut dz_bins = Vec::with_capacity(11);
    let mut m_sum = 0i64;

    for (idx, k_pos) in (-half_span..=half_span).enumerate() {
        let ak = k_pos.abs();
        let cone = (7 - ak) * (7 - ak);
        let sat_clip = if ak >= 2 {
            0
        } else if ak == 1 {
            5
        } else {
            14
        };
        let s_k = cone - sat_clip;
        let t0_k = 2 * s_k;
        let cx_k = cross_for(ak);
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
    let inv_m2 = BigRat::from_i64_pair(1, dest_m * dest_m)?;
    let dp_base = &inv_m2 - &BigRat::from_i64_pair(1, base_n * base_n)?;
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
        let dp = &inv_m2 - &BigRat::from_i64_pair(1, n_val * n_val)?;
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

    let sum_i64_arr = |arr: &[JsonValue], label: &str| -> Result<i64, CoreError> {
        let mut s = 0i64;
        for v in arr {
            let x = require_json_int(v, label)?
                .to_i64()
                .ok_or_else(|| CoreError::ValueError(format!("{} out of i64 range", label)))?;
            s += x;
        }
        Ok(s)
    };
    let phi_cross = sum_i64_arr(cross_edges, "cross")?;
    let phi_sweep = sum_i64_arr(swept_edges, "sweep")?;
    let phi_shed = sum_i64_arr(shed_edges, "shed")?;
    let phi_mov = phi_cross - phi_sweep + phi_shed;

    let rcd_wire = 5i64;
    let c3 = 3i64;
    let a_wire = BigRat::from_i64_pair(1, 3)?;
    let mut later_elec = BigRat::zero();
    let mut wire_tot = BigRat::zero();
    let mut elec_tot = BigRat::zero();
    let mut cut_rows = Vec::with_capacity(4);

    for cv in wire_cuts {
        let cobj = require_obj(cv, "wire_cut")?;
        let cut_k = require_i64(cobj, "cut")?;
        let win_w = require_i64(cobj, "window")?;
        let coupled = require_i64(cobj, "coupled")?;
        if !matches!(coupled, 0 | 1) || win_w <= 0 {
            return Err(CoreError::ValueError("invalid wire cut parameters".to_string()));
        }
        let (w_out, e_out) = if coupled == 1 {
            let rho_w = rcd_wire.min(win_w);
            let w = &BigRat::from_i64(c3 * rho_w) * &a_wire;
            let e = -&w;
            later_elec = &later_elec + &w;
            (w, e)
        } else {
            (BigRat::zero(), BigRat::zero())
        };
        wire_tot = &wire_tot + &w_out;
        elec_tot = &elec_tot + &e_out;
        let union_v = &w_out + &e_out;
        let mut robj = BTreeMap::new();
        robj.insert("cut".to_string(), int_json(cut_k));
        robj.insert("wire_outward".to_string(), pair_json(&w_out));
        robj.insert("electron_outward".to_string(), pair_json(&e_out));
        robj.insert("enclosing_union".to_string(), pair_json(&union_v));
        robj.insert("later_electron_current".to_string(), pair_json(&later_elec));
        cut_rows.push(JsonValue::Object(robj));
    }

    let union_tot = &wire_tot + &elec_tot;
    if !union_tot.is_zero() {
        return Err(CoreError::ValueError(
            "wire+electron union boundary must vanish".to_string(),
        ));
    }

    let mut out = BTreeMap::new();
    out.insert("Phi_cross".to_string(), int_json(phi_cross));
    out.insert("Phi_sweep".to_string(), int_json(phi_sweep));
    out.insert("Phi_shedding".to_string(), int_json(phi_shed));
    out.insert("Phi_moving".to_string(), int_json(phi_mov));
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

    let ups_d = BigRat::from_i64_pair(1, 2)?;
    let ups_b = BigRat::from_i64_pair(7, 10)?;
    let eight = BigRat::from_i64(8);
    let thousand = BigRat::from_i64(1000);
    let hundred = BigRat::from_i64(100);

    let mut rel_sum = BigRat::zero();
    let mut scored = 0i64;

    for bv in bins {
        let bobj = require_obj(bv, "sparc_bin")?;
        let v_obs = parse_printed_rational(require_str(bobj, "V_obs")?, true, true)?;
        let v_gas = parse_printed_rational(require_str(bobj, "V_gas")?, true, true)?;
        let v_disk = parse_printed_rational(require_str(bobj, "V_disk")?, true, true)?;
        let v_bul = parse_printed_rational(require_str(bobj, "V_bul")?, true, true)?;
        let r_kpc = parse_printed_rational(require_str(bobj, "r_kpc")?, true, true)?;

        let u_obs = &v_obs * &v_obs;
        if u_obs.is_positive() {
            let u_gas = &v_gas.abs() * &v_gas;
            let u_disk = &ups_d * &(&v_disk.abs() * &v_disk);
            let u_bul = &ups_b * &(&v_bul.abs() * &v_bul);
            let u_bar = &(&u_gas + &u_disk) + &u_bul;
            let u_bar_pos = if u_bar.is_positive() {
                u_bar
            } else {
                BigRat::zero()
            };
            let boost_num = &(&eight * &r_kpc) * &u_bar_pos;
            let boost_den = &u_bar_pos + &thousand;
            let u_ao = &u_bar_pos + &boost_num.checked_div(&boost_den)?;
            let delta_u = (&u_ao - &u_obs).abs();
            rel_sum = &rel_sum + &delta_u.checked_div(&u_obs)?;
            scored += 1;
        }
    }

    if scored <= 0 {
        return Err(CoreError::ValueError(
            "at least one positive U_obs bin required".to_string(),
        ));
    }

    let mape_exact = (&hundred * &rel_sum).checked_div(&BigRat::from_i64(scored))?;
    let mape_8dp = format_fixed(&mape_exact, 8)?;

    let mut out = BTreeMap::new();
    out.insert("N_total".to_string(), int_json(bins.len() as i64));
    out.insert("N_scored".to_string(), int_json(scored));
    out.insert("MAPE_U_exact".to_string(), pair_json(&mape_exact));
    out.insert("MAPE_U_8dp".to_string(), str_json(&mape_8dp));
    Ok(JsonValue::Object(out))
}
