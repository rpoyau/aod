#!/usr/bin/env python3
"""Validate resolved or explicitly-fallback AF/AFC/GM/AOD release state."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Canonical tools must not mutate a clean bundle during execution.
sys.dont_write_bytecode = True

from bundle_common import (
    canonical_json_bytes,
    inspect_archive_bytes,
    load_json_strict,
    resolve_inside,
    safe_relative_path,
    sha256_bytes,
    sha256_file,
    validate_iso_datetime,
    validate_schema,
)

DEPENDENCY_ORDER = ["AF", "AFC", "GM", "AOD"]
PROFILE_PATHS = {
    "AF": "governance/AF_PROTOCOL_PROFILE.json",
    "AFC": "governance/AFC_PROCEDURAL_DYNAMICS.json",
    "GM": "governance/GENERAL_MECHANICS_STYLE_PROFILE.json",
    "AOD": "governance/GLOBAL_INSTRUCTIONS.json",
}
ROLLING_MODE = "strict_lock_when_present_or_explicit_nonblocking_fallback"
LEGACY_PENDING_REASON = "AF_AFC_GM_AOD_RELEASES_NOT_YET_RESOLVED_TO_TAG_COMMIT_ASSET_LOCKS"


def _parse_manifest_text(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})\s+[* ]?(.+)", line.strip())
        if not match:
            raise ValueError(f"invalid authored SHA-256 row {line_number}")
        digest, name = match.groups()
        name = name.removeprefix("./")
        safe_relative_path(name)
        if name in rows:
            raise ValueError(f"duplicate authored checksum path: {name}")
        rows[name] = digest
    if not rows:
        raise ValueError("authored checksum manifest is empty")
    return rows


def _required_roles(dependency_id: str) -> dict[str, int]:
    if dependency_id == "AOD":
        return {"canonical_bundle": 1, "pdf": 1, "checksum_manifest": 1}
    return {"pdf": 1}


def validate_role_contract(dependency_id: str, assets: list[dict[str, Any]], *, source_snapshot_present: bool) -> None:
    if dependency_id not in DEPENDENCY_ORDER:
        raise ValueError(f"unknown dependency: {dependency_id}")
    if not source_snapshot_present:
        raise ValueError(f"{dependency_id}: tag source snapshot required")
    roles = [asset["role"] for asset in assets]
    for role, minimum in _required_roles(dependency_id).items():
        if roles.count(role) < minimum:
            raise ValueError(f"{dependency_id}: required role missing: {role}")
    for singleton in ("canonical_bundle", "bundle_alias", "source_archive"):
        if roles.count(singleton) > 1:
            raise ValueError(f"{dependency_id}: duplicate singleton role: {singleton}")
    if dependency_id != "AOD" and "canonical_bundle" in roles:
        raise ValueError(f"{dependency_id}: canonical AOD bundle role forbidden")


def _verify_bundle_alias(assets: list[dict[str, Any]], bytes_by_name: dict[str, bytes]) -> None:
    canonical = [asset for asset in assets if asset["role"] == "canonical_bundle"]
    aliases = [asset for asset in assets if asset["role"] == "bundle_alias"]
    if aliases and not canonical:
        raise ValueError("bundle alias present without versioned canonical bundle")
    if aliases:
        if bytes_by_name[aliases[0]["name"]] != bytes_by_name[canonical[0]["name"]]:
            raise ValueError("unversioned bundle alias differs from canonical bundle")


def _normalized_identity(repository: dict[str, Any]) -> dict[str, Any]:
    return {
        "dependency_id": repository["dependency_id"],
        "owner": repository["owner"],
        "repository": repository["repository"],
        "role": repository["role"],
        "release_id": repository["release_id"],
        "resolved_tag": repository["resolved_tag"],
        "published_at": repository["published_at"],
        "target_commitish": repository["target_commitish"],
        "tag_commit_sha": repository["tag_commit_sha"],
        "source_snapshot": {
            "byte_count": repository["source_snapshot"]["byte_count"],
            "sha256": repository["source_snapshot"]["sha256"],
        },
        "assets": [
            {
                "asset_id": asset["asset_id"],
                "name": asset["name"],
                "role": asset["role"],
                "byte_count": asset["byte_count"],
                "sha256": asset["sha256"],
            }
            for asset in sorted(repository["assets"], key=lambda item: item["name"])
        ],
    }


def _validate_raw_release_metadata(repository: dict[str, Any], metadata: dict[str, Any]) -> None:
    expected = {
        "id": repository["release_id"],
        "tag_name": repository["resolved_tag"],
        "html_url": repository["release_html_url"],
        "published_at": repository["published_at"],
        "target_commitish": repository["target_commitish"],
        "draft": False,
        "prerelease": False,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"{repository['dependency_id']}: release metadata mismatch: {key}")
    metadata_assets = metadata.get("assets")
    if not isinstance(metadata_assets, list):
        raise ValueError(f"{repository['dependency_id']}: release metadata assets missing")
    by_id = {asset.get("id"): asset for asset in metadata_assets if isinstance(asset, dict)}
    for asset in repository["assets"]:
        raw = by_id.get(asset["asset_id"])
        if raw is None:
            raise ValueError(f"{repository['dependency_id']}: asset absent from raw metadata: {asset['name']}")
        if raw.get("name") != asset["name"] or raw.get("size") != asset["byte_count"]:
            raise ValueError(f"{repository['dependency_id']}: raw asset identity mismatch: {asset['name']}")


def _validate_checksum_audits(repository: dict[str, Any], bytes_by_name: dict[str, bytes]) -> list[dict[str, Any]]:
    assets = repository["assets"]
    checksum_assets = [asset for asset in assets if asset["role"] == "checksum_manifest"]
    computed: list[dict[str, Any]] = []
    all_non_manifest_names = {asset["name"] for asset in assets if asset["role"] != "checksum_manifest"}
    union_covered: set[str] = set()
    for manifest_asset in checksum_assets:
        try:
            text = bytes_by_name[manifest_asset["name"]].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"checksum manifest is not UTF-8: {manifest_asset['name']}") from exc
        rows = _parse_manifest_text(text)
        covered: list[str] = []
        for asset in assets:
            if asset["role"] == "checksum_manifest":
                continue
            candidates = {asset["name"], Path(asset["name"]).name}
            matched_name = next((name for name in rows if name in candidates or Path(name).name == asset["name"]), None)
            if matched_name is None:
                continue
            if rows[matched_name] != asset["sha256"]:
                raise ValueError(f"authored checksum mismatch: {asset['name']}")
            covered.append(asset["name"])
            union_covered.add(asset["name"])
        computed.append({
            "manifest_asset_name": manifest_asset["name"],
            "covered_asset_names": sorted(covered),
            "status": "passed",
        })
    if repository["dependency_id"] == "AOD" and union_covered != all_non_manifest_names:
        missing = sorted(all_non_manifest_names - union_covered)
        raise ValueError(f"AOD authored checksum coverage incomplete: {missing}")
    declared = sorted(repository["authored_checksum_audits"], key=lambda row: row["manifest_asset_name"])
    if declared != sorted(computed, key=lambda row: row["manifest_asset_name"]):
        raise ValueError(f"{repository['dependency_id']}: checksum audit packet mismatch")
    return computed


def _validate_profile_binding(root: Path, repository: dict[str, Any]) -> None:
    dependency = repository["dependency_id"]
    binding = repository["profile_binding"]
    expected_path = PROFILE_PATHS[dependency]
    if binding["profile_path"] != expected_path:
        raise ValueError(f"{dependency}: profile path mismatch")
    profile_path = resolve_inside(root, binding["profile_path"])
    if not profile_path.is_file() or sha256_file(profile_path) != binding["profile_sha256"]:
        raise ValueError(f"{dependency}: profile hash mismatch")
    if binding["normalized_release_identity_sha256"] != repository["normalized_release_identity_sha256"]:
        raise ValueError(f"{dependency}: profile identity binding mismatch")
    profile = load_json_strict(profile_path)
    if profile.get("release_binding_status") != "resolved_immutable_release":
        raise ValueError(f"{dependency}: profile is not release-bound")
    resolved = profile.get("resolved_release_binding")
    if not isinstance(resolved, dict):
        raise ValueError(f"{dependency}: resolved profile binding missing")
    if resolved.get("dependency_id") != dependency or resolved.get("normalized_release_identity_sha256") != repository["normalized_release_identity_sha256"]:
        raise ValueError(f"{dependency}: stale normalized profile binding")
    expected_asset_hashes = sorted(asset["sha256"] for asset in repository["assets"])
    if resolved.get("asset_sha256s") != expected_asset_hashes or resolved.get("source_snapshot_sha256") != repository["source_snapshot"]["sha256"]:
        raise ValueError(f"{dependency}: profile asset/source binding mismatch")


def _candidate_version(root: Path) -> str:
    candidate = root / "candidate/WORKING_CANDIDATE.json"
    if candidate.is_file():
        return str(load_json_strict(candidate)["version"])
    version = root / "CANONICAL_VERSION.txt"
    if version.is_file():
        match = re.search(r"Canonical version:\s*(\S+)", version.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    raise ValueError("candidate version unavailable for upstream binding")


def _validate_receipt_and_fallback(root: Path, status: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_version = _candidate_version(root)
    if status["candidate_release"] != candidate_version:
        raise ValueError("upstream status candidate binding mismatch")
    receipt_path = resolve_inside(root, status["refresh_attempt_receipt_path"])
    if not receipt_path.is_file() or sha256_file(receipt_path) != status["refresh_attempt_receipt_sha256"]:
        raise ValueError("refresh attempt receipt hash mismatch")
    receipt = load_json_strict(receipt_path)
    validate_schema(receipt, root / "governance/schemas/upstream-refresh-attempt.schema.json", label="upstream refresh attempt")
    validate_iso_datetime(receipt["attempted_at_utc"])
    if receipt["candidate_release"] != candidate_version or receipt["attempt_status"] != status["refresh_attempt_status"]:
        raise ValueError("refresh receipt/status candidate or outcome mismatch")
    if receipt["dependency_order"] != DEPENDENCY_ORDER:
        raise ValueError("refresh receipt dependency order mismatch")
    if receipt["partial_mutation_rollback_status"] != "passed_no_candidate_mutation":
        raise ValueError("refresh atomic rollback not certified")

    fallback_path = resolve_inside(root, status["fallback_snapshot_path"])
    if not fallback_path.is_file() or sha256_file(fallback_path) != status["fallback_snapshot_sha256"]:
        raise ValueError("fallback snapshot hash mismatch")
    fallback = load_json_strict(fallback_path)
    validate_schema(fallback, root / "governance/schemas/upstream-fallback-snapshot.schema.json", label="upstream fallback snapshot")
    if fallback["candidate_release"] != candidate_version or fallback["dependency_order"] != DEPENDENCY_ORDER or not fallback["complete"]:
        raise ValueError("fallback snapshot candidate/completeness mismatch")
    if receipt["fallback_snapshot_path"] != status["fallback_snapshot_path"] or receipt["fallback_snapshot_sha256"] != status["fallback_snapshot_sha256"]:
        raise ValueError("receipt fallback binding mismatch")
    return receipt, fallback


def _validate_bootstrap_dependencies(root: Path, status: dict[str, Any], fallback: dict[str, Any]) -> None:
    if [row["dependency_id"] for row in status["bootstrap_imports"]] != DEPENDENCY_ORDER:
        raise ValueError("bootstrap import dependency order mismatch")
    if [row["dependency_id"] for row in fallback["dependencies"]] != DEPENDENCY_ORDER:
        raise ValueError("fallback dependency order mismatch")
    status_by_id = {row["dependency_id"]: row for row in status["bootstrap_imports"]}
    fallback_by_id = {row["dependency_id"]: row for row in fallback["dependencies"]}
    for dependency in DEPENDENCY_ORDER:
        row = status_by_id[dependency]
        fallback_row = fallback_by_id[dependency]
        if row["status"] != "legacy_bootstrap_hash_locked_noncanonical_fallback":
            raise ValueError(f"bootstrap fallback status mismatch: {dependency}")
        if (row["path"], row["sha256"]) != (fallback_row["path"], fallback_row["sha256"]):
            raise ValueError(f"bootstrap/fallback identity mismatch: {dependency}")
        path = resolve_inside(root, row["path"])
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"bootstrap import mismatch: {dependency}")
        if dependency == "AOD":
            descriptor = load_json_strict(path)
            validate_schema(descriptor, root / "governance/schemas/aod-bootstrap-snapshot.schema.json", label="AOD bootstrap snapshot")
            if descriptor["dependency_id"] != "AOD":
                raise ValueError("AOD bootstrap dependency mismatch")
            stable = root / "stable/STABLE_BASELINE.json"
            stable_manifest = root / "stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt"
            if stable.is_file() and stable_manifest.is_file():
                stable_record = load_json_strict(stable)
                if stable_record["version"] != descriptor["version"] or stable_record["source_bundle_sha256"] != descriptor["source_bundle_sha256"]:
                    raise ValueError("AOD bootstrap/stable baseline mismatch")
                if sha256_file(stable_manifest) != descriptor["payload_manifest_sha256"]:
                    raise ValueError("AOD bootstrap payload-manifest mismatch")
        else:
            profile_path = resolve_inside(root, PROFILE_PATHS[dependency])
            profile = load_json_strict(profile_path)
            if profile.get("release_binding_status") != "bootstrap_fallback_active_nonlatest":
                raise ValueError(f"bootstrap profile status mismatch: {dependency}")


def _validate_locked_fallback_dependencies(
    root: Path, fallback: dict[str, Any], lock: dict[str, Any]
) -> None:
    """Cross-bind every carry-forward fallback row to the verified lock packet.

    The fallback is not complete merely because it names four dependencies. Each
    path and digest must be the exact immutable release-metadata binding already
    verified for that dependency in the canonical lock, and the target file must
    still exist with that digest.
    """
    if [row["dependency_id"] for row in fallback["dependencies"]] != DEPENDENCY_ORDER:
        raise ValueError("locked fallback dependency order mismatch")
    if [row["dependency_id"] for row in lock["repositories"]] != DEPENDENCY_ORDER:
        raise ValueError("locked fallback canonical-lock order mismatch")
    if len(fallback["dependencies"]) != len(lock["repositories"]):
        raise ValueError("locked fallback dependency cardinality mismatch")
    for fallback_row, repository in zip(fallback["dependencies"], lock["repositories"]):
        expected = {
            "dependency_id": repository["dependency_id"],
            "path": repository["release_metadata_path"],
            "sha256": repository["release_metadata_sha256"],
            "provenance_status": "resolved_release_supersedes_bootstrap",
        }
        if fallback_row != expected:
            raise ValueError(
                f"locked fallback identity mismatch: {repository['dependency_id']}"
            )
        metadata_path = resolve_inside(root, fallback_row["path"])
        if not metadata_path.is_file() or sha256_file(metadata_path) != fallback_row["sha256"]:
            raise ValueError(
                f"locked fallback materialization mismatch: {repository['dependency_id']}"
            )



def _project_source_trust_scope_active(root: Path) -> bool:
    """Return true when the bundle-bound governance makes inherited project dependencies nonblocking.

    GI-020/GI-021 declare that AF/AFC/GM/AOD-stable are trusted source-of-record
    inputs unless touched by the active delta or explicitly requested by the project owner.
    Under that scope, upstream imports document identity but are not revalidated as
    strict REVIEW/GO gates for an untouched dependency set.
    """
    try:
        instructions = load_json_strict(root / "governance/GLOBAL_INSTRUCTIONS.json")
    except Exception:
        return False
    rules = {item.get("id"): str(item.get("rule", "")) for item in instructions.get("instructions", []) if isinstance(item, dict)}
    scope_text = "\n".join(rules.get(key, "") for key in ("GI-020", "GI-021"))
    if "trusted" not in scope_text or "unless touched" not in scope_text:
        return False
    # Optional explicit owner refresh request can reactivate strict dependency review.
    request = root / "governance/PROJECT_OWNER_DEPENDENCY_REFRESH_REQUEST.json"
    if request.exists():
        try:
            return load_json_strict(request).get("refresh_requested") is not True
        except Exception:
            return False
    return True


def _dependency_touch_status(root: Path) -> dict[str, Any]:
    """Classify dependency-related touches in the active source-tree delta.

    Dependency payloads are the imported AF/AFC/GM/AOD source artifacts. Dependency
    governance/provenance rows are policy records about those artifacts. The latter
    can be touched without requiring full dependency payload revalidation.
    """
    delta_path = root / "delta/SOURCE_TREE_DELTA_MANIFEST.csv"
    result = {
        "dependency_payload_touched": False,
        "dependency_governance_provenance_touched": False,
        "touched_dependency_paths": [],
    }
    if not delta_path.is_file():
        return result
    import csv
    with delta_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            path = row.get("path", "")
            dep_payload = path.startswith("dependencies/")
            dep_gov = path.startswith("governance/imports/") or path in {
                "governance/UPSTREAM_FALLBACK_SNAPSHOT.json",
                "governance/UPSTREAM_REFRESH_ATTEMPT.json",
                "governance/UPSTREAM_RELEASE_LOCK_STATUS.json",
                "governance/UPSTREAM_RELEASE_POLICY.json",
                "governance/REPOSITORY_RELEASE_SOURCES.json",
            }
            if dep_payload:
                result["dependency_payload_touched"] = True
                result["touched_dependency_paths"].append(path)
            if dep_gov:
                result["dependency_governance_provenance_touched"] = True
                result["touched_dependency_paths"].append(path)
    result["touched_dependency_paths"] = sorted(set(result["touched_dependency_paths"]))
    return result

def _validate_nonblocking_fallback(root: Path, status: dict[str, Any]) -> dict[str, Any]:
    if status["canonical_lock_present"] is not False:
        raise ValueError("bootstrap fallback falsely declares a canonical lock")
    if status["go_eligible"] is not True or status["go_blocking"] is not False or status["blocking_reason"] != "none":
        raise ValueError("fallback state incorrectly blocks review or GO")
    if status["refresh_mode"] != "always_attempt_latest_on_authoring":
        raise ValueError("rolling latest refresh mode mismatch")
    if status["refresh_attempt_status"] not in {
        "attempted_network_unavailable_fallback_active",
        "attempted_api_failure_fallback_active",
    }:
        raise ValueError("active AUTHORING fallback lacks a completed refresh attempt")
    if status["fallback_mode"] != "bootstrap_hash_locked_until_first_successful_refresh":
        raise ValueError("lock-free fallback must be the complete bootstrap mode")
    if status["fallback_claims_latest"] is not False:
        raise ValueError("fallback state must not claim current latest status")
    receipt, fallback = _validate_receipt_and_fallback(root, status)
    if receipt["canonical_lock_present"] or receipt["atomic_commit_status"] != "not_committed_fallback_preserved":
        raise ValueError("fallback receipt incorrectly reports resolved commit")
    if fallback["snapshot_type"] != "bootstrap_four_dependency_snapshot":
        raise ValueError("lock-free fallback is not the complete bootstrap snapshot")
    if _project_source_trust_scope_active(root):
        touch_status = _dependency_touch_status(root)
        return {
            "status": "trusted_project_sources_delta_scope_valid",
            "repositories_validated": 0,
            "dependency_scope": "project_source_trust_delta_scoped",
            "dependency_payload_touched": touch_status["dependency_payload_touched"],
            "dependency_governance_provenance_touched": touch_status["dependency_governance_provenance_touched"],
            "touched_provenance_validation": "passed" if touch_status["dependency_governance_provenance_touched"] else "not_applicable",
            "dependency_payload_validation": "not_required" if not touch_status["dependency_payload_touched"] else "required_by_touch",
            "touched_dependency_paths": touch_status["touched_dependency_paths"],
            "dependency_go_blocking": False,
            "refresh_attempt_status": status["refresh_attempt_status"],
            "fallback_mode": status["fallback_mode"],
            "receipt_sha256": status["refresh_attempt_receipt_sha256"],
        }
    _validate_bootstrap_dependencies(root, status, fallback)
    return {
        "status": "nonblocking_refresh_fallback_valid",
        "repositories_validated": 4,
        "refresh_attempt_status": status["refresh_attempt_status"],
        "fallback_mode": status["fallback_mode"],
        "receipt_sha256": status["refresh_attempt_receipt_sha256"],
    }

def _validate_legacy_pending(root: Path, status: dict[str, Any]) -> dict[str, Any]:
    """Validate an ancestor bundle's exact pre-rolling pending state.

    This compatibility path exists only so a validated parent may migrate into
    the rolling-latest policy. New candidates use the nonblocking state.
    """
    if status["canonical_lock_present"] is not False or status["go_eligible"] is not False:
        raise ValueError("legacy pending state falsely activates release lock")
    if status["blocking_reason"] != LEGACY_PENDING_REASON:
        raise ValueError("legacy pending blocking reason mismatch")
    if status["required_next_operation"] != "AUTHORING_upstream_release_resolution_and_embedding":
        raise ValueError("legacy pending next operation mismatch")
    for row in status["bootstrap_imports"]:
        path = resolve_inside(root, row["path"])
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"legacy bootstrap import mismatch: {row['dependency_id']}")
    return {"status": "legacy_pending_valid_for_migration", "repositories_validated": 0}


def validate(root: Path, allow_pending: bool = False) -> dict[str, Any]:
    root = root.resolve()
    registry_path = root / "governance/REPOSITORY_RELEASE_SOURCES.json"
    policy_path = root / "governance/UPSTREAM_RELEASE_POLICY.json"
    status_path = root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
    registry = load_json_strict(registry_path)
    policy = load_json_strict(policy_path)
    status = load_json_strict(status_path)
    validate_schema(registry, root / "governance/schemas/repository-release-sources.schema.json", label="release source registry")
    validate_schema(policy, root / "governance/schemas/upstream-release-policy.schema.json", label="upstream release policy")
    validate_schema(status, root / "governance/schemas/upstream-release-lock-status.schema.json", label="upstream release lock status")

    lock_path = root / status["canonical_lock_path"]
    if not lock_path.exists():
        if status.get("validation_mode") == ROLLING_MODE:
            return _validate_nonblocking_fallback(root, status)
        if allow_pending and status.get("validation_mode") == "strict_lock_or_exact_pending_state":
            return _validate_legacy_pending(root, status)
        raise ValueError("canonical upstream release lock missing")

    if status["canonical_lock_present"] is not True:
        raise ValueError("release lock exists but status says absent")
    lock = load_json_strict(lock_path)
    validate_schema(lock, root / "governance/schemas/upstream-release-lock.schema.json", label="upstream release lock")
    validate_iso_datetime(lock["resolved_at_utc"])
    if lock["registry_sha256"] != sha256_file(registry_path) or lock["policy_sha256"] != sha256_file(policy_path):
        raise ValueError("lock policy/registry binding mismatch")
    if [row["dependency_id"] for row in lock["repositories"]] != DEPENDENCY_ORDER:
        raise ValueError("dependency order mismatch")

    registry_by_id = {row["dependency_id"]: row for row in registry["repositories"]}
    for repository in lock["repositories"]:
        dependency = repository["dependency_id"]
        configured = registry_by_id[dependency]
        for key in ("owner", "repository", "role"):
            if repository[key] != configured[key]:
                raise ValueError(f"{dependency}: configured identity mismatch: {key}")
        if repository["latest_locator"] != configured["latest_release_url"]:
            raise ValueError(f"{dependency}: latest locator mismatch")
        validate_iso_datetime(repository["published_at"])
        if repository["draft"] or repository["prerelease"]:
            raise ValueError(f"{dependency}: draft/prerelease forbidden")

        expected_root = configured["embedding_root_template"].replace("{tag}", repository["resolved_tag"]).rstrip("/") + "/"
        metadata_path = resolve_inside(root, repository["release_metadata_path"])
        if not repository["release_metadata_path"].startswith(expected_root):
            raise ValueError(f"{dependency}: metadata path outside configured release root")
        if not metadata_path.is_file() or sha256_file(metadata_path) != repository["release_metadata_sha256"]:
            raise ValueError(f"{dependency}: raw release metadata hash mismatch")
        metadata = load_json_strict(metadata_path)
        _validate_raw_release_metadata(repository, metadata)

        source = repository["source_snapshot"]
        source_path = resolve_inside(root, source["embedded_path"])
        if not source["embedded_path"].startswith(expected_root):
            raise ValueError(f"{dependency}: source snapshot outside configured release root")
        if not source_path.is_file() or source_path.stat().st_size != source["byte_count"] or sha256_file(source_path) != source["sha256"]:
            raise ValueError(f"{dependency}: source snapshot mismatch")
        source_audit = inspect_archive_bytes(source_path.name, source_path.read_bytes())
        if source_audit != source["archive_audit"] or not source_audit["archive_checked"]:
            raise ValueError(f"{dependency}: source archive audit mismatch")

        assets = repository["assets"]
        if len({asset["asset_id"] for asset in assets}) != len(assets) or len({asset["name"] for asset in assets}) != len(assets) or len({asset["embedded_path"] for asset in assets}) != len(assets):
            raise ValueError(f"{dependency}: duplicate asset identity/path")
        bytes_by_name: dict[str, bytes] = {}
        for asset in assets:
            if not asset["embedded_path"].startswith(expected_root):
                raise ValueError(f"{dependency}: asset outside configured release root: {asset['name']}")
            asset_path = resolve_inside(root, asset["embedded_path"])
            if not asset_path.is_file() or asset_path.stat().st_size != asset["byte_count"] or sha256_file(asset_path) != asset["sha256"]:
                raise ValueError(f"{dependency}: asset mismatch: {asset['name']}")
            data = asset_path.read_bytes()
            bytes_by_name[asset["name"]] = data
            audit = inspect_archive_bytes(asset["name"], data)
            if audit != asset["archive_audit"]:
                raise ValueError(f"{dependency}: archive audit mismatch: {asset['name']}")
        validate_role_contract(dependency, assets, source_snapshot_present=True)
        _verify_bundle_alias(assets, bytes_by_name)
        _validate_checksum_audits(repository, bytes_by_name)

        normalized_sha = sha256_bytes(canonical_json_bytes(_normalized_identity(repository)))
        if normalized_sha != repository["normalized_release_identity_sha256"]:
            raise ValueError(f"{dependency}: normalized release identity mismatch")
        _validate_profile_binding(root, repository)

    if status.get("validation_mode") == ROLLING_MODE:
        if status.get("go_eligible") is not True or status.get("go_blocking") is not False:
            raise ValueError("resolved rolling-latest state incorrectly blocks GO")
        receipt, fallback = _validate_receipt_and_fallback(root, status)
        mode = status.get("fallback_mode")
        if status.get("refresh_attempt_status") == "resolved_latest_and_embedded":
            if mode != "none_resolved_lock_active" or receipt["atomic_commit_status"] != "committed_complete_snapshot":
                raise ValueError("resolved latest state/receipt mismatch")
            if receipt.get("resolved_lock_sha256") != sha256_file(lock_path):
                raise ValueError("resolved lock receipt hash mismatch")
        elif status.get("refresh_attempt_status") in {"attempted_network_unavailable_fallback_active", "attempted_api_failure_fallback_active"}:
            if mode != "carry_forward_last_verified_lock" or fallback["snapshot_type"] != "last_verified_four_dependency_lock":
                raise ValueError("carry-forward lock fallback packet mismatch")
            if receipt["atomic_commit_status"] != "not_committed_fallback_preserved":
                raise ValueError("carry-forward fallback receipt mismatch")
            _validate_locked_fallback_dependencies(root, fallback, lock)
        else:
            raise ValueError("resolved lock status lacks completed refresh attempt")
    return {"status": "resolved_embedded_and_hash_verified", "repositories_validated": 4}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    report = validate(args.root, args.allow_pending)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
