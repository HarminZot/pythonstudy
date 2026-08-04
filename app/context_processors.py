from flask import request
from flask_login import current_user


def inject_global_context():
    return {
        "current_path": request.path,
        "is_authenticated": current_user.is_authenticated,
    }
