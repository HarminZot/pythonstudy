from ..extensions import db
from .base import TimestampMixin, utcnow


class Lesson(TimestampMixin, db.Model):
    __tablename__ = "lessons"
    __table_args__ = (db.UniqueConstraint("module_id", "order_index", name="uq_lesson_order"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    module_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("course_modules.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.String(500))
    content = db.Column(db.Text, nullable=False)
    lesson_type = db.Column(db.String(30), default="theory", nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    estimated_minutes = db.Column(db.Integer, default=15, nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)

    module = db.relationship("CourseModule", back_populates="lessons")
    materials = db.relationship("LessonMaterial", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonMaterial.order_index")
    progress_records = db.relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    tasks = db.relationship("ProgrammingTask", back_populates="lesson", cascade="all, delete-orphan", order_by="ProgrammingTask.order_index")
    quizzes = db.relationship("Quiz", back_populates="lesson")


class LessonMaterial(db.Model):
    __tablename__ = "lesson_materials"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    lesson_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("lessons.id"), nullable=False)
    file_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("uploaded_files.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    material_type = db.Column(db.String(30), default="document", nullable=False)
    order_index = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    lesson = db.relationship("Lesson", back_populates="materials")
    file = db.relationship("UploadedFile")


class LessonProgress(db.Model):
    __tablename__ = "lesson_progress"
    __table_args__ = (db.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    lesson_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("lessons.id"), nullable=False)
    status = db.Column(db.String(30), default="not_started", nullable=False)
    time_spent_seconds = db.Column(db.Integer, default=0, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    last_opened_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship("User", back_populates="lesson_progress")
    lesson = db.relationship("Lesson", back_populates="progress_records")
