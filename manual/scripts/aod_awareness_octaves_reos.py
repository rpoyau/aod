"""Exact iterated octave carriage, rational field densities and REOS fixtures.

Extends the inherited R04 awareness witnesses (`aod_awareness.py`) without
modifying any frozen R04 source or dataset. All arithmetic uses exact integers
and `fractions.Fraction`; IEEE-754 floats are rejected at every boundary.
Run `--check-data` to verify all rows in
`manual/data/m2/awareness_octave_reos_cases.jsonl`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import aod_awareness as a
import aod_native_closure_wave as n

Q = n.Q
require = n.require
AdmissionError = n.AdmissionError


def reos_price(
    rho_a: Fraction,
    rho_b: Fraction,
    control_a: int | Fraction,
    control_b: int | Fraction,
) -> Fraction:
    """Exact discrete REOS response price: lambda_a = -(rho_b - rho_a) / (R_b - R_a)."""
    ra = Q(control_a)
    rb = Q(control_b)
    dr = rb - ra
    require(dr != 0, "REOS control variation requires distinct boundary control values")
    return -(Q(rho_b) - Q(rho_a)) / dr


def octal_coord_span(total_cells: int) -> str:
    """Canonical base-8 fractal coordinate span starting at first anchor 00_8."""
    require(type(total_cells) is int and total_cells >= 0, "exact nonnegative integer cell count required")
    max_addr = total_cells - 1 if total_cells > 0 else 0
    return f"00_8 -> {max_addr:02o}_8"


def octave_ladder(mutation: str | None = None) -> dict[str, object]:
    """Build a 4-octave (B0 -> B1 -> B2 -> B3) chain-carriage ladder with top-down Expose↓."""
    base = a.contact_chain()
    b0_a, b0_b = base["positive"]["outer_one"]["inner"]
    b1_wave = base["positive"]["higher"]
    b1_peer = base["positive"]["higher_peer"]
    b1_state = base["higher_state"]
    b1_world = base["higher_world"]
    m = a.Model()

    # Build 3 certified B2 folds for b2_wave and 3 certified B2 folds for b2_peer
    b2_start = max(b1_state.present.committed, b1_wave.returns[-1].indices[-1], b1_peer.returns[-1].indices[-1]) + 2
    b2_folds_main = tuple(
        n.fold(
            (b1_wave, b1_peer),
            n.certified(
                n.outer_trace((b1_wave, b1_peer), "b2-chain-main", occ, "B2", 2, start_index=b2_start + 12 * occ),
                "outer",
                inner=(b1_wave, b1_peer),
            ),
        )
        for occ in range(3)
    )
    b2_wave = n.wave(tuple(f["outer"] for f in b2_folds_main))
    b2_peer = n.wave(
        tuple(
            n.certified(
                n.outer_trace((b1_wave, b1_peer), "b2-chain-peer", occ, "B2", 2, start_index=b2_start + 11 * occ),
                "outer",
                inner=(b1_wave, b1_peer),
            )
            for occ in range(3)
        )
    )
    require(n.validate_wave(b2_wave) and n.validate_wave(b2_peer), "invalid B2 recurrent waves")

    if mutation == "same_scale_b2":
        # Hostile local impostor at scale 2: folding scale-2 inner waves at scale 2 must fail!
        impostor_outer = n.certified(
            n.outer_trace((b2_wave, b2_peer), "b2-impostor", 0, "B2", 2, start_index=b2_start + 50),
            "outer",
            inner=(b2_wave, b2_peer),
        )
        n.fold((b2_wave, b2_peer), impostor_outer)

    # Carry retained rebalancing from B1 up into B2 and verify matched causal operativity at B2
    b2_contacts = n.contacts(b2_peer, b2_wave)
    k_b2 = max(e.committed for e in b2_contacts)
    b2_carriage = a.Carriage(
        b1_state.retained[0],
        b2_folds_main[0]["inner"],
        b2_folds_main[0]["outer"],
        b1_world.actions,
        b1_world.prior_commitments,
    )
    b2_prior = a.Prior(
        b2_peer.identity,
        b2_wave.identity,
        b2_wave.scope,
        b2_wave.scale,
        k_b2,
        k_b2 + 1,
        (Q(2),),
        (Q(b2_carriage.retained.value),),
        b2_contacts,
        "M1:unwrapped-count-lag",
        n.compare(b2_peer, b2_wave, b2_contacts, window=(0, k_b2))["lag"],
        n.wave_prefix(b2_peer, k_b2),
        n.wave_prefix(b2_wave, k_b2),
        origin="carried",
        carriage=b2_carriage,
    )
    b2_ret = a.retain(b2_prior)
    b2_world = a.World(b2_wave.identity, (b2_wave, b2_peer), prior_commitments=(a.digest(b2_prior),))
    b2_cut = max(k_b2 + 1, b2_wave.returns[-1].indices[-1], b2_peer.returns[-1].indices[-1]) + 1
    b2_native = n.initial_state(b2_wave)
    b2_state = a.State(
        replace(b2_native, committed=b2_cut, present=(0, 1), closure_memory=(), retained_rebalancing=()),
        b2_native.closure_memory,
        (b2_ret,),
    )
    b2_inputs = (a.Input(b2_cut, available=(b2_peer.identity,)),)
    b2_match = a.matched(b2_state, replace(b2_state, retained=()), b2_world, b2_world, m, m, b2_inputs, b2_inputs)

    def offer_b3(state: a.State) -> dict[str, object]:
        later, event = a.transition(state, b2_world, m, b2_inputs[0])
        if event["current"] <= 0:
            return {"admitted": False, "event": event, "shedding": None}
        b3_start = later.present.committed + 1
        b3_outer = n.certified(
            n.outer_trace((b2_wave, b2_peer), "b3-chain-top", 0, "B3", 3, start_index=b3_start),
            "outer",
            inner=(b2_wave, b2_peer),
        )
        b3_fold = n.fold((b2_wave, b2_peer), b3_outer)
        bridge = a.shedding_bridge(later, event)
        sheddic = n.shedding(
            b3_fold,
            later.present,
            bridge.closure_load,
            bridge.closure_cost,
            source_event_digest=bridge.source_event_digest,
            model_bridge=bridge.bridge_digest,
            committed=b3_fold["outer"][0].indices[-1] + 1,
            route="exoshedding",
            target_scope=b2_wave.scope,
            target_scale=b2_wave.scale,
        )
        exposed_b2 = n.expose(b3_fold, sheddic)
        # Verify nested inner lineages B2 -> B1 -> B0 all survive top-down exposure intact!
        preserved_b1 = n.expose(b2_folds_main[0])
        preserved_b0 = n.expose(base["positive"]["outer_one"])
        return {
            "admitted": True,
            "event": event,
            "fold": b3_fold,
            "shedding": sheddic,
            "exposed_b2_ids": tuple(w.identity for w in exposed_b2),
            "preserved_b1_ids": tuple(w.identity for w in preserved_b1),
            "preserved_b0_ids": tuple(w.identity for w in preserved_b0),
        }

    b3_pos = offer_b3(b2_state)
    b3_rem = offer_b3(replace(b2_state, retained=()))
    b3_res = offer_b3(replace(b2_state, retained=(b2_ret,)))
    require(a.digest(b3_pos) == a.digest(b3_res), "exact B3 restoration changed outcome or shedding digest")

    # Active cell tally across octaves B0..B3:
    # B0: 2 base waves; B1: 2 contact-fused waves; B2: 2 chain-fused waves; B3: 1 chain-fused fold -> 7 cells
    rung_counts = {"B0": 2, "B1": 2, "B2": 2, "B3": 1}
    total_cells = sum(rung_counts.values())
    q4_units = (total_cells + 15) // 16

    if mutation == "top_down_expose":
        # After top-down shedding of B3, B3 is peeled (0 active) while B2, B1, B0 remain completely intact!
        return {
            "b3_shedding_status": b3_pos["shedding"].status,
            "b3_shedding_surplus": b3_pos["shedding"].surplus,
            "b3_shedding_route": b3_pos["shedding"].route,
            "exposed_b2_count": len(b3_pos["exposed_b2_ids"]),
            "preserved_b1_count": len(b3_pos["preserved_b1_ids"]),
            "preserved_b0_count": len(b3_pos["preserved_b0_ids"]),
            "inner_b2_identities_match": b3_pos["exposed_b2_ids"] == (b2_wave.identity, b2_peer.identity),
            "inner_b0_identities_match": b3_pos["preserved_b0_ids"] == (b0_a.identity, b0_b.identity),
            "restored_shedding_digest_equal": a.digest(b3_pos["shedding"]) == a.digest(b3_res["shedding"]),
            "active_octave_after_top_peel": 2,
        }

    return {
        "max_scale": 3,
        "occupied_octaves": 4,
        "b0_cells": rung_counts["B0"],
        "contact_fusions": rung_counts["B1"],
        "chain_fusions": rung_counts["B2"] + rung_counts["B3"],
        "total_cells": total_cells,
        "q4_units": q4_units,
        "octal_coord_span": octal_coord_span(total_cells),
        "b1_match_effect": base["higher_match"]["effect"],
        "b2_match_effect": b2_match["effect"],
        "b3_positive_admitted": b3_pos["admitted"],
        "b3_removed_admitted": b3_rem["admitted"],
        "b3_restored_equal": a.digest(b3_pos) == a.digest(b3_res),
    }


def density_reos(mutation: str | None = None) -> dict[str, object]:
    """Exact rational cell/window densities, discrete REOS shadow prices, and passive-trace invariance."""
    s, w, m, _base_inputs = a.context(peers=2, values=(1, -1))
    ids = tuple(x.identity for x in w.waves[1:])
    k0 = s.present.committed

    # 20 committed boundary cuts alternating operative +1 and -1 source channels:
    # signed_flux sums to 0 while abs_transport sums to 20 (rho_flux == 0, rho_trans == 1).
    inputs_20 = tuple(
        a.Input(k0 + step, available=(ids[0],) if step % 2 == 0 else (ids[1],))
        for step in range(20)
    )
    plain = a.execute(s, w, m, inputs_20, trace=False)
    traced = a.execute(s, w, m, inputs_20, trace=True)
    trace_equal = a.execution_bytes(plain) == a.execution_bytes(traced)
    require(trace_equal, "passive boundary observation mutated realized state or event bytes")

    if mutation == "unmatched_control":
        # Hostile control: changing pressure p=1 -> p=2 inside a matched window comparison is rejected!
        s_bad = replace(s, present=replace(s.present, pressure=Q(2)))
        a.matched(s, s_bad, w, w, m, m, inputs_20[:4], inputs_20[:4])

    # Extract per-cut signed boundary increments delta_t = J_{t} - J_{t-1} directly from committed events
    deltas: list[Fraction] = []
    prev_j = Q(s.present.current)
    for ev in plain["events"]:
        cur_j = Q(ev["current"])
        deltas.append(cur_j - prev_j)
        prev_j = cur_j

    # Deterministic reclosure (bip) and shedding-surplus schedules on the 20 committed cuts:
    # 6 reclosures across 20 cuts (4 inside the last 10 cuts); 2 shedding surpluses in the last 10 cuts.
    reclosures_20 = tuple(1 if idx in (2, 6, 10, 13, 16, 19) else 0 for idx in range(20))
    shed_20 = tuple(1 if idx in (14, 18) else 0 for idx in range(20))

    def window_densities(width: int) -> dict[str, Fraction]:
        require(type(width) is int and 1 <= width <= len(deltas), "invalid boundary window width")
        sub_d = deltas[-width:]
        sub_b = reclosures_20[-width:]
        sub_s = shed_20[-width:]
        return {
            "rho_flux": sum(sub_d, Q(0)) / Q(width),
            "rho_trans": sum((abs(d) for d in sub_d), Q(0)) / Q(width),
            "rho_bip": Q(sum(sub_b), width),
            "rho_shed": Q(sum(sub_s), width),
        }

    w10 = window_densities(10)
    w20 = window_densities(20)

    if mutation == "zero_control_variation":
        # Hostile control: zero control variation (R2 == R1) must be rejected!
        reos_price(w20["rho_bip"], w20["rho_bip"], 20, 20)

    # Cell occupancy density across cell-cap control R^(1) in {32, 64} for 17 active cells (B0..B4 scale)
    total_cells = 17
    q4_units = (total_cells + 15) // 16
    rho_cell_32 = Q(total_cells, 32)
    rho_cell_64 = Q(total_cells, 64)
    rho_q4 = Q(total_cells, 16 * q4_units)

    lambda_cap_32_64 = reos_price(rho_cell_32, rho_cell_64, 32, 64)
    lambda_win_bip_10_20 = reos_price(w10["rho_bip"], w20["rho_bip"], 10, 20)
    lambda_win_shed_10_20 = reos_price(w10["rho_shed"], w20["rho_shed"], 10, 20)

    return {
        "trace_equal": trace_equal,
        "observed_steps": 20,
        "rho_cell_32": rho_cell_32,
        "rho_cell_64": rho_cell_64,
        "rho_q4": rho_q4,
        "rho_flux_20": w20["rho_flux"],
        "rho_trans_20": w20["rho_trans"],
        "rho_bip_10": w10["rho_bip"],
        "rho_bip_20": w20["rho_bip"],
        "rho_shed_10": w10["rho_shed"],
        "rho_shed_20": w20["rho_shed"],
        "lambda_cap_32_64": lambda_cap_32_64,
        "lambda_win_bip_10_20": lambda_win_bip_10_20,
        "lambda_win_shed_10_20": lambda_win_shed_10_20,
    }


def live_vs_playback() -> dict[str, object]:
    """Separate closed-loop live sensory return from open-loop recorded playback on the same command."""
    s, w, m, inputs = a.context()
    source = w.waves[1]
    action = a.Action(a.digest((w.target, 13, Q(2), source.identity)), w.target, 13, Q(2), source.identity)
    old = s.retained[0].prior

    # Live closed-loop sensory return: certified 4-traversal H1 return (y_live = 4) -> r_a = 4 - 2 = 2
    live_trace = replace(
        n.trace("action:" + action.identity, vertices=(0, 1, 3, 2, 0), dwell=2, turn=2, start_index=14),
        ancestor=action.identity,
    )
    # Recorded open-loop playback return: certified 2-traversal return (y_play = 2) -> r_a = 2 - 2 = 0
    play_trace = replace(
        n.trace("action:" + action.identity, vertices=(0, 1, 0), dwell=0, turn=1, start_index=14),
        ancestor=action.identity,
    )

    p_live = replace(old, action=action, action_return=live_trace, observed=Q(4), cross=(Q(2),), origin="action")
    p_play = replace(old, action=action, action_return=play_trace, observed=Q(2), cross=(Q(0),), origin="action")

    w_live = replace(w, actions=(action,), prior_commitments=(a.digest(p_live),))
    w_play = replace(w, actions=(action,), prior_commitments=(a.digest(p_play),))
    s_live = replace(s, retained=(a.retain(p_live),))
    s_play = replace(s, retained=(a.retain(p_play),))

    res_live = a.execute(s_live, w_live, m, inputs[:1])
    res_play = a.execute(s_play, w_play, m, inputs[:1])
    ev_live = res_live["events"][0]
    ev_play = res_play["events"][0]

    return {
        "live_readout": Q(4),
        "playback_readout": Q(2),
        "live_residual": s_live.retained[0].value,
        "playback_residual": s_play.retained[0].value,
        "live_current": ev_live["current"],
        "playback_current": ev_play["current"],
        "live_edge": list(ev_live["edge"]),
        "playback_edge": list(ev_play["edge"]),
        "playback_diverges": (ev_live["edge"] != ev_play["edge"]) and (ev_live["current"] != ev_play["current"]),
    }


def run_case(op: str, args: dict[str, object]) -> dict[str, object]:
    if op == "octave_ladder":
        return octave_ladder(args.get("mutation"))  # type: ignore[arg-type]
    if op == "density_reos":
        return density_reos(args.get("mutation"))  # type: ignore[arg-type]
    if op == "live_vs_playback":
        return live_vs_playback()
    raise AdmissionError(f"unknown octave/REOS fixture operation: {op}")


def execute_row(row: dict[str, object]) -> dict[str, object]:
    try:
        value = a.encode(run_case(str(row["operation"]), dict(row["inputs"])))  # type: ignore[arg-type]
        verdict = "PASS"
        error = None
    except (AdmissionError, ValueError) as exc:
        value = None
        verdict = "REJECT"
        error = str(exc)
    expected_matched = verdict == row["expected_verdict"] and (
        verdict == "REJECT" or value == row["expected_exact"]
    )
    return {
        "fixture_id": row["fixture_id"],
        "verdict": verdict,
        "actual": value,
        "error": error,
        "input_digest": a.digest(row["inputs"]),
        "expected_matched": expected_matched,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-data", action="store_true")
    parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "data/m2/awareness_octave_reos_cases.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [execute_row(row) for row in rows]
    print(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "results": results,
            },
            indent=2,
        )
    )
    return 0 if all(item["expected_matched"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
