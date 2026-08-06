from app.models import Achievement, Course, ProgrammingTask, Quiz, QuizQuestion, TaskTestCase


def test_seed_demo_creates_complete_training_program(runner, app):
    result = runner.invoke(args=["seed-demo"])
    assert result.exit_code == 0
    with app.app_context():
        course = Course.query.filter_by(slug="osnovy-python").one()
        lessons = [lesson for module in course.modules for lesson in module.lessons]
        task_ids = [task.id for lesson in lessons for task in lesson.tasks]
        quizzes = Quiz.query.filter_by(course_id=course.id).all()
        assert len(course.modules) == 8
        assert len(lessons) == 24
        assert len(task_ids) == 25
        assert TaskTestCase.query.filter(TaskTestCase.task_id.in_(task_ids)).count() == 75
        assert len(quizzes) == 8
        assert QuizQuestion.query.filter(QuizQuestion.quiz_id.in_([quiz.id for quiz in quizzes])).count() == 40
        assert Achievement.query.count() >= 8
