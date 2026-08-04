from ..extensions import db
from .base import utcnow


class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    owner_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), unique=True, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(150), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    checksum = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    owner = db.relationship("User")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(100))
    entity_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User")


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    setting_key = db.Column(db.String(150), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    value_type = db.Column(db.String(30), default="string", nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    updated_by = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    editor = db.relationship("User")
