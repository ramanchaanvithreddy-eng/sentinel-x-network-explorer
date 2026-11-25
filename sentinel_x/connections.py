"""Inspect local TCP connections and UDP endpoints on Windows."""

from __future__ import annotations

from typing import Any

from .windows import WindowsCommandError, is_windows, run_powershell_json


_TCP_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$items = Get-NetTCPConnection | Select-Object -First 50 LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
ConvertTo-Json -InputObject @($items) -Depth 4 -Compress
"""

_UDP_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$items = Get-NetUDPEndpoint | Select-Object -First 50 LocalAddress, LocalPort, OwningProcess
ConvertTo-Json -InputObject @($items) -Depth 4 -Compress
"""


def get_tcp_connections() -> list[dict[str, Any]]:
    """Return up to 50 TCP connection entries from the local Windows host."""
    if not is_windows():
        raise WindowsCommandError("TCP connection inspection is supported on Windows.")
    return run_powershell_json(_TCP_SCRIPT)


def get_udp_endpoints() -> list[dict[str, Any]]:
    """Return up to 50 local UDP endpoints from the local Windows host."""
    if not is_windows():
        raise WindowsCommandError("UDP endpoint inspection is supported on Windows.")
    return run_powershell_json(_UDP_SCRIPT)
