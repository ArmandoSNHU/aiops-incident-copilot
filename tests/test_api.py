import json
from pathlib import Path

from fastapi.testclient import TestClient

from aiops.server import app

client = TestClient(app)
SAMPLE = json.loads((Path(__file__).parent.parent / "examples" / "sample_incident.json").read_text())


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_triage_endpoint_returns_ranked_result():
    r = client.post("/triage", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["incident_id"] == "INC-2043"
    assert body["signal_count"] == 5
    assert body["hypotheses"][0]["cause"] == "Database connection pool exhaustion"


def test_metrics_endpoint_exposes_counters():
    client.post("/triage", json=SAMPLE)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "aiops_triage_requests_total" in r.text
