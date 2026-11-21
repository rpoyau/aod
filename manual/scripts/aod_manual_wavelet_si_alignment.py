#!/usr/bin/env python3
"""Passive exact Manual alignment verifier for wavelet continuations and conditional SI mapping.

Reuses existing Manual native-closure (`aod_native_closure_wave`), metrology
(`aod_temporal_metrology`), mapping-error (`aod_mapping_error`), and source-auditor
(`scripts/audit_scientific_sources.py`) modules passively without modifying native
D.E.C. transitions, frozen data records, or scientific contracts. Uses exact `int`
and `fractions.Fraction` arithmetic only and explicit `ValueError`/`TypeError`
checks (active under both normal `python3` and `python3 -O`).
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
MANUAL_SCRIPTS = ROOT / "manual" / "scripts"
if str(MANUAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MANUAL_SCRIPTS))

import aod_mapping_error as mapping_error  # noqa: E402
import aod_native_closure_wave as native  # noqa: E402
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
NON_CLOSURE_RECIPIENT_STAGES = frozenset(
    {"delivered", "accepted", "unaccepted_pass", "seated", "pending_unseated"}
)

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


def require_nonempty_str(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def require_exact_bool(value, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be an exact bool, got {type(value).__name__}")
    return value


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


# --- F01 & F02: Canonical occurrence binding, native passive projection & explicit scope maps ---


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


def _make_admitted_return_witness(
    trace_obj: native.Trace,
    cert_obj: native.Certificate,
    cert_registry: Mapping[str, native.Certificate],
    occurrence_j: int,
    lineage_prefix_digest: str,
    *,
    cut_coordinate: str = "native_cut",
    compatible: bool = True,
    display_label: str | None = None,
) -> dict:
    """Internal constructor binding an admitted native trace within a validated ordered lineage."""
    require(
        isinstance(trace_obj, native.Trace) and isinstance(cert_obj, native.Certificate),
        "admitted native witness requires Trace and Certificate instances",
    )
    require(isinstance(cert_registry, Mapping), "certificate registry mapping required")
    native.admitted(trace_obj, cert_obj, cert_registry)
    j = require_exact_int(occurrence_j, "occurrence_j")
    require(j >= 0, "occurrence_j must be non-negative")
    pref = require_nonempty_str(lineage_prefix_digest, "lineage_prefix_digest")
    coord = require_nonempty_str(cut_coordinate, "cut_coordinate")
    comp = require_exact_bool(compatible, "compatible")
    label = None if display_label is None else require_nonempty_str(display_label, "display_label")
    require(
        trace_obj.return_id == cert_obj.return_id,
        "Trace.return_id and Certificate.return_id mismatch",
    )
    return {
        "record_kind": "admitted_native_trace",
        "authenticated_trace": True,
        "return_id": trace_obj.return_id,
        "display_label": label,
        "occurrence_j": j,
        "start_cut": trace_obj.indices[0],
        "completion_cut": trace_obj.indices[-1],
        "lineage_id": trace_obj.lineage,
        "scope_id": trace_obj.scope,
        "scale": trace_obj.scale,
        "cut_coordinate": coord,
        "compatible": comp,
        "ancestor": trace_obj.ancestor,
        "lineage_prefix_digest": pref,
        "trace_digest": trace_obj.trace_digest,
        "certificate_digest": cert_obj.certificate_digest,
        "trace": trace_obj,
        "certificate": cert_obj,
        "certificate_registry": dict(cert_registry),
    }


def project_admitted_lineage_occurrences(
    certified_records: Sequence[tuple],
    *,
    cut_coordinate: str = "native_cut",
    display_prefix: str = "C",
) -> tuple[dict, ...]:
    """Derive canonical occurrences (origin j=0) from validated ordered native closure records."""
    require(
        isinstance(certified_records, (tuple, list)) and len(certified_records) > 0,
        "certified_records must be a non-empty sequence",
    )
    prefix = require_nonempty_str(display_prefix, "display_prefix")
    if len(certified_records) == 1:
        item = certified_records[0]
        require(isinstance(item, tuple) and len(item) == 3, "certified record must be a 3-tuple")
        t0, c0, reg0 = item
        native.admitted(t0, c0, reg0)
        require(
            native.closure_cycle_count([item]) == 1,
            "origin closure failed closure_cycle_count==1 check",
        )
        pref_digest = native.digest((t0.return_id,))
        return (
            _make_admitted_return_witness(
                t0,
                c0,
                reg0,
                0,
                pref_digest,
                cut_coordinate=cut_coordinate,
                compatible=True,
                display_label=f"{prefix}0",
            ),
        )

    w_obj = native.wave(certified_records)
    native.validate_wave(w_obj)
    merged_reg = {c.certificate_digest: c for c in w_obj.certificates}
    norm_records = [(t, c, merged_reg) for t, c in zip(w_obj.returns, w_obj.certificates)]
    require(
        native.closure_cycle_count(norm_records) == len(w_obj.returns),
        "closure_cycle_count disagrees with admitted wave return count",
    )
    out = []
    for idx, (t, c) in enumerate(zip(w_obj.returns, w_obj.certificates)):
        pref_digest = native.digest(tuple(x.return_id for x in w_obj.returns[: idx + 1]))
        out.append(
            _make_admitted_return_witness(
                t,
                c,
                merged_reg,
                idx,
                pref_digest,
                cut_coordinate=cut_coordinate,
                compatible=True,
                display_label=f"{prefix}{idx}",
            )
        )
    return tuple(out)


def project_admitted_wave_occurrences(
    wave_obj: native.Wave,
    *,
    cut_coordinate: str = "native_cut",
    display_prefix: str = "C",
) -> tuple[dict, ...]:
    """Passively project an admitted native Wave into ordered canonical occurrences (origin j=0)."""
    native.validate_wave(wave_obj)
    cert_registry = {c.certificate_digest: c for c in wave_obj.certificates}
    records = [(t, c, cert_registry) for t, c in zip(wave_obj.returns, wave_obj.certificates)]
    return project_admitted_lineage_occurrences(
        records, cut_coordinate=cut_coordinate, display_prefix=display_prefix
    )


def declare_synthetic_lineage_registry(
    lineage_id: str,
    scope_id: str,
    completion_cuts: Sequence[int],
    *,
    scale: int = 0,
    cut_coordinate: str = "native_cut",
    display_labels: Sequence[str] | None = None,
) -> tuple[tuple[dict, ...], dict[str, dict]]:
    """Derive ordered finite-model occurrences (origin j=0) with display labels separate from IDs."""
    lin = require_nonempty_str(lineage_id, "lineage_id")
    scp = require_nonempty_str(scope_id, "scope_id")
    coord = require_nonempty_str(cut_coordinate, "cut_coordinate")
    scl = require_exact_int(scale, "scale")
    require(
        isinstance(completion_cuts, (tuple, list)) and len(completion_cuts) > 0,
        "completion_cuts must be non-empty",
    )
    cuts = [require_exact_int(c, "completion_cut") for c in completion_cuts]
    require(
        all(a < b for a, b in zip(cuts, cuts[1:])),
        "synthetic lineage completion_cuts must be strictly increasing",
    )
    if display_labels is not None:
        require(
            len(display_labels) == len(cuts),
            "display_labels length must match completion_cuts length",
        )
        labels = [require_nonempty_str(lbl, "display_label") for lbl in display_labels]
    else:
        labels = [f"C{idx}" for idx in range(len(cuts))]
    witnesses = tuple(
        make_return_witness(
            f"syn:{lin}:{scp}:s{scl}:{coord}:j{idx}:k{cut}",
            idx,
            cut,
            lin,
            scp,
            scale=scl,
            cut_coordinate=coord,
            compatible=True,
            display_label=labels[idx],
        )
        for idx, cut in enumerate(cuts)
    )
    return witnesses, build_occurrence_registry(witnesses)


def make_return_witness(
    return_id: str,
    occurrence_j: int,
    completion_cut: int,
    lineage_id: str,
    scope_id: str,
    *,
    scale: int = 0,
    cut_coordinate: str = "native_cut",
    compatible: bool = True,
    display_label: str | None = None,
) -> dict:
    """Construct a declared finite-model occurrence witness (no implicit scope_mapped flag)."""
    rid = require_nonempty_str(return_id, "return_id")
    lin = require_nonempty_str(lineage_id, "lineage_id")
    scp = require_nonempty_str(scope_id, "scope_id")
    coord = require_nonempty_str(cut_coordinate, "cut_coordinate")
    j = require_exact_int(occurrence_j, "occurrence_j")
    cut = require_exact_int(completion_cut, "completion_cut")
    scl = require_exact_int(scale, "scale")
    comp = require_exact_bool(compatible, "compatible")
    require(j >= 0, "occurrence_j must be non-negative")
    require(scl >= 0, "scale must be non-negative")
    label = rid if display_label is None else require_nonempty_str(display_label, "display_label")
    return {
        "record_kind": "declared_synthetic_occurrence",
        "authenticated_trace": False,
        "return_id": rid,
        "display_label": label,
        "occurrence_j": j,
        "start_cut": None,
        "completion_cut": cut,
        "lineage_id": lin,
        "scope_id": scp,
        "scale": scl,
        "cut_coordinate": coord,
        "compatible": comp,
        "ancestor": None,
        "lineage_prefix_digest": None,
        "trace_digest": None,
        "certificate_digest": None,
    }


def _immutable_occurrence_payload(record: Mapping) -> tuple:
    require(isinstance(record, Mapping), "occurrence witness must be a mapping")
    require(
        "scope_mapped" not in record,
        "implicit scope_mapped flag is forbidden; supply an explicit scope_map when scopes differ",
    )
    kind = record.get("record_kind")
    require(
        kind in {"admitted_native_trace", "declared_synthetic_occurrence"},
        "occurrence witness must declare a valid record_kind",
    )
    rid = require_nonempty_str(record.get("return_id"), "return_id")
    lin = require_nonempty_str(record.get("lineage_id"), "lineage_id")
    scp = require_nonempty_str(record.get("scope_id"), "scope_id")
    coord = require_nonempty_str(record.get("cut_coordinate"), "cut_coordinate")
    j = require_exact_int(record.get("occurrence_j"), "occurrence_j")
    cut = require_exact_int(record.get("completion_cut"), "completion_cut")
    scl = require_exact_int(record.get("scale"), "scale")
    comp = require_exact_bool(record.get("compatible"), "compatible")
    require(j >= 0 and scl >= 0, "occurrence_j and scale must be non-negative")

    if kind == "admitted_native_trace":
        require(record.get("authenticated_trace") is True, "admitted trace flag mismatch")
        t = record.get("trace")
        c = record.get("certificate")
        reg = record.get("certificate_registry")
        require(
            isinstance(t, native.Trace)
            and isinstance(c, native.Certificate)
            and isinstance(reg, Mapping),
            "admitted_native_trace missing bound Trace/Certificate/registry",
        )
        native.admitted(t, c, reg)
        require(
            rid == t.return_id == c.return_id,
            "admitted occurrence return_id does not match Trace.return_id",
        )
        require(
            (lin, scp, scl, cut, record.get("start_cut"), record.get("ancestor"))
            == (t.lineage, t.scope, t.scale, t.indices[-1], t.indices[0], t.ancestor),
            "admitted occurrence metadata diverges from bound Trace",
        )
        require(
            (record.get("trace_digest"), record.get("certificate_digest"))
            == (t.trace_digest, c.certificate_digest),
            "admitted occurrence digests diverge from bound Trace/Certificate",
        )
        return (
            kind,
            rid,
            lin,
            scp,
            scl,
            coord,
            j,
            t.indices[0],
            cut,
            comp,
            t.ancestor,
            t.trace_digest,
            c.certificate_digest,
        )

    require(
        record.get("authenticated_trace") is False
        and record.get("trace_digest") is None
        and record.get("certificate_digest") is None,
        "declared_synthetic_occurrence must not claim authenticated trace/certificate digests",
    )
    return (kind, rid, lin, scp, scl, coord, j, None, cut, comp, None, None, None)


def build_occurrence_registry(records: Sequence[Mapping] | Mapping[str, Mapping]) -> dict[str, dict]:
    """Validate an injective, anti-aliased canonical occurrence registry."""
    if isinstance(records, Mapping):
        items = list(records.values())
    elif isinstance(records, (tuple, list)):
        items = list(records)
    else:
        raise TypeError("occurrence records must be a sequence or registry mapping")

    by_id: dict[str, dict] = {}
    payload_by_id: dict[str, tuple] = {}
    by_occ_slot: dict[tuple, str] = {}
    by_cut_slot: dict[tuple, str] = {}
    lineage_kinds: dict[tuple, str] = {}
    grouped: dict[tuple, list[dict]] = {}

    for raw in items:
        payload = _immutable_occurrence_payload(raw)
        rid = raw["return_id"]
        if rid in payload_by_id:
            require(
                payload_by_id[rid] == payload,
                f"return_id collision for {rid!r}: conflicting immutable occurrence payloads",
            )
            continue

        stream_key = (raw["lineage_id"], raw["scope_id"], raw["scale"], raw["cut_coordinate"])
        prev_kind = lineage_kinds.get(stream_key)
        require(
            prev_kind is None or prev_kind == raw["record_kind"],
            f"mixed native and synthetic occurrence kinds on {stream_key}",
        )
        lineage_kinds[stream_key] = raw["record_kind"]

        occ_key = (*stream_key, raw["occurrence_j"])
        if occ_key in by_occ_slot:
            raise ValueError(
                f"canonical occurrence j={raw['occurrence_j']} on {stream_key} aliased under "
                f"multiple return_ids ({by_occ_slot[occ_key]!r}, {rid!r})"
            )
        by_occ_slot[occ_key] = rid

        cut_key = (*stream_key, raw["completion_cut"])
        if cut_key in by_cut_slot:
            raise ValueError(
                f"canonical completion cut {raw['completion_cut']} on {stream_key} aliased under "
                f"multiple return_ids ({by_cut_slot[cut_key]!r}, {rid!r})"
            )
        by_cut_slot[cut_key] = rid

        stored = dict(raw)
        by_id[rid] = stored
        payload_by_id[rid] = payload
        grouped.setdefault(stream_key, []).append(stored)

    for stream_key, members in grouped.items():
        ordered = sorted(members, key=lambda r: r["occurrence_j"])
        for left, right in zip(ordered, ordered[1:]):
            require(
                left["completion_cut"] < right["completion_cut"],
                f"non-monotonic occurrence cuts on {stream_key}: "
                f"j={left['occurrence_j']}@{left['completion_cut']} vs "
                f"j={right['occurrence_j']}@{right['completion_cut']}",
            )
            if left["record_kind"] == "admitted_native_trace":
                require(
                    left["trace"].indices[-1] < right["trace"].indices[0],
                    f"admitted native traces overlap or invert causal order on {stream_key}",
                )
                require(
                    left["trace"].ancestor == right["trace"].ancestor,
                    f"admitted native traces changed retained ancestor on {stream_key}",
                )
        if ordered and ordered[0]["record_kind"] == "admitted_native_trace":
            native_recs = [
                (r["trace"], r["certificate"], r["certificate_registry"]) for r in ordered
            ]
            require(
                native.closure_cycle_count(native_recs) == len(ordered),
                "native closure_cycle_count mismatch on registry stream",
            )

    if isinstance(records, Mapping):
        require(set(records.keys()) == set(by_id.keys()), "registry key/return_id mismatch")
    return by_id


def declare_conditional_scope_map(
    map_id: str,
    source_scope: str,
    target_scope: str,
    lineage_id: str,
    occurrence_records: Sequence[Mapping],
    *,
    scale: int = 0,
) -> dict:
    """Declare an explicit conditional identity-preserving cross-scope map for a finite model."""
    mid = require_nonempty_str(map_id, "map_id")
    src = require_nonempty_str(source_scope, "source_scope")
    dst = require_nonempty_str(target_scope, "target_scope")
    lin = require_nonempty_str(lineage_id, "lineage_id")
    scl = require_exact_int(scale, "scale")
    require(scl >= 0, "scale must be non-negative")
    require(src != dst, "conditional scope map requires distinct source and target scopes")
    canon = build_occurrence_registry(occurrence_records)
    require(bool(canon), "conditional scope map requires at least one bound occurrence")
    bound_payloads: dict[str, tuple] = {}
    for rid, rec in canon.items():
        require(
            (rec["lineage_id"], rec["scope_id"], rec["scale"]) == (lin, src, scl),
            "occurrence in conditional scope map does not match declared source scope/lineage/scale",
        )
        bound_payloads[rid] = _immutable_occurrence_payload(rec)
    return {
        "kind": "declared_conditional_scope_map",
        "authenticated_native_isomorphism": False,
        "map_id": mid,
        "source_scope": src,
        "target_scope": dst,
        "lineage_id": lin,
        "scale": scl,
        "bound_occurrences": bound_payloads,
    }


def validate_scope_map(
    scope_map,
    witness: Mapping,
    *,
    target_scope: str,
    target_lineage: str,
) -> str:
    """Validate an explicit cross-scope map; reject absent/Boolean/fold-proposal substitutes."""
    require(
        scope_map is not None,
        f"cross-scope witness ({witness['scope_id']!r} != {target_scope!r}) requires an "
        "explicit validated scope_map; default is absent",
    )
    require(
        not isinstance(scope_map, bool),
        "Boolean flag cannot establish cross-scope compatibility",
    )
    require(
        isinstance(scope_map, Mapping)
        and scope_map.get("kind") == "declared_conditional_scope_map",
        "cross-scope compatibility requires a declared_conditional_scope_map (a specialized fold "
        "proposal is not a generic scope-isomorphism map)",
    )
    require_nonempty_str(scope_map.get("map_id"), "scope_map.map_id")
    require(
        scope_map.get("source_scope") == witness["scope_id"]
        and scope_map.get("target_scope") == target_scope
        and scope_map.get("source_scope") != scope_map.get("target_scope"),
        "scope_map source/target scope mismatch",
    )
    require(
        scope_map.get("lineage_id") == target_lineage == witness["lineage_id"]
        and scope_map.get("scale") == witness["scale"],
        "scope_map lineage/scale mismatch",
    )
    bound = scope_map.get("bound_occurrences")
    require(isinstance(bound, Mapping) and bool(bound), "scope_map missing bound_occurrences")
    rid = witness["return_id"]
    require(rid in bound, f"return_id {rid!r} is not bound in supplied scope_map")
    require(
        bound[rid] == _immutable_occurrence_payload(witness),
        f"return_id {rid!r} payload conflicts with bound occurrence in scope_map",
    )
    return rid


def eligible_return_ids(
    wavelet: Mapping,
    target_lineage: str | None = None,
    target_scope: str | None = None,
    *,
    scope_map=None,
    registry: Sequence[Mapping] | Mapping[str, Mapping] | None = None,
) -> set[str]:
    require(wavelet["witnesses_complete"], "complete eligible return records required")
    lineage = wavelet["parent_id"] if target_lineage is None else require_nonempty_str(target_lineage, "target_lineage")
    scope = wavelet["scope_id"] if target_scope is None else require_nonempty_str(target_scope, "target_scope")
    require(wavelet["parent_id"] == lineage, "incompatible parent lineage")
    if scope_map is not None and isinstance(scope_map, bool):
        raise ValueError("Boolean flag cannot establish cross-scope compatibility")

    local_reg = build_occurrence_registry(wavelet["return_witnesses"])
    canon_reg = None if registry is None else build_occurrence_registry(registry)

    u, v = wavelet["window"]
    coord = wavelet["cut_coordinate"]
    eligible: set[str] = set()
    for rid, item in local_reg.items():
        if canon_reg is not None:
            require(
                rid in canon_reg,
                f"selected return_id {rid!r} is absent from canonical occurrence registry",
            )
            require(
                _immutable_occurrence_payload(item) == _immutable_occurrence_payload(canon_reg[rid]),
                f"selected return witness {rid!r} conflicts with canonical occurrence record",
            )
        require(item["lineage_id"] == lineage, "return witness lineage mismatch")
        require(
            item["cut_coordinate"] == coord,
            "return witness cut_coordinate differs from wavelet window coordinate",
        )
        if item["scope_id"] != scope:
            validate_scope_map(
                scope_map,
                item,
                target_scope=scope,
                target_lineage=lineage,
            )
        if item["compatible"] and item["occurrence_j"] >= 1 and (u < item["completion_cut"] <= v):
            eligible.add(rid)
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
    *,
    cut_coordinate: str = "native_cut",
    scope_map=None,
    registry: Sequence[Mapping] | Mapping[str, Mapping] | None = None,
) -> dict:
    wid = require_nonempty_str(wavelet_id, "wavelet_id")
    pid = require_nonempty_str(parent_id, "parent_id")
    scp = require_nonempty_str(scope_id, "scope_id")
    coord = require_nonempty_str(cut_coordinate, "cut_coordinate")
    require(
        isinstance(ancestry, (tuple, list)) and len(ancestry) > 0,
        "wavelet must retain non-empty ancestry",
    )
    anc_tuple = tuple(require_nonempty_str(x, "ancestry entry") for x in ancestry)
    require(sigma_seat in VALID_SEAT_STATES, "invalid sigma_seat")
    require(sigma_role in VALID_ROLES, "invalid sigma_role")
    u, v = window
    require_exact_int(u, "window start")
    require_exact_int(v, "window end")
    require(u < v, "ordered half-open window u < v required")
    require(
        isinstance(records, (tuple, list)) and len(records) > 0,
        "wavelet must retain committed construction records",
    )
    rec_tuple = tuple(require_nonempty_str(x, "committed record") for x in records)
    wit_complete = require_exact_bool(witnesses_complete, "witnesses_complete")
    adm_wave = require_exact_bool(is_admitted_wave, "is_admitted_wave")
    build_occurrence_registry(return_witnesses)
    w = {
        "id_w": wid,
        "parent_id": pid,
        "ancestry": anc_tuple,
        "scope_id": scp,
        "cut_coordinate": coord,
        "window": (u, v),
        "sigma_seat": sigma_seat,
        "sigma_role": sigma_role,
        "records": rec_tuple,
        "return_witnesses": tuple(return_witnesses),
        "witnesses_complete": wit_complete,
        "signed_current": require_exact_int(signed_current, "signed_current"),
        "is_admitted_wave": adm_wave,
    }
    eligible = eligible_return_ids(
        w,
        target_lineage=pid,
        target_scope=scp,
        scope_map=scope_map,
        registry=registry,
    )
    if adm_wave and (
        sigma_role == "shed_continuation" or sigma_seat == "open_duon" or len(eligible) < 1
    ):
        raise ValueError(
            "open/shed wavelet or zero-eligible-return fragment cannot be promoted to admitted wave"
        )
    return w


def validate_complete_windows(
    wavelets: tuple[dict, ...],
    known_returns: Sequence[Mapping] | Mapping[str, Mapping],
    *,
    scope_map=None,
) -> dict[str, dict]:
    """Validate canonical registry, verify immutable witness payloads, and check window completeness."""
    canon = build_occurrence_registry(known_returns)
    require(isinstance(wavelets, (tuple, list)) and len(wavelets) > 0, "non-empty wavelets required")
    for w in wavelets:
        actual = eligible_return_ids(
            w,
            target_lineage=w["parent_id"],
            target_scope=w["scope_id"],
            scope_map=scope_map,
            registry=canon,
        )
        u, v = w["window"]
        expected: set[str] = set()
        for rid, r in canon.items():
            if r["lineage_id"] != w["parent_id"] or r["cut_coordinate"] != w["cut_coordinate"]:
                continue
            if r["scope_id"] != w["scope_id"]:
                if scope_map is None:
                    continue
                validate_scope_map(
                    scope_map,
                    r,
                    target_scope=w["scope_id"],
                    target_lineage=w["parent_id"],
                )
            if r["compatible"] and r["occurrence_j"] >= 1 and (u < r["completion_cut"] <= v):
                expected.add(rid)
        require(
            actual == expected,
            f"complete window {w['window']} omitted or mismatched eligible returns: "
            f"actual={sorted(actual)} expected={sorted(expected)}",
        )
    return canon


def deduplicated_return_count(
    wavelets: tuple[dict, ...],
    target_lineage: str,
    target_scope: str = "B:main",
    *,
    scope_map=None,
    registry: Sequence[Mapping] | Mapping[str, Mapping] | None = None,
) -> int:
    require(isinstance(wavelets, (tuple, list)) and len(wavelets) > 0, "non-empty wavelets required")
    combined_records: list[Mapping] = []
    if registry is not None:
        combined_records.extend(
            registry.values() if isinstance(registry, Mapping) else list(registry)
        )
    for w in wavelets:
        combined_records.extend(w["return_witnesses"])
    joint_canon = build_occurrence_registry(combined_records)

    seen: set[str] = set()
    for w in wavelets:
        seen.update(
            eligible_return_ids(
                w,
                target_lineage=target_lineage,
                target_scope=target_scope,
                scope_map=scope_map,
                registry=joint_canon,
            )
        )
    return len(seen)


# --- F03: Recipient chronology, stage-event evidence & admitted closure certificate ---


def make_stage_event(
    event_id: str,
    stage: str,
    scope_id: str,
    cut_coordinate: str,
    cut: int,
) -> dict:
    eid = require_nonempty_str(event_id, "event_id")
    st = require_nonempty_str(stage, "stage")
    require(st in NON_CLOSURE_RECIPIENT_STAGES, f"unsupported stage event kind: {st!r}")
    scp = require_nonempty_str(scope_id, "scope_id")
    coord = require_nonempty_str(cut_coordinate, "cut_coordinate")
    k = require_exact_int(cut, f"{st}.cut")
    return {
        "event_id": eid,
        "stage": st,
        "scope_id": scp,
        "cut_coordinate": coord,
        "cut": k,
    }


def declare_coordinate_relation(
    relation_id: str,
    source_coordinate: str,
    target_coordinate: str,
    parent_id: str,
    emit_cut: int,
    mapped_recipient_cut: int,
) -> dict:
    rid = require_nonempty_str(relation_id, "relation_id")
    src = require_nonempty_str(source_coordinate, "source_coordinate")
    dst = require_nonempty_str(target_coordinate, "target_coordinate")
    pid = require_nonempty_str(parent_id, "parent_id")
    require(src != dst, "coordinate_relation applies to distinct source and target coordinates")
    ek = require_exact_int(emit_cut, "emit_cut")
    mk = require_exact_int(mapped_recipient_cut, "mapped_recipient_cut")
    return {
        "kind": "declared_cut_coordinate_relation",
        "relation_id": rid,
        "source_coordinate": src,
        "target_coordinate": dst,
        "parent_id": pid,
        "emit_cut": ek,
        "mapped_recipient_cut": mk,
    }


def _resolve_effective_emission_cut(shed_witness: Mapping, recipient_context: Mapping) -> int:
    emit_coord = require_nonempty_str(
        shed_witness.get("cut_coordinate"), "shed_witness.cut_coordinate"
    )
    rec_coord = require_nonempty_str(
        recipient_context.get("cut_coordinate"), "recipient_context.cut_coordinate"
    )
    emit_cut = require_exact_int(shed_witness.get("emit_cut"), "shed_witness.emit_cut")
    rel = recipient_context.get("coordinate_relation")
    if emit_coord == rec_coord:
        require(
            rel is None,
            "shared cut_coordinate must not attach a cross-coordinate relation",
        )
        return emit_cut
    require(
        isinstance(rel, Mapping) and rel.get("kind") == "declared_cut_coordinate_relation",
        f"incomparable cut coordinates ({emit_coord!r} != {rec_coord!r}) require an explicit "
        "declared_cut_coordinate_relation",
    )
    require(
        rel.get("source_coordinate") == emit_coord
        and rel.get("target_coordinate") == rec_coord
        and rel.get("parent_id") == shed_witness["parent_id"]
        and rel.get("emit_cut") == emit_cut,
        "coordinate_relation does not match shed emission witness and recipient coordinate",
    )
    return require_exact_int(rel.get("mapped_recipient_cut"), "mapped_recipient_cut")


def _unpack_admitted_closure_record(closure_record) -> tuple[native.Trace, native.Certificate, dict]:
    require(
        closure_record is not None,
        "recipient origin/reclosure stage requires an admitted (Trace, Certificate, registry) record",
    )
    if isinstance(closure_record, Mapping):
        if "has_certificate" in closure_record:
            raise ValueError(
                "bare has_certificate Boolean does not authenticate a closure certificate; "
                "supply an admitted (Trace, Certificate, registry) record"
            )
        raise ValueError("closure_record must be an admitted (Trace, Certificate, registry) tuple")
    require(
        isinstance(closure_record, tuple) and len(closure_record) == 3,
        "closure_record must be an admitted (Trace, Certificate, registry) 3-tuple",
    )
    t_rec, c_rec, reg_rec = closure_record
    require(
        isinstance(t_rec, native.Trace)
        and isinstance(c_rec, native.Certificate)
        and isinstance(reg_rec, Mapping),
        "closure_record elements must be (Trace, Certificate, Mapping)",
    )
    native.admitted(t_rec, c_rec, reg_rec)
    return t_rec, c_rec, dict(reg_rec)


def evaluate_recipient_stage(
    witness: Mapping,
    recipient_context: Mapping,
    stages: tuple[str, ...],
    closure_record=None,
    *,
    stage_events: Mapping[str, Mapping] | None = None,
    recipient_scope_map=None,
) -> dict:
    """Validate passive recipient-stage observations, chronology, and admitted closure certificates."""
    require(isinstance(witness, Mapping), "shed continuation witness mapping required")
    for key in ("parent_id", "emit_boundary", "cut_coordinate", "post_shed_parent_state"):
        require_nonempty_str(witness.get(key), f"witness.{key}")
    require_exact_int(witness.get("emit_cut"), "witness.emit_cut")
    require(witness.get("route") in {"endo", "exo", "redir", "open"}, "invalid shed route tag")
    x_route = require_exact_rational(witness.get("X_route"), "witness.X_route")
    require(x_route > 0, "shed continuation witness requires positive X_route > 0")

    require(isinstance(recipient_context, Mapping), "recipient_context mapping required")
    rec_lineage = require_nonempty_str(
        recipient_context.get("recipient_lineage"), "recipient_lineage"
    )
    rec_scope = require_nonempty_str(recipient_context.get("recipient_scope"), "recipient_scope")
    rec_coord = require_nonempty_str(recipient_context.get("cut_coordinate"), "cut_coordinate")
    u, v = recipient_context["window"]
    require_exact_int(u, "recipient window start")
    require_exact_int(v, "recipient window end")
    require(u < v, "ordered recipient window u < v required")

    require(
        isinstance(stages, (tuple, list)) and bool(stages) and stages[0] == "emitted",
        "recipient stage path must start at 'emitted'",
    )
    for cur, nxt in zip(stages, stages[1:]):
        require(
            nxt in ALLOWED_RECIPIENT_TRANSITIONS.get(cur, frozenset()),
            f"illegal stage transition {cur} -> {nxt}",
        )

    eff_emit_cut = _resolve_effective_emission_cut(witness, recipient_context)

    required_event_stages = [s for s in stages[1:] if s in NON_CLOSURE_RECIPIENT_STAGES]
    require(
        isinstance(stage_events, Mapping),
        "explicit stage_events mapping required; delivery/acceptance/seating cannot be inferred "
        "from routed surplus or a closure certificate alone",
    )
    prev_cut = eff_emit_cut
    prev_stage = "emitted"
    for st in required_event_stages:
        require(
            st in stage_events,
            f"missing explicit stage-event witness for traversed recipient stage {st!r}",
        )
        ev = stage_events[st]
        require(isinstance(ev, Mapping), f"stage_events[{st!r}] must be a mapping")
        require_nonempty_str(ev.get("event_id"), f"stage_events[{st!r}].event_id")
        require(ev.get("stage") == st, f"stage_events[{st!r}] stage tag mismatch")
        require(
            ev.get("scope_id") == rec_scope,
            f"stage_events[{st!r}] scope_id does not match recipient_scope",
        )
        require(
            ev.get("cut_coordinate") == rec_coord,
            f"stage_events[{st!r}] cut_coordinate does not match recipient cut_coordinate",
        )
        ev_cut = require_exact_int(ev.get("cut"), f"stage_events[{st!r}].cut")
        require(
            prev_cut <= ev_cut,
            f"recipient stage {st!r} at cut {ev_cut} precedes {prev_stage!r} at cut {prev_cut} "
            f"on coordinate {rec_coord!r}",
        )
        prev_cut = ev_cut
        prev_stage = st

    terminal = stages[-1]
    if terminal not in {"closed_origin", "reclosed"}:
        require(
            closure_record is None,
            f"non-closure recipient stage {terminal!r} must not attach a closure_record",
        )
        return {
            "stage": terminal,
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
            "blocks_later_seating": False,
            "last_verified_cut": prev_cut,
        }

    t_rec, c_rec, reg_rec = _unpack_admitted_closure_record(closure_record)
    closure_coord = recipient_context.get("closure_cut_coordinate", rec_coord)
    require(
        closure_coord == rec_coord,
        "closure_cut_coordinate differs from recipient cut_coordinate",
    )
    require(t_rec.lineage == rec_lineage, "recipient closure lineage mismatch")

    if t_rec.scope != rec_scope and (
        recipient_scope_map is None or isinstance(recipient_scope_map, bool)
    ):
        validate_scope_map(
            recipient_scope_map,
            {"scope_id": t_rec.scope, "lineage_id": t_rec.lineage, "scale": t_rec.scale, "return_id": t_rec.return_id},
            target_scope=rec_scope,
            target_lineage=rec_lineage,
        )

    raw_prior = recipient_context.get("prior_certified_returns", ())
    require(
        isinstance(raw_prior, (tuple, list)),
        "prior_certified_returns must be a sequence of admitted (Trace, Certificate, registry) tuples",
    )
    prior_records = tuple(_unpack_admitted_closure_record(item) for item in raw_prior)
    for idx, (pt, pc, _) in enumerate(prior_records):
        require(
            (pt.lineage, pt.scope, pt.scale) == (t_rec.lineage, t_rec.scope, t_rec.scale),
            f"prior recipient record {idx} mismatches closure lineage/scope/scale",
        )
    for (lt, _, _), (rt, _, _) in zip(prior_records, prior_records[1:]):
        require(lt.indices[-1] < rt.indices[0], "prior recipient records violate causal order")
        require(lt.ancestor == rt.ancestor, "prior recipient records changed ancestor")

    if t_rec.scope != rec_scope:
        chain_for_scope = (
            ((t_rec, c_rec, reg_rec),)
            if not prior_records or t_rec.return_id in {pt.return_id for pt, _, _ in prior_records}
            else prior_records + ((t_rec, c_rec, reg_rec),)
        )
        wit_rec = project_admitted_lineage_occurrences(
            chain_for_scope, cut_coordinate=rec_coord
        )[-1]
        validate_scope_map(
            recipient_scope_map,
            wit_rec,
            target_scope=rec_scope,
            target_lineage=rec_lineage,
        )
    elif recipient_scope_map is not None:
        raise ValueError("same-scope recipient closure must not attach a cross-scope map")

    completion_cut = t_rec.indices[-1]
    require(
        eff_emit_cut <= prev_cut <= completion_cut,
        f"recipient completion at cut {completion_cut} precedes {prev_stage!r} at cut {prev_cut} "
        f"(effective emission cut {eff_emit_cut}) on coordinate {rec_coord!r}",
    )

    if terminal == "closed_origin":
        require(
            len(prior_records) == 0,
            "closed_origin applies only to initial recipient closure (no prior origin)",
        )
        require(
            native.closure_cycle_count([(t_rec, c_rec, reg_rec)], cut=completion_cut) == 1,
            "initial closure certificate failed closure_cycle_count==1 check",
        )
        return {
            "stage": "closed_origin",
            "closure_phase_delta": int(u < completion_cut <= v),
            "reclosure_bip_delta": 0,
            "origin_return_id": t_rec.return_id,
            "occurrence_j": 0,
        }

    require(
        len(prior_records) >= 1,
        "reclosure requires a pre-existing admitted recipient origin closure (j=0)",
    )
    prior_by_id = {pt.return_id: (pt, pc, preg) for pt, pc, preg in prior_records}
    extra_seen = frozenset(
        require_nonempty_str(x, "seen_return_id")
        for x in recipient_context.get("seen_return_ids", ())
    )
    if t_rec.return_id in prior_by_id:
        pt, pc, _ = prior_by_id[t_rec.return_id]
        require(
            pt == t_rec and pc == c_rec,
            "replayed return_id payload conflicts with prior admitted recipient record",
        )
        return {
            "stage": "reclosed_replay",
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
            "return_id": t_rec.return_id,
        }
    if t_rec.return_id in extra_seen:
        return {
            "stage": "reclosed_replay",
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
            "return_id": t_rec.return_id,
        }

    w_rec = native.wave(prior_records + ((t_rec, c_rec, reg_rec),))
    native.validate_wave(w_rec)
    occ_j = len(w_rec.returns) - 1
    if not (u < completion_cut <= v):
        return {
            "stage": "reclosed_out_of_window",
            "closure_phase_delta": 0,
            "reclosure_bip_delta": 0,
            "return_id": t_rec.return_id,
            "occurrence_j": occ_j,
        }
    return {
        "stage": "reclosed",
        "closure_phase_delta": 1,
        "reclosure_bip_delta": 1,
        "return_id": t_rec.return_id,
        "occurrence_j": occ_j,
    }


def native_cadence_ratio(
    id_a: str, q_a: int, id_r: str, q_r: int, coupled: bool, bound_contacts: int
) -> Fraction:
    require_nonempty_str(id_a, "id_a")
    require_nonempty_str(id_r, "id_r")
    require(id_a != id_r, "aliased wave identities rejected")
    require_exact_bool(coupled, "coupled")
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
    wid = require_nonempty_str(wavelet_id, "wavelet_id")
    pid = require_nonempty_str(parent_id, "parent_id")
    rid = require_nonempty_str(ref_id, "ref_id")
    require(wid != rid and pid != rid, "aliased identities rejected")
    u, v = window
    require_exact_int(u, "window start")
    require_exact_int(v, "window end")
    require_exact_int(bound_contacts, "bound_contacts")
    require(u < v, "ordered window required")
    require(bound_contacts == 1, "single-contact stage association requires bound_contacts == 1")
    return {
        "kind": "single_contact_stage_association",
        "wavelet_id": wid,
        "parent_id": pid,
        "reference_id": rid,
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


def _zeta12_power(exponent: int) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    """Exact power zeta_12^exponent in Q[x]/(x^4 - x^2 + 1) with zero floating-point arithmetic."""
    deg = exponent % 12
    coeffs = [Fraction(0) for _ in range(max(deg, 3) + 1)]
    coeffs[deg] = Fraction(1)
    for power in range(len(coeffs) - 1, 3, -1):
        lead = coeffs[power]
        coeffs[power] = Fraction(0)
        coeffs[power - 2] += lead
        coeffs[power - 4] -= lead
    return (coeffs[0], coeffs[1], coeffs[2], coeffs[3])


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

    # Also verify existing native Duon -> seated Duad helper on an admitted Duon wave
    pivot_t, pivot_c, pivot_reg = native.certified(native.trace("duon_lin", 0, scope="B0", start_index=-5))
    t0 = native.trace("duon_lin", 1, scope="B0", start_index=0)
    t1 = native.trace("duon_lin", 2, scope="B0", start_index=10)
    c0 = native.certify(t0)
    c1 = native.certify(t1)
    reg = {**pivot_reg, c0.certificate_digest: c0, c1.certificate_digest: c1}
    m0 = native.motif_witness("Duon", t0, ((1, -1), (pivot_c.certificate_digest, 1), (-1, 1)), [(pivot_t, pivot_c)], reg)
    m1 = native.motif_witness("Duon", t1, ((1, -1), (pivot_c.certificate_digest, 1), (-1, 1)), [(pivot_t, pivot_c)], reg)
    duon_wave = native.wave([(t0, c0, reg), (t1, c1, reg)], motif_witnesses=(m0, m1))
    seated_state = native.seat_duon(duon_wave, native.initial_state(duon_wave), compatible=True)
    require(
        seated_state.identity == duon_wave.identity and seated_state.closure_status == "seated",
        "native seat_duon failed to preserve identity",
    )

    occ = project_admitted_wave_occurrences(duon_wave)
    w_coupled = make_wavelet(
        "w_coupled", "duon_lin", ("duon_lin:anc", "seg:c"), (5, 15),
        "seated_duad", "coupled_segment", (c0.certificate_digest, c1.certificate_digest),
        occ, scope_id="B0", is_admitted_wave=True, registry=occ,
    )
    w_shed = make_wavelet(
        "w_shed", "duon_lin", ("duon_lin:anc", "shed:1"), (15, 25),
        "seated_duad", "shed_continuation", (c0.certificate_digest, c1.certificate_digest),
        occ, scope_id="B0", is_admitted_wave=False, registry=occ,
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
    w_native = native.recurrent("W_B_1", n=3, spacing=10, scope="B:main", scale=0)
    occ = project_admitted_wave_occurrences(w_native)
    parent = {"id": "W_B_1", "wave_identity": w_native.identity, "active_beyond_v": True}
    w = make_wavelet(
        "w_clip", parent["id"], ("W_B_1:ancestor", "clip:15_19"), (15, 19),
        "seated_duad", "local_segment",
        tuple(c.certificate_digest for c in w_native.certificates[:2]),
        occ[:2], scope_id="B:main", registry=occ,
    )
    require(w["parent_id"] == "W_B_1" and len(w["records"]) == 2, "parent/witnesses lost")
    require(parent["active_beyond_v"] is True, "selected window terminated parent")
    reject(
        lambda: make_wavelet("bad", "", ("anc",), (0, 2), "open_duon", "local_segment", ("r0",)),
        ValueError, "parent_id",
    )
    reject(
        lambda: make_wavelet("bad_rec", "W_B_1", ("anc",), (0, 2), "open_duon", "local_segment", ("",)),
        ValueError, "committed record",
    )
    reject(
        lambda: make_wavelet(
            "bad_promo", "W_B_1", ("anc",), (5, 15), "open_duon", "local_segment",
            (w_native.certificates[1].certificate_digest,), occ[:2],
            scope_id="B:main", is_admitted_wave=True, registry=occ,
        ),
        ValueError, "cannot be promoted",
    )
    # F02 check on localization: unrelated-scope witness with omitted scope_map rejected
    c_unrel = make_return_witness("C1", 1, 2, "W_B_1", "unrelated-scope")
    reject(
        lambda: make_wavelet(
            "bad_scope_default", "W_B_1", ("anc",), (0, 8),
            "seated_duad", "coupled_segment", ("rec:1",), (c_unrel,), scope_id="B:main",
        ),
        ValueError, "explicit validated scope_map",
    )
    return {"parent_retained": True, "parent_active_beyond_v": True, "default_scope_map_absent": True}


def check_p2_03_04() -> dict:
    # 1. Declared finite-model overlap example from Manual prose (C0@0, C1@2, C2@6, C3@8)
    # Occurrence indices j=0..3 are derived from ordered cuts; display labels stay separate from IDs.
    known, canon_reg = declare_synthetic_lineage_registry(
        "W_B_1",
        "B:main",
        (0, 2, 6, 8),
        display_labels=("C0", "C1", "C2", "C3"),
    )
    c0, c1, c2, c3 = known
    require(
        c2["display_label"] == "C2" and c2["return_id"] != "C2",
        "display label must stay separate from canonical synthetic return_id",
    )
    # Idempotent repackaging of exact same valid occurrence
    require(
        len(build_occurrence_registry((c1, deepcopy(c1)))) == 1,
        "repeated packaging of identical valid occurrence must remain idempotent",
    )

    w_out = make_wavelet(
        "w_out", "W_B_1", ("lin:1", "out"), (3, 5),
        "seated_duad", "coupled_segment", ("rec:C0@0", "rec:C1@2"), (c0, c1), registry=canon_reg,
    )
    require(
        len(w_out["return_witnesses"]) == 2
        and eligible_return_ids(w_out, registry=canon_reg) == set(),
        "out-of-window support must be retained and count 0",
    )

    w_origin = make_wavelet(
        "w_orig", "W_B_1", ("lin:1", "orig"), (-1, 1),
        "seated_duad", "local_segment", ("rec:C0@0",), (c0,), registry=canon_reg,
    )
    origins_in_win = {
        r["return_id"] for r in w_origin["return_witnesses"]
        if r["occurrence_j"] == 0 and w_origin["window"][0] < r["completion_cut"] <= w_origin["window"][1]
    }
    require(
        len(origins_in_win) == 1 and eligible_return_ids(w_origin, registry=canon_reg) == set(),
        "origin C0@0 in (-1, 1] must give 1 closure phase and 0 reclosure bips",
    )

    w_half = make_wavelet(
        "w_half", "W_B_1", ("lin:1", "half"), (2, 6),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6"), (c1, c2),
        is_admitted_wave=True, registry=canon_reg,
    )
    half_ids = eligible_return_ids(w_half, registry=canon_reg)
    require(
        half_ids == {c2["return_id"]}
        and [canon_reg[rid]["display_label"] for rid in sorted(half_ids)] == ["C2"],
        "half-open (2, 6] boundary mismatch",
    )

    w1 = make_wavelet(
        "w1", "W_B_1", ("lin:1", "w1"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:C0@0", "rec:C1@2", "rec:C2@6"), (c0, c1, c2),
        signed_current=1, is_admitted_wave=True, registry=canon_reg,
    )
    w2 = make_wavelet(
        "w2", "W_B_1", ("lin:1", "w2"), (4, 8),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6", "rec:C3@8"), (c1, c2, c3),
        signed_current=-1, is_admitted_wave=True, registry=canon_reg,
    )
    validate_complete_windows((w1, w2), canon_reg)
    naive_sum = len(eligible_return_ids(w1, registry=canon_reg)) + len(
        eligible_return_ids(w2, registry=canon_reg)
    )
    union_count = deduplicated_return_count((w1, w2), "W_B_1", registry=canon_reg)
    require(naive_sum == 4 and union_count == 3, "overlap deduplication must give 2+2 vs 3")

    # 2. Passive native-Wave overlap projection via Trace.return_id & closure_cycle_count
    # Trace completions at cuts 0, 3, 6, 9: windows (0, 6] -> {3,6} (2) and (4, 9] -> {6,9} (2), union 3
    native_traces = [
        native.certified(native.trace("W_nat", idx, scope="B:main", start_index=-2 + 3 * idx))
        for idx in range(4)
    ]
    w_nat = native.wave(native_traces)
    nat_occ = project_admitted_wave_occurrences(w_nat)
    require(
        [r["completion_cut"] for r in nat_occ] == [0, 3, 6, 9]
        and [r["occurrence_j"] for r in nat_occ] == [0, 1, 2, 3],
        "native wave occurrence projection mismatch",
    )
    nw1 = make_wavelet(
        "nw1", "W_nat", ("W_nat:ancestor", "nw1"), (0, 6),
        "seated_duad", "coupled_segment",
        tuple(c.certificate_digest for c in w_nat.certificates[:3]),
        nat_occ[:3], is_admitted_wave=True, registry=nat_occ,
    )
    nw2 = make_wavelet(
        "nw2", "W_nat", ("W_nat:ancestor", "nw2"), (4, 9),
        "seated_duad", "coupled_segment",
        tuple(c.certificate_digest for c in w_nat.certificates[1:]),
        nat_occ[1:], is_admitted_wave=True, registry=nat_occ,
    )
    validate_complete_windows((nw1, nw2), nat_occ)
    nat_union = deduplicated_return_count((nw1, nw2), "W_nat", registry=nat_occ)
    nat_expected_bips = (
        native.closure_cycle_count(native_traces, cut=9)
        - native.closure_cycle_count(native_traces, cut=0)
    )
    require(nat_union == nat_expected_bips == 3, "native Trace.return_id overlap union mismatch")

    # 3. F01 hostile regressions:
    # (a) Canonical payload conflict under same ID 'C1' against unchanged canonical registry
    c1_canon = make_return_witness("C1", 1, 2, "W", "B:main")
    c1_mutated = make_return_witness("C1", 2, 6, "W", "B:main")
    w_mut = make_wavelet(
        "w_mut", "W", ("anc",), (0, 8),
        "seated_duad", "coupled_segment", ("rec:1",), (c1_mutated,),
    )
    reject(
        lambda: validate_complete_windows((w_mut,), (c1_canon,)),
        ValueError, "conflicts with canonical occurrence record",
    )
    reject(
        lambda: deduplicated_return_count((w_mut,), "W", registry=(c1_canon,)),
        ValueError, "collision",
    )
    # Swapped payloads preserving ID set {'C1', 'C2'} inside (0, 8] also rejected
    c2_canon = make_return_witness("C2", 2, 6, "W", "B:main")
    w_swap = make_wavelet(
        "w_swap", "W", ("anc",), (0, 8),
        "seated_duad", "coupled_segment", ("rec:swap",),
        (make_return_witness("C2", 1, 2, "W", "B:main"), make_return_witness("C1", 2, 6, "W", "B:main")),
    )
    reject(
        lambda: validate_complete_windows((w_swap,), (c1_canon, c2_canon)),
        ValueError, "conflicts with canonical occurrence record",
    )
    # (b) Return ID collision: two different completions given same ID
    col_a = make_return_witness("collision", 1, 2, "W", "B:main")
    col_b = make_return_witness("collision", 2, 6, "W", "B:main")
    reject(
        lambda: make_wavelet(
            "w_col", "W", ("anc",), (0, 8),
            "seated_duad", "coupled_segment", ("rec:1",), (col_a, col_b),
        ),
        ValueError, "collision",
    )
    # (c) Occurrence aliasing: one canonical occurrence given two different IDs
    al_a = make_return_witness("C1", 1, 2, "W", "B:main")
    al_b = make_return_witness("C1-repackaged", 1, 2, "W", "B:main")
    reject(
        lambda: make_wavelet(
            "w_al", "W", ("anc",), (0, 8),
            "seated_duad", "coupled_segment", ("rec:1",), (al_a, al_b),
        ),
        ValueError, "aliased under multiple return_ids",
    )
    # Also reject aliasing split across two separate wavelets
    w_al1 = make_wavelet("wal1", "W", ("anc",), (0, 8), "seated_duad", "coupled_segment", ("r1",), (al_a,))
    w_al2 = make_wavelet("wal2", "W", ("anc",), (0, 8), "seated_duad", "coupled_segment", ("r2",), (al_b,))
    reject(
        lambda: deduplicated_return_count((w_al1, w_al2), "W"),
        ValueError, "aliased under multiple return_ids",
    )
    # (d) Omitted known eligible return C3@8 in asserted-complete (0, 8]
    w_incomplete = make_wavelet(
        "w_inc", "W_B_1", ("lin:1", "inc"), (0, 8),
        "seated_duad", "coupled_segment", ("rec:C1@2", "rec:C2@6"), (c1, c2),
    )
    reject(lambda: validate_complete_windows((w_incomplete,), canon_reg), ValueError, "omitted")

    # 4. F02 hostile & positive scope-map controls:
    c_other_scope = make_return_witness("C_ext", 1, 4, "W_B_1", "B:other")
    # Omitted scope_map rejected
    reject(
        lambda: make_wavelet(
            "w_noscope", "W_B_1", ("lin:1",), (0, 8),
            "seated_duad", "coupled_segment", ("rec:ext",), (c_other_scope,), scope_id="B:main",
        ),
        ValueError, "explicit validated scope_map",
    )
    # Boolean scope_map=False and scope_map=True rejected
    for flag in (False, True):
        reject(
            lambda flag=flag: make_wavelet(
                "w_boolscope", "W_B_1", ("lin:1",), (0, 8),
                "seated_duad", "coupled_segment", ("rec:ext",), (c_other_scope,),
                scope_id="B:main", scope_map=flag,
            ),
            ValueError, "Boolean flag",
        )
    # Specialized cross-scale fold_proposal rejected as generic scope-isomorphism map
    fold_prop = native.fold_proposal([w_nat], "B:outer", 1)
    nat_other = project_admitted_wave_occurrences(
        native.recurrent("W_nat", n=3, spacing=10, scope="B:other", scale=0)
    )
    reject(
        lambda: make_wavelet(
            "w_fold_misuse", "W_nat", ("W_nat:ancestor",), (0, 25),
            "seated_duad", "coupled_segment", ("rec:fold",), nat_other,
            scope_id="B:main", scope_map=fold_prop,
        ),
        ValueError, "declared_conditional_scope_map",
    )
    # Explicit declared conditional scope map succeeds only for exact bound occurrence payload
    cond_map = declare_conditional_scope_map(
        "map:other_to_main", "B:other", "B:main", "W_B_1", (c_other_scope,)
    )
    w_mapped = make_wavelet(
        "w_mapped", "W_B_1", ("lin:1",), (0, 8),
        "seated_duad", "coupled_segment", ("rec:ext",), (c_other_scope,),
        scope_id="B:main", scope_map=cond_map, is_admitted_wave=True,
    )
    require(
        eligible_return_ids(w_mapped, scope_map=cond_map) == {"C_ext"},
        "explicit declared conditional scope map failed",
    )
    c_other_mutated = make_return_witness("C_ext", 1, 5, "W_B_1", "B:other")
    reject(
        lambda: make_wavelet(
            "w_mapped_mut", "W_B_1", ("lin:1",), (0, 8),
            "seated_duad", "coupled_segment", ("rec:ext",), (c_other_mutated,),
            scope_id="B:main", scope_map=cond_map,
        ),
        ValueError, "conflicts with bound occurrence in scope_map",
    )

    # Cross-lineage union rejected
    w_other_lin = make_wavelet(
        "w_ol", "W_B_2", ("lin:2",), (4, 10), "seated_duad", "coupled_segment",
        ("rec:D1@9",), (make_return_witness("D1", 1, 9, "W_B_2", "B:main"),),
    )
    reject(lambda: deduplicated_return_count((w1, w_other_lin), "W_B_1"), ValueError, "lineage")
    return {
        "out_of_window_count": 0,
        "origin_closure_phases": 1,
        "origin_bips": 0,
        "half_open_2_6": ["C2"],
        "overlap_naive_sum": naive_sum,
        "overlap_deduplicated_union": union_count,
        "native_trace_overlap_union": nat_union,
        "omitted_return_rejected": True,
        "payload_conflict_collision_alias_rejected": True,
        "unmapped_cross_scope_rejected": True,
    }


def check_p2_05_06() -> dict:
    witness = {
        "parent_id": "W_B_1",
        "emit_boundary": "dT_R1",
        "cut_coordinate": "shared_committed_k",
        "emit_cut": 12,
        "route": "exo",
        "X_route": Fraction(1, 2),
        "post_shed_parent_state": "S_W_post_12",
    }
    ctx_fresh = {
        "recipient_lineage": "R_1",
        "recipient_scope": "B_rec:1",
        "cut_coordinate": "shared_committed_k",
        "window": (10, 25),
        "prior_certified_returns": (),
        "seen_return_ids": (),
    }
    ev_unacc = {
        "delivered": make_stage_event("ev:d1", "delivered", "B_rec:1", "shared_committed_k", 12),
        "unaccepted_pass": make_stage_event(
            "ev:u1", "unaccepted_pass", "B_rec:1", "shared_committed_k", 13
        ),
    }
    r_unacc = evaluate_recipient_stage(
        witness, ctx_fresh, ("emitted", "delivered", "unaccepted_pass"), stage_events=ev_unacc
    )
    ev_pend = {
        "delivered": make_stage_event("ev:d2", "delivered", "B_rec:1", "shared_committed_k", 12),
        "accepted": make_stage_event("ev:a2", "accepted", "B_rec:1", "shared_committed_k", 13),
        "pending_unseated": make_stage_event(
            "ev:p2", "pending_unseated", "B_rec:1", "shared_committed_k", 13
        ),
    }
    r_pend = evaluate_recipient_stage(
        witness,
        ctx_fresh,
        ("emitted", "delivered", "accepted", "pending_unseated"),
        stage_events=ev_pend,
    )
    # Later seating after cut-local pending_unseated remains valid
    ev_seat = {
        "delivered": make_stage_event("ev:d2", "delivered", "B_rec:1", "shared_committed_k", 12),
        "accepted": make_stage_event("ev:a2", "accepted", "B_rec:1", "shared_committed_k", 13),
        "seated": make_stage_event("ev:s2", "seated", "B_rec:1", "shared_committed_k", 14),
    }
    r_seat = evaluate_recipient_stage(
        witness, ctx_fresh, ("emitted", "delivered", "accepted", "seated"), stage_events=ev_seat
    )
    require(
        r_unacc["reclosure_bip_delta"] == 0
        and r_pend["reclosure_bip_delta"] == 0
        and r_pend["blocks_later_seating"] is False
        and r_seat["reclosure_bip_delta"] == 0,
        "non-closing recipient stages must add 0 bips and never block later seating",
    )

    # Initial recipient origin closure (j=0) via real admitted (Trace, Certificate, registry)
    rec0 = native.certified(native.trace("R_1", 0, scope="B_rec:1", start_index=13))  # completes at 15
    r_orig = evaluate_recipient_stage(
        witness,
        ctx_fresh,
        ("emitted", "delivered", "accepted", "seated", "closed_origin"),
        rec0,
        stage_events=ev_seat,
    )
    require(
        r_orig["closure_phase_delta"] == 1
        and r_orig["reclosure_bip_delta"] == 0
        and r_orig["occurrence_j"] == 0,
        "initial recipient closure must contribute 1 closure phase and 0 bips",
    )

    # Recipient lineage with prior origin rec_pre0 (completes at 3) and counted rec_pre1 (completes at 15)
    rec_pre0 = native.certified(native.trace("R_1", 0, scope="B_rec:1", start_index=1))   # (1,2,3)
    rec_pre1 = native.certified(native.trace("R_1", 1, scope="B_rec:1", start_index=13))  # (13,14,15)
    ctx_after = {
        "recipient_lineage": "R_1",
        "recipient_scope": "B_rec:1",
        "cut_coordinate": "shared_committed_k",
        "window": (10, 25),
        "prior_certified_returns": (rec_pre0, rec_pre1),
    }
    r_rep = evaluate_recipient_stage(
        witness,
        ctx_after,
        ("emitted", "delivered", "accepted", "seated", "reclosed"),
        rec_pre1,
        stage_events=ev_seat,
    )
    require(r_rep["reclosure_bip_delta"] == 0, "replay must add 0 bips")

    rec_fresh = native.certified(native.trace("R_1", 2, scope="B_rec:1", start_index=16))  # (16,17,18)
    r_fresh = evaluate_recipient_stage(
        witness,
        ctx_after,
        ("emitted", "delivered", "accepted", "seated", "reclosed"),
        rec_fresh,
        stage_events=ev_seat,
    )
    require(
        r_fresh["reclosure_bip_delta"] == 1 and r_fresh["occurrence_j"] == 2,
        "fresh compatible admitted completion must add 1 bip",
    )

    rec_oow = native.certified(native.trace("R_1", 2, scope="B_rec:1", start_index=24))  # completes at 26 > 25
    r_oow = evaluate_recipient_stage(
        witness,
        ctx_after,
        ("emitted", "delivered", "accepted", "seated", "reclosed"),
        rec_oow,
        stage_events=ev_seat,
    )
    require(r_oow["reclosure_bip_delta"] == 0, "out-of-window completion must add 0 bips")

    # F03 hostile regressions:
    # 1. Shared-coordinate completion at cut 18 BEFORE emission at cut 19 (exact review counterexample)
    shed_19 = {
        "parent_id": "P",
        "emit_boundary": "B:shared",
        "cut_coordinate": "shared_committed_k",
        "emit_cut": 19,
        "route": "exo",
        "X_route": Fraction(1, 2),
        "post_shed_parent_state": "Ppost19",
    }
    sh_r0 = native.certified(native.trace("R", 0, scope="B:shared", start_index=1))    # ends 3
    sh_r1 = native.certified(native.trace("R", 1, scope="B:shared", start_index=11))   # ends 13
    sh_r2_18 = native.certified(native.trace("R", 2, scope="B:shared", start_index=16))  # ends 18 < 19
    ctx_shared = {
        "recipient_lineage": "R",
        "recipient_scope": "B:shared",
        "cut_coordinate": "shared_committed_k",
        "window": (10, 20),
        "prior_certified_returns": (sh_r0, sh_r1),
    }
    ev_at_19 = {
        "delivered": make_stage_event("e1", "delivered", "B:shared", "shared_committed_k", 19),
        "accepted": make_stage_event("e2", "accepted", "B:shared", "shared_committed_k", 19),
        "seated": make_stage_event("e3", "seated", "B:shared", "shared_committed_k", 19),
    }
    reject(
        lambda: evaluate_recipient_stage(
            shed_19,
            ctx_shared,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            sh_r2_18,
            stage_events=ev_at_19,
        ),
        ValueError, "precedes",
    )
    ev_before_19 = {
        "delivered": make_stage_event("e1", "delivered", "B:shared", "shared_committed_k", 17),
        "accepted": make_stage_event("e2", "accepted", "B:shared", "shared_committed_k", 17),
        "seated": make_stage_event("e3", "seated", "B:shared", "shared_committed_k", 18),
    }
    reject(
        lambda: evaluate_recipient_stage(
            shed_19,
            ctx_shared,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            sh_r2_18,
            stage_events=ev_before_19,
        ),
        ValueError, "precedes 'emitted'",
    )

    # 2. Bare has_certificate=True dictionary rejected as non-certificate
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            {
                "has_certificate": True,
                "lineage_id": "R_1",
                "scope_id": "B_rec:1",
                "return_id": "ret:R2",
                "occurrence_j": 2,
                "completion_cut": 18,
            },
            stage_events=ev_seat,
        ),
        ValueError, "has_certificate Boolean does not authenticate",
    )

    # 3. Closure certificate alone without explicit stage_events rejected
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            rec_fresh,
            stage_events=None,
        ),
        ValueError, "explicit stage_events mapping required",
    )
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            rec_fresh,
            stage_events={"delivered": ev_seat["delivered"], "seated": ev_seat["seated"]},
        ),
        ValueError, "missing explicit stage-event witness",
    )

    # 4. Incomparable cut coordinates rejected without explicit coordinate_relation
    shed_other_coord = dict(witness, cut_coordinate="source_local_k")
    reject(
        lambda: evaluate_recipient_stage(
            shed_other_coord,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            rec_fresh,
            stage_events=ev_seat,
        ),
        ValueError, "declared_cut_coordinate_relation",
    )
    rel_ok = declare_coordinate_relation(
        "rel:src_to_rec", "source_local_k", "shared_committed_k", "W_B_1", 12, 12
    )
    r_mapped_coord = evaluate_recipient_stage(
        shed_other_coord,
        dict(ctx_after, coordinate_relation=rel_ok),
        ("emitted", "delivered", "accepted", "seated", "reclosed"),
        rec_fresh,
        stage_events=ev_seat,
    )
    require(r_mapped_coord["reclosure_bip_delta"] == 1, "mapped coordinate relation failed")

    # 5. Wrong lineage, unmapped cross-scope closure, and skipped stage transitions rejected
    rec_wrong_lin = native.certified(native.trace("R_WRONG", 2, scope="B_rec:1", start_index=16))
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            rec_wrong_lin,
            stage_events=ev_seat,
        ),
        ValueError, "lineage mismatch",
    )
    rec_wrong_scope = native.certified(native.trace("R_1", 2, scope="B_WRONG", start_index=16))
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "accepted", "seated", "reclosed"),
            rec_wrong_scope,
            stage_events=ev_seat,
        ),
        ValueError, "explicit validated scope_map",
    )
    reject(
        lambda: evaluate_recipient_stage(
            witness,
            ctx_after,
            ("emitted", "delivered", "reclosed"),
            rec_fresh,
            stage_events=ev_seat,
        ),
        ValueError, "illegal stage transition",
    )

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
        transport["emitted"] - transport["arrived"]
        == transport["pending_end"] - transport["pending_start"]
        == 0,
        "passive transport conservation failed",
    )
    return {
        "closed_origin_bips": r_orig["reclosure_bip_delta"],
        "replay_bips": r_rep["reclosure_bip_delta"],
        "fresh_reclosure_bips": r_fresh["reclosure_bip_delta"],
        "out_of_window_bips": r_oow["reclosure_bip_delta"],
        "pre_emission_completion_rejected": True,
        "boolean_certificate_rejected": True,
        "passive_transport_net": transport["net"],
    }


def check_p2_07() -> dict:
    c1 = make_return_witness("C1", 1, 2, "W_B_1", "B:main")
    c2 = make_return_witness("C2", 2, 6, "W_B_1", "B:main")
    reg = build_occurrence_registry((c1, c2))
    w_pos = make_wavelet(
        "w_pos", "W_B_1", ("lin:1", "pos"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:pos",), (c1, c2),
        signed_current=1, is_admitted_wave=True, registry=reg,
    )
    w_neg = make_wavelet(
        "w_neg", "W_B_1", ("lin:1", "neg"), (0, 6),
        "seated_duad", "coupled_segment", ("rec:neg",), (c1, c2),
        signed_current=-1, is_admitted_wave=True, registry=reg,
    )
    net = w_pos["signed_current"] + w_neg["signed_current"]
    histories = ((w_pos["ancestry"], w_pos["records"]), (w_neg["ancestry"], w_neg["records"]))
    require(net == 0 and len(histories) == 2 and histories[0] != histories[1], "cancellation erased history")

    # Also verify native inner/outer fold disjointness via aod_native_closure_wave.fold & expose
    inner_w = native.recurrent("inner_a", n=2, spacing=6, scope="B0", scale=0)
    out_t = native.outer_trace([inner_w], lineage="outer_M", occurrence=0, scope="B1", scale=1)
    out_c = native.certify(out_t, motif="outer", inner=[inner_w])
    folded = native.fold([inner_w], (out_t, out_c, {out_c.certificate_digest: out_c}))
    exposed_inner = native.expose(folded)
    require(
        exposed_inner == (inner_w,)
        and out_t.return_id not in {t.return_id for t in inner_w.returns},
        "native outer closure must preserve inner wave and keep distinct return_id",
    )

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
    dropped = deepcopy(compared)
    dropped.update(phase_start="0", phase_end="0")
    require(metrology.phase_advance(dropped) == Fraction(4) != Fraction(7, 2), "dropped endpoint check")
    mis_c, mis_r, mis_real = metrology.phase_fixture()
    mis_c["window"] = [11, 23]
    mis_c, mis_r, mis_real = _rebind_phase_comparison(mis_c, mis_r, mis_real)
    reject(lambda: metrology.compare_accumulations(mis_c, mis_r, mis_real), ValueError, "matched")
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
            val != diag_1210 and abs(val - Fraction(23, 50)) < Fraction(1, 10**12),
            "ring summary 1:2:10 missing_fraction expected distinct near 23/50",
        )
    require(Fraction(9, 20) != Fraction(23, 50), "9/20 vs 23/50 is a genuine rational change")
    require(
        len(shed_rows) == 90 and all(row["state"] == "open" for row in shed_rows),
        "wavelet_shedding_simulation.csv must have 90 open rows",
    )

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

    cb = json.loads((ROOT / "contracts" / "scientific" / "CANONICAL_BINDINGS.json").read_text())
    frozen = cb["frozen_sha256"]
    for rel, expected_sha in frozen.items():
        actual_sha = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        require(actual_sha == expected_sha, f"frozen file changed: {rel}")

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
    # Exact 12-point DFT in cyclotomic quotient Q[x]/(x^4 - x^2 + 1) on pulse support {0, 4, 8}
    n_order = 12
    l_min = 4
    pulses = (0, 4, 8)
    m_mode = 3
    require(Fraction(m_mode) > Fraction(n_order, 2 * l_min), "m=3 must exceed N/(2*l_min)")
    coeffs_by_mode: dict[int, tuple[Fraction, Fraction, Fraction, Fraction]] = {}
    for mode in range(n_order):
        val = tuple(
            sum(_zeta12_power(-mode * n)[j] for n in pulses) / n_order for j in range(4)
        )
        expected = (
            (Fraction(1, 4), Fraction(0), Fraction(0), Fraction(0))
            if mode % 3 == 0
            else (Fraction(0), Fraction(0), Fraction(0), Fraction(0))
        )
        require(val == expected, f"cyclotomic DFT mismatch at mode {mode}")
        coeffs_by_mode[mode] = val

    v_hat_3 = coeffs_by_mode[m_mode][0]
    require(v_hat_3 == Fraction(1, 4) and v_hat_3 != 0, "exact overtone v_hat(3) != 1/4")
    time_energy = Fraction(len(pulses), n_order)
    freq_energy = sum(val[0] * val[0] for val in coeffs_by_mode.values())
    require(time_energy == freq_energy == Fraction(1, 4), "Parseval identity mismatch on Z_12")
    return {
        "group_order": n_order,
        "pulse_support": list(pulses),
        "l_min": l_min,
        "nonzero_modes": [m for m, val in coeffs_by_mode.items() if val[0] != 0],
        "overtone_mode": m_mode,
        "v_hat_3": str(v_hat_3),
        "parseval_exact": str(freq_energy),
        "certifies_native_reclosure_or_si_frequency": False,
    }


def run_all_checks() -> dict:
    return {
        "schema": "aod.manual.wavelet-si-alignment.v2",
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
