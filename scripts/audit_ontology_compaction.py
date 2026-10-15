"""Rendered mathematical ownership and the reviewed R07 relocation contract.

Main is a self-contained ontology. Manual models import typed Main premises;
immutable fixture tags retain their historical spelling and resolve only via
the reviewed operation-specific bindings, never a union of document labels.
"""
from pathlib import Path
import hashlib
import json
import re


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _formula(block):
    return re.sub(r"\s+", "", re.sub(r"\\label\{[^}]+\}", "", block))


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


# Pinned reviewed bindings from the sealed R07 request; these are not inferred
# from ID ranges, historical anchor tags, or the candidate's active label sets.
REVIEWED = {'fixture_bindings': '097d31a40378cf4a0198b05fb0d6983512cc7b265f6dab3e4fa9c59117ee5958', 'anchor_moves': 'a2f048eefa63082f4a56764f04fccb848da1bcc9500aafcb156912029edebe11', 'source_anchor_bindings': 'b7638c7b3f0da21fd142c12c61dc94e6ff4d2d1aa1a48054cf915a5530c9d2ed', 'baseline_groups': '9e7ae7a93bcac5b0b9e2e9b030213d30dda4516e142895620ea5bcb7d8ba4cae', 'current_groups': 'd866324d660289d8a84b7d82d60450cf50a4edc5502450af8072c8114987b666'}


def _awareness_naming_bytes(path, data):
    # SELF names the existing target role. Reverse only this reviewed naming
    # change; full historical hashes still bind the law, schema and all cases.
    original_source = 'fa5653fa80400af24cc5eaec3ee65818bb7d817b0eccc25390b54fb29a06a03c'
    renamed_source = '6846300c020aca4af2c7fc51c0727dcd0ce7e302453e0a514904ce8aa5331d7b'
    bindings = {
        'manual/scripts/aod_awareness.py': (original_source, (
            ("            'roles':{node:('ME' if node==w.target else 'BETWEEN') for node in nodes},'outside_role':'NOT-ME'}\n",
             "            'roles':{node:('SELF' if node==w.target else 'BETWEEN') for node in nodes},'outside_role':'NOT-SELF'}\n", 1),
            ("    require(candidate in g['nodes'] and g['roles'][candidate]=='ME','I label cannot create operative participation')\n",
             "    require(candidate in g['nodes'] and g['roles'][candidate]=='SELF','I label cannot create operative participation')\n", 1),
        )),
        'evidence/m2/OPERATIVE_SELF_SCHEMA.json': (
            '9464dd36380676d4d6edf11a10c5cbad3b2c2cc73d69dbc3801acf8d85909ba4', (
                ('    "target": "ME",\n', '    "target": "SELF",\n', 1),
                ('    "unconnected": "NOT-ME",\n', '    "unconnected": "NOT-SELF",\n', 1),
            )),
        'manual/data/m2/awareness_cases.jsonl': (
            '6ac3bee0475813cc9ea3513c088d43be0e7b6d54b5c9484ccee60fd2fc7de35a', (
                ('"source_sha256":"' + original_source + '"',
                 '"source_sha256":"' + renamed_source + '"', 47),
            )),
        'evidence/m2/AWARENESS_ACTIVE_CAUSAL_SPEC.json': (
            'ffb51dbf0e63b2599a8ccde85f62aa70c2dfd69ab05758a9d6335a1ce72334af', (
                ('  "source_sha256": "' + original_source + '",\n',
                 '  "source_sha256": "' + renamed_source + '",\n', 1),
            )),
    }
    if path not in bindings:
        return data
    wanted, replacements = bindings[path]
    if hashlib.sha256(data).hexdigest() != wanted:
        for old, new, count in replacements:
            old, new = old.encode(), new.encode()
            _require(data.count(new) == count and old not in data,
                     'Awareness naming repair differs ' + path)
            data = data.replace(new, old)
    _require(hashlib.sha256(data).hexdigest() == wanted,
             'protected Awareness source or fixture changed ' + path)
    return data


def audit_relocation(root, maps, eqs, parts):
    record = json.loads((root / 'evidence/PR39_MAIN_MANUAL_RELOCATION_R07.json').read_text())
    _require(record['schema'] == 'aod.main-manual-relocation.r07', 'unknown relocation schema')
    _require(record['baseline_head'] == 'e6d3f33048ba0453b15d6ad4fdb140f3fdb3922e' and
             record['baseline_tree'] == '1b71284e2df488d985322f37ce880237d1550d86', 'relocation baseline changed')
    for key in ('fixture_bindings', 'anchor_moves'):
        _require(_json_hash(record[key]) == REVIEWED[key], 'unreviewed relocation binding: ' + key)
    spec = json.loads((root / 'evidence/m2/AWARENESS_ACTIVE_CAUSAL_SPEC.json').read_text())
    _require(hashlib.sha256((root / spec['operative_source']).read_bytes()).hexdigest() ==
             spec['source_sha256'], 'current Awareness specification source binding changed')
    _require(_json_hash(spec['source_anchor_bindings']) == REVIEWED['source_anchor_bindings'],
             'unreviewed typed scientific source binding')

    def resolve(binding):
        surface, path, label = (binding[k] for k in ('surface', 'path', 'label'))
        _require(surface in maps and maps[surface].get(label, {}).get('path') == path,
                 'inactive or wrong typed owner ' + label)
        _require(label not in maps['manual' if surface == 'main' else 'main'],
                 'duplicate cross-document owner ' + label)

    for binding in spec['source_anchor_bindings']:
        resolve(binding)
    for move in record.get('additional_anchor_moves', []):
        resolve(dict(move['new'], label=move['label']))
    for move in record['anchor_moves']:
        label = move['label']; binding = dict(move['new'], label=label)
        resolve(binding)
        if move['equation']:
            body = eqs[binding['surface']].get(label)
            _require(body is not None, 'relocated mathematical body absent ' + label)
            _require(hashlib.sha256(_formula(body).encode()).hexdigest() == move['formula_sha256'],
                     'relocated mathematical statement changed ' + label)
    fixture = root / record['fixture_path']
    fixture_bytes = _awareness_naming_bytes(record['fixture_path'], fixture.read_bytes())
    _require(record['fixture_path'] == 'manual/data/m2/awareness_cases.jsonl' and
             hashlib.sha256(fixture_bytes).hexdigest() == record['fixture_sha256'],
             'immutable fixture file changed')
    raw_rows = fixture_bytes.decode().splitlines()
    current_rows = fixture.read_text().splitlines()
    _require(len(raw_rows) == len(record['fixture_bindings']) == 47, 'fixture inventory changed')
    for raw, current_raw, binding in zip(raw_rows, current_rows, record['fixture_bindings']):
        row = json.loads(raw)
        current_row = json.loads(current_raw)
        _require(hashlib.sha256(raw.encode()).hexdigest() == binding['fixture_row_sha256'],
                 'immutable fixture row changed ' + binding['fixture_id'])
        _require((row['fixture_id'], row['main_anchor'], row['manual_anchor'], row['operation']) ==
                 (binding['fixture_id'], binding['immutable_legacy_main_anchor'],
                  binding['immutable_manual_anchor'], binding['operation']), 'fixture provenance mismatch')
        source_bytes = (root / row['source']).read_bytes()
        _require(hashlib.sha256(source_bytes).hexdigest() == current_row['source_sha256'],
                 'current fixture source binding changed')
        original_source_bytes = _awareness_naming_bytes(row['source'], source_bytes)
        _require(hashlib.sha256(original_source_bytes).hexdigest() == row['source_sha256'],
                 'fixture engine changed')
        resolve(binding['current_construct'])
        for label in binding['main_premises']:
            _require(label in eqs['main'], 'missing genuine Main premise ' + label)
        for label in binding['manual_model_equations']:
            _require(label in eqs['manual'] and label not in maps['main'],
                     'missing local Manual model ' + label)
    text = '\n'.join(t for _, t in parts['main'])
    # Stable internal keys are not rendered terminology. Do not rename them.
    prose = re.sub(r'\\(?:label|(?:eqn?|sec|app|fig|tab)?ref)\{[^}]+\}', '', text)
    for name, pattern in (
        ('Main-to-Manual dependency', r'(?i)\bmanual\b'),
        ('application procedure', r'(?i)\b(readout|ledger|cache|implementation|sensor|proprioception|mindfulness)\b'),
        ('action residual', r'r_a\s*=\s*y\s*-\s*u'),
        ('query feedback', r'q_k\s*=\s*-\s*J_k'),
        ('fixture diagnostic', r'\\delta_\{?3'),
    ):
        _require(re.search(pattern, prose) is None, 'Main concept exclusion: ' + name)
    # Formula bodies, even with new labels or renamed prose, cannot return to Main.
    main_formulas = {_formula(m.group()) for m in re.finditer(
        r'\\begin\{(equation|align|gather)(\*?)\}.*?\\end\{\1\2\}', text, re.S)}
    moved_hashes = {m['formula_sha256'] for m in record['anchor_moves'] if m['equation']}
    _require(not ({hashlib.sha256(t.encode()).hexdigest() for t in main_formulas} & moved_hashes),
             'relocated application body copied into Main')
    dep = record['dependency_correspondence']
    _require(_json_hash(dep['baseline_groups']) == REVIEWED['baseline_groups'], 'historical group obligations changed')
    _require(_json_hash(dep['current_groups']) == REVIEWED['current_groups'], 'reviewed current dependency map changed')
    original_edges = {(d, r['concept']) for r in dep['baseline_groups'] for d in r['depends_on']}
    correspondence = dep['edge_correspondence']
    _require({tuple(r['old']) for r in correspondence} == original_edges and len(correspondence) == 67,
             'historical dependency obligation omitted')
    actual_edges = {(d, r['concept']) for r in dep['current_groups'] for d in r['depends_on']}
    accounted = {tuple(e) for r in correspondence for e in r['current']} | {tuple(r['current']) for r in dep['added_edges']}
    _require(accounted == actual_edges, 'current dependency correspondence incomplete')
    return record


def audit(root, main_files, main_parts, labels, equations, manual_files, manual_labels,
          manual_parts, manual_equations):
    root = Path(root)
    contract = json.loads((root / 'evidence/ONTOLOGY_COMPACTION_BINDINGS.json').read_text())
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
    relocation = audit_relocation(root, maps, eqs, parts)
    _require(contract['ownership'] == relocation['dependency_correspondence']['current_groups'],
             'current typed ownership differs from reviewed migration')
    _require({a for r in groups.values() for a in r['anchors']} == set(contract['formulas']) and
             len(contract['formulas']) == 81, 'canonical formula inventory changed')
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
        matches = [(surface, path) for surface, path, body in definition_text
                   for match in re.finditer(record['pattern'], body)]
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
    # The registered Zenodo title and subject updates change only metadata assertions.
    # Reconstruct their original lines; every other byte keeps its frozen hash.
    metadata_expectations = {
        "tests/test_release_naming_hygiene.py": (
            ('    assert "**Alternative title:** The Art Of The Leprechaun: Fractal Calculus" in readme\n',
             '    assert "**Additional subtitle:** The Art Of The Leprechaun: Fractal Calculus" in readme\n'),
            ('    assert "**Other title:** 43 °c" in readme\n',
             '    assert "**Alternative title:** 43◦c" in readme\n'),
        ),
        "tests/test_zenodo_metadata.py": (
            ('    assert any(t.get("title") == "The Art Of The Leprechaun: Fractal Calculus – 𝔖" and t.get("type", {}).get("id") == "alternative-title" for t in data.get("additional_titles", []))\n',
             '    assert any(t.get("title") == "The Art Of The Leprechaun: Fractal Calculus – 𝔖" and t.get("type", {}).get("id") == "subtitle" for t in data.get("additional_titles", []))\n'),
            ('    assert any(t.get("title") == "43 °c" and t.get("type", {}).get("id") == "other" for t in data.get("additional_titles", []))\n',
             '    assert any(t.get("title") == "43◦c" and t.get("type", {}).get("id") == "alternative-title" for t in data.get("additional_titles", []))\n'),
            (
                '    assert data["keywords"] == [\n'
                '        "axiomatic fundamentalism", "AFC", "AOD", "Stokes", "cut calculus",\n'
                '        "temporal dynamics", "AΩD", "math-ph", "math-lo"\n'
                '    ]\n',
                '    assert data["keywords"] == [\n'
                '        "computational calculus", "axiomatic fundamentalism", "AFC",\n'
                '        "AOD", "Stokes", "cut calculus", "temporal dynamics", "AΩD",\n'
                '        "math-ph", "math-lo",\n'
                '        "discrete Stokes calculus", "graph combinatorics", "certified closure",\n'
                '        "discrete recurrence", "relational time", "finite Fourier representation",\n'
                '        "Awareness", "computational intelligence", "persistent learning", "proprioceptive action-return models",\n'
                '        "physical observable maps", "exact rational simulation", "Declared Edge Computation"\n'
                '    ]\n'
                '    assert data["subjects"] == [\n'
                '        {"term": "Mathematical Physics", "identifier": "https://arxiv.org/list/math-ph/recent", "scheme": "url"},\n'
                '        {"term": "Logic", "identifier": "https://arxiv.org/list/math.LO/recent", "scheme": "url"},\n'
                '        {"term": "Combinatorics", "identifier": "https://arxiv.org/list/math.CO/recent", "scheme": "url"},\n'
                '        {"term": "Discrete Mathematics", "identifier": "https://arxiv.org/list/cs.DM/recent", "scheme": "url"},\n'
                '        {"term": "Artificial Intelligence", "identifier": "https://arxiv.org/list/cs.AI/recent", "scheme": "url"},\n'
                '        {"term": "Neural and Evolutionary Computing", "identifier": "https://arxiv.org/list/cs.NE/recent", "scheme": "url"}\n'
                '    ]\n',
            ),
        ),
    }
    # Reverse only the reviewed output-format/provenance repairs; the full
    # original hash still binds every calculation, constant and input byte.
    presentation_expectations = {
        "tests/test_manual_table_grammar_release_polish.py": (
            ('    assert "formula" not in text\n',
             '    target_table = text.split(r"\\caption{Measured rest-energy target records.}", 1)[1].split(r"\\end{table}", 1)[0]\n'
             '    assert "formula" not in target_table\n'),
            ('    assert "Record & Target [MeV]" in text\n',
             '    assert "Record & Target [MeV]" in target_table\n'),
        ),
        "tests/test_sparc_script_release_neutral.py": (
            ('    assert "Controls are declared comparison variants from the current diagnostic run." in text\n',
             '    assert "Carried frozen comparison records; variant recipes and aggregation provenance" in text\n    assert "are not supplied. These values are not computed by this script." in text\n'),
        ),
        "preamble.tex": (
            ('  pdfsubject={The Hidden Temporal Dynamics of Stokes; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD temporal dynamics, boundary accounting, finite simulation fixtures, data-support classes, scoped error},\n',
             '  pdfsubject={The Hidden Temporal Dynamics of Stokes; The Art Of The Leprechaun: Fractal Calculus; AFC/AOD temporal dynamics, ontology, certified closure, discrete recurrence, relational time, finite Fourier representation, Awareness},\n'),
            ('  pdfkeywords={Axiomatic Fundamentalism, AFC, AOD, AΩD, Stokes, SADAR, boundary accounting, data-support classes, scoped error, finite simulation fixtures}\n',
             '  pdfkeywords={Axiomatic Fundamentalism, AFC, AOD, AΩD, Stokes, SADAR, ontology, certified closure, discrete recurrence, relational time, finite Fourier representation, Awareness}\n'),
        ),
        "scripts/generate_field_dynamics_layered.py": (
            ('"""Generate the Layered Field Dynamics figure with AΩD structural labels."""\n',
             '"""Generate the Layered Field Dynamics figure with AΩD structural labels."""\nimport argparse\nfrom pathlib import Path\n\n'),
            ("GRAY = '#b9c2cc'\n",
             "GRAY = '#b9c2cc'\n\nparser = argparse.ArgumentParser(description=__doc__)\nparser.add_argument('--main', action='store_true',\n                    help='omit the Manual-owned storage callout and capacity inset')\nparser.add_argument('--output', type=Path,\n                    help='PNG destination (defaults to the selected figure mode)')\nargs = parser.parse_args()\noutput = args.output or Path(\n    'figures_jpg/field_dynamics_layered_main.png' if args.main\n    else 'figures_jpg/field_dynamics_layered.png')\n"),
            ("callout('channel capacity\\nradial channels store,\\nbuffer, and transfer support', (-0.74,-0.53), (-1.18,-0.82))\n",
             "if not args.main:\n    callout('channel capacity\\nradial channels store,\\nbuffer, and transfer support', (-0.74,-0.53), (-1.18,-0.82))\n"),
            ('for y, title, lines in [\n',
             'insets = [\n'),
            ("    (-0.33, 'B. RADIAL CHANNEL /\\nCAPACITY VIEW', ['channels provide', 'capacity, buffering,', 'and transfer'])]:\n",
             "    (-0.33, 'B. RADIAL CHANNEL /\\nCAPACITY VIEW', ['channels provide', 'capacity, buffering,', 'and transfer'])]\nfor y, title, lines in insets[:1] if args.main else insets:\n"),
            ("fig.savefig('figures_jpg/field_dynamics_layered.png', dpi=150, bbox_inches='tight')\n",
             "fig.savefig(output, dpi=150, bbox_inches='tight')\n"),
        ),
        "manual/scripts/score_sparc_field_dynamics.py": (
            ('lines.append(r"\\caption{SPARC five-galaxy scored records.}")',
             'lines.append(r"\\caption{SPARC five-galaxy scored records. Data-support class is G0 for this radial shell projection lane; the uncertainty policy is observation-only in this release.}")'),
            ('lines.append(r"\\begin{tabular}{lrrrrr}")',
             'lines.append(r"\\begin{tabular}{lccrrrrr}")'),
            ('lines.append(r"$G$ & $N$ & $\\chi^2_U$ & $MAE_U$ & $MSE_U$ & $MAPE_U$ [\\%]\\\\")',
             'lines.append(r"$G$ & Class & $\\sigma$ policy & $N$ & $\\chi^2_U$ & $MAE_U$ & $MSE_U$ & $MAPE_U$ [\\%]\\\\")'),
            ('f"{row[\'galaxy\']} & {int(row[\'N\'])} & {row[\'chi2_U\']:.2f} & {row[\'MAE_U\']:.1f} & {row[\'MSE_U\']:.1f} & {row[\'MAPE_U\']:.2f}',
             'f"{row[\'galaxy\']} & G0 & obs-only & {int(row[\'N\'])} & {row[\'chi2_U\']:.2f} & {row[\'MAE_U\']:.1f} & {row[\'MSE_U\']:.1f} & {row[\'MAPE_U\']:.2f}'),
            ('# Controls are declared comparison variants from the current diagnostic run.',
             '# Carried frozen comparison records; variant recipes and aggregation provenance\n    # are not supplied. These values are not computed by this script.'),
        ),
    }
    for path, wanted in contract["frozen_sha256"].items():
        data = _awareness_naming_bytes(path, (root / path).read_bytes())
        if path in metadata_expectations and hashlib.sha256(data).hexdigest() != wanted:
            for old, new in metadata_expectations[path]:
                old, new = old.encode(), new.encode()
                _require(data.count(new) == 1 and old not in data,
                         "metadata assertion rebase differs " + path)
                data = data.replace(new, old, 1)
        if path in presentation_expectations and hashlib.sha256(data).hexdigest() != wanted:
            for old, new in presentation_expectations[path]:
                old, new = old.encode(), new.encode()
                _require(data.count(new) == 1,
                         "presentation repair differs " + path)
                data = data.replace(new, old, 1)
        if path == "evidence/m2/AWARENESS_ACTIVE_CAUSAL_SPEC.json":
            # Preserve the original byte contract on all scientific fields;
            # the separately pinned typed relocation field is the sole addition.
            original = json.loads(data)
            del original["source_anchor_bindings"]
            data = (json.dumps(original, indent=2) + "\n").encode()
        if path == "sections/01_abstract.tex":
            # Reconstruct only the owner-authorized final sentence deletion.
            removed = (" The core note gives the calculus; the manual carries the downstream finite simulations, "
                       "exact fixtures, diagnostics, observable maps, external comparisons, and setup-error audits.")
            text = data.decode()
            _require(removed not in text, "obsolete abstract routing sentence")
            data = text.replace("\n\\end{abstract}", removed + "\n\\end{abstract}", 1).encode()
        _require(hashlib.sha256(data).hexdigest() == wanted,
                 "protected engine, input, test or presentation changed " + path)
    _require(not (root / "sections/02_introduction.tex").exists(),
             "obsolete introduction restored")
    return {"canonical_groups": len(groups), "canonical_equations": len(contract["formulas"]),
            "ordered_dependencies": edges, "refined_first_uses": len(contract["first_uses"]),
            "unique_defining_signatures": len(contract["unique_signatures"]),
            "appendices": 10, "local_provenance_repairs": len(contract["navigation"]),
            "manual_example_families": len(contract["manual_families"]),
            "frozen_files": len(contract["frozen_sha256"])}
