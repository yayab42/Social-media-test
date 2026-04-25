# Mini Social Network Technical Test in FLASK

This project is a technical test whose goal is to build a mini social network focused on three core concepts:

- a personal feed;
- user follow relationships;
- JWT-based session tokens.

The application exposes a JSON API built with Flask and PostgreSQL. A small web interface is also included for visual testing.

## Requirements

- Docker
- Docker Compose

## Run the Application

For the first launch, build and start the containers:

```bash
docker compose up --build
```

For the next launches:

```bash
docker compose up
```

To stop the application:

```bash
docker compose down --remove-orphans
```

The Flask application runs on port `5000`.

The PostgreSQL database runs in a separate container and is exposed on port `5432`.

## Seed Test Data

After the application has started, you can create fake data and a test user with:

```bash
docker compose exec web flask --app app seed-test-data
```

This command creates a test user:

- username: `test_user`
- password: `test`

It also creates generated users, posts, followers, and following relationships so the feed can be tested quickly.

## Tests

The project includes automated tests for the main API behaviors.

Once the Docker containers are running, the test suite can be executed with:

```bash
docker compose exec web pytest -v -s
```

The tests cover the main features of the application, including:

- user registration and login;
- JWT-protected routes;
- post creation and feed retrieval;
- user profiles;
- follow and unfollow behavior;
- followers and following lists;
- pagination and input validation;
- fake data seeding.

## Web Interface

The original technical test does not require a frontend.

However, a rudimentary web interface is available to visually verify the main features:

```text
http://localhost:5000/web/
```

## Architecture

The project follows an architecture close to MVC for clarity:

- `models.py` contains the database models.
- `views.py` contains the request handlers and application logic.
- `routes.py` defines the available API and web routes.
- `schemas.py` contains request validation schemas.
- `seed.py` contains the fake data command.
- `templates/` contains the minimal web interface.

## API Overview

The API provides endpoints for authentication, users, posts, feeds, and follow relationships.

Main endpoints include:

- `GET /` checks that the API is running.
- `POST /users` registers a new user.
- `POST /login` logs a user in and returns a JWT access token.
- `POST /logout` revokes the current JWT token.
- `GET /users/<username>` returns a public user profile.
- `GET /users/<username>/posts` returns a user's posts.
- `GET /users/<username>/followers` returns a user's followers.
- `GET /users/<username>/following` returns the users followed by a user.
- `POST /posts` creates a post for the authenticated user.
- `GET /posts` returns the authenticated user's feed.
- `POST /users/follow/<username>` follows a user.
- `DELETE /users/follow/<username>` unfollows a user.
- `GET /users/followers` returns the authenticated user's followers.

Some post list endpoints support optional pagination with `page` and `per_page` query parameters.

For the complete and authoritative list of routes, check `routes.py`.

## End User Features

Available end user features are:

- Register a new account with a username, email, and password.
- Log in with a username and password.
- Receive a JWT access token after login.
- Stay authenticated from the web interface through browser local storage.
- Log out and revoke the current JWT token.
- Create a new post while authenticated.
- Read the authenticated user's feed.
- See posts from the authenticated user and from followed users in the feed.
- Browse the feed with pagination.
- Reload the feed manually from the web interface.
- View any user's public profile by username.
- View any user's posts.
- Browse a user's posts with pagination.
- Follow another user.
- Unfollow a followed user.
- Prevent users from following themselves.
- Prevent users from unfollowing themselves.
- See the followers of a user.
- See the users followed by a user.
- See the authenticated user's followers.
- Navigate between feed, login, registration, and user profile pages in the web interface.
- Use seeded fake users, posts, followers, and following relationships for local testing.
- Use the default seeded `test_user` account to quickly test authenticated features.

## Notes

Request bodies are expected to be JSON for the API.

JWT-protected endpoints require an `Authorization` header:

```text
Authorization: Bearer <access_token>
```

User input is validated through three dedicated validation libraries:

- `pydantic` is used to define and validate request payload schemas.
- `email-validator` is used through Pydantic's `EmailStr` type to validate email addresses.
- `python-usernames` is used to reject invalid or reserved usernames.

Passwords are stored as hashes.
