"""Keep the M2.5 run report distinct from active scientific specifications."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = 'manual/scripts/aod_awareness.py'
REPORT = ROOT / 'evidence/m25/awareness.json'


@pytest.fixture(scope='module')
def fresh_runner_output():
    result = subprocess.run(
        [sys.executable, str(ROOT / RUNNER), '--check-data'],
        cwd=ROOT, capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(result.stdout)


def _check_report(report, fresh):
    assert set(report) == {'schema', 'runner', 'runner_output'}, 'Run report envelope required'
    assert report['schema'] == 'aod.fixture-run-report.v1'
    assert report['runner'] == RUNNER
    output = report['runner_output']
    assert output['source_sha256'] == hashlib.sha256((ROOT / RUNNER).read_bytes()).hexdigest(), \
        'Run report engine hash is stale'
    assert output == fresh, 'Run report differs from fresh runner output'
    fixtures = [json.loads(line) for line in
                (ROOT / 'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()
                if line.strip()]
    assert len(output['results']) == len(fixtures) == 47
    assert [row['fixture_id'] for row in output['results']] == [row['fixture_id'] for row in fixtures]
    for result, fixture in zip(output['results'], fixtures):
        assert result['expected_matched'] is True
        assert result['verdict'] == fixture['expected_verdict']
        if fixture['expected_verdict'] == 'PASS':
            assert result['actual'] == fixture['expected_exact']
        else:
            assert result['actual'] is None


def test_committed_awareness_run_report_matches_unchanged_runner(fresh_runner_output):
    _check_report(json.loads(REPORT.read_text()), fresh_runner_output)


@pytest.mark.parametrize('mutation, diagnostic', [
    ('stale-hash', 'Run report engine hash is stale'),
    ('altered-result', 'Run report differs from fresh runner output'),
])
def test_run_report_rejects_stale_hash_or_altered_result(fresh_runner_output, mutation, diagnostic):
    report = deepcopy(json.loads(REPORT.read_text()))
    if mutation == 'stale-hash':
        report['runner_output']['source_sha256'] = '0' * 64
    else:
        # Retain the original expected_matched flag: the recorded verdict
        # cannot conceal a changed result behind a stale success claim.
        report['runner_output']['results'][0]['actual']['first_positive'] = '999'
    with pytest.raises(AssertionError, match=diagnostic):
        _check_report(report, fresh_runner_output)
