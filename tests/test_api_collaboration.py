from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"]
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint():
    response = client.get("/version")

    assert response.status_code == 200

    data = response.json()

    assert data["service"]
    assert data["version"] == "1.0.0"


def test_api_info_endpoint():
    response = client.get("/api/v1/info")

    assert response.status_code == 200

    data = response.json()

    assert data["service"]
    assert data["version"] == "1.0.0"
    assert "kubernetes-triage" in data["features"]
    assert "incident-analysis" in data["features"]
    assert "prometheus-metrics" in data["features"]
