"""Interactive command-line interface for SENTINEL X."""

from __future__ import annotations

import socket
import sys
from typing import Any

from . import __version__
from .connections import get_tcp_connections, get_udp_endpoints
from .diagnostics import (
    InputValidationError,
    ping_host,
    resolve_host,
    test_tcp_connection,
)
from .network import get_arp_table, get_network_configurations, summarize_ipv4
from .windows import WindowsCommandError


LINE = "-" * 72


def _as_list(value: Any) -> list[Any]:
    """Normalize PowerShell JSON values that may be scalar or arrays."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _print_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    if not rows:
        print("No entries found.")
        return
    for index, row in enumerate(rows, start=1):
        print(f"\nEntry {index}")
        for key, label in columns:
            value = row.get(key, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value) or "—"
            elif value in (None, ""):
                value = "—"
            print(f"  {label:<20}: {value}")


def show_network_inspector() -> None:
    print(f"\n{LINE}\nNETWORK INSPECTOR\n{LINE}")
    configurations = get_network_configurations()
    if not configurations:
        print("No active network interfaces were returned by Windows.")
        return

    for index, item in enumerate(configurations, start=1):
        print(f"\nInterface {index}: {item.get('InterfaceAlias', 'Unknown')}")
        print(f"  Adapter             : {item.get('Description') or '—'}")
        ipv4_addresses = _as_list(item.get("IPv4Addresses"))
        prefixes = _as_list(item.get("PrefixLengths"))
        gateways = _as_list(item.get("IPv4Gateways"))
        ipv6_gateways = _as_list(item.get("IPv6Gateways"))
        dns_servers = _as_list(item.get("DnsServers"))
        print(f"  IPv4 addresses      : {', '.join(ipv4_addresses) or '—'}")
        print(f"  IPv4 gateway        : {', '.join(gateways) or '—'}")
        print(f"  IPv6 gateway        : {', '.join(ipv6_gateways) or '—'}")
        print(f"  DNS servers         : {', '.join(dns_servers) or '—'}")

        for ip_address, prefix in zip(ipv4_addresses, prefixes):
            facts = summarize_ipv4(ip_address, int(prefix))
            print(f"\n  Subnet details for {ip_address}/{prefix}")
            print(f"    Subnet mask       : {facts['subnet_mask']}")
            print(f"    Network address   : {facts['network_address']}")
            print(f"    Broadcast address : {facts['broadcast_address']}")
            print(f"    Usable range      : {facts['first_usable']} - {facts['last_usable']}")
            print(f"    Total addresses   : {facts['total_addresses']}")


def show_dns_explorer() -> None:
    print(f"\n{LINE}\nDNS EXPLORER\n{LINE}")
    host = input("Enter a domain or hostname (e.g. google.com): ").strip()
    addresses = resolve_host(host)
    print(f"\nResolved addresses for {host}:")
    for address in addresses:
        family = "IPv6" if ":" in address else "IPv4"
        print(f"  {family:<5} {address}")


def show_ping_tester() -> None:
    print(f"\n{LINE}\nPING TESTER\n{LINE}")
    host = input("Enter a hostname or IP address: ").strip()
    success, output = ping_host(host)
    print("\n" + output)
    print(f"\nResult: {'Replies received' if success else 'No successful replies'}")
    print("Note: Some networks block ICMP Echo Replies. A failed ping alone does not prove internet access is down.")


def show_tcp_tester() -> None:
    print(f"\n{LINE}\nTCP PORT TESTER\n{LINE}")
    host = input("Enter a hostname or IP address: ").strip()
    port = input("Enter a TCP port (e.g. 443): ").strip()
    result = test_tcp_connection(host, port)
    print(f"\nDestination : {result.host}:{result.port}")
    print(f"Remote IP   : {result.remote_ip or 'Not established'}")
    print(f"Result      : {result.message}")


def show_arp_viewer() -> None:
    print(f"\n{LINE}\nLOCAL ARP TABLE\n{LINE}")
    entries = get_arp_table()
    _print_table(entries, [("ip", "IPv4 address"), ("mac", "MAC address"), ("type", "Entry type")])
    print("\nARP shows local IPv4-to-MAC mappings. It does not list every device on the internet.")


def show_tcp_monitor() -> None:
    print(f"\n{LINE}\nLOCAL TCP CONNECTIONS (first 50)\n{LINE}")
    rows = get_tcp_connections()
    _print_table(
        rows,
        [
            ("LocalAddress", "Local address"),
            ("LocalPort", "Local port"),
            ("RemoteAddress", "Remote address"),
            ("RemotePort", "Remote port"),
            ("State", "State"),
            ("OwningProcess", "Process ID"),
        ],
    )


def show_udp_viewer() -> None:
    print(f"\n{LINE}\nLOCAL UDP ENDPOINTS (first 50)\n{LINE}")
    rows = get_udp_endpoints()
    _print_table(
        rows,
        [
            ("LocalAddress", "Local address"),
            ("LocalPort", "Local port"),
            ("OwningProcess", "Process ID"),
        ],
    )
    print("\nUDP endpoints do not have TCP-style Established or Listening connection states.")


def show_menu() -> None:
    print(f"\n{LINE}")
    print(f"  SENTINEL X — NETWORK FUNDAMENTALS EXPLORER v{__version__}")
    print(LINE)
    print("  1. Network Inspector (IP, gateway, DNS, subnet)")
    print("  2. DNS Explorer")
    print("  3. Ping Tester")
    print("  4. TCP Port Tester")
    print("  5. ARP Viewer")
    print("  6. TCP Connection Monitor")
    print("  7. UDP Endpoint Viewer")
    print("  0. Exit")
    print(LINE)


def main() -> int:
    actions = {
        "1": show_network_inspector,
        "2": show_dns_explorer,
        "3": show_ping_tester,
        "4": show_tcp_tester,
        "5": show_arp_viewer,
        "6": show_tcp_monitor,
        "7": show_udp_viewer,
    }

    print("SENTINEL X is a local learning and diagnostics tool.")
    print("Use it on your own computer and only test systems you are authorized to access.")

    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        if choice == "0":
            print("Exiting SENTINEL X. Keep learning!")
            return 0
        action = actions.get(choice)
        if action is None:
            print("Invalid option. Choose 0 through 7.")
            continue
        try:
            action()
        except (WindowsCommandError, InputValidationError, RuntimeError, socket.gaierror) as exc:
            print(f"\n[!] {exc}")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    raise SystemExit(main())
