from lemonapi.main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_server_status():
    response = client.get("/status/")
    assert response.status_code == 200
    assert response.content ==  "Server is running."

def test_server_metrics():
    response = client.get("/metrics/")
    assert response.status_code == 200
    
