import csv
import re
from pathlib import Path

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

base = Path(__file__).resolve().parent / 'csv'
l2 = sp.log(sp.Rational(3, 2), 3)
TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def z3(x):
    return {0: 0, 1: 1, -1: 2}[x]


def bt(x):
    return {0: 0, 1: 1, 2: -1}[x]


def xor3(a, b):
    return bt((z3(a) + z3(b)) % 3)


def parse_native_expr(expr: str):
    expr = expr.strip().strip('"').strip("'")
    expr = expr.replace(r'\\,', '').replace(r'\,', '')
    expr = expr.replace(r'\\ell_2', 'l2').replace(r'\ell_2', 'l2')
    expr = expr.replace(r'\\frac', r'\frac').replace(r'\frac', r'\frac')
    frac_pat = re.compile(r'\\frac\{([^{}]+)\}\{([^{}]+)\}')
    prev = None
    while prev != expr:
        prev = expr
        expr = frac_pat.sub(r'(\1)/(\2)', expr)
    expr = expr.replace('^', '**')
    return sp.simplify(parse_expr(expr, local_dict={'l2': l2}, transformations=TRANSFORMS, evaluate=True))


lines = []
# E4
with open(base / 'E4_loss_channel.csv', newline='') as f:
    for row in csv.DictReader(f):
        n1 = int(row['n1'])
        n2 = int(row['n2'])
        teval = int(row['Teval_bip'])
        bstar = int(row['Bstar'])
        lam = int(row['Lambda_b'])
        rrest_expected = sp.simplify((n1 + n2 * l2) / teval)
        rrest_given = parse_native_expr(row['Rloss_expr'])
        assert sp.simplify(rrest_expected - rrest_given) == 0
        rbiz_expected = sp.simplify((sp.Integer(3) ** rrest_expected - 1) * sp.Integer(bstar) ** (-lam))
        rbiz_given = parse_native_expr(row['Rloss_biz_expr'])
        assert sp.simplify(rbiz_expected - rbiz_given) == 0
        lines.append(f"{row['row']}: E4 chain verified")

# E5
with open(base / 'E5_bstar_ladder.csv', newline='') as f:
    for row in csv.DictReader(f):
        samples = [int(x) for x in row['samples'].split(';')]
        from collections import Counter
        c = Counter(samples)
        bstar = max(c.items(), key=lambda kv: (kv[1], -samples.index(kv[0])))[0]
        assert bstar == int(row['Bstar'])
        lines.append(f"{row['row']}: B* mode verified")

# E6
with open(base / 'E6_collision_export.csv', newline='') as f:
    for row in csv.DictReader(f):
        a = int(row['a'])
        b = int(row['b'])
        out = int(row['a_xor3_b'])
        assert xor3(a, b) == out
        qeff = sp.Rational(a + b, 4)
        assert sp.simplify(qeff - parse_native_expr(row['qeff'])) == 0
        lines.append(f"{row['row']}: ternary gate and q_eff verified")

# E7 consistency with E4.B
with open(base / 'E7_field_property_schema.csv', newline='') as f:
    rows = list(csv.DictReader(f))
vals = {r['field_property']: r['reported_native_value'] for r in rows}
assert vals['AO field key'] == 'O-tetrad:3:4:6'
assert '(1 + 8*log(3/2,3))/24' in vals['Rloss']
assert '137**(-6)' in vals['Rloss_biz']
lines.append('E7: schema row matches loss-channel family row')

# E8 / E9 existence
for name in ['E8_short_window_confinement.csv', 'E9_duon_duad_family.csv']:
    assert (base / name).exists()
    lines.append(f"{name}: present")

# E11 existence and q_eff_hat consistency
with open(base / 'E11_open_seat_wavelet_summary.csv', newline='') as f:
    rows = list(csv.DictReader(f))
assert len(rows) > 0
q = []
qh = []
for row in rows:
    q_val = parse_native_expr(row['q_eff'])
    qh_val = parse_native_expr(row['q_eff_hat'])
    q.append(q_val)
    qh.append(qh_val)
    assert qh_val >= -1 and qh_val <= 1
    if q_val > 0:
        assert qh_val > 0
    elif q_val < 0:
        assert qh_val < 0
    else:
        assert qh_val > -1 and qh_val < 1
assert all(qh[i] < qh[i + 1] for i in range(len(qh) - 1))
assert sp.simplify(qh[0] + 1) == 0
assert sp.simplify(qh[-1] - 1) == 0
lines.append('E11: open-seat wavelet rows present; q_eff_hat bounds/sign/monotonicity/endpoints verified')

report = '\n'.join(lines)
print(report)
(Path(__file__).resolve().parent / 'verify_report.txt').write_text(report)
