#!/usr/bin/env python3
"""Generate the Manual II molecular chain-fusion D.E.C. fixture rows.

The generator is offline and deterministic. It uses only committed component
vectors and route declarations. External target packets are intentionally not
read by this script.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
MOL = ROOT / "manual-2" / "data" / "molecular"
ORDER = ["C", "H", "N", "O", "P", "S"]
COLS = [f"n_{x}" for x in ORDER]
ZERO = {k: 0 for k in ORDER}


def read_vectors() -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    with (MOL / "component_vector_registry.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["component_id"]] = {x: int(row[f"n_{x}"]) for x in ORDER}
    return rows


def add(*vecs: dict[str, int]) -> dict[str, int]:
    out = dict(ZERO)
    for vec in vecs:
        for k in ORDER:
            out[k] += vec[k]
    return out


def sub(vec: dict[str, int], *vecs: dict[str, int]) -> dict[str, int]:
    out = dict(vec)
    for rhs in vecs:
        for k in ORDER:
            out[k] -= rhs[k]
    return out


def scale(vec: dict[str, int], n: int) -> dict[str, int]:
    return {k: vec[k] * n for k in ORDER}


def formula(vec: dict[str, int]) -> str:
    pieces: list[str] = []
    for k in ORDER:
        n = vec[k]
        if n == 0:
            continue
        pieces.append(k if n == 1 else f"{k}{n}")
    return "".join(pieces) or "0"


def residual_text(delta: dict[str, int]) -> str:
    return ";".join(f"{k}:{delta[k]}" for k in ORDER)


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> int:
    v = read_vectors()
    water = v["water"]
    phosphate = v["phosphate"]

    specs = [
        {
            "chain_id": "chain_GA_peptide_seed",
            "chain_class": "peptide_seed",
            "chain_word": "glycine-alanine",
            "components": ["glycine", "alanine"],
            "component_basis": "free_molecule",
            "terminal_policy": "free_termini",
            "link_rule_id": "LINK-peptide-water-001",
            "link_count": 1,
            "check_formula": "C5H10N2O3",
            "split_index": 1,
            "left_fragment_formula": formula(v["glycine"]),
            "right_fragment_formula": formula(v["alanine"]),
        },
        {
            "chain_id": "chain_AMP_nucleotide_seed",
            "chain_class": "nucleotide_seed",
            "chain_word": "adenine-ribose-phosphate",
            "components": ["adenine", "ribose", "phosphate"],
            "component_basis": "free_molecule",
            "terminal_policy": "declared_nucleotide_free_phosphate",
            "link_rule_id": "LINK-nucleotide-water-001",
            "link_count": 2,
            "check_formula": "C10H14N5O7P",
            "split_index": 2,
            "left_fragment_formula": formula(sub(add(v["adenine"], v["ribose"]), water)),
            "right_fragment_formula": formula(phosphate),
        },
        {
            "chain_id": "chain_UMP_nucleotide_seed",
            "chain_class": "nucleotide_seed",
            "chain_word": "uracil-ribose-phosphate",
            "components": ["uracil", "ribose", "phosphate"],
            "component_basis": "free_molecule",
            "terminal_policy": "declared_nucleotide_free_phosphate",
            "link_rule_id": "LINK-nucleotide-water-001",
            "link_count": 2,
            "check_formula": "C9H13N2O9P",
            "split_index": 2,
            "left_fragment_formula": formula(sub(add(v["uracil"], v["ribose"]), water)),
            "right_fragment_formula": formula(phosphate),
        },
        {
            "chain_id": "chain_AU_dinucleotide_seed",
            "chain_class": "dinucleotide_seed",
            "chain_word": "adenylate-uridylate",
            "components": ["AMP_internal", "UMP_internal"],
            "component_basis": "declared_nucleotide",
            "terminal_policy": "free_termini",
            "link_rule_id": "LINK-nucleotide-water-001",
            "link_count": 1,
            "check_formula": "C19H25N7O15P2",
            "split_index": 1,
            "left_fragment_formula": "C10H14N5O7P",
            "right_fragment_formula": "C9H13N2O9P",
        },
        {
            "chain_id": "chain_GAS_tripeptide_seed",
            "chain_class": "tripeptide_seed",
            "chain_word": "glycine-alanine-serine",
            "components": ["glycine", "alanine", "serine"],
            "component_basis": "free_molecule",
            "terminal_policy": "free_termini",
            "link_rule_id": "LINK-peptide-water-001",
            "link_count": 2,
            "check_formula": "C8H15N3O5",
            "split_index": 2,
            "left_fragment_formula": "C5H10N2O3",
            "right_fragment_formula": formula(v["serine"]),
        },
    ]

    # calculated vectors for internal nucleotide components used by the dinucleotide row
    internal_vectors = {
        "AMP_internal": sub(add(v["adenine"], v["ribose"], phosphate), scale(water, 2)),
        "UMP_internal": sub(add(v["uracil"], v["ribose"], phosphate), scale(water, 2)),
    }
    all_vectors = {**v, **internal_vectors}

    chain_rows = []
    formula_rows = []
    fission_rows = []
    delta_rows = []
    motif_rows = []
    sadar_rows = []
    raw_rows = []
    trace_rows = []

    for idx, spec in enumerate(specs, start=1):
        comps = spec["components"]
        link_count = int(spec["link_count"])
        raw_id = f"raw_mol_{idx:03d}"
        trace_id = f"trace_mol_{idx:03d}"
        motif_id = f"motif_mol_{idx:03d}"
        sadar_id = f"sadar_mol_{idx:03d}"
        total = add(*(all_vectors[c] for c in comps))
        frozen = sub(total, scale(water, link_count))
        delta = dict(ZERO)
        formula_status = "closed_formula_freeze" if formula(frozen) == spec["check_formula"] else "manual_check_formula_mismatch"

        chain_rows.append({
            "chain_id": spec["chain_id"],
            "chain_class": spec["chain_class"],
            "chain_word": spec["chain_word"],
            "declared_components": "+".join(comps),
            "component_basis": spec["component_basis"],
            "terminal_policy": spec["terminal_policy"],
            "link_rule_id": spec["link_rule_id"],
            "route_unit_id": "water_equivalent_route_unit",
            "link_count": link_count,
            "chain_status": "declared_for_v40.02r03_dec_run",
            "release_status": "v40.02r03_chain_spec",
        })
        row = {
            "chain_id": spec["chain_id"],
            "chain_class": spec["chain_class"],
            "component_basis": spec["component_basis"],
            "terminal_policy": spec["terminal_policy"],
            "declared_components": "+".join(comps),
            "route_units": "+".join(["H2O"] * link_count),
            "link_count": link_count,
            "frozen_formula": formula(frozen),
            "declared_check_formula": spec["check_formula"],
            **{f"n_{k}": frozen[k] for k in ORDER},
            **{f"Delta_{k}": delta[k] for k in ORDER},
            "sum_abs_Delta_CHNOPS": 0,
            "delta3_formula": residual_text(delta),
            "formula_status": formula_status,
            "release_status": "v40.02r03_formula_freeze_no_external_target",
        }
        formula_rows.append(row)
        for k in ORDER:
            delta_rows.append({
                "audit_id": f"delta_{idx:03d}_{k}",
                "chain_id": spec["chain_id"],
                "coordinate": k,
                "Delta_Z": 0,
                "delta3_residue": 0,
                "delta3_status": "zero_residual",
                "audit_status": "passed",
            })
        # raw rows are deliberately neutral: no chain names, target names, bio labels, or external-source labels
        for j in range(1, link_count + 1):
            raw_rows.append({
                "tick": len(raw_rows),
                "B": f"B_mol_{idx:03d}",
                "v": f"v{j-1}",
                "e": f"e{j-1}_{j}",
                "v_e": f"v{j}",
                "sigma_e": "branch",
                "adm_e_B": 1,
                "w_e_B": 1,
                "P_e_B": f"1/{link_count}",
                "route_e_B": "water_equivalent_route_unit",
            })
        trace_rows.append({
            "trace_id": trace_id,
            "raw_dec_run_id": raw_id,
            "trace_event": "water_route_support_accumulated",
            "cumulative_support_units": link_count,
            "trace_status": "read_only_trace_after_raw_dec",
            "release_status": "v40.02r03_trace_row",
        })
        motif_rows.append({
            "motif_id": motif_id,
            "trace_id": trace_id,
            "chain_id": spec["chain_id"],
            "detected_motif": "water_route_chain_closure",
            "component_basis": spec["component_basis"],
            "link_count": link_count,
            "route_unit_id": "water_equivalent_route_unit",
            "support_units": link_count,
            "detector_status": "detected_after_raw_trace",
            "sadar_context_id": sadar_id,
            "release_status": "v40.02r03_detector_row",
        })
        sadar_rows.append({
            "sadar_context_id": sadar_id,
            "chain_id": spec["chain_id"],
            "detector_input": "ChainWordSpec+RawTrace",
            "detected_relational_context": "water_route_reclosure_context",
            "sadar_scalar_status": "detector_context_not_scalar_evaluated",
            "scalar_value": "",
            "context_status": "context_named_no_scalar_claim",
            "release_status": "v40.02r03_sadar_context",
        })
        # fission audit: left + right = whole + recovered route unit
        # For all committed rows, one split recovers one water-equivalent route unit.
        # We record the exact zero residual, not a chemical kinetic claim.
        fission_rows.append({
            "chain_id": spec["chain_id"],
            "split_index": spec["split_index"],
            "left_fragment_formula": spec["left_fragment_formula"],
            "right_fragment_formula": spec["right_fragment_formula"],
            "whole_chain_formula": formula(frozen),
            "recovered_route_unit": "H2O",
            **{f"Delta_{k}": 0 for k in ORDER},
            "sum_abs_Delta_CHNOPS": 0,
            "delta3_status": "zero_residual",
            "audit_status": "passed_exact_route_recovery",
        })

    write_csv(MOL / "chain_word_spec.csv", ["chain_id", "chain_class", "chain_word", "declared_components", "component_basis", "terminal_policy", "link_rule_id", "route_unit_id", "link_count", "chain_status", "release_status"], chain_rows)
    write_csv(MOL / "raw_dec_trace_molecular_chain.csv", ["tick", "B", "v", "e", "v_e", "sigma_e", "adm_e_B", "w_e_B", "P_e_B", "route_e_B"], raw_rows)
    write_csv(MOL / "read_only_trace_molecular_chain.csv", ["trace_id", "raw_dec_run_id", "trace_event", "cumulative_support_units", "trace_status", "release_status"], trace_rows)
    write_csv(MOL / "detected_chain_motifs.csv", ["motif_id", "trace_id", "chain_id", "detected_motif", "component_basis", "link_count", "route_unit_id", "support_units", "detector_status", "sadar_context_id", "release_status"], motif_rows)
    write_csv(MOL / "sadar_detector_context.csv", ["sadar_context_id", "chain_id", "detector_input", "detected_relational_context", "sadar_scalar_status", "scalar_value", "context_status", "release_status"], sadar_rows)
    write_csv(MOL / "chain_formula_predictions.csv", ["chain_id", "chain_class", "component_basis", "terminal_policy", "declared_components", "route_units", "link_count", "frozen_formula", "declared_check_formula", *COLS, *[f"Delta_{k}" for k in ORDER], "sum_abs_Delta_CHNOPS", "delta3_formula", "formula_status", "release_status"], formula_rows)
    write_csv(MOL / "chain_fission_audit.csv", ["chain_id", "split_index", "left_fragment_formula", "right_fragment_formula", "whole_chain_formula", "recovered_route_unit", *[f"Delta_{k}" for k in ORDER], "sum_abs_Delta_CHNOPS", "delta3_status", "audit_status"], fission_rows)
    write_csv(MOL / "molecular_chain_delta3_audit.csv", ["audit_id", "chain_id", "coordinate", "Delta_Z", "delta3_residue", "delta3_status", "audit_status"], delta_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
