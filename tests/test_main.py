from lemonapi.main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def test_server_status():
    response = client.get("/status/")
    assert response.status_code == 200
    assert response.text ==  "Server is running."

def test_server_metrics():
    response = client.get("/metrics/")
    assert response.status_code == 200

def test_home_endpoint():
    root = client.get("/")
    docs = client.get("/docs/")

    assert root.status_code == 200
    assert root.content == docs.content

def test_uknown_endpoint():
    response = client.get("/asldkfalksdjf/")
    assert response.status_code == 404
    
    
