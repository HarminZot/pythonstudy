from flask import request
from flask_login import current_user

from ..extensions import db
from ..models import AuditLog


def log_action(action, entity_type=None, entity_id=None, details=None, user=None):
    actor = user
    if actor is None and current_user.is_authenticated:
        actor = current_user
    entry = AuditLog(
        user_id=getattr(actor, "id", None),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=(request.user_agent.string or "")[:500],
        details=details or {},
    )
    db.session.add(entry)
    return entry
