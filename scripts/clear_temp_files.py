import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "storage" / "temp"


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for item in ROOT.iterdir():
        if item.name == ".gitkeep":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)
    print("Временные файлы удалены.")


if __name__ == "__main__":
    main()
