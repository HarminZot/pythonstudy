from ..extensions import db
from .base import TimestampMixin, utcnow


class FeedbackRequest(TimestampMixin, db.Model):
    __tablename__ = "feedback_requests"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    assigned_admin_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    attachment_file_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("uploaded_files.id"))
    email = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="new", nullable=False)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    closed_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", foreign_keys=[user_id])
    assigned_admin = db.relationship("User", foreign_keys=[assigned_admin_id])
    attachment = db.relationship("UploadedFile", foreign_keys=[attachment_file_id])
    messages = db.relationship("FeedbackMessage", back_populates="request", cascade="all, delete-orphan")


class FeedbackMessage(db.Model):
    __tablename__ = "feedback_messages"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    request_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("feedback_requests.id"), nullable=False)
    author_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    attachment_file_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("uploaded_files.id"))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    request = db.relationship("FeedbackRequest", back_populates="messages")
    author = db.relationship("User")
    attachment = db.relationship("UploadedFile")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    read_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", back_populates="notifications")
