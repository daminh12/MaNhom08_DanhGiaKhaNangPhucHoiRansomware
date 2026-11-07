"""Read-only audit of the existing verifier; all mutated fixtures are temporary."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(sys.argv[1]).resolve()
module_path = repo / 'SOURCE/verification/verify_hashes.py'
spec = importlib.util.spec_from_file_location('audited_verifier', module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = []

def check(name, expected, actual, detail=None):
    results.append(dict(name=name, expected=expected, actual=actual,
                        status='PASS' if actual == expected else 'FAIL', detail=detail))

with tempfile.TemporaryDirectory(prefix='group08-phase0-') as temporary:
    base = Path(temporary)
    root = base / 'synthetic'
    root.mkdir()
    sample = root / 'example.csv'
    sample.write_bytes(b'abc')
    manifest = module.manifest_for(root)
    path = base / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')

    def cli(action='verify', dataset=root, manifest_path=path):
        return subprocess.run([sys.executable, str(module_path), action,
                               '--root', str(dataset), '--manifest', str(manifest_path)],
                              capture_output=True, text=True, timeout=10)

    check('known_sha256_abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', manifest['files'][0]['sha256'])
    check('cli_unchanged_exit', 0, cli().returncode)
    sample.write_bytes(b'abd')
    changed = cli()
    check('same_size_change_detected', (1, ['example.csv']), (changed.returncode, json.loads(changed.stdout)['modified']))
    sample.write_bytes(b'abc')
    for label, name in [('parent_traversal', '../outside.csv'), ('absolute', '/outside.csv'), ('backslash', '..\\outside.csv')]:
        invalid = copy.deepcopy(manifest)
        invalid['files'][0]['path'] = name
        path.write_text(json.dumps(invalid), encoding='utf-8')
        check(label + '_exit', 2, cli().returncode)
    invalid = copy.deepcopy(manifest)
    invalid['files'].append(copy.deepcopy(invalid['files'][0]))
    path.write_text(json.dumps(invalid), encoding='utf-8')
    check('duplicate_entry_exit', 2, cli().returncode)
    path.write_text(json.dumps(manifest), encoding='utf-8')
    inside = root / 'manifest.json'
    check('manifest_inside_dataset_exit', 2, cli('manifest', manifest_path=inside).returncode)
    check('manifest_inside_dataset_not_written', False, inside.exists())
    link = root / 'link.csv'
    link.symlink_to(sample)
    check('child_symlink_exit', 2, cli().returncode)
    link.unlink()
    root_link = base / 'root_link'
    root_link.symlink_to(root, target_is_directory=True)
    observed = cli(dataset=root_link)
    check('root_symlink_rejected_exit', 2, observed.returncode, observed.stdout.strip())
    check('missing_root_exit', 2, cli(dataset=base/'absent').returncode)
    path.write_text('{', encoding='utf-8')
    check('malformed_json_exit', 2, cli().returncode)
    path.write_text('[]', encoding='utf-8')
    observed = cli()
    check('non_object_manifest_exit', 2, observed.returncode, observed.stderr.splitlines()[-1])
    empty = base / 'empty'
    empty.mkdir()
    empty_result = module.verify(empty, module.manifest_for(empty))
    check('empty_dataset_current_behavior', True, empty_result['passed'], 'Observation only: must not count this as successful application recovery; no non-empty gate exists.')
    path.write_text(json.dumps(manifest), encoding='utf-8')
    check('fixture_unchanged_after_verification', b'abc'.hex(), sample.read_bytes().hex())

print(json.dumps({'python': sys.version.split()[0], 'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=repo, text=True).strip(), 'checks': results}, ensure_ascii=False, indent=2))
raise SystemExit(1 if any(r['status'] == 'FAIL' for r in results) else 0)
