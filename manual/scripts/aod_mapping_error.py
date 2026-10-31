#!/usr/bin/env python3
"""Declared finite rational maps and uncertainty; no physical calibration claim.

All guards use explicit exceptions and remain active under python -O. The small
expression language is intentionally closed: it supports exact scalar arithmetic,
not arbitrary Python or unverified symbolic formula strings.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'manual/data/m3/mapping_error.json'
FIELDS = ('id', 'version', 'code_sha256', 'spec_sha256', 'domain', 'codomain',
          'law', 'parameters', 'sources', 'structure', 'information_loss',
          'resolution', 'error', 'calibration', 'comparison', 'status')
ERROR_COMPONENTS = ('arithmetic', 'resolution', 'window', 'model_discrepancy',
                    'calibration', 'propagation', 'solver', 'comparison')
MODEL_FIELDS = ('code_sha256', 'id', 'version', 'domain', 'codomain', 'law', 'parameters')

class ContractError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ContractError(message)

def rational(value):
    require(isinstance(value, (str, int, Q)) and not isinstance(value, bool),
            'exact rational required; floats and booleans are forbidden')
    try:
        return Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ContractError('invalid rational') from exc

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def source(identity, role, payload):
    require(role in ('model', 'calibration', 'evaluation', 'definition'), 'invalid source role')
    return {'id': identity, 'role': role, 'payload': payload, 'sha256': digest(payload)}

def validate_sources(sources, trusted):
    require(isinstance(sources, list) and sources, 'source bindings required')
    seen = set()
    for item in sources:
        require(set(item) == {'id', 'role', 'payload', 'sha256'}, 'source fields')
        require(item['id'] not in seen, 'duplicate source identity')
        seen.add(item['id'])
        require(item['role'] in ('model', 'calibration', 'evaluation', 'definition'), 'source role')
        require(item['sha256'] == digest(item['payload']), 'source byte/content hash mismatch')
        require(trusted.get(item['id']) == item, 'unbound or changed source identity')
    return {item['id']: item for item in sources}

def port(name, kind='report_scalar', dimension=(0, 0, 0), unit='1', bounds=('-100', '100')):
    return {'name': name, 'kind': kind, 'dimension': list(dimension), 'unit': unit,
            'bounds': list(bounds), 'scope': 'declared-finite-model', 'lineage': 'fixture'}

def validate_port(item):
    require(set(item) == {'name', 'kind', 'dimension', 'unit', 'bounds', 'scope', 'lineage'}, 'port fields')
    require(all(isinstance(item[k], str) and item[k] for k in ('name', 'kind', 'unit', 'scope', 'lineage')), 'typed port identity')
    require(len(item['dimension']) == 3 and all(type(x) is int for x in item['dimension']), 'dimensions L,T,N required')
    units = {'1': [0,0,0], 'm': [1,0,0], 'm^2': [2,0,0], 'm^3': [3,0,0],
             'm^4': [4,0,0], 's': [0,1,0], 'Hz': [0,-1,0],
             'count': [0,0,1], 'cycle': [0,0,1], 'cycle/s': [0,-1,1]}
    require(item['unit'] in units and units[item['unit']] == item['dimension'], 'unit/dimension convention mismatch')
    require(len(item['bounds']) == 2 and rational(item['bounds'][0]) <= rational(item['bounds'][1]), 'ordered admissible bounds')

def typed_equal(a, b):
    return all(a[k] == b[k] for k in ('kind', 'dimension', 'unit', 'scope', 'lineage'))

def expression_refs(expr, kind):
    require(isinstance(expr, list) and expr, 'expression must be a nonempty list')
    if expr[0] in ('input', 'parameter'):
        require(len(expr) == 2 and isinstance(expr[1], str), 'expression reference')
        return {expr[1]} if expr[0] == kind else set()
    require(expr[0] in ('add', 'sub', 'mul', 'div') and len(expr) == 3, 'unsupported expression operation')
    return expression_refs(expr[1], kind) | expression_refs(expr[2], kind)

def expression_dimension(expr, inputs, parameters):
    op = expr[0]
    if op in ('input', 'parameter'):
        registry = inputs if op == 'input' else parameters
        require(expr[1] in registry, 'undeclared operand')
        return tuple(registry[expr[1]]['dimension'])
    a, b = expression_dimension(expr[1], inputs, parameters), expression_dimension(expr[2], inputs, parameters)
    if op in ('add', 'sub'):
        require(a == b, 'addition/subtraction dimensions differ')
        return a
    return tuple(x + (y if op == 'mul' else -y) for x, y in zip(a, b))

def evaluate(expr, inputs, parameters):
    op = expr[0]
    if op == 'input': return rational(inputs[expr[1]])
    if op == 'parameter': return rational(parameters[expr[1]]['value'])
    a, b = evaluate(expr[1], inputs, parameters), evaluate(expr[2], inputs, parameters)
    if op == 'add': return a + b
    if op == 'sub': return a - b
    if op == 'mul': return a * b
    require(op == 'div' and b != 0, 'ratio denominator is zero')
    return a / b

def gradient(expr, inputs, parameters, order):
    op = expr[0]
    if op == 'input': return [Q(int(name == expr[1])) for name in order]
    if op == 'parameter': return [Q(0) for _ in order]
    a, b = evaluate(expr[1], inputs, parameters), evaluate(expr[2], inputs, parameters)
    da, db = gradient(expr[1], inputs, parameters, order), gradient(expr[2], inputs, parameters, order)
    if op == 'add': return [x+y for x,y in zip(da,db)]
    if op == 'sub': return [x-y for x,y in zip(da,db)]
    if op == 'mul': return [x*b+a*y for x,y in zip(da,db)]
    require(b != 0, 'linearization point denominator is zero')
    return [(x*b-a*y)/(b*b) for x,y in zip(da,db)]

def affine(expr):
    """Sufficient structural proof, deliberately not a general simplifier."""
    op = expr[0]
    if op in ('input', 'parameter'): return True
    if op in ('add', 'sub'): return affine(expr[1]) and affine(expr[2])
    left = bool(expression_refs(expr[1], 'input'))
    right = bool(expression_refs(expr[2], 'input'))
    if op == 'mul': return (not left and affine(expr[2])) or (not right and affine(expr[1]))
    return not right and affine(expr[1])

def matrix_rank(matrix):
    a = [list(row) for row in matrix]
    rank = 0
    for col in range(len(a[0])):
        pivot = next((row for row in range(rank, len(a)) if a[row][col]), None)
        if pivot is None: continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][col]
        a[rank] = [v/scale for v in a[rank]]
        for row in range(rank+1, len(a)):
            scale = a[row][col]
            a[row] = [x-scale*y for x,y in zip(a[row], a[rank])]
        rank += 1
    return rank

def seal(record):
    record = deepcopy(record)
    record['code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    record['spec_sha256'] = digest({k: v for k, v in record.items() if k != 'spec_sha256'})
    return record

def model_sha256(record):
    """Computational identity excludes evidence, preventing a self-referential hash."""
    return digest({k: record[k] for k in MODEL_FIELDS})

def validate_output_budgets(record, trusted, operand_sources=None):
    outputs = {p['name']: p for p in record['codomain']}
    require(isinstance(record['error'], dict) and set(record['error']) == set(outputs),
            'error budgets must match output ports')
    complete_operands = operand_sources is not None
    if operand_sources is None:
        operand_sources = {name: {record['parameters'][key]['source_id']:
            trusted[record['parameters'][key]['source_id']]['sha256']
            for key in expression_refs(expr, 'parameter')}
            for name, expr in record['law'].items()}
    evidence_ids, statuses = set(), {}
    for name, output in outputs.items():
        budget = record['error'][name]
        calibration = {identity: binding for identity, binding in operand_sources[name].items()
                       if trusted[identity]['role'] == 'calibration'}
        if calibration:
            require(record['calibration'].get('status') in ('specified', 'unknown'),
                    'calibration source makes calibration applicable')
        statuses[name] = validate_budget(budget, output, trusted,
            model_sha256=model_sha256(record), calibration_sources=calibration)
        require(budget['arithmetic']['kind'] == 'exact', 'rational adapter arithmetic is exact')
        require(budget['model_discrepancy']['kind'] == 'unknown', 'physical discrepancy cannot be resolved by finite arithmetic')
        for component in budget.values():
            if 'evidence' in component:
                evidence_ids.add(component['evidence']['source_id'])
            if complete_operands:
                require(set(component['included_sources']) <= set(operand_sources[name]),
                        'included uncertainty source is not an output operand')
    require(evidence_ids <= {s['id'] for s in record['sources']}, 'evidence must be retained in map sources')
    all_operands = set().union(*(set(sources) for sources in operand_sources.values()))
    require(not evidence_ids & all_operands, 'evidence source cannot also be an operand source')
    return statuses

def validate_map(record, trusted):
    require(set(record) == set(FIELDS), 'map requires all contract fields')
    require(record['id'] and record['version'], 'map identity/version required')
    require(record['code_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'code identity mismatch')
    require(record['spec_sha256'] == digest({k: v for k, v in record.items() if k != 'spec_sha256'}), 'map specification changed')
    require(len(record['domain']) > 0 and len(record['codomain']) > 0, 'domain/codomain required')
    for p in record['domain'] + record['codomain']: validate_port(p)
    inputs = {p['name']: p for p in record['domain']}
    outputs = {p['name']: p for p in record['codomain']}
    require(len(inputs) == len(record['domain']) and len(outputs) == len(record['codomain']), 'duplicate port')
    require(set(record['law']) == set(outputs), 'law output ports differ')
    sources = validate_sources(record['sources'], trusted)
    require(not any(s['role'] == 'evaluation' for s in sources.values()), 'evaluation input leaks into prediction')
    params = record['parameters']
    for name, p in params.items():
        require(set(p) == {'value', 'dimension', 'source_id', 'origin', 'payload_key'}, 'parameter origin required')
        require(p['source_id'] in sources and p['origin'] in ('declared', 'definition', 'fitted'), 'parameter source/origin')
        require(p['payload_key'] in sources[p['source_id']]['payload'], 'parameter source payload key absent')
        require(rational(p['value']) == rational(sources[p['source_id']]['payload'][p['payload_key']]), 'parameter differs from source')
        require(len(p['dimension']) == 3 and all(type(x) is int for x in p['dimension']), 'parameter dimension')
        if p['origin'] == 'fitted':
            require(sources[p['source_id']]['role'] == 'calibration' and name in record['calibration'].get('fitted_parameters', []), 'hidden fitted parameter')
            require(record['calibration'].get('status') == 'specified', 'fitted calibration uncertainty is applicable')
        if p['origin'] == 'definition':
            require(sources[p['source_id']]['role'] == 'definition', 'definition parameter requires definition source')
    used_inputs, used_parameters = set(), set()
    for name, expr in record['law'].items():
        used_inputs |= expression_refs(expr, 'input')
        used_parameters |= expression_refs(expr, 'parameter')
        require(expression_dimension(expr, inputs, params) == tuple(outputs[name]['dimension']), 'output dimension mismatch')
    require(used_inputs <= set(inputs) and used_parameters == set(params), 'unbound or unused parameter')
    for name in ('structure', 'information_loss', 'resolution', 'error', 'calibration', 'comparison', 'status'):
        require(isinstance(record[name], dict) and record[name], 'missing applicable contract record: '+name)
    require(record['comparison'].get('evaluation_sources') == [] and record['comparison'].get('prediction_frozen') is True, 'prediction/evaluation separation')
    for name in ('resolution', 'calibration'):
        item = record[name]
        require(item.get('status') in ('specified', 'unknown', 'not_applicable') and bool(item.get('reason')), 'unknown/not-applicable require a reason')
    injective = record['structure'].get('injective')
    require(type(injective) is bool or injective == 'unknown', 'injectivity must be a boolean or unknown')
    if injective != 'unknown':
        require(all(affine(expr) for expr in record['law'].values()), 'injectivity of nonlinear map is not certified by this adapter')
        order = list(inputs)
        midpoint = {k:(rational(p['bounds'][0])+rational(p['bounds'][1]))/2 for k,p in inputs.items()}
        rank = matrix_rank([gradient(expr, midpoint, params, order) for expr in record['law'].values()])
        if record['structure']['injective'] is True:
            require(rank == len(inputs), 'unique reconstruction requires full column rank')
        else:
            require(rank < len(inputs) and all(rational(p['bounds'][0]) < rational(p['bounds'][1]) for p in inputs.values()), 'noninjectivity requires a nontrivial kernel within a full-dimensional box')
    if record['information_loss'].get('reconstruction') == 'unique':
        require(injective is True, 'unique reconstruction requires proven injectivity')
    if injective is False:
        require(record['information_loss'].get('equivalence') and record['information_loss'].get('task'), 'loss needs equivalence and reconstruction task')
    require(record['status'] == {'arithmetic':'exact within declared domain','physical_applicability':'unknown'}, 'adapter only supports declared exact arithmetic and unknown physical applicability')
    validate_output_budgets(record, trusted)
    return record

def run_map(record, values, trusted):
    validate_map(record, trusted)
    require(set(values) == {p['name'] for p in record['domain']}, 'input port mismatch')
    input_values, provenance, input_sources = {}, {}, {}
    for p in record['domain']:
        v = values[p['name']]
        require(typed_equal(v['port'], p), 'incompatible input type/dimension/unit/scope/lineage')
        q = rational(v['value'])
        require(rational(p['bounds'][0]) <= q <= rational(p['bounds'][1]), 'outside admissible domain')
        require(v['sha256'] == digest({k: v[k] for k in ('port', 'value', 'provenance', 'origin')}), 'input hash mismatch')
        origin = v['origin']
        require(isinstance(origin, dict), 'bound input origin required')
        if origin.get('kind') == 'source':
            require(set(origin) == {'kind','source_id','payload_key'}, 'raw input source path required')
            require(origin['source_id'] in trusted and origin['source_id'] in v['provenance'], 'raw input source unbound')
            payload = trusted[origin['source_id']]['payload']
            require(origin['payload_key'] in payload and rational(payload[origin['payload_key']]) == q, 'input value differs from bound source payload')
            input_sources[p['name']] = {origin['source_id']: trusted[origin['source_id']]['sha256']}
        else:
            require(origin.get('kind') == 'map_output' and set(origin) == {'kind','map','inputs','output','execution_sha256'}, 'validated upstream execution required')
            upstream = run_map(origin['map'], origin['inputs'], trusted)
            require(upstream['outputs'].get(origin['output']) == v, 'upstream execution/output identity mismatch')
            input_sources[p['name']] = upstream['operand_sources'][origin['output']]
        for identity, binding in v['provenance'].items():
            require(identity not in provenance or provenance[identity] == binding, 'shared source has conflicting bindings')
            require(identity in trusted and trusted[identity]['sha256'] == binding, 'input provenance unbound')
            require(trusted[identity]['id'] == identity and trusted[identity]['sha256'] == digest(trusted[identity]['payload']), 'input source content hash mismatch')
            require(trusted[identity]['role'] != 'evaluation', 'evaluation input leaks through upstream map')
            provenance[identity] = binding
        input_values[p['name']] = q
    for s in record['sources']:
        require(s['id'] not in provenance or provenance[s['id']] == s['sha256'], 'shared source mismatch')
        provenance[s['id']] = s['sha256']
    operand_sources = {}
    for name, expr in record['law'].items():
        operands = {record['parameters'][key]['source_id']:
                    trusted[record['parameters'][key]['source_id']]['sha256']
                    for key in expression_refs(expr, 'parameter')}
        for key in expression_refs(expr, 'input'):
            operands.update(input_sources[key])
        operand_sources[name] = operands
    validate_output_budgets(record, trusted, operand_sources)
    outputs = {}
    for p in record['codomain']:
        q = evaluate(record['law'][p['name']], input_values, record['parameters'])
        require(rational(p['bounds'][0]) <= q <= rational(p['bounds'][1]), 'output outside declared codomain')
        execution = {'map_spec_sha256':record['spec_sha256'],'inputs_sha256':digest(values),'output':p['name'],'value':str(q),
                     'provenance':provenance,'operand_sources':operand_sources[p['name']]}
        origin = {'kind':'map_output','map':deepcopy(record),'inputs':deepcopy(values),'output':p['name'],'execution_sha256':digest(execution)}
        outputs[p['name']] = value(p, q, provenance, origin)
    return {'map_id': record['id'], 'spec_sha256': record['spec_sha256'], 'input_sha256': digest(values), 'outputs': outputs,
            'provenance': provenance, 'operand_sources': operand_sources}

def value(p, q, provenance, origin=None):
    result = {'port': deepcopy(p), 'value': str(rational(q)), 'provenance': dict(provenance), 'origin':deepcopy(origin)}
    result['sha256'] = digest(result)
    return result

def compose(first, second, initial, trusted):
    require(len(first['codomain']) == len(second['domain']) == 1, 'composition adapter requires one intermediate port')
    a, b = first['codomain'][0], second['domain'][0]
    require(typed_equal(a, b), 'incompatible composition domains')
    require(rational(b['bounds'][0]) <= rational(a['bounds'][0]) <= rational(a['bounds'][1]) <= rational(b['bounds'][1]), 'intermediate image not covered by second domain')
    one = run_map(first, initial, trusted)
    two = run_map(second, {b['name']: one['outputs'][a['name']]}, trusted)
    return {'stages': [one, two], 'shared_sources': sorted(set(one['provenance']) & {s['id'] for s in second['sources']}),
            'provenance': two['provenance']}

def validate_budget(budget, output_port, trusted, *, model_sha256, calibration_sources=()):
    """Bind each output error to its unit and a separately trusted evidence payload.

    A bound remains a conditional source declaration. A standard uncertainty is
    checked against the finite output-error law in that same evidence payload.
    """
    validate_port(output_port)
    require(isinstance(budget, dict) and set(budget) == set(ERROR_COMPONENTS), 'all applicable error components must be explicit')
    calibration_sources = dict(calibration_sources)
    covered = set()
    for name, component in budget.items():
        require(isinstance(component, dict), 'typed error component required')
        kind = component.get('kind')
        require(kind in ('exact', 'bound', 'standard_uncertainty', 'unknown', 'not_applicable'), 'error kind')
        fields = {'kind', 'unit', 'reason', 'included_sources'}
        if kind == 'exact': fields.add('value')
        if kind in ('bound', 'standard_uncertainty'): fields |= {'value', 'evidence'}
        require(set(component) == fields, 'error component fields; unknown/inapplicable is not zero')
        require(component['unit'] == output_port['unit'], 'error unit differs from output unit')
        require(isinstance(component['reason'], str) and bool(component['reason'].strip()), 'error reason required')
        included = component['included_sources']
        require(isinstance(included, dict), 'included sources require identity/hash bindings')
        for identity, binding in included.items():
            require(identity in trusted and trusted[identity]['sha256'] == binding, 'included source binding mismatch')
            validate_sources([trusted[identity]], trusted)
            require(trusted[identity]['role'] != 'evaluation', 'evaluation evidence cannot certify prediction')
            require(identity not in covered, 'uncertainty source counted twice')
            covered.add(identity)
        if kind in ('exact', 'not_applicable'):
            require(not included, 'exact/inapplicable component cannot absorb uncertain sources')
        if kind in ('unknown', 'not_applicable'):
            continue
        require(rational(component['value']) >= 0, 'nonnegative error value required')
        if kind == 'exact':
            require(name in ('arithmetic', 'propagation', 'solver') and rational(component['value']) == 0,
                    'evidence-free exact zero is restricted to computational components')
        else:
            ref = component['evidence']
            require(isinstance(ref, dict) and set(ref) == {'source_id', 'payload_key', 'sha256'}, 'trusted evidence reference required')
            require(ref['source_id'] in trusted, 'unbound evidence source')
            item = trusted[ref['source_id']]
            validate_sources([item], trusted)
            require(item['role'] != 'evaluation', 'evaluation evidence cannot certify prediction')
            require(ref['sha256'] == item['sha256'], 'evidence source hash mismatch')
            require(ref['source_id'] not in included, 'evidence source cannot include itself')
            require(isinstance(item['payload'], dict) and ref['payload_key'] in item['payload'], 'evidence payload key absent')
            payload = item['payload'][ref['payload_key']]
            expected = {'model_sha256': model_sha256, 'output': output_port['name'],
                        'component': name, 'kind': kind, 'unit': component['unit'],
                        'value': component['value'], 'included_sources': included}
            payload_fields = set(expected) | ({'joint_law'} if kind == 'standard_uncertainty' else set())
            require(isinstance(payload, dict) and set(payload) == payload_fields, 'evidence payload fields')
            require(all(payload[key] == val for key, val in expected.items()), 'evidence disagrees with output/component/model/value/source binding')
            if kind == 'standard_uncertainty':
                law = payload['joint_law']
                require(isinstance(law, list) and law, 'standard uncertainty needs joint law')
                rows, mean, cov = joint_moments(law, ['error'])
                require(rational(component['value'])**2 == cov[0][0], 'standard uncertainty disagrees with supplied law')
    if calibration_sources:
        component = budget['calibration']
        require(component['kind'] in ('unknown', 'bound', 'standard_uncertainty'),
                'real calibration uncertainty cannot be omitted or asserted exact')
        require(all(component['included_sources'].get(identity) == binding
                    for identity, binding in calibration_sources.items()), 'calibration source inclusion required')
    return {'status': 'partial' if any(c['kind'] == 'unknown' for c in budget.values()) else 'specified'}

def validate_psd(matrix):
    n = len(matrix)
    require(n > 0 and all(len(row) == n for row in matrix), 'square covariance required')
    a = [[rational(x) for x in row] for row in matrix]
    require(all(a[i][j] == a[j][i] for i in range(n) for j in range(n)), 'covariance is not symmetric')
    # Exact Schur-complement elimination handles valid singular matrices.
    for k in range(n):
        pivot = a[k][k]
        require(pivot >= 0, 'covariance is not positive semidefinite')
        if pivot == 0:
            require(all(a[k][j] == 0 for j in range(k+1, n)), 'zero pivot has nonzero covariance')
        else:
            for i in range(k+1, n):
                for j in range(k+1, n):
                    a[i][j] -= a[i][k]*a[k][j]/pivot
    return [[rational(x) for x in row] for row in matrix]

def quadratic(j, covariance):
    a = validate_psd(covariance)
    require(len(j) == len(a), 'Jacobian/covariance dimension mismatch')
    return sum(rational(j[i])*a[i][k]*rational(j[k]) for i in range(len(j)) for k in range(len(j)))

def joint_moments(support, order):
    require(support and len(set(order)) == len(order), 'finite support and distinct source identities required')
    rows = [(rational(p), {k:rational(v) for k,v in point.items()}) for p,point in support]
    require(all(p > 0 and set(v) == set(order) for p,v in rows), 'joint support dimensions/probabilities')
    require(sum(p for p,v in rows) == 1, 'joint probabilities must sum to one')
    means = {k:sum(p*v[k] for p,v in rows) for k in order}
    cov = [[sum(p*(v[i]-means[i])*(v[j]-means[j]) for p,v in rows) for j in order] for i in order]
    validate_psd(cov)
    return rows, means, cov

def propagate(expr, order, parameters, means=None, covariance=None, support=None):
    """Exact joint law when supplied; covariance-only nonlinear claims stay partial."""
    require(len(order) == len(set(order)), 'distinct input source identities required')
    require(set(order) == expression_refs(expr, 'input'), 'input identities differ from expression')
    if support is not None:
        rows, mean, cov = joint_moments(support, order)
        if means is not None: require({k:rational(v) for k,v in means.items()} == mean, 'means disagree with joint law')
        if covariance is not None: require(validate_psd(covariance) == cov, 'covariance disagrees with joint law')
    else:
        require(means is not None and covariance is not None and set(means) == set(order), 'means and full covariance required')
        mean, cov = {k:rational(v) for k,v in means.items()}, validate_psd(covariance)
    require(len(cov) == len(order), 'covariance/order dimensions')
    try:
        nominal = evaluate(expr, mean, parameters)
        jac = gradient(expr, mean, parameters, order)
        linear = quadratic(jac, cov)
    except ContractError:
        if support is None: raise
        nominal, jac, linear = None, None, None
    result = {'nominal':None if nominal is None else str(nominal), 'input_order':order, 'input_mean':{k:str(v) for k,v in mean.items()},
              'input_covariance':[[str(x) for x in r] for r in cov], 'jacobian':None if jac is None else [str(x) for x in jac],
              'linearized_variance_diagnostic':None if linear is None else str(linear), 'arithmetic':'exact rational',
              'output_mean':None, 'output_variance':None, 'mean_shift':None,
              'uncertainty_status':'partial', 'adequacy':'unresolved nonlinear propagation; marginal size is insufficient'}
    if support is not None:
        ys = [(p,evaluate(expr,point,parameters)) for p,point in rows]
        average = sum(p*y for p,y in ys)
        variance = sum(p*(y-average)**2 for p,y in ys)
        result.update(output_mean=str(average), output_variance=str(variance), mean_shift=None if nominal is None else str(average-nominal),
                      uncertainty_status='exact_for_declared_joint_law', adequacy='full finite-support propagation',
                      support=[{'p':str(p),'output':str(y)} for p,y in ys],
                      linearized_variance_difference=None if linear is None else str(variance-linear))
    elif affine(expr):
        result.update(output_mean=str(nominal), output_variance=str(linear), mean_shift='0',
                      uncertainty_status='exact_for_declared_affine_model', adequacy='structural affine proof')
    return result

def ratio_bounds(numerator, denominator):
    a,b = map(rational,numerator); c,d = map(rational,denominator)
    require(a <= b and c <= d, 'ordered ratio domains required')
    if c <= 0 <= d:
        return {'status':'undefined_or_unbounded', 'reason':'denominator domain contains zero', 'bounds':None}
    values = [x/y for x in (a,b) for y in (c,d)]
    return {'status':'bounded', 'bounds':[str(min(values)),str(max(values))]}

def composed_bound(bf, bg, intermediate, g_domain, operation, coefficient='1'):
    bf,bg = rational(bf),rational(bg)
    require(bf >= 0 and bg >= 0, 'nonnegative uniform bounds required')
    lo,hi = map(rational,intermediate); a,b = map(rational,g_domain)
    require(a <= lo-bf <= hi+bf <= b, 'both true and approximated images must lie in outer domain')
    require(lo <= hi, 'ordered intermediate interval')
    if operation == 'affine': L = abs(rational(coefficient))
    else:
        require(operation == 'reciprocal' and not a <= 0 <= b, 'reciprocal Lipschitz domain crosses zero')
        L = 1/min(abs(a),abs(b))**2
    return {'bound':str(bg+L*bf), 'L':str(L), 'hypotheses':{'uniform_inner_bound':str(bf), 'uniform_outer_bound':str(bg),
            'intermediate':[str(lo),str(hi)], 'outer_domain':[str(a),str(b)], 'outer_law':operation},
            'scope':'conditional bound given the two stated uniform approximation bounds'}

def parse_printed(token, unit, zero_policy, rounding_policy='nearest_to_printed_last_place'):
    """Rounding is a deterministic enclosure; raw-byte integrity is separate."""
    require(unit in ('1', 'Hz', 'Hz^2', 's', 's^2'), 'declared source unit required')
    from decimal import Decimal, InvalidOperation
    try: d = Decimal(token)
    except InvalidOperation as exc: raise ContractError('invalid printed decimal') from exc
    require(d.is_finite(), 'finite printed decimal required')
    number = Q(d)
    if number == 0:
        require(zero_policy in ('documented_exact_zero', 'rounded_to_last_place', 'unknown'), 'printed zero interpretation required')
        if zero_policy == 'unknown': return {'value':'0', 'bound':None, 'status':'unknown', 'unit':unit}
        if zero_policy == 'documented_exact_zero': return {'value':'0', 'bound':'0', 'status':'exact_source_convention', 'unit':unit}
    require(rounding_policy == 'nearest_to_printed_last_place', 'unsupported or unknown rounding policy')
    rounding = Q(10)**d.as_tuple().exponent/2
    return {'value':str(number), 'bound':str(rounding), 'status':'conditional_deterministic_rounding_bound',
            'unit':unit,'rounding_policy':rounding_policy,'scope':'conditional on nearest rounding to the last printed place; source convention must justify application'}

def reference_uncertainty(kind, variance=None):
    require(kind in ('defining_constant', 'realized_reference'), 'reference kind')
    if kind == 'defining_constant':
        require(variance is not None and rational(variance) == 0, 'defining constant has exactly zero measurement variance')
        return {'kind':kind,'variance':'0','status':'definition_only'}
    if variance is None:
        return {'kind':kind,'variance':None,'status':'partial; realization uncertainty unknown'}
    require(rational(variance) >= 0, 'nonnegative realized variance required')
    return {'kind':kind,'variance':str(rational(variance)),'status':'declared realization input; other budget components remain applicable'}

def default_budget(output_port):
    validate_port(output_port)
    result = {}
    for name in ERROR_COMPONENTS:
        kind = 'exact' if name in ('arithmetic', 'propagation', 'solver') else 'not_applicable'
        if name == 'model_discrepancy': kind = 'unknown'
        result[name] = {'kind':kind, 'unit':output_port['unit'], 'included_sources':{},
                        'reason':'exact rational operation' if kind == 'exact' else ('no physical observation model supplied' if kind == 'unknown' else 'no '+name+' operation in this example')}
        if kind == 'exact': result[name]['value'] = '0'
    return result

def example_map(identity='map:scale', factor='2', source_record=None):
    s = source_record or source('model:scale','model',{'factor':factor,'input':'3'})
    return seal({'id':identity, 'version':'2', 'domain':[port('x',bounds=('-10','10'))],
        'codomain':[port('y',bounds=('-20','20'))], 'law':{'y':['mul',['input','x'],['parameter','factor']]},
        'parameters':{'factor':{'value':factor, 'dimension':[0,0,0], 'source_id':s['id'], 'payload_key':'factor','origin':'declared'}},
        'sources':[s], 'structure':{'injective':rational(factor)!=0, 'invariance':'retains input identity in provenance'},
        'information_loss':{'task':'recover x from y', 'reconstruction':'unique' if rational(factor)!=0 else 'nonunique', 'equivalence':'x values with equal output'},
        'resolution':{'status':'not_applicable','reason':'exact finite rational input'}, 'error':{'y':default_budget(port('y'))},
        'calibration':{'status':'not_applicable','reason':'declared algebraic parameter, no device'},
        'comparison':{'evaluation_sources':[], 'prediction_frozen':True},
        'status':{'arithmetic':'exact within declared domain','physical_applicability':'unknown'}})

def report():
    s = source('model:scale','model',{'factor':'2','input':'3','hidden0':'0','hidden1':'1'})
    trusted = {s['id']:s}
    f = example_map(source_record=s)
    g = example_map('map:scale-again', source_record=s)
    g['domain'][0]['bounds'] = ['-20','20']; g['codomain'][0]['bounds'] = ['-40','40']; g = seal(g)
    x = value(f['domain'][0], '3', {s['id']:s['sha256']}, {'kind':'source','source_id':s['id'],'payload_key':'input'})
    chain = compose(f,g,{'x':x},trusted)
    # New exact rational controls. The unavailable R01 bytes are NOT reconstructed by naming these historic.
    points = [(Q(1,4),Q(-1,100)),(Q(1,2),Q(0)),(Q(1,4),Q(1,100))]
    interval_expr = ['div',['input','cycles'],['mul',['input','ratio'],['input','frequency']]]
    interval_law = [(str(p),{'cycles':'1','ratio':str(1+d),'frequency':str(1-d)}) for p,d in points]
    product_expr = ['mul',['input','ratio'],['input','frequency']]
    product_law = [(str(p),{'ratio':str(1+d),'frequency':str(1-Q(999,1000)*d)}) for p,d in points]
    old_product_law = [('1/4',{'ratio':'1/2','frequency':'3/2'}),('1/2',{'ratio':'1','frequency':'1'}),('1/4',{'ratio':'3/2','frequency':'1/2'})]
    offset_expr = ['sub',['input','end'],['input','start']]
    offset = propagate(offset_expr,['end','start'],{},means={'end':'7','start':'2'},covariance=[['4','4'],['4','4']])
    constant = propagate(['div',['input','x'],['input','x']],['x'],{},support=[('1/2',{'x':'1'}),('1/2',{'x':'2'})])
    projection = example_map('map:project', source_record=s)
    projection['domain']=[port('x'),port('hidden')];projection['codomain']=[port('y')]
    projection['law']={'y':['input','x']};projection['parameters']={}
    projection['structure']={'injective':False,'invariance':'changing hidden coordinate preserves output'}
    projection['information_loss']={'task':'recover the hidden coordinate','reconstruction':'nonunique','equivalence':'equal x, arbitrary hidden coordinate'}
    projection=seal(projection)
    witnesses=[]
    for hidden in ('0','1'):
        v={p['name']:value(p,'3' if p['name']=='x' else hidden,{s['id']:s['sha256']},
           {'kind':'source','source_id':s['id'],'payload_key':'input' if p['name']=='x' else 'hidden'+hidden}) for p in projection['domain']}
        witnesses.append(run_map(projection,v,trusted))
    return {'schema':'aod.m3.mapping-error.v2', 'scope':'exact declared finite models; physical model discrepancy remains unknown',
      'contracts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'contracts/scientific/MAP_CONTRACT.json',ROOT/'contracts/scientific/ERROR_BUDGET.json')},
      'maps':[f,g,projection], 'composition':chain, 'exact_lossy_projection':{'witnesses':witnesses,'arithmetic_error':'0','hidden_coordinate_reconstruction':'nonunique; no scalar reconstruction error asserted'},
      'interval_zero_linear_control':propagate(interval_expr,['cycles','ratio','frequency'],{},support=interval_law),
      'near_cancelled_product_control':propagate(product_expr,['ratio','frequency'],{},support=product_law),
      'historical_product_regression':propagate(product_expr,['ratio','frequency'],{},support=old_product_law),
      'historical_probe_status':{'r01_probe':'unavailable in supplied R02 archive or local filename/text search',
        'expected_file':'probe_metrology_edges.py','expected_sha256':'685f4b2b077d2cde88f2e275800e088d156ed006aa82b648608743d3b670582e',
        'fidelity':'MAP-21/MAP-22 historical exact replay remains partial; new controls do not replace the missing original law',
        'recovered_product':'separate historical consumer test: delta=-1/2,0,1/2; probabilities 1/4,1/2,1/4; mean 7/8 and variance 1/64'},
      'legitimate_common_offset_cancellation':offset, 'constant_on_declared_support':constant,
      'covariance_only_nonlinear':propagate(product_expr,['ratio','frequency'],{},means={'ratio':'1','frequency':'1'},covariance=[['1/20000','-1/20000'],['-1/20000','1/20000']]),
      'ratio_domain':ratio_bounds(('1','2'),('-1','1')),
      'bounded_ratio':ratio_bounds(('1','2'),('2','3')),
      'composed_bound':composed_bound('1/100','1/1000',('1','2'),('1/2','3'),'reciprocal'),
      'reference_definition':reference_uncertainty('defining_constant','0'),
      'reference_realization':reference_uncertainty('realized_reference'),
      'printed_precision':{'zero_unknown':parse_printed('0.0E-34','Hz^2','unknown'),'zero_documented':parse_printed('0.0E-34','Hz^2','documented_exact_zero'),
                           'nonzero':parse_printed('1.234E-4','Hz^2','unknown'),'scope':'synthetic parser controls; no new BIPM-source interpretation'},
      'error_budget':deepcopy(f['error']), 'error_budget_status':validate_output_budgets(f, trusted)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true');group.add_argument('--check', action='store_true')
    parser.add_argument('--output',type=Path,default=REPORT)
    args=parser.parse_args()
    data=json.dumps(report(),indent=2,sort_keys=True)+'\n'
    if args.write: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(data)
    elif args.check: require(args.output.read_text()==data,'stored mapping/error report differs from reconstruction')
    else: print(data,end='')
    if args.write or args.check: print(json.dumps({'report':str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),'mode':'write' if args.write else 'check','status':'reconstructed'}))

if __name__ == '__main__': main()
