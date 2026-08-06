"""Шаблон системного WSGI-файла из раздела Web на PythonAnywhere."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path.home() / "pythonstudy"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")
os.environ.setdefault("APP_CONFIG", "production")

from app import create_app  # noqa: E402


application = create_app()
