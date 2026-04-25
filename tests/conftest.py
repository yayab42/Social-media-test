import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from extensions import db


@pytest.fixture
def app(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-with-enough-length")

    app_module = importlib.import_module("app")
    test_app = app_module.create_app()
    test_app.config.update(TESTING=True)

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_payload():
    def build_payload(username="alice", email=None, password="simple-password", **extra):
        payload = {
            "username": username,
            "email": email or f"{username}@example.com",
            "password": password,
        }
        payload.update(extra)
        return payload

    return build_payload


@pytest.fixture
def register_user(client, user_payload):
    def register(username="alice", email=None, password="simple-password", **extra):
        return client.post(
            "/users",
            json=user_payload(
                username=username,
                email=email,
                password=password,
                **extra,
            ),
        )

    return register


@pytest.fixture
def login_user(client, register_user):
    def login(username="alice", password="simple-password"):
        register_response = register_user(username=username, password=password)
        assert register_response.status_code in {201, 409}

        response = client.post(
            "/login",
            json={"username": username, "password": password},
        )

        assert response.status_code == 200
        return response.json["access_token"]

    return login


@pytest.fixture
def auth_headers(login_user):
    def build_headers(username="alice"):
        token = login_user(username=username)
        return {"Authorization": f"Bearer {token}"}

    return build_headers
