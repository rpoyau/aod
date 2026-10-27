
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text()


def test_higgs_external_data_comparison_record_wording():
    text = read('manual/sections/01_rest_energy_prediction.tex')
    assert 'Table~\\ref{tab:manual-higgs-lhc-comparison} records the declared Higgs mass-input rows' in text


def test_solar_observable_map_affirmative_scope():
    text = read('manual/sections/05_solar_system_field_tests.tex')
    assert 'map value, target, residual/error, and citation' in text
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


def test_pdf_metadata_declared_in_main_and_manual():
    assert r'\hypersetup{' in read('preamble.tex')
    assert 'pdftitle={Alpha↔Omega Dynamics (AΩD)}' in read('preamble.tex')
    assert 'The Hidden Temporal Dynamics of Stokes; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD temporal dynamics' in read('preamble.tex')
    assert 'pdftitle={Alpha↔Omega Dynamics (AΩD) - Manual}' in read('manual/preamble.tex')
    assert 'The Hidden Temporal Dynamics of Stokes Manual; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD finite simulation fixtures' in read('manual/preamble.tex')


def test_simulation_data_card_present_r59():
    scope = read('manual/sections/00_scope.tex')
    assert r'C_{\mathrm{support}}' in scope
    assert r'\Pi_{\mathrm{report}}' in scope
    assert r'\epsilon_{\mathrm{report}}' in scope
    assert r'\mathrm{src}' in scope


def test_registry_completion_rules_are_affirmative_r59():
    registry = read('manual/sections/09_prediction_test_fixture_registry.tex')
    assert 'External-comparison rows record' in registry
    assert 'Observable-map fixture rows record' in registry
    assert 'Benchmark-dataset rows record' in registry
    assert 'Cross-return rows record' in registry


def test_swells_k0_target_acquisition_fields_only_r61():
    table = read('manual/data/lensing/swells_k0_target_tallies_table.tex')
    csv = read('manual/data/lensing/swells_k0_target_tallies_delta3_acquisition.csv')
    assert 'SWELLS K0 target-side acquisition fields' in table
    for forbidden in ['prediction not joined', 'not scored', 'T^\\times tally', '\\delta_3 status', 'T_cross_predicted_tally', 'delta_3_status']:
        assert forbidden not in table
        assert forbidden not in csv
    assert 'Target family & Class $k$ & $O$ tally' in table


def test_main_walk_support_audit_affirmative_r61():
    app = read('appendices/H_combinatorics_rd_tests.tex')
    assert 'A walk-support reduction records declared first-branch support' in app


def test_r71_final_af_lexical_table_pass():
    scope = read('manual/sections/00_scope.tex')
    rest = read('manual/sections/01_rest_energy_prediction.tex')
    assert 'Projection and marginalization maps carry their own comparison coordinates and uncertainty records' in scope
    assert r'\tabref{tab:ao-field-fractal-properties}' in rest
    assert r'\maintable{main:tab:ao-field-fractal-properties}' not in rest
