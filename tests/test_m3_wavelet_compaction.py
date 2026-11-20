"""Phase 1 wavelet compaction, conservation, exact arithmetic and conditional SI tests.

Executable directly under both `python3` and `python3 -O` (no bare `assert`s in
standalone check helpers) as well as via `pytest`. Uses exact `int` and
`fractions.Fraction` arithmetic only (no floating-point comparisons).
"""
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import shutil

try:
    import pytest
except ImportError:  # pragma: no cover - allows standalone stdlib execution
    pytest = None


ROOT = Path(__file__).resolve().parents[1]
CS133_DELTA_NU_HZ = 9_192_631_770


def _load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def _reject(callable_obj, exc_type, match=None):
    try:
        callable_obj()
    except exc_type as exc:
        if match is not None and not re.search(match, str(exc)):
            raise AssertionError(f'expected error matching {match!r}, got {str(exc)!r}') from exc
        return
    raise AssertionError(f'expected {exc_type.__name__} to be raised')


def _require_exact_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f'{name} must be an exact int, got {type(value).__name__}')
    return value


def _require_exact_rational(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f'{name} must be an exact int or Fraction, got {type(value).__name__}')
    return Fraction(value)


# --- PO-1: Duon enumeration and same-current Duad seating ---

def seat_duon_same_current(duon, new_duon_id=None, keep_hinge=True):
    if duon['sigma_seat'] != 'open_seat':
        raise ValueError('only an open-seat Duon can transition to seated_duad')
    if not keep_hinge or not duon.get('hinge_0H'):
        raise ValueError('mandatory structural 0_H hinge missing on seating')
    seated_id = duon['duon_id'] if new_duon_id is None else new_duon_id
    if seated_id != duon['duon_id']:
        raise ValueError('Duad seating must preserve identical duon_id')
    return {
        'duon_id': seated_id,
        'lineage_id': duon['lineage_id'],
        'prefix_digest': duon['prefix_digest'],
        'hinge_0H': True,
        'sigma_seat': 'seated_duad',
    }


def check_po1_duon_duad_same_current():
    dions = ('D_alpha', 'D_Omega')
    hinges = (-1, 0, 1)
    variants = [(d1, mu, d2) for d1 in dions for mu in hinges for d2 in dions]
    _check(len(variants) == 12 and len(set(variants)) == 12, 'expected 12 distinct resolved Duon variants')
    duon = {
        'duon_id': 'duon:001',
        'lineage_id': 'lin:A',
        'prefix_digest': 'sha256:prefix-001',
        'hinge_0H': True,
        'sigma_seat': 'open_seat',
    }
    duad = seat_duon_same_current(duon)
    _check(duad['duon_id'] == duon['duon_id'], 'Duad changed duon_id')
    _check(duad['lineage_id'] == duon['lineage_id'], 'Duad changed lineage_id')
    _check(duad['prefix_digest'] == duon['prefix_digest'], 'Duad changed prefix_digest')
    _check(duad['sigma_seat'] == 'seated_duad', 'Duad state must be seated_duad')
    _reject(lambda: seat_duon_same_current(duon, new_duon_id='duon:fresh'), ValueError, 'identical duon_id')
    _reject(lambda: seat_duon_same_current(duon, keep_hinge=False), ValueError, '0_H hinge')
    return {'resolved_variants': len(variants), 'same_current_seating': True}


# --- PO-2 & PO-3 (F02, F04): Wavelet seating/role separation & eligible window returns ---

VALID_WAVELET_SEAT_STATES = frozenset({'open_duon', 'seated_duad'})
VALID_WAVELET_ROLES = frozenset({'local_segment', 'coupled_segment', 'shed_continuation'})


def make_return_witness(return_id, occurrence_j, completion_cut, lineage_id, scope_id,
                        compatible=True, scope_mapped=True):
    if not return_id or not lineage_id or not scope_id:
        raise ValueError('return witness requires return_id, lineage_id, and scope_id')
    j = _require_exact_int(occurrence_j, 'occurrence_j')
    cut = _require_exact_int(completion_cut, 'completion_cut')
    if j < 0:
        raise ValueError('occurrence index j must be non-negative')
    return {
        'return_id': return_id,
        'occurrence_j': j,
        'completion_cut': cut,
        'lineage_id': lineage_id,
        'scope_id': scope_id,
        'compatible': bool(compatible),
        'scope_mapped': bool(scope_mapped),
    }


def make_wavelet(wavelet_id, parent_id, ancestry, window, sigma_seat, sigma_role,
                 records, return_witnesses=(), signed_current=0, is_admitted_wave=False,
                 scope_id='B:main', witnesses_complete=True):
    if not parent_id or not ancestry:
        raise ValueError('wavelet must preserve parent_id and ancestry')
    if sigma_seat not in VALID_WAVELET_SEAT_STATES:
        raise ValueError('invalid independent seating state')
    if sigma_role not in VALID_WAVELET_ROLES:
        raise ValueError('invalid wavelet coupling/route role')
    u, v = window
    _require_exact_int(u, 'window start')
    _require_exact_int(v, 'window end')
    if not (u < v):
        raise ValueError('window must satisfy u < v')
    if not records:
        raise ValueError('wavelet must retain committed construction records')
    w = {
        'id_w': wavelet_id,
        'parent_id': parent_id,
        'ancestry': tuple(ancestry),
        'scope_id': scope_id,
        'window': (u, v),
        'sigma_seat': sigma_seat,
        'sigma_role': sigma_role,
        'records': tuple(records),
        'return_witnesses': tuple(return_witnesses),
        'witnesses_complete': bool(witnesses_complete),
        'signed_current': _require_exact_int(signed_current, 'signed_current'),
        'is_admitted_wave': bool(is_admitted_wave),
    }
    eligible = eligible_return_ids(w, target_lineage=parent_id, target_scope=scope_id)
    if is_admitted_wave and (sigma_role == 'shed_continuation' or sigma_seat == 'open_duon' or len(eligible) < 1):
        raise ValueError('open/shed wavelet or zero-eligible-return fragment cannot be promoted to an admitted wave')
    return w


def eligible_return_ids(wavelet, target_lineage=None, target_scope=None):
    if not wavelet['witnesses_complete']:
        raise ValueError('complete eligible return records required for window count')
    lineage = wavelet['parent_id'] if target_lineage is None else target_lineage
    scope = wavelet['scope_id'] if target_scope is None else target_scope
    if wavelet['parent_id'] != lineage:
        raise ValueError('incompatible parent lineage')
    u, v = wavelet['window']
    eligible = set()
    for item in wavelet['return_witnesses']:
        if item['lineage_id'] != lineage:
            raise ValueError('return witness lineage mismatch')
        if item['scope_id'] != scope and not item['scope_mapped']:
            raise ValueError('return witness lacks identity-preserving scope map')
        if item['compatible'] and item['occurrence_j'] >= 1 and (u < item['completion_cut'] <= v):
            eligible.add(item['return_id'])
    return eligible


def in_window_closure_phase_presence(wavelet, target_lineage=None, target_scope=None):
    lineage = wavelet['parent_id'] if target_lineage is None else target_lineage
    scope = wavelet['scope_id'] if target_scope is None else target_scope
    u, v = wavelet['window']
    origins = {
        item['return_id']
        for item in wavelet['return_witnesses']
        if (item['lineage_id'] == lineage and (item['scope_id'] == scope or item['scope_mapped'])
            and item['compatible'] and item['occurrence_j'] == 0 and u < item['completion_cut'] <= v)
    }
    reclosures = eligible_return_ids(wavelet, target_lineage=lineage, target_scope=scope)
    return {
        'origin_indicator': 1 if origins else 0,
        'reclosure_bips': len(reclosures),
        'closure_phase_cycles': len(reclosures) + (1 if origins else 0),
        'retained_support_witnesses': len(wavelet['return_witnesses']),
    }


def deduplicated_return_count(wavelets, target_lineage, target_scope='B:main'):
    seen = set()
    for w in wavelets:
        seen.update(eligible_return_ids(w, target_lineage=target_lineage, target_scope=target_scope))
    return len(seen)


def combine_signed_wavelets(w_pos, w_neg):
    total_current = w_pos['signed_current'] + w_neg['signed_current']
    retained_histories = (
        (w_pos['ancestry'], w_pos['records']),
        (w_neg['ancestry'], w_neg['records']),
    )
    return {'net_current': total_current, 'retained_histories': retained_histories}


def check_po2_po3_wavelet_dedup_and_cancellation():
    parent_state = {'id': 'W_B_1', 'active_beyond_v': True}
    # F04: Independent seating & coupling/route coordinates (seated + coupled, shed retaining seating)
    c0_at_0 = make_return_witness('C0', 0, 0, 'W_B_1', 'B:main')
    c1_at_2 = make_return_witness('C1', 1, 2, 'W_B_1', 'B:main')
    c2_at_6 = make_return_witness('C2', 2, 6, 'W_B_1', 'B:main')
    c3_at_8 = make_return_witness('C3', 3, 8, 'W_B_1', 'B:main')
    c4_at_10 = make_return_witness('C4', 4, 10, 'W_B_1', 'B:main')

    # Out-of-window prefix witnesses (C0@0, C1@2) on window (3, 5] must stay retained as support while giving q = 0
    w_prefix = make_wavelet(
        'w_prefix', 'W_B_1', ('lin:1', 'seg:prefix'), (3, 5),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:C0@0', 'rec:C1@2'),
        return_witnesses=(c0_at_0, c1_at_2),
        signed_current=0, is_admitted_wave=False,
    )
    _check(w_prefix['sigma_seat'] == 'seated_duad' and w_prefix['sigma_role'] == 'coupled_segment',
           'coupled_segment must preserve independent seated_duad state (F04)')
    _check(len(w_prefix['return_witnesses']) == 2, 'full supporting witnesses must remain retained')
    _check(deduplicated_return_count((w_prefix,), 'W_B_1') == 0,
           'out-of-window supporting return must contribute 0 local reclosures (F02)')

    # Initial origin C0 at cut 0 inside (-1, 2] gives 1 closure phase cycle, 0 reclosure bips; cut=2 included (right endpoint)
    w_origin_only = make_wavelet(
        'w_origin', 'W_B_1', ('lin:1', 'seg:origin'), (-1, 1),
        sigma_seat='seated_duad', sigma_role='local_segment',
        records=('rec:C0@0',),
        return_witnesses=(c0_at_0,),
        signed_current=0, is_admitted_wave=False,
    )
    origin_info = in_window_closure_phase_presence(w_origin_only)
    _check(origin_info['origin_indicator'] == 1 and origin_info['reclosure_bips'] == 0
           and origin_info['closure_phase_cycles'] == 1,
           'initial origin in window contributes closure phase without reclosure bip (F02)')

    # Half-open window endpoints: (2, 6] excludes C1@2 (left endpoint) and includes C2@6 (right endpoint)
    w_half_open = make_wavelet(
        'w_half_open', 'W_B_1', ('lin:1', 'seg:half_open'), (2, 6),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:C1@2', 'rec:C2@6'),
        return_witnesses=(c1_at_2, c2_at_6),
        signed_current=1, is_admitted_wave=True,
    )
    _check(eligible_return_ids(w_half_open) == {'C2'},
           'half-open (2, 6] must exclude left endpoint cut 2 and include right endpoint cut 6')

    # Overlapping windows: (0, 8] has {C1@2, C2@6, C3@8}? Let's test (1, 8] -> {C1@2, C2@6, C3@8} and (5, 10] -> {C2@6, C3@8, C4@10}
    w1 = make_wavelet(
        'w1', parent_state['id'], ('lin:1', 'seg:1'), (0, 8),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:C0@0', 'rec:C1@2', 'rec:C2@6'),
        return_witnesses=(c0_at_0, c1_at_2, c2_at_6),
        signed_current=1, is_admitted_wave=True,
    )
    w2 = make_wavelet(
        'w2', parent_state['id'], ('lin:1', 'seg:2'), (4, 10),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:C1@2', 'rec:C2@6', 'rec:C3@8'),
        return_witnesses=(c1_at_2, c2_at_6, c3_at_8),
        signed_current=-1, is_admitted_wave=True,
    )
    w_shed = make_wavelet(
        'w_shed', parent_state['id'], ('lin:1', 'shed:1'), (10, 14),
        sigma_seat='seated_duad', sigma_role='shed_continuation',
        records=('rec:C3@8',), return_witnesses=(c3_at_8,), signed_current=0,
        is_admitted_wave=False,
    )
    _check(parent_state['active_beyond_v'] is True, 'window restriction must not terminate parent wave')
    _check(w_shed['sigma_seat'] == 'seated_duad' and w_shed['sigma_role'] == 'shed_continuation',
           'shed continuation must retain its seating state independently (F04)')
    _check(len(eligible_return_ids(w_shed)) == 0 and len(w_shed['return_witnesses']) == 1,
           'zero-local-return shed wavelet retains parent admission witness as support')

    _reject(
        lambda: make_wavelet(
            'bad_promo', 'W_B_1', ('lin:1',), (0, 2), 'open_duon', 'local_segment', ('r0',),
            return_witnesses=(c1_at_2,), is_admitted_wave=True,
        ),
        ValueError, 'cannot be promoted',
    )
    _reject(
        lambda: make_wavelet(
            'bad_shed_promo', 'W_B_1', ('lin:1',), (4, 8), 'seated_duad', 'shed_continuation', ('r0',),
            return_witnesses=(c2_at_6,), is_admitted_wave=True,
        ),
        ValueError, 'cannot be promoted',
    )
    _reject(
        lambda: make_wavelet(
            'bad_detached', '', (), (0, 2), 'open_duon', 'local_segment', ('r0',),
        ),
        ValueError, 'parent_id',
    )

    single_window_sum = len(eligible_return_ids(w1)) + len(eligible_return_ids(w2))  # {C1,C2} + {C2,C3} -> 2 + 2 = 4
    dedup = deduplicated_return_count((w1, w2), 'W_B_1')  # {C1, C2, C3} -> 3
    _check(dedup == 3 and single_window_sum == 4 and dedup < single_window_sum,
           'overlapping windows must deduplicate shared eligible in-window return IDs')

    w_other = make_wavelet(
        'w_other', 'W_B_2', ('lin:2',), (4, 10),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:D1@9',),
        return_witnesses=(make_return_witness('D1', 1, 9, 'W_B_2', 'B:main'),),
    )
    _reject(lambda: deduplicated_return_count((w1, w_other), 'W_B_1'), ValueError, 'lineage')

    _reject(
        lambda: make_wavelet(
            'w_bad_scope', 'W_B_1', ('lin:1',), (4, 10),
            sigma_seat='seated_duad', sigma_role='coupled_segment',
            records=('rec:bad_scope',),
            return_witnesses=(make_return_witness('C9', 1, 9, 'W_B_1', 'B:other', scope_mapped=False),),
        ),
        ValueError, 'scope map',
    )
    w_other_scope = make_wavelet(
        'w_other_scope', 'W_B_1', ('lin:1',), (4, 10),
        sigma_seat='seated_duad', sigma_role='coupled_segment',
        records=('rec:other_scope',),
        return_witnesses=(make_return_witness('C9', 1, 9, 'W_B_1', 'B:other', scope_mapped=False),),
        scope_id='B:other',
    )
    _reject(lambda: eligible_return_ids(w_other_scope, target_scope='B:main'), ValueError, 'scope map')

    combined = combine_signed_wavelets(w1, w2)
    _check(combined['net_current'] == 0, 'opposing signed currents should cancel to zero')
    _check(len(combined['retained_histories']) == 2, 'cancellation must retain both histories')
    _check(combined['retained_histories'][0] != combined['retained_histories'][1], 'retained histories must stay distinct')
    return {
        'deduplicated_returns': dedup,
        'single_window_sum': single_window_sum,
        'out_of_window_prefix_count': deduplicated_return_count((w_prefix,), 'W_B_1'),
        'retained_histories': 2,
        'independent_seating_and_role': True,
    }


# --- PO-4 (F01): Shed continuation witness & origin/reclosure-qualified recipient event lattice ---

ALLOWED_RECIPIENT_TRANSITIONS = {
    'emitted': frozenset({'delivered'}),
    'delivered': frozenset({'accepted', 'unaccepted_pass'}),
    'accepted': frozenset({'seated', 'pending_unseated'}),
    'seated': frozenset({'closed_origin', 'reclosed'}),
    'unaccepted_pass': frozenset(),
    'pending_unseated': frozenset(),
    'closed_origin': frozenset(),
    'reclosed': frozenset(),
}


def evaluate_recipient_observation(witness, recipient_context, stages, closure_witness=None):
    """Evaluate passive recipient-event observation at a cut under F01 premises."""
    required_keys = ('parent_id', 'emit_boundary', 'emit_cut', 'route', 'X_route', 'post_shed_parent_state')
    if any(witness.get(k) in (None, '') for k in required_keys):
        raise ValueError('shed continuation witness missing required provenance field')
    if witness['route'] not in {'endo', 'exo', 'redir', 'open'}:
        raise ValueError('invalid shed route tag')
    if not stages or stages[0] != 'emitted':
        raise ValueError('recipient chain must begin at emitted')
    for cur, nxt in zip(stages, stages[1:]):
        if nxt not in ALLOWED_RECIPIENT_TRANSITIONS.get(cur, frozenset()):
            raise ValueError(f'illegal stage transition {cur} -> {nxt}')

    terminal = stages[-1]
    rec_lineage = recipient_context['recipient_lineage']
    rec_scope = recipient_context['recipient_scope']
    u, v = recipient_context['window']
    _require_exact_int(u, 'recipient window start')
    _require_exact_int(v, 'recipient window end')
    origin_id = recipient_context.get('origin_return_id')
    seen_ids = frozenset(recipient_context.get('seen_return_ids', ()))

    if terminal not in {'closed_origin', 'reclosed'}:
        return {
            'stage': terminal,
            'closure_phase_delta': 0,
            'reclosure_bip_delta': 0,
            'blocks_later_seating': False,
        }

    if closure_witness is None or not closure_witness.get('has_certificate'):
        raise ValueError(f'{terminal} requires a full closure certificate (eq:closure-certificate)')
    if closure_witness.get('lineage_id') != rec_lineage:
        raise ValueError('recipient closure certificate lineage mismatch: no admitted recipient claim')
    if closure_witness.get('scope_id') != rec_scope and not closure_witness.get('scope_mapped', False):
        raise ValueError('recipient closure certificate scope mismatch: no admitted recipient claim')
    cut = _require_exact_int(closure_witness['completion_cut'], 'completion_cut')
    ret_id = closure_witness.get('return_id')
    j = _require_exact_int(closure_witness['occurrence_j'], 'occurrence_j')
    if not ret_id:
        raise ValueError('closure witness requires immutable return_id')

    if terminal == 'closed_origin':
        if origin_id is not None or j != 0:
            raise ValueError('closed_origin applies only to recipient lineage initial closure (j=0, no prior origin)')
        in_win = int(u < cut <= v)
        return {
            'stage': 'closed_origin',
            'closure_phase_delta': in_win,
            'reclosure_bip_delta': 0,  # N_i^C = 1 -> max(1 - 1, 0) = 0
            'origin_return_id': ret_id,
        }

    # terminal == 'reclosed': requires pre-existing compatible origin, j >= 1, in-window, distinct unseen return_id
    if not origin_id:
        raise ValueError('initial closure establishes origin with 0 bips; reclosure requires existing recipient origin')
    if j < 1:
        raise ValueError('reclosure requires occurrence index j >= 1 beyond initial origin')
    if ret_id in seen_ids or ret_id == origin_id:
        # Replay or re-observation of an already counted immutable return identity contributes 0 new beats
        return {
            'stage': 'reclosed_replay',
            'closure_phase_delta': 0,
            'reclosure_bip_delta': 0,
        }
    if not (u < cut <= v):
        return {
            'stage': 'reclosed_out_of_window',
            'closure_phase_delta': 0,
            'reclosure_bip_delta': 0,
        }
    return {
        'stage': 'reclosed',
        'closure_phase_delta': 1,
        'reclosure_bip_delta': 1,
        'return_id': ret_id,
    }


def check_po4_recipient_event_lattice():
    witness = {
        'parent_id': 'W_B_1',
        'emit_boundary': 'dT_R1',
        'emit_cut': 12,
        'route': 'exo',
        'X_route': Fraction(1, 2),
        'post_shed_parent_state': 'S_W_post_12',
    }
    ctx_fresh = {
        'recipient_lineage': 'R_1',
        'recipient_scope': 'B_rec:1',
        'window': (10, 20),
        'origin_return_id': None,
        'seen_return_ids': (),
    }
    r_unacc = evaluate_recipient_observation(witness, ctx_fresh, ('emitted', 'delivered', 'unaccepted_pass'))
    _check(r_unacc['reclosure_bip_delta'] == 0, 'unaccepted_pass must contribute 0 reclosures')
    r_pend = evaluate_recipient_observation(witness, ctx_fresh, ('emitted', 'delivered', 'accepted', 'pending_unseated'))
    _check(r_pend['reclosure_bip_delta'] == 0 and r_pend['blocks_later_seating'] is False,
           'pending_unseated contributes 0 bips and never blocks later witnessed seating')
    r_seated = evaluate_recipient_observation(witness, ctx_fresh, ('emitted', 'delivered', 'accepted', 'seated'))
    _check(r_seated['reclosure_bip_delta'] == 0, 'seated without completion certificate must contribute 0 bips')

    # F01 case 1: First certified closure -> closure phase 1, ZERO reclosure beats
    c0_wit = {
        'has_certificate': True, 'lineage_id': 'R_1', 'scope_id': 'B_rec:1',
        'return_id': 'ret:R0', 'occurrence_j': 0, 'completion_cut': 14,
    }
    r_first = evaluate_recipient_observation(
        witness, ctx_fresh, ('emitted', 'delivered', 'accepted', 'seated', 'closed_origin'), c0_wit,
    )
    _check(r_first['closure_phase_delta'] == 1 and r_first['reclosure_bip_delta'] == 0,
           'first certified closure contributes 1 closure phase and 0 reclosure bips')
    _reject(
        lambda: evaluate_recipient_observation(
            witness, ctx_fresh, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), c0_wit,
        ),
        ValueError, 'origin',
    )

    # F01 case 2: Replay of an already counted return identity -> ZERO additional beats
    ctx_after_c1 = {
        'recipient_lineage': 'R_1',
        'recipient_scope': 'B_rec:1',
        'window': (10, 20),
        'origin_return_id': 'ret:R0',
        'seen_return_ids': ('ret:R1',),
    }
    c1_wit = {
        'has_certificate': True, 'lineage_id': 'R_1', 'scope_id': 'B_rec:1',
        'return_id': 'ret:R1', 'occurrence_j': 1, 'completion_cut': 16,
    }
    r_replay = evaluate_recipient_observation(
        witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), c1_wit,
    )
    _check(r_replay['reclosure_bip_delta'] == 0 and r_replay['closure_phase_delta'] == 0,
           'replay of already counted return identity must contribute 0 additional beats')

    # F01 case 3: Genuine new compatible reclosure relative to existing origin -> ONE bip
    c2_wit = {
        'has_certificate': True, 'lineage_id': 'R_1', 'scope_id': 'B_rec:1',
        'return_id': 'ret:R2', 'occurrence_j': 2, 'completion_cut': 18,
    }
    r_reclosed = evaluate_recipient_observation(
        witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), c2_wit,
    )
    _check(r_reclosed['reclosure_bip_delta'] == 1 and r_reclosed['closure_phase_delta'] == 1,
           'new compatible reclosure relative to origin must contribute 1 bip')

    # F01 case 4: Wrong lineage or wrong scope -> no admitted reclosure claim
    wrong_lin = dict(c2_wit, lineage_id='R_WRONG')
    wrong_scope = dict(c2_wit, scope_id='B_WRONG', scope_mapped=False)
    _reject(
        lambda: evaluate_recipient_observation(
            witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), wrong_lin,
        ),
        ValueError, 'lineage mismatch',
    )
    _reject(
        lambda: evaluate_recipient_observation(
            witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), wrong_scope,
        ),
        ValueError, 'scope mismatch',
    )

    # Transition & certificate negative controls
    _reject(
        lambda: evaluate_recipient_observation(witness, ctx_after_c1, ('emitted', 'delivered', 'reclosed'), c2_wit),
        ValueError, 'illegal stage transition',
    )
    _reject(
        lambda: evaluate_recipient_observation(
            witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'reclosed'), c2_wit,
        ),
        ValueError, 'illegal stage transition',
    )
    _reject(
        lambda: evaluate_recipient_observation(
            witness, ctx_after_c1, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'),
            dict(c2_wit, has_certificate=False),
        ),
        ValueError, 'closure certificate',
    )
    bad_witness = dict(witness, parent_id='')
    _reject(lambda: evaluate_recipient_observation(bad_witness, ctx_fresh, ('emitted', 'delivered')), ValueError, 'provenance')
    return {
        'recipient_stages_verified': True,
        'first_closure_bips': r_first['reclosure_bip_delta'],
        'replay_bips': r_replay['reclosure_bip_delta'],
        'fresh_reclosure_bips': r_reclosed['reclosure_bip_delta'],
    }


# --- PO-5 & PO-7: Inner/outer disjointness, Q_4 cubical partial^2=0 & FOURIER_SCOPE overtone ---

def q4_cubical_cells_and_boundary(flip_sign_edge=False):
    cells = {d: [] for d in range(5)}
    for tup in itertools.product(('0', '1', '*'), repeat=4):
        d = tup.count('*')
        cells[d].append(tup)
    f_vector = tuple(len(cells[d]) for d in range(5))

    def boundary(cell):
        stars = [i for i, ch in enumerate(cell) if ch == '*']
        terms = {}
        for j, idx in enumerate(stars):
            sign = 1 if (j % 2 == 0) else -1
            c_plus = cell[:idx] + ('1',) + cell[idx + 1:]
            c_minus = cell[:idx] + ('0',) + cell[idx + 1:]
            s_plus = -sign if (flip_sign_edge and len(stars) == 2 and cell == ('*', '*', '0', '0') and j == 0) else sign
            terms[c_plus] = terms.get(c_plus, 0) + s_plus
            terms[c_minus] = terms.get(c_minus, 0) - sign
        return {k: v for k, v in terms.items() if v != 0}

    def boundary_squared(cell):
        total = {}
        for face, coeff in boundary(cell).items():
            for subface, scoeff in boundary(face).items():
                total[subface] = total.get(subface, 0) + coeff * scoeff
        return {k: v for k, v in total.items() if v != 0}

    return f_vector, cells, boundary_squared


def register_outer_returns(inner_return_ids, outer_return_ids):
    overlap = set(inner_return_ids) & set(outer_return_ids)
    if overlap:
        raise ValueError(f'inner return IDs cannot be reused as outer returns: {sorted(overlap)}')
    return len(set(outer_return_ids))


def check_po5_po7_cubical_disjointness_and_fourier_overtone():
    _check(register_outer_returns(('in_01', 'in_02'), ('out_01',)) == 1, 'disjoint outer return should register')
    _reject(lambda: register_outer_returns(('in_01', 'in_02'), ('in_02', 'out_01')), ValueError, 'cannot be reused')

    f_vec, cells, b2 = q4_cubical_cells_and_boundary(flip_sign_edge=False)
    _check(f_vec == (16, 32, 24, 8, 1), f'unexpected Q_4 f-vector {f_vec}')
    for d in (2, 3, 4):
        for cell in cells[d]:
            _check(b2(cell) == {}, f'partial^2 != 0 on Q_4 {d}-cell {cell}')

    _, bad_cells, bad_b2 = q4_cubical_cells_and_boundary(flip_sign_edge=True)
    _check(bad_b2(('*', '*', '0', '0')) != {}, 'flipped incidence sign must break partial^2 = 0')
    _check(len(bad_cells[2]) == 24, 'sanity check on 2-cell count')

    n_order = 12
    l_min = 4
    pulses = (0, 4, 8)
    m_mode = 3
    _check(Fraction(m_mode) > Fraction(n_order, 2 * l_min), 'm=3 must exceed N/(2*l_min)')
    _check(all((m_mode * g) % n_order == 0 for g in pulses), 'chi_3 must evaluate to 1 on pulse support')
    v_hat_3 = Fraction(len(pulses), n_order)
    _check(v_hat_3 == Fraction(1, 4) and v_hat_3 != 0, 'exact DFT overtone v_hat(3) must equal 1/4')
    return {'q4_f_vector': f_vec, 'fourier_v_hat_3': str(v_hat_3)}


# --- PO-6 & PO-8 (F03, F05): Repeated-contact cadence, separate 1-contact stage & signed SI ---

def native_cadence_ratio(id_a, q_a, id_r, q_r, coupled, bound_contacts):
    if id_a == id_r:
        raise ValueError('aliased wave identities rejected')
    if not coupled:
        raise ValueError('uncoupled pair rejected')
    _require_exact_int(q_a, 'q_a')
    _require_exact_int(q_r, 'q_r')
    _require_exact_int(bound_contacts, 'bound_contacts')
    if q_a < 0:
        raise ValueError('q_a must be non-negative')
    if q_r <= 0:
        raise ValueError('reference denominator q_r must be strictly positive')
    if bound_contacts < 2:
        raise ValueError('repeated bound contacts (at least 2) required for biz^{TF} cadence ratio even when q_a == 0')
    return Fraction(q_a, q_r)


def single_contact_interval_association(wavelet_id, parent_id, ref_id, window, bound_contacts=1):
    """Separate passive single-contact stage localization; distinct from biz^{TF} cadence."""
    if wavelet_id == ref_id or parent_id == ref_id:
        raise ValueError('aliased wave identities rejected')
    u, v = window
    _require_exact_int(u, 'window start')
    _require_exact_int(v, 'window end')
    _require_exact_int(bound_contacts, 'bound_contacts')
    if not (u < v):
        raise ValueError('ordered window required')
    if bound_contacts != 1:
        raise ValueError('single_contact_interval_association applies specifically to 1 delivered contact')
    return {
        'kind': 'single_contact_stage_association',
        'wavelet_id': wavelet_id,
        'parent_id': parent_id,
        'reference_id': ref_id,
        'window': (u, v),
        'is_cadence_ratio': False,
        'biz_tf': None,
    }


def observation_turns(q_i, gain_i=1, phi_0=0, phi_1=0):
    """Affine + endpoint specialization C_i^{aff} = g_i * q_i + (phi_1 - phi_0) in Q (signed)."""
    q_val = _require_exact_int(q_i, 'q_i')
    g_val = _require_exact_rational(gain_i, 'gain_i')
    p0 = _require_exact_rational(phi_0, 'phi_0')
    p1 = _require_exact_rational(phi_1, 'phi_1')
    if q_val < 0:
        raise ValueError('q_i must be non-negative')
    if g_val <= 0:
        raise ValueError('gain_i must be strictly positive')
    if not (Fraction(0) <= p0 < Fraction(1) and Fraction(0) <= p1 < Fraction(1)):
        raise ValueError('endpoint phases must lie in [0, 1)')
    delta_end = p1 - p0
    return g_val * q_val + delta_end


def conditional_cs133_anchor(c_a, c_cs, delta_nu_cs=CS133_DELTA_NU_HZ):
    """Conditional SI anchoring allowing signed compared advance C_a in Q with strictly positive C_Cs > 0."""
    ca = _require_exact_rational(c_a, 'C_a')
    ccs = _require_exact_rational(c_cs, 'C_Cs')
    dnu = _require_exact_int(delta_nu_cs, 'Delta_nu_Cs')
    if ccs <= 0 or dnu <= 0:
        raise ValueError('C_Cs and Delta_nu_Cs must be strictly positive')
    t_omega = ccs / Fraction(dnu)
    f_bar_a = Fraction(dnu) * (ca / ccs)
    return {
        'T_omega_s': t_omega,
        'f_bar_a_hz': f_bar_a,
        'delta_theta_over_tau': ca,
        'omega_bar_over_tau_hz': f_bar_a,
        'rate_kind': 'signed_mean_phase_rate',
        'atomic_resonance_certified': False,
    }


def conditional_cs133_nonnegative_rate(c_a, c_cs, delta_nu_cs=CS133_DELTA_NU_HZ):
    """Explicit narrower nonnegative specialization (C_a >= 0) still separate from physical resonance validation."""
    ca = _require_exact_rational(c_a, 'C_a')
    if ca < 0:
        raise ValueError('nonnegative SI rate specialization requires C_a >= 0')
    out = conditional_cs133_anchor(ca, c_cs, delta_nu_cs=delta_nu_cs)
    out['rate_kind'] = 'nonnegative_mean_phase_rate_specialization'
    return out


def check_po6_po8_timing_and_conditional_si():
    # PO-6 / F03 positive and negative controls
    _check(native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=True, bound_contacts=2) == Fraction(3, 5),
           'coupled recurrent cadence ratio must equal 3/5')
    _check(native_cadence_ratio('Wshed', 0, 'Wr', 10, coupled=True, bound_contacts=2) == Fraction(0, 1),
           'shed fragment with repeated bound contacts (2) yields 0 cadence ratio')
    _reject(lambda: native_cadence_ratio('Wshed', 0, 'Wr', 10, coupled=True, bound_contacts=1),
            ValueError, 'at least 2')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 0, coupled=True, bound_contacts=2), ValueError, 'strictly positive')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=False, bound_contacts=2), ValueError, 'uncoupled')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=True, bound_contacts=1), ValueError, 'at least 2')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wa', 5, coupled=True, bound_contacts=2), ValueError, 'aliased')
    _reject(lambda: native_cadence_ratio('Wa', True, 'Wr', 5, coupled=True, bound_contacts=2), TypeError, 'exact int')
    _reject(lambda: native_cadence_ratio('Wa', 3.0, 'Wr', 5, coupled=True, bound_contacts=2), TypeError, 'exact int')

    assoc = single_contact_interval_association('Wshed', 'W_B_1', 'Wr', (10, 20), bound_contacts=1)
    _check(assoc['is_cadence_ratio'] is False and assoc['biz_tf'] is None,
           'single-contact interval association must remain separate from biz^{TF}')

    # PO-8 / F05 positive, signed, and negative controls
    c_a_aligned = observation_turns(3, gain_i=1, phi_0=0, phi_1=0)
    c_cs_aligned = observation_turns(5, gain_i=1, phi_0=0, phi_1=0)
    res_aligned = conditional_cs133_anchor(c_a_aligned, c_cs_aligned)
    _check(res_aligned['f_bar_a_hz'] == Fraction(3, 5) * CS133_DELTA_NU_HZ, 'aligned Cs-133 anchor mismatch')
    _check(res_aligned['T_omega_s'] == Fraction(5, CS133_DELTA_NU_HZ), 'aligned T_omega mismatch')
    _check(res_aligned['delta_theta_over_tau'] == Fraction(3), 'Delta_theta/tau must equal C_a')
    _check(res_aligned['omega_bar_over_tau_hz'] == res_aligned['f_bar_a_hz'], 'Omega_bar/tau must equal f_bar_a')

    # F05 exact signed compared-advance case: q_a=0, g_a=1, phi_0=3/4, phi_1=1/4 -> C_a=-1/2
    c_a_signed = observation_turns(0, gain_i=1, phi_0=Fraction(3, 4), phi_1=Fraction(1, 4))
    _check(c_a_signed == Fraction(-1, 2), 'signed endpoint difference 1/4 - 3/4 must equal -1/2')
    res_signed = conditional_cs133_anchor(c_a_signed, Fraction(1))
    _check(res_signed['T_omega_s'] == Fraction(1, CS133_DELTA_NU_HZ), 'C_Cs=1 duration mismatch')
    _check(res_signed['f_bar_a_hz'] == Fraction(-CS133_DELTA_NU_HZ, 2), 'signed mean phase rate must equal -Delta_nu_Cs/2')
    _check(res_signed['rate_kind'] == 'signed_mean_phase_rate' and res_signed['atomic_resonance_certified'] is False,
           'signed rate must remain typed separately from atomic resonance')
    _reject(lambda: conditional_cs133_nonnegative_rate(c_a_signed, Fraction(1)), ValueError, 'C_a >= 0')
    res_nonneg = conditional_cs133_nonnegative_rate(c_a_aligned, c_cs_aligned)
    _check(res_nonneg['f_bar_a_hz'] == res_aligned['f_bar_a_hz'], 'nonnegative specialization mismatch')

    # Nonzero positive endpoint fraction strictly shifts frequency
    c_a_shifted = observation_turns(3, gain_i=1, phi_0=Fraction(1, 4), phi_1=Fraction(1, 2))
    _check(c_a_shifted == Fraction(13, 4), 'endpoint shift must add 1/4 turn')
    res_shifted = conditional_cs133_anchor(c_a_shifted, c_cs_aligned)
    _check(res_shifted['f_bar_a_hz'] != res_aligned['f_bar_a_hz'], 'nonzero endpoint correction must shift f_bar_a')

    # Nonrecurrent shed wavelet timed on Cs-133 window
    res_shed = conditional_cs133_anchor(observation_turns(0), observation_turns(10))
    _check(res_shed['T_omega_s'] == Fraction(10, CS133_DELTA_NU_HZ) and res_shed['f_bar_a_hz'] == 0,
           'nonrecurrent shed wavelet must get exact T_omega and zero mean rate')

    _reject(lambda: conditional_cs133_anchor(Fraction(3), Fraction(0)), ValueError, 'strictly positive')
    _reject(lambda: conditional_cs133_anchor(Fraction(3), Fraction(-1)), ValueError, 'strictly positive')
    _reject(lambda: observation_turns(3, gain_i=0), ValueError, 'strictly positive')
    _reject(lambda: observation_turns(3, gain_i=1.5), TypeError, 'exact int or Fraction')
    _reject(lambda: observation_turns(3, phi_1=1), ValueError, r'\[0, 1\)')
    return {
        'aligned_f_bar_a_hz': str(res_aligned['f_bar_a_hz']),
        'signed_f_bar_a_hz': str(res_signed['f_bar_a_hz']),
        'shed_T_omega_s': str(res_shed['T_omega_s']),
        'zero_count_one_contact_rejected': True,
    }


def check_contract_and_provenance_dag():
    audit = _load_module('m3_wc_source_audit', 'scripts/audit_scientific_sources.py')
    result = audit.audit(ROOT)
    comp = result['compaction']
    _check((comp['canonical_groups'], comp['canonical_equations'], comp['declared_dependencies']) == (44, 81, 72),
           'inherited canonical counts changed')
    _check(comp['m3'] == {'equations': 7, 'sources': 2}, 'inherited M3 cell/mapping counts changed')
    _check(comp['m3_wavelet_compaction'] == {
        'equations': 11,
        'new_equations': 10,
        'inherited_equations': 1,
        'relocated_figures': 2,
        'retained_anchors': 6,
        'new_anchors': 2,
        'sources': 6,
    }, 'unexpected m3_wavelet_compaction summary')

    # Scoped syntax check for non-appendix forward provenance references in rendered Main
    _, parts = audit.include_graph(ROOT, 'main')
    offset = 0
    label_pos = {}
    for path, text in parts:
        for match in re.finditer(r'\\label\{([^}]+)\}', text):
            label_pos[match.group(1)] = (offset + match.start(), path)
        offset += len(text)
    offset = 0
    inversions = []
    for path, text in parts:
        for match in re.finditer(r'\\aodprovenance\{((?:[^{}]|\{[^{}]*\})*)\}', text):
            prov_pos = offset + match.start()
            for ref in re.findall(r'\\(?:eqref|eqnref|secref|figref|tabref|ref)\{([^}]+)\}', match.group(1)):
                if ref in label_pos:
                    rpos, rpath = label_pos[ref]
                    if rpos > prov_pos and not rpath.startswith('appendices/'):
                        inversions.append((path, ref, rpath))
        offset += len(text)
    _check(not inversions, f'forward provenance inversions detected: {inversions}')
    return {'m3_wavelet_compaction': comp['m3_wavelet_compaction'], 'forward_provenance_syntax_hits': 0}


def run_all_standalone_checks():
    return {
        'po1': check_po1_duon_duad_same_current(),
        'po2_po3_f02_f04': check_po2_po3_wavelet_dedup_and_cancellation(),
        'po4_f01': check_po4_recipient_event_lattice(),
        'po5_po7': check_po5_po7_cubical_disjointness_and_fourier_overtone(),
        'po6_po8_f03_f05': check_po6_po8_timing_and_conditional_si(),
        'contract_and_dag': check_contract_and_provenance_dag(),
    }


def test_standalone_exact_checks():
    summary = run_all_standalone_checks()
    assert summary['po1']['resolved_variants'] == 12
    assert summary['po2_po3_f02_f04']['deduplicated_returns'] == 3
    assert summary['po2_po3_f02_f04']['out_of_window_prefix_count'] == 0
    assert summary['po4_f01']['first_closure_bips'] == 0
    assert summary['po4_f01']['replay_bips'] == 0
    assert summary['po4_f01']['fresh_reclosure_bips'] == 1
    assert summary['po5_po7']['q4_f_vector'] == (16, 32, 24, 8, 1)
    assert summary['po6_po8_f03_f05']['zero_count_one_contact_rejected'] is True
    assert summary['contract_and_dag']['forward_provenance_syntax_hits'] == 0


if pytest is not None:
    @pytest.fixture
    def isolated(tmp_path):
        return Path(shutil.copytree(
            ROOT, tmp_path / 'source',
            ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache',
                                         '*.pdf', '*.xdv', '*.log', '*.fls', '*.fdb_latexmk'),
        ))


    def check_m3_wavelet_compaction(root):
        audit = _load_module('m3_wc_audit_direct', 'scripts/audit_scientific_sources.py')
        compaction = _load_module('m3_wc_compaction_direct', 'scripts/audit_ontology_compaction.py')
        maps = {surface: audit.label_map(root, surface) for surface in ('main', 'manual')}
        eqs = {surface: audit.equations(root, surface) for surface in ('main', 'manual')}
        return compaction.audit_m3_wavelet_compaction(root, maps, eqs)


    def test_wavelet_equation_body_cannot_be_removed_behind_retained_label(isolated):
        audit = _load_module('m3_wc_audit_body', 'scripts/audit_scientific_sources.py')
        path = isolated / 'sections/06_wave_state_relational_time.tex'
        block = audit.equations(isolated)['eq:aod-wavelet-continuation']
        path.write_text(path.read_text().replace(block, r'\label{eq:aod-wavelet-continuation}', 1))
        with pytest.raises(ValueError, match='M3 wavelet compaction statement or owner changed eq:aod-wavelet-continuation'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='M3 wavelet compaction statement or owner changed eq:aod-wavelet-continuation'):
            audit.audit(isolated)


    def test_conditional_si_formula_alteration_is_rejected(isolated):
        audit = _load_module('m3_wc_audit_si', 'scripts/audit_scientific_sources.py')
        path = isolated / 'sections/07_cell_measures_mappings.tex'
        block = audit.equations(isolated)['eq:m3-cs133-tau-interface']
        altered = block.replace(r'\tau C_a', r'2\tau C_a')
        assert altered != block
        path.write_text(path.read_text().replace(block, altered, 1))
        with pytest.raises(ValueError, match='M3 wavelet compaction statement or owner changed eq:m3-cs133-tau-interface'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='M3 mathematical source changed|M3 wavelet compaction statement or owner changed'):
            audit.audit(isolated)


    def test_relocated_figure_cannot_drift_back_to_field_section(isolated):
        audit = _load_module('m3_wc_audit_fig', 'scripts/audit_scientific_sources.py')
        s5 = isolated / 'sections/05_curl_closure_duon_current.tex'
        s6 = isolated / 'sections/06_field.tex'
        label = r'\label{fig:closure-ladder}'
        assert label in s5.read_text()
        s5.write_text(s5.read_text().replace(label, '', 1))
        s6.write_text(s6.read_text() + '\n' + label + '\n')
        with pytest.raises(ValueError, match='M3 wavelet compaction figure owner changed fig:closure-ladder'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='M3 wavelet compaction figure owner changed fig:closure-ladder'):
            audit.audit(isolated)


    def test_retained_stub_anchor_cannot_be_dropped(isolated):
        audit = _load_module('m3_wc_audit_stub', 'scripts/audit_scientific_sources.py')
        s6 = isolated / 'sections/06_field.tex'
        label = r'\label{subsec:e2-duad}'
        assert label in s6.read_text()
        s6.write_text(s6.read_text().replace(label, '', 1))
        with pytest.raises(ValueError, match='M3 wavelet compaction tracked anchor changed subsec:e2-duad'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='unresolved main reference subsec:e2-duad|M3 wavelet compaction tracked anchor changed'):
            audit.audit(isolated)


    def test_wavelet_contract_cannot_self_rebind_changed_source(isolated):
        audit = _load_module('m3_wc_audit_tamper', 'scripts/audit_scientific_sources.py')
        path = isolated / 'sections/05_curl_closure_duon_current.tex'
        path.write_text(path.read_text() + '\n% unauthorized edit\n')
        contract = isolated / 'contracts/scientific/M3_WAVELET_COMPACTION_BINDINGS.json'
        record = json.loads(contract.read_text())
        record['sources']['sections/05_curl_closure_duon_current.tex'] = hashlib.sha256(path.read_bytes()).hexdigest()
        contract.write_text(json.dumps(record))
        with pytest.raises(ValueError, match='scientific contract integrity changed M3_WAVELET_COMPACTION_BINDINGS.json'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='scientific contract integrity changed M3_WAVELET_COMPACTION_BINDINGS.json'):
            audit.audit(isolated)


if __name__ == '__main__':
    print(json.dumps(run_all_standalone_checks(), indent=2))
