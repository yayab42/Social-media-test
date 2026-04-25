import random
from datetime import timezone

import click
from faker import Faker
from flask.cli import with_appcontext

from extensions import db
from models import Post, User


TEST_USERNAME = "test_user"
TEST_PASSWORD = "test"
TEST_EMAIL = "test_user@example.com"
GENERATED_USER_PREFIX = "seed_user_"


def get_or_create_user(username: str, email: str, password: str) -> tuple[User, bool]:
    user = User.query.filter_by(username=username).first()

    if user is not None:
        user.email = email
        user.set_password(password)
        return user, False

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    return user, True


def build_post_content(fake: Faker, rng: random.Random) -> str:
    patterns = [
        lambda: fake.paragraph(nb_sentences=rng.randint(2, 5)),
        lambda: f"{fake.sentence()} {fake.catch_phrase()}.",
        lambda: (
            f"Petit retour sur {fake.bs()} : "
            f"{fake.paragraph(nb_sentences=rng.randint(1, 3))}"
        ),
    ]
    return rng.choice(patterns)()


def seed_test_data(
    user_count: int = 50,
    post_count: int = 250,
    follower_count: int = 20,
    following_count: int = 10,
) -> dict:
    fake = Faker("fr_FR")
    Faker.seed(42)
    rng = random.Random(42)

    test_user, created_test_user = get_or_create_user(
        TEST_USERNAME,
        TEST_EMAIL,
        TEST_PASSWORD,
    )

    generated_users = []
    created_users = 1 if created_test_user else 0

    for index in range(1, user_count + 1):
        username = f"{GENERATED_USER_PREFIX}{index:03d}"
        email = f"{username}@example.com"
        user, created = get_or_create_user(username, email, "test")
        generated_users.append(user)
        created_users += int(created)

    db.session.flush()

    for follower in generated_users[:follower_count]:
        follower.follow(test_user)

    for followed in generated_users[:following_count]:
        test_user.follow(followed)

    existing_post_count = (
        Post.query.join(User)
        .filter(User.username.like(f"{GENERATED_USER_PREFIX}%"))
        .count()
    )
    posts_to_create = max(post_count - existing_post_count, 0)

    for _ in range(posts_to_create):
        author = rng.choice(generated_users)
        timestamp = fake.date_time_between(
            start_date="-120d",
            end_date="now",
            tzinfo=timezone.utc,
        )
        db.session.add(
            Post(
                content=build_post_content(fake, rng),
                timestamp=timestamp,
                author=author,
            )
        )

    db.session.commit()

    return {
        "created_users": created_users,
        "created_posts": posts_to_create,
        "test_username": TEST_USERNAME,
        "test_password": TEST_PASSWORD,
        "followers": test_user.followers.count(),
        "following": test_user.followed.count(),
    }


@click.command("seed-test-data")
@click.option("--users", default=50, show_default=True, type=click.IntRange(min=1))
@click.option("--posts", default=250, show_default=True, type=click.IntRange(min=0))
@click.option("--followers", default=20, show_default=True, type=click.IntRange(min=0))
@click.option("--following", default=10, show_default=True, type=click.IntRange(min=0))
@with_appcontext
def seed_test_data_command(
    users: int,
    posts: int,
    followers: int,
    following: int,
) -> None:
    """Create optional local demo data for development."""
    result = seed_test_data(
        user_count=users,
        post_count=posts,
        follower_count=min(followers, users),
        following_count=min(following, users),
    )

    click.echo(
        "Seed complete: "
        f"{result['created_users']} user(s) created, "
        f"{result['created_posts']} post(s) created."
    )
    click.echo(
        f"Login: {result['test_username']} / {result['test_password']} "
        f"({result['followers']} followers, {result['following']} following)"
    )
