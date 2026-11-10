"""Canonical orders and strict identifiers shared by recovery/drill tools."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with Path(path).open('rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def run_id(value):
    if not re.fullmatch(r'p[34]-[a-z0-9-]{1,40}', value):
        raise ValueError('Expected a fresh lowercase p3-/p4- run ID')
    return value


def full_snapshot(value):
    if not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('A full 64-character snapshot ID is required; latest is forbidden')
    return value


def normalize_schema(value):
    value = re.sub(r' AUTO_INCREMENT=\d+', '', value).strip()
    # MySQL can add a redundant column CHARACTER SET after a dump round-trip.
    # Only omit it when it equals the table charset AND an explicit collation
    # of that charset remains. Different charsets/collations are still compared.
    charset = re.search(r' DEFAULT CHARSET=([A-Za-z0-9_]+)', value)
    if charset:
        name = re.escape(charset[1])
        value = re.sub(r' CHARACTER SET '+name+r'(?= COLLATE '+name+r'_[A-Za-z0-9_]+)', '', value)
    return value


def rows_hash(rows):
    previous = -1
    h = hashlib.sha256()
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError('Expected all six orders columns')
        if any(type(row[i]) is not int for i in [0, 3, 4]) or row[0] <= previous:
            raise ValueError('Rows must use exact integers and increasing unique IDs')
        if any(not isinstance(row[i], str) for i in [1, 2, 5]):
            raise ValueError('Invalid text/timestamp column')
        if re.fullmatch(r'LAB-[A-Z0-9-]{1,32}',row[1]) is None or row[2] not in ['Notebook','Pen','Folder']:
            raise ValueError('Only the Group08 synthetic order dataset is supported')
        if not 1<=row[3]<=100 or not 1<=row[4]<=100000000:
            raise ValueError('Order values are outside the fixed lab contract')
        datetime.strptime(row[5], '%Y-%m-%dT%H:%M:%S.%fZ')
        previous = row[0]
        h.update(encode(row) + b'\n')
    return h.hexdigest()


def baseline_for(schema, rows):
    schema = normalize_schema(schema)
    if 'ENGINE=InnoDB' not in schema or '`orders`' not in schema:
        raise ValueError('Expected the InnoDB orders schema')
    return {'schema_version': 1, 'canonicalization': 'orders-jsonl-v1',
            'row_count': len(rows), 'rows_sha256': rows_hash(rows),
            'schema': schema, 'schema_sha256': digest(schema.encode('utf-8'))}


def compare(schema, rows, expected, probe=None):
    current = baseline_for(schema, rows if probe is None else [r for r in rows if r[0] != probe[0]])
    if current != expected:
        raise ValueError('Restored schema or full dataset differs from source baseline')
    if probe is not None:
        if [r for r in rows if r[0] == probe[0]] != [probe] or len(rows) != expected['row_count'] + 1:
            raise ValueError('Write probe missing/changed or unexpected rows present')


def canonical_api(row):
    stamp = datetime.fromisoformat(row['created_at_utc'].replace('Z', '+00:00'))
    if stamp.utcoffset() != timezone.utc.utcoffset(stamp):
        raise ValueError('Expected a UTC API timestamp')
    return [row['id'], row['customer_alias'], row['product_name'], row['quantity'],
            row['unit_price_vnd'], stamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ')]


def acknowledged_comparison(acknowledgements, rows, fault_ns):
    recovered, missing, duplicates = [], [], []
    for ack in acknowledgements:
        matches = [r for r in rows if r[1] == ack['alias']]
        if len(matches) > 1:
            duplicates.append(ack['request_id'])
        if matches == [ack['row']]:
            recovered.append(ack)
        else:
            missing.append(ack['request_id'])
    sequence = [ack['request_id'] for ack in acknowledgements]
    recovered_ids = [ack['request_id'] for ack in recovered]
    prefix = recovered_ids == sequence[:len(recovered_ids)]
    lag = None
    if recovered and prefix and not duplicates:
        last = recovered[-1]
        lag = {'lower_seconds': (fault_ns-last['ack_ns'])/1e9,
               'upper_seconds': (fault_ns-last['sent_ns'])/1e9,
               'meaning': 'bounds on age of last recovered commit from client send/ack; not exact RPO'}
    return {'recovered_requests': recovered_ids, 'unrecovered_acknowledged': missing,
            'duplicates': duplicates, 'recovered_prefix': prefix, 'recovered_commit_age_bounds': lag}
