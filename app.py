import os
from datetime import timedelta

from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from extensions import db, jwt
from models import TokenBlocklist
from routes import api_bp
from seed import seed_test_data_command


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error: SQLAlchemyError):
        db.session.rollback()
        return jsonify({"error": "database error"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        return jsonify({"error": "internal server error"}), 500


def register_jwt_handlers() -> None:
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
        return TokenBlocklist.query.filter_by(jti=jwt_payload["jti"]).first() is not None


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="template",
        static_folder="template/statics",
        static_url_path="/statics",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@db:5432/social_media",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwt_password")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

    db.init_app(app)
    jwt.init_app(app)
    register_jwt_handlers()
    register_error_handlers(app)
    app.register_blueprint(api_bp)
    app.cli.add_command(seed_test_data_command)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
