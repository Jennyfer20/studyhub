from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Enregistrement des blueprints
    from app.routes.auth import auth_bp
    from app.routes.documents import documents_bp
    from app.routes.university import university_bp
    from app.routes.profile import profile_bp
    from app.routes.forum import forum_bp
    from app.routes.groups import groups_bp
    from app.routes.messages import messages_bp
    from app.routes.favorites import favorites_bp
    from app.routes.comments import comments_bp
    from app.routes import pages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(university_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(pages_bp)

    return app