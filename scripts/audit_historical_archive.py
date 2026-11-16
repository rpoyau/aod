"""Verify an explicitly supplied historical archive, outside normal example admission.

The complete anchor audit is executed unchanged and all five original outputs
are compared byte-for-byte. Normal scientific replay uses the selected source
members and its separately bound adapter instead.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ARCHIVES = {
    'anchor': ('2b26210cf0f7f2fa5e510560d5156aebddaa6a7039e1eab4e9a8209500bead25', 'MANIFEST_SHA256.txt'),
    'metrology': ('b8d6df640eda9e4d7db1e1f4075ab915e32f3b1f61f11ffb3acf5d22f3175deb', 'MANIFEST.sha256'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(kind, path):
    expected, manifest_name = ARCHIVES[kind]
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,
            'historical archive changed')
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, 'historical archive CRC failure')
        members = {}
        for line in archive.read(manifest_name).decode().splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            checksum, name = line.split(None, 1)
            name = name.lstrip('*')
            member = Path(name)
            require(not member.is_absolute() and '..' not in member.parts,
                    'unsafe archive member')
            require(name not in members, 'duplicate archive member binding')
            require(hashlib.sha256(archive.read(name)).hexdigest() == checksum,
                    'historical member changed: ' + name)
            members[name] = checksum
        require(set(archive.namelist()) == set(members) | {manifest_name},
                'historical archive inventory changed')
        if kind == 'anchor':
            with tempfile.TemporaryDirectory(prefix='aod-original-anchor-audit-') as temporary:
                folder = Path(temporary)
                archive.extractall(folder)
                out = folder/'replayed'
                command = [sys.executable, '-B'] + (['-O'] if sys.flags.optimize else [])
                result = subprocess.run(command + [str(folder/'audit_anchor.py'), '--output', str(out)],
                                        capture_output=True, text=True)
                require(result.returncode == 0, 'original anchor audit failed: ' + result.stderr)
                files = sorted(p.name for p in (folder/'results').iterdir())
                require(sorted(p.name for p in out.iterdir()) == files, 'original audit output inventory changed')
                for name in files:
                    require((out/name).read_bytes() == (folder/'results'/name).read_bytes(),
                            'original audit output changed: ' + name)
    return {'status': 'PASS_HISTORICAL_ARCHIVE', 'kind': kind,
            'archive_sha256': expected, 'members': len(members),
            'unmodified_anchor_outputs': 5 if kind == 'anchor' else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=ARCHIVES)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.kind, args.archive), sort_keys=True))


if __name__ == '__main__':
    main()
