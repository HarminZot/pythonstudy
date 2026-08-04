import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urljoin, urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from . import bp
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from ..extensions import db
from ..models import PasswordResetToken, Role, User
from ..services.audit_service import log_action
from ..services.helpers import utcnow


def _is_safe_redirect(target):
    if not target:
        return False
    host = urlsplit(request.host_url)
    destination = urlsplit(urljoin(request.host_url, target))
    return destination.scheme in {"http", "https"} and destination.netloc == host.netloc


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard" if current_user.has_role("student") else "public.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if not user or not user.check_password(form.password.data):
            flash("Неверная электронная почта или пароль.", "danger")
        elif not user.is_active_account:
            flash("Учетная запись заблокирована.", "danger")
        else:
            login_user(user, remember=form.remember.data)
            user.last_login_at = utcnow()
            log_action("user.login", "user", user.id, user=user)
            db.session.commit()
            next_url = request.args.get("next")
            destination = next_url if _is_safe_redirect(next_url) else None
            return redirect(destination or url_for("student.dashboard" if user.has_role("student") else "public.index"))
    return render_template("auth/login.html", form=form, breadcrumbs=[("Главная", "public.index"), ("Вход", None)])


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("Пользователь с такой электронной почтой уже существует.", "danger")
        else:
            role = Role.query.filter_by(code="student").first()
            if not role:
                role = Role(code="student", name="Студент")
                db.session.add(role)
                db.session.flush()
            user = User(
                role=role,
                email=email,
                last_name=form.last_name.data.strip(),
                first_name=form.first_name.data.strip(),
                middle_name=(form.middle_name.data or "").strip() or None,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            log_action("user.register", "user", user.id, user=user)
            db.session.commit()
            flash("Регистрация завершена. Войдите в систему.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form, breadcrumbs=[("Главная", "public.index"), ("Регистрация", None)])


@bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        log_action("user.logout", "user", current_user.id)
        db.session.commit()
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("public.index"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            raw_token = secrets.token_urlsafe(32)
            token = PasswordResetToken(
                user_id=user.id,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=utcnow() + timedelta(hours=1),
            )
            db.session.add(token)
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=raw_token, _external=True)
            flash(f"Демонстрационная ссылка для восстановления: {reset_url}", "info")
        else:
            flash("Если адрес зарегистрирован, ссылка будет сформирована.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("auth/forgot_password.html", form=form, breadcrumbs=[("Главная", "public.index"), ("Восстановление пароля", None)])


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = PasswordResetToken.query.filter_by(token_hash=token_hash, used_at=None).first_or_404()
    now = utcnow()
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        now = now.replace(tzinfo=None)
    if expires_at < now:
        flash("Срок действия ссылки истек.", "danger")
        return redirect(url_for("auth.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        record.user.set_password(form.password.data)
        record.used_at = utcnow()
        db.session.commit()
        flash("Пароль изменен.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form, breadcrumbs=[("Главная", "public.index"), ("Новый пароль", None)])
