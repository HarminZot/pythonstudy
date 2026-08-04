from sqlalchemy import func

from ..extensions import db
from ..models import Course, CourseEnrollment, CourseModule, Lesson, ProgrammingTask, Submission, User


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
