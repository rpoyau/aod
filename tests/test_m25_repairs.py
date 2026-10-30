"""Executable controls for the scoped M2.5 proof and intervention repairs.

Fibre events and atomic H1 transitions use their existing, separate APIs.  The
weighted claim is read from Main, then evaluated on exact finite witnesses;
changing its conclusion to structural emptiness must reject the zero-weight
witness.  Awareness tests exercise the existing operative() specialization.
"""
import importlib.util
import re
import sys
from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual/scripts'))
import aod_awareness as a

n = a.n
spec = importlib.util.spec_from_file_location(
    'm25_scientific_sources', ROOT / 'scripts/audit_scientific_sources.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


def _assert_displayed_weighted_claim(display, dwell, positive, weights):
    """Evaluate the displayed empty-set consequent, not a substitute theorem.

    The small grammar deliberately accepts both the repaired intersection and
    the erroneous structural-empty consequent so the hostile mutation below
    fails because of its mathematical value, rather than an unknown spelling.
    """
    normalized = re.sub(r'\s+|\\(?:quad|qquad)', '', display)
    match = re.search(r'\\Longleftrightarrow(A_0(?:\\capA_\+)?)=\\varnothing', normalized)
    assert match, 'The weighted claim must state its empty-support equivalence'
    domains = {'A_0': dwell, 'A_+': positive}
    factors = match[1].split(r'\cap')
    consequent = set(domains[factors[0]])
    for factor in factors[1:]:
        consequent &= domains[factor]
    assert (sum((weights[event] for event in dwell), Q(0)) == 0) == (not consequent), \
        'Weighted dwell sum and displayed support disagree'


def test_displayed_weighted_saturation_on_all_finite_nonnegative_cases():
    claim = source.equations(ROOT)['eq:hinge-saturation-weighted']
    # Distinct channels can share one fibre role.  This is a typed finite
    # specialization, not a combined probability kernel on H1 and fibre rows.
    roles = {'d0': n.fibre_step(0, 0, 'additional_dwell'),
             'd1': n.fibre_step(0, 0, 'additional_dwell'),
             'b-': n.fibre_step(0, -1, 'leave_hinge'),
             'b+': n.fibre_step(0, 1, 'leave_hinge')}
    for admitted_dwell in ((), ('d0',), ('d0', 'd1')):
        admitted = (*admitted_dwell, 'b-', 'b+')
        for values in product((Q(0), Q(1, 2), Q(2)), repeat=len(admitted)):
            weights = dict(zip(admitted, values))
            positive = {event for event in admitted if weights[event] > 0}
            _assert_displayed_weighted_claim(claim, set(admitted_dwell), positive, weights)
            if not admitted_dwell:
                assert {roles[event]['role'] for event in admitted} <= {-1, 1}
            if sum((weights[event] for event in admitted_dwell), Q(0)) == 0:
                assert {roles[event]['role'] for event in positive} <= {-1, 1}
    assert all(event['atomic_traversals'] == 0 for event in roles.values())


def test_zero_weight_counterexample_rejects_structural_empty_conclusion():
    dwell = n.fibre_step(0, 0, 'additional_dwell')
    assert dwell['role'] == 0 and dwell['atomic_traversals'] == 0
    weights = {'d0': Q(0), 'b-': Q(1), 'b+': Q(2)}
    claim = source.equations(ROOT)['eq:hinge-saturation-weighted']
    _assert_displayed_weighted_claim(claim, {'d0'}, {'b-', 'b+'}, weights)
    # This reproduces the incorrect inference being repaired.  The parser
    # accepts it; the exact admitted zero-weight witness refutes it.
    mutant = claim.replace(r'A_0\cap A_+', 'A_0')
    assert mutant != claim
    with pytest.raises(AssertionError, match='Weighted dwell sum and displayed support disagree'):
        _assert_displayed_weighted_claim(mutant, {'d0'}, {'b-', 'b+'}, weights)


def test_atomic_empty_and_zero_support_remain_distinct_from_fibre_dwell():
    edges = ((0, 1, 0, -1), (0, 2, 0, 1))
    assert n.kernel((), {}) == {'status': 'EMPTY_ADMISSIBLE_SUPPORT', 'probabilities': {}}
    zero = n.kernel(edges, dict.fromkeys(edges, Q(0)))
    assert zero == {'status': 'EMPTY_POSITIVE_WEIGHT_SUPPORT', 'probabilities': {}}
    weighted = n.kernel(edges, dict(zip(edges, (Q(1), Q(2)))))
    assert weighted['probabilities'] == dict(zip(edges, (Q(1, 3), Q(2, 3))))
    one_role = n.kernel(edges, dict(zip(edges, (Q(0), Q(2)))))
    assert one_role['probabilities'] == dict(zip(edges, (Q(0), Q(1))))
    # An admitted fibre dwell has no H1 base step and is not normalized here.
    assert n.fibre_step(0, 0, 'additional_dwell')['atomic_traversals'] == 0
    assert n.kernel(((0, 0, 0, 0),), {(0, 0, 0, 0): Q(1)})['status'] == 'EMPTY_ADMISSIBLE_SUPPORT'
    with pytest.raises(n.AdmissionError, match='negative model weight'):
        n.kernel(edges, dict(zip(edges, (Q(-1), Q(2)))))
    with pytest.raises(n.AdmissionError, match='dwell requires existing hinge'):
        n.fibre_step(1, 0, 'additional_dwell')
    with pytest.raises(n.AdmissionError):
        n.fibre_step(1, -1, 'leave_hinge')


def test_strict_positive_hypothesis_and_negative_weight_counterexample():
    # Strict positivity makes zero dwell mass equivalent to structural absence.
    for dwell_weights in ((), (Q(1),), (Q(1, 2), Q(2))):
        assert (sum(dwell_weights, Q(0)) == 0) == (not dwell_weights)
    # Nonnegativity is necessary for the weaker positive-support equivalence.
    weights = {'d0': Q(1), 'd1': Q(-1)}
    claim = source.equations(ROOT)['eq:hinge-saturation-weighted']
    with pytest.raises(AssertionError, match='Weighted dwell sum and displayed support disagree'):
        _assert_displayed_weighted_claim(claim, set(weights), {'d0'}, weights)


def test_operative_removes_exact_source_subset_and_restores_provenance(monkeypatch):
    state, world, model, inputs = a.context(peers=2, values=(1, -1))
    transition = a.transition
    observed = []

    def observe(candidate, candidate_world, candidate_model, candidate_input):
        observed.append((candidate, candidate_world, candidate_model, candidate_input))
        return transition(candidate, candidate_world, candidate_model, candidate_input)

    monkeypatch.setattr(a, 'transition', observe)
    graph = a.operative(state, world, model, inputs[0])
    assert observed[0] == (state, world, model, inputs[0])
    assert graph['sources'] == tuple(record.prior.source for record in state.retained)
    assert len(observed) == 1 + len(state.retained)
    actual = transition(state, world, model, inputs[0])
    assert actual[1]['current'] == 0
    for record, (removed, bound_world, bound_model, bound_input) in zip(state.retained, observed[1:]):
        subset = tuple(r for r in state.retained if r.prior.source == record.prior.source)
        assert subset == (record,)
        assert record.prior.target == world.target
        assert removed.retained == tuple(r for r in state.retained if r not in subset)
        assert removed.present is state.present and removed.closure_memory is state.closure_memory
        assert (bound_world, bound_model, bound_input) == (world, model, inputs[0])
        assert transition(removed, world, model, inputs[0])[1]['current'] == -record.value
        restored = replace(removed, retained=state.retained)
        assert a.digest(restored) == a.digest(state)
        assert transition(restored, world, model, inputs[0]) == actual
    assert actual[1]['at'] > state.present.committed


def test_duplicate_source_cancellation_is_outside_single_record_specialization():
    state, world, model, inputs = a.context(values=(1,))
    opposite = a.retain(replace(state.retained[0].prior, cross=(Q(-1),)))
    world = replace(world, prior_commitments=(*world.prior_commitments, a.digest(opposite.prior)))
    assert a.validate_retention(opposite, world, state.present.committed)
    duplicated = replace(state, retained=(*state.retained, opposite))
    assert sum((record.value for record in duplicated.retained), Q(0)) == 0
    with pytest.raises(a.AdmissionError, match='duplicate retained source channel'):
        a.operative(duplicated, world, model, inputs[0])


def test_unavailable_next_cut_can_be_operative_over_longer_horizon():
    state, world, model, inputs = a.context()
    absent_next = replace(inputs[0], available=())
    assert a.operative(state, world, model, absent_next)['sources'] == ()
    horizon = (absent_next, inputs[1])
    removed = replace(state, retained=())
    pair = a.matched(state, removed, world, world, model, model, horizon, horizon)
    assert pair['effect']
    left, right = pair['left']['events'], pair['right']['events']
    assert a.outcome(left[:1]) == a.outcome(right[:1])
    assert a.outcome(left[1:]) != a.outcome(right[1:])
    assert left[1]['at'] == state.present.committed + 2
    assert pair['left']['final'].retained == state.retained


@pytest.mark.parametrize('mismatch', ('law', 'input'))
def test_source_intervention_rejects_unmatched_law_or_future_inputs(mismatch):
    state, world, model, inputs = a.context()
    removed = replace(state, retained=())
    other_model = replace(model, gain=Q(2)) if mismatch == 'law' else model
    other_inputs = (replace(inputs[0], attention=Q(1)), *inputs[1:]) if mismatch == 'input' else inputs
    with pytest.raises(a.AdmissionError, match='law, world or future exogenous inputs differ'):
        a.matched(state, removed, world, world, model, other_model, inputs, other_inputs)
