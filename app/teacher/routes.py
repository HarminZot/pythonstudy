import re
from io import BytesIO

from flask import abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from openpyxl import Workbook

from . import bp
from ..decorators import roles_required
from ..extensions import db
from ..models import Course, CourseModule, Lesson, LessonMaterial, ProgrammingTask, Quiz, QuizOption, QuizQuestion, Submission, TaskTestCase
from ..services.audit_service import log_action
from ..services.helpers import utcnow
from ..services.file_service import save_upload
from ..services.notification_service import notify
from ..services.statistics_service import teacher_statistics
from ..services.export_service import build_task_submissions_xlsx


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.IGNORECASE)
    return value.strip("-") or "item"


def _own_course(course_id):
    query = Course.query.filter_by(id=course_id)
    if not current_user.has_role("admin"):
        query = query.filter_by(teacher_id=current_user.id)
    return query.first_or_404()


@bp.route("/dashboard")
@roles_required("teacher", "admin")
def dashboard():
    stats = teacher_statistics(current_user.id) if current_user.has_role("teacher") else {}
    courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.created_at.desc()).all()
    return render_template("teacher/dashboard.html", stats=stats, courses=courses)


@bp.route("/courses")
@roles_required("teacher", "admin")
def courses():
    query = Course.query
    if current_user.has_role("teacher"):
        query = query.filter_by(teacher_id=current_user.id)
    return render_template("teacher/courses.html", courses=query.order_by(Course.created_at.desc()).all(), breadcrumbs=[("Главная", "public.index"), ("Курсы преподавателя", None)])


@bp.route("/courses/create", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def course_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Название обязательно.", "danger")
        else:
            base_slug = slugify(request.form.get("slug") or title)
            slug = base_slug
            number = 2
            while Course.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{number}"
                number += 1
            course = Course(
                teacher_id=current_user.id,
                title=title,
                slug=slug,
                short_description=request.form.get("short_description", "").strip() or title,
                full_description=request.form.get("full_description", "").strip() or title,
                difficulty=request.form.get("difficulty", "beginner"),
                status=request.form.get("status", "draft"),
                estimated_hours=max(1, int(request.form.get("estimated_hours", 1))),
                passing_score=min(100, max(1, int(request.form.get("passing_score", 70)))),
                is_sequential=bool(request.form.get("is_sequential")),
                published_at=utcnow() if request.form.get("status") == "published" else None,
            )
            db.session.add(course)
            db.session.flush()
            cover = request.files.get("cover")
            if cover and cover.filename:
                stored = save_upload(cover, current_user.id, "course_covers")
                course.cover_path = stored.storage_path
            log_action("course.create", "course", course.id)
            db.session.commit()
            flash("Курс создан.", "success")
            return redirect(url_for("teacher.course_modules", course_id=course.id))
    return render_template("teacher/course_form.html", course=None, breadcrumbs=[("Главная", "public.index"), ("Курсы", "teacher.courses"), ("Новый курс", None)])


@bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def course_edit(course_id):
    course = _own_course(course_id)
    if request.method == "POST":
        course.title = request.form.get("title", course.title).strip()
        course.short_description = request.form.get("short_description", course.short_description).strip()
        course.full_description = request.form.get("full_description", course.full_description).strip()
        course.difficulty = request.form.get("difficulty", course.difficulty)
        old_status = course.status
        course.status = request.form.get("status", course.status)
        course.estimated_hours = max(1, int(request.form.get("estimated_hours", course.estimated_hours)))
        course.passing_score = min(100, max(1, int(request.form.get("passing_score", course.passing_score))))
        course.is_sequential = bool(request.form.get("is_sequential"))
        cover = request.files.get("cover")
        if cover and cover.filename:
            stored = save_upload(cover, current_user.id, "course_covers")
            course.cover_path = stored.storage_path
        if old_status != "published" and course.status == "published":
            course.published_at = utcnow()
        log_action("course.update", "course", course.id)
        db.session.commit()
        flash("Курс обновлен.", "success")
        return redirect(url_for("teacher.courses"))
    return render_template("teacher/course_form.html", course=course, breadcrumbs=[("Главная", "public.index"), ("Курсы", "teacher.courses"), (course.title, None)])


@bp.route("/courses/<int:course_id>/modules", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def course_modules(course_id):
    course = _own_course(course_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            next_order = max([m.order_index for m in course.modules], default=0) + 1
            db.session.add(CourseModule(course_id=course.id, title=title, description=request.form.get("description"), order_index=next_order))
            db.session.commit()
            flash("Модуль добавлен.", "success")
        return redirect(url_for("teacher.course_modules", course_id=course.id))
    return render_template("teacher/modules.html", course=course, breadcrumbs=[("Главная", "public.index"), ("Курсы", "teacher.courses"), (course.title, None)])


@bp.route("/modules/<int:module_id>/lessons", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def module_lessons(module_id):
    module = CourseModule.query.get_or_404(module_id)
    _own_course(module.course_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            order_index = max([item.order_index for item in module.lessons], default=0) + 1
            lesson = Lesson(
                module_id=module.id,
                title=title,
                slug=slugify(title),
                summary=request.form.get("summary", ""),
                content=request.form.get("content", "<p>Материал урока</p>"),
                lesson_type=request.form.get("lesson_type", "mixed"),
                order_index=order_index,
                estimated_minutes=int(request.form.get("estimated_minutes", 30)),
                is_published=bool(request.form.get("is_published")),
            )
            db.session.add(lesson)
            db.session.commit()
            flash("Урок добавлен.", "success")
        return redirect(url_for("teacher.module_lessons", module_id=module.id))
    return render_template("teacher/lessons.html", module=module, breadcrumbs=[("Главная", "public.index"), (module.course.title, lambda: url_for("teacher.course_modules", course_id=module.course_id)), (module.title, None)])


@bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def lesson_edit(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    _own_course(lesson.module.course_id)
    if request.method == "POST":
        lesson.title = request.form.get("title", lesson.title).strip()
        lesson.summary = request.form.get("summary", "").strip()
        lesson.content = request.form.get("content", lesson.content)
        lesson.lesson_type = request.form.get("lesson_type", lesson.lesson_type)
        lesson.estimated_minutes = int(request.form.get("estimated_minutes", lesson.estimated_minutes))
        lesson.is_published = bool(request.form.get("is_published"))
        material = request.files.get("material")
        if material and material.filename:
            stored = save_upload(material, current_user.id, "lesson_materials")
            db.session.flush()
            db.session.add(LessonMaterial(
                lesson_id=lesson.id,
                file_id=stored.id,
                title=request.form.get("material_title", "Материал урока").strip() or stored.original_name,
                material_type="document",
                order_index=max([m.order_index for m in lesson.materials], default=0) + 1,
            ))
        db.session.commit()
        flash("Урок обновлен.", "success")
        return redirect(url_for("teacher.module_lessons", module_id=lesson.module_id))
    return render_template("teacher/lesson_form.html", lesson=lesson, breadcrumbs=[("Главная", "public.index"), (lesson.title, None)])


@bp.route("/lessons/<int:lesson_id>/tasks", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def lesson_tasks(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    _own_course(lesson.module.course_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            task = ProgrammingTask(
                lesson_id=lesson.id,
                created_by=current_user.id,
                title=title,
                slug=slugify(title),
                description=request.form.get("description", "Решите задачу"),
                input_description=request.form.get("input_description"),
                output_description=request.form.get("output_description"),
                examples=request.form.get("examples"),
                starter_code=request.form.get("starter_code", "# код решения\n"),
                reference_solution=request.form.get("reference_solution"),
                difficulty=request.form.get("difficulty", "beginner"),
                points=int(request.form.get("points", 10)),
                time_limit_seconds=float(request.form.get("time_limit_seconds", 2)),
                memory_limit_mb=int(request.form.get("memory_limit_mb", 256)),
                status=request.form.get("status", "draft"),
                order_index=max([t.order_index for t in lesson.tasks], default=0) + 1,
            )
            db.session.add(task)
            db.session.commit()
            flash("Задание создано.", "success")
        return redirect(url_for("teacher.lesson_tasks", lesson_id=lesson.id))
    return render_template("teacher/tasks.html", lesson=lesson, breadcrumbs=[("Главная", "public.index"), (lesson.title, None), ("Задания", None)])


@bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def task_edit(task_id):
    task = ProgrammingTask.query.get_or_404(task_id)
    _own_course(task.lesson.module.course_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Название обязательно.", "danger")
        else:
            task.title = title
            task.description = request.form.get("description", "").strip()
            task.input_description = request.form.get("input_description", "").strip() or None
            task.output_description = request.form.get("output_description", "").strip() or None
            task.examples = request.form.get("examples", "").strip() or None
            task.starter_code = request.form.get("starter_code", "")
            task.reference_solution = request.form.get("reference_solution", "") or None
            task.difficulty = request.form.get("difficulty", "beginner")
            task.points = max(1, int(request.form.get("points", 10)))
            task.time_limit_seconds = max(0.1, float(request.form.get("time_limit_seconds", 2)))
            task.memory_limit_mb = max(16, int(request.form.get("memory_limit_mb", 256)))
            task.status = request.form.get("status", "draft")
            log_action("task.update", "programming_task", task.id)
            db.session.commit()
            flash("Задание обновлено.", "success")
            return redirect(url_for("teacher.lesson_tasks", lesson_id=task.lesson_id))
    return render_template("teacher/task_form.html", task=task, breadcrumbs=[("Главная", "public.index"), (task.title, None)])


@bp.route("/tasks/<int:task_id>/test-cases", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def test_cases(task_id):
    task = ProgrammingTask.query.get_or_404(task_id)
    _own_course(task.lesson.module.course_id)
    if request.method == "POST":
        db.session.add(TaskTestCase(
            task_id=task.id,
            name=request.form.get("name", "Новый тест"),
            input_data=request.form.get("input_data", ""),
            expected_output=request.form.get("expected_output", ""),
            is_hidden=bool(request.form.get("is_hidden")),
            weight=max(1, int(request.form.get("weight", 1))),
            order_index=max([c.order_index for c in task.test_cases], default=0) + 1,
        ))
        db.session.commit()
        flash("Тестовый случай добавлен.", "success")
        return redirect(url_for("teacher.test_cases", task_id=task.id))
    return render_template("teacher/test_cases.html", task=task, breadcrumbs=[("Главная", "public.index"), (task.title, None), ("Тестовые случаи", None)])


@bp.route("/tasks/<int:task_id>/submissions/export")
@roles_required("teacher", "admin")
def task_submissions_export(task_id):
    task = ProgrammingTask.query.get_or_404(task_id)
    _own_course(task.lesson.module.course_id)
    return send_file(build_task_submissions_xlsx(task), download_name=f"task_{task.id}_submissions.xlsx", as_attachment=True)


@bp.route("/test-cases/<int:case_id>/edit", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def test_case_edit(case_id):
    test_case = TaskTestCase.query.get_or_404(case_id)
    _own_course(test_case.task.lesson.module.course_id)
    if request.method == "POST":
        test_case.name = request.form.get("name", "").strip() or "Тестовый случай"
        test_case.input_data = request.form.get("input_data", "")
        test_case.expected_output = request.form.get("expected_output", "")
        test_case.weight = max(1, int(request.form.get("weight", 1)))
        test_case.is_hidden = bool(request.form.get("is_hidden"))
        timeout = request.form.get("timeout_seconds", "").strip()
        test_case.timeout_seconds = max(0.1, float(timeout)) if timeout else None
        log_action("test_case.update", "task_test_case", test_case.id)
        db.session.commit()
        flash("Тестовый случай обновлен.", "success")
        return redirect(url_for("teacher.test_cases", task_id=test_case.task_id))
    return render_template("teacher/test_case_form.html", test_case=test_case, breadcrumbs=[("Главная", "public.index"), (test_case.name, None)])


@bp.post("/test-cases/<int:case_id>/delete")
@roles_required("teacher", "admin")
def test_case_delete(case_id):
    test_case = TaskTestCase.query.get_or_404(case_id)
    _own_course(test_case.task.lesson.module.course_id)
    task_id = test_case.task_id
    log_action("test_case.delete", "task_test_case", test_case.id)
    db.session.delete(test_case)
    db.session.commit()
    flash("Тестовый случай удален.", "success")
    return redirect(url_for("teacher.test_cases", task_id=task_id))


@bp.route("/courses/<int:course_id>/quizzes", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def course_quizzes(course_id):
    course = _own_course(course_id)
    if request.method == "POST":
        quiz = Quiz(
            course_id=course.id,
            created_by=current_user.id,
            title=request.form.get("title", "Новый тест"),
            description=request.form.get("description"),
            passing_score=int(request.form.get("passing_score", 70)),
            max_attempts=int(request.form.get("max_attempts", 3)),
            status=request.form.get("status", "draft"),
        )
        db.session.add(quiz)
        db.session.commit()
        flash("Тест создан.", "success")
        return redirect(url_for("teacher.quiz_questions", quiz_id=quiz.id))
    return render_template("teacher/quizzes.html", course=course, breadcrumbs=[("Главная", "public.index"), (course.title, None), ("Тесты", None)])


@bp.route("/quizzes/<int:quiz_id>/questions", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def quiz_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    _own_course(quiz.course_id or quiz.lesson.module.course_id)
    if request.method == "POST":
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_type=request.form.get("question_type", "single_choice"),
            question_text=request.form.get("question_text", "Новый вопрос"),
            correct_text_answer=request.form.get("correct_text_answer") or None,
            points=max(1, int(request.form.get("points", 1))),
            order_index=max([q.order_index for q in quiz.questions], default=0) + 1,
        )
        db.session.add(question)
        db.session.flush()
        options = request.form.get("options", "").splitlines()
        correct = request.form.get("correct_option", "1")
        for index, text in enumerate([x.strip() for x in options if x.strip()], 1):
            db.session.add(QuizOption(question_id=question.id, option_text=text, is_correct=str(index) == correct, order_index=index))
        db.session.commit()
        flash("Вопрос добавлен.", "success")
        return redirect(url_for("teacher.quiz_questions", quiz_id=quiz.id))
    return render_template("teacher/quiz_form.html", quiz=quiz, breadcrumbs=[("Главная", "public.index"), (quiz.title, None)])


@bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def quiz_question_edit(question_id):
    question = QuizQuestion.query.get_or_404(question_id)
    quiz = question.quiz
    _own_course(quiz.course_id or quiz.lesson.module.course_id)
    if request.method == "POST":
        question.question_type = request.form.get("question_type", "single_choice")
        question.question_text = request.form.get("question_text", "").strip() or "Вопрос"
        question.correct_text_answer = request.form.get("correct_text_answer", "").strip() or None
        question.explanation = request.form.get("explanation", "").strip() or None
        question.points = max(1, int(request.form.get("points", 1)))
        option_texts = [value.strip() for value in request.form.get("options", "").splitlines() if value.strip()]
        correct_numbers = {
            value.strip() for value in request.form.get("correct_options", "1").split(",") if value.strip()
        }
        question.options.clear()
        for index, option_text in enumerate(option_texts, 1):
            question.options.append(QuizOption(option_text=option_text, is_correct=str(index) in correct_numbers, order_index=index))
        log_action("quiz_question.update", "quiz_question", question.id)
        db.session.commit()
        flash("Вопрос обновлен.", "success")
        return redirect(url_for("teacher.quiz_questions", quiz_id=quiz.id))
    return render_template("teacher/question_form.html", question=question, breadcrumbs=[("Главная", "public.index"), (quiz.title, None), ("Редактирование вопроса", None)])


@bp.route("/courses/<int:course_id>/students")
@roles_required("teacher", "admin")
def students(course_id):
    course = _own_course(course_id)
    return render_template("teacher/students.html", course=course, breadcrumbs=[("Главная", "public.index"), (course.title, None), ("Студенты", None)])


@bp.route("/courses/<int:course_id>/submissions")
@roles_required("teacher", "admin")
def submissions(course_id):
    course = _own_course(course_id)
    lesson_ids = [lesson.id for module in course.modules for lesson in module.lessons]
    task_ids = [task.id for lesson in [lesson for module in course.modules for lesson in module.lessons] for task in lesson.tasks]
    items = Submission.query.filter(Submission.task_id.in_(task_ids)).order_by(Submission.submitted_at.desc()).all() if task_ids else []
    return render_template("teacher/submissions.html", course=course, submissions=items, breadcrumbs=[("Главная", "public.index"), (course.title, None), ("Решения", None)])


@bp.route("/submissions/<int:submission_id>/review", methods=["GET", "POST"])
@roles_required("teacher", "admin")
def submission_review(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    course = _own_course(submission.task.lesson.module.course_id)
    if request.method == "POST":
        submission.teacher_comment = request.form.get("teacher_comment", "").strip() or None
        submission.reviewed_by = current_user.id
        submission.reviewed_at = utcnow()
        notify(
            submission.user_id,
            "Преподаватель проверил решение",
            f"Получен комментарий к заданию «{submission.task.title}».",
            "submission_review",
            url_for("student.submissions"),
        )
        log_action("submission.review", "submission", submission.id)
        db.session.commit()
        flash("Комментарий сохранен.", "success")
        return redirect(url_for("teacher.submissions", course_id=course.id))
    return render_template(
        "teacher/submission_review.html",
        submission=submission,
        course=course,
        breadcrumbs=[("Главная", "public.index"), (course.title, None), ("Проверка решения", None)],
    )


@bp.route("/courses/<int:course_id>/export")
@roles_required("teacher", "admin")
def export_course(course_id):
    course = _own_course(course_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Успеваемость"
    ws.append(["Студент", "Email", "Прогресс", "Статус"])
    for enrollment in course.enrollments:
        ws.append([enrollment.user.full_name, enrollment.user.email, float(enrollment.progress_percent), enrollment.status])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return send_file(stream, download_name=f"course_{course.id}_progress.xlsx", as_attachment=True)
