import pytest
from fastapi.testclient import TestClient
from http_server.routers.users import USERNAME_MIN_LEN, USERNAME_MAX_LEN, PASSWORD_MIN_LEN, PASSWORD_MAX_LEN
from http_server.server import createApp

client = TestClient(createApp("localhost", 6379, "dev"))

def test_register_user_name_too_short():
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

def test_register_user_name_too_long():
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

def test_register_password_too_short():
    user_name = "a" * (USERNAME_MIN_LEN + 1)
    password = "a" * (PASSWORD_MIN_LEN - 1)
    response = client.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": f"Password must be at least {PASSWORD_MIN_LEN} characters, but was {len(password)}!"}

def test_register_password_too_long():
    user_name = "a" * (USERNAME_MIN_LEN + 1)
    password = "a" * (PASSWORD_MAX_LEN + 1)
    response = client.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": f"Password can't be longer than {PASSWORD_MAX_LEN} characters, but was {len(password)}"}

def test_username_and_password_constraints():
    assert 0 < USERNAME_MIN_LEN
    assert USERNAME_MIN_LEN < USERNAME_MAX_LEN
    assert 0 < PASSWORD_MIN_LEN
    assert PASSWORD_MIN_LEN < PASSWORD_MAX_LEN
