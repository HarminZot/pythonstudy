import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
os.environ.setdefault("APP_CONFIG", "production")

from app import create_app  # noqa: E402

application = create_app()
app = application
