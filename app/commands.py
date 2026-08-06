import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .services.helpers import utcnow
from .models import (
    Achievement,
    Course,
    CourseEnrollment,
    CourseModule,
    Lesson,
    ProgrammingTask,
    Quiz,
    QuizOption,
    QuizQuestion,
    Role,
    TaskTestCase,
    User,
)


def register_commands(app):
    app.cli.add_command(init_db)
    app.cli.add_command(seed_demo)


@click.command("init-db")
@with_appcontext
def init_db():
    db.create_all()
    click.echo("Структура базы данных создана.")


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    db.create_all()
    roles = {}
    for code, name in (("student", "Студент"), ("teacher", "Преподаватель"), ("admin", "Администратор")):
        role = Role.query.filter_by(code=code).first() or Role(code=code, name=name)
        db.session.add(role)
        roles[code] = role
    db.session.flush()

    accounts = [
        ("admin@pythonstudy.local", "Администратор", "Системы", "Admin123!", roles["admin"]),
        ("teacher@pythonstudy.local", "Анна", "Преподаватель", "Teacher123!", roles["teacher"]),
        ("student@pythonstudy.local", "Иван", "Студент", "Student123!", roles["student"]),
    ]
    users = {}
    for email, first_name, last_name, password, role in accounts:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, first_name=first_name, last_name=last_name, role=role)
            user.set_password(password)
            db.session.add(user)
        users[email] = user
    db.session.flush()

    course = Course.query.filter_by(slug="osnovy-python").first()
    if not course:
        course = Course(
            teacher_id=users["teacher@pythonstudy.local"].id,
            title="Основы программирования на Python",
            slug="osnovy-python",
            short_description="Интерактивный курс от переменных до функций и коллекций.",
            full_description="Курс объединяет теоретические уроки, программные задания и тесты знаний.",
            difficulty="beginner",
            status="published",
            estimated_hours=24,
            passing_score=70,
            is_sequential=True,
            published_at=utcnow(),
        )
        db.session.add(course)
        db.session.flush()

        module_titles = [
            "Введение и базовый синтаксис",
            "Условия и циклы",
            "Функции и коллекции",
            "Строки и работа с текстом",
            "Файлы и обработка ошибок",
            "Модули и стандартная библиотека",
            "Объектно-ориентированное программирование",
            "Итоговый учебный проект",
        ]
        lesson_counter = 0
        for module_index, module_title in enumerate(module_titles, 1):
            module = CourseModule(course_id=course.id, title=module_title, order_index=module_index)
            db.session.add(module)
            db.session.flush()
            for lesson_index in range(1, 4):
                lesson_counter += 1
                lesson = Lesson(
                    module_id=module.id,
                    title=f"Урок {lesson_counter}. Практика Python",
                    slug=f"urok-{lesson_counter}",
                    summary="Теория, пример и интерактивное задание.",
                    content=(
                        "<h2>Цель урока</h2><p>Освоить базовую конструкцию языка Python и применить ее на практике.</p>"
                        "<pre><code>message = 'Привет, Python!'\nprint(message)</code></pre>"
                        "<p>Измените пример и выполните связанное задание.</p>"
                    ),
                    lesson_type="mixed",
                    order_index=lesson_index,
                    estimated_minutes=35,
                    is_required=True,
                    is_published=True,
                )
                db.session.add(lesson)
                db.session.flush()
                task = ProgrammingTask(
                    lesson_id=lesson.id,
                    created_by=users["teacher@pythonstudy.local"].id,
                    title=f"Задание к уроку {lesson_counter}",
                    slug=f"zadanie-{lesson_counter}",
                    description="Считайте строку и выведите ее в верхнем регистре.",
                    input_description="Одна строка.",
                    output_description="Строка в верхнем регистре.",
                    examples="Ввод: python; вывод: PYTHON",
                    starter_code="text = input()\n# напишите решение\n",
                    reference_solution="text = input()\nprint(text.upper())",
                    difficulty="beginner",
                    points=10,
                    time_limit_seconds=2,
                    memory_limit_mb=256,
                    status="published",
                    order_index=1,
                    is_required=True,
                )
                db.session.add(task)
                db.session.flush()
                for idx, value in enumerate(("python", "Flask", "университет"), 1):
                    db.session.add(TaskTestCase(
                        task_id=task.id,
                        name=f"Тест {idx}",
                        input_data=value + "\n",
                        expected_output=value.upper(),
                        is_hidden=idx > 1,
                        weight=1,
                        order_index=idx,
                    ))

                if lesson_counter == 1:
                    bonus_task = ProgrammingTask(
                        lesson_id=lesson.id,
                        created_by=users["teacher@pythonstudy.local"].id,
                        title="Приветствие пользователя",
                        slug="privetstvie-polzovatelya",
                        description="Считайте имя и выведите персональное приветствие.",
                        input_description="Имя пользователя.",
                        output_description="Строка Привет, имя!",
                        examples="Ввод: Анна; вывод: Привет, Анна!",
                        starter_code="name = input()\n",
                        reference_solution="name = input()\nprint(f'Привет, {name}!')",
                        difficulty="beginner",
                        points=10,
                        time_limit_seconds=2,
                        memory_limit_mb=256,
                        status="published",
                        order_index=2,
                        is_required=False,
                    )
                    db.session.add(bonus_task)
                    db.session.flush()
                    for idx, name in enumerate(("Анна", "Иван", "Python"), 1):
                        db.session.add(TaskTestCase(
                            task_id=bonus_task.id,
                            name=f"Приветствие {idx}",
                            input_data=name + "\n",
                            expected_output=f"Привет, {name}!",
                            is_hidden=idx > 1,
                            weight=1,
                            order_index=idx,
                        ))

        question_sets = [
            ("Какой тип хранит целые числа?", ["str", "int", "list"], 1),
            ("Какой оператор сравнивает значения?", ["=", "==", ":="], 1),
            ("Какая функция выводит данные?", ["input", "print", "len"], 1),
            ("Как начинается определение функции?", ["func", "def", "lambda:"], 1),
            ("Какая коллекция изменяема?", ["tuple", "str", "list"], 2),
        ]
        for quiz_index, module_title in enumerate(module_titles, 1):
            quiz = Quiz(
                course_id=course.id,
                created_by=users["teacher@pythonstudy.local"].id,
                title=f"Тест {quiz_index}. {module_title}",
                description="Проверка понятий раздела и подготовка к следующему модулю.",
                time_limit_minutes=15,
                passing_score=70,
                max_attempts=3,
                randomize_questions=True,
                randomize_options=True,
                show_correct_answers=True,
                status="published",
                is_required=quiz_index in {3, 8},
            )
            db.session.add(quiz)
            db.session.flush()
            for q_index, (text, options, correct_idx) in enumerate(question_sets, 1):
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_type="single_choice",
                    question_text=f"Раздел {quiz_index}. {text}",
                    explanation="Верный вариант соответствует синтаксису и типам Python.",
                    points=1,
                    order_index=q_index,
                )
                db.session.add(question)
                db.session.flush()
                for o_index, option_text in enumerate(options, 1):
                    db.session.add(QuizOption(
                        question_id=question.id,
                        option_text=option_text,
                        is_correct=o_index - 1 == correct_idx,
                        order_index=o_index,
                    ))

    enrollment = CourseEnrollment.query.filter_by(
        course_id=course.id,
        user_id=users["student@pythonstudy.local"].id,
    ).first()
    if not enrollment:
        db.session.add(CourseEnrollment(course_id=course.id, user_id=users["student@pythonstudy.local"].id))

    achievements = [
        ("first_lesson", "Первый урок", "Завершен первый урок", "completed_lessons", 1),
        ("first_task", "Первое решение", "Решено первое программное задание", "completed_tasks", 1),
        ("five_tasks", "Пять решений", "Решено пять заданий", "completed_tasks", 5),
        ("perfect_quiz", "Тест без ошибок", "Тест пройден на 100 процентов", "perfect_quizzes", 1),
        ("ten_lessons", "Уверенный старт", "Завершено десять уроков", "completed_lessons", 10),
        ("all_lessons", "Теоретик Python", "Завершены двадцать четыре урока", "completed_lessons", 24),
        ("ten_tasks", "Практик Python", "Решено десять заданий", "completed_tasks", 10),
        ("all_tasks", "Мастер практики", "Решено двадцать пять заданий", "completed_tasks", 25),
    ]
    for code, name, description, condition_type, condition_value in achievements:
        if not Achievement.query.filter_by(code=code).first():
            db.session.add(Achievement(
                code=code,
                name=name,
                description=description,
                condition_type=condition_type,
                condition_value=condition_value,
                points=10,
            ))

    db.session.commit()
    click.echo("Демонстрационные данные созданы.")
