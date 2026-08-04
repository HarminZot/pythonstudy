from decimal import Decimal

from ..extensions import db
from ..models import SubmissionTestResult
from .achievement_service import evaluate_achievements
from .code_runner import normalize_output, run_python_code
from .helpers import utcnow
from .notification_service import notify
from .progress_service import calculate_course_progress


def grade_submission(submission):
    task = submission.task
    cases = task.test_cases
    submission.status = "running"
    submission.total_tests = len(cases)
    db.session.flush()

    passed_weight = 0
    passed_count = 0
    total_weight = sum(max(1, case.weight) for case in cases) or 1
    max_time = 0
    first_stdout = ""
    first_stderr = ""
    statuses = []

    for case in cases:
        result = run_python_code(
            submission.code,
            input_data=case.input_data or "",
            timeout=float(case.timeout_seconds or task.time_limit_seconds),
            memory_mb=task.memory_limit_mb,
            allowed_imports=task.allowed_imports or [],
        )
        actual = normalize_output(result.stdout)
        expected = normalize_output(case.expected_output)
        passed = result.status == "accepted" and actual == expected
        status = "accepted" if passed else ("wrong_answer" if result.status == "accepted" else result.status)
        statuses.append(status)
        test_result = SubmissionTestResult(
            submission=submission,
            test_case=case,
            status=status,
            actual_output=result.stdout,
            error_message=result.stderr,
            execution_time_ms=result.execution_time_ms,
            is_passed=passed,
        )
        db.session.add(test_result)
        if passed:
            passed_weight += max(1, case.weight)
            passed_count += 1
        max_time = max(max_time, result.execution_time_ms)
        if not first_stdout:
            first_stdout = result.stdout
        if not first_stderr and result.stderr:
            first_stderr = result.stderr

    submission.passed_tests = passed_count
    submission.score = Decimal(str(passed_weight * 100 / total_weight)).quantize(Decimal("0.01"))
    submission.execution_time_ms = max_time
    submission.stdout = first_stdout
    submission.stderr = first_stderr
    submission.checked_at = utcnow()
    if not cases:
        submission.status = "internal_error"
        submission.stderr = "Для задания не настроены тестовые случаи."
    elif passed_count == len(cases):
        submission.status = "accepted"
    elif passed_count > 0:
        submission.status = "partially_accepted"
    else:
        submission.status = statuses[0] if statuses and len(set(statuses)) == 1 else "wrong_answer"

    db.session.flush()
    course_id = task.lesson.module.course_id
    calculate_course_progress(submission.user_id, course_id)
    evaluate_achievements(submission.user_id)
    notify(
        submission.user_id,
        "Решение проверено",
        f"Задание «{task.title}»: {submission.score}%.",
        "task_result",
        f"/student/submissions/{submission.id}",
    )
    return submission
