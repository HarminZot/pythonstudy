from app.extensions import db
from app.models import CourseEnrollment, LessonProgress, Quiz, QuizAttempt, Submission
from app.services.progress_service import calculate_course_progress


def test_required_quiz_is_included_in_course_progress(app):
    with app.app_context():
        quiz = Quiz(
            course_id=1,
            created_by=2,
            title="Итоговый тест",
            status="published",
            is_required=True,
            passing_score=70,
            max_attempts=3,
        )
        db.session.add_all([
            quiz,
            LessonProgress(user_id=1, lesson_id=1, status="completed"),
            Submission(task_id=1, user_id=1, code="print(1)", status="accepted", score=100),
        ])
        db.session.flush()

        assert float(calculate_course_progress(1, 1)) == 66.67
        enrollment = CourseEnrollment.query.filter_by(user_id=1, course_id=1).first()
        assert enrollment.status == "in_progress"

        db.session.add(QuizAttempt(
            quiz_id=quiz.id,
            user_id=1,
            attempt_number=1,
            status="completed",
            score=80,
            total_questions=1,
            correct_answers=1,
        ))
        db.session.flush()
        assert float(calculate_course_progress(1, 1)) == 100
        assert enrollment.status == "completed"
        assert float(enrollment.final_score) == 80
