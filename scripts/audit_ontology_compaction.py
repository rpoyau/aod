"""Current mathematical ownership, fixture provenance and protected source bytes.

Source locations identify the reviewed statements; they do not prescribe style.
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
    "TEMPORAL_METROLOGY.json": "a81b261fca3be6202a1fb02d6334e60751b25d1e0c9ff5ef89bb50ba44145da9",
    "TEMPORAL_OBSERVATION.json": "b02344dcaa98c3de1b7453d868b332b2bd537f08c9c2e92de048e337c6747e69",
    "MAP_CONTRACT.json": "3d6766979397c7732e6cd88793cf6befb9fa48fa69267598cfcf0d781a300aea",
    "CELL_MAPPING_MATHEMATICAL_BINDINGS.json": "b1861d94cd79f4cbd81916dd2c6dd6da869e612185e4d6f2dd4cc887f1f73a0b",
    "M3_WAVELET_COMPACTION_BINDINGS.json": "e35553d9bf455cc503699b22e8e6da9f314062a0cd572f9824dded06ebbeaa6a",
    "ERROR_BUDGET.json": "8ea33dabcf681e01d459f170b31c10b59fdf9e63ea708c64ac6ed7c1be62a57f",
    "CELL_MEASURE_SPEC.json": "75fc35552c419d831d8fcd5dfe1ee1b46dffa4e862535d4b74029f3c2018c9ea",
    "AWARENESS_ACTIVE_CAUSAL_SPEC.json": "ad4070efbdc8ca584812a1a947d083d2f6f4676f2aef22638dfb7f5854da4f27",
    "CANONICAL_BINDINGS.json": "10ee953f5005054e639993d97d1b1b20bbc4b8b1e0c079d22d9156fd07efbc24",
    "FOURIER_SCOPE.md": "0bb855f5666a97a285d4e2ded98adf9cb70dc372b9039c33bcaeb43b38435328",
    "HISTORICAL_TOY_SOURCE_STATUS.csv": "dc0f1b94afc71f930929e64caef8d9f9cb49386035706aa2b79b8b9cc0de42d4",
    "METROLOGY_BOUNDARY.md": "553609db18f523faae6d2a53c3465c56ceb9034c6ba1ae3b7a6cff77fdf678af",
    "OPERATIVE_SELF_SCHEMA.json": "0fba87a85c542a5a9b74f2242724bf334ecb1a0c39886a20c9298309d3005ecd",
    "OWNERSHIP_AND_FIXTURES.json": "935d97f71f9127195febebb276cf43b5355f3b09a59d5d60d02b9c09be484ca4",
    "README.md": "7ea9622a9bdd4e01172f66eebe59c0d0e60cd31a234933b721cac352f6b01016",
    "ROUND_TRIP_PHASE_FACTOR_SPEC.json": "a54b0a8b799228c11b60b88c706824045aaefae2000c1cf081e838582dcba11e",
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
    _require(record['fixture_path'] == 'manual/data/awareness/awareness_cases.jsonl' and
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
    return record


def validate_dependencies(groups):
    """Verify declared premise relations independently of publication order."""
    visiting, complete = set(), set()

    def visit(concept):
        _require(concept in groups, 'unknown prerequisite ' + concept)
        _require(concept not in visiting, 'cyclic scientific prerequisite ' + concept)
        if concept in complete:
            return
        visiting.add(concept)
        dependencies = groups[concept]['depends_on']
        _require(len(dependencies) == len(set(dependencies)),
                 'duplicate scientific prerequisite ' + concept)
        for dependency in dependencies:
            visit(dependency)
        visiting.remove(concept)
        complete.add(concept)

    for concept in groups:
        visit(concept)
    return sum(len(row['depends_on']) for row in groups.values())


def audit_m3(root, maps, eqs):
    """Check the explicit additional mathematics without changing old duties."""
    record = json.loads(_check_contract(root, 'CELL_MAPPING_MATHEMATICAL_BINDINGS.json'))
    _require(record['schema'] == 'aod.scientific.m3-mathematics.v1',
             'unknown M3 mathematical binding schema')
    paths = {'main': 'sections/07_cell_measures_mappings.tex',
             'manual': 'manual/sections/01_cell_measures.tex'}
    _require(set(record['sources']) == set(paths.values()),
             'M3 mathematical source inventory changed')
    _require(len(record['equations']) == 7, 'M3 equation inventory changed')
    for label, binding in record['equations'].items():
        # The original v1 records implicitly owned their equations in Main.
        # An explicit surface extends that same binding to a moved example.
        surface = binding.get('surface', 'main')
        _require(surface in paths and binding['path'] == paths[surface] and
                 maps[surface].get(label, {}).get('path') == binding['path'] and
                 label not in maps['manual' if surface == 'main' else 'main'] and
                 label in eqs[surface] and
                 _formula(eqs[surface][label]) == binding['formula'],
                 'M3 mathematical statement or owner changed ' + label)
    cells = json.loads(_check_contract(root, 'CELL_MEASURE_SPEC.json'))
    _require(cells['schema'] == 'aod.scientific.cell-measure.v1',
             'unknown cell measure specification schema')
    for surface, path in paths.items():
        anchors = cells.get(surface + '_anchors', [])
        _require(isinstance(anchors, list) and all(isinstance(a, str) for a in anchors)
                 and len(anchors) == len(set(anchors)), 'invalid cell measure anchor inventory')
        for label in anchors:
            _require(maps[surface].get(label, {}).get('path') == path and
                     label not in maps['manual' if surface == 'main' else 'main'],
                     'cell measure anchor owner changed ' + label)
    for path, digest in record['sources'].items():
        _require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest,
                 'M3 mathematical source changed ' + path)
    return {'equations': len(record['equations']), 'sources': len(record['sources'])}


def audit_m3_wavelet_compaction(root, maps, eqs):
    """Check additive Phase 1 wavelet-compaction and conditional SI bindings."""
    record = json.loads(_check_contract(root, 'M3_WAVELET_COMPACTION_BINDINGS.json'))
    _require(record['schema'] == 'aod.scientific.m3-wavelet-compaction.v1',
             'unknown M3 wavelet compaction schema')
    eq_map = record['equations']
    _require(len(eq_map) == 11, 'M3 wavelet compaction equation inventory changed')
    _require(sum(b.get('status') == 'new' for b in eq_map.values()) == 10 and
             sum(b.get('status') == 'inherited_reference' for b in eq_map.values()) == 1,
             'M3 wavelet compaction equation classification changed')
    for label, binding in eq_map.items():
        surface = binding.get('surface', 'main')
        _require(surface == 'main' and binding['path'] in record['sources'] and
                 maps['main'].get(label, {}).get('path') == binding['path'] and
                 label not in maps['manual'] and
                 label in eqs['main'] and
                 _formula(eqs['main'][label]) == binding['formula'],
                 'M3 wavelet compaction statement or owner changed ' + label)
        deps = binding.get('depends_on', [])
        _require(isinstance(deps, list) and len(deps) > 0 and len(deps) == len(set(deps)),
                 'M3 wavelet compaction invalid prerequisites ' + label)
        for dep in deps:
            _require(dep in maps['main'], 'M3 wavelet compaction unknown prerequisite ' + dep)
    visiting, complete = set(), set()

    def visit(label):
        _require(label not in visiting, 'M3 wavelet compaction cyclic prerequisite ' + label)
        if label in complete:
            return
        visiting.add(label)
        for dep in eq_map[label]['depends_on']:
            if dep in eq_map:
                visit(dep)
        visiting.remove(label)
        complete.add(label)

    for label in eq_map:
        visit(label)
    figures = record['relocated_figures']
    _require(len(figures) == 2, 'M3 wavelet compaction relocated figure inventory changed')
    for label, binding in figures.items():
        _require(binding.get('surface') == 'main' and
                 maps['main'].get(label, {}).get('path') == binding['path'] and
                 label not in maps['manual'],
                 'M3 wavelet compaction figure owner changed ' + label)
    retained = record['retained_anchors']
    new_anchors = record['new_anchors']
    _require(len(retained) == 6 and len(new_anchors) == 2,
             'M3 wavelet compaction tracked anchor inventory changed')
    for label, binding in list(retained.items()) + list(new_anchors.items()):
        _require(binding.get('surface') == 'main' and
                 maps['main'].get(label, {}).get('path') == binding['path'] and
                 label not in maps['manual'],
                 'M3 wavelet compaction tracked anchor changed ' + label)
    _require(len(record['sources']) == 6, 'M3 wavelet compaction source inventory changed')
    for path, digest in record['sources'].items():
        _require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest,
                 'M3 wavelet compaction source changed ' + path)
    return {
        'equations': len(eq_map),
        'new_equations': 10,
        'inherited_equations': 1,
        'relocated_figures': len(figures),
        'retained_anchors': len(retained),
        'new_anchors': len(new_anchors),
        'sources': len(record['sources']),
    }


def audit(root, main_files, main_parts, labels, equations, manual_files, manual_labels,
          manual_parts, manual_equations):
    root = Path(root)
    contract = json.loads((root / CONTRACT_ROOT / 'CANONICAL_BINDINGS.json').read_text())
    _require(contract['schema'] == 'aod.scientific.canonical.v1', 'unknown canonical schema')
    groups = {row['concept']: row for row in contract['ownership']}
    _require(len(groups) == len(contract['ownership']) == 44, 'canonical group inventory changed')
    maps = {'main': labels, 'manual': manual_labels}
    eqs = {'main': equations, 'manual': manual_equations}
    parts = {'main': main_parts, 'manual': manual_parts}
    _require(not (set(labels) & set(manual_labels)), 'duplicate cross-document active owner')

    def require_anchor(anchor, surface='main'):
        _require(anchor in maps[surface], 'missing active canonical anchor ' + anchor)

    # Keep active-inclusion failures legible before resolving moved equations.
    for record in contract['manual_families']:
        _require(record['manual_path'] in manual_files and
                 manual_labels.get(record['manual_anchor'], {}).get('path') == record['manual_path'],
                 'Manual example family not rendered ' + record['id'])
    edges = validate_dependencies(groups)
    for row in groups.values():
        surface = row['surface']
        for anchor in row['anchors']:
            require_anchor(anchor, surface)
            _require(maps[surface][anchor]['path'] == row['path'], 'canonical owner changed ' + anchor)
            _require(anchor not in maps['manual' if surface == 'main' else 'main'], 'duplicate canonical owner ' + anchor)
            _require(anchor in eqs[surface], 'canonical mathematical body absent ' + anchor)
            _require(_formula(eqs[surface][anchor]) == contract['formulas'][anchor],
                     'canonical mathematical statement changed ' + anchor)
    _require(edges == 72, 'dependency edge inventory changed')
    audit_ownership(root, maps, eqs, parts)
    _require({a for r in groups.values() for a in r['anchors']} == set(contract['formulas']) and
             len(contract['formulas']) == 81, 'canonical formula inventory changed')
    for label, binding in contract['supplemental_formulas'].items():
        surface = binding['surface']
        _require(maps[surface].get(label, {}).get('path') == binding['path'] and
                 label in eqs[surface] and _formula(eqs[surface][label]) == binding['formula'],
                 'supplemental mathematical statement or owner changed ' + label)
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

    for record in contract["manual_families"]:
        _require(record["manual_path"] in manual_files and
                 manual_labels.get(record["manual_anchor"], {}).get("path") == record["manual_path"],
                 "Manual example family not rendered " + record["id"])
        for anchor in record["main_anchors"]:
            require_anchor(anchor)
        for anchor in record.get("manual_model_anchors", []):
            require_anchor(anchor, "manual")
            _require(anchor in manual_equations, "local model body absent " + anchor)
    # Check exact contract bytes after semantic diagnostics, before using any
    # source-protection entries. Deleting or rebinding an entry cannot pass.
    for name in CONTRACT_SHA256:
        _check_contract(root, name)
    m3_result = audit_m3(root, maps, eqs)
    m3_wavelet_result = audit_m3_wavelet_compaction(root, maps, eqs)
    for path, wanted in contract['frozen_sha256'].items():
        _require((root / path).is_file() and
                 hashlib.sha256((root / path).read_bytes()).hexdigest() == wanted,
                 'protected source changed ' + path)
    return {'canonical_groups': len(groups), 'canonical_equations': len(contract['formulas']),
            'supplemental_equations': len(contract['supplemental_formulas']),
            'declared_dependencies': edges,
            'unique_defining_signatures': len(contract['unique_signatures']),
            'manual_example_families': len(contract['manual_families']),
            'frozen_files': len(contract['frozen_sha256']), 'm3': m3_result,
            'm3_wavelet_compaction': m3_wavelet_result}
