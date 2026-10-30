"""Fresh fixture reports remain separate from current scientific contracts."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_fixture_report', ROOT / 'scripts/validate_fixture_report.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.fixture(scope='module')
def fresh_report():
    # Run the actual, unchanged CLI. No historical report or private archive is
    # an input to either these tests or the validator used by the CLI below.
    return validator.run_report(ROOT)


def test_fresh_awareness_run_report_matches_canonical_inputs_and_runner(fresh_report):
    result = validator.validate_report(fresh_report, ROOT)
    assert result['status'] == 'PASS' and result['results'] == 47


@pytest.mark.parametrize('mutation, diagnostic', [
    ('stale-hash', 'Run report engine hash is stale'),
    ('altered-result', 'Run report exact result mismatch'),
    ('altered-type', 'Run report exact result mismatch'),
    ('altered-rejection', 'Run report differs from fresh runner output'),
    ('row-order', 'Run report fixture identity or order mismatch'),
    ('stale-success', 'Run report reports an unmatched expectation'),
    ('wrong-schema', 'Run report schema mismatch'),
    ('wrong-runner', 'Run report runner path mismatch'),
])
def test_run_report_rejects_changed_execution(fresh_report, mutation, diagnostic):
    # The untouched actual execution must pass before a hostile mutation counts.
    assert validator.validate_report(fresh_report, ROOT)['status'] == 'PASS'
    report = deepcopy(fresh_report)
    rows = report['runner_output']['results']
    if mutation == 'stale-hash':
        report['runner_output']['source_sha256'] = '0' * 64
    elif mutation == 'altered-result':
        rows[0]['actual']['first_positive'] = '999'
        assert rows[0]['expected_matched'] is True
    elif mutation == 'altered-type':
        rows[0]['actual']['effect'] = 1  # JSON true and integer 1 are distinct.
    elif mutation == 'altered-rejection':
        rejected = next(row for row in rows if row['verdict'] == 'REJECT')
        rejected['error'] = 'invented rejection that did not occur'
        assert rejected['expected_matched'] is True
    elif mutation == 'row-order':
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == 'stale-success':
        rows[0]['expected_matched'] = False
    elif mutation == 'wrong-schema':
        report['schema'] = 'aod.scientific.unknown.v1'
    else:
        report['runner'] = 'manual/scripts/aod_native_closure_wave.py'
    with pytest.raises(ValueError, match=diagnostic):
        validator.validate_report(report, ROOT)


def test_cli_report_validation_rejects_tampered_actual_under_optimized_python(fresh_report, tmp_path):
    path = tmp_path / 'run-report.json'
    path.write_text(json.dumps(fresh_report))
    command = [sys.executable, '-O', str(ROOT / 'scripts/validate_fixture_report.py'),
               '--root', str(ROOT), '--report', str(path)]
    positive = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert positive.returncode == 0, positive.stdout + positive.stderr
    assert json.loads(positive.stdout)['results'] == 47
    hostile = deepcopy(fresh_report)
    hostile['runner_output']['results'][0]['actual']['first_positive'] = '999'
    path.write_text(json.dumps(hostile))
    negative = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert negative.returncode != 0
    assert json.loads(negative.stdout)['status'] == 'FAIL'
