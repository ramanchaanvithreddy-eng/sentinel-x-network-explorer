"""Network configuration and ARP-table inspection."""

from __future__ import annotations

import ipaddress
import re
import subprocess
from typing import Any

from .windows import WindowsCommandError, is_windows, run_powershell_json


_NETWORK_CONFIG_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$configs = Get-NetIPConfiguration | Where-Object { $_.NetAdapter.Status -eq 'Up' }
$items = foreach ($config in $configs) {
    [PSCustomObject]@{
        InterfaceAlias = [string]$config.InterfaceAlias
        Description = [string]$config.NetAdapter.InterfaceDescription
        IPv4Addresses = @($config.IPv4Address | ForEach-Object { [string]$_.IPAddress })
        PrefixLengths = @($config.IPv4Address | ForEach-Object { [int]$_.PrefixLength })
        IPv4Gateways = @($config.IPv4DefaultGateway | ForEach-Object { [string]$_.NextHop })
        IPv6Gateways = @($config.IPv6DefaultGateway | ForEach-Object { [string]$_.NextHop })
        DnsServers = @($config.DNSServer.ServerAddresses | ForEach-Object { [string]$_ })
    }
}
ConvertTo-Json -InputObject @($items) -Depth 5 -Compress
"""


_ARP_LINE = re.compile(
    r"^\s*(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"(?P<mac>(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})\s+"
    r"(?P<type>dynamic|static)\s*$",
    re.IGNORECASE,
)


def summarize_ipv4(ip_address: str, prefix_length: int) -> dict[str, str | int]:
    """Return subnet facts for an IPv4 address and prefix length."""
    interface = ipaddress.ip_interface(f"{ip_address}/{prefix_length}")
    network = interface.network

    if network.prefixlen <= 30:
        first_host = str(network.network_address + 1)
        last_host = str(network.broadcast_address - 1)
    else:
        hosts = list(network.hosts())
        first_host = str(hosts[0]) if hosts else "N/A"
        last_host = str(hosts[-1]) if hosts else "N/A"

    return {
        "ip_address": str(interface.ip),
        "prefix_length": network.prefixlen,
        "subnet_mask": str(network.netmask),
        "network_address": str(network.network_address),
        "broadcast_address": str(network.broadcast_address),
        "first_usable": first_host,
        "last_usable": last_host,
        "total_addresses": network.num_addresses,
    }


def get_network_configurations() -> list[dict[str, Any]]:
    """Get active interface details using Windows' built-in NetTCPIP module."""
    if not is_windows():
        raise WindowsCommandError(
            "The Network Inspector uses Windows PowerShell. Run it on Windows."
        )
    return run_powershell_json(_NETWORK_CONFIG_SCRIPT)


def get_arp_table() -> list[dict[str, str]]:
    """Read and parse the local Windows ARP table."""
    if not is_windows():
        raise WindowsCommandError("The ARP Viewer is supported on Windows.")
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WindowsCommandError(f"Could not run arp -a: {exc}") from exc

    if result.returncode != 0:
        raise WindowsCommandError(result.stderr.strip() or "arp -a failed.")

    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        match = _ARP_LINE.match(line)
        if match:
            entries.append(match.groupdict())
    return entries
