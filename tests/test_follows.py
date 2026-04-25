def test_follow_user_adds_user_to_following_list(client, auth_headers, register_user):
    register_user(username="bob")

    response = client.post(
        "/users/follow/bob",
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 200
    assert response.json == {"message": "now following bob"}


def test_follow_user_rejects_unknown_username(client, auth_headers):
    response = client.post(
        "/users/follow/missing-user",
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 404
    assert response.json == {"error": "user not found"}


def test_unfollow_user_removes_existing_follow(client, auth_headers, register_user):
    headers = auth_headers(username="alice")
    register_user(username="bob")
    client.post("/users/follow/bob", headers=headers)

    response = client.delete("/users/follow/bob", headers=headers)

    assert response.status_code == 200
    assert response.json == {"message": "unfollowed bob"}


def test_unfollow_user_rejects_user_who_is_not_followed(
    client,
    auth_headers,
    register_user,
):
    register_user(username="bob")

    response = client.delete(
        "/users/follow/bob",
        headers=auth_headers(username="alice"),
    )

    assert response.status_code == 400
    assert response.json == {"error": "user is not followed"}


def test_get_followers_returns_users_following_current_user(
    client,
    auth_headers,
    register_user,
):
    alice_headers = auth_headers(username="alice")
    register_user(username="bob")
    bob_headers = auth_headers(username="bob")
    client.post("/users/follow/alice", headers=bob_headers)

    response = client.get("/users/followers", headers=alice_headers)

    assert response.status_code == 200
    assert [follower["username"] for follower in response.json] == ["bob"]


def test_get_user_followers_returns_clickable_profile_data(
    client,
    auth_headers,
    register_user,
):
    register_user(username="alice")
    register_user(username="bob")
    bob_headers = auth_headers(username="bob")
    client.post("/users/follow/alice", headers=bob_headers)

    response = client.get("/users/alice/followers")

    assert response.status_code == 200
    assert [follower["username"] for follower in response.json] == ["bob"]


def test_get_user_following_returns_clickable_profile_data(
    client,
    auth_headers,
    register_user,
):
    alice_headers = auth_headers(username="alice")
    register_user(username="bob")
    client.post("/users/follow/bob", headers=alice_headers)

    response = client.get("/users/alice/following")

    assert response.status_code == 200
    assert [followed["username"] for followed in response.json] == ["bob"]


def test_get_followers_requires_authentication(client):
    response = client.get("/users/followers")

    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}
