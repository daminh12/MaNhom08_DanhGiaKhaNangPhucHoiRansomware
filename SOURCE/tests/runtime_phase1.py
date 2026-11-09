"""Optional host-side integration check: topology, restart persistence and health.

Requires host Python 3.10+ and Docker Compose, with group08-lab already healthy.
Temporarily stops the lab DB and restarts it in finally. Does not delete data.
"""
import argparse
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


REPO = Path(__file__).resolve().parents[2]


def compose(*args):
    command = ["docker", "compose", *args]
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, timeout=210)
    print("$ " + " ".join(command), flush=True)
    print(result.stdout + result.stderr, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"Compose failed with exit {result.returncode}")
    return result.stdout.strip()


def inspect(kind, identity):
    return json.loads(subprocess.check_output(["docker", kind, "inspect", identity], text=True))[0]


def run(base_url):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(path):
        try:
            with opener.open(base_url + path, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    db = inspect("container", compose("ps", "-q", "db"))
    web = inspect("container", compose("ps", "-q", "web"))
    for container in (db, web):
        assert container["Config"]["Labels"]["com.docker.compose.project"] == "group08-lab", "Unexpected project"
    assert not any(db["HostConfig"].get("PortBindings", {}).values()), "DB must not publish host ports"
    bindings = web["NetworkSettings"]["Ports"]["8000/tcp"]
    assert bindings and all(item["HostIp"] == "127.0.0.1" for item in bindings)
    db_networks = db["NetworkSettings"]["Networks"]
    assert len(db_networks) == 1
    assert inspect("network", next(iter(db_networks)))["Internal"] is True
    assert len(web["NetworkSettings"]["Networks"]) == 2
    assert web["Config"]["User"] == "10001:10001"
    assert web["HostConfig"]["ReadonlyRootfs"] is True
    status, before = get("/api/orders")
    assert status == 200 and before["total"] >= 100
    compose("restart")
    compose("up", "-d", "--no-build", "--wait", "--wait-timeout", "180")
    status, after = get("/api/orders")
    assert status == 200 and before == after, "Data changed across restart; avoid concurrent writes during test"
    print("PASS: topology, non-root/read-only web, and exact API data persisted across restart", flush=True)
    try:
        compose("stop", "db")
        status, health = get("/health")
        assert status == 503 and health == {"status": "unavailable", "database": "unavailable"}, health
        status, listing = get("/api/orders")
        assert status == 503 and "error" in listing, listing
        print("PASS: health and orders API return 503 while DB is stopped", flush=True)
    finally:
        compose("up", "-d", "--no-build", "--wait", "--wait-timeout", "180", "db")
    status, health = get("/health")
    assert status == 200 and health["orders_count"] == before["total"], health
    compose("up", "-d", "--no-build", "--wait", "--wait-timeout", "180")
    print(json.dumps({"result": "PASS", "orders_before": before["total"], "orders_after": health["orders_count"],
                      "checks": ["localhost web binding", "DB no host port", "DB internal network only", "web non-root/read-only", "restart persistence", "DB-down health/API 503", "DB-up health 200"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = parser.parse_args()
    run(args.base_url.rstrip("/"))
