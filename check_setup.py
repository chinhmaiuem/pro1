"""Validate installed dependencies and the demo dataset without starting the UI."""
import importlib
import sys

from utils.data_loader import ROOT, load_data


def main():
    if sys.version_info < (3, 12):
        print("Use Python 3.12 or 3.13.")
        return 1
    for package in ("numpy", "pandas", "plotly", "streamlit"):
        try:
            module = importlib.import_module(package)
            print(f"{package}: {module.__version__}")
        except ImportError:
            print(f"Missing {package}. Run: python -m pip install -r requirements.txt")
            return 1
    try:
        bundle = load_data(ROOT / "data" / "demo")
    except (ValueError, OSError) as exc:
        print(f"Demo validation failed: {exc}")
        return 1
    print(f"Demo ready: {len(bundle.transactions):,} transactions, {len(bundle.users):,} customers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

