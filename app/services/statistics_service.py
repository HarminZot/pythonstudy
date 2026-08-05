from sqlalchemy import func

from ..extensions import db
from ..models import Course, CourseEnrollment, CourseModule, Lesson, LessonProgress, ProgrammingTask, QuizAttempt, Submission, User, UserAchievement


def admin_statistics():
    return {
        "users": User.query.count(),
        "courses": Course.query.count(),
        "enrollments": CourseEnrollment.query.count(),
        "submissions": Submission.query.count(),
        "accepted": Submission.query.filter_by(status="accepted").count(),
    }


def teacher_statistics(teacher_id):
    course_ids = [course.id for course in Course.query.filter_by(teacher_id=teacher_id).all()]
    if not course_ids:
        return {"courses": 0, "students": 0, "submissions": 0}
    students = (
        db.session.query(func.count(func.distinct(CourseEnrollment.user_id)))
        .filter(CourseEnrollment.course_id.in_(course_ids))
        .scalar()
        or 0
    )
    submissions = (
        Submission.query
        .join(ProgrammingTask, Submission.task_id == ProgrammingTask.id)
        .join(Lesson, ProgrammingTask.lesson_id == Lesson.id)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id.in_(course_ids))
        .count()
    )
    return {"courses": len(course_ids), "students": students, "submissions": submissions}


def student_statistics(user_id):
    average_quiz_score = (
        db.session.query(func.avg(QuizAttempt.score))
        .filter(QuizAttempt.user_id == user_id, QuizAttempt.status == "completed")
        .scalar()
    )
    last_activity_candidates = [
        db.session.query(func.max(LessonProgress.last_opened_at)).filter(LessonProgress.user_id == user_id).scalar(),
        db.session.query(func.max(Submission.submitted_at)).filter(Submission.user_id == user_id).scalar(),
        db.session.query(func.max(QuizAttempt.started_at)).filter(QuizAttempt.user_id == user_id).scalar(),
    ]
    return {
        "active_courses": CourseEnrollment.query.filter_by(user_id=user_id, status="in_progress").count(),
        "completed_courses": CourseEnrollment.query.filter_by(user_id=user_id, status="completed").count(),
        "completed_lessons": LessonProgress.query.filter_by(user_id=user_id, status="completed").count(),
        "completed_tasks": db.session.query(func.count(func.distinct(Submission.task_id))).filter(
            Submission.user_id == user_id,
            Submission.status == "accepted",
        ).scalar() or 0,
        "quiz_attempts": QuizAttempt.query.filter_by(user_id=user_id).count(),
        "average_quiz_score": round(float(average_quiz_score or 0), 1),
        "achievements": UserAchievement.query.filter_by(user_id=user_id).count(),
        "last_activity": max((value for value in last_activity_candidates if value), default=None),
    }
