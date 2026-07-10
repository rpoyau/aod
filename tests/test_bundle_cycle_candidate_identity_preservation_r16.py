from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def _version_slug(version: str) -> str:
    return version.strip().replace(".", "_").replace("-", "_")


def _current_candidate_id() -> str:
    state = json.loads((ROOT / "cycle/CYCLE_STATE.json").read_text(encoding="utf-8"))
    return state["working_candidate_bindings"]["candidate_id"]


def test_source_template_declares_authored_candidate_identity():
    state = json.loads((ROOT / "cycle/CYCLE_STATE.json").read_text(encoding="utf-8"))
    candidate_id = _current_candidate_id()
    prefix = f"working_candidate_{_version_slug(state['release']['working_version'])}_"
    assert candidate_id.startswith(prefix)
    assert candidate_id != f"working_candidate_{state['release']['working_version']}"
    assert candidate_id != f"working_candidate_{_version_slug(state['release']['working_version'])}"


def test_materializers_do_not_synthesize_generic_version_only_candidate_id():
    bundle_transition = (ROOT / "tools/run_bundle_transition.py").read_text(encoding="utf-8")
    authoring_revision = (ROOT / "tools/run_authoring_revision.py").read_text(encoding="utf-8")
    assert "_candidate_id_from_source_template" in bundle_transition
    assert "materializer._candidate_id_from_source_template" in authoring_revision
    forbidden = '"candidate_id": f"working_candidate_{args.version}"'
    assert forbidden not in bundle_transition
    assert forbidden not in authoring_revision


def test_review_records_and_validators_bind_candidate_id():
    review_schema = json.loads((ROOT / "cycle/schemas/review-record.schema.json").read_text(encoding="utf-8"))
    review_template_schema = json.loads((ROOT / "cycle/schemas/review-template.schema.json").read_text(encoding="utf-8"))
    assert review_schema["properties"]["candidate_id"] == {"minLength": 1, "type": "string"}
    assert review_template_schema["properties"]["candidate_id"] == {"minLength": 1, "type": "string"}
    transition_text = (ROOT / "tools/run_bundle_transition.py").read_text(encoding="utf-8")
    complete_validator = (ROOT / "tools/validate_complete_bundle.py").read_text(encoding="utf-8")
    phase_validator = (ROOT / "tools/validate_phase_bundle.py").read_text(encoding="utf-8")
    assert '"candidate_id": candidate["candidate_id"]' in transition_text
    assert "REVIEW record candidate-id mismatch" in complete_validator
    assert "phase review candidate-id mismatch" in phase_validator


def test_review_submission_template_names_the_preserved_identity():
    submission = json.loads((ROOT / "governance/reviews/REVIEW_SUBMISSION.template.json").read_text(encoding="utf-8"))
    assert submission["candidate_id"] == _current_candidate_id()
    assert submission["record_scope"] == "source_template"
    assert submission["checks"]
