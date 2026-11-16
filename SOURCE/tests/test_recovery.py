"""Recovery invariants, using synthetic fixtures/mocks, never live Docker/DB."""
from datetime import datetime, timezone
from contextlib import nullcontext, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

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

    def test_malformed_created_response_is_uncertain_without_retry(self):
        for body in [{}, {'order':None}, {'order':{'id':1}}, {'order':{'created_at_utc':1}}]:
            with self.subTest(body=body):
                lab=object.__new__(controller.Lab);events=[];calls=[]
                lab.event=lambda name,**data: events.append(name) or {'monotonic_ns':1}
                def http(*args,**kwargs):
                    calls.append(1)
                    return 201,body
                lab.http=http
                with self.assertRaises(RuntimeError):lab.create_order('LAB-A',8080,'r1')
                self.assertEqual(calls,[1])
                self.assertEqual(events,['REQUEST_SENT','REQUEST_UNCERTAIN'])

    def test_created_response_must_obey_exact_integer_contract(self):
        lab=object.__new__(controller.Lab);events=[]
        lab.event=lambda name,**data: events.append(name) or {'monotonic_ns':1}
        # bool compares equal to 1 in Python, but is not a valid order ID.
        lab.http=lambda *a,**k:(201,{'order':{'id':True,'customer_alias':'LAB-A',
            'product_name':'Pen','quantity':1,'unit_price_vnd':25000,
            'created_at_utc':'2026-01-01T00:00:00Z'}})
        with self.assertRaises(RuntimeError):lab.create_order('LAB-A',8080,'r1')
        self.assertEqual(events,['REQUEST_SENT','REQUEST_UNCERTAIN'])

    def test_valid_created_response_still_produces_business_ack(self):
        lab=object.__new__(controller.Lab);events=[]
        lab.event=lambda name,**data: events.append(name) or {'monotonic_ns':len(events)}
        lab.http=lambda *a,**k:(201,{'order':{'id':1,'customer_alias':'LAB-A',
            'product_name':'Pen','quantity':1,'unit_price_vnd':25000,
            'created_at_utc':'2026-01-01T00:00:00Z'}})
        result=lab.create_order('LAB-A',8080,'r1')
        self.assertEqual(events,['REQUEST_SENT','REQUEST_ACKNOWLEDGED'])
        self.assertEqual((result['sent_ns'],result['ack_ns']),(1,2))
        self.assertEqual(result['row'],self.rows[0])

    def test_missing_or_invalid_local_secret_refused_without_disclosing_values(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(controller,'ROOT',Path(tmp)):
            root=Path(tmp);(root/'secrets').mkdir();(root/'backups/restic').mkdir(parents=True)
            for name in ['db_root_password.txt','db_app_password.txt','db_backup_password.txt','restic_password.txt']:
                (root/'secrets'/name).write_text('a'*64)
            (root/'backups/restic/config').write_text('{}')
            lab=object.__new__(controller.Lab)
            self.assertIn('PASS',lab.local_inputs()['credential_files'])
            path=root/'secrets/restic_password.txt';path.write_text('PRIVATE-INVALID')
            with self.assertRaises(ValueError) as error:lab.local_inputs()
            self.assertNotIn('PRIVATE-INVALID',str(error.exception))
            path.unlink()
            with self.assertRaises(ValueError):lab.local_inputs()
            self.assertEqual(lab.local_inputs(backup=False,archive=False)['repository_config'],'NOT TESTED')
            path.write_text('a'*64)
            (root/'secrets/db_backup_password.txt').unlink()
            # Restoring an existing snapshot does not need the dump account.
            self.assertIn('PASS',lab.local_inputs(backup=False)['credential_files'])
            with self.assertRaises(ValueError):lab.local_inputs()

    def test_low_space_fails_without_service_lifecycle_commands(self):
        lab=object.__new__(controller.Lab);lab.result={};commands=[];events=[]
        lab.event=lambda name,**data:events.append((name,data))
        def call(command,*args,**kwargs):
            commands.append(command)
            return 'vfs' if command[1]=='info' else str(512*1024**2)
        lab.call=call
        with patch.object(controller.shutil,'disk_usage',return_value=types.SimpleNamespace(free=128*1024**2)):
            with self.assertRaises(RuntimeError):lab.resource_check(allow_release_credit=True)
        self.assertEqual(events[0][0],'RESOURCE_CHECK')
        self.assertEqual(lab.result['resources']['host_free_bytes'],128*1024**2)
        self.assertTrue(all(command[1] in ['info','image'] for command in commands))

    def test_preflight_web_scope_does_not_permit_clean_restore(self):
        lab=object.__new__(controller.Lab);lab.result={};lab.a=types.SimpleNamespace(preflight_scope='web-control',release_source_containers=False)
        lab.local_inputs=lambda **kwargs:{'repository_config':'NOT TESTED'}
        lab.capture=lambda:(self.schema,self.rows)
        def api_row(row):
            return dict(zip(['id','customer_alias','product_name','quantity','unit_price_vnd','created_at_utc'],row))
        lab.http=lambda *args:(200,{'total':2,'orders':[api_row(r) for r in reversed(self.rows)]})
        lab.sql=lambda *args,**kwargs:'GRANT SELECT, INSERT ON `lab_config`.`orders` TO `group08_app`@`%`'
        lab.source=lambda *args,**kwargs:'Filesystem 1024-blocks Used Available Capacity Mounted on\nlab 999999 1 524288 1% /\nlab 999999 1 524288 1% /\n'
        events=[];lab.event=lambda name,**kwargs:events.append(name)
        with patch.object(controller.shutil,'disk_usage',return_value=types.SimpleNamespace(free=512*1024**2)):
            lab.preflight()
        self.assertEqual(lab.result['preflight']['status'],'PASS')
        self.assertIn('NOT TESTED',lab.result['preflight']['clean_recovery_resources'])
        self.assertEqual(events,['PREFLIGHT_PASSED'])
        # Host capacity alone cannot grant permission when the Docker VM is full.
        lab.a.preflight_scope='clean-recovery'
        lab.resource_check=lambda **kwargs:{'estimated_required_bytes':1024*1024**2,
                                            'estimated_stopped_container_release_bytes':2*1024*1024**2}
        with self.assertRaises(RuntimeError):lab.preflight()
        self.assertEqual(lab.result['preflight']['status'],'FAILED')

    def test_preflight_refuses_unknown_docker_capacity(self):
        lab=object.__new__(controller.Lab);lab.result={};lab.a=types.SimpleNamespace(preflight_scope='web-control')
        lab.local_inputs=lambda **kwargs:{};lab.capture=lambda:(self.schema,[])
        lab.http=lambda *args:(200,{'total':0,'orders':[]})
        lab.sql=lambda *args,**kwargs:'GRANT SELECT, INSERT ON `lab_config`.`orders` TO `group08_app`@`%`'
        lab.source=lambda *args,**kwargs:'Filesystem Available\n'
        with self.assertRaises(ValueError):lab.preflight()
        self.assertEqual(lab.result['preflight']['status'],'FAILED')

    def direct_resource_lab(self, action, available_kib):
        """Fake Docker/HTTP metadata, keeping the real source/resource gates."""
        lab=object.__new__(controller.Lab)
        lab.rid='p3-resource-fixture'
        lab.a=types.SimpleNamespace(action=action,release_source_containers=True)
        lab.result={'status':'FAILED'};lab.source_touched=False;lab.target_created=False
        lab.source_port=lambda:8080
        lab.http=MagicMock(return_value=(200,{'status':'ok','database':'ok','orders_count':108}))
        lab.local_inputs=lambda **kwargs:{'credential_files':'fixture only'}
        def inspect(name):
            service='db' if name.endswith('db-1') else 'web'
            return {'Id':'fixture-'+service,'Config':{'Labels':{'com.docker.compose.project':'group08-lab','com.docker.compose.service':service}},
                    'State':{'Running':True},'Mounts':[{'Destination':'/var/lib/mysql','Name':'group08-lab_db_data'}],
                    'NetworkSettings':{'Ports':{'8000/tcp':[{'HostIp':'127.0.0.1','HostPort':'8080'}]}}}
        lab.inspect=inspect
        events=[];lab.event=lambda name,**kwargs:events.append(name)
        def call(command,*args,**kwargs):
            if 'df' in command:
                return ('Filesystem 1024-blocks Used Available Capacity Mounted on\n'
                        f'fixture 9999999 1 {available_kib[0]} 1% /var/lib/mysql\n'
                        f'fixture 9999999 1 {available_kib[1]} 1% /\n')
            if command[:2]==['docker','info']:return 'vfs'
            if '--format' in command:return str((512 if 'mysql:8.4.7' in command else 128)*1024**2)
            return '[]'
        lab.call=MagicMock(side_effect=call)
        for name in ['create_order','stop_source','backup','recover','receipt']:
            setattr(lab,name,MagicMock(side_effect=AssertionError('Mutation reached during blocked fixture')))
        return lab,events

    def test_direct_restore_and_drill_reject_full_docker_before_mutation(self):
        for action in ['restore','drill']:
            for capacity in [(1,2097152),(2097152,1)]:
                with self.subTest(action=action,capacity=capacity),tempfile.TemporaryDirectory() as tmp:
                    lab,events=self.direct_resource_lab(action,capacity);lab.work=Path(tmp)
                    argv=['controller.py',action,'--run-id','p3-resource-fixture','--release-source-containers']
                    with patch.object(controller,'Lab',return_value=lab), \
                         patch.object(controller,'controller_lock',return_value=nullcontext()), \
                         patch.object(controller.subprocess,'check_output',return_value='fixture-id'), \
                         patch.object(controller.sys,'argv',argv), \
                         patch.object(controller.shutil,'disk_usage',return_value=types.SimpleNamespace(free=8*1024**3)), \
                         redirect_stdout(io.StringIO()):
                        self.assertEqual(controller.main(),1)
                    self.assertEqual(lab.result['status'],'FAILED')
                    self.assertIn('Docker filesystem space',lab.result['error'])
                    self.assertFalse(lab.source_touched or lab.target_created)
                    for name in ['create_order','stop_source','backup','recover','receipt']:
                        getattr(lab,name).assert_not_called()
                    self.assertIn('DOCKER_RESOURCE_CHECK',events)
                    self.assertTrue((lab.work/'result.json').exists())

    def test_direct_restore_and_drill_accept_measured_sufficient_docker_space(self):
        for action in ['restore','drill']:
            with self.subTest(action=action):
                lab,events=self.direct_resource_lab(action,(2097152,2097152))
                with patch.object(controller.shutil,'disk_usage',return_value=types.SimpleNamespace(free=8*1024**3)):
                    lab.validate_source()
                self.assertIn('DOCKER_RESOURCE_CHECK',events)
                self.assertEqual(len(lab.result['docker_filesystems']),2)
                self.assertFalse(lab.source_touched or lab.target_created)

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
