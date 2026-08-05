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


def _limit_resources(memory_mb, timeout_seconds, output_limit):
    try:
        import resource
        memory_bytes = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (max(1, int(timeout_seconds)), max(1, int(timeout_seconds) + 1)))
        file_limit = max(1024, output_limit)
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
    except (ImportError, ValueError, OSError):
        pass


def _read_limited(path, limit):
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    return content[:limit].decode("utf-8", errors="replace"), len(content) > limit


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
        stdout_path = Path(tmp) / "stdout.txt"
        stderr_path = Path(tmp) / "stderr.txt"
        script_path.write_text(code, encoding="utf-8")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
        kwargs = {}
        if os.name == "posix":
            kwargs["preexec_fn"] = lambda: _limit_resources(memory_mb, timeout, output_limit)
        try:
            with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
                process = subprocess.Popen(
                    [sys.executable, "-I", str(script_path)],
                    stdin=subprocess.PIPE,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    text=True,
                    cwd=tmp,
                    env=env,
                    **kwargs,
                )
                try:
                    process.communicate(input=input_data, timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    elapsed = int((time.perf_counter() - started) * 1000)
                    stdout, _truncated = _read_limited(stdout_path, output_limit)
                    return RunResult(
                        status="time_limit_exceeded",
                        stdout=stdout,
                        stderr="Превышено допустимое время выполнения.",
                        execution_time_ms=elapsed,
                    )
        except Exception as exc:
            return RunResult(status="internal_error", stderr=f"Ошибка запуска: {exc}")

        elapsed = int((time.perf_counter() - started) * 1000)
        stdout, stdout_truncated = _read_limited(stdout_path, output_limit)
        stderr, stderr_truncated = _read_limited(stderr_path, output_limit)
        if stdout_truncated or stderr_truncated:
            stderr = f"{stderr.rstrip()}\nВывод программы был сокращен.".lstrip()
        status = "accepted" if process.returncode == 0 else "runtime_error"
        return RunResult(status=status, stdout=stdout, stderr=stderr, execution_time_ms=elapsed, return_code=process.returncode)


def normalize_output(value):
    return "\n".join(line.rstrip() for line in (value or "").strip().splitlines())
