import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pythonstudy.db"
BACKUP_DIR = ROOT / "storage" / "generated" / "backups"


def main():
    if not SOURCE.exists():
        raise SystemExit("Локальная SQLite-база не найдена. Для PostgreSQL используйте pg_dump.")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"pythonstudy_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(SOURCE, target)
    print(target)


if __name__ == "__main__":
    main()
