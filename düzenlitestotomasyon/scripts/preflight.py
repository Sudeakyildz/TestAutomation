"""CLI preflight - validate staging environment before tests."""
import os
import sys


def configure_stdio():
    """Windows CI consoles may use cp1252; force UTF-8 with replacement."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_text(value):
    text = str(value)
    try:
        text.encode("cp1252")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "backslashreplace").decode("ascii")


def safe_print(value):
    configure_stdio()
    print(safe_text(value))


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

from tests.preflight import run_preflight


def main():
    configure_stdio()
    errors = run_preflight()
    if errors:
        safe_print("PREFLIGHT FAILED:")
        for err in errors:
            safe_print(f"  - {err}")
        sys.exit(1)
    safe_print("PREFLIGHT OK - staging environment is ready.")


if __name__ == "__main__":
    main()
