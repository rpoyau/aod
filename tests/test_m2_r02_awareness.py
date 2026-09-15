"""R04 replacements for held phrase-only M2 assertions; no historical rerun claim."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]

def test_historical_roster_is_separate_from_new_executions():
    rows=list(csv.DictReader((ROOT/'evidence/m2/HISTORICAL_TOY_SOURCE_STATUS.csv').open()))
    assert len(rows)==19
    for row in rows:
        assert 'SOURCE_MISSING' in row.values()
    new=[json.loads(t) for t in (ROOT/'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()]
    assert all(x['fixture_id'].startswith('R04-NEW-') for x in new)


def test_every_m2_claim_has_positive_and_hostile_executable_inputs():
    rows=[json.loads(t) for t in (ROOT/'manual/data/m2/awareness_cases.jsonl').read_text().splitlines()]
    claims={r['claim_id'] for r in rows};assert len(claims)==8
    for claim in claims:assert {'positive','hostile'}<={r['case_kind'] for r in rows if r['claim_id']==claim}
