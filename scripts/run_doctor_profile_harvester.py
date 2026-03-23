#!/usr/bin/env python3
"""Repo-level entrypoint for doctor profile harvesting."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "doctor-profile-harvester" / "doctor_profile_harvester.py"

if __name__ == "__main__":
    os.chdir(ROOT)
    sys.path.insert(0, str(SCRIPT.parent))
    runpy.run_path(str(SCRIPT), run_name="__main__")
