from decimal import Decimal

from sqlalchemy import func, or_

from ..extensions import db
from ..models import CourseEnrollment, CourseModule, Lesson, LessonProgress, ProgrammingTask, Quiz, QuizAttempt, Submission
from .helpers import utcnow


def calculate_course_progress(user_id, course_id):
    lessons = (
        Lesson.query
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(
            CourseModule.course_id == course_id,
            Lesson.is_required.is_(True),
            Lesson.is_published.is_(True),
        )
        .all()
    )
    tasks = (
        ProgrammingTask.query
        .join(Lesson, ProgrammingTask.lesson_id == Lesson.id)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(
            CourseModule.course_id == course_id,
            ProgrammingTask.is_required.is_(True),
            ProgrammingTask.status == "published",
        )
        .all()
    )
    quizzes = (
        Quiz.query
        .outerjoin(Lesson, Quiz.lesson_id == Lesson.id)
        .outerjoin(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(
            Quiz.is_required.is_(True),
            Quiz.status == "published",
            or_(Quiz.course_id == course_id, CourseModule.course_id == course_id),
        )
        .all()
    )
    total = len(lessons) + len(tasks) + len(quizzes)
    if total == 0:
        return Decimal("0.00")

    lesson_ids = [lesson.id for lesson in lessons]
    completed_lessons = 0
    if lesson_ids:
        completed_lessons = LessonProgress.query.filter(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.status == "completed",
        ).count()

    completed_tasks = sum(
        1
        for task in tasks
        if Submission.query.filter_by(user_id=user_id, task_id=task.id, status="accepted").first()
    )

    passed_quizzes = 0
    best_quiz_scores = []
    for quiz in quizzes:
        best_score = (
            db.session.query(func.max(QuizAttempt.score))
            .filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id == quiz.id,
                QuizAttempt.status == "completed",
            )
            .scalar()
        )
        if best_score is not None:
            numeric_score = float(best_score)
            best_quiz_scores.append(numeric_score)
            if numeric_score >= quiz.passing_score:
                passed_quizzes += 1

    percent = Decimal(str((completed_lessons + completed_tasks + passed_quizzes) * 100 / total)).quantize(Decimal("0.01"))
    enrollment = CourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if enrollment:
        final_score = Decimal(str(sum(best_quiz_scores) / len(best_quiz_scores))).quantize(Decimal("0.01")) if best_quiz_scores else None
        enrollment.progress_percent = percent
        enrollment.final_score = final_score
        meets_course_score = final_score is None or final_score >= enrollment.course.passing_score
        enrollment.status = "completed" if percent >= 100 and meets_course_score else "in_progress"
        if enrollment.status == "completed" and not enrollment.completed_at:
            enrollment.completed_at = utcnow()
    return percent


def mark_lesson_complete(user_id, lesson_id):
    progress = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
    if not progress:
        progress = LessonProgress(user_id=user_id, lesson_id=lesson_id)
        db.session.add(progress)
    progress.status = "completed"
    progress.completed_at = utcnow()
    return progress
