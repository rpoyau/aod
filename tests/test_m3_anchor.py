"""Native anchor contexts, frozen transfer and independent replay regressions."""
from copy import deepcopy
from dataclasses import asdict, replace
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'manual/scripts'))
import aod_m3_anchor as a


class AnchorEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=json.loads((ROOT/a.DATA/'inputs.json').read_text())
        cls.cases={name:json.loads(gzip.decompress((ROOT/a.DATA/'cases'/f'{name}.json.gz').read_bytes()))
                   for name in a.CASES}

    def test_original_archive_and_all_member_bindings(self):
        verified=a.verify_archive(ROOT)
        self.assertEqual(verified['manifest_members'],80)
        self.assertEqual(verified['input_bindings'],65)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)/a.DATA;folder.mkdir(parents=True)
            data=bytearray((ROOT/a.DATA/'original_anchor_r02.zip').read_bytes());data[128]^=1
            (folder/'original_anchor_r02.zip').write_bytes(data)
            with self.assertRaisesRegex(ValueError,'archive changed'):
                a.verify_archive(Path(directory))

    def test_unmodified_original_controls_replay_exactly(self):
        result=a.original_replay(ROOT)
        self.assertEqual(result['checks'],33)
        self.assertEqual(len(result['output_sha256']),5)
        self.assertEqual(result['direct_pair_residuals'],{'A':'-5/29','B':'-49/151'})

    def test_new_baseline_conserves_original_four_native_histories(self):
        with zipfile.ZipFile(ROOT/a.DATA/'original_anchor_r02.zip') as archive:
            original=json.loads(gzip.decompress(archive.read('baseline/input/results/direct_pair.histories.json.gz')))
        actual=self.cases['baseline']['complete_execution']['waves']
        for name in ('A','B','F0','F1'):
            self.assertEqual(actual[name],original[name])

    def test_distinct_support_pairs_have_distinct_constructions(self):
        expected={'baseline':('3:3','1:2'), 'second_support_pair':('3:2','3:3')}
        signatures=[]
        for case,motifs in expected.items():
            waves=self.cases[case]['complete_execution']['waves']
            self.assertEqual(tuple(waves[name]['motif'] for name in ('A','B')),motifs)
            signatures.append(tuple(waves[name]['motif_witnesses'][0]['witness_digest'] for name in ('A','B')))
        self.assertNotEqual(*signatures)

    def test_recurring_backgrounds_are_retained_in_every_case(self):
        for case in self.cases.values():
            for name in ('F0','F1'):
                self.assertEqual(case['complete_execution']['waves'][name]['motif'],'3:4')
                self.assertGreater(case['training_counts'][name],1)
                self.assertGreater(case['validation_counts'][name],1)

    def test_separate_interventions_preserve_actual_committed_prefix(self):
        base=self.cases['baseline']['complete_execution']
        def before(payload):
            return [event for event in payload['events'] if event[0]<a.INTERVENTION]
        for case,target in (('compared_population','A'),('reference_exposure','F0')):
            payload=self.cases[case]['complete_execution']
            self.assertEqual(before(payload),before(base))
            new_edges=set(payload['channels'])-set(base['channels'])
            self.assertEqual(new_edges,{target+'|L0','L0|'+target})
            self.assertNotEqual(payload['waves'][target]['returns'],base['waves'][target]['returns'])

    def test_gain_uses_training_only_and_is_frozen(self):
        case=self.cases['baseline']
        self.assertEqual(case['training_counts']['A'],58)
        self.assertEqual(case['validation_counts']['A'],48)
        for name in ('A','B','F1'):
            gain=case['frozen_count_transfer'][name]
            expected=Q(case['training_counts']['F0'],case['training_counts'][name])
            self.assertEqual(Q(gain['reference_bips_per_closure']),expected)
            predicted=case['count_transfer_predictions'][name]
            self.assertEqual(Q(predicted['predicted_reference_bips']),expected*case['validation_counts'][name])
        self.assertEqual(a.evaluate_transfer(case['count_transfer_predictions']['A'],32)['relative_residual'],'-5/29')
        self.assertEqual(a.evaluate_transfer(case['count_transfer_predictions']['B'],32)['relative_residual'],'-49/151')

    def test_baseline_frozen_gain_is_not_refitted_for_changed_contexts(self):
        report=json.loads((ROOT/a.DATA/'report.json').read_text())
        baseline=report['frozen_baseline_count_transfer']['A']
        for name in ('compared_population','reference_exposure'):
            row=report['cases'][name]['baseline_frozen_gain_diagnostic']['A']
            prediction=row['prediction']
            self.assertEqual(prediction['frozen_sha256'],a.digest(baseline))
            self.assertEqual(Q(prediction['predicted_reference_bips']),
                             Q(baseline['reference_bips_per_closure'])*self.cases[name]['validation_counts']['A'])
            self.assertIn('not certified',row['applicability'])

    def test_endpoint_bounds_recompute_from_retained_returns(self):
        for case in self.cases.values():
            diagnostics=case['diagnostics'];waves=case['complete_execution']['waves']
            for row in diagnostics['endpoint_variants']:
                lo,hi=row['window']
                for name,wave in waves.items():
                    count=sum(lo<tr['indices'][-1]<=hi for tr in wave['returns'][1:])
                    self.assertEqual(row['counts'][name],count)
                    self.assertLessEqual(abs(count-diagnostics['endpoint_base_counts'][name]),diagnostics['endpoint_event_bounds'][name])

    def test_directional_duration_uses_actual_reflected_contacts(self):
        case=self.cases['baseline'];directions=case['directional_comparisons']
        values=[]
        for key in ('A|F0','F0|A','A|B','B|A'):
            events=case['complete_execution']['channels'][key]['contacts']
            selected=[event for event in events if a.SPLIT<=event['committed']<=a.HORIZON]
            receiver,sender=key.split('|')
            wave=case['complete_execution']['waves'][sender]
            support=a.n.rd(*map(int,wave['motif'].split(':')))
            expected=support+sum(event['reflection'][0] for event in selected)
            self.assertEqual(int(directions[key]['forward']['duration']),expected)
            values.append(expected)
        self.assertNotEqual(values[0],values[1])

    def test_pending_return_is_retained_and_excluded_before_arrival(self):
        case=self.cases['baseline'];diagnostic=case['diagnostics']['reflection_and_pending']
        packet=diagnostic['packet'];cut=diagnostic['cut']
        self.assertLess(packet['emitted'],cut);self.assertLess(cut,packet['arrives'])
        self.assertGreater(packet['reflection'][0],0)
        contacts=case['complete_execution']['channels'][packet['receiver']+'|'+packet['sender']]['contacts']
        self.assertNotIn(packet['id'],{event['identity'] for event in contacts if event['committed']<=cut})
        self.assertIn(packet['id'],{event['identity'] for event in contacts})
        self.assertFalse(diagnostic['admitted_at_cut'])

    def test_duplicate_reference_names_do_not_certify_independence(self):
        waves=self.cases['baseline']['complete_execution']['waves']
        left,right=([tr['indices'][-1] for tr in waves[name]['returns'][1:]] for name in ('F0','F1'))
        self.assertNotEqual(waves['F0']['identity'],waves['F1']['identity'])
        self.assertEqual(left,right)
        result=a.reference_independence(left,right,['shared:Cs'],['shared:Cs'])
        self.assertFalse(result['independent_evidence'])
        self.assertTrue(result['identical_endpoint_histories'])
        self.assertEqual(result['shared_source_ids'],['shared:Cs'])

    def test_target_only_changes_preserve_complete_prediction_bytes(self):
        case=self.cases['baseline'];before=a.canonical(case)
        prediction=case['count_transfer_predictions']['A']
        left=a.evaluate_transfer(prediction,32);right=a.evaluate_transfer(prediction,33)
        self.assertNotEqual(left,right)
        self.assertEqual(a.canonical(case),before)
        with self.assertRaises(ValueError):a.evaluate_transfer(prediction,True)

    def test_physical_unknowns_and_per_output_units_are_preserved(self):
        for case in self.cases.values():
            self.assertIsNone(case['physical_tolerance'])
            self.assertIsNone(case['complete_physical_standard_uncertainty'])
            for prediction in case['temporal_predictions'].values():
                contract=prediction['mapping_contract']
                for name,unit in (('elapsed_seconds','s'),('average_rate_hz','Hz')):
                    budget=contract['error'][name]
                    self.assertEqual(len(budget),8)
                    self.assertTrue(all(component['unit']==unit for component in budget.values()))
                    for component in ('model_discrepancy','calibration','window'):
                        self.assertEqual(budget[component]['kind'],'unknown')

    def test_original_input_changes_cannot_be_resealed(self):
        altered=deepcopy(self.inputs)
        altered['cases']['reference_exposure']['local_target']='A'
        altered['code_sha256']=a.sha(Path(a.__file__))
        with self.assertRaisesRegex(ValueError,'frozen construction'):
            a.validate_inputs(altered)

    def test_recomputed_hash_does_not_authorize_replaced_history(self):
        altered=deepcopy(self.cases['baseline'])
        altered['complete_execution']['preparation_override']='different preparation'
        altered['original_inputs_sha256']=a.digest(self.inputs)
        self.assertNotEqual(a.digest(altered),a.digest(self.cases['baseline']))
        with self.assertRaisesRegex(ValueError,'original-context replay'):
            a.evaluate_case(altered,32,original_inputs=self.inputs,case='baseline')


class AnchorAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=a.source_modules(ROOT)
        cls.modules,_=cls.source.__enter__()
        cls.inputs=a.default_inputs()
        cls.engine=a.run_engine(cls.inputs['cases']['baseline'],cls.modules)
        cls.context=a.observation_context(cls.engine,cls.inputs,'baseline',(a.SPLIT,a.HORIZON))

    @classmethod
    def tearDownClass(cls):
        cls.source.__exit__(None,None,None)

    def test_actual_population_and_previous_lag_admit(self):
        record=a.t.validate_observation_context(self.context)
        self.assertEqual(record['counts'],{'compared':48,'reference':32})
        self.assertEqual(Q(record['forward']['drift']),Q(16))

    def test_missing_cross_return_cannot_be_forged_by_count_projection(self):
        projection=a.diagnostics(self.engine)['unsupported_short_projection']
        self.assertLess(projection['returned_contacts'],2)
        record=a.native_input(self.engine,'A','F0',projection['window'])
        with self.assertRaisesRegex(ValueError,'contacts'):
            a.t.adapt(record)

    def test_changed_direction_and_reflection_witness_fail_admission(self):
        record=self.context.record
        first=record.contacts[0]
        wrong=replace(first,left=first.right,right=first.left)
        with self.assertRaisesRegex(ValueError,'lineage'):
            a.t.adapt(replace(record,contacts=(wrong,*record.contacts[1:])))
        broken_trace=replace(first.support_trace,reflection=None)
        broken=replace(first,support_trace=broken_trace)
        with self.assertRaises(ValueError):
            a.t.adapt(replace(record,contacts=(broken,*record.contacts[1:])))

    def test_population_preparation_and_pending_mutations_fail(self):
        with self.assertRaisesRegex(ValueError,'population'):
            a.t.validate_observation_context(replace(self.context,population=self.context.population[1:]))
        changed=deepcopy(self.context.preparation);changed['parameters']['intervention_cut']+=1
        with self.assertRaisesRegex(ValueError,'applicability'):
            a.t.validate_observation_context(replace(self.context,preparation=changed))
        pending=list(deepcopy(self.context.pending))
        self.assertTrue(pending)
        pending[0]['prefix_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'pending prefix'):
            a.t.validate_observation_context(replace(self.context,pending=tuple(pending)))


if __name__=='__main__':unittest.main()
