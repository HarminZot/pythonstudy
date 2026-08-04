from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".py", ".html", ".css", ".js"}


def is_logical(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "//", "<!--")):
        return False
    return True


def main():
    total = 0
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in EXTENSIONS and ".venv" not in path.parts:
            count = sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if is_logical(line))
            total += count
            print(f"{count:5d}  {path.relative_to(ROOT)}")
    print(f"\nИтого логических строк: {total}")


if __name__ == "__main__":
    main()
