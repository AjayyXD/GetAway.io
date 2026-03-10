import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv("variables.env")


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.environ.get("APP_KEY")

    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.fa import fa_bp
    from app.routes.warden import warden_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(fa_bp)
    app.register_blueprint(warden_bp)
    app.register_blueprint(admin_bp)

    return app