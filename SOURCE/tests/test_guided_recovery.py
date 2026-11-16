"""Interactive protocol tests with mocked Docker/HTTP; never a real rehearsal."""
from contextlib import nullcontext, redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'recovery'))
import controller


class GuidedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        args=types.SimpleNamespace(run_id='p4-guided-fixture',port=8080,action='drill',
                                  guided=True,post_orders=1,release_source_containers=False,return_source=True)
        with patch.object(controller,'WORK',Path(self.tmp.name)):
            self.lab=controller.Lab(args)
        lab=self.lab;lab.source_port=lambda:8080
        self.rows=[[1,'LAB-PRE','Pen',1,25000,'2026-01-01T00:00:00.000000Z'],
                   [2,'LAB-POST','Pen',1,25000,'2026-01-01T00:00:00.000000Z']]
        self.counter=iter(range(1,100))
        def order(alias,port,request_id):
            i=next(self.counter);row=self.rows[i-1]
            return {'request_id':request_id,'alias':row[1],'row':row,'sent_ns':i*10,'ack_ns':i*10+1}
        lab.create_order=MagicMock(side_effect=order)
        lab.backup=MagicMock(return_value={'dump_metadata':{'business_baseline':{'fixture':True}}})
        lab.preflight_target=MagicMock();lab.recovery_resource_check=MagicMock()
        def stop(fault=False):
            lab.source_touched=True;lab.t0=100
            lab.event('FAULT_REQUESTED');lab.event('FAULT_DETECTED')
        lab.stop_source=MagicMock(side_effect=stop)
        def recover(receipt):
            lab.result['write_probe']=self.rows[1];lab.event('TARGET_CLEANUP',status='PASS')
            return self.rows[:1]
        lab.recover=MagicMock(side_effect=recover)
        lab.capture=MagicMock(return_value=('fixture',self.rows))
        lab.verify_api=MagicMock();lab.stable_health=MagicMock()

    def events(self):
        return [json.loads(line) for line in (self.lab.work/'events.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_correct_handover_waits_for_comparison_and_browser_before_ready(self):
        answers=[x+' '+self.lab.rid for x in ['INJECT','RECOVER','WEB_OK']]
        with patch('builtins.input',side_effect=answers),patch.object(controller,'compare'),redirect_stdout(io.StringIO()):
            self.lab.drill()
        events=self.events();names=[e['event'] for e in events]
        confirmations=[e['action'] for e in events if e['event']=='OPERATOR_CONFIRMED']
        self.assertEqual(confirmations,['INJECT','RECOVER','WEB_OK'])
        self.assertLess(names.index('REQUEST_COMPARISON_FINISHED'),names.index('FINAL_DATA_VERIFIED'))
        self.assertLess(names.index('FINAL_DATA_VERIFIED'),names.index('SERVICE_VERIFIED'))
        self.lab.recovery_resource_check.assert_called_once()
        self.lab.stable_health.assert_called_once_with(8080,2)

    def test_wrong_confirmation_stops_dependent_actions(self):
        for stage in range(3):
            with self.subTest(stage=stage):
                self.setUp()
                answers=[x+' '+self.lab.rid for x in ['INJECT','RECOVER','WEB_OK'][:stage]]+['ACCIDENTAL-SECRET']
                with patch('builtins.input',side_effect=answers),patch.object(controller,'compare'),redirect_stdout(io.StringIO()):
                    with self.assertRaises(ValueError):self.lab.drill()
                if stage==0:self.lab.stop_source.assert_not_called()
                if stage<=1:self.lab.recover.assert_not_called()
                self.lab.stable_health.assert_not_called()
                self.assertNotIn('ACCIDENTAL-SECRET',(self.lab.work/'events.jsonl').read_text(encoding='utf-8'))
                self.assertFalse(any(e['event']=='SERVICE_VERIFIED' for e in self.events()))

    def test_capacity_changed_while_waiting_prevents_fault(self):
        self.lab.recovery_resource_check.side_effect=RuntimeError('disk full')
        with patch('builtins.input',return_value='INJECT '+self.lab.rid),redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError):self.lab.drill()
        self.lab.stop_source.assert_not_called()

    def test_changed_data_after_browser_confirmation_cannot_finish(self):
        answers=[x+' '+self.lab.rid for x in ['INJECT','RECOVER','WEB_OK']]
        with patch('builtins.input',side_effect=answers),patch.object(controller,'compare',side_effect=ValueError('data changed')),redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):self.lab.drill()
        self.lab.stable_health.assert_not_called()

    def test_eof_and_keyboard_abort_keep_result_and_return_source(self):
        for error in [EOFError(),KeyboardInterrupt()]:
            with self.subTest(error=type(error).__name__):
                self.setUp();lab=self.lab
                lab.validate_source=MagicMock();lab.call=MagicMock();lab.source_touched=True
                lab.drill=MagicMock(side_effect=error);lab.return_source=MagicMock()
                argv=['controller.py','drill','--run-id',lab.rid,'--guided','--return-source']
                with patch.object(controller,'Lab',return_value=lab),patch.object(controller,'controller_lock',return_value=nullcontext()), \
                     patch.object(controller.subprocess,'check_output',return_value='a'*40),patch.object(controller.sys,'argv',argv), \
                     patch.object(controller,'committed_sources'), \
                     patch.object(controller.sys.stdin,'isatty',return_value=True),redirect_stdout(io.StringIO()):
                    self.assertEqual(controller.main(),1)
                self.assertEqual(lab.result['status'],'ABORTED');lab.return_source.assert_called_once()
                self.assertTrue((lab.work/'evidence-manifest.json').is_file())

    def test_guided_refuses_piped_input_before_docker(self):
        with patch.object(controller.sys,'argv',['controller.py','drill','--run-id','p4-test','--guided']), \
             patch.object(controller.sys.stdin,'isatty',return_value=False),patch.object(controller.subprocess,'check_output') as docker,redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):controller.main()
        docker.assert_not_called()

    def test_interrupt_during_post_records_uncertain_without_retry(self):
        lab=self.lab;lab.http=MagicMock(side_effect=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            controller.Lab.create_order(lab,'LAB-INTERRUPT',8080,'interrupted-write')
        lab.http.assert_called_once()
        self.assertEqual([e['event'] for e in self.events()],['REQUEST_SENT','REQUEST_UNCERTAIN'])

    def test_crlf_source_cannot_be_hidden_by_clean_git_diff(self):
        import hashlib
        with patch.object(controller.subprocess,'check_output',return_value=b'line\n'):
            with self.assertRaises(ValueError):
                controller.committed_sources('a'*40,{'fixture.py':hashlib.sha256(b'line\r\n').hexdigest()})

    def test_manifest_never_includes_sql_or_secrets(self):
        lab=self.lab
        (lab.work/'database.sql').write_text('PRIVATE SQL')
        (lab.work/'secret.txt').write_text('PRIVATE SECRET')
        controller.write_json(lab.work/'result.json',lab.result)
        lab.event('FIXTURE',operator='Minh Quân');lab.seal_evidence()
        manifest=json.loads((lab.work/'evidence-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(set(manifest['files']),{'result.json','events.jsonl'})
        self.assertNotIn(b'\r\n',(lab.work/'events.jsonl').read_bytes())


if __name__=='__main__':unittest.main()
