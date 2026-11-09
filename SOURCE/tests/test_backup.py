"""Phase 2 failure gates and fixed-scope manifest checks (stdlib only)."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path('/tool/backup.py')
if not SOURCE.exists():
    SOURCE = Path(__file__).resolve().parents[1] / 'backup' / 'backup.py'
SPEC = importlib.util.spec_from_file_location('group08_backup', SOURCE)
BACKUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BACKUP)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_id = 'p2-unit'
        self.run = self.root / 'runs' / self.run_id
        self.payload = self.run / 'payload'
        self.payload.mkdir(parents=True)
        (self.payload/'database.sql').write_text('-- MySQL dump\nCREATE TABLE `orders` (id INT);\n-- Dump completed on 2026-01-01\n')
        self.meta = {'schema_version': 1, 'run_id': self.run_id, 'database': 'lab_config', 'tables': ['orders'], 'engine': 'InnoDB', 'dump_started_at_utc': '2026-01-01T00:00:00Z', 'dump_finished_at_utc': '2026-01-01T00:00:01Z'}
        (self.payload/'metadata.json').write_text(json.dumps(self.meta))
        self.manifest = BACKUP.manifest_for(self.payload)
        self.snapshot_id = 'a'*64

    def responses(self):
        return [json.dumps({'message_type':'summary','snapshot_id':self.snapshot_id[:8]}), json.dumps([{'id':self.snapshot_id,'tags':[self.run_id]}]), 'check ok']

    def result(self):
        return json.loads((self.run/'result.json').read_text())

    def test_manifest_matches_then_detects_same_size_modification(self):
        BACKUP.verify_payload(self.payload, self.manifest)
        path=self.payload/'database.sql'
        path.write_bytes(path.read_bytes().replace(b'orders',b'ORDERS'))
        with self.assertRaises(ValueError): BACKUP.verify_payload(self.payload,self.manifest)

    def test_missing_and_extra_files_rejected(self):
        extra=self.payload/'extra'
        extra.touch()
        with self.assertRaises(ValueError): BACKUP.manifest_for(self.payload)
        extra.unlink()
        (self.payload/'database.sql').unlink()
        with self.assertRaises(ValueError): BACKUP.manifest_for(self.payload)

    def test_empty_file_rejected(self):
        (self.payload/'database.sql').write_bytes(b'')
        with self.assertRaises(ValueError): BACKUP.manifest_for(self.payload)

    def test_root_and_child_symlinks_rejected(self):
        link=self.root/'link'
        link.symlink_to(self.payload,target_is_directory=True)
        with self.assertRaises(ValueError): BACKUP.manifest_for(link)
        path=self.payload/'database.sql'; path.unlink();path.symlink_to(self.payload/'metadata.json')
        with self.assertRaises(ValueError): BACKUP.manifest_for(self.payload)

    def test_manifest_top_level_and_paths_rejected(self):
        for invalid in [[],None,42,{}]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError): BACKUP.validate_manifest(invalid)
        for name in ['../database.sql','/database.sql','x\\database.sql','metadata.json']:
            value=copy.deepcopy(self.manifest);value['files'][0]['path']=name
            with self.subTest(name=name), self.assertRaises(ValueError): BACKUP.validate_manifest(value)

    def test_invalid_hash_or_size_rejected(self):
        for changes in [{'sha256':'x'*64},{'size_bytes':True},{'size_bytes':0},{'size_bytes':-1}]:
            value=copy.deepcopy(self.manifest);value['files'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError): BACKUP.validate_manifest(value)

    def test_run_id_cannot_escape_root(self):
        for value in ['../outside','p2-../outside','p2-abc/x','']:
            with self.subTest(value=value), self.assertRaises(ValueError): BACKUP.run_path(self.root,value)

    def test_truncated_dump_never_calls_restic(self):
        (self.payload/'database.sql').write_text('-- MySQL dump\nunfinished')
        with patch.object(BACKUP,'restic') as restic:
            with self.assertRaises(ValueError): BACKUP.snapshot(self.root,self.run_id)
            restic.assert_not_called()
        self.assertEqual(self.result()['status'],'FAILED')
        self.assertIsNone(self.result()['snapshot_id'])

    def test_metadata_timestamp_or_scope_mismatch(self):
        for changes in [{'database':'real_database'},{'engine':'MyISAM'},{'dump_finished_at_utc':'2025-01-01T00:00:00Z'}]:
            (self.payload/'metadata.json').write_text(json.dumps(self.meta|changes))
            with self.subTest(changes=changes), self.assertRaises(ValueError): BACKUP.validate_dump(self.payload,self.run_id)

    def test_restic_nonzero_exit_not_accepted(self):
        with patch.object(BACKUP,'restic',side_effect=RuntimeError('exit 3')):
            with self.assertRaises(RuntimeError): BACKUP.snapshot(self.root,self.run_id)
        self.assertEqual(self.result()['status'],'FAILED')

    def test_repository_check_failure_keeps_snapshot_untrusted(self):
        with patch.object(BACKUP,'restic',side_effect=self.responses()[:2]+[RuntimeError('check failed')]):
            with self.assertRaises(RuntimeError): BACKUP.snapshot(self.root,self.run_id)
        self.assertEqual(self.result()['status'],'FAILED')
        self.assertEqual(self.result()['snapshot_id'],self.snapshot_id)

    def test_readback_mismatch_prevents_success(self):
        with patch.object(BACKUP,'restic',side_effect=self.responses()), patch.object(BACKUP,'readback',side_effect=ValueError('mismatch')):
            with self.assertRaises(ValueError): BACKUP.snapshot(self.root,self.run_id)
        self.assertEqual(self.result()['status'],'FAILED')

    def test_snapshot_success_and_repeated_run_rejected(self):
        with patch.object(BACKUP,'restic',side_effect=self.responses()), patch.object(BACKUP,'readback') as readback:
            result=BACKUP.snapshot(self.root,self.run_id)
            self.assertEqual(result['status'],'PASS')
            readback.assert_called_once()
        with self.assertRaises(ValueError): BACKUP.snapshot(self.root,self.run_id)

    def test_snapshot_wrong_tag_rejected(self):
        with patch.object(BACKUP,'restic',side_effect=[self.responses()[0],json.dumps([{'id':self.snapshot_id,'tags':['other']}])]):
            with self.assertRaises(ValueError): BACKUP.snapshot(self.root,self.run_id)
        self.assertEqual(self.result()['status'],'FAILED')


if __name__ == '__main__': unittest.main()
