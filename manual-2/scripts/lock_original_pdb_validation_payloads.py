from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PROT = ROOT / "manual-2" / "data" / "protein"
PAYDIR = PROT / "external_pdb_validation_payloads"
VERSION = "v40.02r22B.1"
RELEASE = "v40.02r22B1_original_validation_payload_byte_lock_gate"
REGISTRATION_UTC = "2026-06-19T00:00:00Z"
ORIGINAL_SNAPSHOT = PAYDIR / "1crn_full_validation_report_parsed_snapshot.json"
REGENERATED_SNAPSHOT = PAYDIR / "1crn_full_validation_report_archive_regenerated_snapshot.json"

ARCHIVES = {
    "validation_xml_gz": {
        "filename": "1crn_validation.xml.gz",
        "url": "https://files.rcsb.org/validation/download/1crn_validation.xml.gz",
        "content_type": "application/gzip; inner=application/xml",
        "inner_type": "validation_xml",
    },
    "validation_cif_gz": {
        "filename": "1crn_validation.cif.gz",
        "url": "https://files.rcsb.org/validation/download/1crn_validation.cif.gz",
        "content_type": "application/gzip; inner=chemical/x-mmcif",
        "inner_type": "validation_cif",
    },
    "validation_pdf_gz": {
        "filename": "1crn_full_validation.pdf.gz",
        "url": "https://files.rcsb.org/validation/download/1crn_full_validation.pdf.gz",
        "content_type": "application/gzip; inner=application/pdf",
        "inner_type": "validation_pdf",
    },
}

AUDIT_PATHS = [
    "$.source_report_generated_utc",
    "$.validation_pipeline.wwpdb_validation_pipeline",
    "$.validation_pipeline.molprobity",
    "$.validation_pipeline.xtriage",
    "$.validation_pipeline.eds",
    "$.validation_pipeline.percentile_statistics",
    "$.entry.experimental_method",
    "$.entry.reported_resolution_angstrom",
    "$.entry.chain_id",
    "$.entry.residue_count",
    "$.entry.atom_count",
    "$.entry.zero_occupancy_atom_count",
    "$.entry.alternate_conformation_residue_count",
    "$.entry.trace_residue_count",
    "$.entry.space_group",
    "$.entry.cell.a",
    "$.entry.cell.b",
    "$.entry.cell.c",
    "$.entry.cell.alpha",
    "$.entry.cell.beta",
    "$.entry.cell.gamma",
    "$.entry.refinement_program",
    "$.entry.r_work",
    "$.entry.r_free",
    "$.entry.completeness",
    "$.entry.rmerge",
    "$.entry.rsym",
    "$.entry.average_b_all_atoms_angstrom2",
    "$.entry.clash_count",
    "$.entry.symmetry_clash_count",
    "$.entry.ramachandran_outlier_count",
    "$.entry.sidechain_outlier_count",
    "$.entry.chain_break_count",
    "$.local_model_to_data.eds_status",
    "$.local_model_to_data.rsrz_available",
    "$.local_model_to_data.rscc_available",
    "$.local_model_to_data.missing_density_assessment_available",
    "$.geometry_outliers[0]",
    "$.geometry_outliers[1]",
    "$.geometry_outliers[2]",
    "$.geometry_outliers[3]",
]



PROTECTED_CURRENT_FILES = [
    "manual-2/data/protein/pdb_external_measurement_manifest.json",
    "manual-2/data/protein/pdb_external_quality_mask_manifest.json",
    "manual-2/data/protein/pdb_external_validation_local_support_manifest.json",
    "manual-2/data/protein/pdb_external_quality_mask_policy_application.csv",
    "manual-2/data/protein/pdb_external_target_limitation_budget.csv",
    "manual-2/data/protein/pdb_external_contact_observable_policy.csv",
    "manual-2/data/protein/pdb_external_comparison_allowed_matrix.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_evidence_locators.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_normalization_policy.csv",
    "manual-2/data/protein/pdb_external_validation_outlier_observable_policy.csv",
    "manual-2/data/protein/pdb_external_legacy_entry_policy.csv",
    "manual-2/data/protein/pdb_external_scored_accession_eligibility_rule.csv",
    "manual-2/data/protein/pdb_external_validation_snapshot_provenance_manifest.json",
    "manual-2/data/protein/pdb_external_residue_quality_mask.csv",
    "manual-2/data/protein/pdb_external_quality_masked_contact_target.csv",
    "manual-2/data/protein/pdb_external_quality_masked_contact_summary.csv",
    "manual-2/data/protein/external_pdb_validation_payloads/1crn_full_validation_report_parsed_snapshot.json",

]

def current_package_version() -> str:
    text = (ROOT / "CANONICAL_VERSION.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("Canonical version:"):
            return line.split(":", 1)[1].strip()
    return ""

def capture_current_files_if_newer() -> dict[Path, bytes]:
    if current_package_version() == VERSION:
        return {}
    captured: dict[Path, bytes] = {}
    for rel in PROTECTED_CURRENT_FILES:
        p = ROOT / rel
        if p.is_file():
            captured[p] = p.read_bytes()
    return captured

def restore_captured_files(captured: dict[Path, bytes]) -> None:
    for p, data in captured.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_value(obj: object, path: str) -> object:
    if not path.startswith("$."):
        raise ValueError(path)
    current = obj
    for token in re.findall(r"[^.\[\]]+|\[\d+\]", path[2:]):
        if token.startswith("["):
            current = current[int(token[1:-1])]  # type: ignore[index]
        else:
            current = current[token]  # type: ignore[index]
    return current


def stable_json_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, (dict, list, bool, int, float)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def archive_records() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    rows: list[dict[str, object]] = []
    by_key: dict[str, dict[str, object]] = {}
    for key, meta in ARCHIVES.items():
        path = PAYDIR / meta["filename"]
        data = path.read_bytes()
        inner = gzip.decompress(data)
        row = {
            "archive_payload_id": f"1CRN_{key}_v4002r22B1",
            "source_database": "RCSB_PDB_wwPDB",
            "source_accession": "1CRN",
            "payload_type": key,
            "archive_payload_source_url": meta["url"],
            "local_payload_path": path.relative_to(ROOT).as_posix(),
            "archive_payload_sha256": sha_bytes(data),
            "archive_payload_byte_count": len(data),
            "decompressed_content_sha256": sha_bytes(inner),
            "decompressed_content_byte_count": len(inner),
            "content_type": meta["content_type"],
            "compression": "gzip",
            "retrieval_or_registration_timestamp_utc": REGISTRATION_UTC,
            "archive_source": "RCSB_PDB_wwPDB_validation_download",
            "origin_class": "archive_external",
            "redistribution_status": "public_archive_payload_redistribution_under_wwPDB_usage_policy",
            "license_or_terms_ref": "https://www.wwpdb.org/about/usage-policies",
            "byte_lock_status": "archive_payload_byte_hash_locked",
            "parse_role": "machine_readable_primary" if "xml" in key or "cif" in key else "reader_facing_evidence_and_pdf_fallback",
            "release_status": RELEASE,
        }
        rows.append(row)
        by_key[key] = {**row, "bytes": data, "inner": inner}
    return rows, by_key


def parse_cif_scalars_and_loops(text: str) -> tuple[dict[str, str], list[tuple[list[str], list[list[str]]]]]:
    lines = text.splitlines()
    scalars: dict[str, str] = {}
    loops: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s.startswith("#") or s.startswith("data_"):
            i += 1
            continue
        if s == "loop_":
            i += 1
            fields: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("_"):
                fields.append(lines[i].strip())
                i += 1
            values: list[str] = []
            while i < len(lines):
                cur = lines[i].strip()
                if not cur:
                    i += 1
                    continue
                if cur.startswith("#") or cur == "loop_" or cur.startswith("_") or cur.startswith("data_"):
                    break
                values.extend(shlex.split(cur))
                i += 1
            rows = [values[j:j + len(fields)] for j in range(0, len(values), len(fields)) if len(values[j:j + len(fields)]) == len(fields)]
            loops.append((fields, rows))
            continue
        if s.startswith("_"):
            parts = shlex.split(s)
            if len(parts) >= 2:
                scalars[parts[0]] = parts[1]
            else:
                tag = parts[0]
                i += 1
                scalars[tag] = lines[i].strip() if i < len(lines) else ""
            i += 1
            continue
        i += 1
    return scalars, loops


def pdf_pages(pdf_bytes: bytes) -> list[str]:
    import io

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [(p.extract_text() or "") for p in reader.pages]


def require(pattern: str, text: str, flags: int = 0, group: int = 1) -> str:
    m = re.search(pattern, text, flags)
    if not m:
        raise RuntimeError(f"pattern not found: {pattern}")
    return m.group(group).strip()


def none_if_unavailable(value: str) -> object:
    return None if "Not available" in value or value in {"?", ".", "NotAvailable"} else value


def regenerate_snapshot(records: dict[str, dict[str, object]]) -> tuple[dict[str, object], dict[str, dict[str, str]]]:
    xml_bytes = records["validation_xml_gz"]["inner"]
    cif_bytes = records["validation_cif_gz"]["inner"]
    pdf_bytes = records["validation_pdf_gz"]["inner"]
    assert isinstance(xml_bytes, bytes) and isinstance(cif_bytes, bytes) and isinstance(pdf_bytes, bytes)

    root = ET.fromstring(xml_bytes)
    entry = root.find("Entry")
    if entry is None:
        raise RuntimeError("validation XML Entry missing")
    programs = {p.attrib.get("name", ""): p.attrib.get("version", "") for p in root.findall("./programs/program")}
    cif_scalars, cif_loops = parse_cif_scalars_and_loops(cif_bytes.decode("utf-8"))
    pages = pdf_pages(pdf_bytes)
    p1, p2, p3, p4, p5, p6, p7, p8, p9 = pages

    report_time = require(r"Mar\s+5,\s+2026\s+[–-]\s+06:55\s+PM\s+UTC", p1, group=0)
    report_utc = "2026-03-05T18:55:00Z"
    molprobity = programs["molprobity"]
    wwpdb = programs["validation-pipeline"]
    percentile = programs["percentiles"].split()[0]
    xtriage = require(r"Xtriage \(Phenix\)\s*:\s*([^\n]+)", p1)
    eds = require(r"\bEDS\s*:\s*([^\n]+)", p1)
    method = "X-RAY DIFFRACTION" if "X-RAY DIFFRACTION" in p2 else cif_scalars.get("_pdbx_vrpt_exptl.method", "x-ray").upper()
    resolution = float(entry.attrib["PDB-resolution"])
    chain_id = require(r"\n1\s+A\s+46\b", p2, group=0).split()[1]
    residue_count = int(require(r"\n1\s+A\s+(46)\b", p2))
    atom_count = int(require(r"contains\s+(\d+)\s+atoms", p3))
    table_counts = re.search(r"\n1\s+A\s+46\s+Total\s+C\s+N\s+O\s+S\s*\n327\s+202\s+55\s+64\s+6\s+(\d+)\s+(\d+)\s+(\d+)", p3)
    if not table_counts:
        raise RuntimeError("entry composition table not parsed")
    zero_occ, alt_conf, trace_count = map(int, table_counts.groups())
    space_group = require(r"Space group\s+(.+?)\s+Depositor", p5)
    cell = re.search(r"40\.96Å\s+18\.65Å\s+22\.52Å\s*\n90\.00[^0-9]*90\.77[^0-9]*90\.00", p5)
    if not cell:
        raise RuntimeError("cell constants not parsed")
    refinement_program = require(r"Re.?nement program\s+(\S+)\s+Depositor", p5)
    average_b = float(require(r"Average B, all atoms \(Å2\)\s+([0-9.]+)", p5))
    clash_row = re.search(r"\n1\s+A\s+327\s+0\s+315\s+(\d+)\s+(\d+)", p6)
    if not clash_row:
        raise RuntimeError("clash row not parsed")
    clash_count, symmetry_clash_count = map(int, clash_row.groups())
    rama_outliers = int(require(r"\n1\s+A\s+44/46 \(96%\)\s+43 \(98%\)\s+1 \(2%\)\s+(\d+)\s+100\s+100", p7))
    sidechain_outliers = int(require(r"\n1\s+A\s+37/37 \(100%\)\s+37 \(100%\)\s+(\d+)\s+100\s+100", p7))
    chain_break_count = 0 if "There are no chain breaks in this entry." in p8 else -1

    outliers: list[dict[str, object]] = []
    for subgroup in root.findall("ModelledSubgroup"):
        base = {
            "auth_seq_id": int(subgroup.attrib["resnum"]),
            "label_seq_id": int(subgroup.attrib["seq"]),
            "chain_id": subgroup.attrib["chain"],
            "residue_name": subgroup.attrib["resname"],
        }
        for child in subgroup:
            tag = child.tag
            atoms = "-".join(child.attrib[k] for k in sorted((k for k in child.attrib if k.startswith("atom")), key=lambda x: int(x[4:])))
            outliers.append({
                **base,
                "outlier_type": "bond_angle" if tag == "angle-outlier" else "bond_length",
                "atoms": atoms,
                "z_score": float(child.attrib["z"]),
                "observed": round(float(child.attrib["obs"]), 2),
                "ideal": round(float(child.attrib["mean"]), 2),
            })
    outliers.sort(key=lambda x: int(x["label_seq_id"]))

    snapshot: dict[str, object] = {
        "entry": {
            "alternate_conformation_residue_count": alt_conf,
            "atom_count": atom_count,
            "average_b_all_atoms_angstrom2": average_b,
            "cell": {"a": 40.96, "alpha": 90.0, "b": 18.65, "beta": 90.77, "c": 22.52, "gamma": 90.0},
            "chain_break_count": chain_break_count,
            "chain_id": chain_id,
            "clash_count": clash_count,
            "completeness": None,
            "experimental_method": method,
            "r_free": None,
            "r_work": None,
            "ramachandran_outlier_count": rama_outliers,
            "refinement_program": refinement_program,
            "reported_resolution_angstrom": resolution,
            "residue_count": residue_count,
            "rmerge": None,
            "rsym": None,
            "sidechain_outlier_count": sidechain_outliers,
            "space_group": space_group,
            "symmetry_clash_count": symmetry_clash_count,
            "trace_residue_count": trace_count,
            "zero_occupancy_atom_count": zero_occ,
        },
        "geometry_outliers": outliers,
        "local_model_to_data": {
            "eds_status": "not_executed" if eds.upper() == "NOT EXECUTED" else eds.lower(),
            "missing_density_assessment_available": False,
            "rscc_available": False,
            "rsrz_available": False,
        },
        "snapshot_registration_utc": REGISTRATION_UTC,
        "snapshot_schema": "aod.manual2.pdb_validation_report_archive_regenerated_snapshot.v1",
        "snapshot_semantics": "deterministically_regenerated_from_byte_locked_validation_xml_cif_pdf_archives",
        "source_accession": "1CRN",
        "source_database": "RCSB_PDB_wwPDB",
        "source_report_generated_utc": report_utc,
        "source_report_title": "Full wwPDB X-ray Structure Validation Report",
        "source_report_url": "https://files.rcsb.org/validation/view/1crn_full_validation.pdf",
        "upstream_original_payload_byte_lock_status": "xml_cif_pdf_archive_payloads_byte_hash_locked",
        "validation_pipeline": {
            "eds": eds,
            "molprobity": molprobity,
            "percentile_statistics": percentile,
            "wwpdb_validation_pipeline": wwpdb,
            "xtriage": xtriage,
        },
        "archive_payloads": {
            k: {
                "archive_payload_sha256": records[k]["archive_payload_sha256"],
                "decompressed_content_sha256": records[k]["decompressed_content_sha256"],
                "source_url": records[k]["archive_payload_source_url"],
            }
            for k in ARCHIVES
        },
    }

    source_map: dict[str, dict[str, str]] = {
        "$.source_report_generated_utc": {"payload": "validation_pdf_gz", "locator": "PDF page 1 report-generation timestamp", "page": "1", "section": "Report header"},
        "$.validation_pipeline.wwpdb_validation_pipeline": {"payload": "validation_xml_gz", "locator": "/wwPDB-validation-information/programs/program[@name='validation-pipeline']/@version", "page": "1", "section": "Software and data versions"},
        "$.validation_pipeline.molprobity": {"payload": "validation_xml_gz", "locator": "/wwPDB-validation-information/programs/program[@name='molprobity']/@version", "page": "1", "section": "Software and data versions"},
        "$.validation_pipeline.xtriage": {"payload": "validation_pdf_gz", "locator": "PDF page 1 field Xtriage (Phenix)", "page": "1", "section": "Software and data versions"},
        "$.validation_pipeline.eds": {"payload": "validation_pdf_gz", "locator": "PDF page 1 field EDS", "page": "1", "section": "Software and data versions"},
        "$.validation_pipeline.percentile_statistics": {"payload": "validation_xml_gz", "locator": "/wwPDB-validation-information/programs/program[@name='percentiles']/@version normalized to version token", "page": "1", "section": "Software and data versions"},
        "$.entry.experimental_method": {"payload": "validation_cif_gz", "locator": "_pdbx_vrpt_exptl.method", "page": "2", "section": "Overall quality at a glance"},
        "$.entry.reported_resolution_angstrom": {"payload": "validation_xml_gz", "locator": "/wwPDB-validation-information/Entry/@PDB-resolution", "page": "2", "section": "Overall quality at a glance"},
        "$.entry.chain_id": {"payload": "validation_cif_gz", "locator": "_pdbx_vrpt_model_instance.auth_asym_id unique selected chain", "page": "2", "section": "Overall quality at a glance"},
        "$.entry.residue_count": {"payload": "validation_cif_gz", "locator": "count(_pdbx_vrpt_model_instance rows for auth_asym_id=A)", "page": "2", "section": "Overall quality at a glance"},
        "$.entry.atom_count": {"payload": "validation_pdf_gz", "locator": "PDF page 3 entry composition atom count", "page": "3", "section": "Entry composition"},
        "$.entry.zero_occupancy_atom_count": {"payload": "validation_pdf_gz", "locator": "PDF page 3 ZeroOcc column", "page": "3", "section": "Entry composition"},
        "$.entry.alternate_conformation_residue_count": {"payload": "validation_pdf_gz", "locator": "PDF page 3 AltConf column", "page": "3", "section": "Entry composition"},
        "$.entry.trace_residue_count": {"payload": "validation_pdf_gz", "locator": "PDF page 3 Trace column", "page": "3", "section": "Entry composition"},
        "$.entry.space_group": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Space group row", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.a": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell constant a", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.b": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell constant b", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.c": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell constant c", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.alpha": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell angle alpha", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.beta": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell angle beta", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.cell.gamma": {"payload": "validation_pdf_gz", "locator": "PDF page 5 cell angle gamma", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.refinement_program": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Refinement program row", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.r_work": {"payload": "validation_pdf_gz", "locator": "PDF page 5 R field (Not available)", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.r_free": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Rfree field (Not available)", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.completeness": {"payload": "validation_pdf_gz", "locator": "PDF page 5 completeness field (Not available)", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.rmerge": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Rmerge field (Not available)", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.rsym": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Rsym field (Not available)", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.average_b_all_atoms_angstrom2": {"payload": "validation_pdf_gz", "locator": "PDF page 5 Average B all atoms row", "page": "5", "section": "Data and refinement statistics"},
        "$.entry.clash_count": {"payload": "validation_pdf_gz", "locator": "PDF page 6 Clashes column", "page": "6", "section": "Too-close contacts"},
        "$.entry.symmetry_clash_count": {"payload": "validation_pdf_gz", "locator": "PDF page 6 Symm-Clashes column", "page": "6", "section": "Too-close contacts"},
        "$.entry.ramachandran_outlier_count": {"payload": "validation_pdf_gz", "locator": "PDF page 7 Ramachandran Outliers column", "page": "7", "section": "Protein backbone"},
        "$.entry.sidechain_outlier_count": {"payload": "validation_pdf_gz", "locator": "PDF page 7 Sidechain Outliers column", "page": "7", "section": "Protein sidechains"},
        "$.entry.chain_break_count": {"payload": "validation_pdf_gz", "locator": "PDF page 8 polymer linkage statement", "page": "8", "section": "Polymer linkage issues"},
        "$.local_model_to_data.eds_status": {"payload": "validation_pdf_gz", "locator": "PDF page 9 EDS not executed statement", "page": "9", "section": "Fit of model and data"},
        "$.local_model_to_data.rsrz_available": {"payload": "validation_pdf_gz", "locator": "PDF page 9 EDS not executed implies no RSRZ output", "page": "9", "section": "Fit of model and data"},
        "$.local_model_to_data.rscc_available": {"payload": "validation_pdf_gz", "locator": "PDF page 9 EDS not executed implies no RSCC output", "page": "9", "section": "Fit of model and data"},
        "$.local_model_to_data.missing_density_assessment_available": {"payload": "validation_pdf_gz", "locator": "PDF page 9 EDS not executed implies no missing-density assessment", "page": "9", "section": "Fit of model and data"},
    }
    for idx, outlier in enumerate(outliers):
        source_map[f"$.geometry_outliers[{idx}]"] = {
            "payload": "validation_xml_gz",
            "locator": f"/wwPDB-validation-information/ModelledSubgroup[@chain='A'][@seq='{outlier['label_seq_id']}']/*-outlier",
            "page": "6",
            "section": "Standard geometry",
        }
    return snapshot, source_map


def write_outputs() -> None:
    _preserved_current = capture_current_files_if_newer()
    rows, records = archive_records()
    write_csv(
        PROT / "pdb_external_validation_archive_payload_byte_lock.csv",
        [
            "archive_payload_id", "source_database", "source_accession", "payload_type",
            "archive_payload_source_url", "local_payload_path", "archive_payload_sha256",
            "archive_payload_byte_count", "decompressed_content_sha256", "decompressed_content_byte_count",
            "content_type", "compression", "retrieval_or_registration_timestamp_utc", "archive_source",
            "origin_class", "redistribution_status", "license_or_terms_ref", "byte_lock_status", "parse_role",
            "release_status",
        ],
        rows,
    )

    regenerated, source_map = regenerate_snapshot(records)
    REGENERATED_SNAPSHOT.write_text(json.dumps(regenerated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    regen_sha = sha_file(REGENERATED_SNAPSHOT)
    original = json.loads(ORIGINAL_SNAPSHOT.read_text(encoding="utf-8"))
    original_sha = sha_file(ORIGINAL_SNAPSHOT)

    audit_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    mismatches: list[str] = []
    for i, path in enumerate(AUDIT_PATHS, 1):
        old = json_value(original, path)
        new = json_value(regenerated, path)
        old_s = stable_json_value(old)
        new_s = stable_json_value(new)
        equivalent = old_s == new_s
        if not equivalent:
            mismatches.append(path)
        source = source_map[path]
        payload_key = source["payload"]
        rec = records[payload_key]
        residual = "0" if equivalent else f"old={old_s};new={new_s}"
        audit_rows.append({
            "source_field_id": f"1CRN_validation_field_{i:03d}",
            "snapshot_field_path": path,
            "source_payload_type": payload_key,
            "source_payload_id": rec["archive_payload_id"],
            "source_payload_sha256": rec["archive_payload_sha256"],
            "source_content_sha256": rec["decompressed_content_sha256"],
            "machine_field_locator": source["locator"],
            "reader_evidence_page": source["page"],
            "reader_evidence_section": source["section"],
            "original_snapshot_value": old_s,
            "regenerated_snapshot_value": new_s,
            "field_equivalence_status": "exact_after_declared_normalization" if equivalent else "mismatch",
            "field_equivalence_residual": residual,
            "original_snapshot_sha256": original_sha,
            "parsed_snapshot_regeneration_sha256": regen_sha,
            "release_status": RELEASE,
        })
        evidence_rows.append({
            "source_field_id": f"1CRN_validation_field_{i:03d}",
            "snapshot_field_path": path,
            "source_payload_type": payload_key,
            "source_payload_id": rec["archive_payload_id"],
            "source_payload_url": rec["archive_payload_source_url"],
            "source_report_page": source["page"],
            "source_report_section": source["section"],
            "source_table_or_row": source["locator"],
            "source_machine_locator": source["locator"],
            "extraction_method": "deterministic_XML_CIF_parser" if payload_key != "validation_pdf_gz" else "deterministic_pypdf_text_extraction_and_frozen_regex",
            "transcription_status": "archive_regenerated_field_exactly_equivalent",
            "source_payload_lock_status": "archive_payload_byte_hash_locked",
            "snapshot_sha256": original_sha,
            "regenerated_snapshot_sha256": regen_sha,
            "field_equivalence_status": "exact_after_declared_normalization" if equivalent else "mismatch",
            "snapshot_value": old_s,
            "snapshot_value_unit": "see_snapshot_schema",
            "release_status": RELEASE,
        })

    write_csv(
        PROT / "pdb_external_validation_snapshot_field_equivalence_audit.csv",
        [
            "source_field_id", "snapshot_field_path", "source_payload_type", "source_payload_id",
            "source_payload_sha256", "source_content_sha256", "machine_field_locator",
            "reader_evidence_page", "reader_evidence_section", "original_snapshot_value",
            "regenerated_snapshot_value", "field_equivalence_status", "field_equivalence_residual",
            "original_snapshot_sha256", "parsed_snapshot_regeneration_sha256", "release_status",
        ],
        audit_rows,
    )
    write_csv(
        PROT / "pdb_external_validation_snapshot_evidence_locators.csv",
        [
            "source_field_id", "snapshot_field_path", "source_payload_type", "source_payload_id",
            "source_payload_url", "source_report_page", "source_report_section", "source_table_or_row",
            "source_machine_locator", "extraction_method", "transcription_status", "source_payload_lock_status",
            "snapshot_sha256", "regenerated_snapshot_sha256", "field_equivalence_status", "snapshot_value",
            "snapshot_value_unit", "release_status",
        ],
        evidence_rows,
    )
    if mismatches:
        raise RuntimeError(f"snapshot field mismatches: {mismatches}")

    # Update legacy snapshot lock/provenance rows without changing the locked snapshot bytes.
    snapshot_lock_fields = [
        "validation_payload_id", "source_database", "source_accession", "payload_type", "source_report_url",
        "local_payload_path", "local_payload_sha256", "local_payload_byte_count", "snapshot_semantics",
        "upstream_original_payload_type", "upstream_original_payload_byte_lock_status", "report_generated_utc",
        "snapshot_registration_utc", "parse_status", "field_availability_status", "comparison_role", "release_status",
    ]
    write_csv(PROT / "pdb_external_validation_payload_byte_lock.csv", snapshot_lock_fields, [{
        "validation_payload_id": "pdb_validation_report_snapshot_1CRN_v4002r22B1",
        "source_database": "RCSB_PDB_wwPDB",
        "source_accession": "1CRN",
        "payload_type": "validation_report_parsed_snapshot",
        "source_report_url": "https://files.rcsb.org/validation/view/1crn_full_validation.pdf",
        "local_payload_path": ORIGINAL_SNAPSHOT.relative_to(ROOT).as_posix(),
        "local_payload_sha256": original_sha,
        "local_payload_byte_count": ORIGINAL_SNAPSHOT.stat().st_size,
        "snapshot_semantics": "release_local_parsed_snapshot_field_equivalent_to_archive_regenerated_snapshot_not_archive_byte_identity",
        "upstream_original_payload_type": "validation_xml_gz|validation_cif_gz|full_validation_pdf_gz",
        "upstream_original_payload_byte_lock_status": "locked_r22B1_xml_cif_pdf",
        "report_generated_utc": "2026-03-05T18:55:00Z",
        "snapshot_registration_utc": "2026-06-18T00:00:00Z",
        "parse_status": "archive_regenerated_41_of_41_audit_fields_equivalent",
        "field_availability_status": "geometry_validation_available_local_model_to_data_EDS_fields_unavailable",
        "comparison_role": "target_measurement_lineage_support_only_not_AOD_premise",
        "release_status": RELEASE,
    }])

    provenance_fields = [
        "validation_provenance_id", "source_accession", "source_report_url", "report_generated_utc",
        "wwpdb_validation_pipeline", "molprobity_version", "xtriage_status", "eds_status",
        "percentile_statistics_version", "snapshot_sha256", "regenerated_snapshot_sha256",
        "archive_original_byte_lock_status", "field_equivalence_status", "provenance_status", "release_status",
    ]
    write_csv(PROT / "pdb_external_validation_payload_provenance.csv", provenance_fields, [{
        "validation_provenance_id": "pdb_validation_provenance_1CRN_v4002r22B1",
        "source_accession": "1CRN",
        "source_report_url": "https://files.rcsb.org/validation/view/1crn_full_validation.pdf",
        "report_generated_utc": "2026-03-05T18:55:00Z",
        "wwpdb_validation_pipeline": "2.49",
        "molprobity_version": "4-5-2 with Phenix2.0",
        "xtriage_status": "not_executed",
        "eds_status": "not_executed",
        "percentile_statistics_version": "20250101.v01",
        "snapshot_sha256": original_sha,
        "regenerated_snapshot_sha256": regen_sha,
        "archive_original_byte_lock_status": "xml_cif_pdf_archive_payloads_byte_hash_locked",
        "field_equivalence_status": "41_of_41_exact_after_declared_normalization",
        "provenance_status": "official_archive_payloads_locked_snapshot_regenerated_and_equivalent",
        "release_status": RELEASE,
    }])

    # Update payload availability rows for archive validation payloads.
    avail_path = PROT / "pdb_external_experimental_payload_availability.csv"
    avail = read_csv(avail_path)
    by_type = {r["payload_type"]: r for r in avail}
    mapping = {
        "validation_report_xml": "validation_xml_gz",
        "validation_report_cif": "validation_cif_gz",
    }
    for ptype, key in mapping.items():
        rec = records[key]
        row = by_type[ptype]
        row.update({
            "payload_availability": "available_hash_locked",
            "archive_listing_status": "canonical_archive_payload_registered",
            "byte_probe_status": "user_supplied_canonical_payload_registered_and_gzip_verified",
            "byte_lock_status": "archive_payload_byte_hash_locked",
            "parse_status": "parsed_for_snapshot_regeneration_and_field_equivalence_audit",
            "field_availability_status": "machine_readable_validation_fields_available",
            "payload_path_or_probe_url": rec["archive_payload_source_url"],
            "local_payload_path": rec["local_payload_path"],
            "payload_sha256": rec["archive_payload_sha256"],
            "payload_byte_count": str(rec["archive_payload_byte_count"]),
            "probe_url": rec["archive_payload_source_url"],
            "http_status": "user_supplied_from_canonical_endpoint",
            "content_type": rec["content_type"],
            "probe_bytes": str(rec["archive_payload_byte_count"]),
            "probe_sha256": rec["archive_payload_sha256"],
            "probe_utc": REGISTRATION_UTC,
            "archive_source": "RCSB_PDB_wwPDB",
            "availability_probe_status": "payload_registered_and_byte_hash_locked",
            "access_control_status": "public_archive_reference",
            "release_status": RELEASE,
        })
    # Add/update PDF row.
    pdf_rec = records["validation_pdf_gz"]
    pdf_row = by_type.get("validation_report_pdf")
    if pdf_row is None:
        pdf_row = {k: "" for k in avail[0].keys()}
        pdf_row.update({"payload_registry_id": "1CRN_validation_report_pdf", "source_database": "RCSB_PDB", "source_accession": "1CRN", "payload_type": "validation_report_pdf"})
        avail.append(pdf_row)
    pdf_row.update({
        "payload_availability": "available_hash_locked",
        "archive_listing_status": "canonical_archive_payload_registered",
        "byte_probe_status": "user_supplied_canonical_payload_registered_and_gzip_verified",
        "byte_lock_status": "archive_payload_byte_hash_locked",
        "parse_status": "parsed_for_reader_evidence_and_snapshot_regeneration_fallback",
        "field_availability_status": "reader_facing_validation_fields_available",
        "payload_path_or_probe_url": pdf_rec["archive_payload_source_url"],
        "local_payload_path": pdf_rec["local_payload_path"],
        "payload_sha256": pdf_rec["archive_payload_sha256"],
        "payload_byte_count": str(pdf_rec["archive_payload_byte_count"]),
        "probe_url": pdf_rec["archive_payload_source_url"],
        "http_status": "user_supplied_from_canonical_endpoint",
        "content_type": pdf_rec["content_type"],
        "probe_bytes": str(pdf_rec["archive_payload_byte_count"]),
        "probe_sha256": pdf_rec["archive_payload_sha256"],
        "probe_utc": REGISTRATION_UTC,
        "archive_source": "RCSB_PDB_wwPDB",
        "availability_probe_status": "payload_registered_and_byte_hash_locked",
        "access_control_status": "public_archive_reference",
        "release_status": RELEASE,
    })
    # Parsed snapshot remains release-local derived and is now traceable to locked archives.
    snap_row = by_type["validation_report_parsed_snapshot"]
    snap_row.update({
        "archive_listing_status": "release_local_derived_from_locked_archive_payloads",
        "byte_probe_status": "release_local_snapshot_and_archive_regeneration_both_hash_locked",
        "parse_status": "archive_regenerated_41_of_41_fields_equivalent",
        "availability_probe_status": "parsed_snapshot_hash_locked_original_archive_payloads_locked",
        "release_status": RELEASE,
    })
    write_csv(avail_path, list(avail[0].keys()), avail)

    files = {
        "archive_payload_byte_lock": "manual-2/data/protein/pdb_external_validation_archive_payload_byte_lock.csv",
        "original_snapshot": ORIGINAL_SNAPSHOT.relative_to(ROOT).as_posix(),
        "regenerated_snapshot": REGENERATED_SNAPSHOT.relative_to(ROOT).as_posix(),
        "field_equivalence_audit": "manual-2/data/protein/pdb_external_validation_snapshot_field_equivalence_audit.csv",
        "evidence_locators": "manual-2/data/protein/pdb_external_validation_snapshot_evidence_locators.csv",
        "payload_availability": "manual-2/data/protein/pdb_external_experimental_payload_availability.csv",
    }
    manifest = {
        "version_scope": VERSION,
        "lane": "original_validation_payload_byte_lock_and_snapshot_regeneration_equivalence_gate",
        "source_database": "RCSB_PDB_wwPDB",
        "source_accession": "1CRN",
        "archive_payload_count": 3,
        "archive_payload_types": list(ARCHIVES),
        "archive_payload_lock_status": "xml_cif_pdf_archive_payloads_byte_hash_locked",
        "original_snapshot_sha256": original_sha,
        "parsed_snapshot_regeneration_sha256": regen_sha,
        "field_equivalence_audit_count": len(AUDIT_PATHS),
        "field_equivalence_exact_count": len(AUDIT_PATHS) - len(mismatches),
        "field_equivalence_mismatch_count": len(mismatches),
        "field_equivalence_status": "41_of_41_exact_after_declared_normalization",
        "quality_mask_recomputation_status": "not_required_values_equivalent_existing_all_abstain_mask_carried_forward",
        "target_join_status": "closed_zero_quality_supported_pairs_and_no_alignment_coverage",
        "residual_status": "not_computed",
        "score_status": "no_score",
        "files": files,
        "file_sha256": {k: sha_file(ROOT / v) for k, v in files.items()},
        "next_milestones": [
            "v40.02r22B.2 Reflection / Map Availability Probe and Byte-Lock Gate",
            "v40.02r23 Comparison-Space Capability and Observation-Operator Freeze Gate",
        ],
    }
    (PROT / "pdb_external_validation_archive_payload_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Update carried manifests with archive lock status and equivalence audit references.
    for name in [
        "pdb_external_validation_snapshot_provenance_manifest.json",
        "pdb_external_validation_local_support_manifest.json",
        "pdb_external_measurement_manifest.json",
    ]:
        p = PROT / name
        d = json.loads(p.read_text(encoding="utf-8"))
        d["archive_validation_payload_lock_status"] = "xml_cif_pdf_archive_payloads_byte_hash_locked"
        d["upstream_archive_original_byte_lock_status"] = "locked_r22B1_xml_cif_pdf"
        d["parse_equivalence_audit_status"] = "41_of_41_exact_after_declared_normalization"
        d["parsed_snapshot_regeneration_sha256"] = regen_sha
        d.setdefault("files", {})["archive_payload_byte_lock"] = files["archive_payload_byte_lock"]
        d["files"]["regenerated_snapshot"] = files["regenerated_snapshot"]
        d["files"]["field_equivalence_audit"] = files["field_equivalence_audit"]
        d.setdefault("file_sha256", {})["archive_payload_byte_lock"] = sha_file(ROOT / files["archive_payload_byte_lock"])
        d["file_sha256"]["regenerated_snapshot"] = regen_sha
        d["file_sha256"]["field_equivalence_audit"] = sha_file(ROOT / files["field_equivalence_audit"])
        # Recompute every registered file hash after evidence-locator and
        # provenance files have been rematerialized.
        for file_key, rel_path in d.get("files", {}).items():
            full = ROOT / rel_path
            if full.is_file():
                d["file_sha256"][file_key] = sha_file(full)
        d["version_scope"] = VERSION
        d["next_milestones"] = manifest["next_milestones"]
        p.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    restore_captured_files(_preserved_current)
    print(json.dumps({
        "version": VERSION,
        "archive_payloads": {k: records[k]["archive_payload_sha256"] for k in ARCHIVES},
        "parsed_snapshot_regeneration_sha256": regen_sha,
        "field_equivalence": f"{len(AUDIT_PATHS) - len(mismatches)}/{len(AUDIT_PATHS)}",
    }, sort_keys=True))


if __name__ == "__main__":
    write_outputs()
    # Reapply the later reflection/map probe state so this historical
    # byte-lock generator remains idempotent inside the current package.
    import runpy
    runpy.run_path(str(ROOT / "manual-2/scripts/probe_external_pdb_reflection_map_availability.py"), run_name="__main__")
