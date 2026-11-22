"""Rendered-source and semantic bindings used by the candidate's own suite.

Canonical scientific authority lives under typst/ (Typst primary publication).
Generated LaTeX compatibility output under latex/ is verified as a derivative
surface with the same semantic obligations, and actual_build checks TeX
recorder/aux/log output from a bibliography-complete XeLaTeX build. Files
outside the active include graph cannot satisfy a canonical scientific
obligation.
"""
from pathlib import Path
import argparse, csv, hashlib, importlib.util, json, re
from functools import lru_cache

MAIN_REQUIRED = (
    'typst/sections/03_afc_basis.typ',
    'typst/sections/04_cut_running_fractal_tesseract.typ',
    'typst/sections/05_curl_closure_duon_current.typ',
    'typst/sections/06_wave_state_relational_time.typ',
    'typst/sections/06_field.typ',
    'typst/appendices/A_fractal_address_bip_biz.typ',
    'typst/appendices/B_curling_curls.typ',
    'typst/appendices/C_stochastic_crowning.typ',
    'typst/appendices/D_cycle_shedding_demonstration.typ',
    'typst/appendices/E_glossary.typ',
    'typst/appendices/F_wave.typ',
    'typst/appendices/G_symbolic_cancellation_check.typ',
    'typst/appendices/H_combinatorics_rd_tests.typ',
    'typst/appendices/I_path_complexity_prototype_quarantine.typ',
    'typst/appendices/J_ao_field_fractal_properties.typ',
)
MANUAL_REQUIRED = (
    'typst/manual/sections/00_scope.typ',
    'typst/manual/sections/00_native_closure_wave_temporal_fixtures.typ',
)
CANONICAL_EQUATIONS = {
    'eq:cumulative-closure-counts': r'\mathrm{bip}^{\le}_i(k)=\max(N_i^C(k)-1,0)',
    'eq:closure-phase-window': r'\mathbf1_{\{u<k_0\le v\}}',
    'eq:crown-advance': r'\operatorname{Adv}_k(h_k^+)=x_{k+1}^0',
    'eq:null-axiom': r'x=\Null,\qquadx=x,\qquad\Null\equiv\infD.',
    'eq:closure-phase-step-count': r'm(C):=\#\{\text{committed phase-bearing traversals in }\Gamma_C\}\ge2',
    'eq:closure-phase': r'\Delta\Phi(C)=1_C.',
    'eq:hinge-grammar': r'M_{\varepsilon,m}=\varepsilon\,0_H(0_D)^m(-\varepsilon)',
    'eq:atomic-h1': r'E(\Qfour)=\{(u,v):d_H(u,v)=1\}',
    'eq:hinge-reflection-involution': r'\iota^2=\mathrm{id}',
    'eq:field-organization': r'F_{B,\lambda}|_k=(B,\lambda,I_B(k),\{W^{\mathrm{id}}_{B,i}\}_{i\in I_B(k)})',
    'eq:motif-grammar': r'\mathrm{Dimonon}=2\,\mathrm{Monon}\ne\mathrm{Dion}',
    'eq:phase-unit-embedding': r'\iota_{\mathrm{ref}}(n1_C)=2nh',
    'eq:reflected-leg-bound': r'(n_{\rightarrow}+n_{\leftarrow})h\ge2\Delta\phi_{\rm step}=2h=\iota_{\mathrm{ref}}(1_C)',
    'eq:minimal-phase-quantum-bound': r'2\Delta\phi_{\rm step}\ge1_C',
    'eq:equal-leg-factorization': r'\delta\phi^{\rightarrow}=\delta\phi^{\leftarrow}=\delta\phi',
    'eq:rcd-coupling': r'\RCD_{ij}(B)=RD_B(C_{ij})\bowtie_B R^{\mathrm{asym}}_{ij}(B)',
    'eq:rcd-additive-realization': r'\operatorname{dur}_{+}(RD\bowtie(r_s)_s)=RD+\sum_s r_s',
    'eq:window-clipped-rho': r'\operatorname{Compat}_{\mathcal D}(\rho^D_{ij},|\omega|^{\mathcal D}_{ij})',
    'eq:cadence-ratio': r'\frac{\Delta\operatorname{bip}_i(\omega)}{\Delta\operatorname{bip}_j(\omega)}',
    'eq:flux-types': r'\phi^{\mathrm{AFC}}_{ij}=p_i^{\mathrm{mem}}P_{ij}-p_j^{\mathrm{mem}}P_{ji}',
    'eq:causal-update': r'S^W_{F,k+1}=\mathcal U^{\SADAR}_B(S^W_{\le k},S^\times_{\le k},\mathbf A_{F,\le k})',
    'eq:fourier-transform': r'\widehat v(\chi)=\frac1N\sum_{g\in G}v(g)\overline{\chi(g)}',
    'eq:fourier-convolution-product': r'\widehat{v*w}(\chi)=N\widehat v(\chi)\widehat w(\chi)',
    'eq:fourier-parseval': r'\frac1N\sum_g|v(g)|^2=\sum_\chi|\widehat v(\chi)|^2',
    'eq:fourier-recurrence-support': r'\operatorname{supp}\widehat v\subseteq H^\perp',
}
REQUIRED_LABELS = (
    'eq:first-anchor', 'eq:closure-certificate', 'eq:closure-trace', 'eq:return-identity',
    'eq:beat-reclosure', 'eq:wave-identity', 'eq:motif-admission', 'eq:fold-outer-closure', 'eq:expose-inner-lineage',
    'eq:complete-wave-state', 'eq:wave-update-trace', 'eq:coupling-trace', 'eq:relational-time',
    'eq:afc-stokes-used', 'eq:branch-hinge-rd', 'eq:frg-admission-order', 'eq:frg-identity',
    'eq:fourier-inversion', 'eq:fourier-orthogonality', 'eq:fourier-linearity',
    'eq:fourier-shift-modulation', 'eq:fourier-correlation-power', 'eq:fourier-real-symmetry',
    'eq:fourier-running-standing', 'eq:fourier-product-factorization',
)

SCIENTIFIC_CONTRACT_SCHEMAS = {
    'CANONICAL_BINDINGS.json': 'aod.scientific.canonical.v1',
    'OWNERSHIP_AND_FIXTURES.json': 'aod.scientific.ownership-fixtures.v1',
    'AWARENESS_ACTIVE_CAUSAL_SPEC.json': 'aod.awareness.active.r04',
    'OPERATIVE_SELF_SCHEMA.json': 'aod.operative.self.r04',
    'ROUND_TRIP_PHASE_FACTOR_SPEC.json': 'aod.scientific.round-trip-phase-factor.v1',
    'CELL_MEASURE_SPEC.json': 'aod.scientific.cell-measure.v1',
    'MAP_CONTRACT.json': 'aod.scientific.map-contract.v2',
    'ERROR_BUDGET.json': 'aod.scientific.error-budget.v2',
    'CELL_MAPPING_MATHEMATICAL_BINDINGS.json': 'aod.scientific.m3-mathematics.v1',
    'TEMPORAL_OBSERVATION.json': 'aod_temporal_observation_v1',
    'TEMPORAL_METROLOGY.json': 'aod.scientific.temporal-metrology.v1',
    'M3_WAVELET_COMPACTION_BINDINGS.json': 'aod.scientific.m3-wavelet-compaction.v1',
}
SCIENTIFIC_SCOPE_FILES = {
    'README.md', 'FOURIER_SCOPE.md', 'METROLOGY_BOUNDARY.md',
    'UPDATE_CAUSAL_ORDER.md', 'HISTORICAL_TOY_SOURCE_STATUS.csv',
}
SCIENTIFIC_SOURCE_SPECS = ('AWARENESS_ACTIVE_CAUSAL_SPEC.json',)
BASELINE_SNAPSHOT_REL = Path('archive/latex_baseline_98ddfa0')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


@lru_cache(maxsize=1)
def _load_math_ast_module():
    path = Path(__file__).resolve().parent / 'verify_typst_parity.py'
    spec = importlib.util.spec_from_file_location('aod_audit_math_ast', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def math_ast_from_tex(tex_block):
    vtp = _load_math_ast_module()
    inner = re.sub(
        r'\\begin\{(equation|align|gather|aligned|gathered)\*?\}|\\end\{(equation|align|gather|aligned|gathered)\*?\}',
        '', tex_block,
    )
    inner = re.sub(r'\\label\{[^}]+\}|\\tag\{[^}]+\}|\\nonumber\b|\\notag\b', '', inner)
    ast, unsup = vtp.parse_tex_math_ast(inner)
    if unsup:
        raise ValueError('Unsupported TeX math token in semantic audit: ' + str(unsup[:3]))
    return ast


def math_ast_from_typst(typst_block):
    vtp = _load_math_ast_module()
    body = typst_block.strip()
    m_tag = re.match(r'^#tagged-eq\(\s*"[^"]+"\s*,\s*\$(.*)\$\s*,\s*<[^>]+>\s*\)$', body, re.S)
    if m_tag:
        inner = m_tag.group(1)
    else:
        m_disp = re.match(r'^\$(.*)\$(?:\s*<[^>]+>)?$', body, re.S)
        inner = m_disp.group(1) if m_disp else body
    ast, unsup = vtp.parse_typst_math_ast(inner)
    if unsup:
        raise ValueError('Unsupported Typst math token in semantic audit: ' + str(unsup[:3]))
    return ast


def math_ast_of_block(block):
    s = block.strip()
    if s.startswith(r'\begin{') or s.startswith(r'\[') or r'\label{' in s:
        return math_ast_from_tex(s)
    return math_ast_from_typst(s)


def validate_contract_inventory(root):
    """Select only the complete, explicitly registered current contracts.

    Unknown files in the contract namespace fail regardless of their schema.
    Elsewhere, scientific-specification fields/names cannot silently establish
    an alternative authority. Transient run reports are a separate protocol.
    """
    root = Path(root).resolve()
    folder = root / 'contracts/scientific'
    expected = set(SCIENTIFIC_CONTRACT_SCHEMAS) | SCIENTIFIC_SCOPE_FILES
    paths = list(folder.rglob('*'))
    actual = {path.relative_to(folder).as_posix() for path in paths
              if path.is_file() or path.is_symlink()}
    if actual != expected:
        raise ValueError('Scientific contract inventory mismatch; missing=' + str(sorted(expected - actual))
                         + '; unregistered=' + str(sorted(actual - expected)))
    if any(path.is_symlink() for path in [root / 'contracts', folder, *paths]):
        raise ValueError('Scientific contracts cannot be symlinks')
    records = {}
    for name, schema in SCIENTIFIC_CONTRACT_SCHEMAS.items():
        record = json.loads((folder / name).read_text())
        if not isinstance(record, dict) or record.get('schema') != schema:
            raise ValueError('Scientific contract schema mismatch: ' + name)
        records[name] = record
    registered = {folder / name for name in SCIENTIFIC_CONTRACT_SCHEMAS}
    fields = {'operative_source', 'source_anchors', 'source_anchor_bindings'}
    for path in root.rglob('*.json'):
        if path in registered or any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        if path.name.endswith(('_SPEC.json', '_SCHEMA.json')):
            raise ValueError('Unregistered scientific specification: ' + path.relative_to(root).as_posix())
        try:
            record = json.loads(path.read_text())
        except (ValueError, UnicodeError):
            continue
        if not isinstance(record, dict):
            continue
        schema = record.get('schema', '')
        is_scientific = (bool(fields.intersection(record))
                         or (isinstance(schema, str) and schema.startswith(
                             ('aod.scientific.', 'aod.awareness.', 'aod.operative.'))))
        if is_scientific:
            raise ValueError('Unregistered scientific specification: ' + path.relative_to(root).as_posix())
    return records


def validate_active_specifications(root, records=None):
    root = Path(root).resolve()
    records = validate_contract_inventory(root) if records is None else records
    maps = {surface: label_map(root, surface) for surface in ('main', 'manual')}
    checked = []
    for name in SCIENTIFIC_SOURCE_SPECS:
        record = records[name]
        required = {'operative_source', 'source_sha256', 'source_anchors', 'source_anchor_bindings'}
        if not required <= record.keys():
            raise ValueError('Incomplete active scientific source binding: ' + name)
        relative = record['operative_source']
        if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('Unsafe active scientific source: ' + name)
        source = root / relative
        if not source.is_file() or record['source_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError('Active scientific source hash mismatch: ' + name)
        anchors = record['source_anchors']
        if not isinstance(anchors, list) or not anchors or len(anchors) != len(set(anchors)):
            raise ValueError('Invalid active scientific source anchors: ' + name)
        bindings = record['source_anchor_bindings']
        if [binding['label'] for binding in bindings] != anchors:
            raise ValueError('Active scientific source anchor inventory mismatch: ' + name)
        for binding in bindings:
            if maps.get(binding['surface'], {}).get(binding['label'], {}).get('path') != binding['path']:
                raise ValueError('Active scientific source anchor ownership mismatch: ' + name)
        checked.append('contracts/scientific/' + name)
    return checked


# ---------------------------------------------------------------------------
# TeX source helpers (used for generated latex/, baseline snapshot, and mini TeX controls)
# ---------------------------------------------------------------------------

def clean(text):
    return re.sub(r'(?<!\\)%[^\n]*', '', text)


def visible(text):
    text = clean(text); stack = [True]; result = []; pos = 0
    for m in re.finditer(r'\\(iftrue|iffalse|else|fi)\b', text):
        if all(stack):
            result.append(text[pos:m.start()])
        token = m[1]
        if token.startswith('if'):
            stack.append(token == 'iftrue')
        elif token == 'else':
            if len(stack) == 1:
                raise ValueError('unbound TeX else')
            stack[-1] = not stack[-1]
        else:
            if len(stack) == 1:
                raise ValueError('unbound TeX fi')
            stack.pop()
        pos = m.end()
    if all(stack):
        result.append(text[pos:])
    if len(stack) != 1:
        raise ValueError('unclosed TeX conditional')
    return ''.join(result)


def _tex_include_graph(tex_root, surface='main', *, rel_base=None):
    tex_root = Path(tex_root).resolve()
    rel_base = tex_root if rel_base is None else Path(rel_base).resolve()
    cwd = tex_root if surface == 'main' else tex_root / 'manual'
    seen = []; stack = []; pieces = []

    def visit(p):
        p = p.resolve()
        if p in stack:
            raise ValueError('recursive TeX include')
        if not p.is_relative_to(tex_root):
            raise ValueError('include outside source tree')
        if not p.exists():
            raise ValueError('missing include ' + str(p))
        stack.append(p)
        rel = p.relative_to(rel_base).as_posix()
        seen.append(rel)
        txt = visible(p.read_text(encoding='utf-8'))
        pieces.append((rel, txt))
        for match in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}', txt):
            arg = match[1]
            if any(s in arg for s in ('#', '\\')):
                raise ValueError('ACTUAL_BUILD_VERIFICATION_REQUIRED: dynamic include')
            child = cwd / arg
            if not child.suffix:
                child = child.with_suffix('.tex')
            visit(child)
        stack.pop()

    visit(cwd / 'main.tex')
    return seen, pieces


def _tex_label_map(tex_root, surface='main', *, rel_base=None):
    _, pieces = _tex_include_graph(tex_root, surface, rel_base=rel_base)
    result = {}
    for path, text in pieces:
        for m in re.finditer(r'\\label\{([^}]+)\}', text):
            if m[1] in result:
                raise ValueError('duplicate active label ' + m[1])
            result[m[1]] = {'path': path, 'position': m.start()}
    return result


def _tex_equations(tex_root, surface='main', *, rel_base=None):
    result = {}
    for _, text in _tex_include_graph(tex_root, surface, rel_base=rel_base)[1]:
        for m in re.finditer(r'\\begin\{(equation|align|gather)(\*?)\}.*?\\end\{\1\2\}', text, re.S):
            for lab in re.findall(r'\\label\{([^}]+)\}', m.group()):
                result[lab] = m.group()
    return result


# ---------------------------------------------------------------------------
# Canonical Typst source helpers (primary publication authority under typst/)
# ---------------------------------------------------------------------------

def typst_visible(text):
    """Strip Typst comments (// and /* */) and #if false [...] blocks."""
    out = []
    i = 0
    n = len(text)
    in_str = False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == '\\' and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if ch == '"':
                in_str = False
            i += 1; continue
        if ch == '\\' and i + 1 < n:
            out.append(ch); out.append(text[i + 1]); i += 2; continue
        if ch == '"':
            in_str = True; out.append(ch); i += 1; continue
        if ch == '/' and i + 1 < n and text[i + 1] == '/':
            if i > 0 and text[i - 1] == ':':
                out.append('//'); i += 2; continue
            while i < n and text[i] != '\n':
                i += 1
            continue
        if ch == '/' and i + 1 < n and text[i + 1] == '*':
            i += 2
            while i + 1 < n and not (text[i] == '*' and text[i + 1] == '/'):
                i += 1
            if i + 1 >= n:
                raise ValueError('unclosed Typst block comment')
            i += 2; continue
        if text.startswith('#if false', i):
            j = i + len('#if false')
            while j < n and text[j] in ' \t\r\n':
                j += 1
            if j < n and text[j] in '[{':
                open_c = text[j]; close_c = ']' if open_c == '[' else '}'
                depth = 0
                while j < n:
                    if text[j] == '\\' and j + 1 < n:
                        j += 2; continue
                    if text[j] == open_c:
                        depth += 1
                    elif text[j] == close_c:
                        depth -= 1
                        if depth == 0:
                            j += 1; break
                    j += 1
                else:
                    raise ValueError('unclosed Typst conditional')
                i = j; continue
        out.append(ch); i += 1
    return ''.join(out)


def typst_include_graph(root, surface='main'):
    root = Path(root).resolve()
    typst_root = root / 'typst'
    entry = typst_root / ('main.typ' if surface == 'main' else 'manual/main.typ')
    seen = []; stack = []; pieces = []

    def visit(p):
        p = p.resolve()
        if p in stack:
            raise ValueError('recursive Typst include')
        if not p.is_relative_to(typst_root):
            raise ValueError('include outside typst source tree')
        if not p.exists():
            raise ValueError('missing include ' + str(p))
        stack.append(p)
        rel = p.relative_to(root).as_posix()
        seen.append(rel)
        txt = typst_visible(p.read_text(encoding='utf-8'))
        pieces.append((rel, txt))
        for match in re.finditer(r'#include\s+"([^"]+)"', txt):
            arg = match[1]
            if 'lib/diagrams/' in arg:
                continue
            visit(p.parent / arg)
        stack.pop()

    visit(entry)
    return seen, pieces


def _scan_typst_math(text, start):
    i = start + 1
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '\\' and i + 1 < n:
            i += 2; continue
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == '\\' and i + 1 < n:
                    i += 2; continue
                if text[i] == '"':
                    i += 1; break
                i += 1
            continue
        if ch == '$':
            return i + 1
        i += 1
    return n


def typst_label_map(root, surface='main'):
    _, pieces = typst_include_graph(root, surface)
    result = {}
    for path, text in pieces:
        # Remove $...$ math spans, "..." string literals, and `...` raw spans before scanning
        # <label> so comparisons in math or literal examples like #raw("<anchor>") are never
        # mistaken for Typst label definitions.
        masked = []
        i = 0; n = len(text)
        while i < n:
            if text[i] == '\\' and i + 1 < n:
                masked.append('  '); i += 2; continue
            if text[i] == '"':
                j = i + 1
                while j < n:
                    if text[j] == '\\' and j + 1 < n:
                        j += 2; continue
                    if text[j] == '"':
                        j += 1; break
                    j += 1
                masked.append(' ' * (j - i))
                i = j; continue
            if text[i] == '`':
                k = i
                while k < n and text[k] == '`':
                    k += 1
                fence = text[i:k]
                end_raw = text.find(fence, k)
                j = n if end_raw < 0 else end_raw + len(fence)
                masked.append(' ' * (j - i))
                i = j; continue
            if text[i] == '$':
                end = _scan_typst_math(text, i)
                masked.append(' ' * (end - i))
                i = end; continue
            masked.append(text[i]); i += 1
        scan_txt = ''.join(masked)
        for m in re.finditer(r'<([A-Za-z][A-Za-z0-9:._-]*)>', scan_txt):
            lab = m.group(1)
            if lab in ('aod-ref-meta', 'aod-ref-entry', 'aod-ref-use', 'aod-mainref-use', 'aod-cite-use', 'aod-bib-entry'):
                continue
            if lab in result:
                raise ValueError('duplicate active label ' + lab)
            result[lab] = {'path': path, 'position': m.start()}
    return result


def typst_equations(root, surface='main'):
    result = {}
    for _, text in typst_include_graph(root, surface)[1]:
        for m in re.finditer(r'#tagged-eq\(\s*"[^"]+"\s*,\s*\$([^$]+)\$\s*,\s*<([A-Za-z0-9:._-]+)>\s*\)', text, re.S):
            result[m.group(2)] = m.group(0)
        i = 0; n = len(text)
        while i < n:
            if text[i] == '\\' and i + 1 < n:
                i += 2; continue
            if text[i] == '$':
                end = _scan_typst_math(text, i)
                body = text[i + 1 : end - 1]
                after = text[end : end + 120]
                lm = re.match(r'[ \t]*<([A-Za-z0-9:._-]+)>', after)
                if lm and len(body) >= 2 and body[0].isspace() and body[-1].isspace():
                    result[lm.group(1)] = text[i : end + lm.end()]
                i = end; continue
            i += 1
    return result


# ---------------------------------------------------------------------------
# Public representation-aware API (defaults to canonical Typst when present)
# ---------------------------------------------------------------------------

def _uses_typst_authority(root, surface='main'):
    root = Path(root).resolve()
    entry = root / 'typst' / ('main.typ' if surface == 'main' else 'manual/main.typ')
    return entry.is_file()


def include_graph(root, surface='main', representation='auto'):
    root = Path(root).resolve()
    if representation == 'typst' or (representation == 'auto' and _uses_typst_authority(root, surface)):
        return typst_include_graph(root, surface)
    if representation == 'latex':
        return _tex_include_graph(root / 'latex', surface, rel_base=root / 'latex')
    return _tex_include_graph(root, surface, rel_base=root)


def label_map(root, surface='main', representation='auto'):
    root = Path(root).resolve()
    if representation == 'typst' or (representation == 'auto' and _uses_typst_authority(root, surface)):
        return typst_label_map(root, surface)
    if representation == 'latex':
        return _tex_label_map(root / 'latex', surface, rel_base=root / 'latex')
    return _tex_label_map(root, surface, rel_base=root)


def equations(root, surface='main', representation='auto'):
    root = Path(root).resolve()
    if representation == 'typst' or (representation == 'auto' and _uses_typst_authority(root, surface)):
        return typst_equations(root, surface)
    if representation == 'latex':
        return _tex_equations(root / 'latex', surface, rel_base=root / 'latex')
    return _tex_equations(root, surface, rel_base=root)


def latex_include_graph(root, surface='main'):
    return _tex_include_graph(Path(root).resolve() / 'latex', surface, rel_base=Path(root).resolve() / 'latex')


def latex_label_map(root, surface='main'):
    return _tex_label_map(Path(root).resolve() / 'latex', surface, rel_base=Path(root).resolve() / 'latex')


def latex_equations(root, surface='main'):
    return _tex_equations(Path(root).resolve() / 'latex', surface, rel_base=Path(root).resolve() / 'latex')


def baseline_equations(root, surface='main'):
    snap = Path(root).resolve() / BASELINE_SNAPSHOT_REL
    cwd = snap if surface == 'main' else snap / 'manual'
    seen = set(); eqs = {}

    def visit(p):
        p = p.resolve()
        if p in seen or not p.is_file():
            return
        seen.add(p)
        txt = visible(p.read_text(encoding='utf-8'))
        for m in re.finditer(r'\\begin\{(equation|align|gather)(\*?)\}.*?\\end\{\1\2\}', txt, re.S):
            for lab in re.findall(r'\\label\{([^}]+)\}', m.group()):
                eqs[lab] = m.group()
        for match in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}', txt):
            child = cwd / match[1]
            if not child.suffix:
                child = child.with_suffix('.tex')
            if child.is_file():
                visit(child)

    visit(cwd / 'main.tex')
    return eqs


def normalize_math(t):
    return re.sub(r'\s+', '', t)


def audit(root):
    root = Path(root).resolve()
    records = validate_contract_inventory(root)
    mfiles, mparts = include_graph(root, 'main')
    ufiles, uparts = include_graph(root, 'manual')
    for p in MAIN_REQUIRED:
        _require(p in mfiles, 'canonical Main source not rendered: ' + p)
    for p in MANUAL_REQUIRED:
        _require(p in ufiles, 'canonical Manual fixture not rendered: ' + p)
    labs = label_map(root, 'main')
    ulabs = label_map(root, 'manual')
    eqs = equations(root, 'main')
    ueqs = equations(root, 'manual')
    base_main_eqs = baseline_equations(root, 'main')
    for lab in REQUIRED_LABELS:
        _require(lab in labs, 'missing canonical label ' + lab)
    for lab, formula in CANONICAL_EQUATIONS.items():
        _require(lab in eqs, 'required equation absent from rendered graph: ' + lab)
        _require(lab in base_main_eqs, 'baseline equation absent from immutable snapshot: ' + lab)
        _require(normalize_math(formula) in normalize_math(base_main_eqs[lab]),
                 'baseline equation contract mismatch: ' + lab)
        _require(math_ast_of_block(eqs[lab]) == math_ast_from_tex(base_main_eqs[lab]),
                 'canonical equation content changed: ' + lab)

    refs = []
    for path, text in uparts:
        for lab in re.findall(r'(?<![\w:])main:((?:eq|sec|subsec|app|fig|tab):[A-Za-z0-9:_-]+)', text):
            _require(lab in labs, 'unresolved literal Main provenance: ' + lab + ' in ' + path)
            refs.append((path, lab))
    for surf, parts, mapping in [('main', mparts, labs), ('manual', uparts, ulabs)]:
        for path, text in parts:
            for lab in re.findall(r'#(?:eqref|eqnref|secref|appref|figref|tabref|bare-ref)\(\s*"([^"]+)"\s*\)', text):
                _require(lab in mapping, 'unresolved ' + surf + ' reference ' + lab + ' in ' + path)

    # Guard against forbidden legacy definitions across both canonical Typst and TeX
    for p in list((root / 'typst').rglob('*.typ')) + list(root.rglob('*.tex')):
        text = typst_visible(p.read_text(encoding='utf-8')) if p.suffix == '.typ' else clean(p.read_text(encoding='utf-8'))
        _require(not re.search(r'F\s*(?:_\{[^}]+\}|_\([^)]+\))?\s*=\s*C\^(?:\{\\mathrm\{ret\}|\(upright\("ret"\)\))', text),
                 'parallel field-first definition ' + str(p))
        _require('2\\Delta\\mathrm{phase}\\ge1' not in normalize_math(text)
                 and '2Deltaupright("phase")gt.eq1' not in normalize_math(text),
                 'untyped legacy phase selector')

    result = {
        'canonical_authority': 'typst',
        'main_files': mfiles,
        'manual_files': ufiles,
        'main_labels': len(labs),
        'manual_labels': len(ulabs),
        'literal_provenance': len(refs),
        'equation_contracts': len(CANONICAL_EQUATIONS),
    }
    spec = importlib.util.spec_from_file_location('audit_ontology_compaction', root / 'scripts/audit_ontology_compaction.py')
    compaction = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compaction)
    result['scientific_contracts'] = {
        'registered_json': len(records),
        'active_source_specifications': validate_active_specifications(root, records),
    }
    result['compaction'] = compaction.audit(root, mfiles, mparts, labs, eqs, ufiles, ulabs, uparts, ueqs)

    # Check derivative generated LaTeX compatibility tree when present (after canonical Typst checks)
    if (root / 'latex' / 'main.tex').is_file() and (root / 'latex' / 'manual' / 'main.tex').is_file():
        lmfiles, lmparts = latex_include_graph(root, 'main')
        lufiles, luparts = latex_include_graph(root, 'manual')
        llabs = latex_label_map(root, 'main')
        lulabs = latex_label_map(root, 'manual')
        leqs = latex_equations(root, 'main')
        _require(set(llabs) == set(labs), 'generated LaTeX Main label set differs from canonical Typst')
        _require(set(lulabs) == set(ulabs), 'generated LaTeX Manual label set differs from canonical Typst')
        for lab in CANONICAL_EQUATIONS:
            _require(lab in leqs, 'generated LaTeX missing canonical equation: ' + lab)
            _require(math_ast_from_tex(leqs[lab]) == math_ast_from_tex(base_main_eqs[lab]),
                     'generated LaTeX canonical equation content changed: ' + lab)
        for surf, parts, mapping in [('main', lmparts, llabs), ('manual', luparts, lulabs)]:
            for path, text in parts:
                for lab in re.findall(r'\\(?:ref|eqref|eqnref|secref|appref|figref|tabref)\{([^}]+)\}', text):
                    if '#' not in lab:
                        _require(lab in mapping, 'unresolved generated latex ' + surf + ' reference ' + lab + ' in ' + path)
        result['generated_latex_compatibility'] = {
            'main_files': len(lmfiles),
            'manual_files': len(lufiles),
            'main_labels': len(llabs),
            'manual_labels': len(lulabs),
        }
    return result


def actual_build(root, build_root, surface):
    root = Path(root).resolve()
    b = Path(build_root).resolve()
    # Support generated latex/ build root automatically when passed repository root
    if (b / 'latex' / 'main.fls').is_file() and not (b / 'main.fls').is_file():
        b = b / 'latex'
        src_tex_root = root / 'latex'
    elif (root / 'latex' / 'main.tex').is_file() and (b == root / 'latex' or not (root / 'main.tex').is_file()):
        src_tex_root = root / 'latex'
    else:
        src_tex_root = root

    cwd = b if surface == 'main' else b / 'manual'
    fls = cwd / 'main.fls'; aux = cwd / 'main.aux'; log = cwd / 'main.log'
    if not all(p.exists() for p in (fls, aux, log)):
        raise ValueError('missing actual build evidence')
    if re.search(r'undefined references|multiply defined|Citation .* undefined|^!|Missing character:', log.read_text(), re.M):
        raise ValueError('publication has unresolved source/reference/font errors')
    recorded = []
    for line in fls.read_text().splitlines():
        if line.startswith('INPUT '):
            p = Path(line[6:])
            p = p if p.is_absolute() else cwd / p
            p = p.resolve()
            if p.is_relative_to(b) and p.is_file():
                recorded.append(p.relative_to(b).as_posix())
    for f in _tex_include_graph(src_tex_root, surface, rel_base=src_tex_root)[0]:
        if f not in recorded:
            raise ValueError('static include absent from actual TeX execution ' + f)
        if hashlib.sha256((src_tex_root / f).read_bytes()).digest() != hashlib.sha256((b / f).read_bytes()).digest():
            raise ValueError('build source mismatch ' + f)
    actual_labels = set(re.findall(r'\\newlabel\{([^}]+)\}', aux.read_text()))
    for lab in _tex_label_map(src_tex_root, surface, rel_base=src_tex_root):
        if lab not in actual_labels:
            raise ValueError('source label absent from actual aux ' + lab)
    return {
        'surface': surface,
        'recorded_source_files': sorted(set(recorded)),
        'actual_labels': len(actual_labels),
        'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
    }


def audit_conservation(rows, expected_bindings, root):
    """Bind each reviewed source item to its precise construction destination.

    expected_bindings is the reviewed source-to-construct map, not a caller's
    edited inventory. Hash/reference existence alone never supplies this check.
    """
    indexes = {s: label_map(root, s) for s in ('main', 'manual')}
    seen = set()
    for row in rows:
        sid = row['source_id']
        if sid in seen:
            raise ValueError('duplicate conservation source ' + sid)
        seen.add(sid)
        if sid not in expected_bindings:
            raise ValueError('unreviewed source item ' + sid)
        wanted = expected_bindings[sid]
        if row['source_content_sha256'] != wanted['source_content_sha256']:
            raise ValueError('source content binding changed ' + sid)
        destinations = json.loads(row['destinations_json'])
        if destinations != wanted['destinations']:
            raise ValueError('source mapped to unrelated scientific construction ' + sid)
        for d in destinations:
            if indexes[d['surface']].get(d['label'], {}).get('path') != d['path']:
                raise ValueError('inactive conservation destination ' + sid)
        if row['proof_correspondence'] != wanted['proof_correspondence']:
            raise ValueError('changed premise correspondence ' + sid)
        for key in ('disposition', 'correction_id'):
            if key in wanted and row.get(key) != wanted[key]:
                raise ValueError('changed conservation disposition ' + sid)
        if wanted.get('destination_content_sha256'):
            for d, expected in zip(destinations, wanted['destination_content_sha256']):
                actual = hashlib.sha256(scientific_unit(root, d['path'], d['label']).encode()).hexdigest()
                if actual != expected:
                    raise ValueError('reviewed scientific content changed ' + sid + ' at ' + d['label'])
    if seen != set(expected_bindings):
        raise ValueError('undisposed scientific source items')
    return len(seen)


@lru_cache(maxsize=None)
def scientific_unit(root, path, label):
    p = Path(root) / path
    if p.suffix == '.typ':
        eqs = typst_equations(root, 'manual' if '/manual/' in ('/' + path) else 'main')
        if label in eqs:
            return eqs[label]
        text = typst_visible(p.read_text(encoding='utf-8'))
        pos = text.index('<' + label + '>')
        start = max(0, text.rfind('\n\n', 0, pos))
        end = text.find('\n\n', pos)
        return text[start : len(text) if end == -1 else end].strip()
    text = visible(p.read_text(encoding='utf-8'))
    pos = text.index('\\label{' + label + '}')
    block = re.compile(r'\\\[.*?\\\]|\\begin\{(equation\*?|align\*?|gather\*?|figure\*?|table\*?|longtable|definition|theorem|proposition|lemma|proof)\}.*?\\end\{\1\}', re.S)
    blocks = [m for m in block.finditer(text) if m.start() <= pos < m.end()]
    if blocks:
        return min(blocks, key=lambda m: m.end() - m.start()).group()
    headings = list(re.finditer(r'\\(section|subsection|subsubsection|paragraph)\*?(?:\[[^]]*\])?\{', text))
    before = [m for m in headings if m.start() <= pos]
    selected = before[-1] if before else None
    levels = {'section': 1, 'subsection': 2, 'subsubsection': 3, 'paragraph': 4}
    start = selected.start() if selected else max(0, text.rfind('\n\n', 0, pos))
    level = levels[selected[1]] if selected else 4
    end = min((m.start() for m in headings if m.start() > pos and levels[m[1]] <= level), default=len(text))
    return text[start:end].strip()


def fixture_conservation(destination='eq:closure-phase', root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    audit(root)
    expected = {'source:one-phase': {'source_content_sha256': 'declared-one-phase-source',
        'destinations': [{'surface': 'main', 'path': 'typst/sections/04_cut_running_fractal_tesseract.typ', 'label': 'eq:closure-phase'}],
        'proof_correspondence': 'one certified closure contributes one complete closure-phase cycle'}}
    row = {'source_id': 'source:one-phase', 'source_content_sha256': 'declared-one-phase-source',
           'destinations_json': json.dumps([dict(expected['source:one-phase']['destinations'][0], label=destination,
               path=label_map(root)[destination]['path'])]),
           'proof_correspondence': expected['source:one-phase']['proof_correspondence']}
    return {'rendered': True, 'canonical_bindings': audit_conservation([row], expected, root)}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', nargs='?', default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--build-root')
    p.add_argument('--conservation')
    p.add_argument('--reviewed-bindings')
    a = p.parse_args()
    result = audit(a.root)
    if a.build_root:
        result['actual_build'] = [actual_build(a.root, a.build_root, s) for s in ('main', 'manual')]
    if a.conservation:
        if not a.reviewed_bindings:
            raise ValueError('reviewed semantic bindings required')
        with open(a.conservation, newline='') as f:
            rows = list(csv.DictReader(f))
        binding = json.loads(Path(a.reviewed_bindings).read_text())
        result['conserved_source_items'] = audit_conservation(rows, binding['bindings'], a.root)
    print(json.dumps(result, indent=2))
