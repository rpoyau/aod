"""Independent symbolic and runtime checks of the declared rational response.

The algebra is conditional on matched inputs/law and p > 0. Finite runtime
checks exercise that model; they do not derive its choice or certify ontology.
"""
from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import sys

import pytest
import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'manual/scripts'))
import aod_awareness as a

J, A, QUERY, G, SUM, ALTERNATE = sp.symbols('J A q g S S_prime', real=True)
P = sp.symbols('p', positive=True)
RESPONSE = J + (A + QUERY + G * SUM) / P


def _oracle(state, model, inp):
    """Evaluate the declared equation, independently of transition/update."""
    total = sum((record.value for record in state.retained
                 if record.prior.source in inp.available), Q(0))
    result = RESPONSE.subs({J: state.present.current, A: inp.attention,
                            QUERY: inp.query, G: model.gain, SUM: total,
                            P: state.present.pressure})
    assert result.is_Rational
    return Q(int(sp.numer(result)), int(sp.denom(result)))


def _assert_step(state, model, inp, result):
    after, event = result
    expected = _oracle(state, model, inp)
    assert event['current'] == after.present.current == expected, 'response disagrees with symbolic oracle'
    vertex, role = state.present.present
    slot = 0 if expected > model.selector_threshold else 1
    edge = (vertex, vertex ^ (1 << slot))
    next_role = 0 if role else (1 if slot == 0 else -1)
    assert event['edge'] == edge and after.present.present == (edge[1], next_role), 'selector disagrees at its declared boundary'
    assert event['at'] == event['native_update_at'] == after.present.committed == state.present.committed + 1, 'effect must be strictly later'
    assert event['new_phase'] == 0 and after.present.phases == state.present.phases, 'response cannot certify a new phase'
    assert after.present.motif_certificates == state.present.motif_certificates
    assert after.closure_memory == state.closure_memory and after.retained == state.retained
    assert event['retained_terms'] == tuple((record.prior.source, record.value)
                                           for record in state.retained
                                           if record.prior.source in inp.available)
    return expected


def test_symbolic_matched_difference_and_single_available_source_removal():
    alternative = RESPONSE.subs(SUM, ALTERNATE)
    difference = sp.factor(RESPONSE - alternative)
    assert sp.simplify(difference - G * (SUM - ALTERNATE) / P) == 0
    retained, other, available = sp.symbols('r_i S_other d_i', real=True)
    single = sp.simplify(difference.subs({SUM: other + available * retained, ALTERNATE: other}))
    assert sp.simplify(single.subs(available, 1) - G * retained / P) == 0
    assert single.subs(available, 0) == 0
    assert single.subs(G, 0) == 0 and single.subs(retained, 0) == 0
    # Matched J, attention and query cancel; changing one is a different model
    # comparison, rather than evidence of a retained-coordinate intervention.
    assert not ({J, A, QUERY} & difference.free_symbols)


@pytest.fixture(scope='module')
def contexts():
    return {(pressure, value): a.context(pressure=pressure, values=(value,))
            for pressure, value in product((Q(1, 2), Q(2), Q(7, 3)),
                                           (Q(-2, 3), Q(0), Q(5, 4)))}


@pytest.mark.parametrize('pressure,value,gain,available', list(product(
    (Q(1, 2), Q(2), Q(7, 3)), (Q(-2, 3), Q(0), Q(5, 4)),
    (Q(-3, 2), Q(0), Q(5, 3)), (False, True))))
def test_runtime_matches_symbolic_response_and_removal_at_selector_boundaries(contexts, pressure, value, gain, available):
    state, world, model, inputs = contexts[pressure, value]
    state = replace(state, present=replace(state.present, current=Q(5, 7)))
    inp = replace(inputs[0], attention=Q(-2, 3), query=Q(1, 5),
                  query_observed_at=state.present.committed,
                  available=inputs[0].available if available else ())
    model = replace(model, gain=gain)
    expected = _oracle(state, model, inp)
    removed = replace(state, retained=())
    for offset in (Q(-1, 7), Q(0), Q(1, 7)):
        law = replace(model, selector_threshold=expected + offset)
        actual = a.transition(state, world, law, inp)
        without = a.transition(removed, world, law, inp)
        actual_current = _assert_step(state, law, inp, actual)
        absent_current = _assert_step(removed, law, inp, without)
        assert actual_current - absent_current == (gain * value / pressure if available else 0)
        assert actual[1]['edge'][1] == (state.present.present[0] ^ (1 if offset < 0 else 2))
        assert (a.outcome((actual[1],)) != a.outcome((without[1],))) == bool(gain * value if available else 0)


def test_current_difference_is_an_effect_even_when_selected_edge_is_unchanged():
    state, world, model, inputs = a.context(pressure=Q(3, 2), values=(Q(1, 3),))
    model = replace(model, gain=Q(-2), selector_threshold=Q(10))
    removed = replace(state, retained=())
    pair = a.matched(state, removed, world, world, model, model, inputs[:1], inputs[:1])
    left, right = pair['left']['events'][0], pair['right']['events'][0]
    assert left['edge'] == right['edge']
    assert left['current'] - right['current'] == Q(-4, 9)
    assert pair['effect']


def test_cancellation_preserves_individual_source_effect_and_exact_restoration():
    state, world, model, inputs = a.context(pressure=Q(5, 2), peers=2, values=(Q(3, 7), Q(-3, 7)))
    model = replace(model, gain=Q(-4, 3))
    actual = a.transition(state, world, model, inputs[0])
    assert _assert_step(state, model, inputs[0], actual) == 0
    assert set(a.operative(state, world, model, inputs[0])['sources']) == {r.prior.source for r in state.retained}
    for record in state.retained:
        removed = replace(state, retained=tuple(r for r in state.retained if r.prior.source != record.prior.source))
        alternate = a.transition(removed, world, model, inputs[0])
        _assert_step(removed, model, inputs[0], alternate)
        assert actual[1]['current'] - alternate[1]['current'] == model.gain * record.value / state.present.pressure
        restored = replace(removed, retained=state.retained)
        assert a.digest(restored) == a.digest(state)
        assert a.transition(restored, world, model, inputs[0]) == actual
    empty = replace(state, retained=())
    assert not a.matched(state, empty, world, world, model, model, inputs[:1], inputs[:1])['effect']


def test_multi_step_response_keeps_provenance_and_waits_for_source_availability():
    state, world, model, inputs = a.context(pressure=Q(4, 3), values=(Q(-5, 7),))
    model = replace(model, gain=Q(2, 5))
    inputs = tuple(replace(inp, attention=Q(1, 3), available=() if index == 0 else inp.available)
                   for index, inp in enumerate(inputs))
    removed = replace(state, retained=())
    pair = a.matched(state, removed, world, world, model, model, inputs, inputs)
    assert a.outcome(pair['left']['events'][:1]) == a.outcome(pair['right']['events'][:1])
    assert a.outcome(pair['left']['events'][1:]) != a.outcome(pair['right']['events'][1:])
    for initial, lane in ((state, pair['left']), (removed, pair['right'])):
        before = initial
        for inp, after, event in zip(inputs, lane['states'], lane['events']):
            _assert_step(before, model, inp, (after, event))
            assert a.validate_state(after, world)
            before = after
        assert before.present.phases == initial.present.phases
    restored = replace(removed, retained=state.retained)
    assert a.execution_bytes(a.execute(restored, world, model, inputs)) == a.execution_bytes(pair['left'])


@pytest.mark.parametrize('pressure', (Q(0), Q(-1, 3)))
def test_response_requires_strictly_positive_pressure(pressure):
    with pytest.raises(a.AdmissionError, match='pressure'):
        a.context(pressure=pressure)


@pytest.mark.parametrize('mutation,reason', [
    ('law', 'law, world or future exogenous inputs differ'),
    ('input', 'law, world or future exogenous inputs differ'),
    ('present', 'non-retained coordinates differ'),
    ('provenance', 'retained residual value or lineage digest mismatch'),
    ('future_query', 'query observation requires'),
])
def test_intervention_rejects_broken_model_and_provenance_premises(mutation, reason):
    state, world, model, inputs = a.context()
    removed = replace(state, retained=())
    other_model, other_inputs = model, inputs[:1]
    if mutation == 'law':
        other_model = replace(model, gain=Q(2))
    elif mutation == 'input':
        other_inputs = (replace(inputs[0], attention=Q(1)),)
    elif mutation == 'present':
        removed = replace(removed, present=replace(removed.present, current=Q(1)))
    elif mutation == 'provenance':
        state = replace(state, retained=(replace(state.retained[0], value=Q(2)),))
    else:
        inputs = (replace(inputs[0], query=Q(1), query_observed_at=state.present.committed + 1),)
        other_inputs = inputs
    with pytest.raises(a.AdmissionError, match=reason):
        a.matched(state, removed, world, world, model, other_model, inputs[:1], other_inputs)


@pytest.mark.parametrize('wrong_attention', (lambda attention, pressure: attention,
                                             lambda attention, pressure: -attention / pressure))
def test_runtime_attention_law_mutations_fail_independent_oracle(monkeypatch, wrong_attention):
    state, world, model, inputs = a.context(pressure=Q(3, 2), values=(Q(2, 7),))
    inp = replace(inputs[0], attention=Q(4, 5))
    _assert_step(state, model, inp, a.transition(state, world, model, inp))

    def wrong_update(present, attention, committed):
        return replace(present, committed=present.committed + 1,
                       current=present.current + wrong_attention(attention, present.pressure))

    monkeypatch.setattr(a.n, 'update', wrong_update)
    with pytest.raises(AssertionError, match='response disagrees with symbolic oracle'):
        _assert_step(state, model, inp, a.transition(state, world, model, inp))
