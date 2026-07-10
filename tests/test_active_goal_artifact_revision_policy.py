import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_active_goal_separates_revised_and_frozen_artifacts():
    goal = json.loads((ROOT / "cycle/ACTIVE_GOAL.json").read_text(encoding="utf-8"))
    frozen = set(goal["frozen_artifacts"])
    revised = set(goal["intentionally_revised_artifacts"])
    assert not (frozen & revised)
    assert {"main.pdf", "manual.pdf", "manual-2.pdf", "sections/", "manual/", "manual-2/"} <= revised
    assert {"shared/", "external_payloads/"} <= frozen
