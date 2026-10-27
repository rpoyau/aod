#!/usr/bin/env python3
"""Validate a fresh awareness run against canonical inputs and actual execution.

A run report is transient output, never a scientific specification. This check
uses only this source tree and the unchanged runner; no Git or network access
is needed. A supplied report is compared with a fresh execution as well as the
canonical fixture expectations, including rejection diagnostics and row order.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = 'manual/scripts/aod_awareness.py'
FIXTURES = 'manual/data/m2/awareness_cases.jsonl'
SCHEMA = 'aod.fixture-run-report.v1'


def exact_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run_report(root=ROOT):
    root = Path(root).resolve()
    result = subprocess.run(
        [sys.executable, str(root / RUNNER), '--check-data'], cwd=root,
        capture_output=True, text=True, check=True, timeout=60,
    )
    return {'schema': SCHEMA, 'runner': RUNNER, 'runner_output': json.loads(result.stdout)}


def validate_report(report, root=ROOT):
    root = Path(root).resolve()
    require(isinstance(report, dict) and set(report) == {'schema', 'runner', 'runner_output'},
            'Run report envelope required')
    require(report['schema'] == SCHEMA, 'Run report schema mismatch')
    require(report['runner'] == RUNNER, 'Run report runner path mismatch')
    output = report['runner_output']
    require(isinstance(output, dict) and set(output) == {'source_sha256', 'results'},
            'Raw runner output fields mismatch')
    source_hash = hashlib.sha256((root / RUNNER).read_bytes()).hexdigest()
    require(output['source_sha256'] == source_hash, 'Run report engine hash is stale')
    fixtures = [json.loads(line) for line in (root / FIXTURES).read_text().splitlines() if line.strip()]
    results = output['results']
    require(isinstance(results, list) and len(results) == len(fixtures) == 47,
            'Run report must contain the canonical 47 rows')
    ids = [row['fixture_id'] for row in fixtures]
    require(len(set(ids)) == 47, 'Duplicate canonical fixture identity')
    require(all(isinstance(row, dict) for row in results), 'Invalid run report row')
    require([row.get('fixture_id') for row in results] == ids, 'Run report fixture identity or order mismatch')
    for result, fixture in zip(results, fixtures):
        identity = fixture['fixture_id']
        require(set(result) == {'fixture_id', 'verdict', 'actual', 'error', 'input_digest', 'expected_matched'},
                'Run report result fields mismatch: ' + identity)
        require(fixture['source'] == RUNNER and fixture['source_sha256'] == source_hash,
                'Canonical fixture engine binding mismatch: ' + identity)
        input_hash = hashlib.sha256(json.dumps(fixture['inputs'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        require(result['input_digest'] == input_hash, 'Run report input digest mismatch: ' + identity)
        require(result['expected_matched'] is True, 'Run report reports an unmatched expectation: ' + identity)
        require(result['verdict'] == fixture['expected_verdict'], 'Run report verdict mismatch: ' + identity)
        require(exact_json(result['actual']) == exact_json(fixture['expected_exact']), 'Run report exact result mismatch: ' + identity)
        if fixture['expected_verdict'] == 'PASS':
            require(result['error'] is None, 'Successful fixture contains a rejection: ' + identity)
        else:
            require(fixture['expected_verdict'] == 'REJECT' and isinstance(result['error'], str) and bool(result['error']),
                    'Rejected fixture lacks a diagnostic: ' + identity)
    # Canonical rejected fixtures specify REJECT, rather than a literal error
    # message. Fresh execution additionally binds their exact diagnostics and
    # every other output field; a stale success flag grants no authority.
    require(exact_json(output) == exact_json(run_report(root)['runner_output']), 'Run report differs from fresh runner output')
    return {'status': 'PASS', 'results': len(results), 'engine_sha256': source_hash}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path, help='Validate an existing transient report instead of generating one')
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text()) if args.report else run_report(args.root)
        result = validate_report(report, args.root)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
