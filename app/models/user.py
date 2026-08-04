from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from .base import TimestampMixin, utcnow


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    users = db.relationship("User", back_populates="role", lazy="dynamic")


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    role_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("roles.id"), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    avatar_path = db.Column(db.String(500))
    status = db.Column(db.String(30), default="active", nullable=False, index=True)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True))

    role = db.relationship("Role", back_populates="users")
    taught_courses = db.relationship("Course", back_populates="teacher", foreign_keys="Course.teacher_id")
    enrollments = db.relationship("CourseEnrollment", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = db.relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = db.relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return " ".join(filter(None, [self.last_name, self.first_name, self.middle_name]))

    @property
    def is_active_account(self):
        return self.status == "active"

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *codes):
        return bool(self.role and self.role.code in codes)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User")
