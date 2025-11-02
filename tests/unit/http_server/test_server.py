import pytest
from fastapi.testclient import TestClient
from http_server.server import createApp
from unittest.mock import patch, AsyncMock

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", new_callable=AsyncMock)
@patch("http_server.server.tickets.init", new_callable=AsyncMock)
@patch("http_server.server.load_dotenv", return_value=True)
def test_startup_success(*args):
    with TestClient(createApp("localhost", 6379, "dev")) as c:
        pass
    assert True

@patch("http_server.middlewares.authentication.init", return_value=True)
@patch("http_server.server.db.init", new_callable=AsyncMock)
@patch("http_server.server.tickets.init", new_callable=AsyncMock)
@patch("http_server.server.load_dotenv", return_value=False)
def test_startup_load_dotenv_fails_still_start(*args):
    with TestClient(createApp("localhost", 6379, "dev")) as c:
        pass
    assert True
