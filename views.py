from flask import jsonify, render_template, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Post, TokenBlocklist, User
from schemas import LoginPayload, PostPayload, RegistrationPayload, validation_details


DEFAULT_POSTS_PER_PAGE = 20
MAX_POSTS_PER_PAGE = 100


def validation_error(errors: dict, status_code: int = 400):
    return jsonify({"error": "validation failed", "details": errors}), status_code


def positive_int_query_arg(name: str, default: int) -> tuple[int | None, str | None]:
    raw_value = request.args.get(name, default)

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None, "must be a positive integer"

    if value < 1:
        return None, "must be a positive integer"

    return value, None


def get_posts_pagination():
    page, page_error = positive_int_query_arg("page", 1)
    per_page, per_page_error = positive_int_query_arg(
        "per_page",
        DEFAULT_POSTS_PER_PAGE,
    )

    errors = {}
    if page_error:
        errors["page"] = page_error
    if per_page_error:
        errors["per_page"] = per_page_error
    elif per_page > MAX_POSTS_PER_PAGE:
        errors["per_page"] = f"must be less than or equal to {MAX_POSTS_PER_PAGE}"

    if errors:
        return None, None, validation_error(errors)

    return page, per_page, None


def get_json_body():
    if not request.is_json:
        return None, (jsonify({"error": "request body must be JSON"}), 415)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "request body must be a JSON object"}), 400)

    return data, None


def index():
    return jsonify({"message": "API is running"}), 200


def web_feed():
    return render_template("posts/feed.html")


def web_login():
    return render_template("auth/login.html")


def web_register():
    return render_template("auth/register.html")


def web_user():
    return render_template("users/profile.html")


def register_user():
    data, error_response = get_json_body()
    if error_response:
        return error_response

    try:
        payload = RegistrationPayload.model_validate(data)
    except ValidationError as error:
        return validation_error(validation_details(error))

    if User.query.filter(
        (User.username == payload.username) | (User.email == str(payload.email))
    ).first():
        return jsonify({"error": "username or email already exists"}), 409

    user = User(username=payload.username, email=str(payload.email))
    user.set_password(payload.password.get_secret_value())
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "username or email already exists"}), 409

    return jsonify(user.to_dict()), 201


def login():
    data, error_response = get_json_body()
    if error_response:
        return error_response

    try:
        payload = LoginPayload.model_validate(data)
    except ValidationError as error:
        return validation_error(validation_details(error))

    user = User.query.filter_by(username=payload.username).first()
    if user is None or not user.check_password(payload.password.get_secret_value()):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token}), 200


def logout():
    jti = get_jwt()["jti"]

    if TokenBlocklist.query.filter_by(jti=jti).first() is None:
        db.session.add(TokenBlocklist(jti=jti))
        db.session.commit()

    return jsonify({"message": "successfully logged out"}), 200


def create_post():
    data, error_response = get_json_body()
    if error_response:
        return error_response

    try:
        payload = PostPayload.model_validate(data)
    except ValidationError as error:
        return validation_error(validation_details(error))

    post = Post(content=payload.content, author_id=int(get_jwt_identity()))
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_dict()), 201


def get_feed():
    user = db.session.get(User, int(get_jwt_identity()))
    followed_ids = [followed.id for followed in user.followed]
    author_ids = followed_ids + [user.id]
    wants_pagination = "page" in request.args or "per_page" in request.args
    page, per_page, error_response = get_posts_pagination()

    if error_response:
        return error_response

    feed_query = (
        Post.query.filter(Post.author_id.in_(author_ids))
        .order_by(Post.timestamp.desc())
    )

    if not wants_pagination:
        return jsonify([post.to_dict() for post in feed_query.all()]), 200

    total = feed_query.order_by(None).count()
    posts = feed_query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    return jsonify(
        {
            "items": [post.to_dict() for post in posts],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }
    ), 200


def get_user_profile(username: str):
    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({"error": "user not found"}), 404

    return jsonify(user.to_dict()), 200


def get_user_posts(username: str):
    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({"error": "user not found"}), 404

    wants_pagination = "page" in request.args or "per_page" in request.args
    page, per_page, error_response = get_posts_pagination()

    if error_response:
        return error_response

    posts_query = Post.query.filter_by(author_id=user.id).order_by(Post.timestamp.desc())

    if not wants_pagination:
        return jsonify([post.to_dict() for post in posts_query.all()]), 200

    total = posts_query.order_by(None).count()
    posts = posts_query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    return jsonify(
        {
            "items": [post.to_dict() for post in posts],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }
    ), 200


def get_user_followers(username: str):
    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({"error": "user not found"}), 404

    followers = user.followers.order_by(User.username.asc()).all()
    return jsonify([follower.to_dict() for follower in followers]), 200


def get_user_following(username: str):
    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({"error": "user not found"}), 404

    following = user.followed.order_by(User.username.asc()).all()
    return jsonify([followed.to_dict() for followed in following]), 200


def follow_user(username: str):
    current_user = db.session.get(User, int(get_jwt_identity()))
    user_to_follow = User.query.filter_by(username=username).first()

    if user_to_follow is None:
        return jsonify({"error": "user not found"}), 404

    if user_to_follow.id == current_user.id:
        return jsonify({"error": "cannot follow yourself"}), 400

    current_user.follow(user_to_follow)
    db.session.commit()

    return jsonify({"message": f"now following {user_to_follow.username}"}), 200


def unfollow_user(username: str):
    current_user = db.session.get(User, int(get_jwt_identity()))
    user_to_unfollow = User.query.filter_by(username=username).first()

    if user_to_unfollow is None:
        return jsonify({"error": "user not found"}), 404

    if user_to_unfollow.id == current_user.id:
        return jsonify({"error": "cannot unfollow yourself"}), 400

    if not current_user.is_following(user_to_unfollow):
        return jsonify({"error": "user is not followed"}), 400

    current_user.unfollow(user_to_unfollow)
    db.session.commit()

    return jsonify({"message": f"unfollowed {user_to_unfollow.username}"}), 200


def get_followers():
    current_user = db.session.get(User, int(get_jwt_identity()))
    followers = current_user.followers.order_by(User.username.asc()).all()

    return jsonify([follower.to_dict() for follower in followers]), 200
