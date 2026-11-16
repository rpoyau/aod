"""Published BIPM inputs and full-covariance consistency, not an adjustment fit.

Raw decimals are exact transcription values. Rounding cells propagate as rational
intervals so the input covariance precision and output sigma precision both enter.
"""
from __future__ import annotations
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

REL = Path('manual2/data/m1/bipm')
CS = Q(9192631770)
SOURCE_MANIFEST_SHA256 = 'cf00c503ea0d13029a2293820188bf3e729e49da4d544174a797bd4b6e2b799b'
EXCLUDED = {'q51', 'q117', 'q127', 'q142', 'q147', 'q151', 'q153'}


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def read_json(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            need(k not in out, 'Duplicate JSON key: ' + k)
            out[k] = v
        return out
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal(value):
    with localcontext() as ctx:
        ctx.prec = 50
        return Decimal(value.numerator) / Decimal(value.denominator)


def cell(token):
    """Closed nearest-rounding cell; this is an explicit transcription premise."""
    d = Decimal(token)
    need(d.is_finite(), 'Non-finite decimal')
    half = Q(Decimal(5).scaleb(d.as_tuple().exponent - 1))
    return Q(d) - half, Q(d) + half


def add(a, b): return a[0] + b[0], a[1] + b[1]
def neg(a): return -a[1], -a[0]
def mul(a, b):
    products = [x*y for x in a for y in b]
    return min(products), max(products)
def div(a, b):
    need(b[0] > 0, 'Interval denominator must be positive')
    return mul(a, (1/b[1], 1/b[0]))
def power(a, n):
    need(a[0] >= 0 and n > 0, 'Positive interval power')
    return a[0]**n, a[1]**n


def check_psd(matrix):
    """Exact Schur elimination; no clipping or floating tolerance."""
    n = len(matrix)
    need(n > 0 and all(len(row) == n for row in matrix), 'Covariance shape')
    need(all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n)), 'Covariance symmetry')
    a = [list(row) for row in matrix]
    for k in range(n):
        need(a[k][k] >= 0, 'Covariance is not PSD')
        if a[k][k] == 0:
            need(all(a[k][j] == 0 for j in range(k+1, n)), 'Zero covariance pivot with nonzero row')
        else:
            for i in range(k+1, n):
                for j in range(i, n):
                    a[i][j] -= a[i][k]*a[k][j]/a[k][k]
                    a[j][i] = a[i][j]


def parse_input(text):
    lines = text.splitlines()
    need(lines[0].split() == ['M', '14'], 'Input transition count')
    need(lines[15].split() == ['N', '153'], 'Input measurement count')
    need(lines[169].split() == ['NCorrCoeffs', '1168'], 'Input correlation count')
    rows = []
    for line in lines[16:169]:
        parts = line.split(maxsplit=4)
        need(len(parts) == 5, 'Input measurement columns')
        ident, observable, value, sigma, provenance = parts
        need(re.fullmatch(r'q\d+', ident), 'Measurement identity')
        need(re.fullmatch(r'nu\d+(?:_over_nu\d+)?', observable), 'Measurement observable')
        need(Q(value) > 0 and Q(sigma) > 0 and provenance.startswith('['), 'Measurement/provenance values')
        rows.append({'id': ident, 'observable': observable, 'value': value, 'standard_uncertainty': sigma,
                     'unit': '1' if '_over_' in observable else 'Hz', 'source_annotation': provenance,
                     'effectively_excluded': 'Uncertx10000Exclude' in provenance})
    ids = {r['id'] for r in rows}
    need(ids == {f'q{i}' for i in range(1, 154)}, 'Measurement IDs duplicate/missing')
    need({r['id'] for r in rows if r['effectively_excluded']} == EXCLUDED, 'Exclusion annotations differ')
    pairs = set()
    for line in lines[170:]:
        m = re.fullmatch(r'r\((q\d+),(q\d+)\)\s+(\S+)', line.strip())
        need(m is not None, 'Correlation syntax')
        a, b, value = m.groups()
        pair = tuple(sorted((a, b)))
        need(a in ids and b in ids and a != b and pair not in pairs, 'Correlation identity')
        need(-1 <= Q(value) <= 1, 'Correlation domain')
        pairs.add(pair)
    need(len(pairs) == 1168, 'Correlation completeness')
    return rows


def covariance_checks(covariance_text, output_text):
    lines = covariance_text.splitlines()
    start = next(i for i, row in enumerate(lines) if row.strip() == 'Covariance matrix') + 1
    tokens = [row.split() for row in lines[start:start+14]]
    need(len(tokens) == 14 and all(len(row) == 14 for row in tokens), 'Covariance dimensions')
    matrix = [[Q(x) for x in row] for row in tokens]
    check_psd(matrix)
    ranges = [[cell(x) for x in row] for row in tokens]
    absolute = re.findall(r'^nu(\d+)\s+([\d.]+) Hz \+/- ([\d.eE+-]+)\s+Hz', output_text, re.M)
    need(len(absolute) == 14 and {int(i) for i, _, _ in absolute} == set(range(1, 15)), 'Absolute transition IDs')
    nu = {int(i): Q(v) for i, v, _ in absolute}
    cells = {int(i): cell(v) for i, v, _ in absolute}
    nu[15], cells[15] = CS, (CS, CS)
    ratios = re.findall(r'^nu(\d+)/nu(\d+)\s+([\d.]+) \+/- ([\d.eE+-]+)', output_text, re.M)
    expected = {(i, 15) for i in range(1, 15)} | {(i, j) for i in range(1, 15) for j in range(i+1, 15)}
    need(len(ratios) == 105 and {(int(i), int(j)) for i, j, _, _ in ratios} == expected, 'Ratio IDs/completeness')
    checks = []
    with localcontext() as context:
        context.prec = 50
        for si, sj, _, sigma in ratios:
            i, j = int(si), int(sj)
            v = matrix[i-1][i-1] / nu[j]**2
            interval = div(ranges[i-1][i-1], power(cells[j], 2))
            if j != 15:
                v += nu[i]**2 * matrix[j-1][j-1]/nu[j]**4 - 2*nu[i]*matrix[i-1][j-1]/nu[j]**3
                second = div(mul(power(cells[i], 2), ranges[j-1][j-1]), power(cells[j], 4))
                cross = div(mul(mul((Q(2), Q(2)), cells[i]), ranges[i-1][j-1]), power(cells[j], 3))
                interval = add(add(interval, second), neg(cross))
            need(v >= 0, 'Negative propagated variance')
            reported = power(cell(sigma), 2)
            need(max(interval[0], reported[0]) <= min(interval[1], reported[1]),
                 f'Ratio {i}/{j}: input/output rounding cells do not overlap')
            calculated = decimal(v).sqrt()
            checks.append({'ratio': f'{i}/{j}', 'reported_sigma': sigma, 'sigma_from_printed_covariance': str(calculated),
                           'relative_discrepancy': str(abs(calculated/Decimal(sigma)-1)),
                           'input_output_rounding_overlap': True})
    return checks


def evaluate(root):
    data = Path(root)/REL
    p = data/'source_manifest.json'
    need(digest(p) == SOURCE_MANIFEST_SHA256, 'Pinned BIPM manifest changed')
    manifest = read_json(p)
    need({f.name for f in (data/'raw').iterdir()} == set(manifest['files']), 'Raw source inventory differs')
    for name, info in manifest['files'].items():
        f = data/'raw'/name
        need(f.stat().st_size == info['bytes'] and digest(f) == info['sha256'], 'Raw source hash mismatch: '+name)
    raw = data/'raw'
    input_path = next(raw.glob('ClockInputData*.dat'))
    rows = parse_input(input_path.read_text())
    checks = covariance_checks(next(raw.glob('ClockOutputCovData*.dat')).read_text(), next(raw.glob('ClockOutputData*.dat')).read_text())
    xml = ET.parse(raw/'bipm-rb87-2026-10-26.xml')
    ns = {'f':'NPL_MeP_Schema', 's':'https://ptb.de/si'}
    rb = {'frequency_hz': xml.findtext('.//s:value', namespaces=ns),
          'standard_uncertainty_hz_rounded': xml.findtext('.//s:uncertainty', namespaces=ns),
          'coverage_factor': xml.findtext('.//s:coverageFactor', namespaces=ns),
          'valid_from': xml.findtext('.//f:validfrom', namespaces=ns)}
    need(rb == {'frequency_hz':'6834682610.9043129','standard_uncertainty_hz_rounded':'2.3e-06',
                'coverage_factor':'1','valid_from':'2026-03-27'}, 'Rb reference transcription changed')
    return {'schema_version':1, 'verification_status':'verified_external_data_consistency',
            'classification':'published_adjustment_data_not_atomic_prediction',
            'manifest_sha256':SOURCE_MANIFEST_SHA256, 'source_files':manifest['files'],
            'measurement_rows':153, 'effective_measurements':146, 'effectively_excluded_ids':sorted(EXCLUDED),
            'correlation_coefficients':1168, 'covariance_shape':[14,14], 'exact_rational_psd':True,
            'covariance_source_description':manifest['source_described_covariance_basis'],
            'covariance_interpretation':manifest['numerically_supported_covariance_unit'],
            'interpretation_status':manifest['unit_interpretation_status'],
            'rounding_model':'independent closed nearest-rounding cells for printed covariance and frequencies; exact Cs definition; overlap with squared output-sigma cells',
            'ratio_checks':checks, 'checked_ratios':105,
            'recommendation_sigma_multiplier':'47/20','recommendation_covariance_multiplier':'2209/400',
            'adjustment_added_fractional_uncertainty':'5.324065020e-17',
            'random_effect_already_in_outputs':True, 'additional_random_effect_applied':False,
            'least_squares_adjustment':'not_reproduced', 'input_full_covariance_psd':'not_tested',
            'target_exposure':'previously_exposed', 'rb_reference':rb,
            'atomic_prediction':'not_asserted', 'observations':rows}


def generate(root, output_root=None):
    report = evaluate(root)
    p = Path(output_root or root)/REL/'bipm_report.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(canonical(report))
    return report


def verify(root):
    report = evaluate(root)
    need((Path(root)/REL/'bipm_report.json').read_bytes() == canonical(report), 'BIPM persisted report differs')
    return report
