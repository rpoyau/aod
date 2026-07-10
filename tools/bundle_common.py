#!/usr/bin/env python3
"""Shared deterministic, hash, schema, archive, and manifest primitives."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MAX_ARCHIVE_MEMBERS = 200_000
MAX_UNCOMPRESSED_BYTES = 4 * 1024**3


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_canonical_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def _no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_object)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON {path}: {exc}") from exc


def validate_schema(instance: object, schema_path: Path, *, label: str | None = None) -> None:
    schema = load_json_strict(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        lines = []
        for error in errors:
            location = "/".join(str(part) for part in error.absolute_path) or "<root>"
            lines.append(f"{location}: {error.message}")
        raise ValueError(f"schema validation failed for {label or schema_path.name}:\n" + "\n".join(lines))


def safe_relative_path(value: str, *, allow_spaces: bool = True) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe relative path: {value!r}")
    if not allow_spaces and any(" " in part for part in path.parts):
        raise ValueError(f"spaces forbidden in path: {value!r}")
    return path


def resolve_inside(root: Path, relative: str) -> Path:
    safe_relative_path(relative)
    root_resolved = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {relative}") from exc
    return candidate


def parse_sha_manifest(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"invalid SHA-256 manifest row {path}:{line_number}")
        digest, relative = match.groups()
        safe_relative_path(relative)
        if relative in rows:
            raise ValueError(f"duplicate manifest path: {relative}")
        rows[relative] = digest
    return rows


def write_sha_manifest(path: Path, files: Iterable[Path], base: Path) -> None:
    rows: list[str] = []
    for file_path in sorted(files, key=lambda p: p.relative_to(base).as_posix()):
        relative = file_path.relative_to(base).as_posix()
        safe_relative_path(relative)
        rows.append(f"{sha256_file(file_path)}  {relative}")
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def validate_sha_manifest(
    root: Path,
    manifest_path: Path,
    *,
    expected_paths: set[str] | None = None,
    exclude_paths: set[str] | None = None,
) -> dict[str, str]:
    rows = parse_sha_manifest(manifest_path)
    exclude_paths = exclude_paths or set()
    if expected_paths is None:
        expected_paths = {
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file() and p.relative_to(root).as_posix() not in exclude_paths
        }
    if set(rows) != expected_paths:
        missing = sorted(expected_paths - set(rows))
        extra = sorted(set(rows) - expected_paths)
        raise ValueError(f"manifest coverage mismatch {manifest_path}: missing={missing}, extra={extra}")
    for relative, expected_digest in rows.items():
        file_path = resolve_inside(root, relative)
        if not file_path.is_file():
            raise ValueError(f"manifest file missing: {relative}")
        actual = sha256_file(file_path)
        if actual != expected_digest:
            raise ValueError(f"manifest hash mismatch: {relative}: {actual} != {expected_digest}")
    return rows


def inspect_zip_path(path: Path, *, require_flat_root_ready: bool = False) -> dict[str, int | bool]:
    seen: set[str] = set()
    total = 0
    count = 0
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"corrupt ZIP member: {bad}")
        for info in archive.infolist():
            if info.is_dir():
                continue
            safe_relative_path(info.filename)
            if info.filename in seen:
                raise ValueError(f"duplicate ZIP member: {info.filename}")
            seen.add(info.filename)
            count += 1
            total += info.file_size
            mode = (info.external_attr >> 16) & 0o170000
            if mode in {stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK}:
                raise ValueError(f"ZIP link/device member: {info.filename}")
            if require_flat_root_ready and info.filename.startswith(("source/", "repo/", "repository/")):
                raise ValueError(f"source archive has wrapper directory: {info.filename}")
    if count > MAX_ARCHIVE_MEMBERS or total > MAX_UNCOMPRESSED_BYTES:
        raise ValueError("archive expansion limit exceeded")
    return {"archive_checked": True, "member_count": count, "uncompressed_bytes": total}


def inspect_archive_bytes(name: str, data: bytes) -> dict[str, int | bool]:
    lower = name.lower()
    if lower.endswith(".zip"):
        seen: set[str] = set()
        total = 0
        count = 0
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                safe_relative_path(info.filename)
                if info.filename in seen:
                    raise ValueError(f"duplicate archive member: {info.filename}")
                seen.add(info.filename)
                count += 1
                total += info.file_size
                mode = (info.external_attr >> 16) & 0o170000
                if mode in {stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK}:
                    raise ValueError(f"archive link/device member: {info.filename}")
    elif lower.endswith((".tar", ".tar.gz", ".tgz")):
        seen = set()
        total = 0
        count = 0
        mode = "r:gz" if lower.endswith((".tar.gz", ".tgz")) else "r:"
        with tarfile.open(fileobj=io.BytesIO(data), mode=mode) as archive:
            for member in archive.getmembers():
                safe_relative_path(member.name)
                if member.name in seen:
                    raise ValueError(f"duplicate archive member: {member.name}")
                seen.add(member.name)
                count += 1
                total += max(0, member.size)
                if member.issym() or member.islnk() or member.isdev():
                    raise ValueError(f"archive link/device member: {member.name}")
    else:
        return {"archive_checked": False, "member_count": 0, "uncompressed_bytes": 0}
    if count > MAX_ARCHIVE_MEMBERS or total > MAX_UNCOMPRESSED_BYTES:
        raise ValueError("archive expansion limit exceeded")
    return {"archive_checked": True, "member_count": count, "uncompressed_bytes": total}


def deterministic_zip_from_directory(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file_path in sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.relative_to(source).as_posix()):
            relative = file_path.relative_to(source).as_posix()
            safe_relative_path(relative)
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, file_path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def extract_zip_safe(path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        seen: set[str] = set()
        for info in archive.infolist():
            if info.is_dir():
                continue
            safe_relative_path(info.filename)
            if info.filename in seen:
                raise ValueError(f"duplicate ZIP member: {info.filename}")
            seen.add(info.filename)
            target = resolve_inside(destination, info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))


def directory_hash_map(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha256_file(p)
        for p in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    }


def validate_iso_datetime(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"date-time lacks timezone: {value}")


def csv_rows_strict(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            raise ValueError(f"CSV header mismatch for {path}: {reader.fieldnames} != {expected_header}")
        rows = list(reader)
    for index, row in enumerate(rows, 1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"malformed CSV row {path}:{index + 1}")
    return rows


def row_sha256(values: list[str]) -> str:
    return sha256_bytes(("\x1f".join(values) + "\n").encode("utf-8"))
