"""Tier-1 read-only subprocess adapters for the 9 canonical AOD drivers.

Never imports ``manual.scripts.*`` directly (preserves flat sibling-import scripts
and guarantees zero Group-B import side effects). Propagates ``-B`` and ``-O`` flags
explicitly into every child Python interpreter.
"""
from __future__ import annotations

import gzip
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import zlib

from manual.engine.numeric import parse_exact_int, require
from manual.engine.policy import loads_zero_float, require_no_floats
from manual.engine.registry import SectorSpec
from manual.engine.report import atomic_write_safe_text, validate_runtime_output_path

_DEFAULT_TIMEOUT_SECONDS: int = 300
_ANCHOR_TIMEOUT_SECONDS: int = 3600

_AWARENESS_SCRIPT_SHA256: str = (
    "d480397d0948513cd7a9f8fc9a1f2c1a0ef82d160f3306a892a7642cc0069a15"
)

_WAVELET_CHECK_GROUPS: tuple[str, ...] = (
    "P2-01",
    "P2-02",
    "P2-03_P2-04",
    "P2-05_P2-06",
    "P2-07",
    "P2-08",
    "P2-09",
    "P2-10",
    "P2-11",
    "P2-12",
    "P2-13",
    "P2-14",
    "P2-15",
)

_EXPERIMENTAL_QUANTITY_ROUTES: frozenset[str] = frozenset(
    {
        "finite_joint_law",
        "nonlinear_moments",
        "bounds",
        "metadata",
        "conversion",
        "shared_cancel",
        "shared_reinforce",
        "multi_output",
        "published",
        "published_moments",
    }
)


def _sha256_regular_file(repo_root: Path, rel_path: str) -> str:
    rel = Path(rel_path)
    require(not rel.is_absolute() and ".." not in rel.parts, f"unsafe relative path: {rel_path}")
    target = repo_root / rel
    require(target.exists(), f"required input path missing: {rel_path}")
    require(not target.is_symlink(), f"symlink forbidden for input path: {rel_path}")
    for parent in rel.parents:
        if parent != Path("."):
            require(
                not (repo_root / parent).is_symlink(),
                f"symlink parent forbidden for input path: {rel_path}",
            )
    require(target.is_file(), f"required input path is not a regular file: {rel_path}")
    return hashlib.sha256(target.read_bytes()).hexdigest()


def _hash_inputs(repo_root: Path, input_paths: tuple[str, ...]) -> dict[str, str]:
    return {rel: _sha256_regular_file(repo_root, rel) for rel in sorted(input_paths)}


def _read_json_zero_float(path: Path) -> object:
    payload = loads_zero_float(path.read_text(encoding="utf-8"))
    require_no_floats(payload)
    return payload


def _validate_native_closure_wave(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del repo_root, pre_digests
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "native_closure_wave stdout must be a JSON object")
    require(
        set(data.keys()) == {"results", "passed", "total"},
        f"unexpected native_closure_wave stdout keys: {sorted(data.keys())}",
    )
    total = parse_exact_int(data["total"], name="total")
    passed = parse_exact_int(data["passed"], name="passed")
    results = data["results"]
    require(isinstance(results, list), "results must be a list")
    require(total == 83 and passed == 83 and len(results) == 83, f"expected 83/83 fixtures, got {passed}/{total} ({len(results)})")

    seen_ids: set[str] = set()
    positive_pass = 0
    hostile_reject = 0
    for idx, row in enumerate(results):
        require(isinstance(row, dict), f"results[{idx}] must be a dict")
        require(row.get("expected_matched") is True, f"fixture mismatch at results[{idx}]")
        fid = row.get("fixture_id")
        require(isinstance(fid, str) and bool(fid), f"missing fixture_id at results[{idx}]")
        require(fid not in seen_ids, f"duplicate fixture_id: {fid}")
        seen_ids.add(fid)
        verdict = row.get("actual_verdict")
        require(verdict in ("PASS", "REJECT"), f"invalid verdict for {fid}: {verdict!r}")
        if verdict == "PASS":
            positive_pass += 1
        else:
            hostile_reject += 1

    require(positive_pass > 0 and hostile_reject > 0, "both PASS and REJECT verdicts must be strictly positive")
    return (
        {
            "fixtures_total": total,
            "fixtures_passed": passed,
            "positive_pass": positive_pass,
            "hostile_reject": hostile_reject,
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_awareness(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del repo_root
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "awareness stdout must be a JSON object")
    require(
        set(data.keys()) == {"source_sha256", "results"},
        f"unexpected awareness stdout keys: {sorted(data.keys())}",
    )
    script_sha = pre_digests["manual/scripts/aod_awareness.py"]
    require(
        data["source_sha256"] == script_sha == _AWARENESS_SCRIPT_SHA256,
        "awareness source_sha256 does not match frozen pinned digest",
    )
    results = data["results"]
    require(isinstance(results, list) and len(results) == 47, f"expected 47 awareness results, got {len(results) if isinstance(results, list) else type(results).__name__}")

    expected_ids = {f"R04-NEW-{i:03d}" for i in range(1, 48)}
    seen_ids: set[str] = set()
    positive_pass = 0
    hostile_reject = 0
    for idx, row in enumerate(results):
        require(isinstance(row, dict), f"awareness results[{idx}] must be a dict")
        require(row.get("expected_matched") is True, f"awareness mismatch at index {idx}")
        fid = row.get("fixture_id")
        require(isinstance(fid, str) and fid not in seen_ids, f"invalid/duplicate awareness fixture_id: {fid!r}")
        seen_ids.add(fid)
        verdict = row.get("verdict")
        require(verdict in ("PASS", "REJECT"), f"invalid awareness verdict for {fid}: {verdict!r}")
        if verdict == "PASS":
            positive_pass += 1
        else:
            hostile_reject += 1

    require(seen_ids == expected_ids, "awareness fixture_id set mismatch against R04-NEW-001..047")
    require(positive_pass > 0 and hostile_reject > 0, "awareness must include both PASS and REJECT verdicts")
    return (
        {
            "fixtures_total": 47,
            "fixtures_passed": 47,
            "positive_pass": positive_pass,
            "hostile_reject": hostile_reject,
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_cell_measures(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "cell_measures stdout must be a JSON object")
    rel_report = "manual/data/cell_measures/cells_geometry.json"
    require(data.get("report") == rel_report, f"unexpected cell_measures report path: {data.get('report')!r}")
    require(data.get("conditional_geometry") == "reproduced", "conditional_geometry not reproduced")
    require(data.get("native_metric") == "not_established", "native_metric hold lost")
    require(data.get("sha256") == pre_digests[rel_report], "cell_measures report sha256 mismatch")

    doc = _read_json_zero_float(repo_root / rel_report)
    require(isinstance(doc, dict), "cells_geometry.json must be a dict")
    require(doc.get("schema") == "aod-m3-cells-geometry-v1", "unexpected cells_geometry schema")
    levels = doc["G3_G4"]["levels"]
    require(isinstance(levels, list) and len(levels) == 6, "expected 6 G3_G4 refinement levels")
    level_ns = [parse_exact_int(lv["n"], name="level.n") for lv in levels]
    require(level_ns == [1, 2, 4, 8, 16, 32], f"unexpected refinement levels: {level_ns}")
    neg_controls = doc["negative_controls"]
    require(isinstance(neg_controls, (list, dict)) and len(neg_controls) == 9, "expected 9 negative controls")
    pi_refs = doc["G3_G4"]["reference_comparisons"]
    require(isinstance(pi_refs, list) and len(pi_refs) == 3, "expected 3 pi reference comparisons")
    require(doc["G6"]["status"] == "not_opened", "G6 status hold lost")
    return (
        {
            "disk_refinement_levels": len(levels),
            "negative_controls": len(neg_controls),
            "pi_reference_comparisons": len(pi_refs),
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_mapping_error(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del pre_digests
    data = loads_zero_float(stdout)
    require_no_floats(data)
    rel_report = "manual/data/mapping_error/mapping_error.json"
    require(
        data == {"report": rel_report, "mode": "check", "status": "reconstructed"},
        f"unexpected mapping_error stdout: {data!r}",
    )
    doc = _read_json_zero_float(repo_root / rel_report)
    require(isinstance(doc, dict), "mapping_error.json must be a dict")
    require(doc.get("schema") == "aod.m3.mapping-error.v2", "unexpected mapping_error schema")
    maps = doc["maps"]
    require(isinstance(maps, (list, dict)) and len(maps) == 3, "expected 3 maps in mapping_error.json")
    hist = doc["original_historical_laws"]
    replay = hist["replay"]
    require(
        replay.get("status") == "original_output_byte_identical",
        "historical replay status mismatch",
    )
    require(
        replay.get("legacy_complete_claim_negative_control") == "rejected_as_expected",
        "legacy complete claim negative control mismatch",
    )
    cases = hist["cases"]
    require(isinstance(cases, dict) and set(cases.keys()) == {"MAP-21", "MAP-22"}, "unexpected historical cases")
    for cid in ("MAP-21", "MAP-22"):
        require(
            cases[cid].get("status") == "verified_original_synthetic_finite_law",
            f"{cid} status mismatch",
        )
    bindings = _read_json_zero_float(repo_root / "manual/data/historical_metrology/source_bindings.json")
    require(isinstance(bindings, dict) and len(bindings["files"]) == 8, "expected 8 historical bound files")
    return (
        {
            "maps": len(maps),
            "historical_laws": len(cases),
            "historical_bound_files": len(bindings["files"]),
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_temporal_observation(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del pre_digests
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "temporal_observation stdout must be a JSON object")
    require(
        set(data.keys()) == {"status", "output", "atomic_prediction"},
        f"unexpected temporal_observation stdout keys: {sorted(data.keys())}",
    )
    require(data["status"] == "reconstructed", "temporal_observation status must be reconstructed")
    require(data["atomic_prediction"] == "incomplete", "atomic_prediction hold lost")
    rel_target = "manual/data/temporal_observation/temporal.json"
    expected_abs = (repo_root / rel_target).resolve()
    raw_output = data["output"]
    require(isinstance(raw_output, str) and bool(raw_output), "missing output path in temporal_observation stdout")
    require(
        Path(raw_output).resolve() == expected_abs,
        "temporal_observation output path does not resolve to manual/data/temporal_observation/temporal.json",
    )
    # Strip absolute path from canonical report bytes; only record repo-relative path.
    doc = _read_json_zero_float(expected_abs)
    require(isinstance(doc, dict), "temporal.json must be a dict")
    sv = parse_exact_int(doc["schema_version"], name="schema_version")
    require(sv == 3, f"expected schema_version 3, got {sv}")
    pred = doc["prediction"]
    require(
        pred.get("classification") == "conditional_model_prediction_not_atomic_prediction",
        "temporal.json prediction classification mismatch",
    )
    require(pred.get("atomic_prediction") is None, "temporal.json atomic_prediction must be null")
    countermodels = doc["gain_countermodels"]
    require(isinstance(countermodels, (list, dict)) and len(countermodels) == 2, "expected 2 gain_countermodels")
    return (
        {"schema_version": sv, "gain_countermodels": len(countermodels)},
        {
            "exact_match": True,
            "max_residual": "0",
            "canonical_output_relpath": rel_target,
            "absolute_output_path_stripped": True,
        },
    )


def _validate_temporal_metrology(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del pre_digests
    require(
        stdout.strip() == "temporal metrology report verified",
        f"unexpected temporal_metrology stdout: {stdout.strip()!r}",
    )
    doc = _read_json_zero_float(repo_root / "manual/data/temporal_metrology/report.json")
    require(isinstance(doc, dict), "temporal_metrology report.json must be a dict")
    require(doc.get("schema") == "aod.m3.temporal-metrology-report.v1", "unexpected temporal_metrology schema")
    hydrogen = doc["hydrogen"]
    require(
        isinstance(hydrogen, dict) and set(hydrogen.keys()) == {"table_iv", "table_vi", "published_mean"},
        "unexpected hydrogen reduction keys",
    )
    require(
        hydrogen["published_mean"]["corrected_frequency_hz"] == "14204057517679/10000",
        "hydrogen published_mean frequency mismatch",
    )
    cesium = doc["cesium"]
    require(
        isinstance(cesium, dict) and set(cesium.keys()) == {"August2013", "typical_Table1"},
        "unexpected cesium campaign keys",
    )
    require(
        cesium["August2013"]["method"] != hydrogen["table_iv"]["method"],
        "H-maser and Cs-fountain apparatus methods must remain distinct",
    )
    phase = doc["phase"]
    require(phase.get("ratio") == "7/17", "phase ratio mismatch")
    require(phase.get("duration_seconds") == "17/18385263540", "phase duration_seconds mismatch")
    cs = doc["claim_status"]
    require(cs.get("independent_atomic_prediction") == "not_established", "independent_atomic_prediction hold lost")
    require(cs.get("complete_physical_uncertainty") == "missing_premise", "complete_physical_uncertainty hold lost")
    require(cs.get("nuclear_dynamics") == "not_implemented", "nuclear_dynamics hold lost")
    primary_sources = doc["primary_sources"]
    require(isinstance(primary_sources, dict) and len(primary_sources) == 2, "expected 2 primary_source receipts")
    return (
        {
            "hydrogen_reductions": len(hydrogen),
            "cesium_campaigns": len(cesium),
            "primary_source_receipts": len(primary_sources),
            "bound_data_files": 11,
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_experimental_comparison(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del pre_digests
    require(
        stdout.strip() == "experimental input comparison report verified",
        f"unexpected experimental_comparison stdout: {stdout.strip()!r}",
    )
    doc = _read_json_zero_float(
        repo_root / "manual/data/experimental_comparison/experimental_input_comparison.json"
    )
    require(isinstance(doc, dict), "experimental_input_comparison.json must be a dict")
    require(
        doc.get("schema") == "aod.m3.experimental-input-comparison.v1",
        "unexpected experimental_input_comparison schema",
    )
    qroutes = doc["quantity_routes"]
    require(
        isinstance(qroutes, dict) and set(qroutes.keys()) == _EXPERIMENTAL_QUANTITY_ROUTES,
        f"unexpected quantity_routes: {sorted(qroutes.keys()) if isinstance(qroutes, dict) else type(qroutes).__name__}",
    )
    freeze = doc["freeze"]
    require(freeze.get("target_changes_prediction") is False, "target_changes_prediction must be False")
    comp = freeze["comparison"]
    require(comp.get("independent_validation") is False, "independent_validation hold lost")
    require(comp.get("physical_discrepancy") == "unresolved", "physical_discrepancy hold lost")
    red_controls = doc["reduction_controls"]
    code_bindings = doc["code_bindings"]
    require(isinstance(red_controls, dict) and len(red_controls) == 5, "expected 5 reduction_controls")
    require(isinstance(code_bindings, dict) and len(code_bindings) == 9, "expected 9 code_bindings")
    return (
        {
            "quantity_routes": len(qroutes),
            "reduction_controls": len(red_controls),
            "code_bindings": len(code_bindings),
        },
        {"exact_match": True, "max_residual": "0"},
    )


def _validate_temporal_anchor(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del pre_digests
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "temporal_anchor stdout must be a JSON object")
    require(data.get("status") == "PASS_ANCHOR_REPLAY", f"unexpected temporal_anchor status: {data.get('status')!r}")
    gen_out = parse_exact_int(data.get("generated_outputs"), name="generated_outputs")
    require(gen_out == 6, f"expected 6 generated_outputs, got {gen_out}")
    require(data.get("scientific_source_members_verified") is True, "scientific_source_members_verified must be True")
    require(data.get("source_unchanged") is True, "source_unchanged must be True")
    require(
        data.get("original_controls") == {"A": "-5/29", "B": "-49/151"},
        f"unexpected original_controls: {data.get('original_controls')!r}",
    )

    doc = _read_json_zero_float(repo_root / "manual/data/temporal_anchor/report.json")
    require(isinstance(doc, dict), "temporal_anchor report.json must be a dict")
    require(doc.get("schema") == "aod.m3.anchor-report.v1", "unexpected temporal_anchor report schema")
    cases = doc["cases"]
    require(
        isinstance(cases, dict)
        and set(cases.keys()) == {"baseline", "second_support_pair", "compared_population", "reference_exposure"},
        "unexpected temporal_anchor cases",
    )
    replay_checks = parse_exact_int(doc["historical_replay"]["checks"], name="historical_replay.checks")
    require(replay_checks == 33, f"expected 33 historical replay checks, got {replay_checks}")
    require(doc.get("physical_Cs_observation_law") is None, "physical_Cs_observation_law hold lost")
    require(doc.get("physical_SI_prediction") is None, "physical_SI_prediction hold lost")

    members_doc = _read_json_zero_float(repo_root / "manual/data/temporal_anchor/source_members.json")
    require(isinstance(members_doc, dict) and len(members_doc["members"]) == 30, "expected 30 scientific_source_members")
    return (
        {
            "generated_outputs": gen_out,
            "anchor_cases": len(cases),
            "nested_replay_checks": replay_checks,
            "scientific_source_members": len(members_doc["members"]),
        },
        {"exact_match": True, "max_residual": "0", "original_controls": {"A": "-5/29", "B": "-49/151"}},
    )


def _validate_wavelet_si_alignment(
    repo_root: Path, stdout: str, pre_digests: dict[str, str]
) -> tuple[dict[str, int], dict[str, object]]:
    del repo_root, pre_digests
    data = loads_zero_float(stdout)
    require_no_floats(data)
    require(isinstance(data, dict), "wavelet_si_alignment stdout must be a JSON object")
    require(
        data.get("schema") == "aod.manual.wavelet-si-alignment.v2",
        f"unexpected wavelet_si_alignment schema: {data.get('schema')!r}",
    )
    require(data.get("status") == "PASS", f"unexpected wavelet_si_alignment status: {data.get('status')!r}")
    for group in _WAVELET_CHECK_GROUPS:
        val = data.get(group)
        require(isinstance(val, dict) and bool(val), f"missing or empty check group: {group}")

    p13 = data["P2-13"]
    require(parse_exact_int(p13.get("changed_csvs"), name="changed_csvs") == 0, "P2-13 changed_csvs must be 0")
    require(p13.get("tau_ring_diagnostic_1210") == "9/20", "P2-13 tau_ring_diagnostic_1210 mismatch")
    require(p13.get("rational_difference") == "1/100", "P2-13 rational_difference mismatch")
    require(
        p13.get("tau_ring_generator_status") == "UNRESOLVED_NOT_AUTHENTICATED_IN_REPO",
        "P2-13 tau_ring_generator_status hold lost",
    )
    require(
        parse_exact_int(p13.get("shedding_fixture_ticks"), name="shedding_fixture_ticks") == 90,
        "P2-13 shedding_fixture_ticks mismatch",
    )
    require(
        p13.get("shedding_certifies_native_reclosure_or_exo") is False,
        "P2-13 shedding_certifies_native_reclosure_or_exo hold lost",
    )

    p14 = data["P2-14"]
    frozen_cnt = parse_exact_int(p14.get("frozen_files_verified"), name="frozen_files_verified")
    eq_cnt = parse_exact_int(p14.get("phase1_equations_bound_in_manual"), name="phase1_equations_bound_in_manual")
    sec_cnt = parse_exact_int(p14.get("phase1_sections_bound_in_manual"), name="phase1_sections_bound_in_manual")
    require(frozen_cnt == 180, f"expected 180 frozen files verified, got {frozen_cnt}")
    require(eq_cnt == 10 and sec_cnt == 2, f"unexpected phase1 bindings: eq={eq_cnt}, sec={sec_cnt}")

    p15 = data["P2-15"]
    require(p15.get("v_hat_3") == "1/4", "P2-15 v_hat_3 mismatch")
    require(p15.get("parseval_exact") == "1/4", "P2-15 parseval_exact mismatch")
    return (
        {
            "check_groups": len(_WAVELET_CHECK_GROUPS),
            "p2_checks_covered": 15,
            "frozen_files_verified": frozen_cnt,
            "phase1_equations_bound": eq_cnt,
        },
        {"exact_match": True, "max_residual": "0", "p2_15_v_hat_3": "1/4"},
    )


_VALIDATORS = {
    "native_closure_wave": _validate_native_closure_wave,
    "awareness": _validate_awareness,
    "cell_measures": _validate_cell_measures,
    "mapping_error": _validate_mapping_error,
    "temporal_observation": _validate_temporal_observation,
    "temporal_metrology": _validate_temporal_metrology,
    "experimental_comparison": _validate_experimental_comparison,
    "temporal_anchor": _validate_temporal_anchor,
    "wavelet_si_alignment": _validate_wavelet_si_alignment,
}


_CROSS_ZLIB_ANCHOR_VERIFY_CODE: str = """\
import gzip
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "manual" / "scripts"))
import aod_temporal_anchor as a

folder = root / a.DATA
bound_files = [path for path in folder.rglob("*") if path.is_file()]
bound_files.extend(Path(module.__file__) for module in (a.n, a.m, a.t))
bound_files.append(Path(a.__file__))
before = {str(path): a.sha(path) for path in bound_files}

expected = a.products(root)
actual = {path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()}
sources = {
    "source/" + name
    for name in json.loads((folder / "source_members.json").read_text(encoding="utf-8"))["members"]
}
a.require(actual == set(expected) | sources | {"source_members.json"}, "anchor artifact inventory differs")

for name, value in sorted(expected.items()):
    persisted = (folder / name).read_bytes()
    if name.endswith(".json.gz"):
        a.require(
            gzip.decompress(persisted) == gzip.decompress(value),
            "persisted anchor decompressed payload differs: " + name,
        )
    else:
        a.require(persisted == value, "persisted anchor artifact differs: " + name)

after = {str(path): a.sha(path) for path in bound_files}
a.require(after == before, "anchor replay changed bound source or data")

print(
    json.dumps(
        {
            "status": "PASS_ANCHOR_REPLAY",
            "generated_outputs": len(expected),
            "scientific_source_members_verified": True,
            "full_archive_audit": "separate explicit operation",
            "original_controls": {"A": "-5/29", "B": "-49/151"},
            "source_unchanged": True,
        },
        sort_keys=True,
    )
)
"""


def _host_zlib_roundtrips_anchor_gz(repo_root: Path) -> bool:
    """Return True iff host ``gzip.compress`` reproduces the committed ``baseline.json.gz`` bitstream."""
    gz_path = repo_root / "manual" / "data" / "temporal_anchor" / "cases" / "baseline.json.gz"
    raw = gz_path.read_bytes()
    try:
        return gzip.compress(gzip.decompress(raw), mtime=0) == raw
    except (OSError, EOFError, zlib.error) as exc:
        raise ValueError(f"corrupt anchor gzip stream: {exc}") from exc


def _extract_error_line(text: str, *, last: bool, max_chars: int = 240) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    chosen = lines[-1] if last else lines[0]
    return chosen[:max_chars]


def run_tier1_sector(
    spec: SectorSpec,
    repo_root: Path,
    *,
    diagnostics_dir: Path | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, object]:
    """Execute one Tier-1 canonical driver via isolated read-only subprocess."""
    root = Path(repo_root).resolve()
    require(spec.sector_id in _VALIDATORS, f"unregistered Tier-1 sector: {spec.sector_id}")
    if diagnostics_dir is not None:
        validated_diag_dir = validate_runtime_output_path(
            diagnostics_dir,
            root,
            flag_name="--diagnostics-dir",
            expect_dir=True,
        )
        validate_runtime_output_path(
            validated_diag_dir / f"{spec.sector_id}.stdout.txt",
            root,
            flag_name="--diagnostics-dir child",
            expect_dir=False,
        )
        validate_runtime_output_path(
            validated_diag_dir / f"{spec.sector_id}.stderr.txt",
            root,
            flag_name="--diagnostics-dir child",
            expect_dir=False,
        )

    pre_digests = _hash_inputs(root, spec.input_paths)

    opt_flags = ["-O"] * sys.flags.optimize
    script_rel = spec.invocation[0]
    read_only_flags = list(spec.invocation[1:])
    if spec.sector_id == "temporal_anchor" and not _host_zlib_roundtrips_anchor_gz(root):
        argv = [sys.executable, "-B", *opt_flags, "-c", _CROSS_ZLIB_ANCHOR_VERIFY_CODE, str(root)]
    else:
        argv = [sys.executable, "-B", *opt_flags, str(root / script_rel), *read_only_flags]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    effective_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else (_ANCHOR_TIMEOUT_SECONDS if spec.sector_id == "temporal_anchor" else _DEFAULT_TIMEOUT_SECONDS)
    )

    proc = subprocess.run(
        argv,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=effective_timeout,
    )

    if diagnostics_dir is not None:
        validated_diag_dir = validate_runtime_output_path(
            diagnostics_dir,
            root,
            flag_name="--diagnostics-dir",
            expect_dir=True,
        )
        stdout_path = validated_diag_dir / f"{spec.sector_id}.stdout.txt"
        stderr_path = validated_diag_dir / f"{spec.sector_id}.stderr.txt"
        validate_runtime_output_path(
            stdout_path,
            root,
            flag_name="--diagnostics-dir child",
            expect_dir=False,
        )
        validate_runtime_output_path(
            stderr_path,
            root,
            flag_name="--diagnostics-dir child",
            expect_dir=False,
        )
        atomic_write_safe_text(
            stdout_path,
            proc.stdout,
            root,
            flag_name="--diagnostics-dir child",
        )
        atomic_write_safe_text(
            stderr_path,
            proc.stderr,
            root,
            flag_name="--diagnostics-dir child",
        )

    if proc.returncode != 0:
        tail = _extract_error_line(proc.stderr, last=True) or _extract_error_line(proc.stdout, last=True)
        rc_msg = (
            f"Tier-1 subprocess {spec.sector_id} exited with code {proc.returncode}: {tail}"
            if tail
            else f"Tier-1 subprocess {spec.sector_id} exited with code {proc.returncode}"
        )
        require(False, rc_msg)
    if proc.stderr != "":
        head = _extract_error_line(proc.stderr, last=False)
        stderr_msg = (
            f"Tier-1 subprocess {spec.sector_id} emitted unexpected stderr ({len(proc.stderr)} bytes): {head}"
            if head
            else f"Tier-1 subprocess {spec.sector_id} emitted unexpected stderr ({len(proc.stderr)} bytes)"
        )
        require(False, stderr_msg)

    post_digests = _hash_inputs(root, spec.input_paths)
    require(
        post_digests == pre_digests,
        f"Tier-1 subprocess {spec.sector_id} mutated bound read-only inputs",
    )

    verified_counts, residuals_summary = _VALIDATORS[spec.sector_id](root, proc.stdout, pre_digests)
    for req_key, min_val in spec.required_outputs:
        actual_val = parse_exact_int(verified_counts.get(req_key), name=f"{spec.sector_id}.{req_key}")
        require(
            actual_val >= min_val,
            f"vacuous output for {spec.sector_id}.{req_key}: {actual_val} < {min_val}",
        )

    return {
        "sector_id": spec.sector_id,
        "tier": spec.tier,
        "adapter_id": spec.adapter_id,
        "bound_source_operation": spec.bound_source_operation,
        "capability": spec.capability,
        "check_outcome": "PASS",
        "scientific_status": spec.scientific_status,
        "retained_holds": list(spec.retained_holds),
        "input_digests": pre_digests,
        "verified_counts": verified_counts,
        "exact_residuals_summary": residuals_summary,
        "error": None,
    }
