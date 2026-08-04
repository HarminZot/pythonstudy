from ..extensions import db
from .base import TimestampMixin, utcnow


class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    teacher_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(500), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    cover_path = db.Column(db.String(500))
    difficulty = db.Column(db.String(30), default="beginner", nullable=False)
    status = db.Column(db.String(30), default="draft", nullable=False, index=True)
    estimated_hours = db.Column(db.Integer, default=1, nullable=False)
    passing_score = db.Column(db.Integer, default=70, nullable=False)
    is_sequential = db.Column(db.Boolean, default=True, nullable=False)
    published_at = db.Column(db.DateTime(timezone=True))

    teacher = db.relationship("User", back_populates="taught_courses", foreign_keys=[teacher_id])
    modules = db.relationship("CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.order_index")
    enrollments = db.relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", back_populates="course", cascade="all, delete-orphan")

    @property
    def lessons_count(self):
        return sum(len(module.lessons) for module in self.modules)


class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"
    __table_args__ = (db.UniqueConstraint("course_id", "user_id", name="uq_enrollment_course_user"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    course_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("courses.id"), nullable=False)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="enrolled", nullable=False)
    progress_percent = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    final_score = db.Column(db.Numeric(5, 2))
    enrolled_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))

    course = db.relationship("Course", back_populates="enrollments")
    user = db.relationship("User", back_populates="enrollments")


class CourseModule(TimestampMixin, db.Model):
    __tablename__ = "course_modules"
    __table_args__ = (db.UniqueConstraint("course_id", "order_index", name="uq_module_order"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    course_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order_index = db.Column(db.Integer, nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)

    course = db.relationship("Course", back_populates="modules")
    lessons = db.relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order_index")
