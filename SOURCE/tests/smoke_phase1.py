"""HTTP smoke test. Appends one synthetic order; never deletes or resets data.

Run inside web: python /tests/smoke_phase1.py
Optional --base-url http://127.0.0.1:8080 for host Python.
"""
import argparse
import json
import urllib.error
import urllib.request


def run(base_url):
    # Avoid ambient proxy settings for calls to the local lab.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(base_url + path, data=data,
                                     headers={'Content-Type': 'application/json'} if data else {})
        try:
            with opener.open(req, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    status, health = request('/health')
    assert status == 200 and health['status'] == 'ok', (status, health)
    status, listing = request('/api/orders')
    assert status == 200 and listing['total'] >= 100, (status, listing)
    before = listing['total']
    status, invalid = request('/api/orders', {'customer_alias': 'LAB-SMOKE', 'product_name': 'Pen', 'quantity': True, 'unit_price_vnd': 10000})
    assert status == 400, (status, invalid)
    payload = {'customer_alias': 'LAB-SMOKE', 'product_name': 'Pen', 'quantity': 2, 'unit_price_vnd': 12000}
    status, created = request('/api/orders', payload)
    assert status == 201, (status, created)
    order = created['order']
    status, listing = request('/api/orders')
    assert status == 200 and listing['total'] == before + 1, listing
    assert any(row['id'] == order['id'] and all(row[key] == value for key, value in payload.items()) for row in listing['orders'])
    assert order['created_at_utc'].endswith('Z')
    print(json.dumps({'result': 'PASS', 'orders_before': before, 'orders_after': listing['total'], 'created_order_id': order['id'], 'checks': ['DB-backed health', 'list', 'invalid input rejected', 'create', 'readback', 'UTC timestamp']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    run(args.base_url.rstrip('/'))
