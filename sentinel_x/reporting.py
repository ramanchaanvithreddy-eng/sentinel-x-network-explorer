"""Create privacy-conscious JSON and CSV snapshots for local investigations."""

from __future__ import annotations

import csv
import io
import json
import platform
import socket
from datetime import datetime, timezone
from typing import Any

from . import __version__


def build_snapshot(
    *,
    network: list[dict[str, Any]],
    arp: list[dict[str, Any]],
    tcp: list[dict[str, Any]],
    udp: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a serializable snapshot from already-collected local data."""
    return {
        "application": "SENTINEL X",
        "version": __version__,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "computer_name": socket.gethostname(),
        "platform": platform.platform(),
        "data_scope": "Local machine diagnostics; no remote range scanning performed.",
        "network_interfaces": network,
        "arp_entries": arp,
        "tcp_connections": tcp,
        "udp_endpoints": udp,
    }


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
    """Serialize a snapshot as readable JSON."""
    return json.dumps(snapshot, indent=2, sort_keys=True, default=str)


def snapshot_to_csv(snapshot: dict[str, Any]) -> str:
    """Serialize heterogeneous snapshot records into category + JSON detail columns."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["category", "record_number", "details_json"])
    for category in (
        "network_interfaces",
        "arp_entries",
        "tcp_connections",
        "udp_endpoints",
    ):
        records = snapshot.get(category, [])
        for index, record in enumerate(records, start=1):
            writer.writerow([category, index, json.dumps(record, sort_keys=True, default=str)])
    return output.getvalue()
