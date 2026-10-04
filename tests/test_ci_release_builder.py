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


def test_ci_build_file_names_are_version_free():
    assert (ROOT / ".github" / "workflows" / "build.yml").exists()
    assert (ROOT / "scripts" / "build_release_bundle.py").exists()
    assert not any("v39" in p.name for p in (ROOT / "scripts").glob("*.py"))


def test_source_archive_exactly_preserves_detached_candidate(tmp_path):
    import importlib.util, hashlib, os, subprocess, zipfile
    spec=importlib.util.spec_from_file_location('release_builder',ROOT/'scripts/build_release_bundle.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    source=builder.build_source_tree(tmp_path)
    builder.zip_dir(source,tmp_path/'source.zip')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')
    tracked_paths=(Path(os.fsdecode(raw)) for raw in tracked if raw)
    wanted={rel.as_posix():hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
            for rel in tracked_paths}
    with zipfile.ZipFile(tmp_path/'source.zip') as z:
        actual={i.filename:hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist() if not i.is_dir()}
    assert actual==wanted
    for name in ('.zenodo_doi','requirements-ci.txt','wavelet_shedding_simulation.csv','wavelet_shedding_summary.tex'):
        assert name in actual
