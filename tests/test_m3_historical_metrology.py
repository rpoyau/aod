"""Original MAP-21/22 identity, exact laws and hostile replay controls."""
from contextlib import redirect_stdout
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('historical_mapping', ROOT/'manual/scripts/aod_mapping_error.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class HistoricalMetrologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m.report()
        cls.cases = cls.report['original_historical_laws']['cases']

    def fixture(self, criterion):
        return deepcopy(self.cases[criterion]['law'])

    def test_HMAP_01_authenticated_probe_archive_and_dependency_inventory(self):
        b = m.historical_sources()
        self.assertEqual(b['probe']['bytes'], 6837)
        self.assertEqual(b['probe']['sha256'], '685f4b2b077d2cde88f2e275800e088d156ed006aa82b648608743d3b670582e')
        self.assertEqual([a['entries_verified'] for a in b['archive_provenance']], [21,29,38])
        self.assertEqual(len(b['historical_target_files']), 5)
        self.assertEqual(m.historical_parameters(), {'a':Q(1,1000),'eps':Q(1,1000),'delta':Q(1,1000000)})

    def test_HMAP_02_actual_original_output_and_legacy_failure_replay(self):
        result = m.replay_historical_probe()
        self.assertEqual(result['status'], 'original_output_byte_identical')
        self.assertEqual(result['legacy_complete_claim_negative_control'], 'rejected_as_expected')
        original = json.loads((m.HISTORICAL/'original-output.json').read_text())
        self.assertTrue(original['R1a_interval']['unsafe_complete_first_order_result_reproduced'])
        self.assertTrue(original['R1b_near_cancelled_product']['unsafe_complete_first_order_result_reproduced'])

    def test_HMAP_03_original_executed_points_and_weights_equal_adapter(self):
        """Instrument only the moment collector; unchanged main still executes."""
        m.historical_sources()
        spec = importlib.util.spec_from_file_location('original_probe_capture',m.HISTORICAL/'probe_metrology_edges.py')
        original = importlib.util.module_from_spec(spec)
        # Execute authenticated bytes without caching inside the frozen evidence.
        exec(compile(Path(spec.origin).read_bytes(), spec.origin, 'exec'), original.__dict__)
        sampled, method = [], original.moments
        def capture(values, weights):
            sampled.append((list(values),list(weights)))
            return method(values,weights)
        original.moments = capture
        argv, path = sys.argv[:], sys.path[:]
        modules = {k:sys.modules.pop(k,None) for k in ('matter1_metrology','matter1_bipm')}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with zipfile.ZipFile(m.HISTORICAL/'original_replay_r01.zip') as z:
                    for name in m.historical_sources()['historical_target_files']:
                        p = Path(tmp)/name;p.parent.mkdir(parents=True,exist_ok=True)
                        p.write_bytes(z.read('historical_target/'+name))
                sys.argv = ['probe','--repo',tmp]
                with redirect_stdout(io.StringIO()): original.main()
        finally:
            sys.argv, sys.path = argv, path
            for k,v in modules.items():
                sys.modules.pop(k,None)
                if v is not None: sys.modules[k]=v
        self.assertEqual(len(sampled),2)
        for key,(values,weights) in zip(('MAP-21','MAP-22'),sampled):
            f=self.fixture(key)['propagation']
            self.assertEqual(values,[m.evaluate(f['expr'],p,f['parameters']) for _,p in f['support']])
            self.assertEqual(weights,[Q(w) for w,_ in f['support']])

    def test_HMAP_04_map21_exact_moments_and_zero_linear_diagnostic(self):
        r=self.cases['MAP-21']['result']
        self.assertEqual(r['output_mean'],'1000000/999999')
        self.assertEqual(r['output_variance'],'1/999998000001000000')
        self.assertEqual(r['mean_shift'],'1/999999')
        self.assertEqual(r['linearized_variance_diagnostic'],'0')
        self.assertEqual(r['jacobian'],['-1','1'])
        self.assertEqual(r['input_covariance'],[['1/1000000']*2]*2)

    def test_HMAP_05_map22_exact_moments_and_shared_dependence(self):
        r=self.cases['MAP-22']['result']
        self.assertEqual(r['output_mean'],'1999999000001/2000000000000')
        self.assertEqual(r['output_variance'],'1000000000001/4000000000000000000000000')
        self.assertEqual(r['linearized_variance_diagnostic'],'1/2000000000000000000')
        self.assertEqual(Q(r['output_variance'])/Q(r['linearized_variance_diagnostic']),Q(1000000000001,2000000))
        self.assertEqual(r['jacobian'],['1','1'])
        cov=[[Q(x) for x in row] for row in r['input_covariance']]
        self.assertEqual(cov[0][0]*cov[1][1]-cov[0][1]**2,0)
        self.assertLess(cov[0][1],0)

    def test_HMAP_06_covariance_only_original_laws_remain_incomplete(self):
        for case in self.cases.values():
            p=case['covariance_only']
            self.assertEqual(p['uncertainty_status'],'partial')
            self.assertIsNone(p['output_mean']);self.assertIsNone(p['output_variance'])
            self.assertEqual(p['linearized_variance_diagnostic'],case['result']['linearized_variance_diagnostic'])

    def test_HMAP_07_three_existing_controls_are_unchanged_and_separate(self):
        before=json.loads((m.HISTORICAL/'prior_mapping_error.json').read_text())
        for key in ('interval_zero_linear_control','near_cancelled_product_control','historical_product_regression'):
            self.assertEqual(self.report[key],before[key])
            for criterion in self.cases:
                with self.assertRaisesRegex(m.ContractError,'historical result differs'):
                    m.certify_historical_law(criterion,self.fixture(criterion),self.report[key])

    def test_HMAP_08_json_roundtrip_preserves_complete_certified_laws(self):
        for criterion,case in self.cases.items():
            copy=json.loads(json.dumps(case))
            self.assertTrue(m.certify_historical_law(criterion,copy['law'],copy['result']))

    def test_HMAP_09_support_changes_cannot_claim_original_identity(self):
        for criterion in self.cases:
            law=self.fixture(criterion);f=law['propagation']
            f['support'][0][1][f['order'][0]]='1/2'
            with self.assertRaisesRegex(m.ContractError,'historical joint law changed'):
                m.certify_historical_law(criterion,law,m.propagate(**f))

    def test_HMAP_10_probability_changes_cannot_claim_original_identity(self):
        law=self.fixture('MAP-22');f=law['propagation']
        f['support']=[[str(Q(1,3)),point] for _,point in f['support']]
        with self.assertRaisesRegex(m.ContractError,'historical joint law changed'):
            m.certify_historical_law('MAP-22',law,m.propagate(**f))

    def test_HMAP_11_independent_marginals_cannot_replace_joint_dependence(self):
        law=self.fixture('MAP-21');f=law['propagation'];a=Q(1,1000)
        f['support']=[['1/4',{'y':str(y),'d':str(d)}] for y in [-a,a] for d in [-a,a]]
        with self.assertRaisesRegex(m.ContractError,'historical joint law changed'):
            m.certify_historical_law('MAP-21',law,m.propagate(**f))

    def test_HMAP_12_parameter_expression_and_units_are_bound(self):
        for field in ('parameters','expr','units','source'):
            law=self.fixture('MAP-21')
            if field=='parameters': law['propagation']['parameters']['one']['value']='2'
            elif field=='expr':law['propagation']['expr']=['add',['input','y'],['input','d']]
            elif field=='units':law['units']['output']='Hz'
            else:law['source_bindings_sha256']='0'*64
            with self.assertRaisesRegex(m.ContractError,'historical joint law changed'):
                m.certify_historical_law('MAP-21',law,self.cases['MAP-21']['result'])

    def test_HMAP_13_false_completeness_or_changed_result_is_rejected(self):
        for criterion,case in self.cases.items():
            for key,value in [('output_variance',case['result']['linearized_variance_diagnostic']),
                    ('output_mean','1'),('mean_shift','0'),('uncertainty_status','complete_first_order_conditional'),
                    ('input_covariance',[['0','0'],['0','0']])]:
                result=deepcopy(case['result']);result[key]=value
                with self.assertRaisesRegex(m.ContractError,'historical result differs'):
                    m.certify_historical_law(criterion,self.fixture(criterion),result)

    def test_HMAP_14_incomplete_or_extra_result_cannot_be_certified(self):
        for extra in (False,True):
            r=deepcopy(self.cases['MAP-21']['result'])
            if extra:r['self_recomputed_hash']=m.digest(r)
            else:del r['support']
            with self.assertRaisesRegex(m.ContractError,'historical result differs'):
                m.certify_historical_law('MAP-21',self.fixture('MAP-21'),r)

    def test_HMAP_15_boolean_float_or_invalid_probability_is_rejected(self):
        for bad in (True,False,0.5,-1,'0'):
            f=self.fixture('MAP-21')['propagation'];f['support'][0][0]=bad
            with self.assertRaises(m.ContractError):m.propagate(**f)
        f=self.fixture('MAP-22')['propagation'];f['support'].pop()
        with self.assertRaises(m.ContractError):m.propagate(**f)

    def test_HMAP_16_denominator_pole_and_conflicting_covariance_rejected(self):
        f=self.fixture('MAP-21')['propagation'];f['support'][0][1]['y']='-1'
        with self.assertRaisesRegex(m.ContractError,'denominator is zero'):m.propagate(**f)
        f=self.fixture('MAP-21')['propagation']
        with self.assertRaisesRegex(m.ContractError,'covariance disagrees'):
            m.propagate(**f,covariance=[['1','0'],['0','1']])
        self.assertEqual(m.ratio_bounds(['1','1'],['-1','1'])['status'],'undefined_or_unbounded')

    def test_HMAP_17_legitimate_singular_and_constant_cancellation_retained(self):
        for key in ('legitimate_common_offset_cancellation','constant_on_declared_support'):
            self.assertEqual(self.report[key]['output_variance'],'0')
        self.assertEqual(self.report['legitimate_common_offset_cancellation']['uncertainty_status'],'exact_for_declared_affine_model')

    def test_HMAP_18_independent_decimal_raw_moment_check(self):
        for precision in (50,80,120):
            with localcontext() as ctx:
                ctx.prec=precision
                def dec(q):q=Q(q);return Decimal(q.numerator)/Decimal(q.denominator)
                a=dec('1/1000');delta=dec('1/1000000')
                for criterion,ys,weights in [('MAP-21',[1/(1+x)+x for x in (-a,a)],[Decimal('0.5')]*2),
                        ('MAP-22',[(1+x)*(1-(1-delta)*x) for x in (-a,Decimal(0),a)],
                         [Decimal('.25'),Decimal('.5'),Decimal('.25')])]:
                    mean=sum(y*w for y,w in zip(ys,weights));var=sum(y*y*w for y,w in zip(ys,weights))-mean*mean
                    exact=self.cases[criterion]['result']
                    self.assertLess(abs(mean-dec(exact['output_mean'])),Decimal(10)**(-precision+6))
                    self.assertLess(abs(var/dec(exact['output_variance'])-1),Decimal(10)**(-precision+25))

    def test_HMAP_19_parameter_sweep_zero_and_near_zero_sensitivity(self):
        for a in (Q(1,2),Q(1,10),Q(1,1000),Q(1,10000)):
            f=self.fixture('MAP-21')['propagation'];f['support']=[['1/2',{'y':str(x),'d':str(x)}] for x in (-a,a)]
            self.assertEqual(Q(m.propagate(**f)['output_variance']),a**6/(1-a*a)**2)
        eps=Q(1,1000)
        for delta in (Q(0),Q(1,1000000),Q(1,1000)):
            f=self.fixture('MAP-22')['propagation']
            f['support']=[[str(p),{'ratio':str(1+x),'frequency':str(1-(1-delta)*x)}]
                          for x,p in zip((-eps,Q(0),eps),(Q(1,4),Q(1,2),Q(1,4))) ]
            self.assertEqual(Q(m.propagate(**f)['output_variance']),delta**2*eps**2/2+(1-delta)**2*eps**4/4)

    def test_HMAP_20_changed_source_and_output_bytes_fail_binding(self):
        for name in ('probe_metrology_edges.py','original-output.json','original_replay_r01.zip'):
            with tempfile.TemporaryDirectory() as tmp:
                copy=Path(tmp)/'evidence';shutil.copytree(m.HISTORICAL,copy)
                with (copy/name).open('ab') as f:f.write(b'\n')
                with self.assertRaisesRegex(m.ContractError,'historical source bytes changed'):
                    m.historical_sources(copy)

    def test_HMAP_21_resealed_source_manifest_cannot_replace_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy=Path(tmp)/'evidence';shutil.copytree(m.HISTORICAL,copy)
            name='probe_metrology_edges.py';p=copy/name;p.write_bytes(p.read_bytes()+b'\n')
            b=json.loads((copy/'source_bindings.json').read_text())
            b['files'][name].update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            (copy/'source_bindings.json').write_text(json.dumps(b,indent=2,sort_keys=True)+'\n')
            with self.assertRaisesRegex(m.ContractError,'historical source binding changed'):
                m.replay_historical_probe(copy)

    def test_HMAP_22_extra_or_missing_evidence_is_rejected(self):
        for extra in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                copy=Path(tmp)/'evidence';shutil.copytree(m.HISTORICAL,copy)
                if extra:(copy/'added.json').write_text('{}')
                else:(copy/'original-output.json').unlink()
                with self.assertRaisesRegex(m.ContractError,'historical source inventory changed'):
                    m.historical_sources(copy)

    def test_HMAP_23_persisted_report_and_other_gate_scope(self):
        self.assertEqual(self.report,json.loads(m.REPORT.read_text()))
        original=self.report['original_historical_laws']
        self.assertEqual(set(original['cases']),{'MAP-21','MAP-22'})
        self.assertEqual(len(original['unchanged_obligations']),3)
        self.assertIn('not MAP-28 acceptance',original['replay']['scope'])

    def test_HMAP_24_persisted_rehashed_original_case_fails_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'mapping_error.json'
            altered=deepcopy(self.report)
            case=altered['original_historical_laws']['cases']['MAP-22']
            case['result']['output_variance']=case['result']['linearized_variance_diagnostic']
            case['self_recomputed_sha256']=m.digest(case)
            path.write_bytes(m.canonical(altered));before=path.read_bytes()
            command=[sys.executable,'-B']+([] if __debug__ else ['-O'])+[
                str(ROOT/'manual/scripts/aod_mapping_error.py'),'--check','--output',str(path)]
            result=subprocess.run(command,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn(b'stored mapping/error report differs',result.stderr)
            self.assertEqual(path.read_bytes(),before)

    def test_HMAP_25_dependency_substitution_inside_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy=Path(tmp)/'evidence';shutil.copytree(m.HISTORICAL,copy)
            path=copy/'original_replay_r01.zip'
            with zipfile.ZipFile(path) as z:members={n:z.read(n) for n in z.namelist()}
            members['historical_target/manual2/scripts/matter1_metrology.py']+=b'\n'
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for n,data in members.items():z.writestr(n,data)
            with self.assertRaisesRegex(m.ContractError,'historical source bytes changed'):
                m.replay_historical_probe(copy)


if __name__ == '__main__':
    unittest.main()
