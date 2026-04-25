from models import Post, User


def test_seed_test_data_command_creates_demo_dataset(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "seed-test-data",
            "--users",
            "5",
            "--posts",
            "12",
            "--followers",
            "3",
            "--following",
            "2",
        ]
    )

    assert result.exit_code == 0
    assert "Seed complete" in result.output

    with app.app_context():
        test_user = User.query.filter_by(username="test_user").one()

        assert test_user.check_password("test")
        assert test_user.followers.count() == 3
        assert test_user.followed.count() == 2
        assert User.query.filter(User.username.like("seed_user_%")).count() == 5
        assert Post.query.count() == 12


def test_seed_test_data_command_is_relaunchable(app):
    runner = app.test_cli_runner()

    first_result = runner.invoke(args=["seed-test-data", "--users", "3", "--posts", "4"])
    second_result = runner.invoke(args=["seed-test-data", "--users", "3", "--posts", "4"])

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    with app.app_context():
        assert User.query.filter_by(username="test_user").count() == 1
        assert User.query.filter(User.username.like("seed_user_%")).count() == 3
        assert Post.query.count() == 4
