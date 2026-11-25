"""Small helpers for safely running built-in Windows PowerShell commands."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


class WindowsCommandError(RuntimeError):
    """Raised when a required Windows command cannot be executed."""


def is_windows() -> bool:
    """Return True when the application is running on Windows."""
    import os

    return os.name == "nt"


def run_powershell_json(script: str, timeout: int = 15) -> list[dict[str, Any]]:
    """Run a fixed, application-authored PowerShell script and parse JSON output.

    User input must never be interpolated into PowerShell scripts. The project
    uses this helper only with constant scripts defined in its own source.
    """
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if not executable:
        raise WindowsCommandError(
            "Windows PowerShell was not found. Run this project on Windows."
        )

    try:
        result = subprocess.run(
            [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise WindowsCommandError("PowerShell command timed out.") from exc
    except OSError as exc:
        raise WindowsCommandError(f"Could not start PowerShell: {exc}") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise WindowsCommandError(detail or "PowerShell command failed.")

    output = result.stdout.strip()
    if not output:
        return []

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        raise WindowsCommandError(
            "PowerShell returned data that was not valid JSON. "
            "Try running the command again in a normal PowerShell window."
        ) from exc

    if parsed is None:
        return []
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []
