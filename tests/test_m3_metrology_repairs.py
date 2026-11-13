"""Regression controls for trusted observation scope and exact comparison inputs."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'manual/scripts'))
import aod_m3_metrology as a
import aod_mapping_error as m


def correction_fixture(owner):
    compared, reference, realization = a.phase_fixture()
    records = {'compared': compared, 'reference': reference}
    payload = {key: deepcopy(records[owner][key]) for key in ('coordinate', 'epoch', 'window')}
    payload.update(observation_id=records[owner]['id'], value_turns='1/2', already_applied=False)
    source = m.source('correction:owner', 'calibration', {'corrections': {'offset': payload}})
    # Both channels have identical access to the evidence; rejection must be ownership-based.
    for record in records.values():
        record['sources'].append(source)
    realization['trusted_sources'][source['id']] = source
    entry = {'id': 'offset', 'source_id': source['id'], 'value_turns': '1/2', 'already_applied': False}
    records[owner]['corrections'] = [entry]
    return records, realization


@pytest.mark.parametrize('owner', ['compared', 'reference'])
def test_correction_cannot_move_to_the_other_observation(owner):
    records, realization = correction_fixture(owner)
    args = records['compared'], records['reference'], realization
    assert a.compare_accumulations(*args)['ratio'] == ('8/17' if owner == 'compared' else '7/18')
    other = 'reference' if owner == 'compared' else 'compared'
    records[other]['corrections'] = records[owner]['corrections']
    records[owner]['corrections'] = []
    with pytest.raises(ValueError, match='correction'):
        a.compare_accumulations(*args)


@pytest.mark.parametrize('owner', ['compared', 'reference'])
def test_single_owner_correction_cannot_be_applied_to_both_observations(owner):
    records, realization = correction_fixture(owner)
    other = 'reference' if owner == 'compared' else 'compared'
    records[other]['corrections'] = deepcopy(records[owner]['corrections'])
    with pytest.raises(ValueError, match='correction'):
        a.compare_accumulations(records['compared'], records['reference'], realization)


def test_separately_trusted_reference_correction_is_allowed_and_passive():
    records, realization = correction_fixture('reference')
    before = m.canonical([records, realization])
    result = a.compare_accumulations(records['compared'], records['reference'], realization)
    assert result['ratio'] == '7/18'
    assert result['physical_correspondence'] == 'unestablished'
    assert m.canonical([records, realization]) == before


def test_legacy_correction_without_trusted_observation_owner_is_rejected():
    records, realization = correction_fixture('compared')
    source_id = records['compared']['corrections'][0]['source_id']
    payload = deepcopy(realization['trusted_sources'][source_id]['payload'])
    del payload['corrections']['offset']['observation_id']
    replacement = m.source(source_id, 'calibration', payload)
    realization['trusted_sources'][source_id] = replacement
    for record in records.values():
        record['sources'] = [replacement if item['id'] == source_id else item for item in record['sources']]
    with pytest.raises(ValueError, match='correction'):
        a.compare_accumulations(records['compared'], records['reference'], realization)


def test_correction_evidence_cannot_substitute_integer_for_boolean_ownership_flag():
    records, realization = correction_fixture('compared')
    source_id = records['compared']['corrections'][0]['source_id']
    payload = deepcopy(realization['trusted_sources'][source_id]['payload'])
    payload['corrections']['offset']['already_applied'] = 0
    replacement = m.source(source_id, 'calibration', payload)
    realization['trusted_sources'][source_id] = replacement
    for record in records.values():
        record['sources'] = [replacement if item['id'] == source_id else item for item in record['sources']]
    with pytest.raises(ValueError, match='correction'):
        a.compare_accumulations(records['compared'], records['reference'], realization)


def test_phase_source_evidence_cannot_substitute_boolean_for_integer_winding():
    compared, reference, realization = a.phase_fixture()
    compared['winding'] = 1
    payload = {'observations': {record['id']: a.phase_payload(record) for record in (compared, reference)}}
    payload['observations'][compared['id']]['winding'] = True
    source = m.source('fixture:phase', 'model', payload)
    for record in (compared, reference):
        record['sources'] = [source]
    realization['trusted_sources'][source['id']] = source
    with pytest.raises(ValueError, match='extractor'):
        a.compare_accumulations(compared, reference, realization)


def test_parameter_source_evidence_cannot_substitute_boolean_dimension():
    record = a.finite_dependency_fixture()
    record['expression'] = ['mul', ['input', 'X'], ['parameter', 'gain']]
    parameter = {'value': '1/2', 'unit': '1', 'dimension': [0, 0, 0]}
    evidence = {**parameter, 'dimension': [False, 0, 0]}
    source = m.source('parameter:gain', 'model', {'parameters': {'gain': evidence}})
    record['sources'].append(source)
    record['trusted_sources'][source['id']] = source
    record['parameters'] = {'gain': {**parameter, 'source_id': source['id'], 'quantity_id': 'gain'}}
    with pytest.raises(ValueError, match='parameter differs'):
        a.validate_error_dependencies(record)


def native_preparation_fixture(flag):
    temporal = a.t
    base = temporal.example_context()
    preparation = {**base.preparation, 'flag': False}
    domain = temporal.domain_for(base.population, base.couplings, preparation, base.record.window)
    context = replace(base, preparation=preparation, observation=temporal.observation_law([domain]))
    prediction = temporal.predict(context)
    record, _, _ = a.phase_fixture()
    record.update(
        kind='native_reclosure_count', count=prediction['complete_temporal_record']['counts']['compared'],
        channel='compared', prediction=prediction, original_context=context,
        window=prediction['complete_temporal_record']['window'],
        scope=prediction['complete_temporal_record']['native_scope'],
        coordinate=prediction['coordinate'], epoch=prediction['epoch_seconds'],
        preparation={**preparation, 'flag': flag},
    )
    binding = a.bind_native_prediction(prediction, context)
    payload = {key: deepcopy(record[key]) for key in
               ('kind', 'coordinate', 'epoch', 'window', 'scope', 'preparation', 'count', 'channel')}
    payload.update(prediction_sha256=binding['prediction_sha256'],
                   original_context_sha256=binding['original_context_sha256'])
    source = m.source('native:declared', 'model', {'observations': {record['id']: payload}})
    record['sources'] = [source]
    return record, {source['id']: source}


def test_native_preparation_boolean_is_preserved_under_complete_replay():
    record, trusted = native_preparation_fixture(False)
    before = m.canonical(record['prediction'])
    result = a.validate_observation(record, trusted)
    assert result['preparation']['flag'] is False
    assert record['original_context'].preparation['flag'] is False
    assert m.canonical(record['prediction']) == before


def test_native_preparation_type_cannot_change_after_outer_extractor_is_resealed():
    record, trusted = native_preparation_fixture(0)
    assert record['original_context'].preparation['flag'] is False
    assert type(record['preparation']['flag']) is int
    # The outer source really authenticates 0, but the independent replay context commits False.
    assert m.canonical(trusted['native:declared']['payload']['observations'][record['id']]['preparation']) == m.canonical(record['preparation'])
    with pytest.raises(ValueError, match='preparation differs'):
        a.validate_observation(record, trusted)


def event(identity='event:A', timestamp='3/2'):
    payload = {
        'origin': 'implantation', 'timestamp_origin': 'implantation',
        'timestamp': timestamp, 'timestamp_unit': 's',
        'detector_timebase': {'id': 'clock:A', 'unit': 's',
                             'calibration': {'kind': 'unknown', 'reason': 'not provided'}},
        'resolution': '1/1000', 'uncertainty': deepcopy(a.UNKNOWN), 'status': 'censored',
        'conditioning': {'retained': [False, {'selected': True, 'label': '1'}]},
        'transport': 'flight retained', 'selection': 'declared campaign selection',
    }
    source = m.source(identity, 'model', {'event_timing': deepcopy(payload)})
    return {**payload, 'source': source, 'trusted_sources': {identity: source}}


def nuclear_fixture():
    record, _, realization = a.phase_fixture()
    record.update(kind='nuclear_event_timestamp', event_timing=event())
    source = record['event_timing']['source']
    payload = {key: deepcopy(record[key]) for key in
               ('kind', 'scope', 'coordinate', 'epoch', 'window', 'preparation')}
    payload.update(event_source_id=source['id'], event_source_sha256=source['sha256'])
    outer = m.source('event:outer-observation', 'model', {'observations': {record['id']: payload}})
    record['sources'].extend([source, outer])
    trusted = {**realization['trusted_sources'], source['id']: source, outer['id']: outer}
    return record, trusted


@pytest.mark.parametrize(('field', 'value'), [
    ('id', 'other-observation'), ('kind', 'shed_packet_event'), ('scope', 'other-population'),
    ('coordinate', 'other-clock'), ('epoch', 'other-origin'), ('window', [100000, 100001]),
    ('preparation', {'protocol': 'other preparation'}),
])
def test_nuclear_outer_context_cannot_change_without_association_evidence(field, value):
    record, trusted = nuclear_fixture()
    a.validate_observation(record, trusted)
    record[field] = value
    with pytest.raises(ValueError):
        a.validate_observation(record, trusted)


def test_nuclear_outer_context_cannot_substitute_another_valid_trusted_event():
    record, trusted = nuclear_fixture()
    replacement = event('event:B', '7/2')
    assert a.validate_event_timing(replacement)['status'] == 'valid_event_metadata'
    source = replacement['source']
    record['sources'].append(source)
    trusted[source['id']] = source
    record['event_timing'] = replacement
    with pytest.raises(ValueError, match='extractor/type'):
        a.validate_observation(record, trusted)


def test_nuclear_association_does_not_invent_a_detector_seconds_to_cut_map():
    record, trusted = nuclear_fixture()
    before = m.canonical([record, trusted])
    result = a.validate_observation(record, trusted)
    assert result['coordinate'] == 'fixture-cut' and result['window'] == [10, 22]
    assert result['event_timing']['timestamp_unit'] == 's'
    assert result['event_timing']['timestamp'] == '3/2'
    assert a.validate_event_timing(result['event_timing'])['lifetime_prediction'] is None
    assert m.canonical([record, trusted]) == before


def rebind_declaration(record, trusted):
    payload = {key: deepcopy(value) for key, value in record.items()
               if key not in ('source_id', 'sources')}
    source = m.source(record['source_id'], 'model', {'comparison_assessment': payload})
    record['sources'] = [source if item['id'] == source['id'] else item for item in record['sources']]
    trusted[source['id']] = source


def comparison_fixture(kind='oscillator_phase_advance', prediction='2', comparison='1'):
    record, trusted = a.comparison_fixture()
    unit = 'count' if kind in ('native_reclosure_count', 'shed_packet_event') else 'Hz'
    record.update(kind=kind, unit=unit)
    quantities = {}
    for side, value in [('prediction', prediction), ('comparison', comparison)]:
        record[side]['value'] = value
        quantities[record[side]['quantity_id']] = {'kind': kind, 'unit': unit, 'value': value}
    source_id = record['prediction']['source_id']
    source = m.source(source_id, 'calibration', {'comparison_quantities': quantities})
    record['sources'] = [source if item['id'] == source_id else item for item in record['sources']]
    trusted[source_id] = source
    record['influences'][0]['correction']['unit'] = unit
    rebind_declaration(record, trusted)
    return record, trusted


@pytest.mark.parametrize(('original', 'replacement'), [(False, 0), (True, 1), ('1', 1), (0, '0')])
def test_nested_assessment_evidence_preserves_json_scalar_types(original, replacement):
    record, trusted = comparison_fixture()
    record['influences'][0]['materiality']['reason'] = {'nested': [original]}
    rebind_declaration(record, trusted)
    a.assess_comparison(record, trusted)
    record['influences'][0]['materiality']['reason']['nested'][0] = replacement
    with pytest.raises(ValueError, match='trusted declaration'):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize(('original', 'replacement'), [(False, 0), (True, 1), ('1', 1), (0, '0')])
def test_nested_event_evidence_preserves_json_scalar_types(original, replacement):
    record = event()
    record['conditioning'] = {'nested': [original]}
    payload = {key: deepcopy(value) for key, value in record.items() if key not in ('source', 'trusted_sources')}
    source = m.source('event:typed', 'model', {'event_timing': payload})
    record.update(source=source, trusted_sources={source['id']: source})
    a.validate_event_timing(record)
    record['conditioning']['nested'][0] = replacement
    with pytest.raises(ValueError, match='trusted origin'):
        a.validate_event_timing(record)


@pytest.mark.parametrize('side', ['prediction', 'comparison'])
@pytest.mark.parametrize(('observed', 'evidence'), [(0, False), (1, True), (0, '0'), ('1', 1)])
def test_endpoint_evidence_preserves_its_exact_json_representation(side, observed, evidence):
    values = {'prediction': '2', 'comparison': '1', side: observed}
    record, trusted = comparison_fixture(**values)
    source_id = record[side]['source_id']
    source = trusted[source_id]
    payload = deepcopy(source['payload'])
    payload['comparison_quantities'][record[side]['quantity_id']]['value'] = evidence
    replacement = m.source(source_id, source['role'], payload)
    record['sources'] = [replacement if item['id'] == source_id else item for item in record['sources']]
    trusted[source_id] = replacement
    with pytest.raises(ValueError, match='trusted quantity'):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize('evidence_kind', ['transfer', 'materiality'])
def test_scoped_evidence_window_cannot_substitute_boolean_for_integer(evidence_kind):
    record, trusted = comparison_fixture()
    influence = record['influences'][0]
    expected = {'coordinate': record['coordinate'], 'epoch': record['epoch'], 'window': [False, 12]}
    if evidence_kind == 'transfer':
        condition = influence['conditions']
        condition['input_location'] = 'external_environment'
        expected.update(input_location='external_environment', effect_location='internal_apparatus')
        condition['transfer'] = {'kind': 'source_bound', 'source_id': 'typed:scope', 'payload_key': 'scope'}
    else:
        expected.update(influence_id=influence['id'], bound='1/100', tolerance='1/10', unit=record['unit'])
        influence['materiality'] = {'kind': 'bounded_below_tolerance', 'bound': '1/100', 'tolerance': '1/10',
                                    'unit': record['unit'], 'source_id': 'typed:scope', 'payload_key': 'scope'}
    source = m.source('typed:scope', 'calibration', {'scope': expected})
    record['sources'].append(source); trusted[source['id']] = source
    influence['source_ids'].append(source['id'])
    rebind_declaration(record, trusted)
    with pytest.raises(ValueError, match='differs'):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize('kind', ['native_reclosure_count', 'shed_packet_event'])
@pytest.mark.parametrize('side', ['prediction', 'comparison'])
@pytest.mark.parametrize('value', [0, 1, '0', '3'])
def test_count_endpoint_accepts_nonnegative_exact_integer_representations(kind, side, value):
    values = {'prediction': '2', 'comparison': '1', side: value}
    record, trusted = comparison_fixture(kind, **values)
    before = m.canonical([record, trusted])
    result = a.assess_comparison(record, trusted)
    assert result['residual'] == str(Fraction(values['prediction']) - Fraction(values['comparison']))
    assert not result['independent_physical_validation']
    assert m.canonical([record, trusted]) == before


@pytest.mark.parametrize('kind', ['native_reclosure_count', 'shed_packet_event'])
@pytest.mark.parametrize('side', ['prediction', 'comparison'])
@pytest.mark.parametrize('value', [-1, '-1', '1/2', True, False, 0.5, '0.5', '2/2', '01', '+1', '1/1', '1.0'])
def test_count_endpoint_rejects_negative_fractional_or_noncanonical_values(kind, side, value):
    values = {'prediction': '2', 'comparison': '1', side: value}
    record, trusted = comparison_fixture(kind, **values)
    with pytest.raises(ValueError):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize('field', ['coordinate', 'unit'])
@pytest.mark.parametrize('value', [None, False, True, 0, 1, [], ['cut'], {}, {'name': 'cut'}, '', ' \t\n'])
def test_reflection_coordinate_and_unit_require_nonblank_strings(field, value):
    record, trusted = comparison_fixture()
    record['reflection_duration'][field] = value
    rebind_declaration(record, trusted)
    with pytest.raises(ValueError, match='reflection duration'):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize('duration', [None, False, 'duration', [], {'kind': 'declared_separate'},
    {'kind': 'unknown', 'reason': 'absent', 'value': 0}])
def test_malformed_reflection_duration_records_are_rejected(duration):
    record, trusted = comparison_fixture()
    record['reflection_duration'] = duration
    rebind_declaration(record, trusted)
    with pytest.raises(ValueError):
        a.assess_comparison(record, trusted)


@pytest.mark.parametrize('observation_map', [None, False, [], 'unknown', {},
    {'kind': 'identity', 'reason': 'assumed equal'}, {'kind': 'unknown', 'reason': 'absent', 'gain': '1'}])
def test_malformed_reflection_observation_maps_are_rejected(observation_map):
    record, trusted = comparison_fixture()
    record['reflection_duration']['observation_map'] = observation_map
    rebind_declaration(record, trusted)
    with pytest.raises(ValueError):
        a.assess_comparison(record, trusted)


def test_valid_boolean_metadata_survives_json_roundtrip_without_changing_math_or_inputs():
    record, trusted = comparison_fixture()
    record['influences'][0]['materiality']['reason'] = {'flags': [False, True], 'label': '1', 'number': 1}
    rebind_declaration(record, trusted)
    before = m.canonical([record, trusted])
    original = a.assess_comparison(record, trusted)
    copied_record, copied_trusted = json.loads(json.dumps([record, trusted]))
    assert a.assess_comparison(copied_record, copied_trusted) == original
    assert original['residual'] == '1' and not original['corrections_applied_by_assessment']
    assert original['complete_physical_uncertainty']['kind'] == 'unknown'
    assert m.canonical([record, trusted]) == before
    timing = event()
    timing_before = m.canonical(timing)
    assert a.validate_event_timing(json.loads(json.dumps(timing))) == a.validate_event_timing(timing)
    assert m.canonical(timing) == timing_before


def test_reordered_dictionaries_preserve_source_bindings_and_results():
    def reordered(value):
        if isinstance(value, dict):
            return {key: reordered(item) for key, item in reversed(list(value.items()))}
        if isinstance(value, list):
            return [reordered(item) for item in value]
        return value
    record, trusted = comparison_fixture()
    before = m.canonical([record, trusted])
    reordered_record, reordered_trusted = reordered([record, trusted])
    assert list(reordered_record) != list(record)
    assert a.assess_comparison(reordered_record, reordered_trusted) == a.assess_comparison(record, trusted)
    timing = event()
    assert a.validate_event_timing(reordered(timing)) == a.validate_event_timing(timing)
    assert m.canonical([record, trusted]) == before
