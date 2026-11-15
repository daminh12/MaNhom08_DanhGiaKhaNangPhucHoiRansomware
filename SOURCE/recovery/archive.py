"""Extract exactly one verified Phase 2 payload; executed inside backup image."""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, '/tool')
import backup
from common import full_snapshot, run_id, sha


def extract(backup_id, snapshot_id, expected_digest, restore_id):
    full_snapshot(snapshot_id)
    run_id(restore_id)
    if not re.fullmatch(r'p2-[A-Za-z0-9_-]{1,76}', backup_id):
        raise ValueError('Invalid backup run ID')
    if not re.fullmatch('[0-9a-f]{64}', expected_digest):
        raise ValueError('Invalid trusted manifest digest')
    target = Path('/recovery-work') / restore_id / 'extracted'
    target.mkdir()  # exclusive: never overwrite an old or partial extraction
    log = target / 'restic.log'
    snapshots = json.loads(backup.restic('snapshots', '--json', snapshot_id, log=log))
    if len(snapshots) != 1 or snapshots[0]['id'] != snapshot_id or backup_id not in snapshots[0].get('tags', []):
        raise ValueError('Snapshot ID/tag does not match selected backup run')
    backup.restic('check', '--read-data', log=log)
    prefix = '/data/runs/' + backup_id
    backup.restic('dump', snapshot_id, prefix+'/manifest.json', log=log, output=target/'manifest.json')
    if sha(target/'manifest.json') != expected_digest:
        raise ValueError('Archived manifest differs from trusted receipt')
    manifest = backup.validate_manifest(json.loads((target/'manifest.json').read_text()))
    payload = target/'payload'; payload.mkdir()
    for entry in manifest['files']:
        backup.restic('dump', snapshot_id, prefix+'/payload/'+entry['path'], log=log, output=payload/entry['path'])
    backup.verify_payload(payload, manifest)
    metadata = backup.validate_dump(payload, backup_id)
    baseline = metadata.get('business_baseline')
    if not isinstance(baseline, dict) or baseline.get('schema_version') != 1:
        raise ValueError('Snapshot lacks an independently captured business baseline; full acceptance refused')
    if metadata.get('baseline_sql_sha256') != sha(payload/'database.sql'):
        raise ValueError('Business baseline is not bound to this SQL dump')
    (target/'verified.json').write_text(json.dumps({'snapshot_id':snapshot_id,'manifest_sha256':expected_digest,'status':'PASS'}))
    return {'status':'PASS','snapshot_id':snapshot_id}


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--backup-id',required=True);p.add_argument('--snapshot-id',required=True)
    p.add_argument('--manifest-sha256',required=True);p.add_argument('--restore-id',required=True)
    a=p.parse_args()
    print(json.dumps(extract(a.backup_id,a.snapshot_id,a.manifest_sha256,a.restore_id)))
