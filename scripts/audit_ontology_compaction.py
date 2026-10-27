"""Current mathematical ownership, fixture provenance and protected source bytes.

Main is a self-contained ontology. Manual models import typed Main premises.
Immutable fixture tags resolve through operation-specific current bindings.
"""
from pathlib import Path
import hashlib
import json
import re


CONTRACT_ROOT = 'contracts/scientific/'
# These independent byte bindings are reviewed with the checker. Loading a
# modified contract never changes an expected digest or authorizes new sources.
CONTRACT_SHA256 = {
    "AWARENESS_ACTIVE_CAUSAL_SPEC.json": "a4e530314d03ff2a695a5d9f6d59f20f18ab8ae4c388a594b99fcf0996c5cf05",
    "CANONICAL_BINDINGS.json": "48fafabead1c397690151f843d306da15a363565ccdcbc1355f48d1145ff7ba2",
    "FOURIER_SCOPE.md": "0bb855f5666a97a285d4e2ded98adf9cb70dc372b9039c33bcaeb43b38435328",
    "HISTORICAL_TOY_SOURCE_STATUS.csv": "dc0f1b94afc71f930929e64caef8d9f9cb49386035706aa2b79b8b9cc0de42d4",
    "METROLOGY_BOUNDARY.md": "553609db18f523faae6d2a53c3465c56ceb9034c6ba1ae3b7a6cff77fdf678af",
    "OPERATIVE_SELF_SCHEMA.json": "0fba87a85c542a5a9b74f2242724bf334ecb1a0c39886a20c9298309d3005ecd",
    "OWNERSHIP_AND_FIXTURES.json": "b86ef3d495a0b689da77307ad8facb945dd75bd603c0485bbcd88028c31e69d8",
    "README.md": "27f91f12b10dc04bc875bf39e7c84db5a6049e17204573d888f2c3c273daed75",
    "ROUND_TRIP_PHASE_FACTOR_SPEC.json": "a7f7c6aea4a373655e9031515d95cc19569557ad35357665e1e56d8b81777ed5",
    "UPDATE_CAUSAL_ORDER.md": "879fe4fce9ec09b8640ca31eea28c09a3a6d2047f6d58eeafe463ece055315bd"
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _formula(block):
    return re.sub(r"\s+", "", re.sub(r"\\label\{[^}]+\}", "", block))


def _check_contract(root, name):
    data = (root / CONTRACT_ROOT / name).read_bytes()
    _require(hashlib.sha256(data).hexdigest() == CONTRACT_SHA256[name],
             'scientific contract integrity changed ' + name)
    return data


def audit_ownership(root, maps, eqs, parts):
    record = json.loads(_check_contract(root, 'OWNERSHIP_AND_FIXTURES.json'))
    _require(record['schema'] == 'aod.scientific.ownership-fixtures.v1',
             'unknown ownership and fixture schema')
    spec = json.loads(_check_contract(root, 'AWARENESS_ACTIVE_CAUSAL_SPEC.json'))
    _require(hashlib.sha256((root / spec['operative_source']).read_bytes()).hexdigest() ==
             spec['source_sha256'], 'current Awareness specification source binding changed')

    def resolve(binding):
        surface, path, label = (binding[k] for k in ('surface', 'path', 'label'))
        _require(surface in maps and maps[surface].get(label, {}).get('path') == path,
                 'inactive or wrong typed owner ' + label)
        _require(label not in maps['manual' if surface == 'main' else 'main'],
                 'duplicate cross-document owner ' + label)

    for binding in spec['source_anchor_bindings']:
        resolve(binding)
    for binding in record['anchor_owners']:
        resolve(binding)
        if binding['equation']:
            body = eqs[binding['surface']].get(binding['label'])
            _require(body is not None, 'owned mathematical body absent ' + binding['label'])
            _require(hashlib.sha256(_formula(body).encode()).hexdigest() == binding['formula_sha256'],
                     'owned mathematical statement changed ' + binding['label'])
    fixture = root / record['fixture_path']
    fixture_bytes = fixture.read_bytes()
    _require(record['fixture_path'] == 'manual/data/m2/awareness_cases.jsonl' and
             hashlib.sha256(fixture_bytes).hexdigest() == record['fixture_sha256'],
             'immutable fixture file changed')
    rows = fixture_bytes.decode().splitlines()
    _require(len(rows) == len(record['fixture_bindings']) == 47, 'fixture inventory changed')
    for raw, binding in zip(rows, record['fixture_bindings']):
        row = json.loads(raw)
        _require(hashlib.sha256(raw.encode()).hexdigest() == binding['fixture_row_sha256'],
                 'immutable fixture row changed ' + binding['fixture_id'])
        _require((row['fixture_id'], row['main_anchor'], row['manual_anchor'], row['operation']) ==
                 (binding['fixture_id'], binding['immutable_legacy_main_anchor'],
                  binding['immutable_manual_anchor'], binding['operation']), 'fixture provenance mismatch')
        _require(hashlib.sha256((root / row['source']).read_bytes()).hexdigest() == row['source_sha256'],
                 'current fixture source binding changed')
        resolve(binding['current_construct'])
        for label in binding['main_premises']:
            _require(label in eqs['main'], 'missing genuine Main premise ' + label)
        for label in binding['manual_model_equations']:
            _require(label in eqs['manual'] and label not in maps['main'],
                     'missing local Manual model ' + label)
    text = '\n'.join(t for _, t in parts['main'])
    # Stable internal keys are not rendered terminology.
    prose = re.sub(r'\\(?:label|(?:eqn?|sec|app|fig|tab)?ref)\{[^}]+\}', '', text)
    for name, pattern in (
        ('Main-to-Manual dependency', r'(?i)\bmanual\b'),
        ('application procedure', r'(?i)\b(readout|ledger|cache|implementation|sensor|proprioception|mindfulness)\b'),
        ('action residual', r'r_a\s*=\s*y\s*-\s*u'),
        ('query feedback', r'q_k\s*=\s*-\s*J_k'),
        ('fixture diagnostic', r'\\delta_\{?3'),
    ):
        _require(re.search(pattern, prose) is None, 'Main concept exclusion: ' + name)
    main_formulas = {_formula(m.group()) for m in re.finditer(
        r'\\begin\{(equation|align|gather)(\*?)\}.*?\\end\{\1\2\}', text, re.S)}
    manual_hashes = {b['formula_sha256'] for b in record['anchor_owners']
                     if b['equation'] and b['surface'] == 'manual'}
    _require(not ({hashlib.sha256(t.encode()).hexdigest() for t in main_formulas} & manual_hashes),
             'local application body copied into Main')
    return record


def audit(root, main_files, main_parts, labels, equations, manual_files, manual_labels,
          manual_parts, manual_equations):
    root = Path(root)
    contract = json.loads((root / CONTRACT_ROOT / 'CANONICAL_BINDINGS.json').read_text())
    _require(contract['schema'] == 'aod.scientific.canonical.v1', 'unknown canonical schema')
    groups = {row['concept']: row for row in contract['ownership']}
    _require(len(groups) == len(contract['ownership']) == 44, 'canonical group inventory changed')
    maps = {'main': labels, 'manual': manual_labels}
    eqs = {'main': equations, 'manual': manual_equations}
    files = {'main': main_files, 'manual': manual_files}
    parts = {'main': main_parts, 'manual': manual_parts}
    _require(not (set(labels) & set(manual_labels)), 'duplicate cross-document active owner')

    def position(anchor, surface='main'):
        _require(anchor in maps[surface], 'missing active canonical anchor ' + anchor)
        item = maps[surface][anchor]
        return files[surface].index(item['path']), item['position']

    # Keep active-inclusion failures legible before resolving moved equations.
    for record in contract['manual_families']:
        _require(record['manual_path'] in manual_files and
                 manual_labels.get(record['manual_anchor'], {}).get('path') == record['manual_path'],
                 'Manual example family not rendered ' + record['id'])
    edges = 0
    for row in groups.values():
        surface = row['surface']
        for anchor in row['anchors']:
            position(anchor, surface)
            _require(maps[surface][anchor]['path'] == row['path'], 'canonical owner changed ' + anchor)
            _require(anchor not in maps['manual' if surface == 'main' else 'main'], 'duplicate canonical owner ' + anchor)
            _require(anchor in eqs[surface], 'canonical mathematical body absent ' + anchor)
            _require(_formula(eqs[surface][anchor]) == contract['formulas'][anchor],
                     'canonical mathematical statement changed ' + anchor)
        for dependency in row['depends_on']:
            _require(dependency in groups, 'unknown prerequisite ' + dependency)
            premise = groups[dependency]; ps = premise['surface']
            _require(not (surface == 'main' and ps == 'manual'), 'Main depends on Manual: ' + row['concept'])
            if ps == surface:
                _require(max(position(a, ps) for a in premise['first_declarations']) <
                         min(position(a, surface) for a in row['first_declarations']),
                         'substantive consumer precedes prerequisite ' + row['concept'])
            edges += 1
    _require(edges == 72, 'dependency edge inventory changed')
    audit_ownership(root, maps, eqs, parts)
    _require({a for r in groups.values() for a in r['anchors']} == set(contract['formulas']) and
             len(contract['formulas']) == 81, 'canonical formula inventory changed')
    for label, binding in contract['supplemental_formulas'].items():
        surface = binding['surface']
        _require(maps[surface].get(label, {}).get('path') == binding['path'] and
                 label in eqs[surface] and _formula(eqs[surface][label]) == binding['formula'],
                 'supplemental mathematical statement or owner changed ' + label)
    for record in contract['first_uses']:
        for anchor in record['required_declaration_anchors']:
            _require(position(anchor) < position(record['first_substantive_use_anchor']),
                     'first use precedes its actual declaration ' + record['id'])

    definition_text = []
    for surface in ('main', 'manual'):
        for path, text in parts[surface]:
            body = re.sub(r'\\begin\{(figure\*?|table\*?|longtable)\}.*?\\end\{\1\}', '', text, flags=re.S)
            definition_text.append((surface, path, re.sub(r'\s+', '', body)))
    for record in contract['unique_signatures']:
        pattern = record['pattern']
        matches = [(surface, path) for surface, path, body in definition_text
                   for match in re.finditer(pattern, body)]
        _require(matches == [(record['surface'], record['path'])],
                 'competing or absent canonical binding ' + record['anchor'])

    appendices = contract["appendices"]
    _require([p for p in main_files if p.startswith("appendices/")] == appendices,
             "inherited A-J paths/order changed")
    for path in appendices:
        text = dict(main_parts)[path]
        heading = re.search(r"\\(section|subsection|subsubsection)\*?\{", text)
        _require(heading is not None and heading[1] == "section",
                 "appendix is not a top-level section " + path)
    for record in contract["navigation"]:
        _require(record["replacement"] in dict(main_parts)[record["path"]],
                 "local Main provenance call absent " + record["target"])
        _require(labels.get(record["target"], {}).get("path") == record["target_path"],
                 "local Main provenance target changed " + record["target"])

    for record in contract["manual_families"]:
        _require(record["manual_path"] in manual_files and
                 manual_labels.get(record["manual_anchor"], {}).get("path") == record["manual_path"],
                 "Manual example family not rendered " + record["id"])
        for anchor in record["main_anchors"]:
            position(anchor)
        for anchor in record.get("manual_model_anchors", []):
            position(anchor, "manual")
            _require(anchor in manual_equations, "local model body absent " + anchor)
    # Check exact contract bytes after semantic diagnostics, before using any
    # source-protection entries. Deleting or rebinding an entry cannot pass.
    for name in CONTRACT_SHA256:
        _check_contract(root, name)
    for path, wanted in contract['frozen_sha256'].items():
        _require((root / path).is_file() and
                 hashlib.sha256((root / path).read_bytes()).hexdigest() == wanted,
                 'protected engine, input, test or presentation changed ' + path)
    _require(not (root / 'sections/02_introduction.tex').exists(),
             'obsolete introduction restored')
    return {'canonical_groups': len(groups), 'canonical_equations': len(contract['formulas']),
            'supplemental_equations': len(contract['supplemental_formulas']),
            'ordered_dependencies': edges, 'refined_first_uses': len(contract['first_uses']),
            'unique_defining_signatures': len(contract['unique_signatures']),
            'appendices': 10, 'local_provenance_repairs': len(contract['navigation']),
            'manual_example_families': len(contract['manual_families']),
            'frozen_files': len(contract['frozen_sha256'])}
