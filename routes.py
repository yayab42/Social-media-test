from flask import Blueprint
from flask_jwt_extended import jwt_required

from views import (
    create_post,
    follow_user,
    get_feed,
    get_followers,
    get_user_followers,
    get_user_following,
    get_user_posts,
    get_user_profile,
    index,
    login,
    logout,
    register_user,
    unfollow_user,
    web_feed,
    web_login,
    web_register,
    web_user,
)


api_bp = Blueprint("api", __name__)

api_bp.get("/")(index)
api_bp.post("/users")(register_user)
api_bp.post("/login")(login)
api_bp.post("/logout")(jwt_required()(logout))
api_bp.get("/users/<username>")(get_user_profile)
api_bp.get("/users/<username>/posts")(get_user_posts)
api_bp.get("/users/<username>/followers")(get_user_followers)
api_bp.get("/users/<username>/following")(get_user_following)
api_bp.post("/posts")(jwt_required()(create_post))
api_bp.get("/posts")(jwt_required()(get_feed))
api_bp.post("/users/follow/<username>")(jwt_required()(follow_user))
api_bp.delete("/users/follow/<username>")(jwt_required()(unfollow_user))
api_bp.get("/users/followers")(jwt_required()(get_followers))
api_bp.get("/web/")(web_feed)
api_bp.get("/web/login")(web_login)
api_bp.get("/web/register")(web_register)
api_bp.get("/web/users")(web_user)
