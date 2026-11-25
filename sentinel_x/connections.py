"""Inspect local TCP connections and UDP endpoints on Windows."""

from __future__ import annotations

from typing import Any

from .windows import WindowsCommandError, is_windows, run_powershell_json


# Windows TCP state values are included as a fallback for older PowerShell
# serialization paths. The scripts below also return a readable StateName.
_TCP_STATE_NAMES = {
    1: "Closed",
    2: "Listening",
    3: "SYN Sent",
    4: "SYN Received",
    5: "Established",
    6: "FIN Wait 1",
    7: "FIN Wait 2",
    8: "Close Wait",
    9: "Closing",
    10: "Last ACK",
    11: "Time Wait",
    12: "Delete TCB",
    100: "Bound",
}


def tcp_state_label(state: Any) -> str:
    """Convert Windows TCP state names or numeric enum values to readable labels."""
    if state is None or state == "":
        return "Unknown"
    if isinstance(state, int) or (isinstance(state, str) and state.strip().isdigit()):
        return _TCP_STATE_NAMES.get(int(state), f"Unknown ({state})")

    normalized = str(state).strip().replace("_", " ").replace("-", " ").lower()
    aliases = {
        "listen": "Listening",
        "listening": "Listening",
        "synsent": "SYN Sent",
        "syn sent": "SYN Sent",
        "synreceived": "SYN Received",
        "syn received": "SYN Received",
        "finwait1": "FIN Wait 1",
        "fin wait 1": "FIN Wait 1",
        "finwait2": "FIN Wait 2",
        "fin wait 2": "FIN Wait 2",
        "closewait": "Close Wait",
        "close wait": "Close Wait",
        "lastack": "Last ACK",
        "last ack": "Last ACK",
        "timewait": "Time Wait",
        "time wait": "Time Wait",
        "deletetcb": "Delete TCB",
        "delete tcb": "Delete TCB",
    }
    return aliases.get(normalized, str(state).strip().title())


_PROCESS_AND_SERVICE_MAPS = r"""
$processById = @{}
Get-CimInstance -ClassName Win32_Process | ForEach-Object {
    $processById[[int]$_.ProcessId] = $_
}

$servicesByPid = @{}
Get-CimInstance -ClassName Win32_Service | ForEach-Object {
    $ownerId = [int]$_.ProcessId
    if ($ownerId -gt 0) {
        if (-not $servicesByPid.ContainsKey($ownerId)) {
            $servicesByPid[$ownerId] = @()
        }
        $servicesByPid[$ownerId] = @($servicesByPid[$ownerId]) + [string]$_.Name
    }
}
"""


_TCP_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
""" + _PROCESS_AND_SERVICE_MAPS + r"""
$stateCodes = @{
    'Closed' = 1; 'Listen' = 2; 'Listening' = 2; 'SynSent' = 3;
    'SynReceived' = 4; 'Established' = 5; 'FinWait1' = 6;
    'FinWait2' = 7; 'CloseWait' = 8; 'Closing' = 9;
    'LastAck' = 10; 'TimeWait' = 11; 'DeleteTcb' = 12; 'Bound' = 100
}

# Prioritize established and listening sockets so the 100-row view is useful.
$orderedEntries = Get-NetTCPConnection | Sort-Object `
    @{ Expression = {
        switch ([string]$_.State) {
            'Established' { 0 }
            'Listen'      { 1 }
            'Listening'   { 1 }
            'Bound'       { 2 }
            default       { 3 }
        }
    } }, LocalPort | Select-Object -First 100

$items = foreach ($entry in $orderedEntries) {
    $ownerId = [int]$entry.OwningProcess
    $proc = $processById[$ownerId]
    $processName = $null
    $executablePath = $null
    if ($null -ne $proc) {
        $processName = [string]$proc.Name
        $executablePath = [string]$proc.ExecutablePath
    }
    $serviceNames = @()
    if ($servicesByPid.ContainsKey($ownerId)) {
        $serviceNames = @($servicesByPid[$ownerId])
    }

    # State can arrive as a numeric value or a friendly enum name.
    # Do not cast text such as 'Bound' directly to [int].
    $stateName = [string]$entry.State
    $stateCode = $null
    $parsedStateCode = 0
    if ([int]::TryParse($stateName, [ref]$parsedStateCode)) {
        $stateCode = $parsedStateCode
    } elseif ($stateCodes.ContainsKey($stateName)) {
        $stateCode = $stateCodes[$stateName]
    }

    [PSCustomObject]@{
        LocalAddress = [string]$entry.LocalAddress
        LocalPort = [int]$entry.LocalPort
        RemoteAddress = [string]$entry.RemoteAddress
        RemotePort = [int]$entry.RemotePort
        StateName = $stateName
        StateCode = $stateCode
        OwningProcess = $ownerId
        ProcessName = $processName
        ExecutablePath = $executablePath
        ServiceNames = $serviceNames
    }
}
ConvertTo-Json -InputObject @($items) -Depth 5 -Compress
"""


_UDP_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
""" + _PROCESS_AND_SERVICE_MAPS + r"""
$items = foreach ($entry in (Get-NetUDPEndpoint | Select-Object -First 100)) {
    $ownerId = [int]$entry.OwningProcess
    $proc = $processById[$ownerId]
    $processName = $null
    $executablePath = $null
    if ($null -ne $proc) {
        $processName = [string]$proc.Name
        $executablePath = [string]$proc.ExecutablePath
    }
    $serviceNames = @()
    if ($servicesByPid.ContainsKey($ownerId)) {
        $serviceNames = @($servicesByPid[$ownerId])
    }
    [PSCustomObject]@{
        LocalAddress = [string]$entry.LocalAddress
        LocalPort = [int]$entry.LocalPort
        OwningProcess = $ownerId
        ProcessName = $processName
        ExecutablePath = $executablePath
        ServiceNames = $serviceNames
    }
}
ConvertTo-Json -InputObject @($items) -Depth 5 -Compress
"""


def get_tcp_connections() -> list[dict[str, Any]]:
    """Return up to 100 TCP entries, including readable states and process details."""
    if not is_windows():
        raise WindowsCommandError("TCP connection inspection is supported on Windows.")
    rows = run_powershell_json(_TCP_SCRIPT, timeout=25)
    for row in rows:
        state = row.get("StateName") or row.get("State") or row.get("StateCode")
        row["StateName"] = tcp_state_label(state)
        services = row.get("ServiceNames")
        row["ServiceNames"] = services if isinstance(services, list) else ([services] if services else [])
    return rows


def get_udp_endpoints() -> list[dict[str, Any]]:
    """Return up to 100 UDP endpoints with owning process and service details."""
    if not is_windows():
        raise WindowsCommandError("UDP endpoint inspection is supported on Windows.")
    rows = run_powershell_json(_UDP_SCRIPT, timeout=25)
    for row in rows:
        services = row.get("ServiceNames")
        row["ServiceNames"] = services if isinstance(services, list) else ([services] if services else [])
    return rows
