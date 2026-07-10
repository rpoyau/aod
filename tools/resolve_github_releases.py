#!/usr/bin/env python3
"""Resolve configured GitHub releases into an immutable embedded lock.

Execution is permitted only for a declared upstream-refresh AUTHORING goal. The
command requires an explicit resolution timestamp so identical network snapshots
and inputs can be reproduced without an implicit wall-clock field.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

# Canonical tools must not mutate a clean bundle during execution.
sys.dont_write_bytecode = True
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from bundle_common import (
        canonical_json_bytes,
        inspect_archive_bytes,
        load_json_strict,
        sha256_bytes,
        sha256_file,
        validate_iso_datetime,
        validate_schema,
        write_canonical_json,
    )
except ModuleNotFoundError:  # importlib-based tests
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bundle_common import (  # type: ignore
        canonical_json_bytes,
        inspect_archive_bytes,
        load_json_strict,
        sha256_bytes,
        sha256_file,
        validate_iso_datetime,
        validate_schema,
        write_canonical_json,
    )

VERSION = "3.1"
DEPENDENCY_ORDER = ["AF", "AFC", "GM", "AOD"]
PROFILE_PATHS = {
    "AF": "governance/AF_PROTOCOL_PROFILE.json",
    "AFC": "governance/AFC_PROCEDURAL_DYNAMICS.json",
    "GM": "governance/GENERAL_MECHANICS_STYLE_PROFILE.json",
    "AOD": "governance/GLOBAL_INSTRUCTIONS.json",
}
SAFE_NAME = re.compile(r"^[A-Za-z0-9._+() -]+$")


def safe_asset_name(name: str) -> None:
    if not isinstance(name, str) or not SAFE_NAME.fullmatch(name) or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"unsafe asset name: {name!r}")


def classify_asset(name: str) -> str:
    lower = name.lower()
    if re.fullmatch(r"bundle-v[^/]+\.zip", lower):
        return "canonical_bundle"
    if lower == "bundle.zip":
        return "bundle_alias"
    if lower == "source.zip" or ("source" in lower and lower.endswith((".zip", ".tar.gz", ".tgz"))):
        return "source_archive"
    if lower.endswith(".pdf"):
        return "pdf"
    if "sha256" in lower or "checksum" in lower or lower.endswith((".sha256", ".sha256sum")):
        return "checksum_manifest"
    return "supporting_asset"


def validate_role_contract(dependency_id: str, assets: list[dict[str, Any]], *, source_snapshot_present: bool = True) -> None:
    if dependency_id not in DEPENDENCY_ORDER:
        raise ValueError(f"unknown dependency: {dependency_id}")
    if not source_snapshot_present:
        raise ValueError(f"{dependency_id}: source snapshot required")
    roles = [asset["role"] for asset in assets]
    if "pdf" not in roles:
        raise ValueError(f"{dependency_id}: PDF asset required")
    if dependency_id == "AOD":
        for role in ("canonical_bundle", "checksum_manifest"):
            if role not in roles:
                raise ValueError(f"AOD: {role} required")
    elif "canonical_bundle" in roles:
        raise ValueError(f"{dependency_id}: canonical AOD bundle role forbidden")
    for singleton in ("canonical_bundle", "bundle_alias", "source_archive"):
        if roles.count(singleton) > 1:
            raise ValueError(f"{dependency_id}: duplicate singleton role {singleton}")


def verify_bundle_alias(assets: list[dict[str, Any]], bytes_by_name: dict[str, bytes]) -> None:
    canonical = [asset for asset in assets if asset["role"] == "canonical_bundle"]
    aliases = [asset for asset in assets if asset["role"] == "bundle_alias"]
    if aliases and not canonical:
        raise ValueError("bundle alias present without canonical versioned bundle")
    if aliases and bytes_by_name[aliases[0]["name"]] != bytes_by_name[canonical[0]["name"]]:
        raise ValueError("unversioned bundle alias differs from selected versioned bundle")


def parse_sha256_manifest(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})\s+[* ]?(.+)", line.strip())
        if not match:
            raise ValueError(f"invalid SHA-256 manifest row {line_number}")
        digest, name = match.groups()
        name = name.removeprefix("./")
        if name in rows:
            raise ValueError(f"duplicate checksum path: {name}")
        rows[name] = digest
    if not rows:
        raise ValueError("empty checksum manifest")
    return rows


def verify_authored_manifests(
    dependency_id: str,
    assets: list[dict[str, Any]],
    bytes_by_name: dict[str, bytes],
) -> list[dict[str, Any]]:
    audits: list[dict[str, Any]] = []
    union_covered: set[str] = set()
    required_names = {asset["name"] for asset in assets if asset["role"] != "checksum_manifest"}
    for manifest in [asset for asset in assets if asset["role"] == "checksum_manifest"]:
        try:
            rows = parse_sha256_manifest(bytes_by_name[manifest["name"]].decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError(f"checksum manifest is not UTF-8: {manifest['name']}") from exc
        covered: list[str] = []
        for asset in assets:
            if asset["role"] == "checksum_manifest":
                continue
            matching = [path for path in rows if path == asset["name"] or Path(path).name == asset["name"]]
            if not matching:
                continue
            if rows[matching[0]] != asset["sha256"]:
                raise ValueError(f"authored checksum mismatch: {asset['name']}")
            covered.append(asset["name"])
            union_covered.add(asset["name"])
        audits.append({"manifest_asset_name": manifest["name"], "covered_asset_names": sorted(covered), "status": "passed"})
    if dependency_id == "AOD" and union_covered != required_names:
        raise ValueError(f"AOD checksum coverage incomplete: {sorted(required_names - union_covered)}")
    return sorted(audits, key=lambda row: row["manifest_asset_name"])


def normalized_release_identity(repository: dict[str, Any]) -> dict[str, Any]:
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


def _request_json(url: str, token: str | None, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "AOD-release-resolver/3.1"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_bytes(url: str, token: str | None, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream", "User-Agent": "AOD-release-resolver/3.1"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _resolve_tag_commit(owner: str, repository: str, tag: str, token: str | None, timeout: int) -> str:
    encoded = urllib.parse.quote(tag, safe="")
    ref = _request_json(f"https://api.github.com/repos/{owner}/{repository}/git/ref/tags/{encoded}", token, timeout)
    obj = ref["object"]
    while obj["type"] == "tag":
        obj = _request_json(obj["url"], token, timeout)["object"]
    if obj["type"] != "commit" or not re.fullmatch(r"[0-9a-f]{40}", obj["sha"]):
        raise ValueError(f"unable to resolve tag commit for {owner}/{repository}:{tag}")
    return obj["sha"]


def _embed_profile_binding(root: Path, dependency_id: str, identity_sha: str, assets: list[dict[str, Any]], source_sha: str) -> dict[str, str]:
    profile_path = root / PROFILE_PATHS[dependency_id]
    profile = load_json_strict(profile_path)
    profile["release_binding_status"] = "resolved_immutable_release"
    profile["resolved_release_binding"] = {
        "dependency_id": dependency_id,
        "normalized_release_identity_sha256": identity_sha,
        "source_snapshot_sha256": source_sha,
        "asset_sha256s": sorted(asset["sha256"] for asset in assets),
    }
    write_canonical_json(profile_path, profile)
    return {
        "profile_path": PROFILE_PATHS[dependency_id],
        "profile_sha256": sha256_file(profile_path),
        "normalized_release_identity_sha256": identity_sha,
    }


def _resolve_in_place(root: Path, *, token: str | None, timeout: int, resolved_at_utc: str) -> Path:
    validate_iso_datetime(resolved_at_utc)
    registry_path = root / "governance/REPOSITORY_RELEASE_SOURCES.json"
    policy_path = root / "governance/UPSTREAM_RELEASE_POLICY.json"
    registry = load_json_strict(registry_path)
    validate_schema(registry, root / "governance/schemas/repository-release-sources.schema.json", label="release registry")
    repositories: list[dict[str, Any]] = []

    for configured in registry["repositories"]:
        dependency = configured["dependency_id"]
        metadata = _request_json(configured["api_latest_url"], token, timeout)
        if metadata.get("draft") or metadata.get("prerelease"):
            raise ValueError(f"{dependency}: latest release is draft/prerelease")
        tag = metadata["tag_name"]
        tag_commit = _resolve_tag_commit(configured["owner"], configured["repository"], tag, token, timeout)
        release_root = root / configured["embedding_root_template"].replace("{tag}", tag)
        release_root.mkdir(parents=True, exist_ok=False)
        metadata_path = release_root / "release.json"
        write_canonical_json(metadata_path, metadata)

        source_data = _request_bytes(metadata["zipball_url"], token, timeout)
        source_name = f"source-{tag}.zip"
        safe_asset_name(source_name)
        source_path = release_root / source_name
        source_path.write_bytes(source_data)
        source_audit = inspect_archive_bytes(source_name, source_data)
        if not source_audit["archive_checked"]:
            raise ValueError(f"{dependency}: source snapshot is not a supported archive")

        assets: list[dict[str, Any]] = []
        bytes_by_name: dict[str, bytes] = {}
        for raw in metadata.get("assets", []):
            name = raw["name"]
            safe_asset_name(name)
            data = _request_bytes(raw["browser_download_url"], token, timeout)
            if len(data) != raw["size"]:
                raise ValueError(f"{dependency}: downloaded asset size mismatch: {name}")
            path = release_root / name
            path.write_bytes(data)
            role = classify_asset(name)
            asset = {
                "asset_id": raw["id"],
                "name": name,
                "role": role,
                "download_url": raw["browser_download_url"],
                "byte_count": len(data),
                "sha256": sha256_bytes(data),
                "github_digest": raw.get("digest"),
                "embedded_path": path.relative_to(root).as_posix(),
                "archive_audit": inspect_archive_bytes(name, data),
            }
            assets.append(asset)
            bytes_by_name[name] = data
        validate_role_contract(dependency, assets, source_snapshot_present=True)
        verify_bundle_alias(assets, bytes_by_name)
        audits = verify_authored_manifests(dependency, assets, bytes_by_name)

        repository_record: dict[str, Any] = {
            "dependency_id": dependency,
            "owner": configured["owner"],
            "repository": configured["repository"],
            "role": configured["role"],
            "latest_locator": configured["latest_release_url"],
            "release_id": metadata["id"],
            "resolved_tag": tag,
            "release_html_url": metadata["html_url"],
            "published_at": metadata["published_at"],
            "target_commitish": metadata["target_commitish"],
            "tag_commit_sha": tag_commit,
            "draft": False,
            "prerelease": False,
            "release_metadata_path": metadata_path.relative_to(root).as_posix(),
            "release_metadata_sha256": sha256_file(metadata_path),
            "assets": sorted(assets, key=lambda item: item["name"]),
            "source_snapshot": {
                "download_url": metadata["zipball_url"],
                "byte_count": len(source_data),
                "sha256": sha256_bytes(source_data),
                "embedded_path": source_path.relative_to(root).as_posix(),
                "archive_audit": source_audit,
            },
            "authored_checksum_audits": audits,
            "status": "resolved_embedded_and_hash_verified",
        }
        identity_sha = sha256_bytes(canonical_json_bytes(normalized_release_identity(repository_record)))
        repository_record["normalized_release_identity_sha256"] = identity_sha
        repository_record["profile_binding"] = _embed_profile_binding(root, dependency, identity_sha, repository_record["assets"], repository_record["source_snapshot"]["sha256"])
        repositories.append(repository_record)

    lock = {
        "schema_version": "3.1",
        "lock_id": "AOD_AF_AFC_GM_AOD_PINNED_RELEASE_LOCK",
        "resolved_at_utc": resolved_at_utc,
        "resolver_version": VERSION,
        "registry_sha256": sha256_file(registry_path),
        "policy_sha256": sha256_file(policy_path),
        "repositories": repositories,
    }
    lock_path = root / "governance/UPSTREAM_RELEASE_LOCK.json"
    write_canonical_json(lock_path, lock)
    status_path = root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
    status = load_json_strict(status_path)
    status.update({
        "canonical_lock_present": True,
        "go_eligible": True,
        "go_blocking": False,
        "blocking_reason": "none",
        "required_next_operation": "REVIEW_candidate_scoped_latest_snapshot",
        "refresh_mode": "always_attempt_latest_on_authoring",
        "refresh_attempt_status": "resolved_latest_and_embedded",
        "refresh_attempt_evidence": "All configured GitHub latest-release locators resolved and their immutable candidate snapshots were embedded.",
        "fallback_mode": "none_resolved_lock_active",
        "fallback_claims_latest": False,
        "validation_mode": "strict_lock_when_present_or_explicit_nonblocking_fallback",
        "bootstrap_imports": [
            {**row, "status": "resolved_release_supersedes_bootstrap"}
            for row in status["bootstrap_imports"]
        ],
    })
    write_canonical_json(status_path, status)
    return lock_path


def _write_attempt_receipt(
    root: Path,
    *,
    candidate_release: str,
    attempted_at_utc: str,
    attempt_status: str,
    atomic_commit_status: str,
    canonical_lock_present: bool,
    failure_class: str | None,
    failure_message: str | None,
    resolved_lock_sha256: str | None,
) -> Path:
    validate_iso_datetime(attempted_at_utc)
    fallback_path = root / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json"
    receipt = {
        "schema_version": "3.1",
        "record_scope": "candidate_refresh_attempt",
        "receipt_id": f"refresh_attempt_{candidate_release}_001",
        "candidate_release": candidate_release,
        "attempted_at_utc": attempted_at_utc,
        "refresh_mode": "always_attempt_latest_on_authoring",
        "dependency_order": DEPENDENCY_ORDER,
        "attempt_status": attempt_status,
        "resolver_version": VERSION,
        "staging_mode": "isolated_full_tree_atomic_commit",
        "atomic_commit_status": atomic_commit_status,
        "partial_mutation_rollback_status": "passed_no_candidate_mutation",
        "canonical_lock_present": canonical_lock_present,
        "canonical_lock_path": "governance/UPSTREAM_RELEASE_LOCK.json",
        "fallback_snapshot_path": "governance/UPSTREAM_FALLBACK_SNAPSHOT.json" if fallback_path.is_file() else None,
        "fallback_snapshot_sha256": sha256_file(fallback_path) if fallback_path.is_file() else None,
        "resolved_lock_sha256": resolved_lock_sha256,
        "failure_class": failure_class,
        "failure_message": failure_message,
        "candidate_binding_status": "version_bound",
    }
    path = root / "governance/UPSTREAM_REFRESH_ATTEMPT.json"
    write_canonical_json(path, receipt)
    return path


def _last_verified_fallback(root: Path, candidate_release: str) -> None:
    lock_path = root / "governance/UPSTREAM_RELEASE_LOCK.json"
    if not lock_path.is_file():
        return
    lock = load_json_strict(lock_path)
    dependencies = []
    for repository in lock["repositories"]:
        dependencies.append({
            "dependency_id": repository["dependency_id"],
            "path": repository["release_metadata_path"],
            "sha256": repository["release_metadata_sha256"],
            "provenance_status": "resolved_release_supersedes_bootstrap",
        })
    snapshot = {
        "schema_version": "3.1",
        "snapshot_id": f"LAST_VERIFIED_LOCK_FALLBACK_{candidate_release}",
        "snapshot_type": "last_verified_four_dependency_lock",
        "candidate_release": candidate_release,
        "dependency_order": DEPENDENCY_ORDER,
        "complete": True,
        "dependencies": dependencies,
        "selection_policy": "carry_forward_complete_last_verified_lock_after_failed_refresh",
        "claims_latest": False,
    }
    write_canonical_json(root / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json", snapshot)


def _record_nonblocking_fallback_in_place(
    root: Path,
    reason: str,
    *,
    candidate_release: str | None = None,
    attempted_at_utc: str = "1970-01-01T00:00:00Z",
    failure_class: str = "OSError",
) -> Path:
    status_path = root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
    status = load_json_strict(status_path)
    candidate_release = candidate_release or status.get("candidate_release")
    if not candidate_release:
        raise ValueError("candidate release is required for fallback receipt")
    lock_path = root / "governance/UPSTREAM_RELEASE_LOCK.json"
    if lock_path.is_file():
        _last_verified_fallback(root, candidate_release)
        fallback_mode = "carry_forward_last_verified_lock"
        canonical_lock_present = True
    else:
        fallback_mode = "bootstrap_hash_locked_until_first_successful_refresh"
        canonical_lock_present = False
    receipt_path = _write_attempt_receipt(
        root,
        candidate_release=candidate_release,
        attempted_at_utc=attempted_at_utc,
        attempt_status="attempted_network_unavailable_fallback_active" if failure_class in {"URLError", "TimeoutError", "OSError"} else "attempted_api_failure_fallback_active",
        atomic_commit_status="not_committed_fallback_preserved",
        canonical_lock_present=canonical_lock_present,
        failure_class=failure_class,
        failure_message=reason,
        resolved_lock_sha256=sha256_file(lock_path) if lock_path.is_file() else None,
    )
    fallback_path = root / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json"
    status.update({
        "candidate_release": candidate_release,
        "canonical_lock_present": canonical_lock_present,
        "go_eligible": True,
        "go_blocking": False,
        "blocking_reason": "none",
        "required_next_operation": "REVIEW_candidate_scoped_refresh_receipt_and_complete_fallback",
        "refresh_mode": "always_attempt_latest_on_authoring",
        "refresh_attempt_status": load_json_strict(receipt_path)["attempt_status"],
        "refresh_attempt_evidence": reason,
        "refresh_attempt_receipt_path": "governance/UPSTREAM_REFRESH_ATTEMPT.json",
        "refresh_attempt_receipt_sha256": sha256_file(receipt_path),
        "fallback_snapshot_path": "governance/UPSTREAM_FALLBACK_SNAPSHOT.json",
        "fallback_snapshot_sha256": sha256_file(fallback_path),
        "fallback_mode": fallback_mode,
        "fallback_claims_latest": False,
        "validation_mode": "strict_lock_when_present_or_explicit_nonblocking_fallback",
    })
    status["bootstrap_imports"] = [
        {**row, "status": "resolved_release_supersedes_bootstrap" if canonical_lock_present else "legacy_bootstrap_hash_locked_noncanonical_fallback"}
        for row in status["bootstrap_imports"]
    ]
    write_canonical_json(status_path, status)
    return status_path


def _commit_governance_atomic(stage_root: Path, root: Path) -> None:
    """Replace the complete staged governance tree or restore the prior tree."""
    with tempfile.TemporaryDirectory(dir=root.parent) as backup_dir_name:
        backup = Path(backup_dir_name) / "governance"
        target = root / "governance"
        staged = stage_root / "governance"
        if not staged.is_dir() or not target.is_dir():
            raise ValueError("atomic fallback commit requires complete governance trees")
        os.replace(target, backup)
        try:
            os.replace(staged, target)
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            os.replace(backup, target)
            raise


def _record_nonblocking_fallback(
    root: Path,
    reason: str,
    *,
    candidate_release: str | None = None,
    attempted_at_utc: str = "1970-01-01T00:00:00Z",
    failure_class: str = "OSError",
) -> Path:
    """Stage, validate, and atomically commit a complete fallback packet."""
    root = root.resolve()
    with tempfile.TemporaryDirectory(dir=root.parent) as temporary:
        stage_root = Path(temporary) / "stage"
        shutil.copytree(root, stage_root)
        _record_nonblocking_fallback_in_place(
            stage_root,
            reason,
            candidate_release=candidate_release,
            attempted_at_utc=attempted_at_utc,
            failure_class=failure_class,
        )
        import validate_upstream_release_lock
        validate_upstream_release_lock.validate(stage_root, allow_pending=False)
        _commit_governance_atomic(stage_root, root)
    return root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"


def _commit_atomic(stage_root: Path, root: Path) -> None:
    """Commit only the complete staged governance/stable snapshot, with rollback."""
    with tempfile.TemporaryDirectory(dir=root.parent) as backup_dir_name:
        backup_dir = Path(backup_dir_name)
        moved: list[tuple[Path, Path]] = []
        installed: list[Path] = []
        try:
            for relative in (Path("governance"), Path("stable")):
                staged = stage_root / relative
                target = root / relative
                if not staged.exists():
                    continue
                backup = backup_dir / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    target.rename(backup)
                    moved.append((backup, target))
                staged.rename(target)
                installed.append(target)
        except Exception:
            for target in reversed(installed):
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
            for backup, target in reversed(moved):
                backup.rename(target)
            raise


def resolve(root: Path, *, token: str | None, timeout: int, resolved_at_utc: str, candidate_release: str) -> Path:
    """Resolve all four dependencies in isolation and commit only on total success."""
    validate_iso_datetime(resolved_at_utc)
    root = root.resolve()
    with tempfile.TemporaryDirectory(dir=root.parent) as temporary:
        stage_root = Path(temporary) / "stage"
        shutil.copytree(root, stage_root)
        lock_path = _resolve_in_place(stage_root, token=token, timeout=timeout, resolved_at_utc=resolved_at_utc)
        receipt_path = _write_attempt_receipt(
            stage_root,
            candidate_release=candidate_release,
            attempted_at_utc=resolved_at_utc,
            attempt_status="resolved_latest_and_embedded",
            atomic_commit_status="committed_complete_snapshot",
            canonical_lock_present=True,
            failure_class=None,
            failure_message=None,
            resolved_lock_sha256=sha256_file(lock_path),
        )
        status_path = stage_root / "governance/UPSTREAM_RELEASE_LOCK_STATUS.json"
        status = load_json_strict(status_path)
        status.update({
            "candidate_release": candidate_release,
            "refresh_attempt_receipt_path": "governance/UPSTREAM_REFRESH_ATTEMPT.json",
            "refresh_attempt_receipt_sha256": sha256_file(receipt_path),
            "fallback_snapshot_path": "governance/UPSTREAM_FALLBACK_SNAPSHOT.json",
            "fallback_snapshot_sha256": sha256_file(stage_root / "governance/UPSTREAM_FALLBACK_SNAPSHOT.json"),
        })
        write_canonical_json(status_path, status)
        # Full semantic validation occurs before any candidate mutation is committed.
        import validate_upstream_release_lock
        validate_upstream_release_lock.validate(stage_root, allow_pending=False)
        _commit_atomic(stage_root, root)
    return root / "governance/UPSTREAM_RELEASE_LOCK.json"


def refresh_or_fallback(root: Path, *, token: str | None, timeout: int, attempted_at_utc: str, candidate_release: str, strict_refresh: bool = False) -> Path:
    try:
        return resolve(root, token=token, timeout=timeout, resolved_at_utc=attempted_at_utc, candidate_release=candidate_release)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if strict_refresh:
            raise
        return _record_nonblocking_fallback(
            root,
            f"GitHub latest-release refresh unavailable: {type(exc).__name__}: {exc}",
            candidate_release=candidate_release,
            attempted_at_utc=attempted_at_utc,
            failure_class=type(exc).__name__,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--resolved-at-utc", required=True)
    parser.add_argument("--candidate-release", required=True)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--strict-refresh", action="store_true")
    args = parser.parse_args()
    output = refresh_or_fallback(
        args.root.resolve(),
        token=os.environ.get(args.token_env),
        timeout=args.timeout,
        attempted_at_utc=args.resolved_at_utc,
        candidate_release=args.candidate_release,
        strict_refresh=args.strict_refresh,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
