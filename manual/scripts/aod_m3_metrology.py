#!/usr/bin/env python3
"""Exact, source-bound observer reductions. No atomic or nuclear dynamics added.

Observer turns, native reclosures, packets and detector estimates remain distinct.
Published uncertainty transcriptions do not supply finite probability laws.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re

import aod_m3_temporal as t
import aod_mapping_error as m

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'contracts/scientific/TEMPORAL_METROLOGY.json'
DATA = ROOT / 'manual/data/m3/temporal_metrology'
REPORT = DATA / 'report.json'
CS = 9192631770
PROFILE_DIGESTS = {
    'hydrogen': '428bcdd706881032274bdf1bf339915e4c6df692ea8a231f9f4494e2abc2e462',
    'cesium': '727c293115f4ec81bd901d7dd5f4bfb26ec96045f235525eeb490321b5233b6d',
}
UNCERTAINTY_DIGEST = '5d8f530bd78862171b22581fb937b1668bed2068e6c4e7afcbb23ae82893a061'
KINDS = {'native_reclosure_count', 'shed_packet_event', 'oscillator_phase_advance',
         'fluorescence_population_estimate', 'nuclear_event_timestamp'}
CLASSES = {'exact_mathematical_fixture', 'declared_model_prediction', 'measured_input_reduction',
           'calibration_identity', 'independent_prediction'}
REQUIRED = {'id','evidence_class','kind','scope','sources','preparation','apparatus','detector',
            'estimator','coordinate','epoch','window','calibration','corrections','uncertainty','selection'}
UNKNOWN = {'kind':'unknown', 'reason':'Complete physical observation/model uncertainty not established'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _same_evidence(left, right):
    """Compare evidence in the canonical JSON representation used for its hash."""
    try:
        return m.canonical(left) == m.canonical(right)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False


def exact(value):
    """Canonical JSON integer/rational, never decimal or binary floating input."""
    require(type(value) in (int, str), 'canonical exact integer/rational required')
    try:
        result = Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError('invalid exact rational') from exc
    require(type(value) is int or str(result) == value, 'noncanonical rational')
    return result


def printed(value):
    """Preserve a source decimal token separately; exact arithmetic on its digits."""
    require(type(value) is str and re.fullmatch(r'-?\d+(?:\.\d+)?',value), 'printed decimal token required')
    return Q(value)


def no_floats(value):
    require(not isinstance(value,float), 'floating value forbidden')
    if isinstance(value,dict):
        for item in value.values(): no_floats(item)
    elif isinstance(value,(list,tuple)):
        for item in value: no_floats(item)


def integer(value, name='integer'):
    require(type(value) is int, name+' must be an integer excluding bool')
    return value


def window(value):
    require(isinstance(value,list) and len(value)==2, 'window must contain two cuts')
    a,b=(integer(x,'cut') for x in value)
    require(a<b,'ordered nonempty window required')
    return a,b


def load_profile(name):
    require(name in PROFILE_DIGESTS, 'unknown apparatus profile')
    result=json.loads((DATA/name/'protocol.json').read_text())
    _bind_profile(result,name)
    return result


def _bind_profile(protocol,name):
    require(isinstance(protocol,dict) and m.digest(protocol)==PROFILE_DIGESTS[name],
            'changed or unbound '+name+' source protocol')


def bind_native_prediction(prediction, original_context):
    replayed=t.replay_prediction(prediction,original_context)
    return {'prediction_sha256':m.digest(replayed),
            'original_context_sha256':m.digest(t.plain(asdict(original_context))),
            'native_schema_version':replayed['schema_version'],
            'classification':replayed['classification'],
            'physical_correspondence':'unestablished',
            'complete_physical_uncertainty':deepcopy(UNKNOWN)}


def validate_observation(record, trusted_sources):
    require(isinstance(record,dict) and REQUIRED<=set(record),'missing observation fields')
    no_floats(record)
    require(record['kind'] in KINDS and record['evidence_class'] in CLASSES,'observation type/class')
    require(all(type(record[x]) is str and record[x].strip() for x in
                ('id','scope','coordinate','epoch')),'observation identity/scope')
    window(record['window'])
    registry=m.validate_sources(record['sources'],trusted_sources)
    require(all(record[x] for x in ('preparation','apparatus','detector','estimator','selection')),
            'explicit apparatus/preparation/readout/selection required')
    require(isinstance(record['calibration'],dict) and isinstance(record['uncertainty'],dict),
            'typed calibration and uncertainty required')
    require(isinstance(record['corrections'],list),'correction list required')
    _corrections(record['corrections'],registry,record)
    require(record['uncertainty'].get('kind') in ('unknown','source_reported_uncertainty','declared_finite_law'),
            'uncertainty classification required')
    if record['uncertainty']['kind']=='unknown':
        require('value' not in record['uncertainty'] and record['uncertainty'].get('reason'),
                'unknown uncertainty is not zero')
    elif record['uncertainty']['kind']=='source_reported_uncertainty':
        u=record['uncertainty']
        require(set(u)=={'kind','source','campaign_or_measurement','unit','reported_value_or_bound',
            'category_or_coverage_status','reporting_precision'},'source reported uncertainty fields')
        require(u['source'] in registry and all(type(v) is str and v for v in u.values()),
                'source reported uncertainty provenance/precision')
        require(_same_evidence(registry[u['source']]['payload'].get('reported_uncertainty',{}).get(record['id']),u),
                'reported uncertainty differs from trusted source')
    else:
        u=record['uncertainty']
        require(set(u)=={'kind','source_id','order','support'} and u['source_id'] in registry,
                'declared finite uncertainty law fields')
        require(registry[u['source_id']]['role'] in ('model','calibration') and
                _same_evidence(registry[u['source_id']]['payload'].get('joint_law'),{'order':u['order'],'support':u['support']}),
                'finite law differs from trusted model source')
        _exact_support(u['support']);m.joint_moments(u['support'],u['order'])
    # This version deliberately cannot certify an independent atomic prediction.
    require(record['evidence_class']!='independent_prediction',
            'independent physical prediction requires an unavailable validated dynamics/map interface')
    if record['kind']=='oscillator_phase_advance':
        phase_advance(record)
        require(set(record['source_ids'])<=set(registry),'phase source lineage absent')
        require(any(isinstance(registry[i]['payload'],dict) and
                    _same_evidence(registry[i]['payload'].get('observations',{}).get(record['id']),phase_payload(record))
                    for i in record['source_ids']),'phase extractor differs from source-bound observation')
    elif record['kind']=='native_reclosure_count':
        require(integer(record.get('count'),'reclosure count')>=0,'nonnegative reclosure count')
        require('prediction' in record and 'original_context' in record,'native observation needs independent context replay')
        binding=bind_native_prediction(record['prediction'],record['original_context'])
        require(record.get('channel') in ('compared','reference'),'native count channel required')
        require(record['count']==record['prediction']['complete_temporal_record']['counts'][record['channel']],
                'native count differs from replayed observation')
        native=record['prediction']['complete_temporal_record']
        require(record['window']==native['window'] and record['scope']==native['native_scope'],
                'native observation window/scope differs from replayed context')
        require(record['coordinate']==record['prediction']['coordinate'] and
                record['epoch']==record['prediction']['epoch_seconds'] and
                _same_evidence(record['preparation'],record['original_context'].preparation),
                'native observation coordinate/epoch/preparation differs from replayed context')
        payload={k:deepcopy(record[k]) for k in ('kind','coordinate','epoch','window','scope','preparation','count','channel')}
        payload.update(prediction_sha256=binding['prediction_sha256'],original_context_sha256=binding['original_context_sha256'])
        _bind_extractor(record,registry,payload,roles=('model',))
    elif record['kind']=='shed_packet_event':
        require(type(record.get('packet_id')) is str and record['packet_id'],'packet ancestry required')
        cut=integer(record.get('cut'),'packet cut')
        a,b=window(record['window']);require(a<cut<=b,'packet outside observation window')
        _bind_extractor(record,registry,{k:deepcopy(record[k]) for k in
            ('kind','coordinate','epoch','window','packet_id','cut')})
    elif record['kind']=='fluorescence_population_estimate':
        population_fraction(record['populations'])
        _bind_extractor(record,registry,{k:deepcopy(record[k]) for k in
            ('kind','coordinate','epoch','window','populations')})
    else:
        event=record['event_timing']
        require(all(_same_evidence(registry.get(key),value) for key,value in event['trusted_sources'].items()),
                'event evidence not bound by outer observation trust registry')
        validate_event_timing(event)
        payload={k:deepcopy(record[k]) for k in ('kind','scope','coordinate','epoch','window','preparation')}
        payload.update(event_source_id=event['source']['id'],event_source_sha256=event['source']['sha256'])
        _bind_extractor(record,registry,payload)
    return deepcopy(record)


def _bind_extractor(record,registry,payload,roles=('model','calibration','evaluation')):
    require(any(s['role'] in roles and isinstance(s['payload'],dict) and
                _same_evidence(s['payload'].get('observations',{}).get(record['id']),payload) for s in registry.values()),
            'observable extractor/type differs from trusted observation source')


def phase_payload(record):
    return {k:deepcopy(record[k]) for k in ('kind','coordinate','epoch','window','winding',
        'phase_start','phase_end','orientation','unwrapping_convention')}


def phase_advance(record):
    require(isinstance(record,dict) and record.get('kind')=='oscillator_phase_advance',
            'oscillator phase required; packet/closure is not a turn')
    required={'winding','phase_start','phase_end','coordinate','epoch','window','orientation',
              'unwrapping_convention','source_ids'}
    require(required<=set(record),'phase metadata incomplete')
    require(record['orientation'] in ('forward','reverse') and
            record['unwrapping_convention']=='signed_net_winding','phase orientation/unwrapping convention')
    window(record['window'])
    require(all(type(record[x]) is str and record[x] for x in ('coordinate','epoch')),'phase coordinate/epoch')
    require(isinstance(record['source_ids'],list) and record['source_ids'] and
            len(set(record['source_ids']))==len(record['source_ids']),'phase source lineage')
    a,b=exact(record['phase_start']),exact(record['phase_end'])
    require(0<=a<1 and 0<=b<1,'phase endpoints outside [0,1)')
    return Q(integer(record['winding'],'winding'))+b-a


def _corrections(corrections,registry,context):
    require(isinstance(corrections,list),'corrections list required')
    seen=set();total=Q(0)
    for c in corrections:
        require(set(c)=={'id','source_id','value_turns','already_applied'},'correction fields')
        require(c['id'] not in seen and type(c['already_applied']) is bool,'duplicate correction or ambiguous ownership')
        require(c['source_id'] in registry,'correction source absent')
        evidence={k:deepcopy(context[k]) for k in ('coordinate','epoch','window')}
        evidence.update(observation_id=context['id'],value_turns=c['value_turns'],already_applied=c['already_applied'])
        require(isinstance(registry[c['source_id']]['payload'],dict) and
                _same_evidence(registry[c['source_id']]['payload'].get('corrections',{}).get(c['id']),evidence),
                'correction value/ownership/scope differs from trusted source')
        seen.add(c['id']);v=exact(c['value_turns'])
        require(not c['already_applied'],'correction already included; cannot apply twice')
        total+=v
    return total


def compare_accumulations(compared, reference, reference_realization):
    require(isinstance(reference_realization,dict) and set(reference_realization)==
            {'source','trusted_sources','reference_id','kind','physical_correspondence'},'reference realization fields')
    trusted=reference_realization['trusted_sources']
    validate_observation(compared,trusted);validate_observation(reference,trusted)
    require(all(compared[k]==reference[k] for k in ('coordinate','epoch','window','orientation')),
            'phase records require matched coordinate/epoch/window/orientation')
    require(reference_realization['reference_id']==reference['id'] and
            reference_realization['kind']=='Cs133_equivalent_reference','reference identity/type')
    src=reference_realization['source'];m.validate_sources([src],trusted)
    require(src['role'] in ('model','calibration'),'reference realization needs separate model/calibration evidence')
    require(_same_evidence(src['payload'],{'reference_id':reference['id'],'coordinate':reference['coordinate'],
            'epoch':reference['epoch'],'window':reference['window'],'defining_integer_hz':CS,
            'physical_correspondence':reference_realization['physical_correspondence']}),'reference realization scope mismatch')
    require(reference_realization['physical_correspondence'] in ('unestablished','declared_fixture'),
            'this companion does not certify a physical Cs realization')
    reg={s['id']:s for s in compared['sources']+reference['sources']}
    a=phase_advance(compared)+_corrections(compared['corrections'],reg,compared)
    r=phase_advance(reference)+_corrections(reference['corrections'],reg,reference)
    require(r>0 and reference['orientation']=='forward','positive corrected reference elapsed advance required')
    return {'ratio':str(a/r),'duration_seconds':str(r/CS),'mean_frequency_hz':str(CS*a/r),
            'compared_advance_turns':str(a),'reference_advance_turns':str(r),
            'window':deepcopy(compared['window']),'coordinate':compared['coordinate'],'epoch':compared['epoch'],
            'evidence_class':'exact_mathematical_fixture' if compared['evidence_class']==reference['evidence_class']=='exact_mathematical_fixture' else 'calibration_identity',
            'status':'conditional_on_declared_reference_realization','physical_correspondence':'unestablished',
            'reference_realization_sha256':src['sha256'],'complete_physical_uncertainty':deepcopy(UNKNOWN),
            'universal_seconds_per_bip':False,'independent_atomic_prediction':False}


def heterodyne_advance(maser,reference,synthesizer):
    require(all(maser[k]==reference[k]==synthesizer[k] for k in
                ('coordinate','epoch','window','orientation','unwrapping_convention')),'heterodyne scope mismatch')
    return phase_advance(maser)-284*phase_advance(reference)-phase_advance(synthesizer)


def validate_transport_ledger(record):
    """Committed packet ancestry through a cut; no observer-driven transitions."""
    require(set(record)=={'window','packets','pending_start','pending_end'},'transport fields')
    a,b=window(record['window']);seen=set();emitted=arrived=pa=pb=0
    for packet in record['packets']:
        require(set(packet)=={'id','emitted','arrived'},'packet ancestry fields')
        require(type(packet['id']) is str and packet['id'] and packet['id'] not in seen,'duplicate packet identity')
        seen.add(packet['id']);e=integer(packet['emitted'],'emission cut');r=packet['arrived']
        require(e<=b,'future emission inaccessible')
        if r is not None:
            r=integer(r,'arrival cut');require(e<=r<=b,'arrival precedes emission or reads future cut')
        emitted+=int(a<e<=b);arrived+=int(r is not None and a<r<=b)
        pa+=int(e<=a and (r is None or r>a));pb+=int(r is None)
    require(integer(record['pending_start'])==pa and integer(record['pending_end'])==pb,'pending ancestry mismatch')
    require(emitted-arrived==pb-pa,'transport conservation failed')
    return {'emitted':emitted,'arrived':arrived,'pending_start':pa,'pending_end':pb,
            'net':emitted-arrived,'scope':'committed_record_only; observer introduces no kernel update'}


def population_fraction(record):
    require(isinstance(record,dict) and set(record)=={'N3','N4','calibration_3','calibration_4','estimator'},
            'calibrated population fields')
    require(record['calibration_3'] and record['calibration_3']==record['calibration_4'],
            'population estimates need compatible detector/background calibration')
    require(record['estimator']=='normalized_fluorescence','unsupported population estimator')
    a,b=exact(record['N3']),exact(record['N4']);require(a>=0 and b>=0 and a+b>0,'positive population denominator required')
    return b/(a+b)


def reduce_hydrogen(protocol, measurement_id):
    _bind_profile(protocol,'hydrogen')
    require(measurement_id in ('table_iv','table_vi','published_mean'),'unknown H measurement')
    uncertainty=json.loads((DATA/'hydrogen/reported_uncertainty.json').read_text())
    require(m.digest(uncertainty)==UNCERTAINTY_DIGEST,'changed reported uncertainty transcription')
    if measurement_id=='published_mean':
        a=reduce_hydrogen(protocol,'table_iv');b=reduce_hydrogen(protocol,'table_vi')
        frequency=(exact(a['corrected_frequency_hz'])+exact(b['corrected_frequency_hz']))/2
        chain=[{'operation':'arithmetic_mean','measurements':['table_iv','table_vi'],'frequency_hz':str(frequency)}]
        components={};squares=None;apparatus='published combination of two continuous maser reductions'
        correction_ownership={'combined':'No new correction added to corrected estimates'}
    else:
        key='Table_IV' if measurement_id=='table_iv' else 'Table_VI'
        experiment='experiment_1' if measurement_id=='table_iv' else 'experiment_2'
        contract=protocol['observation_contracts'][experiment]
        require(contract['method']=='continuous_active_maser_heterodyne','H apparatus method mismatch')
        terms=protocol['table_term_provenance'][key]
        total=integer(protocol['receiver']['multiplier'])*printed(protocol['receiver']['reference_nominal_hz'])
        chain=[{'term':'nominal_reference_multiple','frequency_hz':str(total),'value_token':protocol['receiver']['reference_nominal_hz']}]
        for name,term in terms.items():
            total+=printed(term['value_hz']);chain.append({'term':name,'value_token':term['value_hz'],
                'frequency_hz':str(total),'source_locator':term['source']})
        frequency=total;components=deepcopy(uncertainty[measurement_id])
        squares=str(sum((printed(x)**2 for x in components.values()),Q(0)))
        apparatus=contract['apparatus'];correction_ownership={'applied':contract['added_corrections'],
            'already_in_input':['NP3','wall'] if measurement_id=='table_vi' else [],
            'zero_correction_does_not_remove_uncertainty':True}
    return {'measurement_id':measurement_id,'corrected_frequency_hz':str(frequency),
            'source_id':protocol['source_id'],'profile_sha256':m.digest(protocol),
            'method':'continuous_active_maser_heterodyne','apparatus':apparatus,
            'evidence_class':'measured_input_reduction','correction_chain':chain,
            'correction_ownership':correction_ownership,
            'source_reported_uncertainty':{'source':uncertainty['source'],'campaign_or_measurement':measurement_id,
                'unit':'Hz','reported_value_or_bound':uncertainty['quoted'][measurement_id],
                'category_or_coverage_status':'published standard uncertainty',
                'reporting_precision':'preserved decimal token','components_hz':components,
                'component_square_sum_hz2':squares,'finite_distribution_inferred':False,
                'combination_scope':'printed component arithmetic; source convention, not complete physical covariance'},
            'published_rounded_frequency_hz':'1420405751.768' if measurement_id=='published_mean' else None,
            'raw_phase_stream_available':False,'missing_raw_inputs':deepcopy(protocol['missing_raw_inputs']),
            'complete_physical_uncertainty':deepcopy(UNKNOWN),'independent_atomic_prediction':False}


def reduce_cesium(protocol,campaign_id):
    _bind_profile(protocol,'cesium')
    require(campaign_id in ('August2013','typical_Table1'),'unknown Cs campaign')
    budget=protocol['uncertainty_budgets'][campaign_id];items={}
    keys=(('TypeA','TypeA_standard_uncertainty'),('TypeB','TypeB_standard_uncertainty')) if campaign_id=='August2013' else (('TypeB','quoted_TypeB_standard_uncertainty'),)
    for label,key in keys:
        token=budget[key];items[label]={'source':protocol['primary']['doi'],'campaign_or_measurement':campaign_id,
            'unit':'Hz','reported_value_or_bound':str(printed(token)*Q(CS,10**15)),
            'printed_fractional_times_1e15':token,'category_or_coverage_status':'published '+label+' standard uncertainty',
            'reporting_precision':'preserved printed token','finite_distribution_inferred':False}
    return {'campaign_id':campaign_id,'profile_sha256':m.digest(protocol),'method':protocol['method'],
            'evidence_class':'measured_input_reduction','source_reported_uncertainty':items,
            'reported_entries':deepcopy(budget.get('entries',[])),
            'spin_exchange_statistics_already_in_TypeA':True,'complete_covariance':deepcopy(UNKNOWN),
            'nominal_synthesis_is_exact_carrier':False,'Cs_SI_frequency_role':'calibration_identity',
            'raw_population_and_servo_replay':False,'missing_raw_inputs':deepcopy(protocol['missing_for_raw_replay']),
            'independent_atomic_prediction':False}


def _exact_support(support):
    require(isinstance(support,list) and support,'explicit finite support required')
    for row in support:
        require(isinstance(row,list) and len(row)==2 and isinstance(row[1],dict),'finite support row')
        exact(row[0])
        for value in row[1].values(): exact(value)


def validate_error_dependencies(record):
    """One identity per uncertain input; existing finite propagation owns moments."""
    require(isinstance(record,dict) and set(record)=={'sources','trusted_sources','inputs','active',
            'expression','parameters','output_dimension','support','means','covariance'},'dependency record fields')
    no_floats(record);registry=m.validate_sources(record['sources'],record['trusted_sources'])
    inputs=record['inputs'];require(isinstance(inputs,dict) and inputs,'uncertain input definitions required')
    seen=set()
    for name,item in inputs.items():
        require(set(item)=={'source_id','quantity_id','unit','dimension','kind','components'},'dependency input fields')
        require(item['source_id'] in registry and registry[item['source_id']]['role']!='evaluation','prediction uncertainty source role')
        identity=(registry[item['source_id']]['sha256'],item['quantity_id'])
        require(identity not in seen,'same uncertain source duplicated under aliases');seen.add(identity)
        require(item['kind'] in ('finite_law','source_reported_uncertainty','unknown','bound'),'uncertainty input kind')
        m.validate_port(m.port(name,dimension=item['dimension'],unit=item['unit']))
        require(isinstance(item['components'],list) and all(x in inputs for x in item['components']),'aggregate component references')
    active=record['active'];require(isinstance(active,list) and len(active)==len(set(active)) and set(active)<=set(inputs),'active uncertainty identities')
    require(set(active)==m.expression_refs(record['expression'],'input'),'expression/dependency inputs differ')
    def descendants(name,path=()):
        require(name not in path,'aggregate dependency cycle')
        out=set()
        for child in inputs[name]['components']:
            out.add(child);out.update(descendants(child,path+(name,)))
        return out
    for name in inputs:
        children=descendants(name)
        if name in active:
            require(not children&set(active),'aggregate and own components counted together')
    for name,item in record['parameters'].items():
        require(isinstance(item,dict) and set(item)=={'value','unit','dimension','source_id','quantity_id'},
                'parameter needs exact source-bound quantity fields')
        exact(item['value']);m.validate_port(m.port(name,dimension=item['dimension'],unit=item['unit']))
        require(item['source_id'] in registry and registry[item['source_id']]['role'] in ('model','calibration','definition'),
                'parameter source role')
        expected={k:item[k] for k in ('value','unit','dimension')}
        require(_same_evidence(registry[item['source_id']]['payload'].get('parameters',{}).get(item['quantity_id']),expected),
                'parameter differs from trusted source')
    dimension=m.expression_dimension(record['expression'],inputs,record['parameters'])
    require(list(dimension)==record['output_dimension'],'output dimension mismatch')
    if any(inputs[name]['kind']!='finite_law' for name in active):
        require(record['support'] is None and record['means'] is None and record['covariance'] is None,
                'reported/unknown inputs cannot be promoted to a fabricated finite law')
        return {'status':'source_metadata_only','output_variance':None,'physical_uncertainty':deepcopy(UNKNOWN)}
    require(record['support'] is not None,'finite law requires explicit source-bound joint support')
    _exact_support(record['support'])
    if record['means'] is not None:
        for value in record['means'].values(): exact(value)
    if record['covariance'] is not None:
        for row in record['covariance']:
            for value in row: exact(value)
    # The exact joint law must occur in a separately supplied source payload.
    law={'order':active,'support':record['support']}
    require(any(_same_evidence(s['payload'].get('joint_law'),law) for s in registry.values()
                if isinstance(s['payload'],dict) and s['role'] in ('model','calibration')),'joint law absent from trusted source payload')
    return m.propagate(record['expression'],active,record['parameters'],record['means'],record['covariance'],record['support'])


def validate_event_timing(record):
    required={'origin','timestamp_origin','timestamp','timestamp_unit','detector_timebase','resolution','uncertainty',
              'status','conditioning','transport','selection','source','trusted_sources'}
    require(isinstance(record,dict) and set(record)==required,'event timing fields')
    no_floats(record)
    source=record['source'];m.validate_sources([source],record['trusted_sources'])
    payload={k:deepcopy(record[k]) for k in required-{'source','trusted_sources'}}
    require(_same_evidence(source['payload'].get('event_timing'),payload),'event timing differs from trusted origin/timebase evidence')
    require(record['origin'] in ('formation','implantation','detection') and record['timestamp_origin']==record['origin'],
            'event origin cannot be silently renamed')
    exact(record['timestamp']);require(exact(record['resolution'])>0,'positive timestamp resolution')
    require(record['timestamp_unit'] in ('s','detector_tick'),'event timestamp unit')
    clock=record['detector_timebase']
    require(isinstance(clock,dict) and set(clock)=={'id','unit','calibration'} and clock['id'] and
            clock['unit']==record['timestamp_unit'],'typed detector timebase and consistent timestamp unit')
    calibration=clock['calibration']
    require(isinstance(calibration,dict) and calibration.get('kind') in ('unknown','source_bound'),
            'timebase calibration must be explicit')
    if calibration['kind']=='unknown':
        require(set(calibration)=={'kind','reason'} and calibration['reason'],'unknown timebase calibration is not zero')
    else:
        require(set(calibration)=={'kind','source_id','payload_key'} and calibration['source_id'] in record['trusted_sources'],
                'source-bound timebase calibration evidence')
        bound=record['trusted_sources'][calibration['source_id']]
        m.validate_sources([bound],record['trusted_sources'])
        require(bound['role'] in ('model','calibration') and _same_evidence(bound['payload'].get(calibration['payload_key']),
                {'timebase_id':clock['id'],'unit':clock['unit']}),'timebase calibration scope differs')
    require(record['status'] in ('accepted','rejected','censored'),'event selection status')
    require(all(record[k] for k in ('conditioning','transport','selection')),'event transport/selection required')
    u=record['uncertainty'];require(isinstance(u,dict),'typed timing uncertainty')
    require(u.get('kind') in ('unknown','source_reported_uncertainty','bound'),'timing uncertainty kind')
    if u['kind']=='unknown':
        require('value' not in u and u.get('reason'),'unknown timing uncertainty is not resolution or zero')
    else:
        require(set(u)=={'kind','value','unit','evidence_source_id'} and exact(u['value'])>=0 and
                u['unit']==record['timestamp_unit'] and u['evidence_source_id'] in record['trusted_sources'],
                'timing uncertainty needs independently bound evidence and unit')
        bound=record['trusted_sources'][u['evidence_source_id']]
        m.validate_sources([bound],record['trusted_sources'])
        require(_same_evidence(bound['payload'].get('timing_uncertainty'),{'timebase_id':clock['id'],
                'kind':u['kind'],'value':u['value'],'unit':u['unit']}),'timing uncertainty evidence mismatch')
    return {'status':'valid_event_metadata','origin':record['origin'],'selection_status':record['status'],
            'timebase_calibration_status':calibration['kind'],'nuclear_dynamics':'not_implemented','lifetime_prediction':None}


def assess_comparison(record, trusted_sources):
    """Audit a declared comparison; do not apply corrections or certify physics.

    Endpoint values, dependency declarations and influence metadata are bound to
    supplied trusted sources. A passing record establishes metadata consistency,
    not completeness of the physical model, budget or source declaration.
    """
    fields={'id','source_id','sources','measurand','kind','unit','coordinate','epoch','window',
            'reflection_duration','prediction','comparison','reference_role','influences'}
    require(isinstance(record,dict) and set(record)==fields,'comparison assessment fields')
    no_floats(record)
    registry=m.validate_sources(record['sources'],trusted_sources)
    for key in ('id','source_id','measurand','coordinate','epoch'):
        require(type(record[key]) is str and record[key].strip(),'comparison identity/scope')
    require(record['source_id'] in registry,'comparison declaration source absent')
    declaration={k:deepcopy(v) for k,v in record.items() if k not in ('source_id','sources')}
    require(_same_evidence(registry[record['source_id']]['payload'].get('comparison_assessment'),declaration),
            'comparison assessment differs from trusted declaration')
    units={'native_reclosure_count':{'count','1'},'shed_packet_event':{'count','1'},
           'oscillator_phase_advance':{'turn','Hz','1'},'fluorescence_population_estimate':{'1'},
           'nuclear_event_timestamp':{'s'}}
    require(record['kind'] in units and record['unit'] in units[record['kind']],
            'comparison observable/unit mismatch')
    window(record['window'])
    duration=record['reflection_duration']
    require(isinstance(duration,dict),'typed reflection duration required')
    if duration.get('kind')=='unknown':
        require(set(duration)=={'kind','reason'} and duration['reason'],
                'unknown reflection duration is not zero')
    else:
        require(set(duration)=={'kind','coordinate','value','unit','observation_map'} and
                duration['kind']=='declared_separate' and
                all(type(duration[k]) is str and duration[k].strip() for k in ('coordinate','unit')),
                'reflection duration needs its separate coordinate and unit as nonblank strings')
        require(exact(duration['value'])>=0,'nonnegative reflection duration')
        observation_map=duration['observation_map']
        require(isinstance(observation_map,dict) and set(observation_map)=={'kind','reason'} and
                observation_map['kind']=='unknown' and observation_map['reason'],
                'this assessment does not equate reflection duration with the observation window')
    role=record['reference_role']
    require(role in ('calibration_anchor','evaluation','reference_dependent_evaluation'),
            'comparison reference role')
    dependencies={};values={}
    for side in ('prediction','comparison'):
        item=record[side]
        require(isinstance(item,dict) and set(item)=={'value','source_id','quantity_id','dependency_ids'},
                'comparison endpoint fields')
        values[side]=exact(item['value'])
        if record['kind'] in ('native_reclosure_count','shed_packet_event'):
            require(values[side]>=0 and values[side].denominator==1,
                    'count endpoint must be an exact nonnegative integer')
        require(item['source_id'] in registry and type(item['quantity_id']) is str and item['quantity_id'],
                'comparison endpoint source')
        allowed=('model','calibration','definition') if side=='prediction' else ('evaluation','calibration')
        require(registry[item['source_id']]['role'] in allowed,'comparison endpoint source role')
        if side=='comparison' and role=='calibration_anchor':
            require(registry[item['source_id']]['role']=='calibration','anchor requires calibration source')
        ids=item['dependency_ids']
        require(isinstance(ids,list) and len(set(ids))==len(ids) and set(ids)<=set(registry),
                'comparison dependency source identities')
        if side=='prediction':
            require(all(registry[i]['role'] in allowed for i in ids),
                    'evaluation source cannot enter prediction dependencies')
        payload={'kind':record['kind'],'unit':record['unit'],'value':item['value']}
        require(_same_evidence(registry[item['source_id']]['payload'].get('comparison_quantities',{}).get(item['quantity_id']),payload),
                'comparison endpoint differs from trusted quantity')
        dependencies[side]={registry[i]['sha256'] for i in [item['source_id'],*ids]}
    shared=sorted(dependencies['prediction']&dependencies['comparison'])
    influences=record['influences'];require(isinstance(influences,list),'comparison influences list')
    seen=set();unresolved=[];bounded=[];ownership={}
    for item in influences:
        required={'id','stage','mechanism','source_ids','correction','residual_uncertainty',
                  'evaluation_method','conditions','materiality'}
        require(isinstance(item,dict) and set(item)==required,'comparison influence fields')
        identity=item['id']
        require(type(identity) is str and identity and identity not in seen,'duplicate influence identity')
        seen.add(identity)
        require(item['stage'] in ('input','setup','output') and type(item['mechanism']) is str and item['mechanism'],
                'influence stage/mechanism')
        ids=item['source_ids']
        require(isinstance(ids,list) and ids and len(ids)==len(set(ids)) and set(ids)<=set(registry),
                'influence source identities')
        correction=item['correction'];require(isinstance(correction,dict),'typed correction required')
        status=correction.get('kind')
        if status in ('applied','included_in_input'):
            require(set(correction)=={'kind','value','unit'} and correction['unit']==record['unit'],
                    'correction value/unit/ownership')
            exact(correction['value'])
        else:
            require(status in ('not_applied','unknown') and set(correction)=={'kind','reason'} and correction['reason'],
                    'unapplied/unknown correction needs reason without a value')
            if status=='unknown':unresolved.append(identity)
        ownership[identity]=status
        uncertainty=item['residual_uncertainty'];require(isinstance(uncertainty,dict),'typed residual uncertainty')
        if uncertainty.get('kind')=='unknown':
            require(set(uncertainty)=={'kind','reason'} and uncertainty['reason'],'unknown residual uncertainty is not zero')
            unresolved.append(identity)
        else:
            require(uncertainty.get('kind') in ('source_reported_uncertainty','bound') and
                    set(uncertainty)=={'kind','value','unit','category_or_coverage_status'} and
                    uncertainty['unit']==record['unit'] and uncertainty['category_or_coverage_status'],
                    'residual uncertainty needs separate value/unit/category')
            require(exact(uncertainty['value'])>=0,'nonnegative residual uncertainty')
        require(item['evaluation_method'] in ('Type_A','Type_B','unknown','not_applicable'),
                'evaluation method is Type A/B, not random/systematic')
        condition=item['conditions'];require(isinstance(condition,dict),'typed influence conditions')
        if condition.get('kind')=='unknown':
            require(set(condition)=={'kind','reason'} and condition['reason'],'unknown conditions need reason')
            require(status not in ('applied','included_in_input'),'applied correction requires declared applicability conditions')
            unresolved.append(identity)
        else:
            require(set(condition)=={'kind','input_location','effect_location','transfer'} and
                    condition['kind']=='specified','influence condition fields')
            locations={'internal_apparatus','external_environment','reference','detector'}
            require(condition['input_location'] in locations and condition['effect_location'] in locations,
                    'influence condition location')
            transfer=condition['transfer']
            require(isinstance(transfer,dict),'typed condition transfer')
            if condition['input_location']==condition['effect_location']:
                require(transfer=={'kind':'not_needed'},'same-location condition needs no transfer')
            elif transfer.get('kind')=='unknown':
                require(set(transfer)=={'kind','reason'} and transfer['reason'] and
                        status not in ('applied','included_in_input'),
                        'external/internal correction requires transfer evidence')
                unresolved.append(identity)
            else:
                require(set(transfer)=={'kind','source_id','payload_key'} and transfer['kind']=='source_bound' and
                        transfer['source_id'] in ids,'condition transfer source fields')
                expected={'input_location':condition['input_location'],'effect_location':condition['effect_location'],
                          'coordinate':record['coordinate'],'epoch':record['epoch'],'window':record['window']}
                require(_same_evidence(registry[transfer['source_id']]['payload'].get(transfer['payload_key']),expected),
                        'condition transfer differs from trusted scope')
        materiality=item['materiality'];require(isinstance(materiality,dict),'typed materiality assessment')
        if materiality.get('kind')=='bounded_below_tolerance':
            require(set(materiality)=={'kind','bound','tolerance','unit','source_id','payload_key'} and
                    materiality['unit']==record['unit'] and materiality['source_id'] in ids,
                    'materiality bound/tolerance evidence and common output unit')
            bound,tolerance=exact(materiality['bound']),exact(materiality['tolerance'])
            require(0<=bound<tolerance,'materiality requires nonnegative bound below positive tolerance')
            expected={k:materiality[k] for k in ('bound','tolerance','unit')}
            expected.update(influence_id=identity,coordinate=record['coordinate'],epoch=record['epoch'],window=record['window'])
            require(_same_evidence(registry[materiality['source_id']]['payload'].get(materiality['payload_key']),expected),
                    'materiality bound differs from trusted scope')
            bounded.append(identity)
        else:
            require(materiality.get('kind') in ('retained','unresolved') and
                    set(materiality)=={'kind','reason'} and materiality['reason'],'materiality needs a bound or explicit unresolved/retained reason')
            if materiality['kind']=='unresolved':unresolved.append(identity)
    interpretation=('calibration_anchor_check' if role=='calibration_anchor' else
                    'reference_dependent_comparison' if shared or role=='reference_dependent_evaluation' else
                    'comparison_with_independence_unestablished')
    residual=values['prediction']-values['comparison']
    return {'status':'consistent_declared_comparison_metadata','assessment_sha256':m.digest(declaration),
            'residual':str(residual),'unit':record['unit'],'interpretation':interpretation,
            'anchor_equality':residual==0 if role=='calibration_anchor' else None,
            'shared_source_payload_sha256':shared,'correction_ownership':ownership,
            'unresolved_influences':sorted(set(unresolved)),'bounded_influences':bounded,
            'reflection_to_observation_map_status':'unknown',
            'corrections_applied_by_assessment':False,'finite_distribution_inferred':False,
            'independent_physical_validation':False,'complete_physical_uncertainty':deepcopy(UNKNOWN)}


def comparison_fixture():
    """Declared fixture for comparison metadata, not an atomic measurement."""
    source=m.source('fixture:comparison-values','calibration',{'comparison_quantities':{
        'prediction':{'kind':'oscillator_phase_advance','unit':'Hz','value':'101'},
        'comparison':{'kind':'oscillator_phase_advance','unit':'Hz','value':'100'}}})
    record={'id':'fixture-comparison','source_id':'fixture:comparison-assessment','sources':[source],
            'measurand':'declared observer frequency','kind':'oscillator_phase_advance','unit':'Hz',
            'coordinate':'fixture-cut','epoch':'fixture-origin','window':[0,12],
            'reflection_duration':{'kind':'declared_separate','coordinate':'directional-reflection-duration',
                'value':'8','unit':'duration-count','observation_map':{
                    'kind':'unknown','reason':'No duration-to-observation map supplied'}},
            'prediction':{'value':'101','source_id':source['id'],'quantity_id':'prediction','dependency_ids':[]},
            'comparison':{'value':'100','source_id':source['id'],'quantity_id':'comparison','dependency_ids':[]},
            'reference_role':'reference_dependent_evaluation','influences':[{
                'id':'internal-field','stage':'setup','mechanism':'declared residual field response',
                'source_ids':[source['id']],'correction':{'kind':'included_in_input','value':'-2','unit':'Hz'},
                'residual_uncertainty':{'kind':'unknown','reason':'Residual field uncertainty not supplied'},
                'evaluation_method':'unknown','conditions':{'kind':'specified',
                    'input_location':'internal_apparatus','effect_location':'internal_apparatus',
                    'transfer':{'kind':'not_needed'}},
                'materiality':{'kind':'retained','reason':'Effect retained with unresolved uncertainty'}}]}
    declaration={k:deepcopy(v) for k,v in record.items() if k not in ('source_id','sources')}
    bound=m.source(record['source_id'],'model',{'comparison_assessment':declaration})
    record['sources'].append(bound)
    return record,{s['id']:s for s in record['sources']}


def phase_fixture():
    source=m.source('fixture:phase','model',{'scope':'exact declared phase endpoints; no atomic experiment'})
    def observation(identity,winding,start,end):
        return {'id':identity,'evidence_class':'exact_mathematical_fixture','kind':'oscillator_phase_advance',
            'scope':'declared finite fixture','sources':[source],'preparation':'declared endpoints',
            'apparatus':'mathematical fixture','detector':'identity phase readout','estimator':'signed net winding',
            'coordinate':'fixture-cut','epoch':'fixture-origin','window':[10,22],
            'calibration':{'kind':'declared_fixture'},'corrections':[],'uncertainty':deepcopy(UNKNOWN),
            'selection':'all committed endpoints','winding':winding,'phase_start':start,'phase_end':end,
            'orientation':'forward','unwrapping_convention':'signed_net_winding','source_ids':[source['id']]}
    a=observation('compared',4,'2/3','1/6');b=observation('reference',8,'1/4','3/4')
    source=m.source('fixture:phase','model',{'observations':{r['id']:phase_payload(r) for r in (a,b)}})
    a['sources']=[source];b['sources']=[source]
    realization=m.source('fixture:reference','model',{'reference_id':b['id'],'coordinate':b['coordinate'],
        'epoch':b['epoch'],'window':b['window'],'defining_integer_hz':CS,'physical_correspondence':'declared_fixture'})
    return a,b,{'source':realization,'trusted_sources':{s['id']:s for s in (source,realization)},
                'reference_id':b['id'],'kind':'Cs133_equivalent_reference','physical_correspondence':'declared_fixture'}


def finite_dependency_fixture(expression=None):
    support=[['1/2',{'X':'0'}],['1/2',{'X':'1'}]]
    source=m.source('fixture:joint','model',{'joint_law':{'order':['X'],'support':support}})
    return {'sources':[source],'trusted_sources':{source['id']:source},
        'inputs':{'X':{'source_id':source['id'],'quantity_id':'X','unit':'1','dimension':[0,0,0],
                       'kind':'finite_law','components':[]}},'active':['X'],
        'expression':expression or ['add',['input','X'],['input','X']],
        'parameters':{},'output_dimension':[0,0,0],'support':support,'means':None,'covariance':None}


def ensemble_fixtures():
    support=[['1/4',{'X':'0','Y':'0'}],['1/4',{'X':'0','Y':'2'}],
             ['1/4',{'X':'1','Y':'2'}],['1/4',{'X':'1','Y':'4'}]]
    rows,means,cov=m.joint_moments(support,['X','Y']);conditional=[]
    for x in (Q(0),Q(1)):
        mass=sum(p for p,v in rows if v['X']==x)
        mean=sum(p*v['Y'] for p,v in rows if v['X']==x)/mass
        var=sum(p*(v['Y']-mean)**2 for p,v in rows if v['X']==x)/mass
        conditional.append((mass,mean,var))
    within=sum(p*v for p,mu,v in conditional);between=sum(p*(mu-means['Y'])**2 for p,mu,v in conditional)
    require(within+between==cov[1][1],'total variance identity')
    # Exact finite switching response; local derivative at mean(-1,2)=1/2 is zero.
    threshold=[(Q(1,2),Q(-1)),(Q(1,2),Q(2))]
    mean_y=sum(p*int(x>0) for p,x in threshold)
    variance=sum(p*(int(x>0)-mean_y)**2 for p,x in threshold)
    return {'evidence_class':'exact_mathematical_fixture','atomic_transition_model':False,
        'total_variance':{'within':str(within),'between':str(between),'total':str(cov[1][1])},
        'correlated_window_mean_variance':str(m.quadratic(['1/2','1/2'],[['1/4','1/4'],['1/4','1/4']])),
        'shared_source_residual_variance':str(m.quadratic(['1','-1'],[['1/4','1/4'],['1/4','1/4']])),
        'opposite_source_residual_variance':str(m.quadratic(['1','-1'],[['1/4','-1/4'],['-1/4','1/4']])),
        'threshold':{'support':[{'p':str(p),'input':str(x),'output':int(x>0)} for p,x in threshold],
            'exact_variance':str(variance),'local_linearized_variance':'0','local_approximation_adequate':False}}


def build_report():
    context=t.example_context();prediction=t.predict(context)
    binding=bind_native_prediction(prediction,context)  # freeze/replay before loading H evaluation data
    hydrogen=load_profile('hydrogen');cesium=load_profile('cesium')
    files={'companion_code':Path(__file__),'contract':CONTRACT,
           'native_temporal_code':Path(t.__file__),'generic_mapping_error_code':Path(m.__file__)}
    for p in sorted(DATA.rglob('*')):
        if p.is_file() and p!=REPORT: files['data/'+p.relative_to(DATA).as_posix()]=p
    digests={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in files.items()}
    return {'schema':'aod.m3.temporal-metrology-report.v1','inputs_sha256':digests,
        'phase':compare_accumulations(*phase_fixture()),'native_binding':binding,
        'hydrogen':{key:reduce_hydrogen(hydrogen,key) for key in ('table_iv','table_vi','published_mean')},
        'cesium':{key:reduce_cesium(cesium,key) for key in ('August2013','typical_Table1')},
        'shared_input':validate_error_dependencies(finite_dependency_fixture()),'ensemble':ensemble_fixtures(),
        'comparison_assessment':assess_comparison(*comparison_fixture()),
        'transport':validate_transport_ledger({'window':[0,5],'packets':[
            {'id':'p0','emitted':-1,'arrived':2},{'id':'p1','emitted':3,'arrived':None}],
            'pending_start':1,'pending_end':1}),
        'claim_status':{'exact_fixtures':'supported','printed_input_reductions':'supported',
            'native_model_prediction':'conditional','SI_anchor':'conditional_calibration_identity',
            'physical_prepared_state_assignment':'missing_premise','closure_to_physical_cycle_map':'missing_premise',
            'complete_physical_uncertainty':'missing_premise','independent_atomic_prediction':'not_established',
            'nuclear_dynamics':'not_implemented'},
        'limits':['No universal seconds per bip','No raw experimental phase reconstruction',
                  'No new finite uncertainty law inferred from paper summaries','No independent lifetime or atomic-frequency prediction']}


def report_bytes():
    return (json.dumps(build_report(),sort_keys=True,indent=2,ensure_ascii=True)+'\n').encode()


def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--write-data',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args();payload=report_bytes()
    if args.write_data:
        REPORT.write_bytes(payload);print('temporal metrology report written')
    elif args.check:
        require(REPORT.is_file() and REPORT.read_bytes()==payload,'temporal metrology report differs; explicit regeneration required')
        print('temporal metrology report verified')
    else: print(payload.decode(),end='')


if __name__=='__main__': main()
