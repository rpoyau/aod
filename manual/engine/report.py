"""Deterministic canonical report builder and serializer (aod.manual.engine.report.v1).

Output bytes are deterministic across operating environments, checkouts, and
normal vs ``python3 -O`` execution: sorted keys, ASCII-safe UTF-8, LF endings,
zero timestamps/durations/absolute paths, and zero float/complex values.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from manual.engine.numeric import require
from manual.engine.policy import require_no_floats
from manual.engine.registry import SECTOR_SPECS, registry_digest
from manual.engine.schema import (
    BASE_COMMIT_BINDING,
    ENGINE_VERSION,
    REPORT_SCHEMA,
    VALID_SCIENTIFIC_STATUSES,
    validate_report,
)

_CANONICAL_SECTOR_ORDER: dict[str, int] = {
    spec.sector_id: idx for idx, spec in enumerate(SECTOR_SPECS)
}

_ALLOWED_IN_REPO_OUTPUT_ROOTS: frozenset[str] = frozenset(
    {"_build", "build", "dist", "release"}
)

_UNSAFE_FILE_SUFFIXES: tuple[str, ...] = ("/", "\\", "/.", "\\.", "/..", "\\..")


def default_repo_root() -> Path:
    """Resolve the repository root containing ``manual/engine/``."""
    return Path(__file__).resolve().parents[2]


def _path_within_lexical(path: Path, root: Path) -> bool:
    norm_path = Path(os.path.normpath(str(path)))
    norm_root = Path(os.path.normpath(str(root)))
    try:
        norm_path.relative_to(norm_root)
        return True
    except ValueError:
        return False


def _reject_pre_resolution_symlinks(
    raw_path: Path | str,
    roots: tuple[Path, ...],
    *,
    flag_name: str,
) -> None:
    """Reject symlinks on the target itself or any lexical segment inside any guarded root."""
    path_obj = Path(str(raw_path))
    lexical_abs = path_obj if path_obj.is_absolute() else (Path.cwd() / path_obj)
    norm_abs = Path(os.path.normpath(str(lexical_abs)))
    if os.path.islink(lexical_abs) or os.path.islink(norm_abs):
        raise ValueError(f"{flag_name} target must not be a symlink")

    # Walk every lexical prefix BEFORE calling .resolve() so symlinks like _build/escape -> /tmp
    # are caught before resolution can leave the repository tree.
    parts = lexical_abs.parts
    if parts:
        cur = Path(parts[0])
        for part in parts[1:]:
            if part == ".":
                continue
            if part == "..":
                cur = cur.parent
                continue
            cur = cur / part
            if os.path.islink(cur):
                cur_in_resolved_parent = cur.parent.resolve() / cur.name
                if any(
                    _path_within_lexical(cur, r) or _path_within_lexical(cur_in_resolved_parent, r)
                    for r in roots
                ):
                    raise ValueError(
                        f"{flag_name} must not traverse symlink {cur.name!r} inside repository"
                    )


def validate_runtime_output_path(
    raw_path: Path | str,
    repo_root: Path,
    *,
    flag_name: str,
    expect_dir: bool = False,
) -> Path:
    """Reject writing runtime outputs inside distributable repository source directories.

    Enforces pre-resolution symlink checks (including normalized lexical targets),
    rejects directory-specifier file paths when ``expect_dir=False``, checks both
    ``repo_root`` and ``default_repo_root()``, and rejects existing directory/file
    type collisions. Outputs are allowed ONLY outside both repository roots or inside
    an excluded top-level build directory (``_build/``, ``build/``, ``dist/``, ``release/``).
    """
    raw_str = str(raw_path)
    if not raw_str:
        raise ValueError(f"{flag_name} target path must not be empty")
    if not expect_dir and (
        raw_str in {".", ".."} or raw_str.endswith(_UNSAFE_FILE_SUFFIXES)
    ):
        raise ValueError(
            f"{flag_name} target must be a file path, not a directory specifier: {raw_str!r}"
        )

    repo = Path(repo_root).resolve()
    def_repo = default_repo_root().resolve()
    guarded_roots = (repo,) if repo == def_repo else (repo, def_repo)

    _reject_pre_resolution_symlinks(raw_str, guarded_roots, flag_name=flag_name)

    candidate = Path(raw_str)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    for guarded in guarded_roots:
        try:
            rel = candidate.relative_to(guarded)
        except ValueError:
            continue
        if not rel.parts or len(rel.parts) < 2 or rel.parts[0] not in _ALLOWED_IN_REPO_OUTPUT_ROOTS:
            raise ValueError(
                f"{flag_name} target {rel.as_posix()!r} is inside a distributable repository "
                f"directory; write outside the repository or under _build/ to prevent source.zip contamination"
            )
        if candidate.is_symlink() or any(
            (guarded / parent).is_symlink() for parent in rel.parents if parent != Path(".")
        ):
            raise ValueError(f"{flag_name} must not traverse symlinks inside repository")

    if expect_dir:
        if candidate.exists() and not candidate.is_dir():
            raise ValueError(f"{flag_name} target already exists as a non-directory file")
    else:
        if candidate.exists() and candidate.is_dir():
            raise ValueError(f"{flag_name} target already exists as a directory")

    for parent in candidate.parents:
        if parent.exists():
            if not parent.is_dir():
                raise ValueError(f"{flag_name} parent path exists as a non-directory file")
            break

    return candidate


def atomic_write_safe_text(
    raw_path: Path | str,
    content: str,
    repo_root: Path,
    *,
    flag_name: str,
) -> Path:
    """Validate ``raw_path`` and atomically write UTF-8 text to a newly allocated inode.

    Creates an exclusive sibling temporary file via ``O_CREAT | O_EXCL | O_NOFOLLOW``
    and installs it with ``os.replace``. Existing external hard links are replaced
    with a fresh inode so any linked source file remains untouched.
    """
    require(isinstance(content, str), f"{flag_name} content must be str")
    candidate = validate_runtime_output_path(
        raw_path, repo_root, flag_name=flag_name, expect_dir=False
    )
    candidate.parent.mkdir(parents=True, exist_ok=True)
    if os.path.islink(candidate):
        raise ValueError(f"{flag_name} target must not be a symlink")
    if candidate.is_dir():
        raise ValueError(f"{flag_name} target already exists as a directory")

    payload = content.encode("utf-8")
    open_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    pid = os.getpid()
    tmp_path: Path | None = None
    fd: int | None = None
    for attempt in range(10000):
        probe = candidate.parent / f".aod-engine-tmp-{pid}-{attempt}"
        try:
            fd = os.open(probe, open_flags, 0o600)
            tmp_path = probe
            break
        except FileExistsError:
            continue
    if fd is None or tmp_path is None:
        raise OSError(f"{flag_name} failed to allocate unique sibling temporary file")

    replaced = False
    try:
        try:
            view = memoryview(payload)
            written = 0
            while written < len(payload):
                chunk = os.write(fd, view[written:])
                if chunk <= 0:
                    raise OSError(f"{flag_name} short write to sibling temporary file")
                written += chunk
        finally:
            os.close(fd)
            fd = None

        if os.path.islink(candidate):
            raise ValueError(f"{flag_name} target must not be a symlink")
        if candidate.is_dir():
            raise ValueError(f"{flag_name} target already exists as a directory")
        os.replace(tmp_path, candidate)
        replaced = True
    finally:
        if fd is not None:
            os.close(fd)
        if not replaced:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return candidate


def build_report(
    sector_results: list[dict[str, object]],
    *,
    data_coverage_audit: dict[str, object],
    zero_float_policy_audit: dict[str, object],
    vectors_verification: dict[str, object] | None = None,
) -> dict[str, object]:
    """Assemble and validate a canonical ``aod.manual.engine.report.v1`` dict."""
    ordered_sectors = sorted(
        sector_results,
        key=lambda rec: _CANONICAL_SECTOR_ORDER.get(str(rec.get("sector_id", "")), 999),
    )

    outcomes_summary = {
        "total_executed": len(ordered_sectors),
        "PASS": sum(1 for rec in ordered_sectors if rec.get("check_outcome") == "PASS"),
        "FAIL": sum(1 for rec in ordered_sectors if rec.get("check_outcome") == "FAIL"),
    }

    scientific_status_summary = {status: 0 for status in sorted(VALID_SCIENTIFIC_STATUSES)}
    for rec in ordered_sectors:
        if rec.get("check_outcome") == "PASS":
            status = str(rec["scientific_status"])
            if status in scientific_status_summary:
                scientific_status_summary[status] += 1

    payload: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "engine_version": ENGINE_VERSION,
        "base_commit_binding": BASE_COMMIT_BINDING,
        "registry_digest": registry_digest(),
        "sector_count": len(ordered_sectors),
        "data_coverage_audit": data_coverage_audit,
        "sectors": ordered_sectors,
        "outcomes_summary": outcomes_summary,
        "scientific_status_summary": scientific_status_summary,
        "zero_float_policy_audit": zero_float_policy_audit,
    }
    if vectors_verification is not None:
        payload["vectors_verification"] = vectors_verification

    require_no_floats(payload)
    validate_report(payload)
    return payload


def serialize_report(report_obj: dict[str, object]) -> str:
    """Validate and deterministically serialize a canonical report to UTF-8 JSON with LF."""
    validate_report(report_obj)
    return json.dumps(report_obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
