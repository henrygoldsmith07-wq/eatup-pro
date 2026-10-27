import time

import pytest

import api_server
import cleaner
from data.analytics_db import AnalyticsDatabase


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "ROOT_TEMP_DIRS", set())
    monkeypatch.setattr(api_server, "cleaner", None)
    monkeypatch.setattr(api_server, "db", AnalyticsDatabase(tmp_path / "test.db"))
    monkeypatch.setattr(api_server, "scan_jobs", {})
    monkeypatch.setattr(api_server, "latest_scan_id", None)
    monkeypatch.delenv("API_KEY", raising=False)
    (tmp_path / "files").mkdir()
    (tmp_path / "files" / "note.txt").write_text("hello")
    api_server.app.config["TESTING"] = True
    with api_server.app.test_client() as c:
        c.scan_root = str(tmp_path / "files")
        yield c


def wait_for_scan(client, scan_id):
    for _ in range(100):
        status = client.get(f"/api/v1/scan/status/{scan_id}").get_json()
        if status["status"] != "running":
            return status
        time.sleep(0.05)
    pytest.fail("scan did not finish")


def test_health_and_ui(client):
    assert client.get("/api/v1/health").get_json()["status"] == "healthy"
    assert client.get("/app.html").status_code == 200
    assert client.get("/api_server.py").status_code == 404


def test_usage_stats(client):
    assert client.get("/api/v1/usage/stats").get_json()["total_bytes"] > 0


def test_scan_lifecycle(client):
    scan_id = client.post("/api/v1/scan/start", json={"drive": client.scan_root}).get_json()["scan_id"]
    assert wait_for_scan(client, scan_id)["status"] == "complete"
    results = client.get(f"/api/v1/scan/results/{scan_id}").get_json()
    assert results["files_scanned"] == 1
    assert client.get("/api/v1/analytics/scans").get_json()["count"] == 1
    assert client.get("/api/v1/scan/status/unknown").status_code == 404


def test_failed_scan_reports_failure(client):
    scan_id = client.post("/api/v1/scan/start", json={"drive": "/does/not/exist"}).get_json()["scan_id"]
    assert wait_for_scan(client, scan_id)["status"] == "failed"


def test_cleanup_requires_scan_and_json(client):
    assert client.post("/api/v1/cleanup/run", json={"type": "temp"}).status_code == 400
    # A cross-site form post (no JSON content type) must be refused
    assert client.post("/api/v1/cleanup/run", data="type=smart",
                       content_type="text/plain").status_code == 415


def test_scan_start_rejects_invalid_drive(client):
    assert client.post("/api/v1/scan/start", json={"drive": 7}).status_code == 400
    assert client.post("/api/v1/scan/start", json={"drive": "  "}).status_code == 400
    assert client.post("/api/v1/scan/start", json={"drive": client.scan_root}).status_code == 200


def test_cleanup_rejects_bad_min_size(client):
    scan_id = client.post("/api/v1/scan/start", json={"drive": client.scan_root}).get_json()["scan_id"]
    wait_for_scan(client, scan_id)
    assert client.post("/api/v1/cleanup/run", json={"type": "large", "min_size_gb": "big"}).status_code == 400
    assert client.post("/api/v1/cleanup/run", json={"type": "large", "min_size_gb": -2}).status_code == 400
    assert client.post("/api/v1/cleanup/run", json={"type": "large"}).status_code == 200


def test_cleanup_dry_run(client):
    scan_id = client.post("/api/v1/scan/start", json={"drive": client.scan_root}).get_json()["scan_id"]
    wait_for_scan(client, scan_id)
    body = client.post("/api/v1/cleanup/run", json={"type": "smart", "dry_run": True}).get_json()
    assert body["status"] == "preview" and body["files_deleted"] == 0


def test_api_key_enforced(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    assert client.post("/api/v1/cleanup/run", json={}).status_code == 401
    assert client.post("/api/v1/cleanup/run", json={},
                       headers={"X-API-Key": "secret"}).status_code == 400  # No scan yet


def test_foreign_host_rejected(client):
    assert client.get("/api/v1/health", headers={"Host": "evil.example:5000"}).status_code == 403


def test_export_and_analytics(client):
    assert client.get("/api/v1/export/report").status_code == 404
    assert client.get("/api/v1/analytics/statistics").status_code == 200
    assert client.get("/api/v1/analytics/trends").get_json()["data_points"] == 0
