import os
from pathlib import Path

from flask import Flask

from config import CONFIGS
from .context_processors import inject_global_context
from .error_handlers import register_error_handlers
from .extensions import csrf, db, login_manager, migrate


def create_app(config_name=None):
    app = Flask(__name__)
    selected = config_name or os.getenv("APP_CONFIG", "development")
    config_class = CONFIGS.get(selected, CONFIGS["development"])
    app.config.from_object(config_class)
    validate_config = getattr(config_class, "validate", None)
    if validate_config:
        validate_config()

    for key in ("UPLOAD_ROOT", "GENERATED_ROOT", "TEMP_ROOT"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth import bp as auth_bp
    from .public import bp as public_bp
    from .student import bp as student_bp
    from .teacher import bp as teacher_bp
    from .admin import bp as admin_bp
    from .api import bp as api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    app.context_processor(inject_global_context)
    register_error_handlers(app)

    from .commands import register_commands
    register_commands(app)

    return app
