from flask import abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from sqlalchemy import func, or_, select

from . import bp
from .forms import FeedbackForm
from ..extensions import db
from ..models import Course, CourseEnrollment, FeedbackRequest, LessonMaterial, UploadedFile, User
from ..services.audit_service import log_action
from ..services.file_service import save_upload


@bp.route("/")
def index():
    courses = Course.query.filter_by(status="published").order_by(Course.published_at.desc()).limit(6).all()
    return render_template("public/index.html", courses=courses)


@bp.route("/courses")
def courses():
    search = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    teacher_id = request.args.get("teacher", type=int)
    sort = request.args.get("sort", "title")
    query = Course.query.filter_by(status="published")
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Course.title.ilike(pattern), Course.short_description.ilike(pattern)))
    if difficulty in {"beginner", "intermediate", "advanced"}:
        query = query.filter(Course.difficulty == difficulty)
    if teacher_id:
        query = query.filter(Course.teacher_id == teacher_id)
    if sort == "newest":
        query = query.order_by(Course.published_at.desc(), Course.title)
    elif sort == "popular":
        enrollment_count = (
            select(func.count(CourseEnrollment.id))
            .where(CourseEnrollment.course_id == Course.id)
            .correlate(Course)
            .scalar_subquery()
        )
        query = query.order_by(enrollment_count.desc(), Course.title)
    else:
        sort = "title"
        query = query.order_by(Course.title)
    courses = query.all()
    teachers = (
        User.query.join(Course, Course.teacher_id == User.id)
        .filter(Course.status == "published")
        .distinct()
        .order_by(User.last_name, User.first_name)
        .all()
    )
    return render_template(
        "public/courses.html",
        courses=courses,
        search=search,
        difficulty=difficulty,
        teacher_id=teacher_id,
        teachers=teachers,
        sort=sort,
        breadcrumbs=[("Главная", "public.index"), ("Каталог курсов", None)],
    )


@bp.route("/courses/<slug>")
def course_detail(slug):
    course = Course.query.filter_by(slug=slug, status="published").first_or_404()
    enrollment = None
    if current_user.is_authenticated:
        enrollment = next((item for item in current_user.enrollments if item.course_id == course.id), None)
    return render_template(
        "public/course_detail.html",
        course=course,
        enrollment=enrollment,
        breadcrumbs=[("Главная", "public.index"), ("Каталог курсов", "public.courses"), (course.title, None)],
    )


@bp.route("/courses/<int:course_id>/cover")
def course_cover(course_id):
    course = Course.query.filter_by(id=course_id, status="published").first_or_404()
    if not course.cover_path:
        abort(404)
    return send_file(course.cover_path, conditional=True, max_age=3600)


@bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    form = FeedbackForm()
    if current_user.is_authenticated and not form.email.data:
        form.email.data = current_user.email
    if form.validate_on_submit():
        attachment = None
        if form.attachment.data:
            owner_id = current_user.id if current_user.is_authenticated else None
            attachment = save_upload(form.attachment.data, owner_id, "feedback")
        request_record = FeedbackRequest(
            user_id=current_user.id if current_user.is_authenticated else None,
            attachment_file_id=attachment.id if attachment else None,
            email=form.email.data.lower().strip(),
            category=form.category.data,
            subject=form.subject.data.strip(),
            message=form.message.data.strip(),
        )
        db.session.add(request_record)
        db.session.flush()
        log_action("feedback.create", "feedback_request", request_record.id)
        db.session.commit()
        flash("Обращение зарегистрировано.", "success")
        return redirect(url_for("public.feedback"))
    return render_template("public/feedback.html", form=form, breadcrumbs=[("Главная", "public.index"), ("Обратная связь", None)])


@bp.route("/help")
def help_page():
    return render_template("public/help.html", breadcrumbs=[("Главная", "public.index"), ("Справка", None)])


@bp.route("/about")
def about():
    return render_template("public/about.html", breadcrumbs=[("Главная", "public.index"), ("О системе", None)])


@bp.route("/files/<int:file_id>/download")
def download_file(file_id):
    item = UploadedFile.query.filter_by(id=file_id, is_deleted=False).first_or_404()
    if item.category == "feedback":
        allowed = current_user.is_authenticated and (
            current_user.has_role("admin") or item.owner_id == current_user.id
        )
        if not allowed:
            abort(403)
    elif item.category == "lesson_materials":
        material = LessonMaterial.query.filter_by(file_id=item.id).first()
        if not material:
            abort(404)
        course_id = material.lesson.module.course_id
        if not current_user.is_authenticated:
            abort(403)
        if current_user.has_role("student"):
            enrollment = CourseEnrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
            if not enrollment:
                abort(403)
        elif current_user.has_role("teacher") and material.lesson.module.course.teacher_id != current_user.id:
            abort(403)
    return send_file(item.storage_path, download_name=item.original_name, as_attachment=True)
