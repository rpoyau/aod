from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_writes_tests_artifact_before_release_builder():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "pytest -q | tee tests.txt" in workflow
    assert "audit_pack" not in workflow
    assert "verifier.log" not in workflow
    assert "scripts/build_release_bundle.py --outdir dist --tests tests.txt --main main.pdf --manual manual.pdf" in workflow


def test_release_builder_requires_tests_txt_artifact():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "def resolve_required_artifact" not in script
    assert "verifier.log" not in script
    assert "audit_pack" not in script
    assert "tests_txt = (ROOT / args.tests).resolve()" in script
    assert "required artifact missing" in script


def test_release_builder_uses_fixed_deterministic_zip_members():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert "ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)" in script
    assert "def write_zip_member" in script
    assert "zf.write(" not in script


def test_cycle_shedding_generator_input_is_in_source_archive():
    script = (ROOT / "scripts" / "build_release_bundle.py").read_text()
    assert '"wavelet_shedding_simulation.csv"' in script


def test_ci_build_file_names_are_version_free():
    assert (ROOT / ".github" / "workflows" / "build.yml").exists()
    assert (ROOT / "scripts" / "build_release_bundle.py").exists()
    assert not any("v39" in p.name for p in (ROOT / "scripts").glob("*.py"))
