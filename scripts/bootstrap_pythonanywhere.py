import os
import shutil
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTER_DATABASE = PROJECT_ROOT / "data" / "pythonstudy.db"


def main():
    load_dotenv(PROJECT_ROOT / ".env")
    data_root = Path(os.getenv("DATA_ROOT", PROJECT_ROOT / "data")).expanduser().resolve()
    target_database = data_root / "pythonstudy.db"
    for directory in (data_root, data_root / "uploads", data_root / "generated", data_root / "temp"):
        directory.mkdir(parents=True, exist_ok=True)

    if not STARTER_DATABASE.exists():
        raise SystemExit(f"Стартовая база не найдена: {STARTER_DATABASE}")
    if target_database.resolve() != STARTER_DATABASE.resolve():
        if target_database.exists():
            print(f"Рабочая база уже существует, оставлена без изменений: {target_database}")
        else:
            shutil.copy2(STARTER_DATABASE, target_database)
            print(f"Стартовая база скопирована: {target_database}")
    else:
        print(f"Используется база из репозитория: {target_database}")

    print("Каталоги PythonAnywhere подготовлены.")


if __name__ == "__main__":
    main()
