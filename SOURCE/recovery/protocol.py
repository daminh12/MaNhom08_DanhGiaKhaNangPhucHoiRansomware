"""Versioned evidence contract for new runs; historical evidence stays unchanged."""

AUTOMATED = 'automated-v1'
GUIDED = 'guided-v2'
CODE_FILES = (
    'SOURCE/recovery/controller.py', 'SOURCE/recovery/archive.py',
    'SOURCE/recovery/common.py', 'SOURCE/recovery/protocol.py',
    'SOURCE/recovery/run_lab.ps1', 'SOURCE/backup/backup.py',
    'SOURCE/backup/db_dump.sh', 'SOURCE/app/app.py', 'SOURCE/app/requirements.txt',
    'compose.yaml', 'compose.backup.yaml', 'compose.restore.yaml',
    'compose.recovery-tools.yaml',
)
# Deliberately exclude SQL, secret files and unrestricted Docker inspect output.
EVIDENCE_FILES = (
    'result.json', 'events.jsonl', 'acknowledgements.json', 'backup-receipt.json',
    'observed-baseline.json', 'target-grants.txt',
    'source-dataset.jsonl', 'restored-dataset.jsonl',
    'extracted/manifest.json', 'extracted/payload/metadata.json',
    'extracted/verified.json',
)
