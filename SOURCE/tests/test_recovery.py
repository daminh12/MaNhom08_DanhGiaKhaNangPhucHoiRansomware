"""Recovery invariants, using synthetic fixtures/mocks, never live Docker/DB."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

CODE=Path(__file__).resolve().parents[1]/'recovery'
sys.path.insert(0,str(CODE))
from common import (acknowledged_comparison, baseline_for, canonical_api, compare,
                    full_snapshot, rows_hash, run_id)
import controller


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.schema='CREATE TABLE `orders` (`id` bigint unsigned NOT NULL AUTO_INCREMENT, PRIMARY KEY (`id`)) ENGINE=InnoDB AUTO_INCREMENT=3'
        self.rows=[[1,'LAB-A','Pen',1,25000,'2026-01-01T00:00:00.000000Z'],
                   [2,'LAB-B','Folder',2,10000,'2026-01-01T00:00:01.000001Z']]
        self.baseline=baseline_for(self.schema,self.rows)

    def test_full_id_and_run_guards(self):
        self.assertEqual(full_snapshot('a'*64),'a'*64)
        for bad in ['latest','a'*8,'../outside','A'*64]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):full_snapshot(bad)
        for bad in ['../outside','p4-../x','group08-lab','p3-UPPER','p4-']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):run_id(bad)

    def test_schema_volatile_counter_is_not_a_difference(self):
        compare(self.schema.replace('=3','=99'),self.rows,self.baseline)

    def test_mysql_roundtrip_redundant_charset_is_normalized(self):
        before="CREATE TABLE `orders` (`name` varchar(40) COLLATE utf8mb4_unicode_ci) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        after=before.replace('varchar(40) COLLATE','varchar(40) CHARACTER SET utf8mb4 COLLATE')
        compare(after,self.rows,baseline_for(before,self.rows))
        with self.assertRaises(ValueError):
            compare(after.replace('CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci','CHARACTER SET latin1 COLLATE latin1_bin'),self.rows,baseline_for(before,self.rows))

    def test_schema_or_same_count_content_change_is_rejected(self):
        for schema,rows in [(self.schema.replace('unsigned',''),self.rows),
                            (self.schema,[self.rows[0],[2,'LAB-CHANGED',*self.rows[1][2:]]])]:
            with self.subTest(schema=schema),self.assertRaises(ValueError):compare(schema,rows,self.baseline)

    def test_full_dataset_including_older_than_api_limit(self):
        rows=[[i,'LAB-'+str(i),'Pen',1,1,'2026-01-01T00:00:00.000000Z'] for i in range(1,106)]
        baseline=baseline_for(self.schema,rows)
        rows[0]=[1,'LAB-MODIFIED','Pen',1,1,'2026-01-01T00:00:00.000000Z']
        with self.assertRaises(ValueError):compare(self.schema,rows,baseline)

    def test_exact_integer_ids_and_row_order(self):
        rows=[[*self.rows[0]]];rows[0][0]=2**63+1
        rows_hash(rows)
        rows[0][0]=float(rows[0][0])
        with self.assertRaises(ValueError):rows_hash(rows)
        with self.assertRaises(ValueError):rows_hash(list(reversed(self.rows)))

    def test_write_probe_does_not_rebaseline_existing_rows(self):
        probe=[3,'LAB-PROBE','Pen',1,5,'2026-01-01T00:00:02.000000Z']
        compare(self.schema,self.rows+[probe],self.baseline,probe)
        changed=[list(r) for r in self.rows];changed[0][4]+=1
        with self.assertRaises(ValueError):compare(self.schema,changed+[probe],self.baseline,probe)
        with self.assertRaises(ValueError):compare(self.schema,self.rows,self.baseline,probe)

    def test_api_timestamp_is_canonical_but_not_commit_time(self):
        r={'id':1,'customer_alias':'LAB-A','product_name':'Pen','quantity':1,'unit_price_vnd':25000,'created_at_utc':'2026-01-01T00:00:00Z'}
        self.assertEqual(canonical_api(r),self.rows[0])

    def test_lost_ack_is_not_silently_retried(self):
        lab=object.__new__(controller.Lab);events=[]
        lab.event=lambda name,**data: events.append(name) or {'monotonic_ns':1}
        lab.http=lambda *a,**k: (503,{'error':'uncertain'})
        with self.assertRaises(RuntimeError):lab.create_order('LAB-A',8080,'r1')
        self.assertEqual(events,['REQUEST_SENT','REQUEST_UNCERTAIN'])

    def test_acknowledged_loss_and_bounds_not_created_at(self):
        a=[{'request_id':str(i),'alias':row[1],'row':row,'sent_ns':i*100,'ack_ns':i*100+10} for i,row in enumerate(self.rows,1)]
        result=acknowledged_comparison(a,self.rows[:1],1000)
        self.assertEqual(result['unrecovered_acknowledged'],['2'])
        self.assertEqual(result['recovered_commit_age_bounds']['lower_seconds'],890/1e9)

    def test_nonprefix_and_duplicates_do_not_get_a_recovery_point(self):
        a=[{'request_id':str(i),'alias':r[1],'row':r,'sent_ns':i*3+1,'ack_ns':i*3+2} for i,r in enumerate(self.rows)]
        self.assertIsNone(acknowledged_comparison(a,self.rows[1:],10)['recovered_commit_age_bounds'])
        duplicate=[3,*self.rows[0][1:]]
        self.assertTrue(acknowledged_comparison(a,self.rows+[duplicate],10)['duplicates'])

    def test_bad_ack_clocks_cannot_produce_metrics(self):
        ack={'request_id':'r1','alias':'LAB-A','row':self.rows[0],'sent_ns':1,'ack_ns':2}
        for updates in [{'ack_ns':11},{'sent_ns':3},{'sent_ns':-1},{'ack_ns':True},{'ack_ns':float('nan')}]:
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                acknowledged_comparison([ack|updates],self.rows,10)

    def test_repeated_business_identity_is_rejected(self):
        ack={'request_id':'r1','alias':'LAB-A','row':self.rows[0],'sent_ns':1,'ack_ns':2}
        with self.assertRaises(ValueError):acknowledged_comparison([ack,ack|{'sent_ns':3,'ack_ns':4}],self.rows,10)

    def test_overlapping_ack_profile_is_not_silently_sequential(self):
        a=[{'request_id':str(i),'alias':r[1],'row':r,'sent_ns':1,'ack_ns':2} for i,r in enumerate(self.rows)]
        with self.assertRaises(ValueError):acknowledged_comparison(a,self.rows,10)

    def test_existing_or_partial_run_is_never_reused(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(controller,'WORK',Path(tmp)):
            args=types.SimpleNamespace(run_id='p3-existing',port=8081,action='restore',release_source_containers=False)
            controller.Lab(args)
            with self.assertRaises(FileExistsError):controller.Lab(args)

    def test_existing_target_is_rejected_before_creation(self):
        lab=object.__new__(controller.Lab);lab.project='group08-restore-p3-test'
        lab.call=lambda *a,**k:'existing-container'
        with self.assertRaises(ValueError):lab.preflight_target()

    def test_unlabelled_named_volume_is_also_rejected(self):
        lab=object.__new__(controller.Lab);lab.project='group08-restore-p3-test'
        def call(cmd,*a,**kw):
            return lab.project+'_restore_data' if cmd[:3]==['docker','volume','ls'] and '--format' in cmd else ''
        lab.call=call
        with self.assertRaises(ValueError):lab.preflight_target()

    def test_source_url_cannot_point_to_a_different_binding(self):
        lab=object.__new__(controller.Lab);lab.source_port=lambda:8080
        def inspect(name):
            service='db' if name.endswith('db-1') else 'web'
            return {'Config':{'Labels':{'com.docker.compose.project':'group08-lab','com.docker.compose.service':service}},
                    'State':{'Running':True},'Mounts':[{'Destination':'/var/lib/mysql','Name':'group08-lab_db_data'}],
                    'NetworkSettings':{'Ports':{'8000/tcp':[{'HostIp':'0.0.0.0','HostPort':'9999'}]}}}
        lab.inspect=inspect
        with self.assertRaises(ValueError):lab.validate_source()

    def test_process_nonzero_is_not_accepted(self):
        import subprocess
        lab=object.__new__(controller.Lab);lab.env={};lab.event=lambda *a,**k:None
        with patch.object(controller.subprocess,'run',return_value=subprocess.CompletedProcess([],1,b'',b'SIMULATED SQL import error')):
            with self.assertRaises(RuntimeError):lab.call(['not-run'],'SQL import')

    def test_archive_fails_before_import_with_wrong_manifest(self):
        # Exercise extractor with a fake Restic backend; no repository access.
        spec=importlib.util.spec_from_file_location('test_phase2',CODE.parent/'backup/backup.py')
        backup=importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)
        saved=sys.modules.get('backup');sys.modules['backup']=backup
        try:
            spec=importlib.util.spec_from_file_location('archive_test',CODE/'archive.py')
            archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
            with tempfile.TemporaryDirectory() as t:
                actual=Path(t);(actual/'p3-test').mkdir()
                old_path=archive.Path
                def path(value):return actual if value=='/recovery-work' else old_path(value)
                def restic(*args,**kw):
                    if args[0]=='snapshots':return json.dumps([{'id':'a'*64,'tags':['p2-test']}])
                    if args[0]=='dump':kw['output'].write_text('{}')
                    return ''
                with patch.object(archive,'Path',side_effect=path),patch.object(backup,'restic',side_effect=restic):
                    with self.assertRaises(ValueError):archive.extract('p2-test','a'*64,'b'*64,'p3-test')
                self.assertFalse((actual/'p3-test/extracted/payload/database.sql').exists())
        finally:
            if saved is None:sys.modules.pop('backup',None)
            else:sys.modules['backup']=saved


if __name__=='__main__':unittest.main()
