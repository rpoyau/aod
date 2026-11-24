//! All 34 positive golden-vector operations, 3 typed REJECT boundary controls,
//! and the reusable exact 90-tick `cycle_shedding_trace` evaluator.
//!
//! Every operation computes results mathematically from first principles using
//! `BigInt`, `BigRat`, `GaussianRat`, and `Cyclotomic12` with zero floats.

use std::collections::{BTreeMap, BTreeSet};

use crate::bigint::BigInt;
use crate::bigrat::BigRat;
use crate::json::{parse_json, JsonValue};
use crate::numeric::{
    format_fixed, parse_canonical_rational_pair, parse_exact_int_str, parse_printed_rational,
    round_half_even,
};
use crate::rings::{Cyclotomic12, GaussianRat};
use crate::sadar_sim::{
    op_dec_chiral_flip_walk, op_dec_two_carrier_chiral_stokes,
    op_frg_dimonhexon_double_slit_ring, op_hydrogen_shell_series_exact,
    op_sadar_hadron_debris_and_higgs_saddle, op_sadar_pp_tau_five_boundary,
    op_sadar_rest_energy_atlas, op_sadar_rest_energy_qext,
    op_scoped_wire_and_moving_boundary, op_sparc_pooled_primary_exact,
};
use crate::CoreError;

const MAX_EXPONENT_GUARD: u32 = 10_000;
const MAX_WIDTH_GUARD: usize = 10_000;
const MAX_STEPS_GUARD: usize = 100_000;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CycleSheddingTickInput {
    pub lead: BigRat,
    pub lag: BigRat,
    pub compatibility: BigRat,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CycleSheddingStepResult {
    pub span: BigRat,
    pub before_clipping: BigRat,
    pub shed_excess: BigRat,
    pub padar_burden: BigRat,
    pub outward_shedding: BigRat,
    pub local_reclosure: BigRat,
    pub remainder_sum: BigRat,
}

/// Exact single-tick cycle-shedding recurrence in `BigRat`.
pub fn cycle_shedding_step_exact(
    prev_burden: &BigRat,
    lead: &BigRat,
    lag: &BigRat,
    compatibility: &BigRat,
    eta: &BigRat,
    gamma: &BigRat,
    lambda_reclose: &BigRat,
) -> CycleSheddingStepResult {
    let span = (lead - lag).abs();
    let before_clipping = &(eta * prev_burden) + &(gamma * &span);
    let raw_exc = &before_clipping - compatibility;
    let shed_excess = if raw_exc.is_positive() {
        raw_exc
    } else {
        BigRat::zero()
    };
    let padar_burden = &before_clipping - &shed_excess;
    let one_minus_lam = &BigRat::one() - lambda_reclose;
    let outward_shedding = &one_minus_lam * &shed_excess;
    let local_reclosure = lambda_reclose * &shed_excess;
    let remainder_sum = &outward_shedding + &local_reclosure;
    CycleSheddingStepResult {
        span,
        before_clipping,
        shed_excess,
        padar_burden,
        outward_shedding,
        local_reclosure,
        remainder_sum,
    }
}

/// Exact multi-tick chained cycle-shedding trace (arbitrary-precision `BigRat`, no overflow across 90+ ticks).
pub fn cycle_shedding_trace(
    initial_burden: &BigRat,
    ticks: &[CycleSheddingTickInput],
    eta: &BigRat,
    gamma: &BigRat,
    lambda_reclose: &BigRat,
) -> Vec<CycleSheddingStepResult> {
    let mut prev = initial_burden.clone();
    let mut out = Vec::with_capacity(ticks.len());
    for tick in ticks {
        let step = cycle_shedding_step_exact(
            &prev,
            &tick.lead,
            &tick.lag,
            &tick.compatibility,
            eta,
            gamma,
            lambda_reclose,
        );
        prev = step.padar_burden.clone();
        out.push(step);
    }
    out
}

// ---------------------------------------------------------------------------
// Typed JSON extraction & canonical encoding helpers
// ---------------------------------------------------------------------------

fn pair_json(q: &BigRat) -> JsonValue {
    let [n, d] = q.canonical_pair();
    JsonValue::Array(vec![JsonValue::Str(n), JsonValue::Str(d)])
}

fn get_field<'a>(
    obj: &'a BTreeMap<String, JsonValue>,
    key: &str,
) -> Result<&'a JsonValue, CoreError> {
    obj.get(key)
        .ok_or_else(|| CoreError::ValueError(format!("missing required input field {:?}", key)))
}

pub fn require_json_int<'a>(val: &'a JsonValue, name: &str) -> Result<&'a BigInt, CoreError> {
    match val {
        JsonValue::Int(i) => Ok(i),
        other => Err(CoreError::TypeError(format!(
            "{} must be an exact int (excluding bool), got {}",
            name,
            other.type_name()
        ))),
    }
}

pub fn parse_json_exact_int(val: &JsonValue, name: &str) -> Result<BigInt, CoreError> {
    match val {
        JsonValue::Int(i) => Ok(i.clone()),
        JsonValue::Str(s) => parse_exact_int_str(s, false),
        other => Err(CoreError::TypeError(format!(
            "{} must be an exact int or canonical integer str, got {}",
            name,
            other.type_name()
        ))),
    }
}

fn require_json_str<'a>(val: &'a JsonValue, name: &str) -> Result<&'a str, CoreError> {
    match val {
        JsonValue::Str(s) => Ok(s.as_str()),
        other => Err(CoreError::TypeError(format!(
            "{} must be a string, got {}",
            name,
            other.type_name()
        ))),
    }
}

fn require_json_array<'a>(val: &'a JsonValue, name: &str) -> Result<&'a [JsonValue], CoreError> {
    match val {
        JsonValue::Array(v) => Ok(v.as_slice()),
        other => Err(CoreError::TypeError(format!(
            "{} must be a JSON array, got {}",
            name,
            other.type_name()
        ))),
    }
}

fn require_json_object<'a>(
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

pub fn parse_canonical_rational_pair_json(
    val: &JsonValue,
    name: &str,
) -> Result<BigRat, CoreError> {
    let arr = match val {
        JsonValue::Array(v) if v.len() == 2 => v,
        _ => {
            return Err(CoreError::TypeError(format!(
                "{} must be a 2-element array of canonical integer strings",
                name
            )));
        }
    };
    let num_s = match &arr[0] {
        JsonValue::Str(s) => s.as_str(),
        _ => {
            return Err(CoreError::TypeError(format!(
                "{} entries must be canonical integer strings",
                name
            )));
        }
    };
    let den_s = match &arr[1] {
        JsonValue::Str(s) => s.as_str(),
        _ => {
            return Err(CoreError::TypeError(format!(
                "{} entries must be canonical integer strings",
                name
            )));
        }
    };
    parse_canonical_rational_pair(num_s, den_s)
}

fn parse_pair_or_printed_decimal_json(val: &JsonValue, name: &str) -> Result<BigRat, CoreError> {
    match val {
        JsonValue::Array(_) => parse_canonical_rational_pair_json(val, name),
        JsonValue::Str(s) => parse_printed_rational(s, false, false),
        other => Err(CoreError::TypeError(format!(
            "{} must be a canonical rational pair or decimal string, got {}",
            name,
            other.type_name()
        ))),
    }
}

fn int_balance(n: usize, k: usize) -> Vec<BigInt> {
    let base = n / k;
    let rem = n % k;
    (0..k)
        .map(|idx| BigInt::from_usize(base + usize::from(idx < rem)))
        .collect()
}

fn require_u32_exp(val: &BigInt, name: &str) -> Result<u32, CoreError> {
    let exp = val.to_u32().ok_or_else(|| {
        CoreError::ValueError(format!("{} must be a nonnegative u32 integer", name))
    })?;
    if exp > MAX_EXPONENT_GUARD {
        return Err(CoreError::ValueError(format!(
            "{} exceeds guard {}",
            name, MAX_EXPONENT_GUARD
        )));
    }
    Ok(exp)
}

fn sum_rats(iter: impl IntoIterator<Item = BigRat>) -> BigRat {
    iter.into_iter().fold(BigRat::zero(), |acc, x| &acc + &x)
}

fn eval_phase_advance(rec: &BTreeMap<String, JsonValue>) -> Result<BigRat, CoreError> {
    let winding = require_json_int(get_field(rec, "winding")?, "winding")?;
    let a = parse_canonical_rational_pair_json(get_field(rec, "phase_start")?, "phase_start")?;
    let b = parse_canonical_rational_pair_json(get_field(rec, "phase_end")?, "phase_end")?;
    let zero = BigRat::zero();
    let one = BigRat::one();
    if a < zero || a >= one || b < zero || b >= one {
        return Err(CoreError::ValueError("phase out of [0,1)".to_string()));
    }
    Ok(&(&BigRat::from_int(winding.clone()) + &b) - &a)
}

// ---------------------------------------------------------------------------
// Operation dispatcher (24 positive golden operations + cycle_shedding_trace)
// ---------------------------------------------------------------------------

pub fn eval_operation(
    operation: &str,
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    match operation {
        "dec_normalize_one_node" => op_dec_normalize_one_node(inputs),
        "dec_hinge_slide_normalize" => op_dec_hinge_slide_normalize(inputs),
        "dec_field_tunnelling_window_clip" => op_dec_field_tunnelling_window_clip(inputs),
        "sadar_afc_flux_antisymmetry" => op_sadar_afc_flux_antisymmetry(inputs),
        "q4_hamming_and_neighbors" => op_q4_hamming_and_neighbors(inputs),
        "closure_wave_rd_rcd" => op_closure_wave_rd_rcd(inputs),
        "relational_cadence_and_lag" => op_relational_cadence_and_lag(inputs),
        "finite_stokes_cut_balance" => op_finite_stokes_cut_balance(inputs),
        "awareness_current_update" => op_awareness_current_update(inputs),
        "awareness_mindfulness_step" => op_awareness_mindfulness_step(inputs),
        "higgs_trace_score_and_freeze" => op_higgs_trace_score_and_freeze(inputs),
        "brownian_3d_delta3_msb_x" => op_brownian_3d_delta3_msb_x(inputs),
        "run_tumble_3d_delta3_lsb_x" => op_run_tumble_3d_delta3_lsb_x(inputs),
        "cycle_shedding_step" => op_cycle_shedding_step(inputs),
        "cycle_shedding_trace" => op_cycle_shedding_trace(inputs),
        "sparc_exact_bin_eval" => op_sparc_exact_bin_eval(inputs),
        "temporal_metrology_phase_si" => op_temporal_metrology_phase_si(inputs),
        "temporal_metrology_signed_advance" => op_temporal_metrology_signed_advance(inputs),
        "temporal_metrology_hellwig_mean" => op_temporal_metrology_hellwig_mean(inputs),
        "lensing_swells_delta3_and_tau_discrepancy" => {
            op_lensing_swells_delta3_and_tau_discrepancy(inputs)
        }
        "map21_nonlinear_finite_law_variance" => op_map21_nonlinear_finite_law_variance(inputs),
        "sympy_z4_dft" => op_sympy_z4_dft(inputs),
        "cyclotomic_z12_overtone" => op_cyclotomic_z12_overtone(inputs),
        "higgs_lhc_rounded_display" => op_higgs_lhc_rounded_display(inputs),
        "printed_token_half_ulp_enclosure" => op_printed_token_half_ulp_enclosure(inputs),
        "dec_chiral_flip_walk" => op_dec_chiral_flip_walk(inputs),
        "dec_two_carrier_chiral_stokes" => op_dec_two_carrier_chiral_stokes(inputs),
        "sadar_pp_tau_five_boundary" => op_sadar_pp_tau_five_boundary(inputs),
        "sadar_hadron_debris_and_higgs_saddle" => op_sadar_hadron_debris_and_higgs_saddle(inputs),
        "sadar_rest_energy_atlas" => op_sadar_rest_energy_atlas(inputs),
        "frg_dimonhexon_double_slit_ring" => op_frg_dimonhexon_double_slit_ring(inputs),
        "hydrogen_shell_series_exact" => op_hydrogen_shell_series_exact(inputs),
        "scoped_wire_and_moving_boundary" => op_scoped_wire_and_moving_boundary(inputs),
        "sadar_rest_energy_qext" => op_sadar_rest_energy_qext(inputs),
        "sparc_pooled_primary_exact" => op_sparc_pooled_primary_exact(inputs),
        _ => Err(CoreError::ValueError(format!(
            "unsupported vector operation: {:?}",
            operation
        ))),
    }
}

/// Execute one of the 3 typed REJECT negative-control vectors (`RC-021`, `RC-022`, `RC-023`).
pub fn verify_reject_operation(
    operation: &str,
    inputs: &BTreeMap<String, JsonValue>,
    expected_error_class: &str,
) -> Result<(), CoreError> {
    match operation {
        "typed_reject_float_operand" => {
            if expected_error_class != "TypeError" {
                return Err(CoreError::ValueError(
                    "RC-021 expects TypeError".to_string(),
                ));
            }
            let json_float_text =
                require_json_str(get_field(inputs, "json_float_text")?, "json_float_text")?;
            if !matches!(parse_json(json_float_text), Err(CoreError::FloatLiteral(_))) {
                return Err(CoreError::ValueError(
                    "zero-float JSON parser failed to reject JSON float literal".to_string(),
                ));
            }
            let dec_tok = require_json_str(
                get_field(inputs, "decimal_token_for_runtime_float")?,
                "decimal_token_for_runtime_float",
            )?;
            if !matches!(parse_json(dec_tok), Err(CoreError::FloatLiteral(_))) {
                return Err(CoreError::ValueError(
                    "zero-float JSON parser failed to reject standalone float token".to_string(),
                ));
            }
            if !matches!(parse_exact_int_str(dec_tok, false), Err(CoreError::ValueError(_))) {
                return Err(CoreError::ValueError(
                    "parse_exact_int_str failed to reject decimal token".to_string(),
                ));
            }
            let str_val = JsonValue::Str(dec_tok.to_string());
            if !matches!(
                require_json_int(&str_val, "probe"),
                Err(CoreError::TypeError(_))
            ) {
                return Err(CoreError::ValueError(
                    "require_json_int failed to reject non-int operand with TypeError".to_string(),
                ));
            }
            if !matches!(
                parse_canonical_rational_pair_json(&str_val, "probe"),
                Err(CoreError::TypeError(_))
            ) {
                return Err(CoreError::ValueError(
                    "parse_canonical_rational_pair_json failed to reject non-pair with TypeError"
                        .to_string(),
                ));
            }
            Ok(())
        }
        "typed_reject_bool_as_int" => {
            if expected_error_class != "TypeError" {
                return Err(CoreError::ValueError(
                    "RC-022 expects TypeError".to_string(),
                ));
            }
            let operand = get_field(inputs, "bool_operand")?;
            if operand.as_bool().is_none() {
                return Err(CoreError::ValueError(
                    "RC-022 requires JSON bool operand".to_string(),
                ));
            }
            if !matches!(
                require_json_int(operand, "bool_operand"),
                Err(CoreError::TypeError(_))
            ) {
                return Err(CoreError::ValueError(
                    "require_json_int failed to reject bool with TypeError".to_string(),
                ));
            }
            if !matches!(
                parse_json_exact_int(operand, "bool_operand"),
                Err(CoreError::TypeError(_))
            ) {
                return Err(CoreError::ValueError(
                    "parse_json_exact_int failed to reject bool with TypeError".to_string(),
                ));
            }
            if !matches!(
                parse_canonical_rational_pair_json(operand, "bool_operand"),
                Err(CoreError::TypeError(_))
            ) {
                return Err(CoreError::ValueError(
                    "parse_canonical_rational_pair_json failed to reject bool with TypeError"
                        .to_string(),
                ));
            }
            Ok(())
        }
        "typed_reject_nonfinite_and_malformed_tokens" => {
            if expected_error_class != "ValueError" {
                return Err(CoreError::ValueError(
                    "RC-023 expects ValueError".to_string(),
                ));
            }
            let tokens = require_json_array(get_field(inputs, "bad_tokens")?, "bad_tokens")?;
            if tokens.is_empty() {
                return Err(CoreError::ValueError(
                    "RC-023 requires non-empty bad_tokens".to_string(),
                ));
            }
            for tok_val in tokens {
                let tok = require_json_str(tok_val, "bad_token")?;
                if !matches!(
                    parse_printed_rational(tok, true, false),
                    Err(CoreError::ValueError(_))
                ) {
                    return Err(CoreError::ValueError(format!(
                        "parse_printed_rational failed to reject malformed token {:?}",
                        tok
                    )));
                }
            }
            Ok(())
        }
        _ => Err(CoreError::ValueError(format!(
            "unsupported REJECT vector operation: {:?}",
            operation
        ))),
    }
}

// ---------------------------------------------------------------------------
// Individual exact operations
// ---------------------------------------------------------------------------

fn op_dec_normalize_one_node(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let rows = require_json_array(get_field(inputs, "rows")?, "rows")?;
    if rows.len() != 4 {
        return Err(CoreError::ValueError(
            "dec_normalize_one_node expects 4 rows".to_string(),
        ));
    }
    let mut aw_list: Vec<BigInt> = Vec::with_capacity(4);
    let mut routes: Vec<JsonValue> = Vec::with_capacity(4);
    let mut seen_neighbors: BTreeSet<[BigInt; 4]> = BTreeSet::new();

    for row_val in rows {
        let row = require_json_object(row_val, "row")?;
        let adm = require_json_int(get_field(row, "admissible")?, "admissible")?;
        let wt = require_json_int(get_field(row, "weight")?, "weight")?;
        let st = require_json_int(get_field(row, "state")?, "state")?;
        let nbr = require_json_array(get_field(row, "neighbor")?, "neighbor")?;
        if nbr.len() != 4 {
            return Err(CoreError::ValueError("non-H1 Q4 neighbor".to_string()));
        }
        let mut coords = [BigInt::zero(), BigInt::zero(), BigInt::zero(), BigInt::zero()];
        let mut coord_sum = BigInt::zero();
        for (idx, item) in nbr.iter().enumerate() {
            let c = require_json_int(item, "neighbor_coord")?;
            if !c.is_zero() && !c.is_one() {
                return Err(CoreError::ValueError(
                    "neighbor must be a Q4 basis vector (exact {0,1} with Hamming weight 1)"
                        .to_string(),
                ));
            }
            coord_sum = &coord_sum + c;
            coords[idx] = c.clone();
        }
        if !coord_sum.is_one() {
            return Err(CoreError::ValueError(
                "neighbor must be a Q4 basis vector (exact {0,1} with Hamming weight 1)"
                    .to_string(),
            ));
        }
        seen_neighbors.insert(coords);
        let route = match st.to_i64() {
            Some(1) => "outgoing",
            Some(-1) => "returned",
            Some(0) => "hinge",
            _ => {
                return Err(CoreError::ValueError(format!(
                    "invalid state {} in dec_normalize_one_node",
                    st
                )));
            }
        };
        aw_list.push(adm * wt);
        routes.push(JsonValue::Str(route.to_string()));
    }
    if seen_neighbors.len() != 4 {
        return Err(CoreError::ValueError(
            "dec_normalize_one_node requires 4 distinct Q4 neighbors".to_string(),
        ));
    }
    let z_tot = aw_list.iter().fold(BigInt::zero(), |acc, x| &acc + x);
    let mut probs: Vec<BigRat> = Vec::with_capacity(4);
    for aw in &aw_list {
        probs.push(BigRat::new(aw.clone(), z_tot.clone())?);
    }
    let prob_sum = sum_rats(probs.iter().cloned());

    let mut out = BTreeMap::new();
    out.insert("Z".to_string(), JsonValue::Int(z_tot));
    out.insert(
        "probabilities".to_string(),
        JsonValue::Array(probs.iter().map(pair_json).collect()),
    );
    out.insert("sum".to_string(), pair_json(&prob_sum));
    out.insert("routes".to_string(), JsonValue::Array(routes));
    Ok(JsonValue::Object(out))
}

fn op_dec_hinge_slide_normalize(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let branches = require_json_array(get_field(inputs, "branches")?, "branches")?;
    if branches.is_empty() {
        return Err(CoreError::ValueError("branches required".to_string()));
    }
    let mut weights: Vec<BigRat> = Vec::with_capacity(branches.len());
    let mut routes: Vec<&str> = Vec::with_capacity(branches.len());
    for b_val in branches {
        let b = require_json_object(b_val, "branch")?;
        weights.push(parse_canonical_rational_pair_json(
            get_field(b, "weight")?,
            "weight",
        )?);
        routes.push(require_json_str(get_field(b, "route")?, "route")?);
    }
    let z_tot = sum_rats(weights.iter().cloned());
    let mut probs: Vec<BigRat> = Vec::with_capacity(weights.len());
    for w in &weights {
        probs.push(w.checked_div(&z_tot)?);
    }
    let mut sum_ret = BigRat::zero();
    let mut sum_out = BigRat::zero();
    for (route, p) in routes.iter().zip(probs.iter()) {
        if *route == "returned" {
            sum_ret = &sum_ret + p;
        } else if *route == "outgoing" {
            sum_out = &sum_out + p;
        }
    }
    let mut out = BTreeMap::new();
    out.insert("Z".to_string(), pair_json(&z_tot));
    out.insert(
        "probabilities".to_string(),
        JsonValue::Array(probs.iter().map(pair_json).collect()),
    );
    out.insert("sum_returned".to_string(), pair_json(&sum_ret));
    out.insert("sum_outgoing".to_string(), pair_json(&sum_out));
    Ok(JsonValue::Object(out))
}

fn op_dec_field_tunnelling_window_clip(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let direct_adm = require_json_int(get_field(inputs, "direct_adm")?, "direct_adm")?;
    if !direct_adm.is_zero() {
        return Err(CoreError::ValueError("direct_adm must be 0".to_string()));
    }
    let sw = parse_canonical_rational_pair_json(get_field(inputs, "slide_weight")?, "slide_weight")?;
    let z_val = parse_canonical_rational_pair_json(get_field(inputs, "Z")?, "Z")?;
    let rd_val = require_json_int(get_field(inputs, "RD")?, "RD")?;
    let omega = require_json_int(get_field(inputs, "omega")?, "omega")?;
    let c3 = require_json_int(get_field(inputs, "C3")?, "C3")?;

    let p_val = sw.checked_div(&z_val)?;
    let rho = rd_val.min(omega).clone();
    let pd_val = c3 * &rho;
    let tc = &p_val * &BigRat::from_int(pd_val.clone());

    let mut out = BTreeMap::new();
    out.insert("P".to_string(), pair_json(&p_val));
    out.insert("rhoD_omega".to_string(), JsonValue::Int(rho));
    out.insert("pD".to_string(), JsonValue::Int(pd_val));
    out.insert("tunnel_contribution".to_string(), pair_json(&tc));
    Ok(JsonValue::Object(out))
}

fn op_sadar_afc_flux_antisymmetry(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let mem_arr = require_json_array(get_field(inputs, "memory")?, "memory")?;
    let mat_arr = require_json_array(get_field(inputs, "matrix")?, "matrix")?;
    let n = mem_arr.len();
    if n == 0 || mat_arr.len() != n {
        return Err(CoreError::ValueError(
            "memory and matrix dimensions must match and be non-empty".to_string(),
        ));
    }
    let mut mem: Vec<BigRat> = Vec::with_capacity(n);
    for item in mem_arr {
        mem.push(parse_canonical_rational_pair_json(item, "memory")?);
    }
    if sum_rats(mem.iter().cloned()) != BigRat::one() {
        return Err(CoreError::ValueError("memory not normalized".to_string()));
    }
    let mut mat: Vec<Vec<BigRat>> = Vec::with_capacity(n);
    for row_val in mat_arr {
        let row_arr = require_json_array(row_val, "matrix_row")?;
        if row_arr.len() != n {
            return Err(CoreError::ValueError("matrix must be square".to_string()));
        }
        let mut row: Vec<BigRat> = Vec::with_capacity(n);
        for cell in row_arr {
            row.push(parse_canonical_rational_pair_json(cell, "matrix_cell")?);
        }
        if sum_rats(row.iter().cloned()) != BigRat::one() {
            return Err(CoreError::ValueError("matrix not stochastic".to_string()));
        }
        mat.push(row);
    }
    let mut flux: Vec<Vec<BigRat>> = Vec::with_capacity(n);
    for i in 0..n {
        let mut row: Vec<BigRat> = Vec::with_capacity(n);
        for j in 0..n {
            let f_ij = &(&mem[i] * &mat[i][j]) - &(&mem[j] * &mat[j][i]);
            row.push(f_ij);
        }
        flux.push(row);
    }
    let mut antisym = true;
    for i in 0..n {
        for j in 0..n {
            if flux[i][j] != -&flux[j][i] {
                antisym = false;
            }
        }
    }
    let flux_json = JsonValue::Array(
        flux.iter()
            .map(|row| JsonValue::Array(row.iter().map(pair_json).collect()))
            .collect(),
    );
    let mut out = BTreeMap::new();
    out.insert("flux".to_string(), flux_json);
    out.insert("antisymmetric".to_string(), JsonValue::Bool(antisym));
    Ok(JsonValue::Object(out))
}

fn op_q4_hamming_and_neighbors(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let v = require_json_int(get_field(inputs, "vertex")?, "vertex")?;
    let t = require_json_int(get_field(inputs, "target")?, "target")?;
    let w_int = require_json_int(get_field(inputs, "width")?, "width")?;
    let w = w_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("width must be a nonnegative integer".to_string())
    })?;
    if w > MAX_WIDTH_GUARD {
        return Err(CoreError::ValueError(format!(
            "width exceeds guard {}",
            MAX_WIDTH_GUARD
        )));
    }
    let limit = BigInt::one().shl_usize(w);
    if v.is_negative() || *v >= limit || t.is_negative() || *t >= limit {
        return Err(CoreError::ValueError("vertex out of Q_w range".to_string()));
    }
    let hd = v.bit_xor(t)?.bit_count();
    let mut neighbors = Vec::with_capacity(w);
    for slot in 0..w {
        let mask = BigInt::one().shl_usize(slot);
        neighbors.push(JsonValue::Int(v.bit_xor(&mask)?));
    }
    let mut out = BTreeMap::new();
    out.insert("hamming_distance".to_string(), JsonValue::Int(BigInt::from_usize(hd)));
    out.insert("is_h1_edge".to_string(), JsonValue::Bool(hd == 1));
    out.insert("neighbors".to_string(), JsonValue::Array(neighbors));
    Ok(JsonValue::Object(out))
}

fn op_closure_wave_rd_rcd(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let p_int = require_json_int(get_field(inputs, "p")?, "p")?;
    let p = require_u32_exp(p_int, "p")?;
    let q = require_json_int(get_field(inputs, "q")?, "q")?;
    let hinges = require_json_int(get_field(inputs, "hinges")?, "hinges")?;
    let refl_arr = require_json_array(get_field(inputs, "reflection_counts")?, "reflection_counts")?;
    let win = require_json_int(get_field(inputs, "window")?, "window")?;

    let mut refl_sum = BigInt::zero();
    for item in refl_arr {
        refl_sum = &refl_sum + require_json_int(item, "reflection_count")?;
    }
    let pi_v = &q.pow_u32(p) + q;
    let rd_v = &(&BigInt::from_i64(2) * &pi_v) + hinges;
    let dur = &rd_v + &refl_sum;
    let part = (&dur).min(win).clone();

    let mut out = BTreeMap::new();
    out.insert("Pi".to_string(), JsonValue::Int(pi_v));
    out.insert("RD".to_string(), JsonValue::Int(rd_v));
    out.insert("rcd_duration".to_string(), JsonValue::Int(dur));
    out.insert("participation".to_string(), JsonValue::Int(part));
    Ok(JsonValue::Object(out))
}

fn op_relational_cadence_and_lag(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let na = require_json_int(get_field(inputs, "na")?, "na")?;
    let nb = require_json_int(get_field(inputs, "nb")?, "nb")?;
    let bias = require_json_array(get_field(inputs, "bias")?, "bias")?;
    if bias.len() != 2 {
        return Err(CoreError::ValueError(
            "bias must be a 2-element array".to_string(),
        ));
    }
    let b0 = parse_canonical_rational_pair_json(&bias[0], "bias[0]")?;
    let b1 = parse_canonical_rational_pair_json(&bias[1], "bias[1]")?;
    let prior_lag = parse_canonical_rational_pair_json(get_field(inputs, "prior_lag")?, "prior_lag")?;

    let bias_diff = &b0 - &b1;
    let fwd_ratio = BigRat::new(na.clone(), nb.clone())?;
    let fwd_lag = &BigRat::from_int(na - nb) + &bias_diff;
    let fwd_drift = &fwd_lag - &prior_lag;

    let rev_ratio = BigRat::new(nb.clone(), na.clone())?;
    let rev_bias = -&bias_diff;
    let rev_lag = -&fwd_lag;
    let rev_drift = &rev_lag - &(-&prior_lag);

    let mut fwd = BTreeMap::new();
    fwd.insert("ratio".to_string(), pair_json(&fwd_ratio));
    fwd.insert("bias_diff".to_string(), pair_json(&bias_diff));
    fwd.insert("lag".to_string(), pair_json(&fwd_lag));
    fwd.insert("drift".to_string(), pair_json(&fwd_drift));

    let mut rev = BTreeMap::new();
    rev.insert("ratio".to_string(), pair_json(&rev_ratio));
    rev.insert("bias_diff".to_string(), pair_json(&rev_bias));
    rev.insert("lag".to_string(), pair_json(&rev_lag));
    rev.insert("drift".to_string(), pair_json(&rev_drift));

    let mut out = BTreeMap::new();
    out.insert("forward".to_string(), JsonValue::Object(fwd));
    out.insert("reverse".to_string(), JsonValue::Object(rev));
    Ok(JsonValue::Object(out))
}

fn op_finite_stokes_cut_balance(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let region_arr = require_json_array(get_field(inputs, "region")?, "region")?;
    let mut region: BTreeSet<BigInt> = BTreeSet::new();
    for item in region_arr {
        region.insert(require_json_int(item, "region_node")?.clone());
    }
    let channels = require_json_array(get_field(inputs, "channels")?, "channels")?;
    let mut ledger: BTreeMap<(BigInt, BigInt, String), BigRat> = BTreeMap::new();
    for ch_val in channels {
        let ch = require_json_object(ch_val, "channel")?;
        let i = require_json_int(get_field(ch, "i")?, "i")?.clone();
        let j = require_json_int(get_field(ch, "j")?, "j")?.clone();
        let p_v = parse_canonical_rational_pair_json(get_field(ch, "p")?, "p")?;
        let a_v = parse_canonical_rational_pair_json(get_field(ch, "a")?, "a")?;
        let lin = require_json_str(get_field(ch, "lineage")?, "lineage")?;
        if i == j || p_v.is_negative() || lin.is_empty() {
            return Err(CoreError::ValueError(
                "invalid oriented channel".to_string(),
            ));
        }
        let val = &p_v * &a_v;
        ledger.insert((i.clone(), j.clone(), lin.to_string()), val.clone());
        ledger.insert((j, i, lin.to_string()), -&val);
    }

    let mut internal = BigRat::zero();
    let mut divergence = BigRat::zero();
    let mut boundary = BigRat::zero();
    for ((i, j, _), val) in &ledger {
        let i_in = region.contains(i);
        let j_in = region.contains(j);
        if i_in {
            divergence = &divergence + val;
            if j_in {
                internal = &internal + val;
            } else {
                boundary = &boundary + val;
            }
        }
    }

    let mut out = BTreeMap::new();
    out.insert("internal".to_string(), pair_json(&internal));
    out.insert("boundary".to_string(), pair_json(&boundary));
    out.insert("divergence".to_string(), pair_json(&divergence));
    out.insert(
        "divergence_equals_boundary".to_string(),
        JsonValue::Bool(divergence == boundary && internal.is_zero()),
    );
    Ok(JsonValue::Object(out))
}

fn op_awareness_current_update(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let cur = parse_canonical_rational_pair_json(get_field(inputs, "current")?, "current")?;
    let pres = parse_canonical_rational_pair_json(get_field(inputs, "pressure")?, "pressure")?;
    let att = parse_canonical_rational_pair_json(get_field(inputs, "attention")?, "attention")?;
    let qry = parse_canonical_rational_pair_json(get_field(inputs, "query")?, "query")?;
    let gain = parse_canonical_rational_pair_json(get_field(inputs, "gain")?, "gain")?;
    let ret_arr = require_json_array(
        get_field(inputs, "available_retained_values")?,
        "available_retained_values",
    )?;
    let thresh = parse_canonical_rational_pair_json(
        get_field(inputs, "selector_threshold")?,
        "selector_threshold",
    )?;
    if !pres.is_positive() {
        return Err(CoreError::ValueError(
            "positive pressure required".to_string(),
        ));
    }
    let mut ret_sum = BigRat::zero();
    for item in ret_arr {
        ret_sum = &ret_sum + &parse_canonical_rational_pair_json(item, "retained_value")?;
    }
    let carried = &gain * &ret_sum;
    let native_cur = &cur + &att.checked_div(&pres)?;
    let next_cur = &native_cur + &(&qry + &carried).checked_div(&pres)?;
    let rem_cur = &native_cur + &qry.checked_div(&pres)?;
    let slot = if next_cur > thresh { 0 } else { 1 };

    let mut out = BTreeMap::new();
    out.insert("carried".to_string(), pair_json(&carried));
    out.insert("native_current".to_string(), pair_json(&native_cur));
    out.insert("next_current".to_string(), pair_json(&next_cur));
    out.insert("selected_slot".to_string(), JsonValue::Int(BigInt::from_i64(slot)));
    out.insert("removal_current".to_string(), pair_json(&rem_cur));
    out.insert(
        "awareness_effect".to_string(),
        JsonValue::Bool(next_cur != rem_cur),
    );
    Ok(JsonValue::Object(out))
}

fn op_awareness_mindfulness_step(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let pres = parse_canonical_rational_pair_json(get_field(inputs, "pressure")?, "pressure")?;
    let j0 =
        parse_canonical_rational_pair_json(get_field(inputs, "initial_current")?, "initial_current")?;
    let forcing = parse_canonical_rational_pair_json(
        get_field(inputs, "constant_forcing")?,
        "constant_forcing",
    )?;
    let delay_init = parse_canonical_rational_pair_json(
        get_field(inputs, "delay_initial_history")?,
        "delay_initial_history",
    )?;
    let steps_int = require_json_int(get_field(inputs, "steps")?, "steps")?;
    let steps = steps_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("steps must be a nonnegative integer".to_string())
    })?;
    if steps > MAX_STEPS_GUARD {
        return Err(CoreError::ValueError(format!(
            "steps exceeds guard {}",
            MAX_STEPS_GUARD
        )));
    }
    if pres.is_zero() {
        return Err(CoreError::DivisionByZero(
            "pressure cannot be zero".to_string(),
        ));
    }

    let mut no_delay: Vec<BigRat> = Vec::with_capacity(steps);
    let mut j_cur = j0.clone();
    for _ in 0..steps {
        let delta = (&forcing - &j_cur).checked_div(&pres)?;
        j_cur = &j_cur + &delta;
        no_delay.push(j_cur.clone());
    }

    let mut extra_delay: Vec<BigRat> = Vec::with_capacity(steps);
    let mut j_cur = j0;
    let mut prev_obs = delay_init;
    for _ in 0..steps {
        let obs = j_cur.clone();
        let delta = (&forcing - &prev_obs).checked_div(&pres)?;
        j_cur = &j_cur + &delta;
        prev_obs = obs;
        extra_delay.push(j_cur.clone());
    }

    let one = BigRat::one();
    let no_delay_stable = no_delay.iter().all(|x| *x == one);
    let extra_delay_stable = extra_delay.iter().all(|x| *x == one);

    let mut out = BTreeMap::new();
    out.insert(
        "no_delay_currents".to_string(),
        JsonValue::Array(no_delay.iter().map(pair_json).collect()),
    );
    out.insert(
        "no_delay_stable_at_one".to_string(),
        JsonValue::Bool(no_delay_stable),
    );
    out.insert(
        "extra_delay_currents".to_string(),
        JsonValue::Array(extra_delay.iter().map(pair_json).collect()),
    );
    out.insert(
        "extra_delay_stable_at_one".to_string(),
        JsonValue::Bool(extra_delay_stable),
    );
    Ok(JsonValue::Object(out))
}

fn op_higgs_trace_score_and_freeze(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let cands = require_json_array(get_field(inputs, "candidates")?, "candidates")?;
    if cands.is_empty() {
        return Err(CoreError::ValueError(
            "candidates must be non-empty".to_string(),
        ));
    }
    struct Detail {
        pi_v: BigInt,
        rd_v: BigInt,
        pd_v: BigInt,
        qd_v: BigInt,
        win_l: BigInt,
    }
    let mut scores: Vec<BigRat> = Vec::with_capacity(cands.len());
    let mut details: Vec<Detail> = Vec::with_capacity(cands.len());
    let b0 = BigInt::zero();
    let b1 = BigInt::one();
    let b2 = BigInt::from_i64(2);
    let b3 = BigInt::from_i64(3);
    let bm3 = BigInt::from_i64(-3);
    let b7 = BigInt::from_i64(7);
    let b12 = BigInt::from_i64(12);
    let b100 = BigInt::from_i64(100);
    let b250 = BigInt::from_i64(250);

    for c_val in cands {
        let c = require_json_object(c_val, "candidate")?;
        let p = require_u32_exp(require_json_int(get_field(c, "p")?, "p")?, "p")?;
        let q = require_json_int(get_field(c, "q")?, "q")?;
        let win_l = require_json_int(get_field(c, "L")?, "L")?;
        let c3 = require_json_int(get_field(c, "C3")?, "C3")?;
        let ca = require_json_int(get_field(c, "Ca")?, "Ca")?;
        let cb = require_json_int(get_field(c, "Cb")?, "Cb")?;

        let pi_v = &q.pow_u32(p) + q;
        let rd_v = &(&b2 * &pi_v) + &b1;
        let rho = (&rd_v).min(win_l).clone();
        let pd_v = c3 * &rho;
        let diff_rd_l = &rd_v - win_l;
        let excess_rd = if diff_rd_l > b0 { diff_rd_l } else { b0.clone() };
        let qd_v = c3 * &excess_rd;
        let dl = &pd_v - ca;
        let du = &pd_v - cb;
        let d_sad = &(&dl - &b3).abs() + &(&du + &b3).abs();
        let d_q = if qd_v >= b100 && qd_v <= b250 {
            b0.clone()
        } else if qd_v < b100 {
            &b100 - &qd_v
        } else {
            &qd_v - &b250
        };
        let d_route = if *win_l == b7 && dl == b3 && du == bm3 && qd_v >= b100 && qd_v <= b250 {
            BigRat::zero()
        } else {
            BigRat::one()
        };
        let s_h = &(&(&BigRat::new(d_sad, b12.clone())? + &BigRat::new(d_q, b100.clone())?)
            + &BigRat::new((win_l - &b7).abs(), b2.clone())?)
            + &d_route;
        scores.push(s_h);
        details.push(Detail {
            pi_v,
            rd_v,
            pd_v,
            qd_v,
            win_l: win_l.clone(),
        });
    }

    let mut win_idx = 0usize;
    for idx in 1..scores.len() {
        if scores[idx] < scores[win_idx] {
            win_idx = idx;
        }
    }
    let wd = &details[win_idx];
    let shift_int = &wd.win_l + &BigInt::from_i64(4);
    let shift = shift_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("winner L + 4 must be nonnegative".to_string())
    })?;
    if shift > MAX_WIDTH_GUARD {
        return Err(CoreError::ValueError(
            "winner L + 4 exceeds exponent guard".to_string(),
        ));
    }
    let e_mev = wd.rd_v.shl_usize(shift);
    let e_gev = BigRat::new(e_mev.clone(), BigInt::from_i64(1000))?;

    let mut out = BTreeMap::new();
    out.insert(
        "scores".to_string(),
        JsonValue::Array(scores.iter().map(pair_json).collect()),
    );
    out.insert(
        "winner_index".to_string(),
        JsonValue::Int(BigInt::from_usize(win_idx)),
    );
    out.insert("winner_Pi".to_string(), JsonValue::Int(wd.pi_v.clone()));
    out.insert("winner_RD".to_string(), JsonValue::Int(wd.rd_v.clone()));
    out.insert("winner_PD".to_string(), JsonValue::Int(wd.pd_v.clone()));
    out.insert("winner_QD".to_string(), JsonValue::Int(wd.qd_v.clone()));
    out.insert("E_H_0_MeV".to_string(), JsonValue::Int(e_mev));
    out.insert("E_H_0_GeV".to_string(), pair_json(&e_gev));
    Ok(JsonValue::Object(out))
}

fn op_brownian_3d_delta3_msb_x(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let disps = require_json_array(get_field(inputs, "displacements")?, "displacements")?;
    let beta_a_int = require_json_int(get_field(inputs, "beta_a")?, "beta_a")?;
    let beta_a = beta_a_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("beta_a must be a positive integer".to_string())
    })?;
    if beta_a == 0 || beta_a > MAX_WIDTH_GUARD {
        return Err(CoreError::ValueError("invalid beta_a".to_string()));
    }
    if disps.is_empty() {
        return Err(CoreError::ValueError(
            "displacements must be non-empty".to_string(),
        ));
    }

    let mut q_vals: Vec<BigInt> = Vec::with_capacity(disps.len());
    let mut octs: Vec<BigInt> = Vec::with_capacity(disps.len());
    let mut phase_cnt = vec![BigInt::zero(); beta_a];
    let mut oct_cnt = vec![BigInt::zero(); 8];
    let mut sx = BigInt::zero();
    let mut sy = BigInt::zero();
    let mut sz = BigInt::zero();

    for row_val in disps {
        let row = require_json_array(row_val, "displacement")?;
        if row.len() != 3 {
            return Err(CoreError::ValueError(
                "each displacement must have 3 coordinates".to_string(),
            ));
        }
        let a = require_json_int(&row[0], "a")?;
        let b = require_json_int(&row[1], "b")?;
        let c = require_json_int(&row[2], "c")?;
        let aa = a * a;
        let bb = b * b;
        let cc = c * c;
        let qv = &(&aa + &bb) + &cc;
        let oc: usize = (if a.is_negative() { 4 } else { 0 })
            + (if b.is_negative() { 2 } else { 0 })
            + (if c.is_negative() { 1 } else { 0 });
        let theta = qv.rem_euclid_u64(beta_a as u64)? as usize;
        phase_cnt[theta] = &phase_cnt[theta] + &BigInt::one();
        oct_cnt[oc] = &oct_cnt[oc] + &BigInt::one();
        sx = &sx + &aa;
        sy = &sy + &bb;
        sz = &sz + &cc;
        q_vals.push(qv);
        octs.push(BigInt::from_usize(oc));
    }

    let n = disps.len();
    let p_comp = int_balance(n, beta_a);
    let o_comp = int_balance(n, 8);
    let p_dz: Vec<BigInt> = p_comp.iter().zip(&phase_cnt).map(|(c, o)| c - o).collect();
    let o_dz: Vec<BigInt> = o_comp.iter().zip(&oct_cnt).map(|(c, o)| c - o).collect();
    let sum_phase_m = p_dz.iter().fold(BigInt::zero(), |acc, x| &acc + &x.abs());
    let sum_octant_m = o_dz.iter().fold(BigInt::zero(), |acc, x| &acc + &x.abs());
    let sum_q = q_vals.iter().fold(BigInt::zero(), |acc, x| &acc + x);

    let r_q = BigRat::new(sum_q.clone(), BigInt::from_usize(n))?;
    let r_x = BigRat::new(sx, sum_q.clone())?;
    let r_y = BigRat::new(sy, sum_q.clone())?;
    let r_z = BigRat::new(sz, sum_q)?;

    let mut out = BTreeMap::new();
    out.insert(
        "Q".to_string(),
        JsonValue::Array(q_vals.into_iter().map(JsonValue::Int).collect()),
    );
    out.insert(
        "octants_msb_x".to_string(),
        JsonValue::Array(octs.into_iter().map(JsonValue::Int).collect()),
    );
    out.insert(
        "phase_DeltaZ".to_string(),
        JsonValue::Array(p_dz.into_iter().map(JsonValue::Int).collect()),
    );
    out.insert(
        "octant_DeltaZ".to_string(),
        JsonValue::Array(o_dz.into_iter().map(JsonValue::Int).collect()),
    );
    out.insert("sum_phase_m".to_string(), JsonValue::Int(sum_phase_m));
    out.insert("sum_octant_m".to_string(), JsonValue::Int(sum_octant_m));
    out.insert("R_Q".to_string(), pair_json(&r_q));
    out.insert("R_x".to_string(), pair_json(&r_x));
    out.insert("R_y".to_string(), pair_json(&r_y));
    out.insert("R_z".to_string(), pair_json(&r_z));
    Ok(JsonValue::Object(out))
}

fn op_run_tumble_3d_delta3_lsb_x(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let vecs = require_json_array(get_field(inputs, "z_vectors")?, "z_vectors")?;
    let beta_a = require_json_int(get_field(inputs, "beta_a")?, "beta_a")?;
    if !beta_a.is_positive() {
        return Err(CoreError::ValueError("beta_a must be positive".to_string()));
    }
    let mut lsb = Vec::with_capacity(vecs.len());
    let mut msb = Vec::with_capacity(vecs.len());
    let mut q3s = Vec::with_capacity(vecs.len());
    let mut thetas = Vec::with_capacity(vecs.len());

    for row_val in vecs {
        let row = require_json_array(row_val, "z_vector")?;
        if row.len() != 3 {
            return Err(CoreError::ValueError(
                "each z_vector must have 3 coordinates".to_string(),
            ));
        }
        let x = require_json_int(&row[0], "x")?;
        let y = require_json_int(&row[1], "y")?;
        let z = require_json_int(&row[2], "z")?;
        let oc_lsb: i64 = (if x.is_negative() { 1 } else { 0 })
            + (if y.is_negative() { 2 } else { 0 })
            + (if z.is_negative() { 4 } else { 0 });
        let oc_msb: i64 = (if x.is_negative() { 4 } else { 0 })
            + (if y.is_negative() { 2 } else { 0 })
            + (if z.is_negative() { 1 } else { 0 });
        let q3 = &(&(x * x) + &(y * y)) + &(z * z);
        let (_, theta) = q3.div_rem_euclid(beta_a)?;
        lsb.push(JsonValue::Int(BigInt::from_i64(oc_lsb)));
        msb.push(JsonValue::Int(BigInt::from_i64(oc_msb)));
        q3s.push(JsonValue::Int(q3));
        thetas.push(JsonValue::Int(theta));
    }

    let mut out = BTreeMap::new();
    out.insert("octants_lsb_x".to_string(), JsonValue::Array(lsb));
    out.insert("octants_msb_x_contrast".to_string(), JsonValue::Array(msb));
    out.insert("Q3".to_string(), JsonValue::Array(q3s));
    out.insert("theta".to_string(), JsonValue::Array(thetas));
    Ok(JsonValue::Object(out))
}

fn step_result_to_json(step: &CycleSheddingStepResult) -> JsonValue {
    let mut out = BTreeMap::new();
    out.insert("span".to_string(), pair_json(&step.span));
    out.insert("before_clipping".to_string(), pair_json(&step.before_clipping));
    out.insert("shed_excess".to_string(), pair_json(&step.shed_excess));
    out.insert("padar_burden".to_string(), pair_json(&step.padar_burden));
    out.insert("outward_shedding".to_string(), pair_json(&step.outward_shedding));
    out.insert("local_reclosure".to_string(), pair_json(&step.local_reclosure));
    out.insert("remainder_sum".to_string(), pair_json(&step.remainder_sum));
    JsonValue::Object(out)
}

fn op_cycle_shedding_step(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let prev = parse_canonical_rational_pair_json(get_field(inputs, "prev_burden")?, "prev_burden")?;
    let lead = parse_canonical_rational_pair_json(get_field(inputs, "lead")?, "lead")?;
    let lag = parse_canonical_rational_pair_json(get_field(inputs, "lag")?, "lag")?;
    let comp = parse_canonical_rational_pair_json(
        get_field(inputs, "compatibility")?,
        "compatibility",
    )?;
    let eta = parse_canonical_rational_pair_json(get_field(inputs, "eta")?, "eta")?;
    let gamma = parse_canonical_rational_pair_json(get_field(inputs, "gamma")?, "gamma")?;
    let lam = parse_canonical_rational_pair_json(
        get_field(inputs, "lambda_reclose")?,
        "lambda_reclose",
    )?;
    let res = cycle_shedding_step_exact(&prev, &lead, &lag, &comp, &eta, &gamma, &lam);
    Ok(step_result_to_json(&res))
}

fn op_cycle_shedding_trace(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let init = parse_pair_or_printed_decimal_json(
        get_field(inputs, "initial_burden")?,
        "initial_burden",
    )?;
    let eta = parse_pair_or_printed_decimal_json(get_field(inputs, "eta")?, "eta")?;
    let gamma = parse_pair_or_printed_decimal_json(get_field(inputs, "gamma")?, "gamma")?;
    let lam = parse_pair_or_printed_decimal_json(
        get_field(inputs, "lambda_reclose")?,
        "lambda_reclose",
    )?;
    let raw_ticks = require_json_array(get_field(inputs, "ticks")?, "ticks")?;
    let mut ticks = Vec::with_capacity(raw_ticks.len());
    for t_val in raw_ticks {
        let obj = require_json_object(t_val, "tick")?;
        let lead = parse_pair_or_printed_decimal_json(get_field(obj, "lead")?, "lead")?;
        let lag = parse_pair_or_printed_decimal_json(get_field(obj, "lag")?, "lag")?;
        let compatibility = parse_pair_or_printed_decimal_json(
            get_field(obj, "compatibility")?,
            "compatibility",
        )?;
        ticks.push(CycleSheddingTickInput {
            lead,
            lag,
            compatibility,
        });
    }
    let trace = cycle_shedding_trace(&init, &ticks, &eta, &gamma, &lam);
    let mut max_span = BigRat::zero();
    let mut max_burden = BigRat::zero();
    let mut max_excess = BigRat::zero();
    let mut total_outward = BigRat::zero();
    let mut total_local = BigRat::zero();
    for step in &trace {
        if step.span > max_span {
            max_span = step.span.clone();
        }
        if step.padar_burden > max_burden {
            max_burden = step.padar_burden.clone();
        }
        if step.shed_excess > max_excess {
            max_excess = step.shed_excess.clone();
        }
        total_outward = &total_outward + &step.outward_shedding;
        total_local = &total_local + &step.local_reclosure;
    }
    let final_burden = trace
        .last()
        .map(|s| s.padar_burden.clone())
        .unwrap_or(init);
    let mut out = BTreeMap::new();
    out.insert(
        "ticks".to_string(),
        JsonValue::Array(trace.iter().map(step_result_to_json).collect()),
    );
    out.insert("final_burden".to_string(), pair_json(&final_burden));
    out.insert("max_span".to_string(), pair_json(&max_span));
    out.insert("max_burden".to_string(), pair_json(&max_burden));
    out.insert("max_excess".to_string(), pair_json(&max_excess));
    out.insert("total_outward".to_string(), pair_json(&total_outward));
    out.insert("total_local".to_string(), pair_json(&total_local));
    Ok(JsonValue::Object(out))
}

fn op_sparc_exact_bin_eval(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let r_v = parse_printed_rational(require_json_str(get_field(inputs, "R")?, "R")?, false, false)?;
    let v_obs =
        parse_printed_rational(require_json_str(get_field(inputs, "Vobs")?, "Vobs")?, false, false)?;
    let err_v =
        parse_printed_rational(require_json_str(get_field(inputs, "errV")?, "errV")?, false, false)?;
    let v_gas =
        parse_printed_rational(require_json_str(get_field(inputs, "Vgas")?, "Vgas")?, false, false)?;
    let v_disk = parse_printed_rational(
        require_json_str(get_field(inputs, "Vdisk")?, "Vdisk")?,
        false,
        false,
    )?;
    let v_bul =
        parse_printed_rational(require_json_str(get_field(inputs, "Vbul")?, "Vbul")?, false, false)?;

    let u_obs = &v_obs * &v_obs;
    let sigma_u = &(&BigRat::from_i64(2) * &v_obs) * &err_v;
    let u_gas = &v_gas * &v_gas;
    let u_disk = &v_disk * &v_disk;
    let u_bul = &v_bul * &v_bul;
    let half = BigRat::from_i64_pair(1, 2)?;
    let seven_tenths = BigRat::from_i64_pair(7, 10)?;
    let u_bar = &(&u_gas + &(&half * &u_disk)) + &(&seven_tenths * &u_bul);
    let c_cap = &r_v * &(&(&v_gas.abs() + &v_disk.abs()) + &v_bul.abs());
    let d_bf = c_cap.clone();
    let u_ao = &u_bar + &(&BigRat::from_i64(8) * &d_bf);
    let delta_u = &u_ao - &u_obs;
    let z_u = delta_u.checked_div(&sigma_u)?;

    let mut out = BTreeMap::new();
    out.insert("U_obs".to_string(), pair_json(&u_obs));
    out.insert("sigma_U".to_string(), pair_json(&sigma_u));
    out.insert("U_gas".to_string(), pair_json(&u_gas));
    out.insert("U_disk".to_string(), pair_json(&u_disk));
    out.insert("U_bulge".to_string(), pair_json(&u_bul));
    out.insert("U_bar".to_string(), pair_json(&u_bar));
    out.insert("C_cap".to_string(), pair_json(&c_cap));
    out.insert("D_BF".to_string(), pair_json(&d_bf));
    out.insert("U_AO".to_string(), pair_json(&u_ao));
    out.insert("Delta_U".to_string(), pair_json(&delta_u));
    out.insert("z_U".to_string(), pair_json(&z_u));
    Ok(JsonValue::Object(out))
}

fn op_temporal_metrology_phase_si(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let cs_hz = require_json_int(get_field(inputs, "cs133_hz")?, "cs133_hz")?;
    if !cs_hz.is_positive() {
        return Err(CoreError::ValueError("cs133_hz must be positive".to_string()));
    }
    let cs_rat = BigRat::from_int(cs_hz.clone());
    let c_adv = eval_phase_advance(require_json_object(get_field(inputs, "compared")?, "compared")?)?;
    let r_adv =
        eval_phase_advance(require_json_object(get_field(inputs, "reference")?, "reference")?)?;
    let sl = eval_phase_advance(require_json_object(
        get_field(inputs, "split_left")?,
        "split_left",
    )?)?;
    let sr = eval_phase_advance(require_json_object(
        get_field(inputs, "split_right")?,
        "split_right",
    )?)?;
    if !r_adv.is_positive() {
        return Err(CoreError::ValueError(
            "positive reference advance required".to_string(),
        ));
    }
    let ratio = c_adv.checked_div(&r_adv)?;
    let duration_seconds = r_adv.checked_div(&cs_rat)?;
    let mean_frequency_hz = (&cs_rat * &c_adv).checked_div(&r_adv)?;

    let mut out = BTreeMap::new();
    out.insert("compared_advance".to_string(), pair_json(&c_adv));
    out.insert("reference_advance".to_string(), pair_json(&r_adv));
    out.insert("ratio".to_string(), pair_json(&ratio));
    out.insert("duration_seconds".to_string(), pair_json(&duration_seconds));
    out.insert("mean_frequency_hz".to_string(), pair_json(&mean_frequency_hz));
    out.insert("split_left_advance".to_string(), pair_json(&sl));
    out.insert("split_right_advance".to_string(), pair_json(&sr));
    out.insert(
        "split_additivity_exact".to_string(),
        JsonValue::Bool(&sl + &sr == c_adv),
    );
    Ok(JsonValue::Object(out))
}

fn op_temporal_metrology_signed_advance(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let cs_hz = require_json_int(get_field(inputs, "cs133_hz")?, "cs133_hz")?;
    if !cs_hz.is_positive() {
        return Err(CoreError::ValueError("cs133_hz must be positive".to_string()));
    }
    let cs_rat = BigRat::from_int(cs_hz.clone());
    let c_adv = eval_phase_advance(require_json_object(get_field(inputs, "compared")?, "compared")?)?;
    let r_adv =
        eval_phase_advance(require_json_object(get_field(inputs, "reference")?, "reference")?)?;
    if !r_adv.is_positive() {
        return Err(CoreError::ValueError(
            "positive reference advance required".to_string(),
        ));
    }
    let duration_seconds = r_adv.checked_div(&cs_rat)?;
    let signed_mean_frequency_hz = (&cs_rat * &c_adv).checked_div(&r_adv)?;

    let mut out = BTreeMap::new();
    out.insert("compared_advance".to_string(), pair_json(&c_adv));
    out.insert("reference_advance".to_string(), pair_json(&r_adv));
    out.insert("duration_seconds".to_string(), pair_json(&duration_seconds));
    out.insert(
        "signed_mean_frequency_hz".to_string(),
        pair_json(&signed_mean_frequency_hz),
    );
    Ok(JsonValue::Object(out))
}

fn op_temporal_metrology_hellwig_mean(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let t4 = parse_canonical_rational_pair_json(get_field(inputs, "table_iv_hz")?, "table_iv_hz")?;
    let t6 = parse_canonical_rational_pair_json(get_field(inputs, "table_vi_hz")?, "table_vi_hz")?;
    let mean = (&t4 + &t6).checked_div(&BigRat::from_i64(2))?;
    let diff = &t4 - &t6;

    let mut out = BTreeMap::new();
    out.insert("published_mean_hz".to_string(), pair_json(&mean));
    out.insert("difference_hz".to_string(), pair_json(&diff));
    Ok(JsonValue::Object(out))
}

fn op_lensing_swells_delta3_and_tau_discrepancy(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let pred_arr = require_json_array(get_field(inputs, "swells_predicted")?, "swells_predicted")?;
    let obs_arr = require_json_array(get_field(inputs, "swells_observed")?, "swells_observed")?;
    if pred_arr.len() != obs_arr.len() {
        return Err(CoreError::ValueError(
            "swells_predicted and swells_observed lengths must match".to_string(),
        ));
    }
    let mut dz = Vec::with_capacity(pred_arr.len());
    let mut s3 = Vec::with_capacity(pred_arr.len());
    let mut m_vals = Vec::with_capacity(pred_arr.len());
    let mut sum_dz = BigInt::zero();
    let mut sum_m = BigInt::zero();

    for (p_v, o_v) in pred_arr.iter().zip(obs_arr.iter()) {
        let p = require_json_int(p_v, "swells_predicted")?;
        let o = require_json_int(o_v, "swells_observed")?;
        let d = p - o;
        let s = BigInt::from_i64(d.signum_i8() as i64);
        let m = d.abs();
        sum_dz = &sum_dz + &d;
        sum_m = &sum_m + &m;
        dz.push(JsonValue::Int(d));
        s3.push(JsonValue::Int(s));
        m_vals.push(JsonValue::Int(m));
    }
    let tau_d = parse_canonical_rational_pair_json(
        get_field(inputs, "tau_diagnostic_1210")?,
        "tau_diagnostic_1210",
    )?;
    let tau_s = parse_canonical_rational_pair_json(
        get_field(inputs, "tau_summary_nominal_1210")?,
        "tau_summary_nominal_1210",
    )?;
    let tau_diff = &tau_s - &tau_d;

    let mut out = BTreeMap::new();
    out.insert("deltaZ".to_string(), JsonValue::Array(dz));
    out.insert("s3".to_string(), JsonValue::Array(s3));
    out.insert("m".to_string(), JsonValue::Array(m_vals));
    out.insert("sum_deltaZ".to_string(), JsonValue::Int(sum_dz));
    out.insert("sum_m".to_string(), JsonValue::Int(sum_m));
    out.insert("tau_difference".to_string(), pair_json(&tau_diff));
    out.insert("tau_distinct".to_string(), JsonValue::Bool(tau_d != tau_s));
    Ok(JsonValue::Object(out))
}

fn op_map21_nonlinear_finite_law_variance(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let support = require_json_array(get_field(inputs, "support")?, "support")?;
    if support.is_empty() {
        return Err(CoreError::ValueError(
            "support must be non-empty".to_string(),
        ));
    }
    let one = BigRat::one();
    let mut probs = Vec::with_capacity(support.len());
    let mut ys = Vec::with_capacity(support.len());
    let mut ds = Vec::with_capacity(support.len());
    let mut outs = Vec::with_capacity(support.len());

    for pt_val in support {
        let pt = require_json_object(pt_val, "support_point")?;
        let p_w = parse_canonical_rational_pair_json(get_field(pt, "p")?, "p")?;
        let y_v = parse_canonical_rational_pair_json(get_field(pt, "y")?, "y")?;
        let d_v = parse_canonical_rational_pair_json(get_field(pt, "d")?, "d")?;
        let denom = &one + &y_v;
        if denom.is_zero() {
            return Err(CoreError::ValueError(
                "MAP-21 denominator 1+y == 0".to_string(),
            ));
        }
        let val = &one.checked_div(&denom)? + &d_v;
        probs.push(p_w);
        ys.push(y_v);
        ds.push(d_v);
        outs.push(val);
    }
    if sum_rats(probs.iter().cloned()) != one {
        return Err(CoreError::ValueError(
            "support weights must sum to 1".to_string(),
        ));
    }
    let mean = sum_rats(probs.iter().zip(&outs).map(|(p, o)| p * o));
    let var = sum_rats(probs.iter().zip(&outs).map(|(p, o)| {
        let diff = o - &mean;
        p * &(&diff * &diff)
    }));
    let my = sum_rats(probs.iter().zip(&ys).map(|(p, y)| p * y));
    let md = sum_rats(probs.iter().zip(&ds).map(|(p, d)| p * d));
    let cyy = sum_rats(probs.iter().zip(&ys).map(|(p, y)| {
        let diff = y - &my;
        p * &(&diff * &diff)
    }));
    let cdd = sum_rats(probs.iter().zip(&ds).map(|(p, d)| {
        let diff = d - &md;
        p * &(&diff * &diff)
    }));
    let cyd = sum_rats(
        probs
            .iter()
            .zip(ys.iter().zip(&ds))
            .map(|(p, (y, d))| p * &(&(y - &my) * &(d - &md))),
    );
    let lin_var = &(&cyy - &(&BigRat::from_i64(2) * &cyd)) + &cdd;
    let mean_shift = &mean - &one;

    let mut out = BTreeMap::new();
    out.insert(
        "outputs".to_string(),
        JsonValue::Array(outs.iter().map(pair_json).collect()),
    );
    out.insert("output_mean".to_string(), pair_json(&mean));
    out.insert("mean_shift".to_string(), pair_json(&mean_shift));
    out.insert("output_variance".to_string(), pair_json(&var));
    out.insert(
        "linearized_variance_diagnostic".to_string(),
        pair_json(&lin_var),
    );
    Ok(JsonValue::Object(out))
}

fn op_sympy_z4_dft(inputs: &BTreeMap<String, JsonValue>) -> Result<JsonValue, CoreError> {
    let raw_vals = require_json_array(get_field(inputs, "values")?, "values")?;
    if raw_vals.len() != 4 {
        return Err(CoreError::ValueError("Z4 DFT requires 4 values".to_string()));
    }
    let mut vals: Vec<BigRat> = Vec::with_capacity(4);
    for item in raw_vals {
        let tok = require_json_str(item, "z4_val")?;
        vals.push(parse_printed_rational(tok, true, false)?);
    }
    let four = BigRat::from_i64(4);
    let mut coeffs: Vec<GaussianRat> = Vec::with_capacity(4);
    for k in 0i64..4 {
        let mut acc = GaussianRat::zero();
        for g in 0i64..4 {
            let phase = GaussianRat::pow_i(&BigInt::from_i64(-k * g));
            let term = &GaussianRat::from_rat(vals[g as usize].clone()) * &phase;
            acc = &acc + &term;
        }
        coeffs.push(acc.div_rat(&four)?);
    }
    let mut recon: Vec<GaussianRat> = Vec::with_capacity(4);
    for g in 0i64..4 {
        let mut acc = GaussianRat::zero();
        for k in 0i64..4 {
            let phase = GaussianRat::pow_i(&BigInt::from_i64(k * g));
            let term = &coeffs[k as usize] * &phase;
            acc = &acc + &term;
        }
        recon.push(acc);
    }
    let time_e = sum_rats(vals.iter().map(|v| v * v)).checked_div(&four)?;
    let freq_e = sum_rats(coeffs.iter().map(GaussianRat::norm_sq));
    if time_e != freq_e {
        return Err(CoreError::ValueError(
            "Parseval identity failed on Z4 DFT".to_string(),
        ));
    }

    let mut out = BTreeMap::new();
    out.insert(
        "coefficients".to_string(),
        JsonValue::Array(
            coeffs
                .iter()
                .map(|c| JsonValue::Str(c.to_sympy_string()))
                .collect(),
        ),
    );
    out.insert(
        "reconstruction".to_string(),
        JsonValue::Array(
            recon
                .iter()
                .map(|r| JsonValue::Str(r.to_sympy_string()))
                .collect(),
        ),
    );
    out.insert("parseval_time".to_string(), pair_json(&time_e));
    out.insert("parseval_freq".to_string(), pair_json(&freq_e));
    Ok(JsonValue::Object(out))
}

fn op_cyclotomic_z12_overtone(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let n_order_int = require_json_int(get_field(inputs, "group_order")?, "group_order")?;
    let n_order = n_order_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("group_order must be a positive integer".to_string())
    })?;
    if n_order != 12 {
        return Err(CoreError::ValueError(format!(
            "cyclotomic_z12_overtone requires group_order == 12, got {}",
            n_order
        )));
    }
    let pulses_arr = require_json_array(get_field(inputs, "pulses")?, "pulses")?;
    let mut pulses: Vec<BigInt> = Vec::with_capacity(pulses_arr.len());
    for item in pulses_arr {
        pulses.push(require_json_int(item, "pulse")?.clone());
    }
    let l_min = require_json_int(get_field(inputs, "l_min")?, "l_min")?;
    if !l_min.is_positive() {
        return Err(CoreError::ValueError("l_min must be positive".to_string()));
    }
    let m_mode_int = require_json_int(get_field(inputs, "overtone_mode")?, "overtone_mode")?;
    let m_mode = m_mode_int.to_usize().ok_or_else(|| {
        CoreError::ValueError("overtone_mode must be in 0..group_order".to_string())
    })?;
    if m_mode >= n_order {
        return Err(CoreError::ValueError(
            "overtone_mode out of range".to_string(),
        ));
    }

    let n_rat = BigRat::from_int(BigInt::from_usize(n_order));
    let mut coeffs_by_mode: Vec<Cyclotomic12> = Vec::with_capacity(n_order);
    for mode in 0..n_order {
        let neg_mode = -BigInt::from_usize(mode);
        let mut acc = Cyclotomic12::zero();
        for p in &pulses {
            let exp = &neg_mode * p;
            acc.add_assign_ref(&Cyclotomic12::zeta_pow(&exp));
        }
        coeffs_by_mode.push(acc.div_rat(&n_rat)?);
    }
    for coeff in &coeffs_by_mode {
        if !coeff.is_rational() {
            return Err(CoreError::ValueError(
                "unexpected non-rational cyclotomic part".to_string(),
            ));
        }
    }
    let v_hat_3 = coeffs_by_mode[m_mode].rational_part().clone();
    let nonzero: Vec<JsonValue> = (0..n_order)
        .filter(|&m| !coeffs_by_mode[m].rational_part().is_zero())
        .map(|m| JsonValue::Int(BigInt::from_usize(m)))
        .collect();
    let freq_e = sum_rats(coeffs_by_mode.iter().map(|c| {
        let r = c.rational_part();
        r * r
    }));
    let time_e = BigRat::new(BigInt::from_usize(pulses.len()), BigInt::from_usize(n_order))?;
    if freq_e != time_e {
        return Err(CoreError::ValueError("Z12 Parseval mismatch".to_string()));
    }
    let nyquist = BigRat::new(n_order_int.clone(), &BigInt::from_i64(2) * l_min)?;
    let exceeds = BigRat::from_int(m_mode_int.clone()) > nyquist;

    let mut out = BTreeMap::new();
    out.insert("v_hat_3".to_string(), pair_json(&v_hat_3));
    out.insert("nonzero_modes".to_string(), JsonValue::Array(nonzero));
    out.insert("parseval_exact".to_string(), pair_json(&freq_e));
    out.insert(
        "overtone_exceeds_nyquist_bound".to_string(),
        JsonValue::Bool(exceeds),
    );
    Ok(JsonValue::Object(out))
}

fn op_higgs_lhc_rounded_display(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let mass = parse_printed_rational(
        require_json_str(get_field(inputs, "mass_GeV")?, "mass_GeV")?,
        false,
        false,
    )?;
    let sigma = parse_printed_rational(
        require_json_str(get_field(inputs, "sigma_GeV")?, "sigma_GeV")?,
        false,
        false,
    )?;
    let pred = parse_printed_rational(
        require_json_str(get_field(inputs, "prediction_GeV")?, "prediction_GeV")?,
        false,
        false,
    )?;
    let dec_int = require_json_int(get_field(inputs, "decimals")?, "decimals")?;
    let dec = require_u32_exp(dec_int, "decimals")?;

    let delta = &pred - &mass;
    let z_ex = delta.checked_div(&sigma)?;
    let z_rnd = round_half_even(&z_ex, dec)?;
    let ape_ex = (&delta.abs() * &BigRat::from_i64(100)).checked_div(&mass)?;
    let ape_rnd = round_half_even(&ape_ex, dec)?;

    let mut out = BTreeMap::new();
    out.insert("delta_GeV".to_string(), pair_json(&delta));
    out.insert("z_score_exact".to_string(), pair_json(&z_ex));
    out.insert(
        "z_score_rounded_6dp".to_string(),
        JsonValue::Str(format_fixed(&z_ex, dec)?),
    );
    out.insert(
        "z_score_rounding_residual".to_string(),
        pair_json(&(&z_rnd - &z_ex).abs()),
    );
    out.insert(
        "abs_percent_error_rounded_6dp".to_string(),
        JsonValue::Str(format_fixed(&ape_ex, dec)?),
    );
    out.insert(
        "abs_percent_error_rounding_residual".to_string(),
        pair_json(&(&ape_rnd - &ape_ex).abs()),
    );
    Ok(JsonValue::Object(out))
}

fn op_printed_token_half_ulp_enclosure(
    inputs: &BTreeMap<String, JsonValue>,
) -> Result<JsonValue, CoreError> {
    let tok = require_json_str(get_field(inputs, "printed_token")?, "printed_token")?;
    let (_, frac) = tok.split_once('.').ok_or_else(|| {
        CoreError::ValueError("decimal printed_token required".to_string())
    })?;
    let val = parse_printed_rational(tok, false, false)?;
    let dec_places = frac.len();
    let dec_u32 = u32::try_from(dec_places).map_err(|_| {
        CoreError::ValueError("decimal_places overflow".to_string())
    })?;
    let half_ulp = BigRat::new(
        BigInt::one(),
        &BigInt::from_i64(2) * &BigInt::pow10(dec_u32),
    )?;
    let lower = &val - &half_ulp;
    let upper = &val + &half_ulp;

    let mut out = BTreeMap::new();
    out.insert(
        "decimal_places".to_string(),
        JsonValue::Int(BigInt::from_usize(dec_places)),
    );
    out.insert("value".to_string(), pair_json(&val));
    out.insert("half_ulp_bound".to_string(), pair_json(&half_ulp));
    out.insert("enclosure_lower".to_string(), pair_json(&lower));
    out.insert("enclosure_upper".to_string(), pair_json(&upper));
    Ok(JsonValue::Object(out))
}
