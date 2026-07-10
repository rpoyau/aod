#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, shutil, sys, tempfile
from pathlib import Path

EXPECTED_RELEASES = {
    "AF": ("axiomatic-fundamentalism", "authoring_and_review_protocol"),
    "AFC": ("afc", "procedural_calculus_basis"),
    "GM": ("general-mechanics", "authoring_and_review_style"),
    "AOD": ("aod", "stable_project_release_baseline"),
}


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path: Path):
    rows=[]
    for raw in path.read_text(encoding='utf-8').splitlines():
        if not raw: continue
        h, rel = raw.split('  ', 1)
        rows.append((h, rel))
    return rows


def verify_manifest(base: Path, manifest: Path):
    rows=parse_manifest(manifest)
    actual_files={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    expected={rel for _,rel in rows}
    if actual_files != expected:
        raise SystemExit(f'manifest path-set mismatch: missing={sorted(expected-actual_files)} extra={sorted(actual_files-expected)}')
    for expected_hash, rel in rows:
        actual=sha256_file(base/rel)
        if actual != expected_hash:
            raise SystemExit(f'hash mismatch: {rel}')
    return rows




def verify_bundle_manifest(root: Path):
    rows=parse_manifest(root/'BUNDLE_CONTENTS_SHA256.txt')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='BUNDLE_CONTENTS_SHA256.txt'}
    expected={rel for _,rel in rows}
    if actual != expected:
        raise SystemExit(f'bundle manifest path-set mismatch: missing={sorted(expected-actual)} extra={sorted(actual-expected)}')
    for h, rel in rows:
        if sha256_file(root/rel) != h:
            raise SystemExit(f'bundle manifest hash mismatch: {rel}')

def validate_release_registry(root: Path):
    reg=json.loads((root/'governance/REPOSITORY_RELEASE_SOURCES.json').read_text(encoding='utf-8'))
    if reg.get('latest_locator_semantics') != 'authoring_discovery_resolved_snapshot_frozen_per_candidate':
        raise SystemExit('latest locator semantics do not freeze a candidate snapshot')
    rows=reg.get('repositories', [])
    if [r.get('dependency_id') for r in rows] != ['AF','AFC','GM','AOD']:
        raise SystemExit('release dependency order/set mismatch')
    for r in rows:
        dep=r['dependency_id']; repo, role=EXPECTED_RELEASES[dep]
        if r.get('owner')!='rpoyau' or r.get('repository')!=repo or r.get('role')!=role:
            raise SystemExit(f'release source identity mismatch: {dep}')
        expected=f'https://github.com/rpoyau/{repo}/releases/latest'
        expected_api=f'https://api.github.com/repos/rpoyau/{repo}/releases/latest'
        if r.get('latest_release_url')!=expected or r.get('api_latest_url')!=expected_api:
            raise SystemExit(f'release locator mismatch: {dep}')
    policy=json.loads((root/'governance/UPSTREAM_RELEASE_POLICY.json').read_text(encoding='utf-8'))
    if (not policy['discovery']['latest_is_locator_only'] or policy['discovery']['normal_phase_network_access'] or not policy['discovery']['resolved_snapshot_frozen_per_candidate'] or policy['discovery']['latest_refresh_mode'] != 'always_attempt_on_authoring'):
        raise SystemExit('release policy does not enforce authoring-only rolling latest refresh')
    return rows


def main(root: Path):
    verify_bundle_manifest(root)
    verify_manifest(root/'stable/payload', root/'stable/STABLE_PAYLOAD_CONTENTS_SHA256.txt')
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'candidate'
        shutil.copytree(root/'stable/payload', out)
        with (root/'delta/DELTA_MANIFEST.csv').open(encoding='utf-8', newline='') as f:
            rows=list(csv.DictReader(f))
        if [int(r['operation_order']) for r in rows] != list(range(len(rows))):
            raise SystemExit('delta operation order is not contiguous')
        for r in rows:
            rel=Path(r['path'])
            if rel.is_absolute() or '..' in rel.parts:
                raise SystemExit(f'unsafe delta path: {rel}')
            target=out/rel
            op=r['operation']
            if op=='delete':
                if not target.exists(): raise SystemExit(f'delete target absent: {rel}')
                if r['base_sha256'] and sha256_file(target)!=r['base_sha256']:
                    raise SystemExit(f'delete base hash mismatch: {rel}')
                target.unlink()
            elif op in {'add','replace'}:
                src=root/rel
                if not src.is_file(): raise SystemExit(f'candidate source absent: {rel}')
                if sha256_file(src)!=r['candidate_sha256']:
                    raise SystemExit(f'candidate delta hash mismatch: {rel}')
                if op=='replace':
                    if not target.is_file(): raise SystemExit(f'replace target absent: {rel}')
                    if sha256_file(target)!=r['base_sha256']:
                        raise SystemExit(f'replace base hash mismatch: {rel}')
                elif target.exists():
                    raise SystemExit(f'add target already exists: {rel}')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src,target)
            else:
                raise SystemExit(f'unknown delta operation: {op}')
        verify_manifest(out, root/'PAYLOAD_CONTENTS_SHA256.txt')
    imports=json.loads((root/'governance/IMPORT_MANIFEST.json').read_text(encoding='utf-8'))
    if imports.get('canonical_future_lock_path') != 'governance/UPSTREAM_RELEASE_LOCK.json':
        raise SystemExit('canonical future release lock path missing')
    for item in imports['imports']:
        p=root/item['path']
        if sha256_file(p)!=item['sha256']:
            raise SystemExit(f'governance import hash mismatch: {item["import_id"]}')
        if item.get('provenance_status')!='legacy_bootstrap_hash_locked_noncanonical_fallback':
            raise SystemExit(f'bootstrap import provenance status mismatch: {item["import_id"]}')
    validate_release_registry(root)
    root_pointer=json.loads((root/'GLOBAL_INSTRUCTIONS.json').read_text(encoding='utf-8'))
    if root_pointer['canonical_sha256'] != sha256_file(root/'governance/GLOBAL_INSTRUCTIONS.json'):
        raise SystemExit('root global-instruction pointer hash mismatch')
    print('PASS: complete planning-bundle manifest verifies')
    print('PASS: stable + delta materializes candidate')
    print('PASS: bootstrap governance import hashes verify')
    print('PASS: exact AF/AFC/GM/AOD rolling-latest registry and candidate-snapshot policy verify')

if __name__=='__main__':
    main(Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve())
