from ..extensions import db
from .base import TimestampMixin, utcnow


class Quiz(TimestampMixin, db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    lesson_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("lessons.id"))
    course_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("courses.id"))
    created_by = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    time_limit_minutes = db.Column(db.Integer)
    passing_score = db.Column(db.Integer, default=70, nullable=False)
    max_attempts = db.Column(db.Integer, default=3, nullable=False)
    randomize_questions = db.Column(db.Boolean, default=False, nullable=False)
    randomize_options = db.Column(db.Boolean, default=False, nullable=False)
    show_correct_answers = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(30), default="draft", nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)

    lesson = db.relationship("Lesson", back_populates="quizzes")
    course = db.relationship("Course", back_populates="quizzes")
    author = db.relationship("User", foreign_keys=[created_by])
    questions = db.relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = db.relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    quiz_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("quizzes.id"), nullable=False)
    question_type = db.Column(db.String(40), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text)
    correct_text_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    points = db.Column(db.Integer, default=1, nullable=False)
    order_index = db.Column(db.Integer, default=1, nullable=False)

    quiz = db.relationship("Quiz", back_populates="questions")
    options = db.relationship("QuizOption", back_populates="question", cascade="all, delete-orphan", order_by="QuizOption.order_index")
    answers = db.relationship("QuizAnswer", back_populates="question")


class QuizOption(db.Model):
    __tablename__ = "quiz_options"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    question_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("quiz_questions.id"), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    order_index = db.Column(db.Integer, default=1, nullable=False)

    question = db.relationship("QuizQuestion", back_populates="options")


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    quiz_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("quizzes.id"), nullable=False)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="in_progress", nullable=False)
    score = db.Column(db.Numeric(5, 2))
    correct_answers = db.Column(db.Integer, default=0, nullable=False)
    total_questions = db.Column(db.Integer, default=0, nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at = db.Column(db.DateTime(timezone=True))

    quiz = db.relationship("Quiz", back_populates="attempts")
    user = db.relationship("User", back_populates="quiz_attempts")
    answers = db.relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answers"
    __table_args__ = (db.UniqueConstraint("attempt_id", "question_id", name="uq_quiz_answer"),)

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    attempt_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("quiz_questions.id"), nullable=False)
    selected_option_ids = db.Column(db.JSON)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    awarded_points = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    answered_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    attempt = db.relationship("QuizAttempt", back_populates="answers")
    question = db.relationship("QuizQuestion", back_populates="answers")
