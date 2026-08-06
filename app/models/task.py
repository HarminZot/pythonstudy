from ..extensions import db
from .base import TimestampMixin, utcnow


class ProgrammingTask(TimestampMixin, db.Model):
    __tablename__ = "programming_tasks"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    lesson_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("lessons.id"), nullable=False)
    created_by = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_description = db.Column(db.Text)
    output_description = db.Column(db.Text)
    examples = db.Column(db.Text)
    starter_code = db.Column(db.Text)
    reference_solution = db.Column(db.Text)
    difficulty = db.Column(db.String(30), default="beginner", nullable=False)
    points = db.Column(db.Integer, default=10, nullable=False)
    time_limit_seconds = db.Column(db.Numeric(5, 2), default=2, nullable=False)
    memory_limit_mb = db.Column(db.Integer, default=256, nullable=False)
    allowed_imports = db.Column(db.JSON)
    status = db.Column(db.String(30), default="draft", nullable=False)
    order_index = db.Column(db.Integer, default=1, nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)

    lesson = db.relationship("Lesson", back_populates="tasks")
    author = db.relationship("User", foreign_keys=[created_by])
    test_cases = db.relationship("TaskTestCase", back_populates="task", cascade="all, delete-orphan", order_by="TaskTestCase.order_index")
    submissions = db.relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class TaskTestCase(TimestampMixin, db.Model):
    __tablename__ = "task_test_cases"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    task_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("programming_tasks.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    input_data = db.Column(db.Text)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=True, nullable=False)
    weight = db.Column(db.Integer, default=1, nullable=False)
    order_index = db.Column(db.Integer, default=1, nullable=False)
    timeout_seconds = db.Column(db.Numeric(5, 2))

    task = db.relationship("ProgrammingTask", back_populates="test_cases")
    results = db.relationship("SubmissionTestResult", back_populates="test_case")


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    task_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("programming_tasks.id"), nullable=False)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    code = db.Column(db.Text, nullable=False)
    python_version = db.Column(db.String(20), default="3", nullable=False)
    status = db.Column(db.String(40), default="queued", nullable=False)
    score = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    passed_tests = db.Column(db.Integer, default=0, nullable=False)
    total_tests = db.Column(db.Integer, default=0, nullable=False)
    execution_time_ms = db.Column(db.Integer)
    memory_used_kb = db.Column(db.Integer)
    stdout = db.Column(db.Text)
    stderr = db.Column(db.Text)
    teacher_comment = db.Column(db.Text)
    reviewed_by = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime(timezone=True))
    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    checked_at = db.Column(db.DateTime(timezone=True))

    task = db.relationship("ProgrammingTask", back_populates="submissions")
    user = db.relationship("User", back_populates="submissions", foreign_keys=[user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    test_results = db.relationship("SubmissionTestResult", back_populates="submission", cascade="all, delete-orphan")


class SubmissionTestResult(db.Model):
    __tablename__ = "submission_test_results"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    submission_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("submissions.id"), nullable=False)
    test_case_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("task_test_cases.id"), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    actual_output = db.Column(db.Text)
    error_message = db.Column(db.Text)
    execution_time_ms = db.Column(db.Integer)
    memory_used_kb = db.Column(db.Integer)
    is_passed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    submission = db.relationship("Submission", back_populates="test_results")
    test_case = db.relationship("TaskTestCase", back_populates="results")
