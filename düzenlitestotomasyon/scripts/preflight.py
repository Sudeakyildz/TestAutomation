"""CLI preflight — staging ortamını doğrula."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

from tests.preflight import run_preflight


def main():
    errors = run_preflight()
    if errors:
        print("PREFLIGHT FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("PREFLIGHT OK - staging environment is ready.")


if __name__ == "__main__":
    main()
