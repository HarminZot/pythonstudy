from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*role_codes):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_active_account:
                abort(403)
            if current_user.role.code not in role_codes:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
