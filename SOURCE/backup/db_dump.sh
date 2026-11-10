#!/bin/sh
# Executed inside the existing lab DB. Passwords are read from files, never argv.
set -eu
umask 077
action=${1:-}
run_id=${2:-}
case "$run_id" in ''|*[!A-Za-z0-9_-]*) echo 'Invalid run ID' >&2; exit 2;; esac
case "$run_id" in p2-*) ;; *) echo 'Expected p2- run ID' >&2; exit 2;; esac
[ ${#run_id} -le 80 ] || exit 2
stage="/tmp/group08-$run_id"
secret="/tmp/group08-$run_id.secret"
if [ "$action" = cleanup ]; then
    rm -f "$stage/client.cnf" "$stage/database.sql.part" "$stage/database.sql" "$stage/metadata.json" "$secret"
    if [ -d "$stage" ]; then rmdir "$stage"; fi
    exit 0
fi
[ ! -e "$stage" ] && [ ! -L "$stage" ] || { echo 'Staging path already exists' >&2; exit 2; }
mkdir -m 700 "$stage"
trap 'rm -f "$stage/client.cnf" "$secret"' EXIT
chmod 600 "$secret"
password=$(cat "$secret")
case "$password" in ''|*[!a-f0-9]*) echo 'Invalid backup credential format' >&2; exit 2;; esac
[ ${#password} -eq 64 ] || exit 2
printf '[client]\nuser=group08_backup\npassword=%s\nhost=127.0.0.1\n' "$password" > "$stage/client.cnf"
if [ "$action" = provision ]; then
    # If credentials already work, validate privileges instead of rotating passwords.
    if ! mysql --defaults-extra-file="$stage/client.cnf" -Nse 'SELECT 1' >/dev/null 2>&1; then
        export MYSQL_PWD="$(cat /run/secrets/db_root_password)"
        mysql -u root <<SQL
CREATE USER 'group08_backup'@'%' IDENTIFIED BY '$password';
GRANT SELECT ON lab_config.orders TO 'group08_backup'@'%';
SQL
        unset MYSQL_PWD
    fi
    mysql --defaults-extra-file="$stage/client.cnf" -Nse 'SHOW GRANTS' | grep -v 'GRANT USAGE ON' > "$stage/grants.txt"
    [ "$(cat "$stage/grants.txt")" = 'GRANT SELECT ON `lab_config`.`orders` TO `group08_backup`@`%`' ] || { echo 'Unexpected backup grants; manual review required' >&2; exit 2; }
    rm "$stage/grants.txt"
    echo 'Backup role provisioned/validated: SELECT only on lab_config.orders'
    rmdir "$stage" 2>/dev/null || true
elif [ "$action" = dump ]; then
    engine=$(mysql --defaults-extra-file="$stage/client.cnf" -Nse "SELECT ENGINE FROM information_schema.tables WHERE TABLE_SCHEMA='lab_config' AND TABLE_NAME='orders'")
    [ "$engine" = InnoDB ] || { echo 'Expected InnoDB orders table' >&2; exit 2; }
    started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    mysqldump --defaults-extra-file="$stage/client.cnf" \
        --single-transaction --quick --skip-lock-tables --no-tablespaces \
        --set-gtid-purged=OFF --skip-triggers --skip-add-drop-table --default-character-set=utf8mb4 \
        --result-file="$stage/database.sql.part" lab_config orders
    [ -s "$stage/database.sql.part" ] || { echo 'Empty dump' >&2; exit 2; }
    finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    mv "$stage/database.sql.part" "$stage/database.sql"
    printf '{"schema_version":1,"run_id":"%s","database":"lab_config","tables":["orders"],"engine":"InnoDB","dump_started_at_utc":"%s","dump_finished_at_utc":"%s","consistency":"mysqldump single-transaction; no DDL during dump","scope":"schema and data of orders only; triggers/routines/events excluded"}\n' "$run_id" "$started" "$finished" > "$stage/metadata.json"
    echo "Completed consistent dump: $run_id"
else
    echo 'Expected provision/dump/cleanup' >&2; exit 2
fi
