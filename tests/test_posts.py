def test_create_post_publishes_content(client, auth_headers):
    response = client.post(
        "/posts",
        json={"content": "First post from Alice"},
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 201
    assert response.json["content"] == "First post from Alice"
    assert response.json["author_id"] == 1


def test_create_post_rejects_empty_content(client, auth_headers):
    response = client.post(
        "/posts",
        json={"content": ""},
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation failed"
    assert "content" in response.json["details"]


def test_get_feed_returns_own_posts(client, auth_headers):
    headers = auth_headers(username="alice")
    client.post("/posts", json={"content": "A useful update"}, headers=headers)

    response = client.get("/posts", headers=headers)

    assert response.status_code == 200
    assert [post["content"] for post in response.json] == ["A useful update"]


def test_get_feed_returns_paginated_posts(client, auth_headers):
    headers = auth_headers(username="alice")

    for number in range(1, 6):
        client.post("/posts", json={"content": f"Post #{number}"}, headers=headers)

    response = client.get("/posts?page=2&per_page=2", headers=headers)

    assert response.status_code == 200
    assert [post["content"] for post in response.json["items"]] == [
        "Post #3",
        "Post #2",
    ]
    assert response.json["pagination"] == {
        "page": 2,
        "per_page": 2,
        "total_items": 5,
        "total_pages": 3,
    }


def test_get_feed_rejects_invalid_pagination(client, auth_headers):
    response = client.get(
        "/posts?page=0&per_page=101",
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation failed"
    assert response.json["details"] == {
        "page": "must be a positive integer",
        "per_page": "must be less than or equal to 100",
    }


def test_get_feed_requires_authentication(client):
    response = client.get("/posts")

    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}
