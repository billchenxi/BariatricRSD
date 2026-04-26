#!/usr/bin/env python3
"""
Compatibility entrypoint for the strict-protocol patch helper.

The authoritative implementation lives at repo-root:
  `scripts/11_apply_protocol_patches.py`

This wrapper keeps older references under `lambda_setup/scripts/` working while
ensuring there is only one patch implementation to maintain.
"""
from __future__ import annotations

import runpy
from pathlib import Path


ROOT_HELPER = Path(__file__).resolve().parents[2] / "scripts" / "11_apply_protocol_patches.py"

if not ROOT_HELPER.exists():
    raise FileNotFoundError(f"Expected helper at {ROOT_HELPER}")

runpy.run_path(str(ROOT_HELPER), run_name="__main__")
