#!/usr/bin/env python3
"""Read optional Codex thread credit estimates; see ttgl.subscription."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ttgl.subscription import main

if __name__ == "__main__":
    raise SystemExit(main())
