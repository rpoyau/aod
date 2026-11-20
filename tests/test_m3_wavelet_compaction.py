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


# --- PO-2 & PO-3: AOmegaD wavelet continuation, overlap dedup & cancellation history ---

VALID_WAVELET_SEAT_STATES = frozenset({
    'open_duon', 'seated_duad', 'coupled_segment', 'shed_continuation',
})


def make_wavelet(wavelet_id, parent_id, ancestry, window, sigma_seat, records,
                 return_ids=(), signed_current=0, is_admitted_wave=False):
    if not parent_id or not ancestry:
        raise ValueError('wavelet must preserve parent_id and ancestry')
    if sigma_seat not in VALID_WAVELET_SEAT_STATES:
        raise ValueError('invalid wavelet seat state')
    u, v = window
    _require_exact_int(u, 'window start')
    _require_exact_int(v, 'window end')
    if not (u < v):
        raise ValueError('window must satisfy u < v')
    if not records:
        raise ValueError('wavelet must retain committed construction records')
    return_tuple = tuple(return_ids)
    if is_admitted_wave and (sigma_seat in {'open_duon', 'shed_continuation'} or len(set(return_tuple)) < 1):
        raise ValueError('open/shed wavelet or zero-return fragment cannot be promoted to an admitted wave')
    return {
        'id_w': wavelet_id,
        'parent_id': parent_id,
        'ancestry': tuple(ancestry),
        'window': (u, v),
        'sigma_seat': sigma_seat,
        'records': tuple(records),
        'return_ids': return_tuple,
        'signed_current': _require_exact_int(signed_current, 'signed_current'),
        'is_admitted_wave': bool(is_admitted_wave),
    }


def deduplicated_return_count(wavelets, target_lineage):
    seen = set()
    for w in wavelets:
        if w['parent_id'] != target_lineage:
            raise ValueError('lineage mismatch across wavelet overlap union')
        seen.update(w['return_ids'])
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
    w1 = make_wavelet(
        'w1', parent_state['id'], ('lin:1', 'seg:1'), (0, 8),
        'coupled_segment', ('r1', 'r2'), return_ids=('occ_01', 'occ_02'),
        signed_current=1, is_admitted_wave=True,
    )
    w2 = make_wavelet(
        'w2', parent_state['id'], ('lin:1', 'seg:2'), (4, 10),
        'coupled_segment', ('r2', 'r3'), return_ids=('occ_02',),
        signed_current=-1, is_admitted_wave=True,
    )
    w_shed = make_wavelet(
        'w_shed', parent_state['id'], ('lin:1', 'shed:1'), (8, 12),
        'shed_continuation', ('r3',), return_ids=(), signed_current=0,
        is_admitted_wave=False,
    )
    _check(parent_state['active_beyond_v'] is True, 'window restriction must not terminate parent wave')
    _check(len(w_shed['return_ids']) == 0, 'shed wavelet may carry zero local returns')
    _reject(
        lambda: make_wavelet(
            'bad_promo', 'W_B_1', ('lin:1',), (0, 2), 'open_duon', ('r0',),
            return_ids=(), is_admitted_wave=True,
        ),
        ValueError, 'cannot be promoted',
    )
    _reject(
        lambda: make_wavelet(
            'bad_detached', '', (), (0, 2), 'open_duon', ('r0',),
        ),
        ValueError, 'parent_id',
    )
    naive_sum = len(w1['return_ids']) + len(w2['return_ids'])
    dedup = deduplicated_return_count((w1, w2), 'W_B_1')
    _check(dedup == 2 and dedup < naive_sum, 'overlapping windows must deduplicate shared return IDs')
    w_other = make_wavelet('w_other', 'W_B_2', ('lin:2',), (4, 10), 'coupled_segment', ('r9',), return_ids=('occ_09',))
    _reject(lambda: deduplicated_return_count((w1, w_other), 'W_B_1'), ValueError, 'lineage mismatch')

    combined = combine_signed_wavelets(w1, w2)
    _check(combined['net_current'] == 0, 'opposing signed currents should cancel to zero')
    _check(len(combined['retained_histories']) == 2, 'cancellation must retain both histories')
    _check(combined['retained_histories'][0] != combined['retained_histories'][1], 'retained histories must stay distinct')
    return {'deduplicated_returns': dedup, 'naive_sum': naive_sum, 'retained_histories': 2}


# --- PO-4: Shed continuation witness & four-stage recipient event lattice ---

ALLOWED_RECIPIENT_TRANSITIONS = {
    'emitted': frozenset({'delivered'}),
    'delivered': frozenset({'accepted', 'unaccepted_pass'}),
    'accepted': frozenset({'seated', 'pending_unseated'}),
    'seated': frozenset({'reclosed'}),
    'unaccepted_pass': frozenset(),
    'pending_unseated': frozenset(),
    'reclosed': frozenset(),
}


def validate_recipient_chain(witness, stages, has_closure_certificate=False):
    required_keys = ('parent_id', 'emit_boundary', 'emit_cut', 'route', 'X_route', 'post_shed_parent_state')
    if any(not witness.get(k) for k in required_keys):
        raise ValueError('shed continuation witness missing required provenance field')
    if witness['route'] not in {'endo', 'exo', 'redir', 'open'}:
        raise ValueError('invalid shed route tag')
    if not stages or stages[0] != 'emitted':
        raise ValueError('recipient chain must begin at emitted')
    for cur, nxt in zip(stages, stages[1:]):
        if nxt not in ALLOWED_RECIPIENT_TRANSITIONS.get(cur, frozenset()):
            raise ValueError(f'illegal stage transition {cur} -> {nxt}')
    terminal = stages[-1]
    if terminal == 'reclosed':
        if not has_closure_certificate:
            raise ValueError('reclosed stage requires a full closure certificate')
        return 1
    return 0


def check_po4_recipient_event_lattice():
    witness = {
        'parent_id': 'W_B_1',
        'emit_boundary': 'dT_R1',
        'emit_cut': 12,
        'route': 'exo',
        'X_route': Fraction(1, 2),
        'post_shed_parent_state': 'S_W_post_12',
    }
    _check(validate_recipient_chain(witness, ('emitted', 'delivered', 'unaccepted_pass')) == 0,
           'unaccepted_pass must contribute 0 reclosures')
    _check(validate_recipient_chain(witness, ('emitted', 'delivered', 'accepted', 'pending_unseated')) == 0,
           'pending_unseated must contribute 0 reclosures')
    _check(validate_recipient_chain(witness, ('emitted', 'delivered', 'accepted', 'seated')) == 0,
           'seated without reclosure must contribute 0 reclosures')
    _check(validate_recipient_chain(witness, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'),
                                    has_closure_certificate=True) == 1,
           'certified reclosed chain must contribute 1 reclosure')
    _reject(lambda: validate_recipient_chain(witness, ('emitted', 'delivered', 'reclosed'), True),
            ValueError, 'illegal stage transition')
    _reject(lambda: validate_recipient_chain(witness, ('emitted', 'delivered', 'accepted', 'reclosed'), True),
            ValueError, 'illegal stage transition')
    _reject(lambda: validate_recipient_chain(witness, ('emitted', 'delivered', 'accepted', 'seated', 'reclosed'), False),
            ValueError, 'closure certificate')
    bad_witness = dict(witness, parent_id='')
    _reject(lambda: validate_recipient_chain(bad_witness, ('emitted', 'delivered')), ValueError, 'provenance')
    return {'recipient_stages_verified': True}


# --- PO-5 & PO-7: Inner/outer disjointness, Q_4 cubical partial^2=0 & FOURIER_SCOPE overtone ---

def q4_cubical_cells_and_boundary(flip_sign_edge=False):
    # Cubical cells in Q_4 encoded as 4-tuples over {'0', '1', '*'} where '*' is an interval coordinate.
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

    # FOURIER_SCOPE exact overtone check: N=12, l_min=4 pulse train at {0, 4, 8}.
    # At m=3 (> N/(2*l_min) = 3/2), m*g = 0 mod 12 for every g in {0, 4, 8},
    # so chi_3(g) = 1 identically and v_hat(3) = (1 + 1 + 1) / 12 = 1/4 != 0 exactly.
    n_order = 12
    l_min = 4
    pulses = (0, 4, 8)
    m_mode = 3
    _check(Fraction(m_mode) > Fraction(n_order, 2 * l_min), 'm=3 must exceed N/(2*l_min)')
    _check(all((m_mode * g) % n_order == 0 for g in pulses), 'chi_3 must evaluate to 1 on pulse support')
    v_hat_3 = Fraction(len(pulses), n_order)
    _check(v_hat_3 == Fraction(1, 4) and v_hat_3 != 0, 'exact DFT overtone v_hat(3) must equal 1/4')
    return {'q4_f_vector': f_vec, 'fourier_v_hat_3': str(v_hat_3)}


# --- PO-6 & PO-8: Reference-window timing & conditional SI / Cs-133 / tau anchoring ---

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
    if q_a > 0 and bound_contacts < 2:
        raise ValueError('recurrent cadence comparison requires at least 2 bound contacts')
    if q_a == 0 and bound_contacts < 1:
        raise ValueError('localized/shed fragment timing requires a bound reference contact')
    return Fraction(q_a, q_r)


def observation_turns(q_i, gain_i=1, phi_0=0, phi_1=0):
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
    ca = _require_exact_rational(c_a, 'C_a')
    ccs = _require_exact_rational(c_cs, 'C_Cs')
    dnu = _require_exact_int(delta_nu_cs, 'Delta_nu_Cs')
    if ccs <= 0 or dnu <= 0:
        raise ValueError('C_Cs and Delta_nu_Cs must be strictly positive')
    if ca < 0:
        raise ValueError('C_a must be non-negative')
    t_omega = ccs / Fraction(dnu)
    f_bar_a = Fraction(dnu) * (ca / ccs)
    # Angular coefficients over tau = 2*pi stay exact rationals: Delta_theta/tau = C_a, Omega_bar/tau = f_bar_a.
    return {
        'T_omega_s': t_omega,
        'f_bar_a_hz': f_bar_a,
        'delta_theta_over_tau': ca,
        'omega_bar_over_tau_hz': f_bar_a,
    }


def check_po6_po8_timing_and_conditional_si():
    # PO-6 positive and negative controls
    _check(native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=True, bound_contacts=2) == Fraction(3, 5),
           'coupled recurrent cadence ratio must equal 3/5')
    _check(native_cadence_ratio('Wshed', 0, 'Wr', 10, coupled=True, bound_contacts=2) == Fraction(0, 1),
           'shed fragment timed on bound reference window must yield 0')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 0, coupled=True, bound_contacts=2), ValueError, 'strictly positive')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=False, bound_contacts=2), ValueError, 'uncoupled')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wr', 5, coupled=True, bound_contacts=1), ValueError, 'at least 2')
    _reject(lambda: native_cadence_ratio('Wa', 3, 'Wa', 5, coupled=True, bound_contacts=2), ValueError, 'aliased')
    _reject(lambda: native_cadence_ratio('Wa', True, 'Wr', 5, coupled=True, bound_contacts=2), TypeError, 'exact int')
    _reject(lambda: native_cadence_ratio('Wa', 3.0, 'Wr', 5, coupled=True, bound_contacts=2), TypeError, 'exact int')

    # PO-8 positive and negative controls
    c_a_aligned = observation_turns(3, gain_i=1, phi_0=0, phi_1=0)
    c_cs_aligned = observation_turns(5, gain_i=1, phi_0=0, phi_1=0)
    res_aligned = conditional_cs133_anchor(c_a_aligned, c_cs_aligned)
    _check(res_aligned['f_bar_a_hz'] == Fraction(3, 5) * CS133_DELTA_NU_HZ, 'aligned Cs-133 anchor mismatch')
    _check(res_aligned['T_omega_s'] == Fraction(5, CS133_DELTA_NU_HZ), 'aligned T_omega mismatch')
    _check(res_aligned['delta_theta_over_tau'] == Fraction(3), 'Delta_theta/tau must equal C_a')
    _check(res_aligned['omega_bar_over_tau_hz'] == res_aligned['f_bar_a_hz'], 'Omega_bar/tau must equal f_bar_a')

    # Nonzero endpoint fraction strictly shifts frequency
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
    return {'aligned_f_bar_a_hz': str(res_aligned['f_bar_a_hz']), 'shed_T_omega_s': str(res_shed['T_omega_s'])}


def check_contract_and_provenance_dag():
    audit = _load_module('m3_wc_source_audit', 'scripts/audit_scientific_sources.py')
    result = audit.audit(ROOT)
    comp = result['compaction']
    _check((comp['canonical_groups'], comp['canonical_equations'], comp['declared_dependencies']) == (44, 81, 72),
           'inherited canonical counts changed')
    _check(comp['m3'] == {'equations': 7, 'sources': 2}, 'inherited M3 cell/mapping counts changed')
    _check(comp['m3_wavelet_compaction'] == {
        'equations': 11, 'relocated_figures': 2, 'retained_anchors': 8, 'sources': 6,
    }, 'unexpected m3_wavelet_compaction summary')

    # Verify zero non-appendix forward provenance inversions across rendered Main
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
    return {'m3_wavelet_compaction': comp['m3_wavelet_compaction'], 'forward_provenance_inversions': 0}


def run_all_standalone_checks():
    return {
        'po1': check_po1_duon_duad_same_current(),
        'po2_po3': check_po2_po3_wavelet_dedup_and_cancellation(),
        'po4': check_po4_recipient_event_lattice(),
        'po5_po7': check_po5_po7_cubical_disjointness_and_fourier_overtone(),
        'po6_po8': check_po6_po8_timing_and_conditional_si(),
        'contract_and_dag': check_contract_and_provenance_dag(),
    }


# --- Pytest test functions & isolated mutation negative controls ---

def test_standalone_exact_checks():
    summary = run_all_standalone_checks()
    assert summary['po1']['resolved_variants'] == 12
    assert summary['po2_po3']['deduplicated_returns'] == 2
    assert summary['po4']['recipient_stages_verified'] is True
    assert summary['po5_po7']['q4_f_vector'] == (16, 32, 24, 8, 1)
    assert summary['contract_and_dag']['forward_provenance_inversions'] == 0


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
        with pytest.raises(ValueError, match='M3 wavelet compaction retained anchor changed subsec:e2-duad'):
            check_m3_wavelet_compaction(isolated)
        with pytest.raises(ValueError, match='unresolved main reference subsec:e2-duad|M3 wavelet compaction retained anchor changed'):
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
