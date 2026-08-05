from app.services.code_runner import normalize_output, run_python_code


def test_normalize_output():
    assert normalize_output("a  \n b\n") == "a\n b"


def test_run_success(app):
    with app.app_context():
        result = run_python_code("value = int(input())\nprint(value * 2)", "4\n", memory_mb=256)
        assert result.status == "accepted"
        assert result.stdout.strip() == "8"


def test_run_syntax_error(app):
    with app.app_context():
        result = run_python_code("print(", "")
        assert result.status == "security_error"


def test_run_timeout(app):
    with app.app_context():
        result = run_python_code("while True:\n    pass", "", timeout=0.2, memory_mb=256)
        assert result.status == "time_limit_exceeded"


def test_output_is_limited_without_buffering_in_memory(app):
    with app.app_context():
        app.config["CODE_OUTPUT_LIMIT"] = 100
        result = run_python_code("print('x' * 5000)", memory_mb=256)
        assert len(result.stdout) <= 100
        assert "Вывод программы был сокращен" in result.stderr
