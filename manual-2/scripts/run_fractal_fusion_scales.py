#!/usr/bin/env python3
"""Generate deterministic Fractal Fusion Scales fixture data.

This script is intentionally offline-safe. PubChem and RDKit are used as
comparison/graph lanes only. PubChem rows are lookup fixtures. RDKit descriptor
rows are generated when RDKit is importable; otherwise the committed data can be
kept as an offline fixture with a clear status marker.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "manual-2" / "data"
SNAPSHOT = "offline_fixture_2026-06-14"
NORMALIZER_VERSION = "v40.02r05"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


ELEMENTS: list[tuple[int, str, str]] = [
    (1, "H", "Hydrogen"), (2, "He", "Helium"), (3, "Li", "Lithium"),
    (4, "Be", "Beryllium"), (5, "B", "Boron"), (6, "C", "Carbon"),
    (7, "N", "Nitrogen"), (8, "O", "Oxygen"), (9, "F", "Fluorine"),
    (10, "Ne", "Neon"), (11, "Na", "Sodium"), (12, "Mg", "Magnesium"),
    (13, "Al", "Aluminium"), (14, "Si", "Silicon"), (15, "P", "Phosphorus"),
    (16, "S", "Sulfur"), (17, "Cl", "Chlorine"), (18, "Ar", "Argon"),
    (19, "K", "Potassium"), (20, "Ca", "Calcium"), (21, "Sc", "Scandium"),
    (22, "Ti", "Titanium"), (23, "V", "Vanadium"), (24, "Cr", "Chromium"),
    (25, "Mn", "Manganese"), (26, "Fe", "Iron"), (27, "Co", "Cobalt"),
    (28, "Ni", "Nickel"), (29, "Cu", "Copper"), (30, "Zn", "Zinc"),
    (31, "Ga", "Gallium"), (32, "Ge", "Germanium"), (33, "As", "Arsenic"),
    (34, "Se", "Selenium"), (35, "Br", "Bromine"), (36, "Kr", "Krypton"),
    (37, "Rb", "Rubidium"), (38, "Sr", "Strontium"), (39, "Y", "Yttrium"),
    (40, "Zr", "Zirconium"), (41, "Nb", "Niobium"), (42, "Mo", "Molybdenum"),
    (43, "Tc", "Technetium"), (44, "Ru", "Ruthenium"), (45, "Rh", "Rhodium"),
    (46, "Pd", "Palladium"), (47, "Ag", "Silver"), (48, "Cd", "Cadmium"),
    (49, "In", "Indium"), (50, "Sn", "Tin"), (51, "Sb", "Antimony"),
    (52, "Te", "Tellurium"), (53, "I", "Iodine"), (54, "Xe", "Xenon"),
    (55, "Cs", "Caesium"), (56, "Ba", "Barium"), (57, "La", "Lanthanum"),
    (58, "Ce", "Cerium"), (59, "Pr", "Praseodymium"), (60, "Nd", "Neodymium"),
    (61, "Pm", "Promethium"), (62, "Sm", "Samarium"), (63, "Eu", "Europium"),
    (64, "Gd", "Gadolinium"), (65, "Tb", "Terbium"), (66, "Dy", "Dysprosium"),
    (67, "Ho", "Holmium"), (68, "Er", "Erbium"), (69, "Tm", "Thulium"),
    (70, "Yb", "Ytterbium"), (71, "Lu", "Lutetium"), (72, "Hf", "Hafnium"),
    (73, "Ta", "Tantalum"), (74, "W", "Tungsten"), (75, "Re", "Rhenium"),
    (76, "Os", "Osmium"), (77, "Ir", "Iridium"), (78, "Pt", "Platinum"),
    (79, "Au", "Gold"), (80, "Hg", "Mercury"), (81, "Tl", "Thallium"),
    (82, "Pb", "Lead"), (83, "Bi", "Bismuth"), (84, "Po", "Polonium"),
    (85, "At", "Astatine"), (86, "Rn", "Radon"), (87, "Fr", "Francium"),
    (88, "Ra", "Radium"), (89, "Ac", "Actinium"), (90, "Th", "Thorium"),
    (91, "Pa", "Protactinium"), (92, "U", "Uranium"), (93, "Np", "Neptunium"),
    (94, "Pu", "Plutonium"), (95, "Am", "Americium"), (96, "Cm", "Curium"),
    (97, "Bk", "Berkelium"), (98, "Cf", "Californium"), (99, "Es", "Einsteinium"),
    (100, "Fm", "Fermium"), (101, "Md", "Mendelevium"), (102, "No", "Nobelium"),
    (103, "Lr", "Lawrencium"), (104, "Rf", "Rutherfordium"), (105, "Db", "Dubnium"),
    (106, "Sg", "Seaborgium"), (107, "Bh", "Bohrium"), (108, "Hs", "Hassium"),
    (109, "Mt", "Meitnerium"), (110, "Ds", "Darmstadtium"), (111, "Rg", "Roentgenium"),
    (112, "Cn", "Copernicium"), (113, "Nh", "Nihonium"), (114, "Fl", "Flerovium"),
    (115, "Mc", "Moscovium"), (116, "Lv", "Livermorium"), (117, "Ts", "Tennessine"),
    (118, "Og", "Oganesson"),
]

ATOM_ORDER = ["C", "H", "N", "O", "P", "S"]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_formula(formula: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    i = 0
    while i < len(formula):
        if not formula[i].isalpha() or not formula[i].isupper():
            raise ValueError(f"bad formula at {formula[i:]} in {formula!r}")
        symbol = formula[i]
        i += 1
        if i < len(formula) and formula[i].islower():
            symbol += formula[i]
            i += 1
        digits = []
        while i < len(formula) and formula[i].isdigit():
            digits.append(formula[i])
            i += 1
        counts[symbol] += int("".join(digits)) if digits else 1
    return counts


def formula_text(counts: Counter[str]) -> str:
    parts: list[str] = []
    for atom in ATOM_ORDER:
        n = counts.get(atom, 0)
        if n:
            parts.append(atom if n == 1 else f"{atom}{n}")
    for atom in sorted(k for k in counts if k not in ATOM_ORDER and counts[k]):
        n = counts[atom]
        parts.append(atom if n == 1 else f"{atom}{n}")
    return "".join(parts) or "0"


def residual_text(counts: Counter[str]) -> str:
    return ";".join(f"{atom}:{counts.get(atom, 0)}" for atom in ATOM_ORDER)


def combine(reactants: Iterable[str], shed: Iterable[str] = ()) -> Counter[str]:
    total: Counter[str] = Counter()
    for formula in reactants:
        total.update(parse_formula(formula))
    for formula in shed:
        total.subtract(parse_formula(formula))
    return total


def diff_counts(a: Counter[str], b: Counter[str]) -> Counter[str]:
    out: Counter[str] = Counter()
    for atom in set(a) | set(b) | set(ATOM_ORDER):
        d = a.get(atom, 0) - b.get(atom, 0)
        if d:
            out[atom] = d
    return out


def scale_label(z: int) -> str:
    if z <= 2:
        return "light-nuclei boundary marker"
    if z <= 5:
        return "bridge-gap comparison marker"
    if z <= 8:
        return "alpha-chain comparison marker"
    if z <= 28:
        return "stellar-burning comparison marker"
    return "heavy-element comparison marker"


def generate_elementary() -> None:
    registry_rows = [
        {
            "Z": z,
            "symbol": sym,
            "name": name,
            "octave": "elementary",
            "registry_authority": "IUPAC periodic-table registry lane",
            "registry_status": "frozen_118_name_symbol_fixture",
        }
        for z, sym, name in ELEMENTS
    ]
    write_csv(DATA / "elementary" / "element_registry_118.csv", registry_rows)

    for rule_id, left, right, retained in [("FFL-336", 3, 3, 6), ("FFL-346", 3, 4, 6)]:
        rows = []
        for z, sym, name in ELEMENTS:
            depth = math.ceil(z / retained)
            capacity = depth * retained
            residual = capacity - z
            surplus = depth * (left + right - retained)
            rows.append({
                "rule_id": rule_id,
                "element_Z": z,
                "symbol": sym,
                "element_name": name,
                "declared_ratio": f"{left}:{right}:{retained}",
                "boundary_unit_left": left,
                "boundary_unit_right": right,
                "retained_unit": retained,
                "ladder_depth": depth,
                "retained_capacity_Z": capacity,
                "residual_Z": residual,
                "sheddic_surplus": surplus,
                "admissibility_status": "closed" if residual == 0 else "boundary_residual",
                "observable_map_status": "registry_Z_coordinate_after_freeze",
            })
        write_csv(DATA / "elementary" / f"fusion_ladder_{left}{right}{retained}.csv", rows)

    stellar_rows = []
    for z, sym, name in ELEMENTS:
        depth = math.ceil(z / 6)
        capacity = depth * 6
        err = capacity - z
        stellar_rows.append({
            "element_Z": z,
            "symbol": sym,
            "element_name": name,
            "octave_case": "elementary",
            "stellar_scale_label": scale_label(z),
            "declared_scale_coordinate": "Z registry coordinate",
            "external_dataset": "IUPAC element name/symbol/atomic-number registry lane",
            "external_value": z,
            "scaled_aod_value": capacity,
            "absolute_error": err,
            "relative_error": f"{err / z:.12g}",
            "residual_class": "zero" if err == 0 else "capacity_minus_Z",
            "map_status": "comparison_lane_not_core_calculus",
            "src": "manual-2/scripts/run_fractal_fusion_scales.py",
        })
    write_csv(DATA / "elementary" / "stellar_scaled_comparison.csv", stellar_rows)

    pubchem_rows = [
        {
            "Z": z,
            "symbol": sym,
            "name": name,
            "pubchem_query_key": name,
            "pubchem_query_url": f"https://pubchem.ncbi.nlm.nih.gov/#query={name}",
            "comparison_status": "lookup_fixture_no_network_fetch",
            "acquisition_policy": "downstream_external_comparison_lane_only",
            "src": "PubChem lookup lane declared; not used as AOD premise",
        }
        for z, sym, name in ELEMENTS
    ]
    write_csv(DATA / "elementary" / "pubchem_element_map.csv", pubchem_rows)


@dataclass(frozen=True)
class Component:
    component_id: str
    klass: str
    formula: str
    smiles: str

COMPONENTS = [
    Component("water", "boundary_shedding", "H2O", "O"),
    Component("carbon_dioxide", "precursor", "CO2", "O=C=O"),
    Component("ammonia", "precursor", "H3N", "N"),
    Component("methane", "precursor", "CH4", "C"),
    Component("formaldehyde", "precursor", "CH2O", "C=O"),
    Component("hydrogen_cyanide", "precursor", "CHN", "C#N"),
    Component("phosphate", "precursor", "H3O4P", "OP(=O)(O)O"),
    Component("ribose", "sugar", "C5H10O5", "OCC1OC(O)C(O)C1O"),
    Component("deoxyribose", "sugar", "C5H10O4", "OCC1OC(O)CC1O"),
    Component("adenine", "base", "C5H5N5", "Nc1ncnc2[nH]cnc12"),
    Component("guanine", "base", "C5H5N5O", "Nc1nc2[nH]cnc2c(=O)[nH]1"),
    Component("cytosine", "base", "C4H5N3O", "Nc1ncc(=O)[nH]1"),
    Component("uracil", "base", "C4H4N2O2", "O=c1cc[nH]c(=O)[nH]1"),
    Component("thymine", "base", "C5H6N2O2", "Cc1c[nH]c(=O)[nH]c1=O"),
    Component("glycine", "amino_acid", "C2H5NO2", "NCC(=O)O"),
    Component("alanine", "amino_acid", "C3H7NO2", "CC(N)C(=O)O"),
    Component("serine", "amino_acid", "C3H7NO3", "NC(CO)C(=O)O"),
    Component("methionine", "amino_acid", "C5H11NO2S", "CSCCC(N)C(=O)O"),
]

COMPONENT_BY_ID = {c.component_id: c for c in COMPONENTS}


def generate_molecular() -> None:
    comp_rows = []
    for c in COMPONENTS:
        parsed = formula_text(parse_formula(c.formula))
        residual = diff_counts(parse_formula(parsed), parse_formula(c.formula))
        comp_rows.append({
            "component_id": c.component_id,
            "class": c.klass,
            "declared_formula": c.formula,
            "normalized_formula": parsed,
            "smiles": c.smiles,
            "formula_status": "exact" if not residual else "residual",
            "residual_CHONPS": residual_text(residual),
        })
    write_csv(DATA / "molecular" / "component_registry_seed.csv", comp_rows)

    fusions = [
        ("carbonic_acid_fixture", ["H2O", "CO2"], [], "H2CO3"),
        ("ribose_formose_fixture", ["CH2O"] * 5, [], "C5H10O5"),
        ("adenine_hcn_pentamer_fixture", ["CHN"] * 5, [], "C5H5N5"),
        ("amp_closure_fixture", ["C5H5N5", "C5H10O5", "H3O4P"], ["H2O", "H2O"], "C10H14N5O7P"),
    ]
    fusion_rows = []
    residual_rows = []
    for fid, reactants, shed, expected in fusions:
        out = combine(reactants, shed)
        residual = diff_counts(out, parse_formula(expected))
        fusion_rows.append({
            "fusion_id": fid,
            "reactants": "+".join(reactants),
            "shedding_vector": "+".join(shed) if shed else "none",
            "formula": formula_text(out),
            "expected_formula": expected,
            "residual_CHONPS": residual_text(residual),
            "status": "closed" if not residual else "residual",
        })
        residual_rows.append({
            "row_id": fid,
            "formula": formula_text(out),
            "target_formula": expected,
            "residual_CHONPS": residual_text(residual),
            "sum_abs_residual_CHONPS": sum(abs(v) for v in residual.values()),
        })
    write_csv(DATA / "molecular" / "molecular_fusion_candidates.csv", fusion_rows)
    write_csv(DATA / "molecular" / "formula_residuals.csv", residual_rows)

    pubchem_rows = [
        {
            "component_id": c.component_id,
            "formula": c.formula,
            "pubchem_query_key": c.component_id.replace("_", " "),
            "pubchem_query_url": f"https://pubchem.ncbi.nlm.nih.gov/#query={c.component_id.replace('_', '%20')}",
            "comparison_status": "lookup_fixture_no_network_fetch",
            "src": "PubChem lookup lane declared; not used as AOD premise",
        }
        for c in COMPONENTS
    ]
    write_csv(DATA / "molecular" / "pubchem_molecule_map.csv", pubchem_rows)


def vector_columns(formula: str) -> dict[str, int]:
    counts = parse_formula(formula)
    return {f"n_{atom}": counts.get(atom, 0) for atom in ATOM_ORDER}


def zero_delta_columns() -> dict[str, int]:
    return {f"delta_{atom}": 0 for atom in ATOM_ORDER}


def target_packet_id(prefix: str, key: str) -> str:
    return f"{prefix}_{key}".replace(" ", "_").replace("/", "_").lower()


def generate_molecular_target_scaffold() -> None:
    """Generate v40.02r02 molecular target-packet and link-rule scaffolds.

    Rows are locator/fixture packets only. They do not release chain scoring or
    active molecular/graph/chain value maps.
    """
    component_pubchem_rows = []
    vector_rows = []
    delta_rows = []
    pubchem_packets = []
    rdkit_rows = []
    for c in COMPONENTS:
        vec = vector_columns(c.formula)
        norm = formula_text(parse_formula(c.formula))
        raw_payload = f"{c.component_id}|{c.formula}|{c.smiles}|{SNAPSHOT}"
        digest = sha256_text(raw_payload)
        component_pubchem_rows.append({
            "component_id": c.component_id,
            "class": c.klass,
            "declared_formula": c.formula,
            **vec,
            "pubchem_target_id": target_packet_id("pubchem", c.component_id),
            "smiles": c.smiles,
            "rdkit_formula": norm,
            "rdkit_graph_status": "offline_fixture_not_graph_scored",
            "formula_delta3": "C:0;H:0;N:0;O:0;P:0;S:0",
            "target_status": "target_packet_fixture_no_network_fetch",
            "release_status": "v40.02r02_scaffold_no_value_map",
        })
        vector_rows.append({
            "component_id": c.component_id,
            "declared_formula": c.formula,
            "vector_order": "C,H,N,O,P,S",
            **vec,
            "vector_status": "parsed_from_declared_formula",
        })
        delta_rows.append({
            "component_id": c.component_id,
            "declared_formula": c.formula,
            "target_formula": norm,
            **zero_delta_columns(),
            "sum_abs_delta_CHNOPS": 0,
            "delta3_formula": "C:0;H:0;N:0;O:0;P:0;S:0",
            "formula_delta3_status": "exact_fixture",
        })
        pubchem_packets.append({
            "target_packet_id": target_packet_id("pubchem", c.component_id),
            "lane": "molecular_compound",
            "source": "PubChem",
            "source_accession": f"query:{c.component_id.replace('_', ' ')}",
            "source_release_or_snapshot": SNAPSHOT,
            "source_record_url_or_path": f"https://pubchem.ncbi.nlm.nih.gov/#query={c.component_id.replace('_', '%20')}",
            "acquisition_utc": "2026-06-14T00:00:00Z",
            "raw_sha256": digest,
            "normalized_sha256": digest,
            "normalizer_script": "manual-2/scripts/acquire_pubchem_molecular_data.py",
            "normalizer_version": NORMALIZER_VERSION,
            "license_or_terms_ref": "PubChem public data terms; offline locator fixture only",
            "target_status": "locator_fixture_no_network_fetch",
            "leakage_role": "target_only",
            "release_status": "scaffold_only_no_chain_score",
            "name": c.component_id.replace("_", " "),
            "formula": c.formula,
            "canonical_smiles": c.smiles,
            "inchi_key": "deferred_no_network_fetch",
            "charge": 0,
            "exact_mass": "deferred_no_network_fetch",
            "rdkit_parse_status": "not_evaluated_in_target_packet",
            "rdkit_canonical_status": "fixture_smiles_only",
        })
        rdkit_rows.append({
            "molecule_id": c.component_id,
            "canonical_smiles": c.smiles,
            "formula": c.formula,
            "heavy_atom_count": sum(n for atom, n in parse_formula(c.formula).items() if atom != "H"),
            "total_atom_count": sum(parse_formula(c.formula).values()),
            "bond_count": "deferred_offline_scaffold",
            "ring_count": "deferred_offline_scaffold",
            "aromatic_ring_count": "deferred_offline_scaffold",
            "heteroatom_count": sum(n for atom, n in parse_formula(c.formula).items() if atom not in {"C", "H"}),
            "formal_charge": 0,
            "rdkit_version": "deferred_optional_dependency",
            "rdkit_status": "offline_fixture_not_value_map",
            "leakage_role": "comparison_only",
        })

    write_csv(DATA / "molecular" / "component_registry_pubchem.csv", component_pubchem_rows)
    write_csv(DATA / "molecular" / "component_vector_registry.csv", vector_rows)
    write_csv(DATA / "molecular" / "component_composition_delta3.csv", delta_rows)
    write_csv(DATA / "molecular" / "pubchem_compound_target_packets.csv", pubchem_packets)
    write_csv(DATA / "molecular" / "rdkit_graph_descriptors.csv", rdkit_rows)

    water_vec = vector_columns("H2O")
    methane_vec = vector_columns("CH4")
    route_rows = [{
        "route_unit_id": "water_equivalent_route_unit",
        "route_formula": "H2O",
        **water_vec,
        "route_role": "dehydration_condensation_accounting_unit",
        "route_status": "declared_route_unit_carried_forward",
        "release_status": "v40.02r04_target_normalization_carried_forward",
    }]
    control_rows = [{
        "control_unit_id": "methane_carbon_saturation_control",
        "control_formula": "CH4",
        **methane_vec,
        "control_role": "carbon_saturation_control",
        "route_status": "not_a_default_chain_route",
        "release_status": "v40.02r04_target_normalization_carried_forward",
    }]
    link_rows = [
        {
            "link_rule_id": "LINK-peptide-water-001",
            "left_component_class": "amino_acid",
            "right_component_class": "amino_acid",
            "route_unit": "water_equivalent_route_unit",
            "route_vector": "H2O",
            "declared_link_type": "peptide_condensation_formula_scaffold",
            "admissibility_status": "schema_declared_active_for_fixture_rows",
            "detector_status": "detector_active_in_v40.02r03",
            "release_status": "v40.02r03_chain_dec_schema_active",
        },
        {
            "link_rule_id": "LINK-nucleotide-water-001",
            "left_component_class": "nucleotide_candidate",
            "right_component_class": "nucleotide_candidate",
            "route_unit": "water_equivalent_route_unit",
            "route_vector": "H2O",
            "declared_link_type": "phosphodiester_formula_scaffold",
            "admissibility_status": "schema_declared_active_for_fixture_rows",
            "detector_status": "detector_active_in_v40.02r03",
            "release_status": "v40.02r03_chain_dec_schema_active",
        },
        {
            "link_rule_id": "CTRL-methane-carbon-saturation",
            "left_component_class": "control",
            "right_component_class": "control",
            "route_unit": "methane_carbon_saturation_control",
            "route_vector": "CH4",
            "declared_link_type": "control_not_chain_route",
            "admissibility_status": "not_admissible_as_default_chain_route",
            "detector_status": "control_only",
            "release_status": "v40.02r05_control_schema_carried_forward",
        },
    ]
    write_csv(DATA / "molecular" / "route_unit_registry.csv", route_rows)
    write_csv(DATA / "molecular" / "control_unit_registry.csv", control_rows)
    write_csv(DATA / "molecular" / "link_rule_registry.csv", link_rows)
    write_csv(DATA / "molecular" / "water_route_unit.csv", route_rows)
    write_csv(DATA / "molecular" / "methane_control_unit.csv", control_rows)

    manifest = {
        "lane": "molecular_data_scale",
        "version_scope": "v40.02r05",
        "vector_order": ATOM_ORDER,
        "status": "target_packet_scaffold_plus_chain_dec_fixture_carried_forward_no_external_score",
        "no_active_value_maps": [
            "lambda_molecule",
            "lambda_formula",
            "lambda_graph",
            "lambda_chain",
            "lambda_fold",
            "lambda_bio",
        ],
        "files": {
            "component_registry_pubchem": "manual-2/data/molecular/component_registry_pubchem.csv",
            "component_vector_registry": "manual-2/data/molecular/component_vector_registry.csv",
            "component_composition_delta3": "manual-2/data/molecular/component_composition_delta3.csv",
            "pubchem_compound_target_packets": "manual-2/data/molecular/pubchem_compound_target_packets.csv",
            "rdkit_graph_descriptors": "manual-2/data/molecular/rdkit_graph_descriptors.csv",
            "route_unit_registry": "manual-2/data/molecular/route_unit_registry.csv",
            "control_unit_registry": "manual-2/data/molecular/control_unit_registry.csv",
            "link_rule_registry": "manual-2/data/molecular/link_rule_registry.csv",
            "chain_word_spec": "manual-2/data/molecular/chain_word_spec.csv",
            "raw_dec_trace_molecular_chain": "manual-2/data/molecular/raw_dec_trace_molecular_chain.csv",
            "read_only_trace_molecular_chain": "manual-2/data/molecular/read_only_trace_molecular_chain.csv",
            "detected_chain_motifs": "manual-2/data/molecular/detected_chain_motifs.csv",
            "sadar_detector_context": "manual-2/data/molecular/sadar_detector_context.csv",
            "chain_formula_predictions": "manual-2/data/molecular/chain_formula_predictions.csv",
            "chain_fission_audit": "manual-2/data/molecular/chain_fission_audit.csv",
            "molecular_chain_delta3_audit": "manual-2/data/molecular/molecular_chain_delta3_audit.csv",
        },
        "claim_discipline": "molecular chain-D.E.C. rows are internal fixture rows carried forward; target rows are downstream comparison lanes, not raw AFC/D.E.C. premises",
    }
    (DATA / "molecular" / "molecular_target_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def generate_protein_target_scaffold() -> None:
    """Generate protein sequence/folding target locator scaffolds carried into v40.02r05."""
    protein_dir = DATA / "protein"
    protein_dir.mkdir(parents=True, exist_ok=True)
    sequence_targets = [
        {
            "protein_id": "manual_seed_GAS",
            "source": "manual_fixture",
            "source_accession": "pep_GAS",
            "isoform_id": "not_applicable",
            "organism": "manual_fixture",
            "sequence": "GAS",
            "sequence_length": 3,
            "sequence_sha256": sha256_text("GAS"),
            "reviewed_status": "not_uniprot_record",
            "sequence_status": "manual_seed_sequence_for_future_contact_lane",
            "target_status": "scaffold_only_not_fold_target",
            "leakage_role": "allowed_input",
            "release_status": "v40.02r04_target_normalization_carried_forward",
        },
        {
            "protein_id": "manual_seed_MAG",
            "source": "manual_fixture",
            "source_accession": "pep_MAG",
            "isoform_id": "not_applicable",
            "organism": "manual_fixture",
            "sequence": "MAG",
            "sequence_length": 3,
            "sequence_sha256": sha256_text("MAG"),
            "reviewed_status": "not_uniprot_record",
            "sequence_status": "manual_seed_sequence_for_future_contact_lane",
            "target_status": "scaffold_only_not_fold_target",
            "leakage_role": "allowed_input",
            "release_status": "v40.02r04_target_normalization_carried_forward",
        },
        {
            "protein_id": "uniprot_P69905_locator",
            "source": "UniProt",
            "source_accession": "P69905",
            "isoform_id": "canonical",
            "organism": "Homo sapiens locator row",
            "sequence": "deferred_no_network_fetch",
            "sequence_length": "deferred_no_network_fetch",
            "sequence_sha256": sha256_text("P69905|deferred|" + SNAPSHOT),
            "reviewed_status": "external_record_status_deferred",
            "sequence_status": "target_locator_only_no_sequence_committed",
            "target_status": "target_packet_fixture_no_network_fetch",
            "leakage_role": "target_only",
            "release_status": "v40.02r04_target_normalization_carried_forward",
        },
    ]
    write_csv(protein_dir / "protein_sequence_targets.csv", sequence_targets)

    def packet(packet_id: str, lane: str, source: str, accession: str, url: str, script: str, status: str, leakage_role: str = "target_only") -> dict[str, object]:
        raw = f"{packet_id}|{source}|{accession}|{SNAPSHOT}"
        return {
            "target_packet_id": packet_id,
            "lane": lane,
            "source": source,
            "source_accession": accession,
            "source_release_or_snapshot": SNAPSHOT,
            "source_record_url_or_path": url,
            "acquisition_utc": "2026-06-14T00:00:00Z",
            "raw_sha256": sha256_text(raw),
            "normalized_sha256": sha256_text(raw + "|normalized"),
            "normalizer_script": script,
            "normalizer_version": NORMALIZER_VERSION,
            "license_or_terms_ref": "external database terms; locator fixture only",
            "target_status": status,
            "leakage_role": leakage_role,
            "release_status": "scaffold_only_no_prediction_or_score",
        }

    uniprot_packets = [
        packet("uniprot_P69905_locator", "protein_sequence", "UniProt", "P69905", "https://www.uniprot.org/uniprotkb/P69905/entry", "manual-2/scripts/acquire_uniprot_sequences.py", "locator_fixture_no_network_fetch"),
        packet("uniprot_P68871_locator", "protein_sequence", "UniProt", "P68871", "https://www.uniprot.org/uniprotkb/P68871/entry", "manual-2/scripts/acquire_uniprot_sequences.py", "locator_fixture_no_network_fetch"),
    ]
    write_csv(protein_dir / "uniprot_target_packets.csv", uniprot_packets)

    pdb_rows = []
    for pdb_id, chain in [("1CRN", "A"), ("1UBQ", "A")]:
        row = packet(f"pdb_{pdb_id.lower()}_{chain}_locator", "experimental_structure", "RCSB_PDB", pdb_id, f"https://files.rcsb.org/download/{pdb_id}.cif", "manual-2/scripts/acquire_pdb_structures.py", "structure_locator_no_coordinates_committed")
        row.update({
            "structure_source": "PDB/mmCIF",
            "structure_file": f"{pdb_id}.cif",
            "chain_id": chain,
            "entity_id": "deferred_no_network_fetch",
            "experimental_method": "deferred_no_network_fetch",
            "resolution_angstrom": "deferred_no_network_fetch",
            "model_version": "not_applicable",
            "resolved_residue_count": "deferred_no_network_fetch",
            "missing_residue_count": "deferred_no_network_fetch",
            "coordinate_status": "not_committed_target_locator_only",
            "confidence_source": "experimental_metadata_deferred",
            "target_limitation_class": "target_locator_only_no_coordinates",
        })
        pdb_rows.append(row)
    write_csv(protein_dir / "pdb_structure_target_packets.csv", pdb_rows)

    af_rows = []
    for accession in ["P69905", "P68871"]:
        row = packet(f"alphafold_AF-{accession}-F1_locator", "predicted_structure", "AlphaFold_DB", f"AF-{accession}-F1", f"https://alphafold.ebi.ac.uk/entry/{accession}", "manual-2/scripts/acquire_alphafold_structures.py", "predicted_structure_locator_no_coordinates_committed")
        row.update({
            "structure_source": "AlphaFold_DB",
            "structure_file": f"AF-{accession}-F1-model_v4.cif",
            "chain_id": "A",
            "entity_id": "canonical_uniprot_chain",
            "experimental_method": "predicted_model_not_experimental",
            "resolution_angstrom": "not_applicable",
            "model_version": "deferred_no_network_fetch",
            "resolved_residue_count": "deferred_no_network_fetch",
            "missing_residue_count": "deferred_no_network_fetch",
            "coordinate_status": "not_committed_target_locator_only",
            "confidence_source": "pLDDT_deferred",
            "target_limitation_class": "predicted_structure_target_not_ground_truth",
        })
        af_rows.append(row)
    write_csv(protein_dir / "alphafold_structure_target_packets.csv", af_rows)

    leakage_rows = [
        {
            "guard_id": "LEAK-RAW-DEC-001",
            "forbidden_source_class": "PubChem/RDKit/UniProt/PDB/AlphaFold target fields",
            "forbidden_destination": "raw_dec_trace_*",
            "allowed_role": "target_only_after_freeze",
            "guard_status": "active",
        },
        {
            "guard_id": "LEAK-PRED-FREEZE-001",
            "forbidden_source_class": "PDB_or_AlphaFold_coordinates_contact_maps_distance_matrices",
            "forbidden_destination": "aod_prediction_freeze_inputs",
            "allowed_role": "comparison_only_after_prediction_freeze",
            "guard_status": "active",
        },
    ]
    write_csv(protein_dir / "protein_target_leakage_guard.csv", leakage_rows)
    lambda_rows = [
        {"lambda_id": name, "status": "deferred_not_attached", "active_value_map": "false", "release_status": "v40.02r04_target_normalization_carried_forward_no_active_map"}
        for name in ["lambda_molecule", "lambda_formula", "lambda_graph", "lambda_chain", "lambda_fold", "lambda_bio"]
    ]
    write_csv(protein_dir / "protein_value_map_quarantine.csv", lambda_rows)
    manifest = {
        "lane": "protein_target_scale",
        "version_scope": "v40.02r05",
        "status": "target_packet_scaffold_plus_folding_target_normalization_gate_no_prediction_score",
        "files": {
            "protein_sequence_targets": "manual-2/data/protein/protein_sequence_targets.csv",
            "uniprot_target_packets": "manual-2/data/protein/uniprot_target_packets.csv",
            "pdb_structure_target_packets": "manual-2/data/protein/pdb_structure_target_packets.csv",
            "alphafold_structure_target_packets": "manual-2/data/protein/alphafold_structure_target_packets.csv",
            "protein_target_leakage_guard": "manual-2/data/protein/protein_target_leakage_guard.csv",
            "protein_value_map_quarantine": "manual-2/data/protein/protein_value_map_quarantine.csv",
            "protein_sequence_target_packets": "manual-2/data/protein/protein_sequence_target_packets.csv",
            "pdb_mmcif_structure_targets": "manual-2/data/protein/pdb_mmcif_structure_targets.csv",
            "alphafold_structure_targets": "manual-2/data/protein/alphafold_structure_targets.csv",
            "protein_contact_map_targets": "manual-2/data/protein/protein_contact_map_targets.csv",
            "protein_distance_matrix_targets": "manual-2/data/protein/protein_distance_matrix_targets.csv",
            "protein_structure_target_limitations": "manual-2/data/protein/protein_structure_target_limitations.csv",
            "protein_folding_target_manifest": "manual-2/data/protein/protein_folding_target_manifest.json",
        },
        "downstream_milestones": {
            "v40.02r05": "freeze AOD contact/reclosure predictions without target leakage",
            "v40.02r06": "score frozen predictions against target contact maps",
        },
        "claim_discipline": "protein folding is a downstream target lane; v40.02r05 normalizes target rows only and does not activate a folding prediction or biological-function claim",
    }
    (protein_dir / "protein_target_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def nucleotide_formula(base: str, sugar: str) -> Counter[str]:
    return combine([
        COMPONENT_BY_ID[base].formula,
        COMPONENT_BY_ID[sugar].formula,
        COMPONENT_BY_ID["phosphate"].formula,
    ], ["H2O", "H2O"])


def peptide_formula(residues: list[str]) -> Counter[str]:
    reactants = [COMPONENT_BY_ID[r].formula for r in residues]
    shed = ["H2O"] * (len(residues) - 1)
    return combine(reactants, shed)


def generate_bio_chain() -> None:
    nucleotide_specs = [
        ("RNA_A", "RNA", "A", "adenine", "ribose", "C10H14N5O7P"),
        ("RNA_G", "RNA", "G", "guanine", "ribose", "C10H14N5O8P"),
        ("RNA_C", "RNA", "C", "cytosine", "ribose", "C9H14N3O8P"),
        ("RNA_U", "RNA", "U", "uracil", "ribose", "C9H13N2O9P"),
        ("DNA_A", "DNA", "A", "adenine", "deoxyribose", "C10H14N5O6P"),
        ("DNA_T", "DNA", "T", "thymine", "deoxyribose", "C10H15N2O8P"),
        ("DNA_G", "DNA", "G", "guanine", "deoxyribose", "C10H14N5O7P"),
        ("DNA_C", "DNA", "C", "cytosine", "deoxyribose", "C9H14N3O7P"),
    ]
    nt_rows = []
    nt_formula: dict[str, Counter[str]] = {}
    for nid, alphabet, symbol, base, sugar, expected in nucleotide_specs:
        out = nucleotide_formula(base, sugar)
        residual = diff_counts(out, parse_formula(expected))
        nt_formula[nid] = out
        nt_rows.append({
            "candidate_id": nid,
            "alphabet": alphabet,
            "symbol": symbol,
            "declared_components": f"{base}+{sugar}+phosphate",
            "shedding_vector": "H2O+H2O",
            "formula": formula_text(out),
            "expected_formula": expected,
            "residual_CHONPS": residual_text(residual),
            "status": "closed" if not residual else "residual",
        })
    write_csv(DATA / "bio_chain" / "nucleotide_candidates.csv", nt_rows)

    dinuc_specs = [
        ("RNA_AU", "RNA", "AU", ["RNA_A", "RNA_U"]),
        ("RNA_GC", "RNA", "GC", ["RNA_G", "RNA_C"]),
        ("DNA_AT", "DNA", "AT", ["DNA_A", "DNA_T"]),
        ("DNA_GC", "DNA", "GC", ["DNA_G", "DNA_C"]),
    ]
    dinuc_rows = []
    closure_rows = []
    for cid, alphabet, seq, ids in dinuc_specs:
        out = Counter()
        for nid in ids:
            out.update(nt_formula[nid])
        out.subtract(parse_formula("H2O"))
        dinuc_rows.append({
            "chain_id": cid,
            "alphabet": alphabet,
            "sequence": seq,
            "declared_components": "+".join(ids),
            "shedding_vector": "H2O",
            "formula": formula_text(out),
            "residual_CHONPS": residual_text(Counter()),
            "status": "closed",
        })
        closure_rows.append({
            "chain_id": cid,
            "alphabet": alphabet,
            "sequence": seq,
            "declared_components": "+".join(ids),
            "shedding_count": 1,
            "formula": formula_text(out),
            "residual_CHONPS": residual_text(Counter()),
            "observable_map_status": "sequence_closure_after_formula_freeze",
        })
    write_csv(DATA / "bio_chain" / "dinucleotide_candidates.csv", dinuc_rows)
    write_csv(DATA / "bio_chain" / "rna_dna_chain_closures.csv", closure_rows)

    peptide_specs = [
        ("pep_GA", "GA", ["glycine", "alanine"]),
        ("pep_GG", "GG", ["glycine", "glycine"]),
        ("pep_GAS", "GAS", ["glycine", "alanine", "serine"]),
        ("pep_MAG", "MAG", ["methionine", "alanine", "glycine"]),
    ]
    pep_rows = []
    protein_rows = []
    route_rows = []
    for pid, sequence, residues in peptide_specs:
        out = peptide_formula(residues)
        shed_count = len(residues) - 1
        row = {
            "chain_id": pid,
            "sequence": sequence,
            "residue_count": len(residues),
            "declared_components": "+".join(residues),
            "water_shedding_count": shed_count,
            "formula": formula_text(out),
            "residual_CHONPS": residual_text(Counter()),
            "status": "closed",
        }
        pep_rows.append(row)
        if len(residues) >= 3:
            protein_rows.append({**row, "protein_chain_status": "seed_chain_candidate_not_folded_structure"})
        route_rows.append({
            "route_id": pid,
            "chain_id": pid,
            "route_formula": f"sum(residues)-{shed_count}H2O",
            "sheddic_route_status": "declared_condensation_route",
        })
    write_csv(DATA / "bio_chain" / "peptide_candidates.csv", pep_rows)
    write_csv(DATA / "bio_chain" / "protein_chain_candidates.csv", protein_rows)
    write_csv(DATA / "bio_chain" / "chain_sheddic_routes.csv", route_rows)


def generate_rdkit() -> None:
    rows = []
    try:
        from rdkit import Chem, RDLogger
        from rdkit.Chem import rdMolDescriptors
        import rdkit
        RDLogger.DisableLog("rdApp.*")
        available = True
        version = rdkit.__version__
    except Exception:
        Chem = None
        rdMolDescriptors = None
        available = False
        version = "unavailable"

    for c in COMPONENTS:
        if available:
            mol = Chem.MolFromSmiles(c.smiles)  # type: ignore[union-attr]
            if mol is None:
                row = {
                    "molecule_id": c.component_id,
                    "canonical_smiles": "",
                    "heavy_atom_count": "",
                    "total_atom_count": "",
                    "bond_count": "",
                    "ring_count": "",
                    "aromatic_ring_count": "",
                    "heteroatom_count": "",
                    "formal_charge": "",
                    "rdkit_version": version,
                    "rdkit_status": "parse_failed",
                }
            else:
                mol_h = Chem.AddHs(mol)  # type: ignore[union-attr]
                ring_info = mol.GetRingInfo()
                aromatic_rings = sum(
                    1 for ring in ring_info.AtomRings()
                    if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring)
                )
                row = {
                    "molecule_id": c.component_id,
                    "canonical_smiles": Chem.MolToSmiles(mol, canonical=True),  # type: ignore[union-attr]
                    "heavy_atom_count": mol.GetNumHeavyAtoms(),
                    "total_atom_count": mol_h.GetNumAtoms(),
                    "bond_count": mol.GetNumBonds(),
                    "ring_count": rdMolDescriptors.CalcNumRings(mol),  # type: ignore[union-attr]
                    "aromatic_ring_count": aromatic_rings,
                    "heteroatom_count": sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() not in (1, 6)),
                    "formal_charge": sum(atom.GetFormalCharge() for atom in mol.GetAtoms()),
                    "rdkit_version": version,
                    "rdkit_status": "computed_optional_graph_lane",
                }
        else:
            row = {
                "molecule_id": c.component_id,
                "canonical_smiles": c.smiles,
                "heavy_atom_count": "",
                "total_atom_count": "",
                "bond_count": "",
                "ring_count": "",
                "aromatic_ring_count": "",
                "heteroatom_count": "",
                "formal_charge": "",
                "rdkit_version": version,
                "rdkit_status": "rdkit_unavailable_offline_fixture",
            }
        rows.append(row)
    write_csv(DATA / "bio_chain" / "rdkit_graph_descriptors.csv", rows)


def generate_manifest() -> None:
    manifest = {
        "manual": "manual-2",
        "title": "Fractal Fusion Scales",
        "subtitle": "Up the Octaves",
        "version_scope": "v40.02r05",
        "protocol": [
            "setup declared boundary/window/octave",
            "run raw AFC/D.E.C. substrate",
            "trace-detect retained events",
            "freeze exact ladder rows or target packets",
            "map to observables only after freeze",
            "report residuals and error ledger",
        ],
        "lanes": {
            "elementary": {
                "status": "frozen_from_v40.02r01",
                "registry": "manual-2/data/elementary/element_registry_118.csv",
                "ladders": [
                    "manual-2/data/elementary/fusion_ladder_336.csv",
                    "manual-2/data/elementary/fusion_ladder_346.csv",
                ],
                "comparison": [
                    "manual-2/data/elementary/stellar_scaled_comparison.csv",
                    "manual-2/data/elementary/pubchem_element_map.csv",
                ],
            },
            "molecular": {
                "fixtures": "manual-2/data/molecular/component_registry_seed.csv",
                "fusions": "manual-2/data/molecular/molecular_fusion_candidates.csv",
                "residuals": "manual-2/data/molecular/formula_residuals.csv",
                "pubchem_legacy_lookup": "manual-2/data/molecular/pubchem_molecule_map.csv",
                "target_manifest": "manual-2/data/molecular/molecular_target_manifest.json",
                "target_packets": "manual-2/data/molecular/pubchem_compound_target_packets.csv",
                "route_units": "manual-2/data/molecular/route_unit_registry.csv",
                "link_rules": "manual-2/data/molecular/link_rule_registry.csv",
                "chain_word_spec": "manual-2/data/molecular/chain_word_spec.csv",
                "raw_dec_trace": "manual-2/data/molecular/raw_dec_trace_molecular_chain.csv",
                "read_only_trace": "manual-2/data/molecular/read_only_trace_molecular_chain.csv",
                "detected_motifs": "manual-2/data/molecular/detected_chain_motifs.csv",
                "sadar_context": "manual-2/data/molecular/sadar_detector_context.csv",
                "chain_formula_predictions": "manual-2/data/molecular/chain_formula_predictions.csv",
                "fission_audit": "manual-2/data/molecular/chain_fission_audit.csv",
                "chain_delta3_audit": "manual-2/data/molecular/molecular_chain_delta3_audit.csv",
            },
            "bio_chain": {
                "nucleotides": "manual-2/data/bio_chain/nucleotide_candidates.csv",
                "dinucleotides": "manual-2/data/bio_chain/dinucleotide_candidates.csv",
                "rna_dna": "manual-2/data/bio_chain/rna_dna_chain_closures.csv",
                "peptides": "manual-2/data/bio_chain/peptide_candidates.csv",
                "protein_chain": "manual-2/data/bio_chain/protein_chain_candidates.csv",
                "rdkit": "manual-2/data/bio_chain/rdkit_graph_descriptors.csv",
            },
            "protein": {
                "target_manifest": "manual-2/data/protein/protein_target_manifest.json",
                "sequence_targets": "manual-2/data/protein/protein_sequence_targets.csv",
                "uniprot_target_packets": "manual-2/data/protein/uniprot_target_packets.csv",
                "pdb_structure_target_packets": "manual-2/data/protein/pdb_structure_target_packets.csv",
                "alphafold_structure_target_packets": "manual-2/data/protein/alphafold_structure_target_packets.csv",
                "leakage_guard": "manual-2/data/protein/protein_target_leakage_guard.csv",
                "value_map_quarantine": "manual-2/data/protein/protein_value_map_quarantine.csv",
                "sequence_target_packets": "manual-2/data/protein/protein_sequence_target_packets.csv",
                "pdb_mmcif_structure_targets": "manual-2/data/protein/pdb_mmcif_structure_targets.csv",
                "alphafold_structure_targets": "manual-2/data/protein/alphafold_structure_targets.csv",
                "contact_map_targets": "manual-2/data/protein/protein_contact_map_targets.csv",
                "distance_matrix_targets": "manual-2/data/protein/protein_distance_matrix_targets.csv",
                "target_limitations": "manual-2/data/protein/protein_structure_target_limitations.csv",
                "folding_target_manifest": "manual-2/data/protein/protein_folding_target_manifest.json",
            },
        },
        "deferred_lambda_register": {
            "lambda_molecule": "deferred_not_attached",
            "lambda_formula": "deferred_not_attached",
            "lambda_graph": "deferred_not_attached",
            "lambda_chain": "deferred_not_attached",
            "lambda_fold": "deferred_not_attached",
            "lambda_bio": "deferred_not_attached",
        },
        "claim_discipline": "external datasets are target/comparison lanes; target-normalization rows are not premises of the raw AFC/AOD calculus or future prediction-freeze inputs",
    }
    path = DATA / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    generate_elementary()
    generate_molecular()
    generate_molecular_target_scaffold()
    generate_bio_chain()
    generate_rdkit()
    generate_protein_target_scaffold()
    generate_manifest()
    subprocess.run([sys.executable, str(ROOT / "manual-2" / "scripts" / "run_molecular_chain_fusion_dec.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "manual-2" / "scripts" / "normalize_protein_folding_targets.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "manual-2" / "scripts" / "freeze_aod_contact_reclosure_predictions.py")], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
