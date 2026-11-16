"""Typed SI observation/calibration arithmetic; no atomic law is supplied here.

Exact rational input algebra is separated from decimal display. The delivered
interval examples are synthetic. They demonstrate a declared measurement map,
not a calibration of a physical Cs device or native atomic motif admission.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path

CS_HZ = Fraction(9192631770)
DATA = Path('manual2/data/m1/metrology')
SOURCE_PATH = 'sections/06_wave_state_relational_time.tex'
SOURCE_LABELS = ['eq:cadence-ratio', 'eq:count-comparator-realization', 'eq:relational-time']
EXTERNAL_SOURCES = {
    'SI_definition': 'https://www.bipm.org/en/si-base-units/second',
    'realization': 'https://www.bipm.org/documents/20126/41489667/SI-App2-second.pdf/3c76fec8-04d9-f484-5c3c-a2e280a0f248',
    'uncertainty': 'https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf',
}
STATUSES = {'record_class': 'synthetic_declared_metrology', 'native_admission': 'not_claimed',
            'device_calibration': 'not_performed', 'atomic_prediction': 'not_performed'}


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def keys(obj, expected, context):
    require(isinstance(obj, dict) and set(obj) == set(expected), context + ': missing or unsupported fields')


def rational(value):
    require(type(value) in (int, str) or isinstance(value, Fraction), 'Exact rational required; no float/bool/null')
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError('Invalid rational') from exc


def integer(value, minimum=0):
    require(type(value) is int and value >= minimum, 'Integer cut/count required')
    return value


def canonical_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sqrt_display(value):
    with localcontext() as ctx:
        ctx.prec = 35
        value = rational(value)
        require(value >= 0, 'Nonnegative variance required')
        return str((Decimal(value.numerator) / Decimal(value.denominator)).sqrt())


def validate_psd(matrix):
    """Exact Schur-complement test including singular positive semidefinite cases."""
    require(isinstance(matrix, list) and len(matrix) > 0, 'Covariance matrix required')
    n = len(matrix)
    require(all(isinstance(row, list) and len(row) == n for row in matrix), 'Covariance shape')
    a = [[rational(x) for x in row] for row in matrix]
    require(all(a[i][j] == a[j][i] for i in range(n) for j in range(n)), 'Covariance symmetry')
    for k in range(n):
        pivot = a[k][k]
        require(pivot >= 0, 'Covariance is not positive semidefinite')
        if pivot == 0:
            require(all(a[k][j] == 0 for j in range(k + 1, n)), 'Zero covariance pivot has nonzero row')
            continue
        for i in range(k + 1, n):
            for j in range(i, n):
                a[i][j] -= a[i][k] * a[k][j] / pivot
                a[j][i] = a[i][j]
    return [[rational(x) for x in row] for row in matrix]


def covariance_record(matrix, variables, units, status='complete'):
    return {'variables': list(variables), 'units': list(units),
            'matrix_units': [[a + '*' + b for b in units] for a in units],
            'matrix': [[None if x is None else str(x) for x in row] for row in matrix],
            'status': status, 'rounding_policy': 'exact_rational_no_tolerance'}


def validate_covariance(record, variables, units):
    keys(record, ['variables', 'units', 'matrix_units', 'matrix', 'status', 'rounding_policy'], 'covariance')
    require(record['variables'] == list(variables) and record['units'] == list(units), 'Covariance order or units')
    require(record['matrix_units'] == [[a + '*' + b for b in units] for a in units], 'Covariance product units')
    require(record['rounding_policy'] == 'exact_rational_no_tolerance', 'Unsupported covariance rounding policy')
    require(record['status'] in ('complete', 'partial'), 'Unsupported covariance status')
    m, n = record['matrix'], len(variables)
    require(isinstance(m, list) and len(m) == n and all(isinstance(row, list) and len(row) == n for row in m), 'Covariance shape')
    require(all(m[i][j] == m[j][i] for i in range(n) for j in range(n)), 'Covariance symmetry')
    unknown = any(x is None for row in m for x in row)
    require((record['status'] == 'partial') == unknown, 'Covariance completeness status contradicts values')
    if unknown:
        for i in range(n):
            if m[i][i] is not None:
                require(rational(m[i][i]) >= 0, 'Negative known variance')
            for j in range(n):
                if m[i][j] is not None:
                    rational(m[i][j])
        # Every wholly known principal submatrix must still be valid.
        for mask in range(1, 1 << n):
            indices = [i for i in range(n) if mask & (1 << i)]
            sub = [[m[i][j] for j in indices] for i in indices]
            if all(x is not None for row in sub for x in row):
                validate_psd(sub)
        return None
    return validate_psd(m)


def quadratic(jacobian, matrix):
    m = validate_psd(matrix)
    j = [rational(x) for x in jacobian]
    require(len(j) == len(m), 'Jacobian dimension')
    return sum(j[i] * m[i][k] * j[k] for i in range(len(j)) for k in range(len(j)))


def frequency_from_ratio(ratio, ratio_variance=None, reference_hz=CS_HZ,
                         reference_variance=None, ratio_reference_covariance=None,
                         reference_kind='exact_si_definition'):
    """Convert an already supplied ratio. This function does not derive it.

    Variances are input statistical/model uncertainty, not a native certificate.
    Exact Cs definition carries zero uncertainty by definition; real reference
    calibration is a separate parameterization and must provide its budget.
    """
    r, f = rational(ratio), rational(reference_hz)
    require(r > 0 and f > 0, 'Positive ratio/reference required')
    require(reference_kind in ('exact_si_definition', 'realized_reference'), 'Reference kind')
    if reference_kind == 'exact_si_definition':
        require(f == CS_HZ, 'Exact defining reference must be Cs-133')
        require(reference_variance is None or rational(reference_variance) == 0, 'Exact definition cannot have nonzero variance')
        require(ratio_reference_covariance is None or rational(ratio_reference_covariance) == 0, 'Exact definition cannot covary')
        reference_variance, ratio_reference_covariance = Fraction(0), Fraction(0)
    raw = [[ratio_variance, ratio_reference_covariance], [ratio_reference_covariance, reference_variance]]
    record = covariance_record(raw, ['ratio', 'reference_frequency'], ['1', 'Hz'],
                               'partial' if any(x is None for row in raw for x in row) else 'complete')
    cov = validate_covariance(record, ['ratio', 'reference_frequency'], ['1', 'Hz'])
    frequency, period = r * f, 1 / (r * f)
    first_order_variance = None if cov is None else quadratic([f, r], cov)
    unknown = []
    if cov is None:
        unknown.append('unknown_input_covariance_or_variance')
    else:
        # A small propagated variance can be cancellation of large uncertain
        # inputs. Check each marginal before using a first-order product budget.
        if cov[0][0] > r*r/10000 or cov[1][1] > f*f/10000:
            unknown.append('product_input_nonlinearity_requires_joint_distribution')
        # Even small marginals can cancel at first order while their product
        # still varies. Higher moments cannot be inferred from covariance alone.
        if first_order_variance == 0 and cov[0][0] > 0 and cov[1][1] > 0:
            unknown.append('cancelled_product_gradient_requires_joint_distribution')
        if first_order_variance > frequency**2/10000:
            unknown.append('reciprocal_nonlinearity_requires_distribution')
    linear = not unknown
    variance = first_order_variance if linear else None
    return {'classification': 'conditional_unit_conversion_not_ratio_derivation',
            'reference_kind': reference_kind, 'ratio': str(r), 'reference_hz': str(f),
            'frequency_hz': str(frequency), 'quantity_kind': 'transition_period',
            'transition_period_seconds': str(period),
            'first_order_frequency_variance_hz2': None if first_order_variance is None else str(first_order_variance),
            'frequency_variance_hz2': None if variance is None else str(variance),
            'transition_period_variance_s2': str(variance / frequency**4) if linear else None,
            'standard_uncertainty_hz_display': None if variance is None else sqrt_display(variance),
            'standard_uncertainty_seconds_display': sqrt_display(variance / frequency**4) if linear else None,
            'uncertainty_status': 'complete_first_order_conditional' if linear else 'partial',
            'period_propagation': 'conditional_first_order; marginal_and_output_relative_standard_uncertainties_at_most_1_percent' if linear else 'not_established',
            'linearity_scope': 'Local first-order approximation; marginal guards are not distribution-free error bounds.',
            'unresolved_uncertainty': unknown,
            'covariance': record, 'native_admission': 'not_asserted'}


def source_binding(root):
    text = (root / SOURCE_PATH).read_text()
    require(all('\\label{' + x + '}' in text for x in SOURCE_LABELS), 'Main relational labels missing')
    return {'path': SOURCE_PATH, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'labels': SOURCE_LABELS, 'external_sources': EXTERNAL_SOURCES}


def _returns(lineage, cuts):
    return [{'id': lineage + ':return:' + str(i), 'cut': cut} for i, cut in enumerate(cuts)]


def default_input(root):
    ref = _returns('synthetic:reference', [0, 3, 6, 9, 12])
    target = _returns('synthetic:compared', [0, 4, 8, 12])
    ps = Fraction(1, 10**12)
    u = [50 * ps * CS_HZ, 2 * ps, 30 * ps]
    matrix = [[u[0]**2, 0, u[0]*u[2]/2], [0, u[1]**2, 0], [u[0]*u[2]/2, 0, u[2]**2]]
    variables, units = ['physical_cycles', 'fractional_offset', 'endpoint_correction'], ['cycle', '1', 's']
    budget = []
    for name, unit, sigma in zip(variables, units, u):
        budget.append({'id': name, 'covers': [name], 'included': True, 'included_in_aggregate': None,
                       'unit': unit, 'standard_uncertainty': str(sigma), 'evaluation': 'synthetic_Type_B',
                       'distribution': 'declared_local_covariance', 'covariance_group': 'synthetic_joint_budget',
                       'source': 'R02_declared_example_not_device_data', 'correction_status': 'applied_or_zero_by_setup'})
    return {'schema_version': 2, 'model_id': 'm1:synthetic-si-map:v2', 'statuses': dict(STATUSES),
            'source_binding': source_binding(root),
            'binding': {'window': [0, 12], 'comparison_cut': 12, 'reference_lineage': 'synthetic:reference',
                        'lineages': [{'id': 'synthetic:reference', 'returns': ref, 'prefix_sha256': sha(ref)},
                                     {'id': 'synthetic:compared', 'returns': target, 'prefix_sha256': sha(target)}],
                        'contact_cuts': [4, 8, 12], 'reference_increment': 4,
                        'scope': 'synthetic:common-window', 'native_certificate_status': 'not_claimed'},
            'observation': {'kind': 'synthetic_affine_cycle_map', 'reference_lineage': 'synthetic:reference',
                            'window': [0, 12], 'cycles_per_return': str(CS_HZ/4), 'endpoint_phase_cycles': ['0', '0'],
                            'observed_cycles': str(CS_HZ), 'calibration_record': 'synthetic:stipulated-alpha',
                            'map_status': 'declared_synthetic_only'},
            'reference': {'kind': 'synthetic_realization', 'nominal_ratio': '1', 'nominal_hz': str(CS_HZ),
                          'fractional_offset': '0', 'effective_window': [0, 12],
                          'offset_status': 'stipulated_synthetic', 'realization_status': 'synthetic_not_device'},
            'calibration': {'available_at_cut': 0, 'validity_cuts': [0, 12], 'mode': 'online',
                            'evidence_id': 'synthetic:calibration', 'traceability': 'synthetic_setup_not_physical_traceability',
                            'fitted_targets': [], 'exposed_targets': ['H-1', 'Rb-87'],
                            'prediction_class': 'not_an_atomic_prediction'},
            'measurand': {'kind': 'elapsed_interval', 'time_coordinate': 'local_proper_time',
                          'point_or_scale': 'synthetic:connector', 'epoch_seconds': '0',
                          'global_gravitational_correction_seconds': None,
                          'transfer_model': None, 'coordinate_status': 'declared_synthetic'},
            'endpoint_correction_seconds': '0', 'covariance': covariance_record(matrix, variables, units),
            'budget': budget,
            'acquisition': {'noise_model': 'declared_joint_covariance_not_independent_samples',
                            'dead_time_status': 'none_by_synthetic_setup', 'dead_time_seconds': '0',
                            'extrapolation_model': None, 'cycle_slip_status': 'resolved_by_synthetic_setup',
                            'cycle_slip_alternatives': [0]},
            'coverage': {'standard': True, 'expanded_factor': None, 'coverage_basis': None}}


def validate_binding(binding):
    keys(binding, ['window', 'comparison_cut', 'reference_lineage', 'lineages', 'contact_cuts',
                   'reference_increment', 'scope', 'native_certificate_status'], 'binding')
    require(binding['native_certificate_status'] == 'not_claimed', 'Synthetic binding cannot claim native certificate')
    require(isinstance(binding['scope'], str) and binding['scope'], 'Scope identity')
    w = binding['window']
    require(isinstance(w, list) and len(w) == 2, 'Window pair')
    u, v = [integer(x) for x in w]
    require(u < v and binding['comparison_cut'] == v, 'Committed comparison cut/window')
    lineages = binding['lineages']
    require(isinstance(lineages, list) and len(lineages) == 2, 'Two recurrent lineages required')
    ids = [x['id'] for x in lineages]
    require(len(set(ids)) == 2 and binding['reference_lineage'] in ids, 'Distinct reference identities')
    all_ids, counts = set(), {}
    for lineage in lineages:
        keys(lineage, ['id', 'returns', 'prefix_sha256'], 'lineage')
        events = lineage['returns']
        require(isinstance(events, list) and len(events) >= 2, 'Recurrent return history')
        cuts = []
        for event in events:
            keys(event, ['id', 'cut'], 'return event')
            require(isinstance(event['id'], str) and event['id'] and event['id'] not in all_ids, 'Distinct committed return identity')
            all_ids.add(event['id']); cuts.append(integer(event['cut']))
        require(cuts == sorted(set(cuts)) and cuts[-1] <= v, 'Committed prefix excludes future/replayed returns')
        require(lineage['prefix_sha256'] == sha(events), 'Return prefix digest')
        # The first completion establishes the recurrence anchor. The subsequent
        # distinct completions are reclosures; retain the initial event itself.
        counts[lineage['id']] = sum(u < k <= v for k in cuts[1:])
    contacts = binding['contact_cuts']
    require(isinstance(contacts, list) and len(contacts) >= 2 and contacts == sorted(set(contacts)), 'Repeated distinct contacts')
    require(all(type(k) is int and u <= k <= v for k in contacts), 'Closed contact window')
    n = integer(binding['reference_increment'], 1)
    require(n == counts[binding['reference_lineage']], 'Reference increment must match committed returns')
    return n


def validate_budget(rows, covariance):
    require(isinstance(rows, list) and len(rows) >= 3, 'Budget rows required')
    index = {}
    active_effects = set()
    for row in rows:
        keys(row, ['id', 'covers', 'included', 'included_in_aggregate', 'unit', 'standard_uncertainty',
                   'evaluation', 'distribution', 'covariance_group', 'source', 'correction_status'], 'budget row')
        require(isinstance(row['id'], str) and row['id'] not in index, 'Unique budget identity')
        index[row['id']] = row
        require(type(row['included']) is bool, 'Budget inclusion boolean')
        require(isinstance(row['covers'], list) and len(row['covers']) > 0 and len(set(row['covers'])) == len(row['covers']), 'Budget coverage identities')
        require(row['evaluation'] in ('synthetic_Type_A', 'synthetic_Type_B'), 'Budget evaluation scope')
        require(row['correction_status'] == 'applied_or_zero_by_setup', 'Unapplied correction')
        require(row['distribution'] == 'declared_local_covariance', 'Budget distribution')
        require(row['covariance_group'] == 'synthetic_joint_budget', 'Budget covariance group')
        require(isinstance(row['source'], str) and row['source'], 'Budget source')
        if row['standard_uncertainty'] is not None:
            require(rational(row['standard_uncertainty']) >= 0, 'Negative standard uncertainty')
        if row['included']:
            require(row['included_in_aggregate'] is None, 'Budget contribution included twice')
            require(not active_effects.intersection(row['covers']), 'Duplicate aggregate effect')
            active_effects.update(row['covers'])
    for row in rows:
        parent = row['included_in_aggregate']
        if not row['included']:
            require(parent in index and index[parent]['included'], 'Excluded component needs included aggregate')
            require(set(row['covers']) <= set(index[parent]['covers']), 'Aggregate does not include component')
    require({row['id'] for row in rows if row['included']} == set(covariance['variables']), 'Budget/covariance variables')
    for i, name in enumerate(covariance['variables']):
        row = index[name]
        require(row['unit'] == covariance['units'][i], 'Budget units')
        sigma, variance = row['standard_uncertainty'], covariance['matrix'][i][i]
        require((sigma is None) == (variance is None), 'Budget unknown diagonal mismatch')
        if sigma is not None:
            require(rational(sigma)**2 == rational(variance), 'Budget sigma does not match covariance')


def interval(record, root=None):
    """Evaluate a bound synthetic measurement equation, retaining its limitations."""
    keys(record, ['schema_version', 'model_id', 'statuses', 'source_binding', 'binding', 'observation',
                  'reference', 'calibration', 'measurand', 'endpoint_correction_seconds', 'covariance',
                  'budget', 'acquisition', 'coverage'], 'interval input')
    require(type(record['schema_version']) is int and record['schema_version'] == 2, 'Schema version')
    require(record['model_id'] == 'm1:synthetic-si-map:v2' and record['statuses'] == STATUSES, 'Model/status scope')
    root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    require(record['source_binding'] == source_binding(root), 'Source binding')
    n = validate_binding(record['binding']); w = record['binding']['window']
    obs = record['observation']
    keys(obs, ['kind', 'reference_lineage', 'window', 'cycles_per_return', 'endpoint_phase_cycles',
               'observed_cycles', 'calibration_record', 'map_status'], 'observation')
    require(obs['kind'] == 'synthetic_affine_cycle_map' and obs['map_status'] == 'declared_synthetic_only', 'Explicit observation map required')
    require(obs['window'] == w and obs['reference_lineage'] == record['binding']['reference_lineage'], 'Observation identity/window')
    require(isinstance(obs['calibration_record'], str) and obs['calibration_record'], 'Observation calibration record')
    phase = obs['endpoint_phase_cycles']; require(isinstance(phase, list) and len(phase) == 2, 'Endpoint phase pair')
    alpha = rational(obs['cycles_per_return']); require(alpha > 0, 'Positive calibrated map coefficient')
    c = alpha*n + rational(phase[1]) - rational(phase[0])
    require(c > 0 and c == rational(obs['observed_cycles']), 'Observed cycles must follow declared map')
    ref = record['reference']
    keys(ref, ['kind', 'nominal_ratio', 'nominal_hz', 'fractional_offset', 'effective_window', 'offset_status', 'realization_status'], 'reference')
    require(ref['kind'] == 'synthetic_realization' and ref['offset_status'] == 'stipulated_synthetic' and ref['realization_status'] == 'synthetic_not_device', 'Reference realization status')
    f = rational(ref['nominal_hz']); y = rational(ref['fractional_offset'])
    require(f > 0 and f == rational(ref['nominal_ratio'])*CS_HZ and 1+y > 0, 'Reference frequency/nominal synthesis')
    require(ref['effective_window'] == w, 'Offset averaging window')
    cal = record['calibration']
    keys(cal, ['available_at_cut', 'validity_cuts', 'mode', 'evidence_id', 'traceability', 'fitted_targets', 'exposed_targets', 'prediction_class'], 'calibration')
    available = integer(cal['available_at_cut']); require(cal['mode'] in ('online', 'retrospective'), 'Calibration mode')
    require(cal['mode'] != 'online' or available <= w[1], 'Future calibration cannot be online')
    require(isinstance(cal['validity_cuts'], list) and len(cal['validity_cuts']) == 2 and
            integer(cal['validity_cuts'][0]) <= w[0] and integer(cal['validity_cuts'][1]) >= w[1], 'Calibration validity')
    require(cal['evidence_id'] and cal['traceability'] == 'synthetic_setup_not_physical_traceability', 'Synthetic calibration is not device traceability')
    require(cal['fitted_targets'] == [] and cal['exposed_targets'] == ['H-1', 'Rb-87'] and cal['prediction_class'] == 'not_an_atomic_prediction', 'Exposure/calibration roles')
    meas = record['measurand']
    keys(meas, ['kind', 'time_coordinate', 'point_or_scale', 'epoch_seconds', 'global_gravitational_correction_seconds', 'transfer_model', 'coordinate_status'], 'measurand')
    require(meas['kind'] == 'elapsed_interval' and meas['coordinate_status'] == 'declared_synthetic', 'Interval type/status')
    require(meas['time_coordinate'] in ('local_proper_time', 'coordinated_scale') and meas['point_or_scale'], 'Time coordinate identity')
    rational(meas['epoch_seconds'])
    if meas['time_coordinate'] == 'local_proper_time':
        require(meas['global_gravitational_correction_seconds'] is None, 'No blanket gravitational correction to local proper time')
        require(meas['transfer_model'] is None, 'Local proper-time example has no scale-transfer model')
    else:
        require(meas['global_gravitational_correction_seconds'] is None, 'Scale corrections must be included in the explicit endpoint transfer budget')
        require(isinstance(meas['transfer_model'], dict), 'Coordinated scale needs explicit transfer model')
        keys(meas['transfer_model'], ['status', 'included_in', 'source'], 'transfer')
        require(meas['transfer_model']['status'] == 'synthetic_included' and meas['transfer_model']['included_in'] == 'endpoint_correction' and meas['transfer_model']['source'], 'Transfer correction inclusion')
    cov = validate_covariance(record['covariance'], ['physical_cycles', 'fractional_offset', 'endpoint_correction'], ['cycle', '1', 's'])
    validate_budget(record['budget'], record['covariance'])
    acq = record['acquisition']
    keys(acq, ['noise_model', 'dead_time_status', 'dead_time_seconds', 'extrapolation_model', 'cycle_slip_status', 'cycle_slip_alternatives'], 'acquisition')
    require(acq['noise_model'] == 'declared_joint_covariance_not_independent_samples', 'Noise model')
    require(acq['dead_time_status'] in ('none_by_synthetic_setup', 'unmodeled'), 'Dead time status')
    dead = rational(acq['dead_time_seconds']); require(dead >= 0, 'Dead time nonnegative')
    require((dead == 0) == (acq['dead_time_status'] == 'none_by_synthetic_setup'), 'Dead time amount/status')
    require(acq['extrapolation_model'] is None, 'No undeclared dead-time interpolation')
    require(acq['cycle_slip_status'] in ('resolved_by_synthetic_setup', 'ambiguous'), 'Cycle slip status')
    slips = acq['cycle_slip_alternatives']
    require(isinstance(slips, list) and all(type(x) is int for x in slips) and len(set(slips)) == len(slips), 'Discrete slip alternatives')
    require((slips == [0]) == (acq['cycle_slip_status'] == 'resolved_by_synthetic_setup'), 'Cycle slip ambiguity/status')
    require(len(slips) > 0 and all(c+x > 0 for x in slips), 'Positive cycle alternatives')
    coverage = record['coverage']
    keys(coverage, ['standard', 'expanded_factor', 'coverage_basis'], 'coverage')
    require(coverage['standard'] is True, 'Report standard uncertainty')
    factor = coverage['expanded_factor']
    if factor is None:
        require(coverage['coverage_basis'] is None, 'Coverage basis without factor')
    else:
        factor = rational(factor)
        require(factor > 0 and isinstance(coverage['coverage_basis'], str) and coverage['coverage_basis'], 'Expanded uncertainty needs coverage interpretation')
    d = rational(record['endpoint_correction_seconds'])
    t = c / (f*(1+y)) + d
    require(t > 0, 'Positive interval required')
    jacobian = [1/(f*(1+y)), -c/(f*(1+y)**2), Fraction(1)]
    unknown = []
    if cov is None: unknown.append('partial_input_covariance')
    if dead: unknown.append('dead_time_extrapolation_not_modeled')
    if acq['cycle_slip_status'] == 'ambiguous': unknown.append('discrete_cycle_slips_unresolved')
    # Small fractional-frequency uncertainty is an explicit first-order guard.
    if cov is not None and cov[1][1] > (1+y)**2 / 10000:
        unknown.append('frequency_denominator_nonlinearity_requires_distribution')
    variance = quadratic(jacobian, cov) if cov is not None and not unknown else None
    return {'classification': 'synthetic_calibrated_interval', 'input_sha256': sha(record),
            'quantity_kind': 'elapsed_interval', 'unit': 's', 'time_coordinate': meas['time_coordinate'],
            'bound_window': w, 'reference_increment': n, 'physical_reference_cycles': str(c),
            'elapsed_seconds': str(t) if acq['cycle_slip_status'] != 'ambiguous' and not dead else None,
            'conditional_interval_alternatives_seconds': [str((c+x)/(f*(1+y))+d) for x in slips],
            'variance_seconds2': None if variance is None else str(variance),
            'standard_uncertainty_seconds_display': None if variance is None else sqrt_display(variance),
            'expanded_uncertainty_seconds_display': sqrt_display(variance*factor**2) if variance is not None and factor is not None else None,
            'coverage_factor': None if factor is None else str(factor), 'coverage_basis': coverage['coverage_basis'],
            'uncertainty_status': 'partial' if unknown else 'complete_first_order_synthetic',
            'unresolved_uncertainty': unknown, 'jacobian': [str(x) for x in jacobian],
            'native_admission': 'not_claimed', 'device_calibration': 'not_performed'}


def gaussian_quadratic_shift(coefficient, mean, sigma):
    q, b, s = map(rational, (coefficient, mean, sigma))
    require(s >= 0, 'Nonnegative Gaussian sigma')
    return {'mean_shift': str(q*(b*b+s*s)), 'variance': str(q*q*(2*s**4+4*b*b*s*s)),
            'scope': 'exact_Gaussian_moments_of_declared_quadratic_response'}


def stateful_integration(root):
    """Bind real v2 histories to an explicitly stipulated synthetic observation.

    Both histories use the same synthetic cycle-per-return coefficient, chosen
    for a one-second reference example. This cannot identify an atomic line or
    supply an experimental calibration. The compared output is a finite-window
    cycle-average rate, never a stationary hyperfine transition frequency.
    """
    import matter1_stateful as stateful
    prepared = stateful.prepare(root)
    baseline = prepared['baseline_trace']
    reference_count = baseline['summary']['observed_reclosure_counts']['outer_minus']
    alpha = CS_HZ / reference_count
    results = {}
    for name in ('baseline', 'early_loss'):
        trace = prepared[name + '_trace']
        record = default_input(root)
        waves = {wave['name']: wave for wave in trace['outer_waves']}
        window = trace['summary']['window']
        lineages = []
        for wave in trace['outer_waves']:
            returns = [{'id': event['trace_id'], 'cut': event['events'][-1]['cut']}
                       for event in wave['returns']]
            lineages.append({'id': wave['identity'], 'returns': returns, 'prefix_sha256': sha(returns)})
        reference = waves['outer_minus']['identity']
        ref_count = trace['summary']['observed_reclosure_counts']['outer_minus']
        record['binding'].update(window=window, comparison_cut=window[1], reference_lineage=reference,
                                 lineages=lineages, contact_cuts=[e['cut'] for e in trace['contacts']],
                                 reference_increment=ref_count, scope='stateful:synthetic-observation-window')
        record['observation'].update(reference_lineage=reference, window=window,
                                     cycles_per_return=str(alpha), observed_cycles=str(alpha*ref_count))
        record['reference']['effective_window'] = window
        record['calibration']['validity_cuts'] = window
        result = interval(record, root)
        target_cycles = alpha * trace['summary']['observed_reclosure_counts']['outer_plus']
        rate = target_cycles / rational(result['elapsed_seconds'])
        results[name] = {'stateful_trace_sha256': sha(trace), 'stateful_model_sha256': trace['model_sha256'],
                         'coupled_comparison_history_sha256': sha(trace['comparisons']),
                         'mapped_input': record, 'interval_result': result,
                         'compared_return_count': trace['summary']['observed_reclosure_counts']['outer_plus'],
                         'synthetic_finite_window_cycle_average_rate_hz': str(rate),
                         'atomic_transition_frequency_hz': None,
                         'physical_atomic_map_status': 'not_established'}
    require(results['baseline']['interval_result']['elapsed_seconds'] == results['early_loss']['interval_result']['elapsed_seconds'], 'Same synthetic reference interval')
    require(results['baseline']['synthetic_finite_window_cycle_average_rate_hz'] != results['early_loss']['synthetic_finite_window_cycle_average_rate_hz'], 'Intervention reaches synthetic mapped observable')
    return {'classification': 'stateful_history_with_stipulated_synthetic_cycle_map',
            'cycles_per_return': str(alpha), 'coefficient_origin': 'stipulated_for_demonstration_not_a_physical_calibration',
            'cases': results, 'native_admission': 'not_claimed', 'atomic_prediction': 'not_performed',
            'limitation': 'Finite-window average of a synthetic observable; no atomic or stationary-frequency identification.'}


def examples(root):
    base = default_input(root)
    partial = deepcopy(base)
    partial['covariance']['status'] = 'partial'
    partial['covariance']['matrix'][0][1] = partial['covariance']['matrix'][1][0] = None
    slips = deepcopy(base)
    slips['acquisition']['cycle_slip_status'] = 'ambiguous'
    slips['acquisition']['cycle_slip_alternatives'] = [-1, 0, 1]
    dead = deepcopy(base)
    dead['acquisition'].update(dead_time_status='unmodeled', dead_time_seconds='1/10')
    return {'schema_version': 2, 'statuses': dict(STATUSES), 'examples':
            {'complete_synthetic': base, 'unknown_cross_covariance': partial,
             'ambiguous_cycle_slips': slips, 'unmodeled_dead_time': dead}}


def evaluate(inputs, root):
    keys(inputs, ['schema_version', 'statuses', 'examples'], 'examples bundle')
    require(type(inputs['schema_version']) is int and inputs['schema_version'] == 2 and inputs['statuses'] == STATUSES, 'Examples statuses/schema')
    require(set(inputs['examples']) == {'complete_synthetic', 'unknown_cross_covariance', 'ambiguous_cycle_slips', 'unmodeled_dead_time'}, 'Example inventory')
    results = {}
    for name, record in inputs['examples'].items():
        require(record['source_binding'] == source_binding(root), 'Source binding')
        results[name] = interval(record, root)
    # The persisted bundle is a named regression input; the reusable interval API
    # accepts valid alternate declared measurements rather than fixing values.
    require(inputs == examples(root), 'Delivered example changed; use a distinct declared scenario')
    ps = Fraction(1, 10**12)
    return {'schema_version': 2, 'statuses': dict(STATUSES), 'input_sha256': sha(inputs),
            'intervals': results,
            'correlated_bias_100_seconds_variance_s2': str(quadratic([100], [[ps**2]])),
            'incorrect_independent_100_samples_variance_s2': str(100*ps**2),
            'quadratic_zero_field_example': gaussian_quadratic_shift(1, 0, '1/10'),
            'ratio_conversion_example': frequency_from_ratio('1/7', '1/100000000000000000000'),
            'stateful_integration': stateful_integration(root),
            'scope': 'Executed synthetic metrology and guards; no physical device calibration or atomic prediction.'}


def normalize_root(root):
    root = Path(root).resolve()
    return root.parent if root.name == 'manual2' else root


def generate(root, output_root=None):
    root = normalize_root(root)
    destination = normalize_root(output_root) if output_root else root
    inputs = examples(root); report = evaluate(inputs, root)
    folder = destination / DATA; folder.mkdir(parents=True, exist_ok=True)
    (folder/'metrology_inputs.json').write_bytes(canonical_bytes(inputs))
    (folder/'metrology_report.json').write_bytes(canonical_bytes(report))
    return report


def verify(root):
    root = normalize_root(root)
    inputs = json.loads((root/DATA/'metrology_inputs.json').read_text())
    report = evaluate(inputs, root)
    require((root/DATA/'metrology_inputs.json').read_bytes() == canonical_bytes(inputs), 'Canonical input serialization')
    require((root/DATA/'metrology_report.json').read_bytes() == canonical_bytes(report), 'Metrology report differs from recomputation')
    return {'status': 'PASS_SYNTHETIC_METROLOGY', 'input_sha256': sha(inputs),
            'examples': len(inputs['examples']), 'statuses': dict(STATUSES),
            'synthetic_interval_seconds': report['intervals']['complete_synthetic']['elapsed_seconds'],
            'synthetic_standard_uncertainty_seconds': report['intervals']['complete_synthetic']['standard_uncertainty_seconds_display'],
            'physical_calibration': 'not_performed', 'atomic_prediction': 'not_performed'}
