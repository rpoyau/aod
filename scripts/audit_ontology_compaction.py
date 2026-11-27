"""Current mathematical ownership, fixture provenance and protected source bytes.

Canonical scientific authority lives in typst/ (Typst primary publication).
Historical mathematical formula strings and SHA-256 digests in contracts remain
untouched and are verified against the immutable historical baseline snapshot
(archive/latex_baseline_98ddfa0/), while live canonical Typst equations (and
generated latex/ compatibility equations when present) are verified for exact
semantic math AST equivalence against those bound statements.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
from functools import lru_cache


CONTRACT_ROOT = 'contracts/scientific/'
# These independent byte bindings are reviewed with the checker. Loading a
# modified contract never changes an expected digest or authorizes new sources.
CONTRACT_SHA256 = {
    "TEMPORAL_METROLOGY.json": "a81b261fca3be6202a1fb02d6334e60751b25d1e0c9ff5ef89bb50ba44145da9",
    "TEMPORAL_OBSERVATION.json": "b02344dcaa98c3de1b7453d868b332b2bd537f08c9c2e92de048e337c6747e69",
    "MAP_CONTRACT.json": "3d6766979397c7732e6cd88793cf6befb9fa48fa69267598cfcf0d781a300aea",
    "CELL_MAPPING_MATHEMATICAL_BINDINGS.json": "541cdd9ab197a79c7dc65fd7008a44e2abecaa178f0126817ac4a9b5bf228698",
    "M3_WAVELET_COMPACTION_BINDINGS.json": "95838de7e91afc8a2f03ff32b9795682136fd205c2ce584419249efd68d07415",
    "ERROR_BUDGET.json": "8ea33dabcf681e01d459f170b31c10b59fdf9e63ea708c64ac6ed7c1be62a57f",
    "CELL_MEASURE_SPEC.json": "3c3e495357606a73a9bb2a142ec08dd102472eaf455a74e4626960e464ca61c2",
    "AWARENESS_ACTIVE_CAUSAL_SPEC.json": "ad365ac80b4fcc0fc46ceacc76e736fd80941109d85d7f953b02bd54a7b40b54",
    "CANONICAL_BINDINGS.json": "a6038a976955e9b37198aaaef42ba0f4eee6fd2fc3a4a360217201e6ab413067",
    "FOURIER_SCOPE.md": "8cc902c9fd4b7aceb8cb67f4345059eec752bbe0d04e3c2dc79c2fcf36a577e1",
    "HISTORICAL_TOY_SOURCE_STATUS.csv": "dc0f1b94afc71f930929e64caef8d9f9cb49386035706aa2b79b8b9cc0de42d4",
    "METROLOGY_BOUNDARY.md": "553609db18f523faae6d2a53c3465c56ceb9034c6ba1ae3b7a6cff77fdf678af",
    "OPERATIVE_SELF_SCHEMA.json": "0fba87a85c542a5a9b74f2242724bf334ecb1a0c39886a20c9298309d3005ecd",
    "OWNERSHIP_AND_FIXTURES.json": "a1a9101b5ed232c94f375cb272dbb535fa4fb15f1205b7f975a0f3e8d75d504a",
    "README.md": "7ea9622a9bdd4e01172f66eebe59c0d0e60cd31a234933b721cac352f6b01016",
    "ROUND_TRIP_PHASE_FACTOR_SPEC.json": "9d704b35c510d3f3d932a4856bbc59195eb0aec23929307ec16e22ca3f4d4c28",
    "UPDATE_CAUSAL_ORDER.md": "879fe4fce9ec09b8640ca31eea28c09a3a6d2047f6d58eeafe463ece055315bd",
}

TYPST_SIGNATURE_PATTERNS = {
    'eq:null-axiom': r'x=Null',
    'eq:atomic-h1': r'E\(Qfour\)(?::=|=)',
    'eq:monon-cycle': r'upright\("Monon"\)\(x\)(?::=|=)',
    'eq:closure-phase': r'DeltaPhi\(C\)(?::=|=)1_C',
    'eq:wave-identity': r'W\^\(upright\("id"\)\)_\(B,i\)(?::=|=)',
    'eq:field-organization': r'F_\(B,lambda\)(?:bar\.v_k)?(?::=|=)',
    'eq:relational-time': r'op\("RT"\)_\(I,B\)\(omega\)&?(?::=|=)',
    'eq:awareness-state-factorization': r'S_k\^\(\+\)(?::=|=)',
    'eq:awareness-active': r'op\("Op"\)\^\(O,H\)_e\(S_k\^\(\+\)\)=1quadarrow\.l\.r\.double\.long',
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _formula(block):
    return re.sub(r"\s+", "", re.sub(r"\\label\{[^}]+\}", "", block))


@lru_cache(maxsize=1)
def _load_sources_mod():
    path = Path(__file__).resolve().parent / 'audit_scientific_sources.py'
    spec = importlib.util.spec_from_file_location('aod_compaction_sources_helper', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _baseline_eqs(root):
    src = _load_sources_mod()
    return {
        'main': src.baseline_equations(root, 'main'),
        'manual': src.baseline_equations(root, 'manual'),
    }


def _check_equation_matches_contract(root, base_eqs, surface, label, live_body, *, expected_formula=None, expected_sha256=None, err_msg):
    """Verify baseline equation matches contract exactly and live Typst equation matches baseline AST."""
    src = _load_sources_mod()
    base_body = base_eqs[surface].get(label)
    _require(base_body is not None, err_msg)
    if expected_formula is not None:
        _require(_formula(base_body) == expected_formula, err_msg)
    if expected_sha256 is not None:
        _require(hashlib.sha256(_formula(base_body).encode()).hexdigest() == expected_sha256, err_msg)
    try:
        live_ast = src.math_ast_of_block(live_body)
        base_ast = src.math_ast_from_tex(base_body)
    except ValueError:
        raise ValueError(err_msg)
    _require(live_ast == base_ast, err_msg)


def _strip_typst_floats(text):
    out = []
    i = 0; n = len(text)
    while i < n:
        if text.startswith('#figure(', i):
            d = 0; j = i + 7
            while j < n:
                if text[j] == '\\' and j + 1 < n:
                    j += 2; continue
                if text[j] == '"':
                    j += 1
                    while j < n and text[j] != '"':
                        j += 2 if text[j] == '\\' else 1
                    j += 1; continue
                if text[j] == '(':
                    d += 1
                elif text[j] == ')':
                    d -= 1
                    if d == 0:
                        j += 1; break
                j += 1
            i = j; continue
        if text.startswith('#aod-uncaptioned-longtable[', i):
            d = 0; j = i + len('#aod-uncaptioned-longtable')
            while j < n:
                if text[j] == '\\' and j + 1 < n:
                    j += 2; continue
                if text[j] == '[':
                    d += 1
                elif text[j] == ']':
                    d -= 1
                    if d == 0:
                        j += 1; break
                j += 1
            i = j; continue
        out.append(text[i]); i += 1
    return ''.join(out)


def _check_contract(root, name):
    data = (root / CONTRACT_ROOT / name).read_bytes()
    _require(hashlib.sha256(data).hexdigest() == CONTRACT_SHA256[name],
             'scientific contract integrity changed ' + name)
    return data


def audit_ownership(root, maps, eqs, parts, base_eqs=None):
    base_eqs = _baseline_eqs(root) if base_eqs is None else base_eqs
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
            _check_equation_matches_contract(
                root, base_eqs, binding['surface'], binding['label'], body,
                expected_sha256=binding['formula_sha256'],
                err_msg='owned mathematical statement changed ' + binding['label'],
            )
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


def audit_m3(root, maps, eqs, base_eqs=None):
    """Check the explicit additional mathematics without changing old duties."""
    base_eqs = _baseline_eqs(root) if base_eqs is None else base_eqs
    record = json.loads(_check_contract(root, 'CELL_MAPPING_MATHEMATICAL_BINDINGS.json'))
    _require(record['schema'] == 'aod.scientific.m3-mathematics.v1',
             'unknown M3 mathematical binding schema')
    paths = {'main': 'typst/sections/07_cell_measures_mappings.typ',
             'manual': 'typst/manual/sections/01_cell_measures.typ'}
    _require(set(record['sources']) == set(paths.values()),
             'M3 mathematical source inventory changed')
    _require(len(record['equations']) == 7, 'M3 equation inventory changed')
    for label, binding in record['equations'].items():
        surface = binding.get('surface', 'main')
        _require(surface in paths and binding['path'] == paths[surface] and
                 maps[surface].get(label, {}).get('path') == binding['path'] and
                 label not in maps['manual' if surface == 'main' else 'main'] and
                 label in eqs[surface],
                 'M3 mathematical statement or owner changed ' + label)
        _check_equation_matches_contract(
            root, base_eqs, surface, label, eqs[surface][label],
            expected_formula=binding['formula'],
            err_msg='M3 mathematical statement or owner changed ' + label,
        )
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


def audit_m3_wavelet_compaction(root, maps, eqs, base_eqs=None):
    """Check additive Phase 1 wavelet-compaction and conditional SI bindings."""
    base_eqs = _baseline_eqs(root) if base_eqs is None else base_eqs
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
                 label in eqs['main'],
                 'M3 wavelet compaction statement or owner changed ' + label)
        _check_equation_matches_contract(
            root, base_eqs, 'main', label, eqs['main'][label],
            expected_formula=binding['formula'],
            err_msg='M3 wavelet compaction statement or owner changed ' + label,
        )
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
    base_eqs = _baseline_eqs(root)
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
    for name in CONTRACT_SHA256:
        _check_contract(root, name)
    for row in groups.values():
        surface = row['surface']
        for anchor in row['anchors']:
            _check_equation_matches_contract(
                root, base_eqs, surface, anchor, eqs[surface][anchor],
                expected_formula=contract['formulas'][anchor],
                err_msg='canonical mathematical statement changed ' + anchor,
            )
    _require(edges == 72, 'dependency edge inventory changed')
    audit_ownership(root, maps, eqs, parts, base_eqs=base_eqs)
    _require({a for r in groups.values() for a in r['anchors']} == set(contract['formulas']) and
             len(contract['formulas']) == 81, 'canonical formula inventory changed')
    for label, binding in contract['supplemental_formulas'].items():
        surface = binding['surface']
        _require(maps[surface].get(label, {}).get('path') == binding['path'] and label in eqs[surface],
                 'supplemental mathematical statement or owner changed ' + label)
        _check_equation_matches_contract(
            root, base_eqs, surface, label, eqs[surface][label],
            expected_formula=binding['formula'],
            err_msg='supplemental mathematical statement or owner changed ' + label,
        )

    # Check unique defining signatures across canonical Typst bodies (excluding figures/tables)
    definition_text = []
    for surface in ('main', 'manual'):
        for path, text in parts[surface]:
            if path.endswith('.typ'):
                body = _strip_typst_floats(text)
            else:
                body = re.sub(r'\\begin\{(figure\*?|table\*?|longtable)\}.*?\\end\{\1\}', '', text, flags=re.S)
            definition_text.append((surface, path, re.sub(r'\s+', '', body)))
    for record in contract['unique_signatures']:
        is_typ = record['path'].endswith('.typ')
        pattern = TYPST_SIGNATURE_PATTERNS[record['anchor']] if is_typ else record['pattern']
        matches = [(surface, path) for surface, path, body in definition_text
                   for _ in re.finditer(pattern, body)]
        _require(matches == [(record['surface'], record['path'])],
                 'competing or absent canonical binding ' + record['anchor'])

    # Also verify generated latex/ compatibility formulas & unique signatures when present
    if (root / 'latex' / 'main.tex').is_file() and (root / 'latex' / 'manual' / 'main.tex').is_file():
        src = _load_sources_mod()
        l_eqs = {'main': src.latex_equations(root, 'main'), 'manual': src.latex_equations(root, 'manual')}
        for row in groups.values():
            surface = row['surface']
            for anchor in row['anchors']:
                _require(anchor in l_eqs[surface], 'generated LaTeX missing canonical equation ' + anchor)
                _check_equation_matches_contract(
                    root, base_eqs, surface, anchor, l_eqs[surface][anchor],
                    expected_formula=contract['formulas'][anchor],
                    err_msg='generated LaTeX canonical mathematical statement changed ' + anchor,
                )

    for record in contract["manual_families"]:
        _require(record["manual_path"] in manual_files and
                 manual_labels.get(record["manual_anchor"], {}).get("path") == record["manual_path"],
                 "Manual example family not rendered " + record["id"])
        for anchor in record["main_anchors"]:
            require_anchor(anchor)
        for anchor in record.get("manual_model_anchors", []):
            require_anchor(anchor, "manual")
            _require(anchor in manual_equations, "local model body absent " + anchor)

    for name in CONTRACT_SHA256:
        _check_contract(root, name)
    m3_result = audit_m3(root, maps, eqs, base_eqs=base_eqs)
    m3_wavelet_result = audit_m3_wavelet_compaction(root, maps, eqs, base_eqs=base_eqs)
    for path, wanted in contract['frozen_sha256'].items():
        _require((root / path).is_file() and
                 hashlib.sha256((root / path).read_bytes()).hexdigest() == wanted,
                 'protected source changed ' + path)
    return {
        'canonical_groups': len(groups),
        'canonical_equations': len(contract['formulas']),
        'supplemental_equations': len(contract['supplemental_formulas']),
        'declared_dependencies': edges,
        'unique_defining_signatures': len(contract['unique_signatures']),
        'manual_example_families': len(contract['manual_families']),
        'frozen_files': len(contract['frozen_sha256']),
        'm3': m3_result,
        'm3_wavelet_compaction': m3_wavelet_result,
    }
