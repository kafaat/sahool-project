import pytest
from fastapi.testclient import TestClient

# dynamic import based on service
@pytest.fixture
def client():
    # Import app from the service package
    from app.main import app
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
