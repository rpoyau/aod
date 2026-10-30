"""Exact consequences of the declared D.E.C. CSV inputs.

These are arithmetic checks on finite examples, not a derivation of their
chosen weights or an empirical test. The slide pool has its own weights.
"""
import ast
import csv
from copy import deepcopy
from fractions import Fraction as Q
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual/scripts'))
import aod_native_closure_wave as n

DATA = ROOT / 'manual/data/dec'
ROUTES = {-1: 'returned', 0: 'hinge', 1: 'outgoing'}


def _read(name):
    with (DATA / name).open(newline='') as source:
        return list(csv.DictReader(source))


def _normalize(weights, admitted):
    """Independent finite normalization, with structural/weighted emptiness."""
    assert len(weights) == len(admitted)
    assert all(weight >= 0 for weight in weights), 'negative weight'
    assert all(type(flag) is bool for flag in admitted), 'boolean admissibility required'
    total = sum((weight for weight, flag in zip(weights, admitted) if flag), Q(0))
    if not any(admitted):
        return 'EMPTY_ADMISSIBLE_SUPPORT', total, []
    if total == 0:
        return 'EMPTY_POSITIVE_WEIGHT_SUPPORT', total, []
    return 'NORMALIZED', total, [weight / total if flag else Q(0)
                                 for weight, flag in zip(weights, admitted)]


def _one_node(rows):
    weights, admitted = [], []
    for row in rows:
        neighbor = ast.literal_eval(row['neighbor'])
        assert len(neighbor) == 4 and all(type(bit) is int and bit in (0, 1) for bit in neighbor)
        assert sum(neighbor) == 1, 'one-node channel must be Hamming-1'
        role = int(row['state'])
        assert role in ROUTES and row['route'] == ROUTES[role], 'route does not match role'
        assert row['admissible'] in ('0', '1'), 'invalid admissibility'
        weights.append(Q(row['weight']))
        admitted.append(row['admissible'] == '1')
    assert len({row['edge'] for row in rows}) == len(rows), 'duplicate edge'
    assert len({row['neighbor'] for row in rows}) == len(rows), 'duplicate neighbor'
    status, total, probabilities = _normalize(weights, admitted)
    assert status == 'NORMALIZED', status
    assert [Q(row['probability_exact']) for row in rows] == probabilities, 'recorded probability disagrees with weights'
    routes = {route: sum((p for row, p in zip(rows, probabilities) if row['route'] == route), Q(0))
              for route in ROUTES.values()}
    assert sum(routes.values(), Q(0)) == 1
    return total, probabilities, routes


def _slide(rows):
    # No mapping from the old one-node weights is assumed: these are separately
    # declared branch weights, not a normalization of the old non-hinge rows.
    weights = [Q(int(row['weight_num']), int(row['weight_den'])) for row in rows]
    for row in rows:
        match = re.fullmatch(r'\((e[1-9][0-9]*),([+-]1)\)', row['branch'])
        assert match, 'slide requires a declared branch role'
        assert row['route'] == ROUTES[int(match[2])], 'route does not match role'
    assert len({row['branch'] for row in rows}) == len(rows), 'duplicate slide branch'
    status, total, probabilities = _normalize(weights, [True] * len(rows))
    assert status == 'NORMALIZED', status
    assert [Q(row['probability_exact']) for row in rows] == probabilities, 'recorded slide probability disagrees with weights'
    routes = {route: sum((p for row, p in zip(rows, probabilities) if row['route'] == route), Q(0))
              for route in ('returned', 'outgoing')}
    assert sum(routes.values(), Q(0)) == 1
    return total, probabilities, routes


def _window(rows, slide):
    total, probabilities, _ = _slide(slide)
    branches = {row['branch'][1:-1].replace(',', ':'): (row, probability)
                for row, probability in zip(slide, probabilities)}
    assert len(rows) == len(branches) and len({row['slide_branch'] for row in rows}) == len(rows)
    contributions = []
    for row in rows:
        declared, probability = branches[row['slide_branch']]
        assert row['scope_B'] == 'B|t' and row['direct_hinge'] == 'e0'
        assert row['direct_adm'] == '0', 'direct hinge must be blocked in this example'
        weight = Q(int(row['slide_weight_num']), int(row['slide_weight_den']))
        assert weight == Q(int(declared['weight_num']), int(declared['weight_den']))
        assert Q(int(row['Z_num']), int(row['Z_den'])) == total, 'recorded normalizer disagrees'
        assert Q(int(row['P_num']), int(row['P_den'])) == probability, 'recorded probability disagrees'
        assert row['is_tunnel_branch'] in ('0', '1')
        if row['is_tunnel_branch'] == '1':
            assert declared['route'] == 'outgoing', 'tunnel successor must be outgoing'
            duration, window, capacity = (Q(row[key]) for key in ('RD', 'omega', 'C3'))
            assert duration >= 0 and window >= 0 and capacity >= 0
            clipped = min(duration, window)
            pressure = capacity * clipped
            contribution = probability * pressure
            assert Q(row['rhoD_omega']) == clipped, 'recorded duration clipping disagrees'
            assert Q(row['pD']) == pressure, 'recorded pressure disagrees'
            assert Q(int(row['tunnel_contribution_num']), int(row['tunnel_contribution_den'])) == contribution, 'recorded tunnel contribution disagrees'
            contributions.append(contribution)
    assert len(contributions) == 1, 'this fixture declares one tunnel successor'
    return contributions[0]


def test_actual_dec_inputs_determine_probabilities_and_routes():
    total, probabilities, routes = _one_node(_read('dec_one_node_ledger_example.csv'))
    assert total == 8
    assert probabilities == [Q(1, 8), Q(1, 8), Q(1, 2), Q(1, 4)]
    assert routes == {'returned': Q(1, 8), 'hinge': Q(1, 2), 'outgoing': Q(3, 8)}
    slide_total, slide_probabilities, slide_routes = _slide(_read('dec_hinge_slide_example.csv'))
    assert slide_total == 7
    assert slide_probabilities == [Q(3, 7), Q(3, 7), Q(1, 7)]
    assert slide_routes == {'returned': Q(6, 7), 'outgoing': Q(1, 7)}


def test_actual_window_csv_recomputes_clipping_pressure_and_tunnel_contribution():
    assert _window(_read('field_tunnelling_hinge_slide_window_clip.csv'),
                   _read('dec_hinge_slide_example.csv')) == Q(6, 7)


def test_weight_change_with_stale_probability_fails_arithmetic_without_hashes():
    rows = _read('dec_one_node_ledger_example.csv')
    _one_node(rows)
    rows[0]['weight'] = '2'
    assert Q(rows[0]['weight']) / sum(Q(row['weight']) for row in rows) == Q(2, 9)
    with pytest.raises(AssertionError, match='recorded probability disagrees'):
        _one_node(rows)


@pytest.mark.parametrize('column,value,reason', [
    ('admissible', '0', 'recorded probability disagrees'),
    ('admissible', '2', 'invalid admissibility'),
    ('weight', '-1', 'negative weight'),
    ('neighbor', '(1,1,0,0)', 'Hamming-1'),
    ('route', 'returned', 'route does not match role'),
])
def test_one_node_rejects_inconsistent_declared_rows(column, value, reason):
    rows = _read('dec_one_node_ledger_example.csv')
    rows[0][column] = value
    with pytest.raises(AssertionError, match=reason):
        _one_node(rows)


def test_zero_admissibility_gets_zero_mass_and_renormalizes():
    rows = _read('dec_one_node_ledger_example.csv')
    rows[0]['admissible'] = '0'
    for row, probability in zip(rows, ('0', '1/7', '4/7', '2/7')):
        row['probability_exact'] = probability
    total, probabilities, _ = _one_node(rows)
    assert total == 7 and probabilities[0] == 0


@pytest.mark.parametrize('column,value,reason', [
    ('Z_num', '8', 'normalizer'), ('P_num', '2', 'probability'),
    ('rhoD_omega', '5', 'clipping'), ('pD', '15', 'pressure'),
    ('tunnel_contribution_num', '15', 'contribution'),
    ('direct_adm', '1', 'blocked'),
])
def test_window_rejects_stale_recorded_outputs(column, value, reason):
    rows = _read('field_tunnelling_hinge_slide_window_clip.csv')
    rows[-1][column] = value
    with pytest.raises(AssertionError, match=reason):
        _window(rows, _read('dec_hinge_slide_example.csv'))


def test_slide_weights_are_independent_and_stale_probabilities_fail():
    rows = _read('dec_hinge_slide_example.csv')
    changed = deepcopy(rows)
    changed[0]['weight_num'] = '1'
    with pytest.raises(AssertionError, match='recorded slide probability disagrees'):
        _slide(changed)
    changed[0]['weight_num'] = '-1'
    with pytest.raises(AssertionError, match='negative weight'):
        _slide(changed)


def test_atomic_kernel_matches_independent_admission_and_normalization():
    # Each row here is explicitly an atomic (vertex, vertex, role, role) tuple;
    # the CSV's hinge label alone is never promoted to an atomic dwell.
    edges = ((0, 1, 0, 1), (0, 2, 0, -1), (0, 3, 0, 1), (0, 4, 1, -1), (0, 0, 0, 0))
    weights = [Q(1, 2), Q(3, 2), Q(7), Q(9), Q(11)]
    admitted = [True, True, False, False, False]
    status, _, probabilities = _normalize(weights, admitted)
    assert n.kernel(edges, dict(zip(edges, weights))) == {
        'status': status, 'probabilities': dict(zip(edges, probabilities))}
    for candidates, values, flags in (((), [], []), (edges[:2], [Q(0), Q(0)], [True, True]),
                                      (edges[2:], weights[2:], [False] * 3)):
        expected_status, _, _ = _normalize(values, flags)
        assert n.kernel(candidates, dict(zip(candidates, values))) == {
            'status': expected_status, 'probabilities': {}}
    with pytest.raises(n.AdmissionError, match='negative model weight'):
        n.kernel(edges[:2], {edges[0]: Q(-1), edges[1]: Q(2)})
    dwell = n.fibre_step(0, 0, 'additional_dwell')
    assert dwell['atomic_traversals'] == 0 and dwell['role'] == 0
    assert n.kernel(((0, 0, 0, 0),), {(0, 0, 0, 0): Q(1)})['status'] == 'EMPTY_ADMISSIBLE_SUPPORT'
