# SHA-256 manifest verifier — synthetic datasets only

This module creates a baseline manifest and verifies an independently restored copy. It does **not** perform backups, simulate malware, or measure application RTO/RPO.

Requires Python 3.10+; standard library only.

From repository root (PowerShell or bash):

    python -m unittest discover -s SOURCE/tests -v
    python SOURCE/verification/verify_hashes.py manifest --root SOURCE/data/synthetic --manifest baseline.sha256.json
    python SOURCE/verification/verify_hashes.py verify --root SOURCE/data/synthetic --manifest baseline.sha256.json

Keep the generated baseline outside the dataset directory; do not commit runtime datasets, backup credentials, or private data.
The CLI returns 0 = PASS, 1 = mismatch, 2 = invalid input / error.
The fixture has only 3 fake records: it is a functional test, not an RTO/RPO experiment.
