"""DNS, ICMP ping and TCP connectivity diagnostics."""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
from dataclasses import dataclass


_HOST_CHARS = re.compile(r"^[A-Za-z0-9._:%-]+$")


class InputValidationError(ValueError):
    """Raised when a host name or port is not valid for a diagnostic test."""


@dataclass(frozen=True)
class TcpTestResult:
    host: str
    port: int
    remote_ip: str | None
    success: bool
    message: str


def validate_host(host: str) -> str:
    """Validate a hostname/IP before using it in a diagnostic operation."""
    value = host.strip()
    if not value or len(value) > 253 or value.startswith("-"):
        raise InputValidationError("Enter a valid hostname or IP address.")
    if not _HOST_CHARS.fullmatch(value):
        raise InputValidationError(
            "Host may contain only letters, numbers, dots, colons, percent signs and hyphens."
        )
    return value


def validate_port(port: int | str) -> int:
    """Convert and validate a TCP port number."""
    try:
        value = int(port)
    except (TypeError, ValueError) as exc:
        raise InputValidationError("Port must be a whole number from 1 to 65535.") from exc
    if not 1 <= value <= 65535:
        raise InputValidationError("Port must be between 1 and 65535.")
    return value


def resolve_host(host: str) -> list[str]:
    """Resolve a hostname and return unique IPv4/IPv6 addresses."""
    host = validate_host(host)
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError(f"DNS/name resolution failed: {exc}") from exc

    addresses: list[str] = []
    for record in records:
        address = record[4][0]
        if address not in addresses:
            addresses.append(address)
    return addresses


def ping_host(host: str, count: int = 4) -> tuple[bool, str]:
    """Run the Windows ping utility against one supplied host."""
    host = validate_host(host)
    if not 1 <= count <= 10:
        raise InputValidationError("Ping count must be between 1 and 10.")
    ping_executable = shutil.which("ping.exe") or shutil.which("ping")
    if not ping_executable:
        raise RuntimeError("The Windows ping utility could not be found.")

    try:
        result = subprocess.run(
            [ping_executable, "-n", str(count), "-w", "1000", host],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=count + 8,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Ping test timed out.") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not start ping: {exc}") from exc

    output = (result.stdout or result.stderr).strip()
    return result.returncode == 0, output or "No output was returned by ping."


def test_tcp_connection(host: str, port: int | str, timeout: float = 4.0) -> TcpTestResult:
    """Attempt a TCP connection to one host and port, with a short timeout."""
    host = validate_host(host)
    port_number = validate_port(port)
    try:
        with socket.create_connection((host, port_number), timeout=timeout) as connection:
            remote_ip = connection.getpeername()[0]
        return TcpTestResult(
            host=host,
            port=port_number,
            remote_ip=remote_ip,
            success=True,
            message="TCP connection succeeded.",
        )
    except OSError as exc:
        return TcpTestResult(
            host=host,
            port=port_number,
            remote_ip=None,
            success=False,
            message=f"TCP connection failed: {exc}",
        )
