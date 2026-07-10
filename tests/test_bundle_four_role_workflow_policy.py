import json
from pathlib import Path


def test_four_role_policy_is_authority_bound():
    policy = json.loads(Path('governance/AGENT_WORKFLOW_POLICY.json').read_text())
    assert policy['workflow_id'] == 'AOD_AF_AFC_FOUR_ROLE_BUNDLE_LOOP'
    assert policy['scientific_research_authority'] == 'project_owner'
    assert policy['roles']['owner_researcher']['may_not_be_substituted_by_ai'] is True
    assert 'new_axioms' in policy['roles']['authoring_builder']['forbidden']
    assert 'source_tree_hash_surfaces' in policy['roles']['surface_synchronizer']['must_check']
    assert policy['roles']['independent_reviewer']['self_review_sufficient'] is False


def test_role_trace_records_four_role_lifecycle():
    rows = [json.loads(line) for line in Path('cycle/ROLE_TRACE.jsonl').read_text().splitlines() if line]
    roles = [row['role'] for row in rows]
    assert roles[:4] == ['owner_researcher','authoring_builder','surface_synchronizer','independent_reviewer']
