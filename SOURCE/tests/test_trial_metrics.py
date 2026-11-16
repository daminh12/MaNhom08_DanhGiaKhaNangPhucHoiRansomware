"""Synthetic sealed-run fixtures only. These tests are not Windows/restore evidence."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'metrics'))
import evidence
import trial_metrics as live
from protocol import CODE_FILES, EVIDENCE_FILES, GUIDED, AUTOMATED


class TrialMetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.directory=self.root/'p4-fixture';self.directory.mkdir()
        original=evidence.load_case('main')
        self.result=copy.deepcopy(original['result']);self.events=copy.deepcopy(original['events'])
        self.result.update(schema_version=2,run_id='p4-fixture',measurement_version=AUTOMATED,
                           runtime={'host_os':'FixtureOS','os_release':'fixture','os_version':'fixture','python':'3.11'},
                           target_project='group08-restore-p4-fixture',target_volume='group08-restore-p4-fixture_restore_data',
                           source_url='http://127.0.0.1:8080',return_source_requested=True,source_touched=True)
        self.acks=copy.deepcopy(original['acks']);self.receipt=self.result['backup']
        self.receipt['snapshot_id']='a'*64
        self.events[0].update(commit='b'*40,measurement_version=AUTOMATED,runtime=self.result['runtime'],observer_id='c'*32,
                              working_source_sha256={name:hashlib.sha256(name.encode()).hexdigest() for name in CODE_FILES})
        for e in self.events:
            e['run_id']='p4-fixture'
            if e['event']=='TARGET_READY':e['volume']=self.result['target_volume']
            if 'snapshot_id' in e:e['snapshot_id']=self.receipt['snapshot_id']
        # Fake Git blobs are explicit: no fixture can certify a real execution.
        patcher=patch.object(live,'git_bytes',side_effect=lambda ref,name:name.encode())
        patcher.start();self.addCleanup(patcher.stop)

    def dump(self,name,value):
        path=self.directory/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return path

    def seal(self):
        records={}
        for name in EVIDENCE_FILES:
            path=self.directory/name
            if path.exists():records[name]={'sha256':evidence.sha(path),'size_bytes':path.stat().st_size}
        self.dump('evidence-manifest.json',{'schema_version':1,'run_id':self.result['run_id'],'files':records})

    def write(self):
        meta=self.dump('extracted/payload/metadata.json',self.receipt['dump_metadata'])
        manifest={'schema_version':1,'hash_algorithm':'SHA-256','files':[
            {'path':'database.sql','size_bytes':1,'sha256':self.receipt['dump_metadata']['baseline_sql_sha256']},
            {'path':'metadata.json','size_bytes':meta.stat().st_size,'sha256':evidence.sha(meta)}]}
        self.receipt['manifest_sha256']=evidence.sha(self.dump('extracted/manifest.json',manifest))
        self.dump('extracted/verified.json',{'snapshot_id':self.receipt['snapshot_id'],
                  'manifest_sha256':self.receipt['manifest_sha256'],'status':'PASS'})
        self.dump('observed-baseline.json',self.receipt['dump_metadata']['business_baseline'])
        self.dump('backup-receipt.json',self.receipt);self.dump('acknowledgements.json',self.acks)
        for e in self.events:
            if e['event']=='SNAPSHOT_VERIFIED':e['manifest_sha256']=self.receipt['manifest_sha256']
        self.dump('result.json',self.result)
        (self.directory/'events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in self.events),encoding='utf-8')
        self.seal()

    def guided(self):
        self.result['measurement_version']=GUIDED;self.events[0]['measurement_version']=GUIDED
        one=lambda name:evidence.one(self.events,name)
        cleanup=one('TARGET_CLEANUP')['monotonic_ns'];fault=one('FAULT_REQUESTED')['monotonic_ns']
        detected=one('FAULT_DETECTED')['monotonic_ns']
        one('REQUEST_COMPARISON_FINISHED')['monotonic_ns']=cleanup+1000
        def event(name,ns,**extra):
            self.events.append({'run_id':self.result['run_id'],'event':name,'monotonic_ns':ns,
                                'utc':one('FAULT_REQUESTED')['utc'],**extra})
        for action,operator,ns in [('INJECT','Đa Minh',fault-10),('RECOVER','Minh Quân',detected+10),('WEB_OK','Minh Quân',cleanup+2000)]:
            event('OPERATOR_PROMPT',ns,action=action,operator=operator)
            event('OPERATOR_CONFIRMED',ns+1,action=action,operator=operator)
        event('FINAL_DATA_VERIFIED',cleanup+3000,row_count=self.result['restored_snapshot_rows']+1)
        self.events.sort(key=lambda e:e['monotonic_ns'])

    def test_export_new_run_without_historical_runtime_or_exact_rpo_claims(self):
        self.write();summary=live.export_trial(self.directory,self.root/'export')
        row=summary['samples'][0]
        self.assertEqual(row['host_os'],'FixtureOS');self.assertEqual(row['observed_rto_seconds'],'54.198351197')
        self.assertEqual(row['unrecovered_acknowledged_requests'],3)
        self.assertIsNone(row['exact_rpo_seconds']);self.assertEqual(row['fresh_artifact_integrity'],'NOT TESTED')
        self.assertNotIn('Linux',row['notes']);self.assertEqual(row['rto_target_result'],'NOT TESTED')
        csv_path=self.root/'export/Đo_lường_RPO_RTO.csv'
        self.assertTrue(csv_path.read_bytes().startswith(b'\xef\xbb\xbf'))
        with csv_path.open(encoding='utf-8-sig',newline='') as f:
            self.assertEqual(list(csv.DictReader(f))[0]['host_os'],'FixtureOS')
        with self.assertRaises(FileExistsError):live.export_trial(self.directory,self.root/'export')

    def test_guided_handover_and_ready_order_accepted(self):
        self.guided();self.write()
        row=live.export_trial(self.directory,self.root/'export')['samples'][0]
        self.assertTrue(row['operator_confirmation'].startswith('RECORDED'))
        self.assertEqual(row['measurement_version'],GUIDED)

    def test_missing_handover_or_comparison_cannot_be_pass(self):
        for missing in ['OPERATOR_CONFIRMED','REQUEST_COMPARISON_FINISHED','FINAL_DATA_VERIFIED']:
            with self.subTest(missing=missing):
                self.setUp();self.guided();self.events=[e for e in self.events if e['event']!=missing];self.write()
                with self.assertRaises(evidence.EvidenceError):live.export_trial(self.directory,self.root/'export')

    def test_guided_cannot_reuse_automated_event_order(self):
        self.result['measurement_version']=GUIDED;self.events[0]['measurement_version']=GUIDED;self.write()
        with self.assertRaises(evidence.EvidenceError):live.export_trial(self.directory,self.root/'export')

    def test_changed_bytes_or_source_fingerprint_are_rejected(self):
        self.write();(self.directory/'result.json').write_text('{}',encoding='utf-8')
        with self.assertRaises(evidence.EvidenceError):live.load_trial(self.directory)
        self.events[0]['working_source_sha256'][CODE_FILES[0]]='0'*64;self.write()
        with self.assertRaises(evidence.EvidenceError):live.load_trial(self.directory)

    def test_mixed_run_reversed_clock_and_summary_override_rejected(self):
        for kind in ['run','clock','summary']:
            with self.subTest(kind=kind):
                self.setUp()
                if kind=='run':self.events[2]['run_id']='p4-other'
                elif kind=='clock':self.events[3]['monotonic_ns']=0
                else:self.result['observed_rto_seconds']=0
                self.write()
                with self.assertRaises(evidence.EvidenceError):live.export_trial(self.directory,self.root/'export')

    def test_failed_uncertain_and_aborted_are_not_zero_duration(self):
        for status in ['FAILED','ABORTED']:
            with self.subTest(status=status):
                self.setUp();self.result['status']=status
                evidence.one(self.events,'TRIAL_ENDED')['status']=status
                item=copy.deepcopy(evidence.one(self.events,'FAULT_REQUESTED'));item.update(event='REQUEST_UNCERTAIN',request_id='fixture-uncertain')
                self.events.append(item);self.events.sort(key=lambda e:e['monotonic_ns']);self.write()
                row=live.export_trial(self.directory,self.root/'export')['samples'][0]
                self.assertEqual(row['rto_status'],'NOT TESTED (censored)');self.assertIsNone(row['observed_rto_seconds'])
                self.assertEqual(row['uncertain_requests'],1)

    def test_success_with_uncertain_or_wrong_target_url_is_rejected(self):
        for kind in ['uncertain','volume','url']:
            with self.subTest(kind=kind):
                self.setUp()
                if kind=='uncertain':
                    self.events.insert(2,dict(self.events[1],event='REQUEST_UNCERTAIN'))
                elif kind=='volume':self.result['target_volume']='group08-lab_db_data'
                else:self.result['source_url']='http://127.0.0.1:9999'
                self.write()
                with self.assertRaises(evidence.EvidenceError):live.export_trial(self.directory,self.root/'export')

    def test_unsafe_manifest_path_and_symlink_rejected(self):
        self.write()
        seal=evidence.load(self.directory/'evidence-manifest.json');seal['files']['../outside']={}
        self.dump('evidence-manifest.json',seal)
        with self.assertRaises(evidence.EvidenceError):live.load_trial(self.directory)
        self.write();path=self.directory/'result.json';other=self.root/'other.json';path.rename(other)
        try:path.symlink_to(other)
        except OSError:self.skipTest('Host does not permit symlinks')
        with self.assertRaises(evidence.EvidenceError):live.load_trial(self.directory)

    def test_no_export_inside_evidence(self):
        self.write()
        with self.assertRaises(evidence.EvidenceError):live.export_trial(self.directory,self.directory/'export')

    def test_source_return_failure_remains_visible_without_erasing_trial(self):
        self.result['return_source_status']='FAILED'
        end=evidence.one(self.events,'POST_TRIAL_RETURN_SOURCE_FINISHED');end['event']='POST_TRIAL_RETURN_SOURCE_FAILED'
        self.write();row=live.export_trial(self.directory,self.root/'export')['samples'][0]
        self.assertEqual(row['return_source_status'],'FAILED');self.assertEqual(row['rto_status'],'MEASURED')

    def test_failed_sent_without_ack_counts_as_uncertain(self):
        self.result['status']='ABORTED';evidence.one(self.events,'TRIAL_ENDED')['status']='ABORTED'
        self.events=[e for e in self.events if not(e['event']=='REQUEST_ACKNOWLEDGED' and e.get('request_id')=='recovery-write-probe')]
        self.write();row=live.export_trial(self.directory,self.root/'export')['samples'][0]
        self.assertEqual(row['uncertain_requests'],1)

    def test_metadata_manifest_and_snapshot_must_agree(self):
        for change in ['metadata','snapshot','missing-seal']:
            with self.subTest(change=change):
                self.setUp();self.write()
                if change=='metadata':self.dump('extracted/payload/metadata.json',{'business_baseline':{}});self.seal()
                elif change=='snapshot':
                    data=evidence.load(self.directory/'extracted/verified.json');data['snapshot_id']='d'*64
                    self.dump('extracted/verified.json',data);self.seal()
                else:(self.directory/'evidence-manifest.json').unlink()
                with self.assertRaises((evidence.EvidenceError,FileNotFoundError)):
                    live.export_trial(self.directory,self.root/'export')

    def test_web_control_and_corrupt_keep_not_applicable_metrics(self):
        for scenario,name in [('web-outage','web-control'),('reject-corrupt','corrupt')]:
            with self.subTest(scenario=scenario):
                self.setUp();sample=evidence.load_case(name)
                prepared=self.events[0];self.events=copy.deepcopy(sample['events']);self.events[0]=prepared
                self.result.update(sample['result'])
                self.result.update(run_id='p4-fixture',schema_version=2,scenario=scenario,
                                   measurement_version=AUTOMATED,runtime=prepared['runtime'],return_source_requested=False)
                self.result.pop('return_source_status',None)
                self.events=[e for e in self.events if not e['event'].startswith('POST_TRIAL_RETURN_SOURCE')]
                self.result['backup']=self.receipt
                for e in self.events:
                    e['run_id']='p4-fixture'
                    if 'snapshot_id' in e:e['snapshot_id']=self.receipt['snapshot_id']
                self.events[0]['monotonic_ns']=self.events[1]['monotonic_ns']-1
                self.write();row=live.export_trial(self.directory,self.root/'export')['samples'][0]
                self.assertEqual(row['rpo_status'],'NOT APPLICABLE')
                if name=='corrupt':self.assertEqual(row['rto_status'],'NOT APPLICABLE');self.assertEqual(row['negative_test_result'],'PASS')
                else:self.assertEqual(row['rto_status'],'MEASURED')

    def test_clean_restore_is_not_an_incident_rto(self):
        self.result['scenario']='restore'
        self.events=[e for e in self.events if e['event'] not in ('FAULT_REQUESTED','FAULT_DETECTED','REQUEST_COMPARISON_FINISHED')]
        self.write();row=live.export_trial(self.directory,self.root/'export')['samples'][0]
        self.assertEqual(row['rto_status'],'NOT APPLICABLE');self.assertIsNone(row['observed_rto_seconds'])


if __name__=='__main__':unittest.main()
