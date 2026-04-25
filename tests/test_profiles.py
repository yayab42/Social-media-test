def test_get_user_profile_returns_public_user_details(register_user, client):
    register_user(username="alice", email="alice@example.com")

    response = client.get("/users/alice")

    assert response.status_code == 200
    assert response.json["username"] == "alice"
    assert response.json["email"] == "alice@example.com"
    assert "password" not in response.json


def test_get_user_profile_rejects_unknown_username(client):
    response = client.get("/users/missing-user")

    assert response.status_code == 404
    assert response.json == {"error": "user not found"}


def test_get_user_posts_returns_only_requested_users_posts(client, auth_headers):
    alice_headers = auth_headers(username="alice")
    bob_headers = auth_headers(username="bob")
    client.post("/posts", json={"content": "Alice update"}, headers=alice_headers)
    client.post("/posts", json={"content": "Bob update"}, headers=bob_headers)

    response = client.get("/users/alice/posts")

    assert response.status_code == 200
    assert [post["content"] for post in response.json] == ["Alice update"]


def test_get_user_posts_returns_paginated_posts(client, auth_headers):
    headers = auth_headers(username="alice")

    for number in range(1, 6):
        client.post("/posts", json={"content": f"Profile post #{number}"}, headers=headers)

    response = client.get("/users/alice/posts?page=2&per_page=2")

    assert response.status_code == 200
    assert [post["content"] for post in response.json["items"]] == [
        "Profile post #3",
        "Profile post #2",
    ]
    assert response.json["pagination"] == {
        "page": 2,
        "per_page": 2,
        "total_items": 5,
        "total_pages": 3,
    }


def test_get_user_posts_rejects_unknown_username(client):
    response = client.get("/users/missing-user/posts")

    assert response.status_code == 404
    assert response.json == {"error": "user not found"}


def test_get_user_posts_rejects_invalid_pagination(register_user, client):
    register_user(username="alice")

    response = client.get("/users/alice/posts?page=0&per_page=101")

    assert response.status_code == 400
    assert response.json["error"] == "validation failed"
    assert response.json["details"] == {
        "page": "must be a positive integer",
        "per_page": "must be less than or equal to 100",
    }
