from __future__ import annotations

"""Backward-compatible entry for `npm run smoke:api`. Prefer `python -m pytest`."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    return pytest.main([str(ROOT / "tests"), "-q"])


if __name__ == "__main__":
    sys.exit(main())
