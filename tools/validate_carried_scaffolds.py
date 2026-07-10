#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tempfile, zipfile
from pathlib import Path

def load_json(p: Path): return json.loads(p.read_text(encoding='utf-8'))

def check(root: Path):
    path=root/'governance/CARRIED_SCAFFOLD_LOCK.json'
    if not path.is_file(): return [f'missing {path}']
    lock=load_json(path)
    errors=[]
    for rel, needles in lock.get('files',{}).items():
        f=root/rel
        if not f.is_file():
            # Bundle roots only carry selected source-facing files; source roots carry all.
            continue
        text=f.read_text(encoding='utf-8')
        for needle in needles:
            if needle not in text:
                errors.append(f'{rel} missing scaffold {needle!r}')
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root', type=Path); args=ap.parse_args(); root=args.root.resolve()
    errors=[]
    if (root/'source.zip').is_file():
        with tempfile.TemporaryDirectory() as d:
            with zipfile.ZipFile(root/'source.zip') as z: z.extractall(d)
            errors.extend('source.zip:'+e for e in check(Path(d)))
    errors.extend(check(root))
    if errors: raise SystemExit('\n'.join(errors))
    print(json.dumps({'status':'passed','validator':'carried_scaffolds'}, sort_keys=True))
if __name__ == '__main__': main()
