import pytest
from fastapi.testclient import TestClient
from http_server.routers import users
from http_server.server import createApp

client = TestClient(createApp("localhost", 6379, "dev"))

def test_register_empty_user_name_error():
    response = client.post(
        "/users",
        data={
            "user_name": "",
            "password": "password"
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": "Password can't be empty!"}
