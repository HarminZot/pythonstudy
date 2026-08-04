from decimal import Decimal

from ..extensions import db
from ..models import CourseEnrollment, CourseModule, Lesson, LessonProgress, ProgrammingTask, Submission
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
    total = len(lessons) + len(tasks)
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

    percent = Decimal(str((completed_lessons + completed_tasks) * 100 / total)).quantize(Decimal("0.01"))
    enrollment = CourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if enrollment:
        enrollment.progress_percent = percent
        enrollment.status = "completed" if percent >= 100 else "in_progress"
        if percent >= 100 and not enrollment.completed_at:
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
