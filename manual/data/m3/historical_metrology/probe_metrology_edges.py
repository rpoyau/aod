#!/usr/bin/env python3
"""Read-only review probes for f2dcf014; no source or persisted data changes.

Run with --repo CHECKOUT, normally and with python -O. Exact finite-support
oracles expose limitations of first-order uncertainty. The BIPM probe tests
the numerical helper, not the raw-file manifest guard. --expect-repaired
fails while the two uncertainty completeness defects remain; BIPM treatment
also needs a documented zero-format policy and is reported separately.
"""
import argparse
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise ValueError(message)


def moments(values, weights):
    mean = sum(v*w for v, w in zip(values, weights))
    variance = sum(w*(v-mean)**2 for v, w in zip(values, weights))
    return mean, variance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--expect-repaired', action='store_true')
    args = parser.parse_args()
    root = args.repo.resolve()
    sys.path.insert(0, str(root/'manual2/scripts'))
    import matter1_metrology as m
    import matter1_bipm as b
    paths = [root/'manual2/scripts/matter1_metrology.py', root/'manual2/scripts/matter1_bipm.py']
    paths += sorted((root/b.REL/'raw').glob('ClockOutput*.dat'))
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    # R1a. All covariance and budget validation succeeds. y and d/s are
    # the same equally likely +/-a variable; C=f_Cs exactly.
    record = m.default_input(root)
    a = Q(1, 1000)
    cov = [[Q(0), Q(0), Q(0)], [Q(0), a*a, a*a], [Q(0), a*a, a*a]]
    m.validate_psd(cov)
    record['covariance'] = m.covariance_record(cov,
        ['physical_cycles', 'fractional_offset', 'endpoint_correction'], ['cycle', '1', 's'])
    for row, sigma in zip(record['budget'], [Q(0), a, a]):
        row['standard_uncertainty'] = str(sigma)
    interval = m.interval(record, root)
    mean_i, variance_i = moments([1/(1+y)+y for y in [-a, a]], [Q(1,2), Q(1,2)])
    require(mean_i == 1/(1-a*a) and variance_i == a**6/(1-a*a)**2, 'Interval oracle')
    interval_bad = (interval['uncertainty_status'] == 'complete_first_order_synthetic'
                    and interval['variance_seconds2'] == '0')

    # R1b. Near cancellation evades an exact-zero guard. Both marginal
    # uncertainties are below 0.1 percent, well inside the 1 percent guard.
    eps, delta = Q(1, 1000), Q(1, 1000000)
    vx = eps**2/2
    product = m.frequency_from_ratio('1', vx, reference_hz='1',
        reference_variance=(1-delta)**2*vx,
        ratio_reference_covariance=-(1-delta)*vx, reference_kind='realized_reference')
    mean_p, variance_p = moments([(1+x)*(1-(1-delta)*x) for x in [-eps, 0, eps]],
                                  [Q(1,4), Q(1,2), Q(1,4)])
    linear_variance_p = delta**2*vx
    require(variance_p == linear_variance_p+(1-delta)**2*eps**4/4, 'Product oracle')
    product_bad = (product['uncertainty_status'] == 'complete_first_order_conditional'
                   and product['frequency_variance_hz2'] is not None
                   and Q(product['frequency_variance_hz2']) == linear_variance_p)

    # R2. Changing one ratio sigma by about 2% survives the numerical check
    # because printed zero off-diagonal entries are expanded to +/-5e-6.
    raw = root/b.REL/'raw'
    covariance_text = next(raw.glob('ClockOutputCovData*')).read_text()
    output_text = next(raw.glob('ClockOutputData20*')).read_text()
    line = next(s for s in output_text.splitlines() if s.startswith('nu9/nu14 '))
    match = re.search(r'\+/- ([\d.eE+-]+)', line)
    original = match.group(1)
    altered = format(Decimal(original)*Decimal('1.02'), '.3e')
    altered_line = line[:match.start(1)]+altered+line[match.end(1):]
    try:
        b.covariance_checks(covariance_text, output_text.replace(line, altered_line, 1))
        sigma_mutation_accepted = True
    except ValueError:
        sigma_mutation_accepted = False
    # A control with zero entries retained as exact rejects the same mutation.
    source_cell = b.cell
    try:
        b.cell = lambda token: (Q(0), Q(0)) if Q(token) == 0 else source_cell(token)
        b.covariance_checks(covariance_text, output_text)
        try:
            b.covariance_checks(covariance_text, output_text.replace(line, altered_line, 1))
            zero_exact_rejects = False
        except ValueError:
            zero_exact_rejects = True
    finally:
        b.cell = source_cell

    after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    require(before == after, 'Read-only probe changed source bytes')
    result = {
        'scope': 'accepted synthetic API inputs and a numerical source-data helper; not physical measurements or a frozen-fixture verifier bypass',
        'source_sha256': before, 'read_only': before == after,
        'R1a_interval': {
            'distribution': 'C=f_Cs exactly; y=d/s equally +/-0.001; T/s=1/(1+y)+y',
            'input_record': record, 'output': interval,
            'exact_mean_seconds': str(mean_i), 'exact_variance_seconds2': str(variance_i),
            'exact_standard_uncertainty_seconds': m.sqrt_display(variance_i),
            'unsafe_complete_first_order_result_reproduced': interval_bad,
        },
        'R1b_near_cancelled_product': {
            'distribution': 'x={-0.001,0,0.001}, p={1/4,1/2,1/4}; R=1+x; f/Hz=1-(1-1e-6)*x',
            'output': product, 'exact_mean_hz': str(mean_p),
            'exact_variance_hz2': str(variance_p),
            'linearized_variance_hz2': str(linear_variance_p),
            'variance_ratio_exact_to_linearized': str(variance_p/linear_variance_p),
            'unsafe_complete_first_order_result_reproduced': product_bad,
        },
        'R2_BIPM_zero_cell': {
            'ratio': '9/14', 'original_sigma': original, 'altered_sigma': altered,
            'printed_zero_cell': [str(x) for x in b.cell('0.00000e+00')],
            'altered_sigma_accepted_by_numerical_helper': sigma_mutation_accepted,
            'original_105_pass_with_zero_exact_control': True,
            'zero_exact_control_rejects_mutation': zero_exact_rejects,
            'limit': 'Raw-source hash guard still rejects a modified delivered file. Clarify/justify the source zero-format convention; this probe does not establish a new physical covariance.'
        }
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.expect_repaired:
        require(not interval_bad and not product_bad, 'Uncertainty completeness defects remain')


if __name__ == '__main__':
    main()
