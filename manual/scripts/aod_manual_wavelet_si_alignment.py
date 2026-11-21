#!/usr/bin/env python3
"""Passive exact Manual alignment verifier for wavelet continuations and conditional SI mapping.

Reuses existing Manual metrology and source-auditor modules passively without modifying
native D.E.C. transitions, frozen data records, or scientific contracts. Uses exact int
and Fraction arithmetic only and explicit ValueError checks (safe under both normal
python3 and python3 -O).
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
MANUAL_SCRIPTS = ROOT / "manual" / "scripts"
if str(MANUAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MANUAL_SCRIPTS))

import aod_mapping_error as mapping_error  # noqa: E402
import aod_temporal_metrology as metrology  # noqa: E402

CS133_DELTA_NU_HZ = metrology.CS
VALID_SEAT_STATES = frozenset({"open_duon", "seated_duad"})
VALID_ROLES = frozenset({"local_segment", "coupled_segment", "shed_continuation"})
ALLOWED_RECIPIENT_TRANSITIONS = {
    "emitted": frozenset({"delivered"}),
    "delivered": frozenset({"accepted", "unaccepted_pass"}),
    "accepted": frozenset({"seated", "pending_unseated"}),
    "seated": frozenset({"closed_origin", "reclosed"}),
    "unaccepted_pass": frozenset(),
    "pending_unseated": frozenset(),
    "closed_origin": frozenset(),
    "reclosed": frozenset(),
}

ALIGNED_MANUAL_FILES = (
    "manual/sections/00_native_closure_wave_temporal_fixtures.tex",
    "manual/sections/03_temporal_observation.tex",
    "manual/sections/03_short_window_rcd_shedding_fixtures.tex",
    "manual/appendices/A_simulation_fixtures_and_tau_prediction_context.tex",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject(callable_obj, exc_type, match: str | None = None) -> None:
    try:
        callable_obj()
    except exc_type as exc:
        if match is not None and not re.search(match, str(exc)):
            raise ValueError(
                f"expected error matching {match!r}, got {str(exc)!r}"
            ) from exc
        return
    raise ValueError(f"expected {exc_type.__name__} to be raised")


def require_exact_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an exact int, got {type(value).__name__}")
    return value


def require_exact_rational(value, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(
            f"{name} must be an exact int or Fraction, got {type(value).__name__}"
        )
    return Fraction(value)


def _load_source_auditor():
    spec = importlib.util.spec_from_file_location(
        "aod_manual_alignment_source_audit",
        ROOT / "scripts" / "audit_scientific_sources.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rebind_phase_comparison(compared: dict, reference: dict, realization: dict):
    source = mapping_error.source(
        "fixture:phase",
        "model",
        {
            "observations": {
                compared["id"]: metrology.phase_payload(compared),
                reference["id"]: metrology.phase_payload(reference),
            }
        },
    )
    for rec in (compared, reference):
        rec["sources"] = [source]
        rec["source_ids"] = [source["id"]]
    ref_src = mapping_error.source(
        "fixture:reference",
        "model",
        {
            "reference_id": reference["id"],
            "coordinate": reference["coordinate"],
            "epoch": reference["epoch"],
            "window": reference["window"],
            "defining_integer_hz": CS133_DELTA_NU_HZ,
            "physical_correspondence": realization["physical_correspondence"],
        },
    )
    realization["source"] = ref_src
    realization["trusted_sources"] = {s["id"]: s for s in (source, ref_src)}
    return compared, reference, realization


def tau_angular_report(comparison: dict) -> dict:
    """Exact symbolic tau-normalized angular readout from a conditional SI comparison."""
    ca = metrology.exact(comparison["compared_advance_turns"])
    f_bar = metrology.exact(comparison["mean_frequency_hz"])
    return {
        "angular_constant": "tau",
        "delta_theta_over_tau": str(ca),
        "omega_bar_over_tau_hz": str(f_bar),
        "rate_kind": (
            "signed_mean_phase_rate" if ca < 0 else "nonnegative_mean_phase_rate"
        ),
        "independent_atomic_prediction": comparison["independent_atomic_prediction"],
    }


# --- Primitive same-current seating, localized wavelet, overlap dedup, recipient lattice ---


def seat_duon_same_current(duon: dict, new_duon_id=None, keep_hinge: bool = True) -> dict:
    require(
        duon["sigma_seat"] == "open_seat",
        "only an open-seat Duon can seat into seated_duad",
    )
    require(keep_hinge and bool(duon.get("hinge_0H")), "structural 0_H hinge required")
    seated_id = duon["duon_id"] if new_duon_id is None else new_duon_id
    require(seated_id == duon["duon_id"], "Duad seating must preserve identical duon_id")
    return {
        "duon_id": seated_id,
        "lineage_id": duon["lineage_id"],
        "prefix_digest": duon["prefix_digest"],
        "hinge_0H": True,
        "sigma_seat": "seated_duad",
    }


def make_return_witness(
    return_id: str,
    occurrence_j: int,
    completion_cut: int,
    lineage_id: str,
    scope_id: str,
    compatible: bool = True,
    scope_mapped: bool = True,
) -> dict:
    require(bool(return_id and lineage_id and scope_id), "return witness identity required")
    j = require_exact_int(occurrence_j, "occurrence_j")
    cut = require_exact_int(completion_cut, "completion_cut")
    require(j >= 0, "occurrence_j must be non-negative")
    return {
        "return_id": return_id,
        "occurrence_j": j,
        "completion_cut": cut,
        "lineage_id": lineage_id,
        "scope_id": scope_id,
        "compatible": bool(compatible),
        "scope_mapped": bool(scope_mapped),
    }


def eligible_return_ids(
    wavelet: dict, target_lineage: str | None = None, target_scope: str | None = None
) -> set[str]:
    require(wavelet["witnesses_complete"], "complete eligible return records required")
    lineage = wavelet["parent_id"] if target_lineage is None else target_lineage
    scope = wavelet["scope_id"] if target_scope is None else target_scope
    require(wavelet["parent_id"] == lineage, "incompatible parent lineage")
    u, v = wavelet["window"]
    eligible: set[str] = set()
    for item in wavelet["return_witnesses"]:
        require(item["lineage_id"] == lineage, "return witness lineage mismatch")
        require(
            item["scope_id"] == scope or item["scope_mapped"],
            "return witness lacks identity-preserving scope map",
        )
        if item["compatible"] and item["occurrence_j"] >= 1 and (u < item["completion_cut"] <= v):
            eligible.add(item["return_id"])
    return eligible


def make_wavelet(
    wavelet_id: str,
    parent_id: str,
    ancestry: tuple[str, ...],
    window: tuple[int, int],
    sigma_seat: str,
    sigma_role: str,
    records: tuple[str, ...],
    return_witnesses: tuple[dict, ...] = (),
    signed_current: int = 0,
    is_admitted_wave: bool = False,
    scope_id: str = "B:main",
    witnesses_complete: bool = True,
) -> dict:
    require(bool(parent_id and ancestry), "wavelet must retain parent_id and ancestry")
    require(sigma_seat in VALID_SEAT_STATES, "invalid sigma_seat")
    require(sigma_role in VALID_ROLES, "invalid sigma_role")
    u, v = window
    require_exact_int(u, "window start")
    require_exact_int(v, "window end")
    require(u < v, "ordered half-open window u < v required")
    require(bool(records), "wavelet must retain committed construction records")
    w = {
        "id_w": wavelet_id,
        "parent_id": parent_id,
        "ancestry": tuple(ancestry),
        "scope_id": scope_id,
        "window": (u, v),
        "sigma_seat": sigma_seat,
        "sigma_role": sigma_role,
        "records": tuple(records),
        "return_witnesses": tuple(return_witnesses),
        "witnesses_complete": bool(witnesses_complete),
        "signed_current": require_exact_int(signed_current, "signed_current"),
        "is_admitted_wave": bool(is_admitted_wave),
    }
    eligible = eligible_return_ids(w, target_lineage=parent_id, target_scope=scope_id)
    if is_admitted_wave and (
        sigma_role == "shed_continuation" or sigma_seat == "open_duon" or len(eligible) < 1
    ):
        raise ValueError(
            "open/shed wavelet or zero-eligible-return fragment cannot be promoted to admitted wave"
        )
    return w


def validate_complete_windows(wavelets: tuple[dict, ...], known_returns: tuple[dict, ...]) -> None:
    """Reject any asserted-complete window that omits a known eligible return in (u, v]."""
    for w in wavelets:
        u, v = w["window"]
        expected = {
            r["return_id"]
            for r in known_returns
            if (
                r["lineage_id"] == w["parent_id"]
                and (r["scope_id"] == w["scope_id"] or r["scope_mapped"])
                and r["compatible"]
                and r["occurrence_j"] >= 1
                and u < r["completion_cut"] <= v
            )
        }
        actual = eligible_return_ids(w)
        require(
            actual == expected,
            f"complete window {w['window']} omitted or mismatched eligible returns: "
            f"actual={sorted(actual)} expected={sorted(expected)}",
        )


def deduplicated_return_count(
    wavelets: tuple[dict, ...], target_lineage: str, target_scope: str = "B:main"
) -> int:
    seen: set[str] = set()
    for w in wavelets:
        seen.update(
            eligible_return_ids(w, target_lineage=target_lineage, target_scope=target_scope)
        )
    return len(seen)


def evaluate_recipient_stage(
    witness: dict, recipient_context: dict, stages: tuple[str, ...], closure_witness=None
) -> dict:
    for key in (
        "parent_id",
        "emit_boundary",
        "emit_cut",
        "route",
        "X_route",
        "post_shed_parent_state",
    ):
        require(witness.get(key) not in (None, ""), f"missing shed witness field: {key}")
    require(witness["route"] in {"endo", "exo", "redir", "open"}, "invalid shed route tag")
    require(bool(stages) and stages[0] == "emitted", "recipient stages must start at emitted")
    for cur, nxt in zip(stages, stages[1:]):
        require(
            nxt in ALLOWED_RECIPIENT_TRANSITIONS.get(cur, frozenset()),
            f"illegal stage transition {cur} -> {nxt}",
        )
    terminal = stages[-1]
    u, v = recipient_context["window"]
    require_exact_int(u, "recipient window start")
    require_exact_int(v, "recipient window end")
    if terminal not in {"closed_origin", "reclosed"}:
        return {
            "stage": terminal,
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
            "blocks_later_seating": False,
        }
    require(
        closure_witness is not None and bool(closure_witness.get("has_certificate")),
        f"{terminal} requires full closure certificate",
    )
    require(
        closure_witness.get("lineage_id") == recipient_context["recipient_lineage"],
        "recipient closure lineage mismatch",
    )
    require(
        closure_witness.get("scope_id") == recipient_context["recipient_scope"]
        or bool(closure_witness.get("scope_mapped", False)),
        "recipient closure scope mismatch",
    )
    cut = require_exact_int(closure_witness["completion_cut"], "completion_cut")
    j = require_exact_int(closure_witness["occurrence_j"], "occurrence_j")
    ret_id = closure_witness.get("return_id")
    require(bool(ret_id), "closure witness requires immutable return_id")
    origin_id = recipient_context.get("origin_return_id")
    seen_ids = frozenset(recipient_context.get("seen_return_ids", ()))
    if terminal == "closed_origin":
        require(
            origin_id is None and j == 0,
            "closed_origin applies only to initial recipient closure (j=0)",
        )
        return {
            "stage": "closed_origin",
            "closure_phase_delta": int(u < cut <= v),
            "reclosure_bip_delta": 0,
            "origin_return_id": ret_id,
        }
    require(bool(origin_id), "reclosure requires pre-existing recipient origin")
    require(j >= 1, "reclosure requires j >= 1")
    if ret_id in seen_ids or ret_id == origin_id:
        return {"stage": "reclosed_replay", "closure_phase_delta": 0, "reclosure_bip_delta": 0}
    if not (u < cut <= v):
        return {
            "stage": "reclosed_out_of_window",
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
        }
    return {
        "stage": "reclosed",
        "closure_phase_delta": 1,
        "reclosure_bip_delta": 1,
        "return_id": ret_id,
    }


def native_cadence_ratio(
    id_a: str, q_a: int, id_r: str, q_r: int, coupled: bool, bound_contacts: int
) -> Fraction:
    require(id_a != id_r, "aliased wave identities rejected")
    require(coupled, "uncoupled comparison rejected")
    require_exact_int(q_a, "q_a")
    require_exact_int(q_r, "q_r")
    require_exact_int(bound_contacts, "bound_contacts")
    require(q_a >= 0, "q_a must be non-negative")
    require(q_r > 0, "reference denominator q_r must be strictly positive")
    require(bound_contacts >= 2, "repeated bound contacts (>= 2) required for biz^{TF}")
    return Fraction(q_a, q_r)


def single_contact_stage_association(
    wavelet_id: str, parent_id: str, ref_id: str, window: tuple[int, int], bound_contacts: int = 1
) -> dict:
    require(wavelet_id != ref_id and parent_id != ref_id, "aliased identities rejected")
    u, v = window
    require_exact_int(u, "window start")
    require_exact_int(v, "window end")
    require_exact_int(bound_contacts, "bound_contacts")
    require(u < v, "ordered window required")
    require(bound_contacts == 1, "single-contact stage association requires bound_contacts == 1")
    return {
        "kind": "single_contact_stage_association",
        "wavelet_id": wavelet_id,
        "parent_id": parent_id,
        "reference_id": ref_id,
        "window": (u, v),
        "is_cadence_ratio": False,
        "biz_tf": None,
    }


def compare_typed_quantities(left: dict, right: dict) -> Fraction:
    """Reject comparing or equating distinct semantic quantity kinds."""
    require(
        left["kind"] == right["kind"],
        f"semantic quantity kind mismatch: {left['kind']} != {right['kind']}",
    )
    return require_exact_rational(left["value"], "left") - require_exact_rational(
        right["value"], "right"
    )


# --- Acceptance Checks P2-01 through P2-15 ---


def check_p2_01() -> dict:
    variants = [
        (d1, mu, d2)
        for d1 in ("D_alpha", "D_Omega")
        for mu in (-1, 0, 1)
        for d2 in ("D_alpha", "D_Omega")
    ]
    require(len(variants) == 12 and len(set(variants)) == 12, "expected 12 Duon variants")
    duon = {
        "duon_id": "duon:001",
        "lineage_id": "lin:A",
        "prefix_digest": "sha256:prefix-001",
        "hinge_0H": True,
        "sigma_seat": "open_seat",
    }
    duad = seat_duon_same_current(duon)
    require(duad["duon_id"] == duon["duon_id"], "Duad changed duon_id")
    require(duad["sigma_seat"] == "seated_duad", "Duad sigma_seat mismatch")
    reject(lambda: seat_duon_same_current(duon, new_duon_id="duon:other"), ValueError, "identical")
    reject(lambda: seat_duon_same_current(duon, keep_hinge=False), ValueError, "0_H")

    c1 = make_return_witness("C1", 1, 2, "W_B_1", "B:main")
    w_coupled = make_wavelet(
        "w_coupled", "W_B_1", ("lin:1", "seg:c"), (0, 4),
        "seated_duad", "coupled_segment", ("rec:C1@2",), (c1,), is_admitted_wave=True,
    )
    w_shed = make_wavelet(
        "w_shed", "W_B_1", ("lin:1", "shed:1"), (6, 10),
        "seated_duad", "shed_continuation", ("rec:C1@2",), (c1,), is_admitted_wave=False,
    )
    require(
        w_coupled["sigma_seat"] == "seated_duad" and w_coupled["sigma_role"] == "coupled_segment",
        "seated Duad must remain able to be coupled_segment",
    )
    require(
        w_shed["sigma_seat"] == "seated_duad" and w_shed["sigma_role"] == "shed_continuation",
        "shed_continuation must retain seated_duad without forced unseating",
    )
    return {"duon_variants": 12, "same_current_seating": True, "independent_seat_role": True}


def check_p2_02() -> dict:
    parent = {"id": "W_B_1", "active_beyond_v": True}
    c0 = make_return_witness("C0", 0, 0, "W_B_1", "B:main")
    c1 = make_return_witness("C1", 1, 2, "W_B_1", "B:main")
    w = make_wavelet(
        "w_clip", parent["id"], ("lin:1", "clip:3_5"), (3, 5),
        "seated_duad", "local_segment", ("rec:C0@0", "rec:C1@2"), (c0, c1),
    )
    require(w["parent_id"] == "W_B_1" and len(w["records"]) == 2, "parent/witnesses lost")
    require(parent["active_beyond_v"] is True, "selected window terminated parent")
    reject(
        lambda: make_wavelet("bad", "", (), (0, 2), "open_duon", "local_segment", ("r0",)),
        ValueError, "parent_id",
    )
    reject(
        lambda: make_wavelet(
            "bad_promo", "W_B_1", ("lin:1",), (0, 4), "open_duon", "local_segment",
            ("r0",), (c1,), is_admitted_wave=True,
        ),
        ValueError, "cannot be promoted",
    )
    return {"parent_retained": True, "parent_active_beyond_v": True}


def check_p2_03_04() -> dict:
    c0 = make_return_witness("C0", 0, 0, "W_B_1", "B:main")
    c1 = make_return_witness("C1", 1, 2, "W_B_1", "B:main")
    c2 = make_return_witness("C2", 2, 6, "W_B_1", "B:main")
    c3 = make_return_witness("C3", 3, 8, "W_B_1", "B:main")
    known = (c0, c1, c2, c3)

    w_out = make_wavelet(
        "w_out", "W_B_1", ("lin:1", "out"), (3, 5),
        "seated_duad", "coupled_segment", ("rec:C0@0", "rec:C1@2"), (c0, c1),
    )
    require(
        len(w_out["return_witnesses"]) == 2 and eligible_return_ids(w_out) == set(),
        "out-of-window support must be retained and count 0",
    )

    w_origin = make_wavelet(
        "w_orig", "W_B_1", ("lin:1", "orig"), (-1, 1),
        "seated_duad", "local_segment", ("rec:C0@0",), (c0,),
    )
    origins_in_win = {
        r["return_id"] for r in w_origin["return_witnesses"]
        if r["occurrence_j"] == 0 and w_origin["window"][0] < r["completion_cut"] <= w_origin["window"][1]
    }
    require(
        len(origins_in_win) == 1 and eligible_return_ids(w_origin) == set(),
        "origin C0@0 in (-1, 1] must give 1 closure phase and 0 reclosure bips",
    )

    w_half = make_wavelet(
        "w_half", "W_B_1", ("lin:1", "half"), (2, 6),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6"), (c1, c2), is_admitted_wave=True,
    )
    require(eligible_return_ids(w_half) == {"C2"}, "half-open (2, 6] boundary mismatch")

    w1 = make_wavelet(
        "w1", "W_B_1", ("lin:1", "w1"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:C0@0", "rec:C1@2", "rec:C2@6"), (c0, c1, c2),
        signed_current=1, is_admitted_wave=True,
    )
    w2 = make_wavelet(
        "w2", "W_B_1", ("lin:1", "w2"), (4, 8),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6", "rec:C3@8"), (c1, c2, c3),
        signed_current=-1, is_admitted_wave=True,
    )
    validate_complete_windows((w1, w2), known)
    naive_sum = len(eligible_return_ids(w1)) + len(eligible_return_ids(w2))
    union_count = deduplicated_return_count((w1, w2), "W_B_1")
    require(naive_sum == 4 and union_count == 3, "overlap deduplication must give 2+2 vs 3")

    # Negative control: asserted-complete (0, 8] omitting known eligible C3@8 must reject
    w_incomplete = make_wavelet(
        "w_inc", "W_B_1", ("lin:1", "inc"), (0, 8),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6"), (c1, c2),
    )
    reject(lambda: validate_complete_windows((w_incomplete,), known), ValueError, "omitted")

    # Negative controls: wrong lineage and unmapped scope
    w_other_lin = make_wavelet(
        "w_ol", "W_B_2", ("lin:2",), (4, 10), "seated_duad", "coupled_segment",
        ("rec:D1@9",), (make_return_witness("D1", 1, 9, "W_B_2", "B:main"),),
    )
    reject(lambda: deduplicated_return_count((w1, w_other_lin), "W_B_1"), ValueError, "lineage")
    reject(
        lambda: make_wavelet(
            "w_bad_scope", "W_B_1", ("lin:1",), (4, 10), "seated_duad", "coupled_segment",
            ("rec:bad",), (make_return_witness("C9", 1, 9, "W_B_1", "B:other", scope_mapped=False),),
        ),
        ValueError, "scope map",
    )
    return {
        "out_of_window_count": 0,
        "origin_closure_phases": 1,
        "origin_bips": 0,
        "half_open_2_6": ["C2"],
        "overlap_naive_sum": naive_sum,
        "overlap_deduplicated_union": union_count,
        "omitted_return_rejected": True,
    }


def check_p2_05_06() -> dict:
    witness = {
        "parent_id": "W_B_1",
        "emit_boundary": "dT_R1",
        "emit_cut": 12,
        "route": "exo",
        "X_route": Fraction(1, 2),
        "post_shed_parent_state": "S_W_post_12",
    }
    ctx_fresh = {
        "recipient_lineage": "R_1",
        "recipient_scope": "B_rec:1",
        "window": (10, 20),
        "origin_return_id": None,
        "seen_return_ids": (),
    }
    r_unacc = evaluate_recipient_stage(witness, ctx_fresh, ("emitted", "delivered", "unaccepted_pass"))
    r_pend = evaluate_recipient_stage(
        witness, ctx_fresh, ("emitted", "delivered", "accepted", "pending_unseated")
    )
    r_seat = evaluate_recipient_stage(witness, ctx_fresh, ("emitted", "delivered", "accepted", "seated"))
    require(
        r_unacc["reclosure_bip_delta"] == 0
        and r_pend["reclosure_bip_delta"] == 0
        and r_pend["blocks_later_seating"] is False
        and r_seat["reclosure_bip_delta"] == 0,
        "non-closing recipient stages must add 0 bips and never block later seating",
    )

    c0_wit = {
        "has_certificate": True, "lineage_id": "R_1", "scope_id": "B_rec:1",
        "return_id": "ret:R0", "occurrence_j": 0, "completion_cut": 14,
    }
    r_orig = evaluate_recipient_stage(
        witness, ctx_fresh, ("emitted", "delivered", "accepted", "seated", "closed_origin"), c0_wit
    )
    require(
        r_orig["closure_phase_delta"] == 1 and r_orig["reclosure_bip_delta"] == 0,
        "initial recipient closure must contribute 1 closure phase and 0 bips",
    )

    ctx_after = {
        "recipient_lineage": "R_1",
        "recipient_scope": "B_rec:1",
        "window": (10, 20),
        "origin_return_id": "ret:R0",
        "seen_return_ids": ("ret:R1",),
    }
    c1_replay = {
        "has_certificate": True, "lineage_id": "R_1", "scope_id": "B_rec:1",
        "return_id": "ret:R1", "occurrence_j": 1, "completion_cut": 16,
    }
    r_rep = evaluate_recipient_stage(
        witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"), c1_replay
    )
    require(r_rep["reclosure_bip_delta"] == 0, "replay must add 0 bips")

    c2_fresh = {
        "has_certificate": True, "lineage_id": "R_1", "scope_id": "B_rec:1",
        "return_id": "ret:R2", "occurrence_j": 2, "completion_cut": 18,
    }
    r_fresh = evaluate_recipient_stage(
        witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"), c2_fresh
    )
    require(r_fresh["reclosure_bip_delta"] == 1, "fresh compatible completion must add 1 bip")

    # Negative controls: wrong lineage, wrong scope, skipped stage, missing cert, out-of-window
    reject(
        lambda: evaluate_recipient_stage(
            witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"),
            dict(c2_fresh, lineage_id="R_WRONG"),
        ),
        ValueError, "lineage mismatch",
    )
    reject(
        lambda: evaluate_recipient_stage(
            witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"),
            dict(c2_fresh, scope_id="B_WRONG", scope_mapped=False),
        ),
        ValueError, "scope mismatch",
    )
    reject(
        lambda: evaluate_recipient_stage(witness, ctx_after, ("emitted", "delivered", "reclosed"), c2_fresh),
        ValueError, "illegal stage transition",
    )
    reject(
        lambda: evaluate_recipient_stage(
            witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"),
            dict(c2_fresh, has_certificate=False),
        ),
        ValueError, "certificate",
    )
    r_oow = evaluate_recipient_stage(
        witness, ctx_after, ("emitted", "delivered", "accepted", "seated", "reclosed"),
        dict(c2_fresh, return_id="ret:R3", occurrence_j=3, completion_cut=24),
    )
    require(r_oow["reclosure_bip_delta"] == 0, "out-of-window completion must add 0 bips")

    # Existing passive transport ledger check: routed packets alone supply no reclosure beat
    ledger = {
        "window": [0, 5],
        "packets": [
            {"id": "p0", "emitted": -1, "arrived": 2},
            {"id": "p1", "emitted": 3, "arrived": None},
        ],
        "pending_start": 1,
        "pending_end": 1,
    }
    transport = metrology.validate_transport_ledger(ledger)
    require(
        transport["emitted"] - transport["arrived"] == transport["pending_end"] - transport["pending_start"] == 0,
        "passive transport conservation failed",
    )
    return {
        "closed_origin_bips": r_orig["reclosure_bip_delta"],
        "replay_bips": r_rep["reclosure_bip_delta"],
        "fresh_reclosure_bips": r_fresh["reclosure_bip_delta"],
        "out_of_window_bips": r_oow["reclosure_bip_delta"],
        "passive_transport_net": transport["net"],
    }


def check_p2_07() -> dict:
    c1 = make_return_witness("C1", 1, 2, "W_B_1", "B:main")
    c2 = make_return_witness("C2", 2, 6, "W_B_1", "B:main")
    w_pos = make_wavelet(
        "w_pos", "W_B_1", ("lin:1", "pos"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:pos",), (c1, c2), signed_current=1, is_admitted_wave=True,
    )
    w_neg = make_wavelet(
        "w_neg", "W_B_1", ("lin:1", "neg"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:neg",), (c1, c2), signed_current=-1, is_admitted_wave=True,
    )
    net = w_pos["signed_current"] + w_neg["signed_current"]
    histories = ((w_pos["ancestry"], w_pos["records"]), (w_neg["ancestry"], w_neg["records"]))
    require(net == 0 and len(histories) == 2 and histories[0] != histories[1], "cancellation erased history")

    def register_outer(inner_ids, outer_ids):
        overlap = set(inner_ids) & set(outer_ids)
        require(not overlap, f"inner returns reused as outer: {sorted(overlap)}")
        return len(set(outer_ids))

    require(register_outer(("in_01", "in_02"), ("out_01",)) == 1, "disjoint outer return failed")
    reject(lambda: register_outer(("in_01", "in_02"), ("in_02", "out_01")), ValueError, "reused")
    return {"net_current": net, "retained_histories": 2, "inner_outer_disjoint": True}


def check_p2_08() -> dict:
    require(
        native_cadence_ratio("Wa", 3, "Wr", 5, coupled=True, bound_contacts=2) == Fraction(3, 5),
        "coupled cadence mismatch",
    )
    require(
        native_cadence_ratio("Wshed", 0, "Wr", 10, coupled=True, bound_contacts=2) == Fraction(0, 1),
        "repeated-contact zero-numerator cadence must equal 0",
    )
    reject(lambda: native_cadence_ratio("Wshed", 0, "Wr", 10, coupled=True, bound_contacts=1), ValueError, ">= 2")
    reject(lambda: native_cadence_ratio("Wa", 3, "Wr", 0, coupled=True, bound_contacts=2), ValueError, "positive")
    reject(lambda: native_cadence_ratio("Wa", 3, "Wr", 5, coupled=False, bound_contacts=2), ValueError, "uncoupled")
    reject(lambda: native_cadence_ratio("Wa", 3, "Wa", 5, coupled=True, bound_contacts=2), ValueError, "aliased")
    reject(lambda: native_cadence_ratio("Wa", 3.0, "Wr", 5, coupled=True, bound_contacts=2), TypeError, "exact int")

    assoc = single_contact_stage_association("Wshed", "W_B_1", "Wr", (10, 20), bound_contacts=1)
    require(assoc["is_cadence_ratio"] is False and assoc["biz_tf"] is None, "1-contact typed separately")
    return {
        "coupled_ratio": "3/5",
        "zero_numerator_repeated_contact": "0",
        "single_contact_is_cadence": assoc["is_cadence_ratio"],
    }


def check_p2_09() -> dict:
    compared, reference, realization = metrology.phase_fixture()
    compared.update(winding=0, phase_start="0", phase_end="0")
    reference.update(winding=10, phase_start="0", phase_end="0")
    compared, reference, realization = _rebind_phase_comparison(compared, reference, realization)
    res = metrology.compare_accumulations(compared, reference, realization)
    ang = tau_angular_report(res)
    require(res["compared_advance_turns"] == "0", "nonrecurrent C_a must be 0")
    require(res["reference_advance_turns"] == "10", "reference C_Cs must be 10")
    require(
        metrology.exact(res["duration_seconds"]) == Fraction(10, CS133_DELTA_NU_HZ),
        "nonrecurrent duration mismatch",
    )
    require(res["mean_frequency_hz"] == "0", "nonrecurrent mean rate must be 0")
    require(
        ang["delta_theta_over_tau"] == "0" and ang["omega_bar_over_tau_hz"] == "0",
        "nonrecurrent tau angular outputs must be 0",
    )
    require(
        res["universal_seconds_per_bip"] is False and res["independent_atomic_prediction"] is False,
        "nonrecurrent localization must not claim universal second or independent prediction",
    )
    return {
        "duration_seconds": res["duration_seconds"],
        "mean_frequency_hz": res["mean_frequency_hz"],
        "delta_theta_over_tau": ang["delta_theta_over_tau"],
        "universal_seconds_per_bip": res["universal_seconds_per_bip"],
    }


def check_p2_10() -> dict:
    # Distinct general observation map vs explicit affine specialization
    def general_nonlinear_map(q_i: int) -> Fraction:
        return Fraction(q_i * q_i + 1, 2)

    def affine_map(q_i: int, g_i: Fraction, phi_0: Fraction, phi_1: Fraction) -> Fraction:
        require(g_i > 0, "positive gain required")
        require(Fraction(0) <= phi_0 < 1 and Fraction(0) <= phi_1 < 1, "endpoint domain [0, 1)")
        return g_i * q_i + (phi_1 - phi_0)

    require(
        general_nonlinear_map(2) != affine_map(2, Fraction(1), Fraction(0), Fraction(0)),
        "general O_i must stay distinct from affine specialization",
    )

    # Signed compared advance C_a = -1/2 against positive Cs reference C_Cs = 1 via real metrology API
    c_a_aff = affine_map(0, Fraction(1), Fraction(3, 4), Fraction(1, 4))
    require(c_a_aff == Fraction(-1, 2), "affine signed advance must equal -1/2")

    compared, reference, realization = metrology.phase_fixture()
    compared.update(winding=0, phase_start="3/4", phase_end="1/4")
    reference.update(winding=1, phase_start="0", phase_end="0")
    compared, reference, realization = _rebind_phase_comparison(compared, reference, realization)
    res = metrology.compare_accumulations(compared, reference, realization)
    ang = tau_angular_report(res)
    require(res["compared_advance_turns"] == "-1/2", "signed C_a mismatch")
    require(
        metrology.exact(res["duration_seconds"]) == Fraction(1, CS133_DELTA_NU_HZ),
        "signed-advance reference duration mismatch",
    )
    require(
        metrology.exact(res["mean_frequency_hz"]) == Fraction(-CS133_DELTA_NU_HZ, 2),
        "signed mean phase rate must equal -Delta_nu_Cs/2",
    )
    require(
        ang["delta_theta_over_tau"] == "-1/2"
        and ang["omega_bar_over_tau_hz"] == str(Fraction(-CS133_DELTA_NU_HZ, 2))
        and ang["rate_kind"] == "signed_mean_phase_rate",
        "signed tau angular readout mismatch",
    )

    def nonnegative_resonance_specialization(c_a: Fraction):
        require(c_a >= 0, "nonnegative specialization requires C_a >= 0")
        return c_a

    reject(lambda: nonnegative_resonance_specialization(c_a_aff), ValueError, "C_a >= 0")

    # Nonpositive reference advance rejected
    bad_comp, bad_ref, bad_real = metrology.phase_fixture()
    bad_ref.update(winding=0, phase_start="0", phase_end="0")
    bad_comp, bad_ref, bad_real = _rebind_phase_comparison(bad_comp, bad_ref, bad_real)
    reject(
        lambda: metrology.compare_accumulations(bad_comp, bad_ref, bad_real),
        ValueError, "positive",
    )
    return {
        "signed_C_a": res["compared_advance_turns"],
        "duration_seconds": res["duration_seconds"],
        "signed_mean_frequency_hz": res["mean_frequency_hz"],
        "delta_theta_over_tau": ang["delta_theta_over_tau"],
        "omega_bar_over_tau_hz": ang["omega_bar_over_tau_hz"],
        "rate_kind": ang["rate_kind"],
    }


def check_p2_11() -> dict:
    compared, reference, realization = metrology.phase_fixture()
    res = metrology.compare_accumulations(compared, reference, realization)
    ang = tau_angular_report(res)
    require(res["compared_advance_turns"] == "7/2", "7/2 advance mismatch")
    require(res["reference_advance_turns"] == "17/2", "17/2 advance mismatch")
    require(res["ratio"] == "7/17", "7/17 ratio mismatch")
    require(res["duration_seconds"] == "17/18385263540", "duration mismatch")
    require(res["mean_frequency_hz"] == "64348422390/17", "mean frequency mismatch")
    require(
        ang["delta_theta_over_tau"] == "7/2"
        and ang["omega_bar_over_tau_hz"] == "64348422390/17",
        "tau angular report mismatch on 7/2 fixture",
    )
    # Exact endpoint additivity / cancellation at midpoint phase 5/6
    left = deepcopy(compared)
    left.update(window=[10, 16], winding=2, phase_end="5/6")
    right = deepcopy(compared)
    right.update(window=[16, 22], winding=2, phase_start="5/6")
    require(
        metrology.phase_advance(left) == Fraction(13, 6)
        and metrology.phase_advance(right) == Fraction(4, 3)
        and metrology.phase_advance(left) + metrology.phase_advance(right) == Fraction(7, 2),
        "endpoint cancellation failed",
    )
    # Dropping endpoints fails 7/2
    dropped = deepcopy(compared)
    dropped.update(phase_start="0", phase_end="0")
    require(metrology.phase_advance(dropped) == Fraction(4) != Fraction(7, 2), "dropped endpoint check")
    # Mismatched window rejected
    mis_c, mis_r, mis_real = metrology.phase_fixture()
    mis_c["window"] = [11, 23]
    mis_c, mis_r, mis_real = _rebind_phase_comparison(mis_c, mis_r, mis_real)
    reject(lambda: metrology.compare_accumulations(mis_c, mis_r, mis_real), ValueError, "matched")
    # Promoting conditional fixture to experimentally validated rejected even with rebound source
    bad_c, bad_r, bad_real = metrology.phase_fixture()
    bad_real["physical_correspondence"] = "experimentally_validated"
    bad_c, bad_r, bad_real = _rebind_phase_comparison(bad_c, bad_r, bad_real)
    reject(lambda: metrology.compare_accumulations(bad_c, bad_r, bad_real), ValueError, "certify")
    return {
        "ratio": res["ratio"],
        "duration_seconds": res["duration_seconds"],
        "mean_frequency_hz": res["mean_frequency_hz"],
        "delta_theta_over_tau": ang["delta_theta_over_tau"],
        "omega_bar_over_tau_hz": ang["omega_bar_over_tau_hz"],
        "split_sum": "13/6 + 4/3 = 7/2",
    }


def check_p2_12() -> dict:
    h_proto = metrology.load_profile("hydrogen")
    cs_proto = metrology.load_profile("cesium")
    h_iv = metrology.reduce_hydrogen(h_proto, "table_iv")
    h_vi = metrology.reduce_hydrogen(h_proto, "table_vi")
    h_mean = metrology.reduce_hydrogen(h_proto, "published_mean")
    cs_aug = metrology.reduce_cesium(cs_proto, "August2013")
    cs_typ = metrology.reduce_cesium(cs_proto, "typical_Table1")
    require(h_iv["method"] != cs_aug["method"], "H-maser and Cs-fountain chains must stay distinct")
    require(h_iv["corrected_frequency_hz"] == "14204057517691/10000", "H Table IV mismatch")
    require(h_vi["corrected_frequency_hz"] == "14204057517667/10000", "H Table VI mismatch")
    require(h_mean["corrected_frequency_hz"] == "14204057517679/10000", "H mean mismatch")
    require(h_vi["correction_ownership"]["already_in_input"] == ["NP3", "wall"], "H ownership mismatch")
    require(cs_aug["Cs_SI_frequency_role"] == "calibration_identity", "Cs anchor role mismatch")
    require(cs_aug["nominal_synthesis_is_exact_carrier"] is False, "nominal synthesis check failed")
    require(
        cs_aug["source_reported_uncertainty"]["TypeB"]["printed_fractional_times_1e15"] == "0.16"
        and cs_typ["source_reported_uncertainty"]["TypeB"]["printed_fractional_times_1e15"] == "0.11",
        "Cs August 2013 vs typical Table 1 budgets must stay separate",
    )
    require(
        h_iv["complete_physical_uncertainty"]["kind"] == "unknown"
        and "value" not in h_iv["complete_physical_uncertainty"],
        "unknown uncertainty must not be coerced to 0",
    )
    require(
        h_mean["independent_atomic_prediction"] is False
        and cs_aug["independent_atomic_prediction"] is False,
        "measured reductions are not independent predictions",
    )
    # Negative controls: double-applied correction and independent_prediction claim rejected
    c_rec, r_rec, real = metrology.phase_fixture()
    r_rec["corrections"] = [
        {"id": "dup", "source_id": "fixture:phase", "value_turns": "0", "already_applied": True}
    ]
    reject(lambda: metrology.compare_accumulations(c_rec, r_rec, real), ValueError, "correction")
    bad_indep, _, real2 = metrology.phase_fixture()
    bad_indep["evidence_class"] = "independent_prediction"
    reject(
        lambda: metrology.validate_observation(bad_indep, real2["trusted_sources"]),
        ValueError, "independent physical prediction",
    )
    return {
        "h_method": h_iv["method"],
        "cs_method": cs_aug["method"],
        "h_exact_mean_hz": h_mean["corrected_frequency_hz"],
        "cs_aug2013_typeB_1e15": "0.16",
        "cs_typical_typeB_1e15": "0.11",
        "unknown_uncertainty_preserved": True,
    }


def check_p2_13() -> dict:
    # Read-only provenance audit of frozen Tau ring CSVs & 90-tick shedding simulation CSV
    diag_path = ROOT / "manual" / "data" / "derived" / "tau_ring_diagnostic.csv"
    ring_path = ROOT / "manual" / "data" / "tau" / "aod_tau_fractal_ring_summary.csv"
    shed_path = ROOT / "wavelet_shedding_simulation.csv"

    with diag_path.open(newline="", encoding="utf-8") as fh:
        diag_rows = {row["K"]: row for row in csv.DictReader(fh)}
    with ring_path.open(newline="", encoding="utf-8") as fh:
        ring_1210 = [row for row in csv.DictReader(fh) if row["candidate"] == "1:2:10"]
    with shed_path.open(newline="", encoding="utf-8") as fh:
        shed_rows = list(csv.DictReader(fh))

    diag_1210 = Fraction(diag_rows["1:2:10"]["missing_fraction"])
    require(diag_1210 == Fraction(9, 20), "tau_ring_diagnostic 1:2:10 must remain exact 9/20")
    require(len(ring_1210) == 3, "expected 3 depth rows for 1:2:10 in ring summary")
    for row in ring_1210:
        val = Fraction(row["missing_fraction"])
        require(
            abs(val - Fraction(23, 50)) < Fraction(1, 10**12),
            "ring summary 1:2:10 missing_fraction expected near 23/50",
        )
    require(Fraction(9, 20) != Fraction(23, 50), "9/20 vs 23/50 is a genuine rational change")
    require(
        len(shed_rows) == 90 and all(row["state"] == "open" for row in shed_rows),
        "wavelet_shedding_simulation.csv must have 90 open rows",
    )

    # Semantic quantity-kind separation guard (bit-window span 8160 vs summed per-lineage closure count 9104)
    q_span = {"kind": "bit_window_span", "value": 8160}
    q_sum = {"kind": "summed_per_lineage_closure_count", "value": 9104}
    reject(lambda: compare_typed_quantities(q_span, q_sum), ValueError, "semantic quantity kind mismatch")
    require(
        compare_typed_quantities(
            {"kind": "missing_fraction", "value": Fraction(23, 50)},
            {"kind": "missing_fraction", "value": Fraction(9, 20)},
        )
        == Fraction(1, 100),
        "23/50 - 9/20 must equal 1/100",
    )
    return {
        "changed_csvs": 0,
        "tau_ring_diagnostic_1210": str(diag_1210),
        "tau_ring_summary_1210_nominal": "23/50",
        "rational_difference": "1/100",
        "tau_ring_generator_status": "UNRESOLVED_NOT_AUTHENTICATED_IN_REPO",
        "shedding_fixture_ticks": len(shed_rows),
        "shedding_lambda_reclose": "19/50",
        "shedding_certifies_native_reclosure_or_exo": False,
        "bit_span_vs_summed_lineage_counts_rejected": True,
    }


def check_p2_14() -> dict:
    auditor = _load_source_auditor()
    audit_out = auditor.audit(ROOT)
    comp = audit_out["compaction"]
    require(
        (comp["canonical_groups"], comp["canonical_equations"], comp["declared_dependencies"])
        == (44, 81, 72),
        "inherited canonical equation counts changed",
    )
    require(
        comp["m3_wavelet_compaction"]["new_equations"] == 10
        and comp["m3_wavelet_compaction"]["new_anchors"] == 2,
        "Main Phase 1 wavelet compaction counts changed",
    )

    # Verify all 166 frozen SHA-256 bindings remain intact
    cb = json.loads((ROOT / "contracts" / "scientific" / "CANONICAL_BINDINGS.json").read_text())
    frozen = cb["frozen_sha256"]
    for rel, expected_sha in frozen.items():
        actual_sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        require(actual_sha == expected_sha, f"frozen file changed: {rel}")

    # Verify all \mainequation, \mainsection, \mainappendix in aligned Manual files bind validly
    main_eqs = auditor.equations(ROOT)
    main_labels = auditor.label_map(ROOT)
    found_refs: dict[str, list[str]] = {}
    all_main_eq_refs: set[str] = set()
    all_main_sec_refs: set[str] = set()
    for rel in ALIGNED_MANUAL_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        refs = re.findall(r"\\(mainequation|mainsection|mainappendix)\{main:([^}]+)\}", text)
        found_refs[rel] = sorted({f"{k}:{v}" for k, v in refs})
        for kind, key in refs:
            require(key in main_labels, f"unresolved Main label {key} in {rel}")
            if kind == "mainequation":
                require(key in main_eqs, f"non-equation target {key} in \\mainequation in {rel}")
                all_main_eq_refs.add(key)
            elif kind == "mainsection":
                require(
                    main_labels[key]["path"].startswith("sections/"),
                    f"non-section target {key} in \\mainsection in {rel}",
                )
                all_main_sec_refs.add(key)
            elif kind == "mainappendix":
                require(
                    main_labels[key]["path"].startswith("appendices/"),
                    f"non-appendix target {key} in \\mainappendix in {rel}",
                )

    expected_phase1_eqs = {
        "eq:duad-same-current",
        "eq:aod-wavelet-continuation",
        "eq:wavelet-overlap-dedup",
        "eq:wavelet-cancellation-retention",
        "eq:wavelet-reference-timing",
        "eq:shed-continuation-witness",
        "eq:recipient-event-lattice",
        "eq:m3-observation-map",
        "eq:m3-conditional-si-anchor",
        "eq:m3-cs133-tau-interface",
    }
    expected_phase1_secs = {
        "subsec:aod-wavelet-continuation",
        "subsec:m3-conditional-si-interface",
    }
    require(
        expected_phase1_eqs <= all_main_eq_refs,
        f"missing Phase 1 Main equation references: {sorted(expected_phase1_eqs - all_main_eq_refs)}",
    )
    require(
        expected_phase1_secs <= all_main_sec_refs,
        f"missing Phase 1 Main section references: {sorted(expected_phase1_secs - all_main_sec_refs)}",
    )

    # Confirm zero forbidden experimental engine references in aligned Manual files and this script
    forbidden = re.compile(r"aod[-_]" + r"dec", re.IGNORECASE)
    for rel in (*ALIGNED_MANUAL_FILES, "manual/scripts/aod_manual_wavelet_si_alignment.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        require(forbidden.search(text) is None, f"forbidden experimental token in {rel}")

    return {
        "frozen_files_verified": len(frozen),
        "phase1_equations_bound_in_manual": len(expected_phase1_eqs),
        "phase1_sections_bound_in_manual": len(expected_phase1_secs),
        "aligned_file_ref_counts": {k: len(v) for k, v in found_refs.items()},
    }


def check_p2_15() -> dict:
    # Exact rational finite harmonic overtone on Z_12 with pulse support {0, 4, 8} (l_min = 4)
    n_order = 12
    l_min = 4
    pulses = (0, 4, 8)
    m_mode = 3
    require(Fraction(m_mode) > Fraction(n_order, 2 * l_min), "m=3 must exceed N/(2*l_min)")
    # For g in {0, 4, 8}, exp(-2*pi*i*m*g/12) sums to 3 when 3 | m and 0 otherwise (1 + w_3 + w_3^2 = 0)
    v_hat = {
        m: (Fraction(len(pulses), n_order) if (m % 3 == 0) else Fraction(0))
        for m in range(n_order)
    }
    require(v_hat[m_mode] == Fraction(1, 4) and v_hat[m_mode] != 0, "exact overtone v_hat(3) != 1/4")
    time_energy = Fraction(len(pulses), n_order)
    freq_energy = sum(val * val for val in v_hat.values())
    require(time_energy == freq_energy == Fraction(1, 4), "Parseval identity mismatch on Z_12")
    return {
        "group_order": n_order,
        "pulse_support": list(pulses),
        "l_min": l_min,
        "overtone_mode": m_mode,
        "v_hat_3": str(v_hat[m_mode]),
        "parseval_exact": str(freq_energy),
        "certifies_native_reclosure_or_si_frequency": False,
    }


def run_all_checks() -> dict:
    return {
        "schema": "aod.manual.wavelet-si-alignment.v1",
        "P2-01": check_p2_01(),
        "P2-02": check_p2_02(),
        "P2-03_P2-04": check_p2_03_04(),
        "P2-05_P2-06": check_p2_05_06(),
        "P2-07": check_p2_07(),
        "P2-08": check_p2_08(),
        "P2-09": check_p2_09(),
        "P2-10": check_p2_10(),
        "P2-11": check_p2_11(),
        "P2-12": check_p2_12(),
        "P2-13": check_p2_13(),
        "P2-14": check_p2_14(),
        "P2-15": check_p2_15(),
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="execute all passive alignment checks")
    args = parser.parse_args()
    if not args.check:
        parser.error("pass --check to run passive alignment verification")
    report = run_all_checks()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
