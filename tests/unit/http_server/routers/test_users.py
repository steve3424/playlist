import pytest
from fastapi.testclient import TestClient
from http_server.routers.users import USERNAME_MIN_LEN, USERNAME_MAX_LEN
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

@pytest.mark.skipif((USERNAME_MIN_LEN - 1) == 0, reason=f"Short username will be empty, covered by other test.")
def test_register_empty_user_name_too_short():
    user_name = "a" * (USERNAME_MIN_LEN - 1)
    response = client.post(
        "/users",
        data={
            "user_name": user_name,
            "password": "password"
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": f"Username must be at least {USERNAME_MIN_LEN} characters, but was {len(user_name)}!"}

def test_register_empty_user_name_too_long():
    user_name = "a" * (USERNAME_MAX_LEN + 1)
    response = client.post(
        "/users",
        data={
            "user_name": user_name,
            "password": "password"
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": f"Username can't be longer than {USERNAME_MAX_LEN} characters, but was {len(user_name)}"}
