"""Optional host Python check against an initialized Phase 2 lab repository.

Creates a deliberately truncated temporary artifact, never modifies real dumps,
SQL data or snapshots. Requires at least one successful backup.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DC = ['docker', 'compose', '-f', 'compose.yaml', '-f', 'compose.backup.yaml']


def main():
    logs = []

    def call(args, expected=0):
        command = DC + ['run', '--rm', '--no-deps'] + args
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
        logs.append({'command': command, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        if expected == 0:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0, 'Invalid input was accepted'
        return result.stdout

    before = json.loads(call(['backup', 'snapshots']))
    successful = [p for p in sorted((ROOT/'backups/runs').glob('*/result.json')) if json.loads(p.read_text()).get('status') == 'PASS']
    assert successful, 'Create a successful backup first'
    good_run = successful[0].parent.name
    call(['backup', 'verify', '--run-id', good_run])
    call(['backup', 'init'], expected=1)
    call(['backup', 'snapshot', '--run-id', good_run], expected=1)
    bad_id = 'p2-negative-' + secrets.token_hex(6)
    run = ROOT/'backups/runs'/bad_id
    (run/'payload').mkdir(parents=True)
    (run/'payload/database.sql').write_text('-- MySQL dump\nTRUNCATED TEST FIXTURE\n')
    original = json.loads((successful[0].parent/'payload/metadata.json').read_text())
    (run/'payload/metadata.json').write_text(json.dumps(original | {'run_id': bad_id}))
    call(['backup', 'snapshot', '--run-id', bad_id], expected=1)
    failed = json.loads((run/'result.json').read_text())
    assert failed['status'] == 'FAILED' and failed['snapshot_id'] is None
    assert not (run/'restic.log').exists(), 'Restic should not run on incomplete dump'
    call(['-e', 'RESTIC_PASSWORD_FILE=/run/secrets/missing', 'backup', 'check'], expected=1)
    after = json.loads(call(['backup', 'snapshots']))
    assert sorted(p['id'] for p in before) == sorted(p['id'] for p in after)
    print(json.dumps({'result':'PASS','checked_at_utc':datetime.now(timezone.utc).isoformat(), 'snapshots_before':len(before),'snapshots_after':len(after), 'good_run_verified':good_run, 'truncated_fixture_run':bad_id, 'checks':['existing snapshot readback', 'init refuses existing repo', 'repeat run refused', 'truncated dump rejected before Restic', 'missing password fails closed', 'negative checks create no snapshots'], 'commands':logs}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
