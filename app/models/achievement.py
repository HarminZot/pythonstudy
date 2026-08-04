from ..extensions import db
from .base import utcnow


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon_path = db.Column(db.String(500))
    condition_type = db.Column(db.String(50), nullable=False)
    condition_value = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    awards = db.relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"
    __table_args__ = (db.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    achievement_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("achievements.id"), nullable=False)
    awarded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User")
    achievement = db.relationship("Achievement", back_populates="awards")
