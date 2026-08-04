import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from flask import current_app

from .code_validator import ValidationError, validate_code


@dataclass
class RunResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    return_code: int | None = None

    def to_dict(self):
        return asdict(self)


def _limit_resources(memory_mb, timeout_seconds):
    try:
        import resource
        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (max(1, int(timeout_seconds)), max(1, int(timeout_seconds) + 1)))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
    except (ImportError, ValueError, OSError):
        pass


def run_python_code(code, input_data="", timeout=None, memory_mb=None, allowed_imports=None):
    timeout = float(timeout or current_app.config["CODE_TIMEOUT_SECONDS"])
    memory_mb = int(memory_mb or current_app.config["CODE_MEMORY_MB"])
    output_limit = int(current_app.config["CODE_OUTPUT_LIMIT"])
    try:
        validate_code(code, allowed_imports=allowed_imports)
    except ValidationError as exc:
        return RunResult(status="security_error", stderr=str(exc))

    temp_root = Path(current_app.config["TEMP_ROOT"])
    temp_root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="pythonstudy_", dir=temp_root) as tmp:
        script_path = Path(tmp) / "main.py"
        script_path.write_text(code, encoding="utf-8")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
        kwargs = {}
        if os.name == "posix":
            kwargs["preexec_fn"] = lambda: _limit_resources(memory_mb, timeout)
        try:
            process = subprocess.run(
                [sys.executable, "-I", str(script_path)],
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=tmp,
                env=env,
                **kwargs,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = int((time.perf_counter() - started) * 1000)
            return RunResult(
                status="time_limit_exceeded",
                stdout=(exc.stdout or "")[:output_limit] if isinstance(exc.stdout, str) else "",
                stderr="Превышено допустимое время выполнения.",
                execution_time_ms=elapsed,
            )
        except Exception as exc:
            return RunResult(status="internal_error", stderr=f"Ошибка запуска: {exc}")

    elapsed = int((time.perf_counter() - started) * 1000)
    stdout = process.stdout[:output_limit]
    stderr = process.stderr[:output_limit]
    if len(process.stdout) > output_limit or len(process.stderr) > output_limit:
        stderr += "\nВывод программы был сокращен."
    status = "accepted" if process.returncode == 0 else "runtime_error"
    return RunResult(status=status, stdout=stdout, stderr=stderr, execution_time_ms=elapsed, return_code=process.returncode)


def normalize_output(value):
    return "\n".join(line.rstrip() for line in (value or "").strip().splitlines())
