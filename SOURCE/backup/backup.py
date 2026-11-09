"""Restic + SHA-256 workflow for the fixed Group08 orders lab; stdlib only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


FILES = ('database.sql', 'metadata.json')


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    temp.replace(path)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_directory(path):
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_dir():
        raise ValueError('Expected existing directory with no symlink components')


def run_path(root, run_id):
    if not re.fullmatch(r'p2-[A-Za-z0-9_-]{1,76}', run_id):
        raise ValueError('Invalid run ID')
    safe_directory(root)
    result = root / 'runs' / run_id
    safe_directory(result)
    return result


def manifest_for(payload):
    safe_directory(payload)
    if set(p.name for p in payload.iterdir()) != set(FILES):
        raise ValueError('Payload must contain only database.sql and metadata.json')
    files = []
    for name in FILES:
        path = payload / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
            raise ValueError('Payload must contain nonempty regular files')
        files.append({'path': name, 'size_bytes': path.stat().st_size, 'sha256': sha(path)})
    return {'schema_version': 1, 'hash_algorithm': 'SHA-256', 'files': files}


def validate_manifest(value):
    if not isinstance(value, dict) or value.get('schema_version') != 1 or value.get('hash_algorithm') != 'SHA-256':
        raise ValueError('Invalid manifest format')
    entries = value.get('files')
    if not isinstance(entries, list) or len(entries) != len(FILES):
        raise ValueError('Invalid manifest files')
    if any(not isinstance(e, dict) for e in entries):
        raise ValueError('Invalid manifest entry')
    names = [e.get('path') for e in entries]
    if sorted(str(n) for n in names) != sorted(FILES):
        raise ValueError('Unsafe, missing or duplicate manifest path')
    for entry in entries:
        if type(entry.get('size_bytes')) is not int or entry['size_bytes'] <= 0 or not isinstance(entry.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
            raise ValueError('Invalid hash or size')
    return value


def verify_payload(payload, expected):
    validate_manifest(expected)
    if manifest_for(payload) != expected:
        raise ValueError('SHA-256 integrity mismatch')


def validate_dump(payload, run_id):
    # The completion footer detects empty/truncated copies, not SQL semantic validity.
    with (payload / 'database.sql').open('rb') as stream:
        header = stream.read(512)
        stream.seek(max(0, (payload / 'database.sql').stat().st_size - 1024))
        footer = stream.read()
    if not header.startswith(b'-- MySQL dump') or b'-- Dump completed on ' not in footer:
        raise ValueError('Dump is missing its header or completion footer')
    meta = json.loads((payload / 'metadata.json').read_text(encoding='utf-8'))
    if not isinstance(meta, dict) or meta.get('run_id') != run_id or meta.get('database') != 'lab_config' or meta.get('tables') != ['orders'] or meta.get('engine') != 'InnoDB':
        raise ValueError('Dump metadata does not match fixed lab scope')
    start = datetime.fromisoformat(meta['dump_started_at_utc'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(meta['dump_finished_at_utc'].replace('Z', '+00:00'))
    if start.utcoffset() is None or end.utcoffset() is None or end < start:
        raise ValueError('Invalid dump timestamps')
    return meta


def restic(*args, log=None, output=None):
    command = ['restic', *args]
    if output is not None:
        with output.open('xb') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, timeout=600)
        text = result.stderr.decode('utf-8', errors='replace')
    else:
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
        text = result.stdout + result.stderr
    if log:
        with log.open('a', encoding='utf-8') as stream:
            stream.write(f'[{utc()}] $ {" ".join(command)}\n{text}\nexit_code={result.returncode}\n')
    if result.returncode:
        raise RuntimeError(f'Restic command failed (exit {result.returncode}); inspect local log')
    return result.stdout if output is None else None


def readback(snapshot_id, archive_path, expected, log=None):
    validate_manifest(expected)
    if not re.fullmatch('[0-9a-f]{64}', snapshot_id):
        raise ValueError('Use a full snapshot ID')
    with tempfile.TemporaryDirectory(prefix='group08-readback-') as directory:
        target = Path(directory)
        for entry in expected['files']:
            restic('dump', snapshot_id, archive_path + '/' + entry['path'], log=log, output=target / entry['path'])
        verify_payload(target, expected)
        # The manifest was itself stored outside payload to avoid self-hashing.
        restic('dump', snapshot_id, archive_path.rsplit('/', 1)[0] + '/manifest.json', log=log, output=target / 'archived-manifest.json')
        archived = json.loads((target / 'archived-manifest.json').read_text())
        if validate_manifest(archived) != expected:
            raise ValueError('Archived manifest differs from trusted baseline')


def snapshot(root, run_id):
    run = run_path(root, run_id)
    result_file = run / 'result.json'
    if result_file.exists():
        raise ValueError('Run already has a result; use a new run ID')
    # Exclusive marker prevents accidental concurrent processing of the same run.
    with (run / '.processing').open('x'):
        pass
    log = run / 'restic.log'
    result = {'schema_version': 1, 'run_id': run_id, 'status': 'FAILED', 'started_at_utc': utc(), 'snapshot_id': None}
    try:
        payload = run / 'payload'
        expected = manifest_for(payload)
        result['dump_metadata'] = validate_dump(payload, run_id)
        write_json(run / 'manifest.json', expected)
        result['manifest_sha256'] = sha(run / 'manifest.json')
        # Snapshot only the explicit artifact, not result/log/credentials.
        raw = restic('backup', '--json', '--host', 'group08-lab', '--tag', 'group08-orders', '--tag', run_id,
                     str(payload), str(run / 'manifest.json'), log=log)
        summaries = [j for line in raw.splitlines() if (j := json.loads(line)).get('message_type') == 'summary']
        if len(summaries) != 1 or not summaries[0].get('snapshot_id'):
            raise ValueError('Restic did not report a snapshot ID')
        short_id = summaries[0]['snapshot_id']
        snapshots = json.loads(restic('snapshots', '--json', short_id, log=log))
        if len(snapshots) != 1 or run_id not in snapshots[0].get('tags', []):
            raise ValueError('Snapshot selection does not match run')
        result['snapshot_id'] = snapshots[0]['id']
        restic('check', '--read-data', log=log)
        readback(result['snapshot_id'], str(payload), expected, log)
        # Recheck local source to reject changes during backup/check/readback.
        verify_payload(payload, expected)
        result.update(status='PASS', verified_at_utc=utc(), repository_check='PASS', snapshot_readback_sha256='PASS')
    except Exception as exc:
        result['error_type'] = type(exc).__name__
        result['error'] = str(exc)
        raise
    finally:
        result['finished_at_utc'] = utc()
        write_json(result_file, result)
        (run / '.processing').unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'snapshot', 'snapshots', 'check', 'verify'])
    parser.add_argument('--run-id')
    args = parser.parse_args()
    root = Path(os.environ.get('LAB_BACKUP_ROOT', '/data'))
    if args.action == 'init':
        safe_directory(root)
        repository = Path(os.environ['RESTIC_REPOSITORY'])
        if repository.exists() and (repository.is_symlink() or any(repository.iterdir())):
            raise ValueError('Repository path must be new/empty; init never overwrites or repairs')
        print(restic('init'))
    elif args.action == 'snapshot':
        print(json.dumps(snapshot(root, args.run_id or ''), indent=2))
    elif args.action == 'verify':
        run = run_path(root, args.run_id or '')
        result = json.loads((run / 'result.json').read_text())
        if result.get('status') != 'PASS' or sha(run / 'manifest.json') != result['manifest_sha256']:
            raise ValueError('Run is not trusted/verified or baseline digest changed')
        expected = validate_manifest(json.loads((run / 'manifest.json').read_text()))
        restic('check', '--read-data', log=run / 'verify.log')
        readback(result['snapshot_id'], str(run / 'payload'), expected, run / 'verify.log')
        print(json.dumps({'status': 'PASS', 'run_id': args.run_id, 'snapshot_id': result['snapshot_id'], 'verified_at_utc': utc()}))
    else:
        print(restic('snapshots', '--json') if args.action == 'snapshots' else restic('check', '--read-data'))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ERROR ({type(exc).__name__}): {exc}')
        raise SystemExit(1)
