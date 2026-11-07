import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_DB", str(tmp_path / "test.db"))

@pytest.fixture
def client():
    return TestClient(app)

def auth(client, user):
    token = client.post(f"/demo/login/{user}").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
