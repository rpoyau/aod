from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    return list(csv.DictReader((ROOT / path).open(encoding="utf-8")))


def test_manual2_occurrence_overlay_is_after_shared_dec_ledger():
    main = (ROOT / "manual-2" / "main.tex").read_text(encoding="utf-8")
    dec = "sections/00_dec_ledger.tex"
    overlay = "sections/01_ontology_to_dec_occurrence_overlay.tex"
    elementary = "sections/02_elementary_dec_worked_example.tex"
    assert overlay in main
    assert main.index(dec) < main.index(overlay) < main.index(elementary)


def test_motif_family_registry_has_recurring_families():
    fam = {r["motif_family"]: r for r in rows("manual-2/data/ontology/manual2_curling_curl_motif_family_registry.csv")}
    assert fam["Dimonnanyro"]["scale_exclusivity"] == "not_scale_exclusive"
    assert fam["Tritrioseptyro"]["scale_exclusivity"] == "not_scale_exclusive"
    assert fam["contact_reclosure"]["family_role"] == "recurring contact/reclosure route family"
    assert fam["field_tunnelling"]["route_form"] == "hinge_slide_window_clip"


def test_scoped_occurrence_registry_separates_family_from_occurrence_and_keeps_trace_first_ids():
    data = rows("manual-2/data/ontology/manual2_scoped_occurrence_registry.csv")
    assert all(r["motif_family"] for r in data)
    assert all(r["scoped_occurrence_id"] for r in data)
    assert all(r["motif_family"] != r["scoped_occurrence_id"] for r in data)
    gas = next(r for r in data if r["scoped_occurrence_id"] == "gas_contact_reclosure_occurrence_001")
    assert gas["boundary_id"] == "B_mol_005"
    assert gas["dec_trace_id"] == "trace_mol_005"
    assert gas["aod_motif_id"] == "motif_mol_005"
    assert gas["sadar_context_id"] == "sadar_mol_005"
    assert gas["occurrence_status"] == "occurrence_card_only_not_raw_dec_field"


def test_ontology_to_dec_manifest_order_is_aod_dec_safe():
    data = rows("manual-2/data/ontology/manual2_ontology_to_dec_trace_manifest.csv")
    stages = [r["stage"] for r in data]
    assert stages == [
        "motif_family_registry",
        "scoped_occurrence_card",
        "raw_dec_trace",
        "read_only_trace",
        "aod_motif_curling_curls_detection",
        "sadar",
        "downstream_target_map",
    ]
    status = {r["stage"]: r["order_status"] for r in data}
    assert status["raw_dec_trace"] == "execution_ledger"
    assert status["aod_motif_curling_curls_detection"] == "post_trace_detection"
    assert status["downstream_target_map"] == "downstream_after_freeze"


def test_overlay_does_not_extend_raw_dec_schema():
    raw_header = (ROOT / "manual-2" / "data" / "molecular" / "raw_dec_trace_molecular_chain.csv").read_text(encoding="utf-8").splitlines()[0]
    forbidden = ["motif_family", "scoped_occurrence_id", "adar_id", "sadar_context_id", "external_comparison_lane"]
    for term in forbidden:
        assert term not in raw_header
    section = (ROOT / "manual-2" / "sections" / "01_ontology_to_dec_occurrence_overlay.tex").read_text(encoding="utf-8")
    assert "raw D.E.C. row therefore stays in the shared form" in section
    assert "A$\\Omega$D motif / curling-curls detection" in section
