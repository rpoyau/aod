"""Pure-Python schema validators for canonical engine reports and S4 golden vectors.

Zero .json files are created under manual/engine/ per S2_SPEC.md packaging contract.
"""
from __future__ import annotations

import re

from manual.engine.numeric import require, require_exact_int
from manual.engine.policy import require_no_floats

ENGINE_VERSION: str = "0.1.0"
REPORT_SCHEMA: str = "aod.manual.engine.report.v1"
VECTOR_SCHEMA: str = "aod.s4.vector.v1"
BASE_COMMIT_BINDING: str = "cea71a76f26c08b603866e746867b3982da6c88e"

VALID_TIERS: frozenset[str] = frozenset(
    {
        "tier1_canonical_adapter",
        "tier2_exact_data_verifier",
        "tier3_provenance_guard",
    }
)

VALID_CAPABILITIES: frozenset[str] = frozenset(
    {
        "canonical_calculation",
        "declared_fixture_replay",
        "retained_data_conformance",
        "provenance_guard",
    }
)

VALID_OUTCOMES: frozenset[str] = frozenset({"PASS", "FAIL"})

VALID_SCIENTIFIC_STATUSES: frozenset[str] = frozenset(
    {
        "AUTHENTICATED_EXACT",
        "CONFORMANT_DECLARED_FIXTURE",
        "RETAINED_DATA_CONFORMANT",
        "UNRESOLVED_PROVENANCE_QUARANTINED",
    }
)

VALID_RUST_INT_TYPES: frozenset[str] = frozenset({"i32", "i64", "i128", "BigInt"})

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_ISO_TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_ABS_UNIX_PATH_RE = re.compile(
    r"(?:^/|(?<=[\s'\"(=:\[{,])/(?:(?:home|tmp|var|Users|root|opt|usr|etc|private|mnt|srv|proc|sys|workspace|github|app|runner|builds)(?:/|$)|[A-Za-z0-9._-]+/[A-Za-z0-9._-]+))"
)
_ABS_WIN_PATH_RE = re.compile(r"(?:^|[\s'\"(=:\[{,])[A-Za-z]:[\\/]")
_TEMP_MARKER_RE = re.compile(r"(?:pytest-of-|aod-anchor-scientific-replay-|/tmp/|\\Temp\\)")

FORBIDDEN_REPORT_KEYS: frozenset[str] = frozenset(
    {
        "timestamp",
        "created_at",
        "started_at",
        "finished_at",
        "duration",
        "duration_s",
        "elapsed",
        "elapsed_s",
        "wall_clock",
        "pid",
        "hostname",
        "python_executable",
        "stdout",
        "stderr",
        "temp_dir",
    }
)

_REPORT_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "schema",
        "engine_version",
        "base_commit_binding",
        "registry_digest",
        "sector_count",
        "data_coverage_audit",
        "sectors",
        "outcomes_summary",
        "scientific_status_summary",
        "zero_float_policy_audit",
    }
)

_REPORT_OPTIONAL_KEYS: frozenset[str] = frozenset({"vectors_verification"})

_SECTOR_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "sector_id",
        "tier",
        "adapter_id",
        "bound_source_operation",
        "capability",
        "check_outcome",
        "scientific_status",
        "retained_holds",
        "input_digests",
        "verified_counts",
        "exact_residuals_summary",
        "error",
    }
)

_VECTOR_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "case_id",
        "source_binding",
        "operation",
        "domain",
        "inputs",
        "expected_outcome",
        "evidence_role",
        "scientific_status",
        "oracle_basis",
        "integer_encoding",
    }
)


def _check_portable_strings(value: object, *, path: str = "$") -> None:
    """Recursively reject absolute paths, temp paths, timestamps, and forbidden volatile keys."""
    if isinstance(value, dict):
        for k, v in value.items():
            require(isinstance(k, str), f"non-string key at {path}: {k!r}")
            require(
                k not in FORBIDDEN_REPORT_KEYS,
                f"forbidden volatile report key {k!r} at {path}",
            )
            _check_portable_strings(k, path=f"{path}.<key:{k}>")
            _check_portable_strings(v, path=f"{path}.{k}")
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _check_portable_strings(item, path=f"{path}[{idx}]")
    elif isinstance(value, str):
        require(
            _ABS_WIN_PATH_RE.search(value) is None,
            f"absolute Windows path leaked in canonical report at {path}: {value!r}",
        )
        require(
            _ABS_UNIX_PATH_RE.search(value) is None,
            f"absolute Unix path leaked in canonical report at {path}: {value!r}",
        )
        require(
            _TEMP_MARKER_RE.search(value) is None,
            f"temporary directory marker leaked in canonical report at {path}: {value!r}",
        )
        require(
            _ISO_TIMESTAMP_RE.search(value) is None,
            f"timestamp leaked in canonical report at {path}: {value!r}",
        )


def validate_report(report_obj: object) -> None:
    """Validate canonical report structure, types, rollups, non-conflation, and portability."""
    require_no_floats(report_obj)
    require(isinstance(report_obj, dict), "report must be a JSON object")
    keys = set(report_obj.keys())
    missing = _REPORT_REQUIRED_KEYS - keys
    extra = keys - (_REPORT_REQUIRED_KEYS | _REPORT_OPTIONAL_KEYS)
    require(not missing, f"report missing required keys: {sorted(missing)}")
    require(not extra, f"report contains unexpected keys: {sorted(extra)}")

    require(report_obj["schema"] == REPORT_SCHEMA, f"unexpected report schema: {report_obj['schema']!r}")
    require(
        isinstance(report_obj["engine_version"], str) and bool(report_obj["engine_version"]),
        "engine_version must be a non-empty string",
    )
    require(
        isinstance(report_obj["base_commit_binding"], str)
        and _HEX40_RE.fullmatch(report_obj["base_commit_binding"]) is not None,
        "base_commit_binding must be a 40-char lowercase hex commit SHA",
    )
    require(
        isinstance(report_obj["registry_digest"], str)
        and _HEX64_RE.fullmatch(report_obj["registry_digest"]) is not None,
        "registry_digest must be a 64-char lowercase hex SHA-256",
    )

    sectors = report_obj["sectors"]
    require(isinstance(sectors, list), "sectors must be a list")
    sector_count = require_exact_int(report_obj["sector_count"], name="sector_count")
    require(sector_count == len(sectors), "sector_count must equal len(sectors)")

    cov = report_obj["data_coverage_audit"]
    require(isinstance(cov, dict), "data_coverage_audit must be a dict")
    require(cov.get("status") in {"PASS", "FAIL", "NOT_REQUESTED"}, "invalid data_coverage_audit status")
    if cov.get("status") == "PASS":
        require(require_exact_int(cov["manual_data_subdirs"], name="manual_data_subdirs") == 18, "expected 18 manual/data subdirs")
        require(require_exact_int(cov["manual_data_files"], name="manual_data_files") == 124, "expected 124 manual/data files")
        require(require_exact_int(cov["uncovered_files"], name="uncovered_files") == 0, "uncovered_files must be 0")

    seen_ids: set[str] = set()
    outcome_counts = {"PASS": 0, "FAIL": 0}
    sci_counts = {status: 0 for status in VALID_SCIENTIFIC_STATUSES}

    for idx, sec in enumerate(sectors):
        require(isinstance(sec, dict), f"sectors[{idx}] must be a dict")
        require(
            set(sec.keys()) == _SECTOR_REQUIRED_KEYS,
            f"sectors[{idx}] key mismatch: {sorted(sec.keys())}",
        )
        sid = sec["sector_id"]
        require(isinstance(sid, str) and bool(sid), f"sectors[{idx}].sector_id must be non-empty str")
        require(sid not in seen_ids, f"duplicate sector_id in report: {sid!r}")
        seen_ids.add(sid)

        require(sec["tier"] in VALID_TIERS, f"invalid tier for {sid}: {sec['tier']!r}")
        require(isinstance(sec["adapter_id"], str) and bool(sec["adapter_id"]), f"invalid adapter_id for {sid}")
        require(
            isinstance(sec["bound_source_operation"], str) and bool(sec["bound_source_operation"]),
            f"invalid bound_source_operation for {sid}",
        )
        require(sec["capability"] in VALID_CAPABILITIES, f"invalid capability for {sid}: {sec['capability']!r}")
        require(sec["check_outcome"] in VALID_OUTCOMES, f"invalid check_outcome for {sid}: {sec['check_outcome']!r}")
        require(
            sec["scientific_status"] in VALID_SCIENTIFIC_STATUSES,
            f"invalid scientific_status for {sid}: {sec['scientific_status']!r}",
        )

        if sid == "provenance_quarantine":
            require(
                sec["scientific_status"] == "UNRESOLVED_PROVENANCE_QUARANTINED",
                "provenance_quarantine must preserve UNRESOLVED_PROVENANCE_QUARANTINED status",
            )
            require(
                sec["capability"] == "provenance_guard",
                "provenance_quarantine must preserve provenance_guard capability",
            )

        holds = sec["retained_holds"]
        require(
            isinstance(holds, list) and all(isinstance(h, str) and bool(h) for h in holds),
            f"retained_holds for {sid} must be list of non-empty strings",
        )

        digests = sec["input_digests"]
        require(isinstance(digests, dict), f"input_digests for {sid} must be a dict")
        if sec["check_outcome"] == "PASS":
            require(bool(digests), f"passing sector {sid} must record non-empty input_digests")
        for rel, sha in digests.items():
            require(
                isinstance(rel, str) and bool(rel) and not rel.startswith("/") and ".." not in rel.split("/"),
                f"invalid repo-relative path in input_digests for {sid}: {rel!r}",
            )
            require(
                isinstance(sha, str) and _HEX64_RE.fullmatch(sha) is not None,
                f"invalid SHA-256 digest for {sid}:{rel}",
            )

        counts = sec["verified_counts"]
        require(isinstance(counts, dict), f"verified_counts for {sid} must be a dict")
        if sec["check_outcome"] == "PASS":
            require(bool(counts), f"passing sector {sid} must record non-empty verified_counts")
        for ck, cv in counts.items():
            require(isinstance(ck, str) and bool(ck), f"invalid count key for {sid}")
            require_exact_int(cv, name=f"{sid}.verified_counts.{ck}")

        require(
            isinstance(sec["exact_residuals_summary"], dict),
            f"exact_residuals_summary for {sid} must be a dict",
        )

        if sec["check_outcome"] == "PASS":
            require(sec["error"] is None, f"passing sector {sid} must have error=None")
            sci_counts[sec["scientific_status"]] += 1
        else:
            require(
                isinstance(sec["error"], str) and bool(sec["error"]),
                f"failing sector {sid} must record a non-empty error message",
            )
        outcome_counts[sec["check_outcome"]] += 1

    os_sum = report_obj["outcomes_summary"]
    require(isinstance(os_sum, dict), "outcomes_summary must be a dict")
    require(
        set(os_sum.keys()) == {"total_executed", "PASS", "FAIL"},
        f"unexpected outcomes_summary keys: {sorted(os_sum.keys())}",
    )
    require(
        require_exact_int(os_sum["total_executed"], name="total_executed") == len(sectors)
        and require_exact_int(os_sum["PASS"], name="PASS") == outcome_counts["PASS"]
        and require_exact_int(os_sum["FAIL"], name="FAIL") == outcome_counts["FAIL"],
        "outcomes_summary does not match sector records",
    )

    ss_sum = report_obj["scientific_status_summary"]
    require(isinstance(ss_sum, dict), "scientific_status_summary must be a dict")
    require(
        set(ss_sum.keys()) == VALID_SCIENTIFIC_STATUSES,
        f"unexpected scientific_status_summary keys: {sorted(ss_sum.keys())}",
    )
    for st in VALID_SCIENTIFIC_STATUSES:
        require(
            require_exact_int(ss_sum[st], name=f"scientific_status_summary.{st}") == sci_counts[st],
            f"scientific_status_summary.{st} mismatch",
        )

    zf_audit = report_obj["zero_float_policy_audit"]
    require(isinstance(zf_audit, dict), "zero_float_policy_audit must be a dict")
    require(
        zf_audit.get("status") in {"PASS", "FAIL", "NOT_REQUESTED"},
        f"invalid zero_float_policy_audit status: {zf_audit.get('status')!r}",
    )
    if zf_audit.get("status") == "PASS":
        require(
            require_exact_int(zf_audit.get("violation_count"), name="zero_float_policy_audit.violation_count") == 0,
            "PASS zero_float_policy_audit requires violation_count == 0",
        )
        require(
            isinstance(zf_audit.get("violations"), list) and len(zf_audit["violations"]) == 0,
            "PASS zero_float_policy_audit requires empty violations list",
        )

    if "vectors_verification" in report_obj and report_obj["vectors_verification"] is not None:
        vv = report_obj["vectors_verification"]
        require(isinstance(vv, dict), "vectors_verification must be a dict")
        require(vv.get("status") in {"PASS", "FAIL"}, "invalid vectors_verification status")
        rc_cnt = require_exact_int(vv["rational_core_count"], name="rational_core_count")
        sd_cnt = require_exact_int(vv["symbolic_and_display_count"], name="symbolic_and_display_count")
        tot_cnt = require_exact_int(vv["total_vectors"], name="total_vectors")
        pass_cnt = require_exact_int(vv["passed_vectors"], name="passed_vectors")
        fail_cnt = require_exact_int(vv["failed_vectors"], name="failed_vectors")
        require(tot_cnt == rc_cnt + sd_cnt, "total_vectors must equal rational_core + symbolic_and_display")
        require(tot_cnt == pass_cnt + fail_cnt, "total_vectors must equal passed + failed")
        if vv.get("status") == "PASS":
            require(
                fail_cnt == 0 and tot_cnt > 0 and pass_cnt == tot_cnt,
                "PASS vectors_verification requires failed_vectors == 0 and total_vectors > 0",
            )
        fdig = vv.get("file_digests")
        require(isinstance(fdig, dict) and bool(fdig), "vectors_verification.file_digests required")
        for rel, sha in fdig.items():
            require(isinstance(rel, str) and not rel.startswith("/"), f"invalid vector path {rel!r}")
            require(isinstance(sha, str) and _HEX64_RE.fullmatch(sha) is not None, f"invalid vector sha for {rel}")

    _check_portable_strings(report_obj)


def validate_vector_record(record: object) -> None:
    """Validate one JSONL golden vector record against ``aod.s4.vector.v1``."""
    require_no_floats(record)
    require(isinstance(record, dict), "vector record must be a JSON object")
    missing = _VECTOR_REQUIRED_KEYS - set(record.keys())
    extra = set(record.keys()) - _VECTOR_REQUIRED_KEYS
    require(not missing, f"vector record missing keys: {sorted(missing)}")
    require(not extra, f"vector record has unexpected keys: {sorted(extra)}")
    require(
        record["schema_version"] == VECTOR_SCHEMA,
        f"unexpected vector schema_version: {record['schema_version']!r}",
    )
    for field in ("case_id", "source_binding", "operation", "domain", "evidence_role", "oracle_basis"):
        require(isinstance(record[field], str) and bool(record[field]), f"vector {field} must be non-empty str")
    require(
        record["oracle_basis"] != "candidate_snapshot",
        "circular candidate_snapshot oracle_basis is forbidden",
    )
    require(
        record["scientific_status"] in VALID_SCIENTIFIC_STATUSES,
        f"invalid vector scientific_status: {record['scientific_status']!r}",
    )
    require(isinstance(record["inputs"], dict), "vector inputs must be a dict")
    exp = record["expected_outcome"]
    require(isinstance(exp, dict) and exp.get("status") in {"OK", "REJECT"}, "invalid expected_outcome")
    if exp["status"] == "OK":
        require("exact_value" in exp, "OK expected_outcome requires exact_value")
    else:
        require(
            isinstance(exp.get("expected_error_class"), str) and bool(exp["expected_error_class"]),
            "REJECT expected_outcome requires expected_error_class",
        )
        require(
            isinstance(exp.get("expected_status"), str) and bool(exp["expected_status"]),
            "REJECT expected_outcome requires expected_status",
        )
    enc = record["integer_encoding"]
    require(isinstance(enc, dict), "integer_encoding must be a dict")
    require(
        enc.get("rust_min_int_type") in VALID_RUST_INT_TYPES,
        f"invalid rust_min_int_type: {enc.get('rust_min_int_type')!r}",
    )
    digits = require_exact_int(enc.get("max_abs_integer_digits"), name="max_abs_integer_digits")
    require(digits >= 1, "max_abs_integer_digits must be >= 1")
    require(
        isinstance(enc.get("overflow_note"), str) and bool(enc["overflow_note"]),
        "integer_encoding.overflow_note must be non-empty str",
    )
