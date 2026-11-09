#!/bin/sh
# Linux counterpart of backup.ps1. Requires host Python3 for secrets/run IDs.
set -eu
umask 077
export BACKUP_UID="${BACKUP_UID:-$(id -u)}" BACKUP_GID="${BACKUP_GID:-$(id -g)}"
cd "$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
dc() { docker compose -f compose.yaml -f compose.backup.yaml "$@"; }
new_id() { printf 'p2-%s-%s' "$(date -u +%Y%m%dT%H%M%SZ)" "$(python3 -c 'import secrets; print(secrets.token_hex(6))')"; }
copy_inputs() {
    dc cp SOURCE/backup/db_dump.sh db:/tmp/group08_phase2_db.sh
    dc cp secrets/db_backup_password.txt "db:/tmp/group08-$1.secret"
}
case "${1:-backup}" in
setup)
    python3 - <<'PY'
from pathlib import Path
import secrets,re
assert Path('secrets/db_root_password.txt').is_file(), 'Run Phase 1 setup first'
for name in ['db_backup_password.txt','restic_password.txt']:
    p=Path('secrets')/name
    if not p.exists():
        assert name!='restic_password.txt' or not Path('backups/restic/config').exists(), 'Recover original repository password'
        with p.open('x') as f:f.write(secrets.token_hex(32))
    assert re.fullmatch('[a-f0-9]{64}',p.read_text()), 'Refusing to replace unexpected credential'
    p.chmod(0o644)
Path('backups/runs').mkdir(parents=True,exist_ok=True)
PY
    if [ "${PHASE2_SKIP_BUILD:-0}" != 1 ]; then dc build backup; fi
    id=$(new_id)
    trap 'dc exec -T db sh /tmp/group08_phase2_db.sh cleanup "$id"' EXIT
    copy_inputs "$id"
    dc exec -T db sh /tmp/group08_phase2_db.sh provision "$id"
    if [ -f backups/restic/config ]; then dc run --rm --no-deps backup check
    else dc run --rm --no-deps backup init; fi
    ;;
backup)
    [ -f backups/restic/config ] || { echo 'Run setup first' >&2; exit 2; }
    id=$(new_id)
    run="backups/runs/$id"
    mkdir -p backups/runs
    mkdir "$run"
    mkdir "$run/payload"
    phase=dump_or_copy
    cleanup() {
        code=$?
        if [ "$code" -ne 0 ] && [ ! -f "$run/result.json" ]; then
            printf '{"run_id":"%s","status":"FAILED","phase":"%s","snapshot_id":null}\n' "$id" "$phase" > "$run/result.json"
        fi
        dc exec -T db sh /tmp/group08_phase2_db.sh cleanup "$id" || true
        exit "$code"
    }
    trap cleanup EXIT
    copy_inputs "$id"
    dc exec -T db sh /tmp/group08_phase2_db.sh dump "$id"
    for file in database.sql metadata.json; do dc cp "db:/tmp/group08-$id/$file" "$run/payload/$file"; done
    phase=backup_container
    dc run --rm --no-deps backup snapshot --run-id "$id"
    ;;
verify) dc run --rm --no-deps backup verify --run-id "${2:?Run ID required}";;
snapshots|check) dc run --rm --no-deps backup "$1";;
*) echo 'Usage: backup.sh setup|backup|snapshots|check|verify RUN_ID' >&2; exit 2;;
esac
