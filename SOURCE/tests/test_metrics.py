"""Offline evidence/math/CSV regression tests. No service or database access."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

CODE=Path(__file__).resolve().parents[1]/'metrics'
sys.path.insert(0,str(CODE))
import evidence
from evidence import EvidenceError,artifact_check,load_case,one,timeline
from export_metrics import analyze,csv_cell,export


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={k:load_case(k) for k in evidence.CASES}

    def main_bundle(self):return copy.deepcopy(self.samples['main'])

    def test_real_events_recompute_rto_and_bounded_lag(self):
        row,_=analyze(self.main_bundle())
        self.assertEqual(row['observed_rto_seconds'],'54.198351197')
        self.assertEqual(row['recovered_commit_lag_lower_seconds'],'10.518407983')
        self.assertEqual(row['recovered_commit_lag_upper_seconds'],'10.532435583')
        self.assertEqual(row['unrecovered_acknowledged_requests'],3)
        self.assertEqual(row['acknowledged_requests'],4)
        self.assertIsNone(row['exact_rpo_seconds'])
        self.assertEqual(row['rpo_target_result'],'NOT TESTED')
        self.assertEqual(row['backup_age_since_verified_seconds'],'0.091588006')
        self.assertNotEqual(row['sql_import_seconds'],row['observed_rto_seconds'])

    def test_summary_cannot_override_raw_time(self):
        b=self.main_bundle();b['result']['observed_rto_seconds']=0
        with self.assertRaises(EvidenceError):analyze(b)

    def test_mixed_run_identity_rejected(self):
        b=self.main_bundle();b['events'][2]['run_id']='p4-other'
        with self.assertRaises(EvidenceError):analyze(b)

    def test_backwards_clock_rejected(self):
        b=self.main_bundle();b['events'][3]['monotonic_ns']=0
        with self.assertRaises(EvidenceError):analyze(b)

    def test_truncated_timeline_is_not_pass(self):
        b=self.main_bundle();b['events']=[e for e in b['events'] if e['event']!='TRIAL_ENDED']
        with self.assertRaises(EvidenceError):analyze(b)

    def test_false_status_is_not_hidden(self):
        b=self.main_bundle();b['result']['status']='FAILED'
        with self.assertRaises(EvidenceError):analyze(b)

    def test_failed_outage_is_censored_not_zero(self):
        b=self.main_bundle();b['result']['status']='FAILED'
        one(b['events'],'TRIAL_ENDED')['status']='FAILED'
        b['events']=[e for e in b['events'] if e['event']!='SERVICE_VERIFIED']
        row,_=analyze(b)
        self.assertEqual(row['rto_status'],'NOT TESTED (censored)')
        self.assertIsNone(row['observed_rto_seconds'])

    def test_failed_phase3_attempt_kept_without_incident_metric(self):
        row,_=analyze(copy.deepcopy(self.samples['failed-restore']))
        self.assertEqual(row['trial_status'],'FAILED')
        self.assertEqual(row['rto_status'],'NOT APPLICABLE')
        self.assertIsNone(row['observed_rto_seconds'])

    def test_unknown_or_repeated_ack_identity_rejected(self):
        b=self.main_bundle();b['acks'][1]['request_id']=b['acks'][0]['request_id']
        with self.assertRaises(EvidenceError):analyze(b)

    def test_ack_file_and_journal_disagreement_rejected(self):
        b=self.main_bundle();b['acks'][0]['ack_ns']+=1
        with self.assertRaises(EvidenceError):analyze(b)

    def test_stability_gate_required(self):
        b=self.main_bundle();b['events']=[e for e in b['events'] if not(e['event']=='STABILITY_PROBE' and e['sample']==3)]
        with self.assertRaises(EvidenceError):analyze(b)

    def test_import_verification_order_required(self):
        b=self.main_bundle();one(b['events'],'IMPORT_FINISHED')['monotonic_ns']=one(b['events'],'DATA_VERIFIED')['monotonic_ns']+1
        b['events'].sort(key=lambda e:e['monotonic_ns'])
        with self.assertRaises(EvidenceError):analyze(b)

    def test_source_fingerprint_is_not_an_unchecked_label(self):
        b=self.main_bundle();b['events'][0]['working_source_sha256']['SOURCE/recovery/common.py']='0'*64
        with self.assertRaises(EvidenceError):analyze(b)

    def test_integrity_only_test_has_no_rto_or_rpo(self):
        row,_=analyze(copy.deepcopy(self.samples['corrupt']))
        self.assertEqual(row['rto_status'],'NOT APPLICABLE')
        self.assertEqual(row['rpo_status'],'NOT APPLICABLE')
        self.assertIsNone(row['observed_rto_seconds'])

    def test_json_duplicate_and_nonfinite_numbers_fail(self):
        for raw in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
            with self.subTest(raw=raw),self.assertRaises(EvidenceError):evidence.decode(raw)

    def test_csv_formula_neutralization(self):
        for value in ['=1+1',' +formula','@SUM(A1)','\t=1','-formula']:
            self.assertTrue(csv_cell(value).startswith("'"))
        self.assertEqual(csv_cell(None),'')
        self.assertEqual(csv_cell('54.198351197'),'54.198351197')

    def test_actual_extract_detects_modified_sql_in_temporary_copy(self):
        b=self.main_bundle()
        original=evidence.ROOT/'work/recovery'/b['result']['run_id']/'extracted'
        if not original.exists():self.skipTest('Private SQL artifact not in a fresh clone')
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/b['result']['run_id']/'extracted'
            shutil.copytree(original,target)
            artifact_check(b,Path(t))
            with (target/'payload/database.sql').open('ab') as f:f.write(b'\nTEST FIXTURE MODIFICATION\n')
            with self.assertRaises(EvidenceError):artifact_check(b,Path(t))

    def test_pin_detects_different_git_bytes_without_editing_repository(self):
        with patch.object(evidence,'git_bytes',return_value=b'not the committed evidence'):
            with self.assertRaises(EvidenceError):evidence.pinned('docs/evidence/phase4/main-result.json',evidence.EVIDENCE_REF,{})

    def test_fresh_verification_must_return_source_and_bind_to_trial(self):
        path=evidence.ROOT/'docs/evidence/phase5/retained-integrity.json'
        if not path.exists():self.skipTest('Post-trial integrity record not available')
        original=evidence.load(path)
        for changed in [{'return_source_status':'FAILED'},{'source_unchanged':False},{'trial_run_id':'p4-other'}]:
            with self.subTest(changed=changed),self.assertRaises(EvidenceError):
                analyze(self.main_bundle(),fresh=original|changed)

    def test_fresh_membership_must_match_recorded_observation(self):
        path=evidence.ROOT/'docs/evidence/phase5/retained-integrity.json'
        if not path.exists():self.skipTest('Post-trial integrity record not available')
        fresh=evidence.load(path);fresh['request_observations'][0]['matching_rows']=[]
        with self.assertRaises(EvidenceError):analyze(self.main_bundle(),fresh=fresh)

    def test_export_is_reproducible_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'export'
            summary=export(out,evidence.EVIDENCE_REF)
            self.assertEqual(summary['main_trial_count'],1)
            self.assertEqual(len(summary['samples']),4)
            csv=(out/'metrics.csv').read_bytes()
            self.assertTrue(csv.startswith(b'\xef\xbb\xbf'))
            self.assertIn(b'FAILED',csv)
            out2=Path(t)/'second';export(out2,evidence.EVIDENCE_REF)
            self.assertEqual(csv,(out2/'metrics.csv').read_bytes())
            with self.assertRaises(FileExistsError):export(out,evidence.EVIDENCE_REF)


if __name__=='__main__':unittest.main()
