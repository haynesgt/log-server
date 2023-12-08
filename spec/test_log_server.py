# test fastapi app

from fastapi.testclient import TestClient
from log_server.api import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_clear():
    response = client.get("/_clear")
    assert response.status_code == 200


def test_save_request():
    i_response = client.get("/i/test")
    assert i_response.status_code == 200

    o_response = client.get("/o/test")
    o_response_json = o_response.json()
    assert o_response.status_code == 200
    assert len(o_response_json["requests"]) == 1
    assert o_response_json["requests"][0]["method"] == "GET"
    assert o_response_json["requests"][0]["path"] == "/i/test"
    assert o_response_json["*"] == []
