from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workflow_writes_tests_artifact_before_release_builder():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text()
    assert "pytest -q | tee tests.txt" in workflow
    assert "audit_pack" not in workflow
    assert "verifier.log" not in workflow
    assert "scripts/build_release_bundle.py --outdir dist --tests tests.txt --main main.pdf --manual manual.pdf" in workflow


def test_executed_science_gate_precedes_release_packaging():
    workflow = (ROOT / ".github/workflows/build.yml").read_text()
    gate = "python3 scripts/audit_scientific_sources.py . --build-root ."
    assert workflow.index("cp manual/main.pdf manual.pdf") < workflow.index(gate)
    assert workflow.index(gate) < workflow.index("scripts/build_release_bundle.py --outdir")


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


# This expected inventory is a reader-facing source contract maintained here,
# independently of the release builder's Git command, allowlist and exclusions.
# It works in both the checkout and the published source archive.
SOURCE_ROOT_FILES = {
    ".zenodo.json", ".zenodo_doi", "BUILD.md", "CHANGELOG.md",
    "CANONICAL_VERSION.txt", "LICENSE", "README.md", "cycle_shedding_summary.tex",
    "main.tex", "preamble.tex", "refs.bib", "requirements-ci.txt",
    "wavelet_shedding_simulation.csv", "wavelet_shedding_summary.tex",
}
SOURCE_DIRECTORY_TYPES = {
    ".github": {".yml", ".yaml"},
    "appendices": {".tex"},
    "contracts": {".json", ".md", ".csv"},
    "figures_jpg": {".png", ".jpg"},
    "manual": {".tex", ".bib", ".py", ".csv", ".dat", ".jsonl", ".png", ".jpg", ".md"},
    "scripts": {".py"},
    "sections": {".tex"},
    "tests": {".py"},
}


def expected_source_inventory(root):
    import hashlib
    paths = {root / name for name in SOURCE_ROOT_FILES}
    for name, suffixes in SOURCE_DIRECTORY_TYPES.items():
        for path in (root / name).rglob("*"):
            rel = path.relative_to(root / name)
            if any(part.startswith(".") or part in {"__pycache__", "build", "dist", "release", "_build", "_render", "_renders", "node_modules"}
                   for part in rel.parts[:-1]):
                continue
            if path.is_file() and path.suffix in suffixes:
                paths.add(path)
    assert any(path.parts[-3:-1] == ("contracts", "scientific") for path in paths), "scientific contracts are required"
    return {path.relative_to(root).as_posix():
            (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o777)
            for path in paths}


def release_builder():
    import importlib.util
    spec = importlib.util.spec_from_file_location("release_builder", ROOT / "scripts/build_release_bundle.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


def archive_inventory(path):
    import hashlib
    import zipfile
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        members = archive.infolist()
        names = [item.filename for item in members]
        assert len(names) == len(set(names))
        assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in names)
        return {item.filename: (hashlib.sha256(archive.read(item)).hexdigest(),
                                (item.external_attr >> 16) & 0o777)
                for item in members if not item.is_dir()}


def test_source_archive_exactly_preserves_detached_candidate(tmp_path):
    builder = release_builder()
    source = builder.build_source_tree(tmp_path)
    archive = tmp_path / "source.zip"
    builder.zip_dir(source, archive)
    wanted = expected_source_inventory(ROOT)
    actual = archive_inventory(archive)
    assert actual == wanted
    for name in (".zenodo_doi", "requirements-ci.txt", "wavelet_shedding_simulation.csv",
                 "wavelet_shedding_summary.tex", "CHANGELOG.md"):
        assert name in actual
    assert all(not name.startswith(("evidence/", "projects/", "skills/")) for name in actual)


def test_source_archive_round_trip_without_git_ignores_generated_files(tmp_path, monkeypatch):
    import zipfile
    builder = release_builder()
    wanted = expected_source_inventory(ROOT)
    source = builder.build_source_tree(tmp_path / "first")
    archive = tmp_path / "source.zip"
    builder.zip_dir(source, archive)
    assert archive_inventory(archive) == wanted
    extracted = tmp_path / "extracted"
    # Restore Unix modes as a normal mode-aware unzip implementation does.
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            target = extracted / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zipped.read(info))
            target.chmod((info.external_attr >> 16) & 0o777)
    assert not (extracted / ".git").exists()
    generated = ["main.pdf", "main.aux", "main.fls", "main.fdb_latexmk", "tests.txt",
                 "manual/main.pdf", "manual/main.log", "manual/main.synctex.gz",
                 "manual/main.run.xml", "manual/main.bcf", "manual/main.lof",
                 "scripts/__pycache__/generated.py", "tests/.pytest_cache/README.md",
                 "manual/build/temporary.tex", "dist/source.zip",
                 "evidence/history.json", "projects/private-plan.md",
                 "RELEASE_READINESS.txt", "STALE_TEST_DISPOSITION.md"]
    for name in generated:
        path = extracted / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated or administrative content must not be packaged")
    monkeypatch.setattr(builder, "ROOT", extracted)
    second = builder.build_source_tree(tmp_path / "second")
    builder.zip_dir(second, tmp_path / "second.zip")
    assert archive_inventory(tmp_path / "second.zip") == wanted


def test_detached_source_packaging_does_not_consult_parent_git(tmp_path, monkeypatch):
    import hashlib
    # Ancestor directory names must not be mistaken for generated directories.
    root = tmp_path / "build" / "release" / "source"
    fixture = {"CHANGELOG.md": ("reader changes", 0o644),
               "contracts/scientific/current.json": ('{"scope":"current"}', 0o644),
               "scripts/runner.py": ("#!/usr/bin/env python3\n", 0o755),
               "manual/data/input.dat": ("1 2 3\n", 0o644)}
    wanted = {}
    for name, (body, mode) in fixture.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        target.chmod(mode)
        wanted[name] = (hashlib.sha256(body.encode()).hexdigest(), mode)
    (root.parent / ".git").mkdir()
    builder = release_builder()
    monkeypatch.setattr(builder, "ROOT", root)
    def reject_git(*args, **kwargs):
        raise AssertionError("detached packaging must not consult an unrelated parent checkout")
    monkeypatch.setattr(builder.subprocess, "run", reject_git)
    source = builder.build_source_tree(tmp_path / "stage")
    builder.zip_dir(source, tmp_path / "source.zip")
    assert archive_inventory(tmp_path / "source.zip") == wanted


def test_detached_source_packaging_rejects_symlink_dependency(tmp_path, monkeypatch):
    import pytest
    root = tmp_path / "source"
    (root / "contracts").mkdir(parents=True)
    private = tmp_path / "private.json"
    private.write_text("private project records")
    (root / "contracts/current.json").symlink_to(private)
    builder = release_builder()
    monkeypatch.setattr(builder, "ROOT", root)
    with pytest.raises(ValueError, match="symlink"):
        builder.build_source_tree(tmp_path / "stage")
