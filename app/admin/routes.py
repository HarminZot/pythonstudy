from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from . import bp
from ..decorators import roles_required
from ..extensions import db
from ..models import AuditLog, Course, FeedbackMessage, FeedbackRequest, Role, SystemSetting, User
from ..services.audit_service import log_action
from ..services.helpers import utcnow
from ..services.notification_service import notify
from ..services.statistics_service import admin_statistics


@bp.route("/")
@roles_required("admin")
def dashboard():
    return render_template("admin/dashboard.html", stats=admin_statistics())


@bp.route("/users")
@roles_required("admin")
def users():
    query = request.args.get("q", "").strip()
    users_query = User.query
    if query:
        users_query = users_query.filter((User.email.ilike(f"%{query}%")) | (User.last_name.ilike(f"%{query}%")))
    return render_template("admin/users.html", users=users_query.order_by(User.created_at.desc()).all(), q=query, breadcrumbs=[("Главная", "public.index"), ("Пользователи", None)])


@bp.route("/users/create", methods=["GET", "POST"])
@roles_required("admin")
def user_create():
    roles = Role.query.order_by(Role.name).all()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = Role.query.filter_by(code=request.form.get("role_code", "student")).first()
        if not email or "@" not in email:
            flash("Укажите корректный email.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует.", "danger")
        elif len(password) < 8:
            flash("Пароль должен содержать не менее 8 символов.", "danger")
        elif not role:
            flash("Выберите существующую роль.", "danger")
        else:
            user = User(
                role=role,
                email=email,
                last_name=request.form.get("last_name", "").strip() or "Пользователь",
                first_name=request.form.get("first_name", "").strip() or "Новый",
                middle_name=request.form.get("middle_name", "").strip() or None,
                status=request.form.get("status", "active"),
                is_email_verified=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            log_action("admin.user_create", "user", user.id)
            db.session.commit()
            flash("Пользователь создан.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_create.html", roles=roles, breadcrumbs=[("Главная", "public.index"), ("Пользователи", "admin.users"), ("Новый пользователь", None)])


@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@roles_required("admin")
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        role = Role.query.filter_by(code=request.form.get("role_code")).first()
        if role:
            user.role = role
        user.status = request.form.get("status", user.status)
        user.last_name = request.form.get("last_name", user.last_name).strip()
        user.first_name = request.form.get("first_name", user.first_name).strip()
        password = request.form.get("password", "")
        if password:
            user.set_password(password)
        log_action("admin.user_update", "user", user.id)
        db.session.commit()
        flash("Пользователь обновлен.", "success")
        return redirect(url_for("admin.users"))
    roles = Role.query.order_by(Role.name).all()
    return render_template("admin/user_form.html", user=user, roles=roles, breadcrumbs=[("Главная", "public.index"), ("Пользователи", "admin.users"), (user.full_name, None)])


@bp.route("/courses")
@roles_required("admin")
def courses():
    return render_template("admin/courses.html", courses=Course.query.order_by(Course.created_at.desc()).all(), breadcrumbs=[("Главная", "public.index"), ("Все курсы", None)])


@bp.post("/courses/<int:course_id>/status")
@roles_required("admin")
def course_status(course_id):
    course = Course.query.get_or_404(course_id)
    status = request.form.get("status", "")
    if status not in {"draft", "published", "archived"}:
        flash("Неизвестный статус курса.", "danger")
    else:
        previous_status = course.status
        course.status = status
        if status == "published" and not course.published_at:
            course.published_at = utcnow()
        log_action("admin.course_status", "course", course.id, {"from": previous_status, "to": status})
        db.session.commit()
        flash("Статус курса обновлен.", "success")
    return redirect(url_for("admin.courses"))


@bp.route("/feedback")
@roles_required("admin")
def feedback():
    items = FeedbackRequest.query.order_by(FeedbackRequest.created_at.desc()).all()
    return render_template("admin/feedback.html", requests=items, breadcrumbs=[("Главная", "public.index"), ("Обращения", None)])


@bp.route("/feedback/<int:request_id>", methods=["GET", "POST"])
@roles_required("admin")
def feedback_detail(request_id):
    item = FeedbackRequest.query.get_or_404(request_id)
    if request.method == "POST":
        text = request.form.get("message", "").strip()
        if text:
            db.session.add(FeedbackMessage(request_id=item.id, author_id=current_user.id, message=text))
            item.assigned_admin_id = current_user.id
            item.status = request.form.get("status", "in_progress")
            if item.status == "resolved":
                item.closed_at = utcnow()
            if item.user_id:
                notify(item.user_id, "Ответ на обращение", text[:200], "feedback_reply", url_for("public.feedback"))
            db.session.commit()
            flash("Ответ сохранен.", "success")
        return redirect(url_for("admin.feedback_detail", request_id=item.id))
    return render_template("admin/feedback_detail.html", item=item, breadcrumbs=[("Главная", "public.index"), ("Обращения", "admin.feedback"), (f"Обращение №{item.id}", None)])


@bp.route("/audit")
@roles_required("admin")
def audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(500).all()
    return render_template("admin/audit_logs.html", logs=logs, breadcrumbs=[("Главная", "public.index"), ("Журнал действий", None)])


@bp.route("/statistics")
@roles_required("admin")
def statistics():
    return render_template("admin/statistics.html", stats=admin_statistics(), breadcrumbs=[("Главная", "public.index"), ("Статистика", None)])


@bp.route("/settings", methods=["GET", "POST"])
@roles_required("admin")
def settings():
    defaults = {
        "site_name": ("PythonStudy", "string", "general"),
        "registration_enabled": ("true", "boolean", "registration"),
        "code_time_limit": ("3", "integer", "code_execution"),
        "code_memory_limit": ("128", "integer", "code_execution"),
        "passing_score": ("70", "integer", "education"),
        "notifications_enabled": ("true", "boolean", "notifications"),
        "max_file_size_mb": ("10", "integer", "files"),
    }
    for key, (value, value_type, group) in defaults.items():
        if not SystemSetting.query.filter_by(setting_key=key).first():
            db.session.add(SystemSetting(setting_key=key, setting_value=value, value_type=value_type, group_name=group))
    db.session.commit()
    if request.method == "POST":
        for setting in SystemSetting.query.all():
            if setting.setting_key in request.form:
                setting.setting_value = request.form[setting.setting_key]
                setting.updated_by = current_user.id
        log_action("settings.update", "system_settings")
        db.session.commit()
        flash("Настройки сохранены.", "success")
        return redirect(url_for("admin.settings"))
    groups = {}
    for setting in SystemSetting.query.order_by(SystemSetting.group_name, SystemSetting.setting_key).all():
        groups.setdefault(setting.group_name, []).append(setting)
    return render_template("admin/settings.html", groups=groups, breadcrumbs=[("Главная", "public.index"), ("Настройки", None)])
