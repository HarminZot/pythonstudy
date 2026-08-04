from flask import abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user

from . import bp
from ..decorators import roles_required
from ..extensions import db
from ..models import (
    Course, CourseEnrollment, Lesson, LessonProgress, Notification, ProgrammingTask,
    Quiz, QuizAnswer, QuizAttempt, Submission, UserAchievement,
)
from ..services.achievement_service import evaluate_achievements
from ..services.export_service import build_certificate_pdf, build_student_docx, build_student_xlsx
from ..services.helpers import utcnow
from ..services.progress_service import calculate_course_progress


def _require_enrollment(course_id):
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        abort(403)
    return enrollment


@bp.route("/dashboard")
@roles_required("student")
def dashboard():
    enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id).all()
    recent_submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.submitted_at.desc()).limit(5).all()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template("student/dashboard.html", enrollments=enrollments, recent_submissions=recent_submissions, unread=unread)


@bp.route("/courses")
@roles_required("student")
def my_courses():
    enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id).all()
    return render_template("student/courses.html", enrollments=enrollments, breadcrumbs=[("Главная", "public.index"), ("Мои курсы", None)])


@bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
@roles_required("student")
def enroll(course_id):
    course = Course.query.filter_by(id=course_id, status="published").first_or_404()
    enrollment = CourseEnrollment.query.filter_by(course_id=course.id, user_id=current_user.id).first()
    if not enrollment:
        enrollment = CourseEnrollment(course_id=course.id, user_id=current_user.id)
        db.session.add(enrollment)
        db.session.commit()
        flash("Вы записаны на курс.", "success")
    return redirect(url_for("public.course_detail", slug=course.slug))


@bp.route("/lessons/<int:lesson_id>")
@roles_required("student")
def lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.module.course
    _require_enrollment(course.id)
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson.id, status="in_progress", started_at=utcnow())
        db.session.add(progress)
    else:
        progress.last_opened_at = utcnow()
        if progress.status == "not_started":
            progress.status = "in_progress"
    db.session.commit()
    return render_template(
        "student/lesson.html",
        lesson=lesson,
        course=course,
        progress=progress,
        breadcrumbs=[("Главная", "public.index"), ("Мои курсы", "student.my_courses"), (course.title, lambda: url_for("public.course_detail", slug=course.slug)), (lesson.title, None)],
    )


@bp.route("/tasks/<int:task_id>")
@roles_required("student")
def task(task_id):
    task = ProgrammingTask.query.filter_by(id=task_id, status="published").first_or_404()
    _require_enrollment(task.lesson.module.course_id)
    submissions = Submission.query.filter_by(task_id=task.id, user_id=current_user.id).order_by(Submission.submitted_at.desc()).limit(10).all()
    return render_template("student/task.html", task=task, submissions=submissions, breadcrumbs=[("Главная", "public.index"), (task.lesson.module.course.title, lambda: url_for("public.course_detail", slug=task.lesson.module.course.slug)), (task.title, None)])


@bp.route("/submissions")
@roles_required("student")
def submissions():
    items = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    return render_template("student/submissions.html", submissions=items, breadcrumbs=[("Главная", "public.index"), ("История решений", None)])


@bp.route("/submissions/<int:submission_id>")
@roles_required("student")
def submission_detail(submission_id):
    submission = Submission.query.filter_by(id=submission_id, user_id=current_user.id).first_or_404()
    return render_template("student/submission_detail.html", submission=submission, breadcrumbs=[("Главная", "public.index"), ("История решений", "student.submissions"), (f"Решение №{submission.id}", None)])


@bp.route("/quizzes/<int:quiz_id>", methods=["GET", "POST"])
@roles_required("student")
def quiz(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, status="published").first_or_404()
    course_id = quiz.course_id or quiz.lesson.module.course_id
    _require_enrollment(course_id)
    attempts_count = QuizAttempt.query.filter_by(quiz_id=quiz.id, user_id=current_user.id).count()
    if request.method == "GET":
        return render_template("student/quiz.html", quiz=quiz, attempts_count=attempts_count, breadcrumbs=[("Главная", "public.index"), (quiz.title, None)])
    if attempts_count >= quiz.max_attempts:
        flash("Количество попыток исчерпано.", "danger")
        return redirect(url_for("student.quiz", quiz_id=quiz.id))

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        attempt_number=attempts_count + 1,
        total_questions=len(quiz.questions),
        status="completed",
        finished_at=utcnow(),
    )
    db.session.add(attempt)
    db.session.flush()
    total_points = sum(q.points for q in quiz.questions) or 1
    earned = 0
    correct_count = 0
    for question in quiz.questions:
        raw_values = request.form.getlist(f"question_{question.id}")
        text_value = request.form.get(f"question_{question.id}_text", "").strip()
        selected_ids = [int(value) for value in raw_values if value.isdigit()]
        correct_ids = sorted(option.id for option in question.options if option.is_correct)
        if question.question_type in {"single_choice", "multiple_choice"}:
            is_correct = sorted(selected_ids) == correct_ids
        else:
            is_correct = text_value.casefold() == (question.correct_text_answer or "").strip().casefold()
        points = question.points if is_correct else 0
        earned += points
        correct_count += int(is_correct)
        db.session.add(QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_ids=selected_ids or None,
            answer_text=text_value or None,
            is_correct=is_correct,
            awarded_points=points,
        ))
    attempt.correct_answers = correct_count
    attempt.score = round(earned * 100 / total_points, 2)
    calculate_course_progress(current_user.id, course_id)
    evaluate_achievements(current_user.id)
    db.session.commit()
    return redirect(url_for("student.quiz_result", attempt_id=attempt.id))


@bp.route("/quiz-results/<int:attempt_id>")
@roles_required("student")
def quiz_result(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    return render_template("student/quiz_result.html", attempt=attempt, breadcrumbs=[("Главная", "public.index"), ("Результат теста", None)])


@bp.route("/progress")
@roles_required("student")
def progress():
    for enrollment in current_user.enrollments:
        calculate_course_progress(current_user.id, enrollment.course_id)
    db.session.commit()
    return render_template("student/progress.html", enrollments=current_user.enrollments, breadcrumbs=[("Главная", "public.index"), ("Прогресс", None)])


@bp.route("/achievements")
@roles_required("student")
def achievements():
    awards = UserAchievement.query.filter_by(user_id=current_user.id).all()
    return render_template("student/achievements.html", awards=awards, breadcrumbs=[("Главная", "public.index"), ("Достижения", None)])


@bp.route("/notifications")
@roles_required("student", "teacher", "admin")
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("student/notifications.html", notifications=items, breadcrumbs=[("Главная", "public.index"), ("Уведомления", None)])


@bp.route("/profile", methods=["GET", "POST"])
@roles_required("student", "teacher", "admin")
def profile():
    if request.method == "POST":
        current_user.last_name = request.form.get("last_name", "").strip() or current_user.last_name
        current_user.first_name = request.form.get("first_name", "").strip() or current_user.first_name
        current_user.middle_name = request.form.get("middle_name", "").strip() or None
        new_password = request.form.get("new_password", "")
        if new_password:
            if len(new_password) < 8:
                flash("Пароль должен содержать не менее восьми символов.", "danger")
                return redirect(url_for("student.profile"))
            current_user.set_password(new_password)
        db.session.commit()
        flash("Профиль обновлен.", "success")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html", breadcrumbs=[("Главная", "public.index"), ("Профиль", None)])


@bp.route("/export/xlsx")
@roles_required("student")
def export_xlsx():
    return send_file(build_student_xlsx(current_user), download_name="student_report.xlsx", as_attachment=True)


@bp.route("/export/docx")
@roles_required("student")
def export_docx():
    return send_file(build_student_docx(current_user), download_name="student_report.docx", as_attachment=True)


@bp.route("/courses/<int:course_id>/certificate")
@roles_required("student")
def certificate(course_id):
    enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first_or_404()
    if enrollment.status != "completed" and float(enrollment.progress_percent) < 100:
        abort(403)
    return send_file(
        build_certificate_pdf(current_user, enrollment.course),
        download_name=f"certificate_{course_id}.pdf",
        as_attachment=True,
        mimetype="application/pdf",
    )
