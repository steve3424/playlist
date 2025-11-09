import pytest
from fastapi.testclient import TestClient
from http_server.server import createApp, StartupException
from unittest.mock import patch, AsyncMock

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", new_callable=AsyncMock)
@patch("http_server.server.tickets.init", new_callable=AsyncMock)
@patch("http_server.server.load_dotenv", return_value=True)
def test_startup_success(*args):
    with TestClient(createApp("localhost", 6379, "dev")) as c:
        assert True

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", new_callable=AsyncMock)
@patch("http_server.server.tickets.init", new_callable=AsyncMock)
@patch("http_server.server.load_dotenv", return_value=False)
def test_startup_load_dotenv_fails_still_start(*args):
    with TestClient(createApp("localhost", 6379, "dev")) as c:
        assert True

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", new_callable=AsyncMock)
@patch("http_server.server.tickets.init", return_value=False)
@patch("http_server.server.load_dotenv", return_value=True)
def test_startup_ticket_init_fails_still_start(*args):
    with TestClient(createApp("localhost", 6379, "dev")) as c:
        assert True

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", return_value=False)
@patch("http_server.server.tickets.init", return_value=True)
@patch("http_server.server.load_dotenv", return_value=True)
def test_startup_db_init_fails_startup_fails(*args):
    with pytest.raises(StartupException) as exception:
        with TestClient(createApp("localhost", 6379, "dev")) as c:
            pass

@patch("http_server.middlewares.authentication.init", return_value=False)
@patch("http_server.server.db.init", return_value=True)
@patch("http_server.server.tickets.init", return_value=True)
@patch("http_server.server.load_dotenv", return_value=True)
def test_startup_authentication_init_fails_startup_fails(*args):
    with pytest.raises(StartupException) as exception:
        with TestClient(createApp("localhost", 6379, "dev")) as c:
            pass
