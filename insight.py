"""Compatibility entry point: python insight.py rebuild --help."""

from analysis.insight import main

if __name__ == "__main__":
    raise SystemExit(main())
