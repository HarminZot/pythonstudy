from flask import jsonify, request
from flask_login import current_user, login_required

from . import bp
from ..extensions import db
from ..models import CourseEnrollment, Lesson, LessonProgress, Notification, ProgrammingTask, Submission
from ..services.achievement_service import evaluate_achievements
from ..services.code_runner import run_python_code
from ..services.grading_service import grade_submission
from ..services.helpers import utcnow
from ..services.progress_service import calculate_course_progress


def _student_access(task):
    if not current_user.is_authenticated or not current_user.has_role("student"):
        return False
    return CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=task.lesson.module.course_id).first() is not None


@bp.route("/code/run", methods=["POST"])
@login_required
def code_run():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    input_data = payload.get("input", "")
    task_id = payload.get("task_id")
    task = ProgrammingTask.query.get(task_id) if task_id else None
    if task and not _student_access(task) and not current_user.has_role("teacher", "admin"):
        return jsonify({"error": "Доступ запрещен"}), 403
    result = run_python_code(
        code,
        input_data=input_data,
        timeout=float(task.time_limit_seconds) if task else None,
        memory_mb=task.memory_limit_mb if task else None,
        allowed_imports=task.allowed_imports if task else [],
    )
    return jsonify(result.to_dict())


@bp.route("/tasks/<int:task_id>/submit", methods=["POST"])
@login_required
def task_submit(task_id):
    task = ProgrammingTask.query.filter_by(id=task_id, status="published").first_or_404()
    if not _student_access(task):
        return jsonify({"error": "Доступ запрещен"}), 403
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    submission = Submission(task_id=task.id, user_id=current_user.id, code=code)
    db.session.add(submission)
    db.session.flush()
    grade_submission(submission)
    db.session.commit()
    return jsonify({
        "id": submission.id,
        "status": submission.status,
        "score": float(submission.score),
        "passed_tests": submission.passed_tests,
        "total_tests": submission.total_tests,
        "redirect": f"/student/submissions/{submission.id}",
    })


@bp.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@login_required
def lesson_complete(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=lesson.module.course_id).first()
    if not enrollment:
        return jsonify({"error": "Доступ запрещен"}), 403
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson.id)
        db.session.add(progress)
    progress.status = "completed"
    progress.completed_at = utcnow()
    calculate_course_progress(current_user.id, lesson.module.course_id)
    evaluate_achievements(current_user.id)
    db.session.commit()
    return jsonify({"status": "completed"})


@bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def notification_read(notification_id):
    item = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    item.is_read = True
    item.read_at = utcnow()
    db.session.commit()
    return jsonify({"status": "ok"})


@bp.route("/notifications/read-all", methods=["POST"])
@login_required
def notifications_read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True, "read_at": utcnow()})
    db.session.commit()
    return jsonify({"status": "ok"})
