import time

import pytest

import api_server
import cleaner
from data.analytics_db import AnalyticsDatabase


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "ROOT_TEMP_DIRS", set())
    monkeypatch.setattr(cleaner, "TEMP_LOCATIONS", ())
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
    assert client.get("/favicon.ico").status_code == 200
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


def test_ai_analyze_uses_the_engine(client):
    body = client.post("/api/v1/ai/analyze", json={
        "files": [{"path": f"{client.scan_root}/note.txt", "size": 5}]
    }).get_json()
    assert body["count"] == 1
    assert 0 <= body["analyses"][0]["safety_score"] <= 1
    assert body["recommendations"][0]["risk_level"] in {"safe", "moderate", "risky"}
    assert "confidence_score" not in body  # no hardcoded placeholder value


def test_ai_analyze_without_files_needs_a_scan(client):
    assert client.post("/api/v1/ai/analyze", json={}).status_code == 404


def test_cloud_connect_is_not_implemented(client):
    for service in ("google-drive", "dropbox"):
        response = client.post(f"/api/v1/cloud/connect/{service}", json={})
        assert response.status_code == 501
        assert response.get_json()["error"] == "Not implemented"


def test_cloud_files_and_stats_are_not_implemented(client):
    assert client.get("/api/v1/cloud/files").status_code == 501
    assert client.get("/api/v1/cloud/stats").status_code == 501


def test_ai_prediction_without_scans(client):
    body = client.get("/api/v1/ai/prediction").get_json()
    assert body["available"] is False
    assert body["success_rate"] is None


def test_latest_scan_endpoint(client):
    assert client.get("/api/v1/scan/latest").status_code == 404
    scan_id = client.post("/api/v1/scan/start", json={"drive": client.scan_root}).get_json()["scan_id"]
    wait_for_scan(client, scan_id)
    latest = client.get("/api/v1/scan/latest").get_json()
    assert latest["files_scanned"] == 1
    assert latest["categories"]["Documents"] >= 0  # serialised in GB


def test_scan_results_without_results(client, monkeypatch):
    monkeypatch.setattr(api_server, "latest_scan_id", "stale-id")
    assert client.get("/api/v1/scan/results/stale-id").status_code == 404


def test_nonlocal_reads_require_api_key(client, monkeypatch):
    remote = {"REMOTE_ADDR": "8.8.8.8"}
    for path in ("/api/v1/scan/latest", "/api/v1/analytics/statistics",
                 "/api/v1/schedule/list"):
        assert client.get(path, environ_base=remote).status_code == 403
    monkeypatch.setenv("API_KEY", "secret")
    assert client.get("/api/v1/analytics/statistics", environ_base=remote,
                      headers={"X-API-Key": "secret"}).status_code == 200


def test_nonlocal_writes_require_api_key(client, monkeypatch):
    remote = {"REMOTE_ADDR": "8.8.8.8"}
    assert client.post("/api/v1/cleanup/run", json={"type": "temp"},
                       environ_base=remote).status_code == 403
    monkeypatch.setenv("API_KEY", "secret")
    assert client.post("/api/v1/cleanup/run", json={"type": "temp"},
                       environ_base=remote,
                       headers={"X-API-Key": "secret"}).status_code == 400  # no scan yet
