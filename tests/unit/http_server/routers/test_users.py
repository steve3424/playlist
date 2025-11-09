import logging
import pytest
import pytest_asyncio
import os
import random
import string
from pathlib import Path
from fastapi.testclient import TestClient
from http_server.routers.users import USERNAME_MIN_LEN, USERNAME_MAX_LEN, PASSWORD_MIN_LEN, PASSWORD_MAX_LEN
from http_server.server import createApp
from http_server.data import db
from http_server.middlewares.authorization.models import User
from unittest.mock import patch, AsyncMock

LOGGER = logging.getLogger(f"playlist.{__name__}")
CLIENT = TestClient(createApp("localhost", 6379, "dev"), raise_server_exceptions=False)

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup():
    LOGGER.info("Setting up...")
    os.environ["DB_NAME"] = "unittest.db"
    test_db_path = Path(os.path.dirname(db.__file__)) / os.environ["DB_NAME"]
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    await db.init()

    yield

    LOGGER.info("Tearing down...")
    os.remove(test_db_path)

def test_username_and_password_constraints():
    assert 0 < USERNAME_MIN_LEN
    assert USERNAME_MIN_LEN < USERNAME_MAX_LEN
    assert 0 < PASSWORD_MIN_LEN
    assert PASSWORD_MIN_LEN < PASSWORD_MAX_LEN

def test_register_user_name_too_short():
    user_name = "a" * (USERNAME_MIN_LEN - 1)
    response = CLIENT.post(
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
    response = CLIENT.post(
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
    response = CLIENT.post(
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
    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )
    assert response.status_code == 422
    assert response.json() == {"message": f"Password can't be longer than {PASSWORD_MAX_LEN} characters, but was {len(password)}"}

@patch("http_server.middlewares.authentication.sessionCreate", new_callable=AsyncMock)
@patch("http_server.middlewares.authentication.sessionDelete", new_callable=AsyncMock)
def test_register_user_name_password_good(*args):
    user_name = "a" * (USERNAME_MIN_LEN + 1)
    password = "a" * (PASSWORD_MIN_LEN + 1)
    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == user_name

@patch("http_server.middlewares.authentication.sessionCreate", new_callable=AsyncMock)
@patch("http_server.middlewares.authentication.sessionDelete", new_callable=AsyncMock)
def test_register_user_name_password_min_len(*args):
    user_name = "a" * USERNAME_MIN_LEN
    password = "a" * PASSWORD_MIN_LEN
    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == user_name

@patch("http_server.middlewares.authentication.sessionCreate", new_callable=AsyncMock)
@patch("http_server.middlewares.authentication.sessionDelete", new_callable=AsyncMock)
def test_register_user_name_password_max_len(*args):
    user_name = "a" * USERNAME_MAX_LEN
    password = "a" * PASSWORD_MAX_LEN
    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == user_name

@pytest.mark.asyncio
async def test_register_user_name_already_exists():
    user_name = "".join(random.choices(string.ascii_letters, k=USERNAME_MAX_LEN))
    password = "password"
    await db.userAdd(user_name, password)

    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )

    assert response.status_code == 422
    assert response.json() == {"message": f"Username '{user_name}' already taken!"}

@patch("http_server.routers.users.db.userAdd", new_callable=AsyncMock)
def test_register_db_error(db_mock):
    db_mock.side_effect = Exception()

    user_name = "a" * USERNAME_MIN_LEN
    password = "a" * PASSWORD_MIN_LEN

    response = CLIENT.post(
        "/users",
        data={
            "user_name": user_name,
            "password": password
        }
    )

    assert response.status_code == 500
    assert response.json() == {"message": "Something went wrong"}

def test_all_no_session_id_error():
    response = CLIENT.get(
        "/users"
    )

    assert response.status_code == 401
    assert response.json() == {"message": "Session id not found in request!"}

@patch("http_server.middlewares.authentication.sessionValidate", new_callable=AsyncMock)
def test_all_user_not_allowed(session_mock):
    session_mock.return_value = User.model_validate(
        {
            "id": 1,
            "name": "user_name",
            "role": "user",
        }
    )
    response = CLIENT.get(
        "/users"
    )

    assert response.status_code == 403
    assert response.json() == {"message": "Unauthorized"}

@patch("http_server.routers.users.db.usersAll", new_callable=AsyncMock)
@patch("http_server.middlewares.authentication.sessionValidate", new_callable=AsyncMock)
def test_all_admin_allowed(session_mock: AsyncMock, db_mock: AsyncMock):
    session_mock.return_value = User.model_validate(
        {
            "id": 1,
            "name": "user_name",
            "role": "admin",
        }
    )
    db_mock.return_value = []
    response = CLIENT.get(
        "/users"
    )

    assert response.status_code == 200
    db_mock.assert_awaited_once()
