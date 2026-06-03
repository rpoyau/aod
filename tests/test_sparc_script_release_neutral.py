from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sparc_score_script_uses_current_release_comments():
    text = (ROOT / "manual" / "scripts" / "score_sparc_field_dynamics.py").read_text(encoding="utf-8")
    assert "Frozen primary-lane declarations for the current release lane." in text
    assert "Controls are declared comparison variants from the current diagnostic run." in text
    assert "v39.99r1" not in text
    assert "v39.99 diagnostic run" not in text
