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
PRIMARY_SOURCE_BINDINGS = {
    'hydrogen': {'file':'hellwig1970.pdf',
        'sha256':'e8bba435fbb9e6b54f41fa1d60f9c02df8e06b6a73ce8fab323afb3ea7d02dc4',
        'receipt_sha256':'d200cd0d4549bd50586c9d6b8094ee9189857b14888f74309a82c14f5dd40a55'},
    'cesium': {'file':'heavner2014.pdf',
        'sha256':'85482447888dc5524b7ebf3754ea4fdcde3a80d9c36ae927e5d69d9e9f980eb5',
        'receipt_sha256':'12b45da70073d54d0205f2e505b63785bfcb443b59a36b3ddf7746b3f45cbcf8'},
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


def load_primary_receipt(name):
    require(name in PRIMARY_SOURCE_BINDINGS, 'primary source not bound')
    binding=PRIMARY_SOURCE_BINDINGS[name];directory=DATA/name/'source'
    receipt=json.loads((directory/'source_receipt.json').read_text())
    require(m.digest(receipt)==binding['receipt_sha256'], 'primary transcription receipt changed')
    raw=(directory/binding['file']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==binding['sha256']==receipt['sha256']
            and receipt['file']==binding['file'] and len(raw)==receipt['bytes'], 'primary source bytes changed')
    return receipt


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
        declared=registry[item['source_id']]['payload'].get('quantities',{}).get(item['quantity_id'])
        if declared is not None:
            require(all(k in declared and _same_evidence(item[k],declared[k]) for k in ('unit','dimension','kind')),
                    'dependency differs from trusted quantity metadata')
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
    output_dimension=record['output_dimension']
    require(type(output_dimension) is list and len(output_dimension)==3
            and all(type(value) is int for value in output_dimension),
            'output dimension requires three integers excluding bool')
    dimension=m.expression_dimension(record['expression'],inputs,record['parameters'])
    require(list(dimension)==output_dimension,'output dimension mismatch')
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


# External quantities are separate from legacy, caller-typed finite fixtures.
QUANTITY_SCHEMA = 'aod.m3.external-quantity.v1'
PROPAGATION_SCHEMA = 'aod.m3.quantity-propagation.v1'
_UNIT_TYPES = {'1':([0,0,0],Q(1)), 'm':([1,0,0],Q(1)),
    'cm':([1,0,0],Q(1,100)), 'mm':([1,0,0],Q(1,1000)),
    'm^2':([2,0,0],Q(1)), 'm^3':([3,0,0],Q(1)), 'm^4':([4,0,0],Q(1)),
    's':([0,1,0],Q(1)), 'ms':([0,1,0],Q(1,1000)),
    'Hz':([0,-1,0],Q(1)), 'kHz':([0,-1,0],Q(1000)),
    'count':([0,0,1],Q(1)), 'cycle':([0,0,1],Q(1)), 'cycle/s':([0,-1,1],Q(1))}


def _quantity_type(item):
    require(type(item['kind']) is str and item['kind'].strip(), 'quantity kind required')
    require(type(item['dimension']) is list and len(item['dimension'])==3
            and all(type(x) is int for x in item['dimension']), 'quantity dimension requires integers')
    require(item['unit'] in _UNIT_TYPES and item['dimension']==_UNIT_TYPES[item['unit']][0],
            'quantity unit/dimension convention mismatch')


def _trusted_quantity_source(identity, trusted_sources):
    require(isinstance(trusted_sources,dict) and identity in trusted_sources, 'quantity source is not trusted')
    source=trusted_sources[identity]
    require(isinstance(source,dict) and set(source)=={'id','role','payload','sha256'} and isinstance(source['payload'],dict), 'trusted quantity source fields')
    require(source['id']==identity and source['sha256']==m.digest(source['payload']), 'quantity source hash mismatch')
    m.validate_sources([source],trusted_sources)
    return source


def validate_quantity(binding, trusted_sources):
    """Authenticate the exact quantity payload, not caller-agreed unit labels."""
    require(isinstance(binding,dict) and set(binding)=={'schema','source_id','source_sha256','quantity_id','quantity'},
            'external quantity binding fields')
    require(binding['schema']==QUANTITY_SCHEMA, 'external quantity schema')
    no_floats(binding)
    source=_trusted_quantity_source(binding['source_id'],trusted_sources)
    require(binding['source_sha256']==source['sha256'], 'quantity source payload changed')
    require(type(binding['quantity_id']) is str and binding['quantity_id'], 'quantity identity required')
    q=binding['quantity']
    require(isinstance(q,dict) and set(q)=={'kind','unit','dimension','domain','window','locator','role',
            'meaning','value','uncertainty','components','corrections'}, 'quantity payload fields')
    require(_same_evidence(source['payload'].get('quantities',{}).get(binding['quantity_id']),q),
            'quantity differs from trusted quantity payload')
    _quantity_type(q)
    require(q['role']==source['role'], 'quantity source role differs')
    require(all(type(q[k]) is str and q[k].strip() for k in ('locator','meaning')), 'quantity source locator and meaning required')
    require(isinstance(q['domain'],list) and len(q['domain'])==2, 'quantity domain required')
    lo,hi=map(exact,q['domain']);require(lo<=hi, 'ordered quantity domain required')
    if q['value'] is not None: require(lo<=exact(q['value'])<=hi, 'quantity value outside domain')
    if q['window'] is not None:
        w=q['window'];require(isinstance(w,dict) and set(w)=={'coordinate','epoch','bounds'}, 'quantity window fields')
        require(all(type(w[k]) is str and w[k].strip() for k in ('coordinate','epoch')), 'quantity window coordinate and epoch')
        require(isinstance(w['bounds'],list) and len(w['bounds'])==2 and exact(w['bounds'][0])<exact(w['bounds'][1]), 'quantity window bounds')
    require(isinstance(q['components'],list) and len(q['components'])==len(set(q['components']))
            and all(type(x) is str and x for x in q['components']), 'quantity component identities')
    def components(identity, path=()):
        require(identity not in path, 'quantity aggregate dependency cycle')
        declaration=source['payload']['quantities'].get(identity)
        require(isinstance(declaration,dict), 'quantity aggregate component absent from source')
        for child in declaration.get('components',[]): components(child,path+(identity,))
    components(binding['quantity_id'])
    require(isinstance(q['corrections'],dict), 'quantity correction ownership required')
    for name,correction in q['corrections'].items():
        require(type(name) is str and isinstance(correction,dict) and
                set(correction)=={'owner_quantity_id','status','value','unit'}, 'quantity correction fields')
        require(correction['owner_quantity_id']==binding['quantity_id'] and
                correction['status'] in ('included_in_input','not_applied','unknown'), 'quantity correction ownership/status')
        require(correction['unit']==q['unit'], 'quantity correction unit')
        if correction['value'] is not None: exact(correction['value'])
    u=q['uncertainty'];require(isinstance(u,dict) and 'category' in u, 'quantity uncertainty category required')
    require(u['category'] in ('finite_joint_law','moments','standard_uncertainty','expanded_uncertainty',
                            'bound','exact_definition','unknown'), 'unsupported quantity uncertainty category')
    if u['category'] in ('standard_uncertainty','expanded_uncertainty'):
        require('value' in u and exact(u['value'])>=0, 'reported uncertainty value required')
        require(type(u.get('printed_token')) is str and u['printed_token'], 'printed uncertainty token required')
        if u['category']=='expanded_uncertainty':
            require('coverage_factor' in u and 'coverage_information' in u, 'expanded coverage information required')
            if u['coverage_factor'] is not None: require(exact(u['coverage_factor'])>0, 'positive supplied coverage factor required')
    if u['category']=='bound':
        require(isinstance(u.get('interval'),list) and len(u['interval'])==2, 'source bound interval required')
        a,b=map(exact,u['interval']);require(lo<=a<=b<=hi, 'source bound outside quantity domain')
        if q['value'] is not None: require(a<=exact(q['value'])<=b, 'source nominal lies outside its bound')
    if u['category']=='unknown':
        require(type(u.get('reason')) is str and u['reason'].strip(), 'unknown uncertainty needs a reason')
        require(not set(u)&{'value','variance','interval','standard_uncertainty'}, 'unknown uncertainty cannot carry a numerical contribution')
    if u['category']=='exact_definition':
        require(q['value'] is not None, 'exact definition value required')
        require(not set(u)&{'value','variance','interval','standard_uncertainty'}, 'exact definition cannot carry contradictory uncertainty')
    return deepcopy(q)


def _quantity_descendants(binding, trusted_sources):
    declarations=trusted_sources[binding['source_id']]['payload']['quantities']
    def descendants(identity):
        children=declarations[identity]['components']
        return set(children).union(*(descendants(child) for child in children))
    return descendants(binding['quantity_id'])


def _input_identity(binding):
    return {'source_sha256':binding['source_sha256'],'quantity_id':binding['quantity_id']}


def _exact_covariance(matrix):
    require(isinstance(matrix,list) and matrix and all(isinstance(row,list) for row in matrix), 'complete exact covariance required')
    for row in matrix:
        for value in row: exact(value)
    return m.validate_psd(matrix)


def _expression_interval(expr, intervals, parameters):
    op=expr[0]
    if op=='input': return tuple(map(exact,intervals[expr[1]]))
    if op=='parameter':
        value=exact(parameters[expr[1]]['value']);return value,value
    a,b=_expression_interval(expr[1],intervals,parameters);c,d=_expression_interval(expr[2],intervals,parameters)
    if op=='add': return a+c,b+d
    if op=='sub': return a-d,b-c
    if op=='mul':
        values=[a*c,a*d,b*c,b*d];return min(values),max(values)
    result=m.ratio_bounds([str(a),str(b)],[str(c),str(d)])
    require(result['status']=='bounded', 'denominator domain contains zero; output is undefined or unbounded')
    return tuple(map(exact,result['bounds']))



def _expression_unit_scale(expr, inputs, parameters):
    op=expr[0]
    if op in ('input','parameter'):
        return _UNIT_TYPES[(inputs if op=='input' else parameters)[expr[1]]['unit']][1]
    left=_expression_unit_scale(expr[1],inputs,parameters)
    right=_expression_unit_scale(expr[2],inputs,parameters)
    if op in ('add','sub'):
        require(left==right, 'mixed coordinate units require explicit conversion')
        return left
    return left*right if op=='mul' else left/right


def _quantity_budget(result, output, contributing, quantities, stage):
    unit=output['unit']
    def component(kind,reason,**fields): return {'kind':kind,'unit':unit,'reason':reason,**fields}
    budget={
        'arithmetic':component('exact','Exact rational evaluation of supplied quantities',value='0',included_sources={}),
        'resolution':component('unknown','No additional input/report resolution model supplied',included_sources={}),
        'window':component('unknown','No physical window contribution established',included_sources={}),
        'model_discrepancy':component('unknown','Conditional propagation does not quantify physical discrepancy',included_sources={}),
        'calibration':component('included_in_propagation','Calibration input uncertainty is counted in the joint input model',
            included_sources={k:v for k,v in contributing.items() if quantities[k]['role']=='calibration'}),
        'solver':component('not_applicable','No approximate solver used',included_sources={}),
        'comparison':component('unknown' if stage=='comparison' else 'not_applicable',
            'Joint comparison propagation retains supplied dependence; external adequacy remains unresolved' if stage=='comparison' else 'Prediction product before comparison',included_sources={})}
    propagation=component('unknown','Supplied metadata do not determine output uncertainty',included_sources=contributing)
    if result.get('output_variance') is not None:
        propagation.update(kind='variance',reason=result['uncertainty_status'],variance=result['output_variance'],
            variance_unit={'base_unit':unit,'power':2},variance_dimension=[2*x for x in output['dimension']],
            standard_deviation={'representation':'symbolic_square_root','radicand':result['output_variance'],'unit':unit})
    if result.get('output_bounds') is not None:
        propagation.update(kind='bound',reason='Conditional interval enclosure; dependence is not replaced by independence',
            interval=result['output_bounds'])
    budget['propagation']=propagation
    calibration=budget['calibration']
    if not calibration['included_sources']:
        calibration.update(kind='not_applicable',reason='No calibration-role input contributes to this output')
    elif propagation['kind']=='unknown':
        calibration.update(kind='unknown',reason='Calibration input retained; its output uncertainty remains unresolved')
    return budget


def propagate_quantities(record, trusted_sources):
    """Dispatch an authenticated uncertainty model through the existing exact calculus.

    The supplied trust store is an input, never synthesized from a caller record.
    Conditional moment or interval evidence is not experimental validation.
    """
    require(isinstance(record,dict) and set(record)=={'schema','stage','inputs','parameters','model_source_id','model_id','model'},
            'quantity propagation record fields')
    require(record['schema']==PROPAGATION_SCHEMA and record['stage'] in ('prediction','comparison'), 'quantity propagation schema/stage')
    no_floats(record)
    model=record['model'];source=_trusted_quantity_source(record['model_source_id'],trusted_sources)
    require(source['role'] in ('model','calibration'), 'propagation model source role')
    require(_same_evidence(source['payload'].get('uncertainty_models',{}).get(record['model_id']),model),
            'uncertainty model differs from trusted source')
    require(set(model)=={'method','input_order','input_bindings','parameter_bindings','outputs','support','means',
            'covariance','bounds','interpretation'}, 'uncertainty model fields')
    require(type(model['interpretation']) is str and model['interpretation'].strip(), 'model interpretation required')
    inputs=record['inputs'];require(isinstance(inputs,dict) and inputs, 'quantity inputs required')
    order=model['input_order'];require(isinstance(order,list) and len(order)==len(set(order)) and set(order)==set(inputs), 'complete input order required')
    quantities={name:validate_quantity(binding,trusted_sources) for name,binding in inputs.items()}
    require(_same_evidence(model['input_bindings'],{name:_input_identity(b) for name,b in inputs.items()}), 'model input source bindings differ')
    seen=set()
    for name,binding in inputs.items():
        identity=(binding['source_sha256'],binding['quantity_id'])
        require(identity not in seen, 'same quantity duplicated under payload aliases');seen.add(identity)
        if record['stage']=='prediction': require(quantities[name]['role']!='evaluation', 'evaluation quantity cannot enter prediction')
        for component in _quantity_descendants(binding,trusted_sources):
            require((binding['source_sha256'],component) not in {(b['source_sha256'],b['quantity_id']) for b in inputs.values()},
                    'aggregate and own components counted together')
    parameters={name:validate_quantity(binding,trusted_sources) for name,binding in record['parameters'].items()}
    require(_same_evidence(model['parameter_bindings'],{name:_input_identity(b) for name,b in record['parameters'].items()}), 'model parameter source bindings differ')
    for name,q in parameters.items():
        require(q['uncertainty']['category']=='exact_definition' and q['role']!='evaluation',
                'uncertain parameters must enter as propagated input quantities')
    method=model['method'];require(method in ('finite_joint_law','moments','bounds','metadata'), 'unsupported uncertainty route')
    categories={q['uncertainty']['category'] for q in quantities.values()}
    if method=='finite_joint_law':
        require(categories<= {'finite_joint_law','exact_definition'}, 'source category cannot be fabricated into a finite law')
        require(model['support'] is not None and model['bounds'] is None, 'finite law support required')
        _exact_support(model['support']);rows,means,cov=m.joint_moments(model['support'],order)
        if model['means'] is not None:
            require({n:exact(v) for n,v in model['means'].items()}==means, 'means disagree with joint law')
        if model['covariance'] is not None:
            require(_exact_covariance(model['covariance'])==cov, 'covariance disagrees with joint law')
        for p,point in rows:
            require(all(exact(quantities[n]['domain'][0])<=point[n]<=exact(quantities[n]['domain'][1]) for n in order), 'finite support outside quantity domain')
            require(all(quantities[n]['uncertainty']['category']!='exact_definition' or point[n]==exact(quantities[n]['value']) for n in order), 'exact definition varies in finite law')
    elif method=='moments':
        require(model['support'] is None and model['bounds'] is None and model['means'] is not None
                and model['covariance'] is not None, 'moments require means and complete covariance without fabricated support')
        require(categories<= {'moments','standard_uncertainty','expanded_uncertainty','exact_definition'}, 'source category cannot supply moments')
        require(set(model['means'])==set(order), 'moment coordinates differ')
        means={n:exact(model['means'][n]) for n in order};cov=_exact_covariance(model['covariance'])
        require(len(cov)==len(order), 'complete covariance dimensions')
        for i,n in enumerate(order):
            q=quantities[n];u=q['uncertainty'];require(exact(q['domain'][0])<=means[n]<=exact(q['domain'][1]), 'mean outside quantity domain')
            if q['value'] is not None: require(means[n]==exact(q['value']), 'mean differs from source quantity value')
            lo,hi=map(exact,q['domain'])
            require(cov[i][i]<=(hi-means[n])*(means[n]-lo), 'variance incompatible with bounded input domain')
            if u['category']=='standard_uncertainty': require(cov[i][i]==exact(u['value'])**2, 'covariance disagrees with source standard uncertainty')
            if u['category']=='expanded_uncertainty':
                require(u['coverage_factor'] is not None, 'expanded uncertainty lacks supplied coverage factor')
                require(cov[i][i]==(exact(u['value'])/exact(u['coverage_factor']))**2, 'covariance disagrees with supplied expanded uncertainty')
            if u['category']=='exact_definition': require(cov[i][i]==0, 'exact definition has nonzero variance')
    elif method=='bounds':
        require(categories<= {'bound','exact_definition'} and model['support'] is None and model['means'] is None
                and model['covariance'] is None and set(model['bounds'] or {})==set(order), 'bounds require source intervals without a probability model')
        for n,q in quantities.items():
            expected=q['uncertainty']['interval'] if q['uncertainty']['category']=='bound' else [q['value'],q['value']]
            require(_same_evidence(model['bounds'][n],expected), 'input bounds differ from source interval')
    else:
        require(all(model[k] is None for k in ('support','means','covariance','bounds')), 'metadata route cannot fabricate an uncertainty model')
    outputs=model['outputs'];require(isinstance(outputs,dict) and outputs, 'output definitions required')
    require(set().union(*(m.expression_refs(o['expression'],'input') for o in outputs.values()))==set(order), 'applicable input contribution omitted')
    require(set().union(*(m.expression_refs(o['expression'],'parameter') for o in outputs.values()))==set(parameters), 'parameter declaration/use differs')
    result_outputs={};gradients={};atoms={}
    for name,out in outputs.items():
        require(set(out)=={'kind','unit','dimension','domain','expression','conversion'}, 'output quantity fields')
        _quantity_type(out);expr=out['expression']
        require(list(m.expression_dimension(expr,quantities,parameters))==out['dimension'], 'output expression dimension mismatch')
        used=m.expression_refs(expr,'input')
        # A different coordinate unit needs the explicit scale, not a changed label.
        conversion=out['conversion']
        if conversion is not None:
            require(set(conversion)=={'input','parameter','from_unit','to_unit'}, 'conversion fields')
            n,p=conversion['input'],conversion['parameter']
            require(n in quantities and p in parameters and quantities[n]['unit']==conversion['from_unit']
                    and out['unit']==conversion['to_unit'], 'conversion quantity units differ')
            require(out['dimension']==quantities[n]['dimension'] and parameters[p]['dimension']==[0,0,0], 'conversion dimensions differ')
            require(exact(parameters[p]['value'])==_UNIT_TYPES[conversion['from_unit']][1]/_UNIT_TYPES[conversion['to_unit']][1], 'conversion scale differs from unit convention')
            require(expr==['mul',['input',n],['parameter',p]], 'conversion law must execute its declared scale')
        else:
            require(_expression_unit_scale(expr,quantities,parameters)==_UNIT_TYPES[out['unit']][1], 'unit change requires explicit conversion')
            require(not any(quantities[n]['dimension']==out['dimension'] and quantities[n]['unit']!=out['unit'] for n in used), 'unit change requires explicit conversion')
        suborder=[n for n in order if n in used]
        if not suborder:
            value=m.evaluate(expr,{},parameters)
            r={'nominal':str(value),'output_mean':str(value),'output_variance':'0',
               'uncertainty_status':'exact_for_constant_map','arithmetic':'exact rational'}
            if method=='finite_joint_law': atoms[name]=[value for _ in rows]
            elif method=='moments': gradients[name]=[Q(0) for _ in order]
            if method=='bounds': r['output_bounds']=[str(value),str(value)]
        elif method in ('finite_joint_law','moments'):
            subset_cov=[[str(cov[order.index(i)][order.index(j)]) for j in suborder] for i in suborder]
            support=None if method=='moments' else [[str(p),{n:str(point[n]) for n in suborder}] for p,point in rows]
            r=m.propagate(expr,suborder,parameters,{n:str(means[n]) for n in suborder},subset_cov,support)
            if method=='finite_joint_law': atoms[name]=[m.evaluate(expr,point,parameters) for p,point in rows]
            elif m.affine(expr): gradients[name]=m.gradient(expr,means,parameters,order)
        elif method=='bounds':
            low,high=_expression_interval(expr,model['bounds'],parameters)
            r={'output_mean':None,'output_variance':None,'output_bounds':[str(low),str(high)],
                'uncertainty_status':'conditional_interval_enclosure','arithmetic':'exact rational',
                'scope':'Supplied source intervals; no probability distribution inferred'}
        else:
            r={'output_mean':None,'output_variance':None,'uncertainty_status':'partial',
                'reason':'Measurement retained; category, covariance or transformation is insufficient'}
            if all(quantities[n]['value'] is not None for n in used):
                r['nominal']=str(m.evaluate(expr,{n:quantities[n]['value'] for n in used},parameters))
        if out['domain'] is not None:
            require(isinstance(out['domain'],list) and len(out['domain'])==2, 'output domain fields')
            lo,hi=map(exact,out['domain']);require(lo<=hi, 'ordered output domain required')
            if method=='finite_joint_law': image=min(atoms[name]),max(atoms[name])
            elif method=='bounds': image=tuple(map(exact,r['output_bounds']))
            else:
                image=_expression_interval(expr,{n:quantities[n]['domain'] for n in used},parameters)
            require(lo<=image[0]<=image[1]<=hi, 'output image leaves declared domain')
        contributing={n:_input_identity(inputs[n]) for n in suborder}
        result_outputs[name]={'kind':out['kind'],'unit':out['unit'],'dimension':out['dimension'],'domain':out['domain'],'result':r,
            'budget':_quantity_budget(r,out,contributing,quantities,record['stage']),
            'parameter_bindings':{p:_input_identity(record['parameters'][p]) for p in m.expression_refs(expr,'parameter')}}
    names=list(outputs);output_covariance=None
    if method=='finite_joint_law':
        averages={n:sum(p*y for (p,_),y in zip(rows,atoms[n])) for n in names}
        output_covariance=[[str(sum(p*(a-averages[i])*(b-averages[j]) for (p,_),a,b in zip(rows,atoms[i],atoms[j]))) for j in names] for i in names]
    elif method=='moments' and len(gradients)==len(outputs):
        output_covariance=[[str(sum(gradients[i][a]*cov[a][b]*gradients[j][b] for a in range(len(order)) for b in range(len(order)))) for j in names] for i in names]
    return {'schema':'aod.m3.quantity-propagation-result.v1',
        'status':'partial' if any(v['result']['output_variance'] is None and v['result'].get('output_bounds') is None for v in result_outputs.values()) else 'conditional',
        'method':method,'stage':record['stage'],'interpretation':model['interpretation'],
        'inputs':deepcopy(quantities),'outputs':result_outputs,'output_order':names,'output_covariance':output_covariance,
        'covariance_units':[[{'left':outputs[i]['unit'],'right':outputs[j]['unit']} for j in names] for i in names],
        'source_bindings':deepcopy(model['input_bindings']),'parameter_bindings':deepcopy(model['parameter_bindings']),
        'model_binding':{'source_id':source['id'],'source_sha256':source['sha256'],'model_id':record['model_id']},
        'physical_model_discrepancy':deepcopy(UNKNOWN)}


def quantity_input_fixture(route='finite_joint_law'):
    """Small declared inputs for the common dispatcher; no experimental model inferred."""
    def quantity(category='finite_joint_law',unit='1',dimension=None,value='0',**uncertainty):
        return {'kind':'reported_scalar','unit':unit,'dimension':dimension or [0,0,0],'domain':['-100','100'],
            'window':None,'locator':'declared fixture X','role':'model','meaning':'Declared scalar model input',
            'value':value,'uncertainty':{'category':category,**uncertainty},'components':[],'corrections':{}}
    q=quantity();parameter_quantities={};expr=['mul',['input','X'],['input','X']]
    method='finite_joint_law';support=[['1/2',{'X':'-1'}],['1/2',{'X':'1'}]];means=None;covariance=None;bounds=None
    outputs={'Y':{'kind':'reported_scalar','unit':'1','dimension':[0,0,0],'domain':None,'expression':expr,'conversion':None}}
    if route in ('moments','nonlinear_moments','shared_cancel','shared_reinforce','multi_output'):
        method='moments';support=None;means={'X':'0'};covariance=[['2']];q=quantity('moments')
        if route!='nonlinear_moments': outputs['Y']['expression']=['input','X']
        if route.startswith('shared_'):
            outputs['A']=deepcopy(outputs.pop('Y'));outputs['E']=deepcopy(outputs['A'])
            if route=='shared_reinforce':
                parameter_quantities['minus_one']=quantity('exact_definition',value='-1')
                outputs['E']['expression']=['mul',['input','X'],['parameter','minus_one']]
            outputs['residual']={**deepcopy(outputs['A']),'expression':['sub',deepcopy(outputs['A']['expression']),deepcopy(outputs['E']['expression'])]}
        if route=='multi_output':
            parameter_quantities['frequency']=quantity('exact_definition',unit='Hz',dimension=[0,-1,0],value='2')
            parameter_quantities['duration']=quantity('exact_definition',unit='s',dimension=[0,1,0],value='3')
            outputs={name:{'kind':'reported_scalar','unit':unit,'dimension':dimension,'domain':None,
                'expression':['mul',['input','X'],['parameter',name]],'conversion':None}
                for name,unit,dimension in [('frequency','Hz',[0,-1,0]),('duration','s',[0,1,0])]}
    elif route=='bounds':
        method='bounds';support=None;q=quantity('bound',value='2',interval=['1','3']);bounds={'X':['1','3']}
        parameter_quantities['one']=quantity('exact_definition',value='1')
        outputs['Y']['expression']=['div',['parameter','one'],['input','X']]
    elif route=='metadata':
        method='metadata';support=None;q=quantity('expanded_uncertainty',value='2')
        q['uncertainty']={'category':'expanded_uncertainty','value':'1','printed_token':'±1','coverage_factor':None,'coverage_information':'not supplied'}
        outputs['Y']['expression']=['input','X']
    elif route=='conversion':
        method='moments';support=None;means={'X':'2'};covariance=[['1/4']]
        q=quantity('standard_uncertainty',unit='m',dimension=[1,0,0],value='2',printed_token='0.5')
        q['uncertainty']['value']='1/2'
        parameter_quantities['scale']=quantity('exact_definition',value='100')
        outputs['Y'].update(unit='cm',dimension=[1,0,0],domain=['-10000','10000'],expression=['mul',['input','X'],['parameter','scale']],
            conversion={'input':'X','parameter':'scale','from_unit':'m','to_unit':'cm'})
    elif route in ('published','published_moments'):
        method='metadata';support=None
        reduced=reduce_hydrogen(load_profile('hydrogen'),'table_vi');primary=load_primary_receipt('hydrogen')
        q=quantity('standard_uncertainty',unit='Hz',dimension=[0,-1,0],value=reduced['corrected_frequency_hz'])
        q.update(domain=['0','2000000000'],role='calibration',locator='Hellwig et al., Table VI; bound hydrogen protocol',
                 meaning='Printed-input hydrogen maser reduction with corrections already included')
        u=reduced['source_reported_uncertainty'];q['uncertainty']={'category':'standard_uncertainty',
            'value':str(printed(u['reported_value_or_bound'])),'printed_token':u['reported_value_or_bound'],
            'source_profile_sha256':reduced['profile_sha256'],
            'primary_source_sha256':primary['sha256'],'primary_receipt_sha256':m.digest(primary),'covariance_status':'complete source component covariance not supplied'}
        q['corrections']={name:{'owner_quantity_id':'X','status':'included_in_input','value':None,'unit':'Hz'}
                          for name in reduced['correction_ownership']['already_in_input']}
        if route=='published_moments':
            aggregate=primary['transcription']['p200_abstract']
            q.update(value=str(printed(aggregate['mean_frequency_hz'])),corrections={},
                locator='Hellwig et al., p200 abstract and p207 conclusion',
                meaning='Published combined estimate treated as the conditional input mean')
            q['uncertainty'].update(value=str(printed(aggregate['one_sigma_uncertainty_hz'])),
                printed_token=aggregate['one_sigma_uncertainty_hz'],
                covariance_status='One published aggregate standard uncertainty; no component independence inferred',
                shared_reference=aggregate['shared_reference'])
            method='moments';means={'X':q['value']};covariance=[[str(printed(aggregate['one_sigma_uncertainty_hz'])**2)]]
        outputs['Y'].update(unit='Hz',dimension=[0,-1,0],expression=['input','X'])
    else: require(route=='finite_joint_law','unknown quantity fixture route')
    source=m.source('fixture:quantity:'+route,q['role'],{'quantities':{'X':q,**parameter_quantities}})
    def bind(name):
        return {'schema':QUANTITY_SCHEMA,'source_id':source['id'],'source_sha256':source['sha256'],
                'quantity_id':name,'quantity':deepcopy(source['payload']['quantities'][name])}
    inputs={'X':bind('X')};parameters={n:bind(n) for n in parameter_quantities}
    model={'method':method,'input_order':['X'],'input_bindings':{n:_input_identity(b) for n,b in inputs.items()},
        'parameter_bindings':{n:_input_identity(b) for n,b in parameters.items()},'outputs':outputs,
        'support':support,'means':means,'covariance':covariance,'bounds':bounds,
        'interpretation':'Conditional declared input model; exact arithmetic is separate from physical uncertainty'}
    model_source=m.source('fixture:uncertainty:'+route,'model',{'uncertainty_models':{'worked':deepcopy(model)}})
    record={'schema':PROPAGATION_SCHEMA,'stage':'prediction','inputs':inputs,'parameters':parameters,
            'model_source_id':model_source['id'],'model_id':'worked','model':model}
    return record,{s['id']:s for s in (source,model_source)}


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
        'primary_sources':{name:load_primary_receipt(name) for name in PRIMARY_SOURCE_BINDINGS},
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
