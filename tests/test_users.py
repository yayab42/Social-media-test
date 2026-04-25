def test_index_returns_api_status(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json == {"message": "API is running"}


def test_index_rejects_unsupported_method(client):
    response = client.post("/")

    assert response.status_code == 405
    assert response.json["error"] == "The method is not allowed for the requested URL."


def test_register_user_creates_account(register_user):
    response = register_user(
        username="alice",
        email="alice@example.com",
        password="simple-password",
    )

    assert response.status_code == 201
    assert response.json["username"] == "alice"
    assert response.json["email"] == "alice@example.com"
    assert "password" not in response.json


def test_register_user_rejects_invalid_payload(register_user):
    response = register_user(
        username="alice",
        email="not-an-email",
        password="short",
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation failed"
    assert "email" in response.json["details"]
    assert "password" in response.json["details"]


def test_register_user_rejects_duplicate_username_or_email(register_user):
    first_response = register_user(username="alice")
    duplicate_response = register_user(username="alice")

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json == {"error": "username or email already exists"}
