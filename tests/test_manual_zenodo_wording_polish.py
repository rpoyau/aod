
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def test_higgs_external_data_comparison_record_wording():
    text = read('manual/sections/01_rest_energy_prediction.tex')
    assert r'\paragraph{External data-comparison record.}' in text
    assert 'Allowed claim level' not in text
    assert 'Table~\\ref{tab:manual-higgs-lhc-comparison} records the declared Higgs mass-input rows' in text


def test_solar_observable_map_affirmative_scope():
    text = read('manual/sections/05_solar_system_field_tests.tex')
    assert 'map value, target, residual/error, and citation' in text
    assert 'full derivation constants' not in text
    assert 'GR equation' not in text
    assert 'Input audit: target values are cited' in text


def test_sparc_scope_and_uncertainty_policy_are_data_scoped():
    text = read('manual/sections/06_field_dynamics_applications.tex')
    assert 'G0 active input fields' in text
    assert r'\(\sigma_U=2V^{\mathrm{obs}}\sigma_V\)' in text
    assert 'G0 active input fields' in text
    assert r'G1/G2/G3 packages carry angular, vertical, or time-flow fields through declared source or proxy rows' in text


def test_lensing_l3_data_package_wording():
    text = read('manual/sections/07_galactic_lensing_plan.tex') + read('manual/sections/09_prediction_test_fixture_registry.tex')
    assert 'L3 lensing input package' in text
    assert 'L3 input-manifest row' in text
    assert 'release not claimed' not in text


def test_simulation_reading_route_and_provenance_policy_present():
    text = read('manual/sections/00_scope.tex')
    assert r'\subsection{Simulation reading route}' in text
    assert r'\subsection{Provenance-label policy}' in text
    assert 'Tokens of the form' in text and 'cross-document provenance anchors' in text


def test_pdf_metadata_declared_in_main_and_manual():
    assert r'\hypersetup{' in read('preamble.tex')
    assert 'pdftitle={Alpha-Omega Dynamics: The Hidden Temporal Dynamics of Stokes}' in read('preamble.tex')
    assert 'The Hidden Temporal Dynamics of Stokes; AFC/AOD temporal dynamics' in read('preamble.tex')
    assert 'pdftitle={Alpha-Omega Dynamics: The Hidden Temporal Dynamics of Stokes - Manual}' in read('manual/preamble.tex')
    assert 'The Hidden Temporal Dynamics of Stokes Manual; AFC/AOD finite simulation fixtures' in read('manual/preamble.tex')



def test_manual_no_claim_data_scope_wording():
    manual_text = "\n".join(p.read_text() for p in (ROOT / "manual" / "sections").glob("*.tex"))
    manual_text += "\n" + "\n".join(p.read_text() for p in (ROOT / "manual" / "appendices").glob("*.tex"))
    forbidden = [
        "not present in this release",
        "release not claimed",
        "not as released worked examples",
        "fails promotion",
        "fails release status",
        "release audit to be declared",
        "does not carry application labels",
        "external comparison claims",
        "not a SPARC projection lane",
        "does not declare angular",
        "not external measured-sector residuals",
        "not a Gaia-scored comparison",
        "No GeV target or LHC value appears",
    ]
    for term in forbidden:
        assert term not in manual_text


def test_simulation_data_card_present():
    scope = read('manual/sections/00_scope.tex')
    assert r'\paragraph{Simulation data card.}' in scope
    assert r'C_{\mathrm{support}}' in scope
    assert r'\Pi_{\mathrm{report}}' in scope
    assert r'\epsilon_{\mathrm{report}}' in scope
    assert r'\mathrm{src}' in scope


def test_registry_completion_rules_are_affirmative():
    registry = read('manual/sections/09_prediction_test_fixture_registry.tex')
    assert 'Completion rule' in registry
    assert 'External-comparison rows record' in registry
    assert 'Observable-map fixture rows record' in registry
    assert 'Benchmark-dataset rows record' in registry
    assert 'Cross-return rows record' in registry



def test_swells_k0_target_acquisition_fields_only():
    table = read('manual/data/lensing/swells_k0_target_tallies_table.tex')
    csv = read('manual/data/lensing/swells_k0_target_tallies_delta3_acquisition.csv')
    assert 'SWELLS K0 target-side acquisition fields' in table
    for forbidden in ['prediction not joined', 'not scored', 'T^\\times tally', '\\delta_3 status', 'T_cross_predicted_tally', 'delta_3_status']:
        assert forbidden not in table
        assert forbidden not in csv
    assert 'Target family & Class $k$ & $O$ tally' in table


def test_main_walk_support_audit_affirmative():
    app = read('appendices/H_combinatorics_rd_tests.tex')
    assert r'\subsection{Walk-support audit}' in app
    assert 'A walk-support reduction records declared first-branch support' in app
    for forbidden in ['claimed RD row', 'claimed row', 'Use of \\(2\\Pi+1\\) fails', 'A kernel fails']:
        assert forbidden not in app


def test_sparc_caption_records_not_entries():
    table = read('manual/data/derived/sparc_summary_table.tex')
    assert 'SPARC five-galaxy scored records' in table
    assert 'SPARC five-galaxy scored entries' not in table


def test_final_af_lexical_table_pass():
    scope = read('manual/sections/00_scope.tex')
    field = read('manual/sections/06_field_dynamics_applications.tex')
    rest = read('manual/sections/01_rest_energy_prediction.tex')
    solar = read('manual/sections/05_solar_system_field_tests.tex')
    dec = read('manual/sections/00_dec_ledger.tex')
    assert 'Projection and marginalization maps carry their own comparison coordinates and uncertainty records' in scope
    assert 'unresolved' not in field.lower()
    assert 'undeclared' not in field.lower()
    assert 'route / slosh / pending' not in field
    assert 'no-override internal selection rule' not in rest
    assert 'candidate-identity override' not in rest
    assert 'Field-support properties are listed in the main note, App.~J' in rest
    assert 'Field-support properties are not repeated here' not in rest
    assert 'read-only unless' not in rest
    assert 'Status' not in solar.split('\\subsection{Observable-map comparison table}', 1)[1].split('\\end{table}', 1)[0]
    assert 'It carries no external measured-sector target' not in dec
    assert 'not low probability' not in dec
