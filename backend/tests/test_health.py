"""
Smoke test for the /health endpoint.

Acts as a tripwire: if anyone breaks the basic FastAPI wiring, this test
fails immediately in CI, before the change can be merged.
"""

from fastapi.testclient import TestClient

from app.main import app

# `TestClient` spins up the FastAPI app in-process (no real network),
# which makes the test fast and deterministic.
client = TestClient(app)


def test_health() -> None:
    """The endpoint must respond 200 OK with the documented JSON body."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
