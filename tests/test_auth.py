def test_login_returns_access_token(client, register_user):
    register_user(username="alice", password="simple-password")

    response = client.post(
        "/login",
        json={"username": "alice", "password": "simple-password"},
    )

    assert response.status_code == 200
    assert isinstance(response.json["access_token"], str)


def test_login_rejects_invalid_credentials(client, register_user):
    register_user(username="alice", password="simple-password")

    response = client.post(
        "/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json == {"error": "invalid credentials"}


def test_logout_revokes_current_token(client, auth_headers):
    headers = auth_headers(username="alice")

    response = client.post("/logout", headers=headers)
    protected_response = client.get("/posts", headers=headers)

    assert response.status_code == 200
    assert response.json == {"message": "successfully logged out"}
    assert protected_response.status_code == 401


def test_logout_requires_authentication(client):
    response = client.post("/logout")

    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}
