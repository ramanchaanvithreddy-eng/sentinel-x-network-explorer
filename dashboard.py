"""Local-only Streamlit dashboard for SENTINEL X."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import streamlit as st

from sentinel_x import __version__
from sentinel_x.connections import get_tcp_connections, get_udp_endpoints, tcp_state_label
from sentinel_x.diagnostics import ping_host, resolve_host, test_tcp_connection
from sentinel_x.network import get_arp_table, get_network_configurations, summarize_ipv4
from sentinel_x.reporting import build_snapshot, snapshot_to_csv, snapshot_to_json


st.set_page_config(
    page_title="SENTINEL X | Network Operations",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
      [data-testid="stMetric"] {background: rgba(120,130,150,.08); padding: 14px 16px; border-radius: 12px;}
      .sx-muted {color: #8290a6; font-size: .9rem;}
      .sx-title {font-size: 2rem; font-weight: 750; letter-spacing: -.035em;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe_collect(collector: Callable[[], Any]) -> tuple[Any, str | None]:
    try:
        return collector(), None
    except Exception as exc:  # Surface the issue to the dashboard without crashing the app.
        return [], f"{type(exc).__name__}: {exc}"


@st.cache_data(ttl=15, show_spinner=False)
def load_snapshot_data() -> dict[str, Any]:
    collectors = {
        "network": get_network_configurations,
        "arp": get_arp_table,
        "tcp": get_tcp_connections,
        "udp": get_udp_endpoints,
    }
    data: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for key, collector in collectors.items():
        value, error = _safe_collect(collector)
        data[key] = value
        if error:
            errors[key] = error
    data["errors"] = errors
    return data


def _records(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _values(value: Any) -> list[Any]:
    """Normalize PowerShell JSON fields that may be scalar or arrays."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _join_values(value: Any) -> str:
    return ", ".join(str(item) for item in _values(value))


def _interface_rows(configurations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in configurations:
        ipv4 = _values(item.get("IPv4Addresses"))
        prefixes = _values(item.get("PrefixLengths"))
        gateways = _values(item.get("IPv4Gateways"))
        dns = _values(item.get("DnsServers"))
        rows.append(
            {
                "Interface": item.get("InterfaceAlias"),
                "Adapter": item.get("Description"),
                "IPv4": ", ".join(str(v) for v in ipv4),
                "Prefix": ", ".join(str(v) for v in prefixes),
                "Gateway": ", ".join(str(v) for v in gateways),
                "DNS servers": ", ".join(str(v) for v in dns),
            }
        )
    return rows


def _tcp_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "Local address": row.get("LocalAddress"),
                "Local port": row.get("LocalPort"),
                "Remote address": row.get("RemoteAddress"),
                "Remote port": row.get("RemotePort"),
                "State": tcp_state_label(row.get("StateName") or row.get("StateCode") or row.get("State")),
                "PID": row.get("OwningProcess"),
                "Process": row.get("ProcessName") or "Unknown / access restricted",
                "Services": _join_values(row.get("ServiceNames")),
            }
        )
    return output


def _udp_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "Local address": row.get("LocalAddress"),
                "Local port": row.get("LocalPort"),
                "PID": row.get("OwningProcess"),
                "Process": row.get("ProcessName") or "Unknown / access restricted",
                "Services": _join_values(row.get("ServiceNames")),
                "Executable": row.get("ExecutablePath"),
            }
        )
    return output


def _show_errors(errors: dict[str, str]) -> None:
    if errors:
        with st.expander("Collection warnings", expanded=False):
            for section, message in errors.items():
                st.warning(f"{section}: {message}")


def main() -> None:
    st.sidebar.markdown("# 🛡️ SENTINEL X")
    st.sidebar.caption(f"Network Fundamentals Explorer · v{__version__}")
    page = st.sidebar.radio(
        "Workspace",
        [
            "Overview",
            "Network Interfaces",
            "TCP Connections",
            "UDP Endpoints",
            "ARP Table",
            "Diagnostics",
            "Investigation Reports",
        ],
    )
    if st.sidebar.button("↻ Refresh local data", use_container_width=True):
        load_snapshot_data.clear()
        st.rerun()
    st.sidebar.divider()
    st.sidebar.caption("Local-only diagnostics. Use only on devices and services you are authorized to inspect.")

    st.markdown('<div class="sx-title">SENTINEL X</div>', unsafe_allow_html=True)
    st.caption("Local network visibility and beginner-friendly investigation workspace")
    data = load_snapshot_data()
    errors = data["errors"]
    _show_errors(errors)

    if page == "Overview":
        tcp = _tcp_rows(_records(data["tcp"]))
        udp = _udp_rows(_records(data["udp"]))
        established = sum(1 for row in tcp if row["State"] == "Established")
        cols = st.columns(4)
        cols[0].metric("Network interfaces", len(_records(data["network"])))
        cols[1].metric("TCP entries", len(tcp))
        cols[2].metric("Established TCP", established)
        cols[3].metric("UDP endpoints", len(udp))
        st.subheader("Network interfaces")
        st.dataframe(_interface_rows(_records(data["network"])), use_container_width=True, hide_index=True)
        st.subheader("Recent TCP entries")
        st.dataframe(tcp[:15], use_container_width=True, hide_index=True)
        st.info("A connection or listening port is not automatically suspicious. Review its owning process and expected purpose.")

    elif page == "Network Interfaces":
        st.subheader("Network interface inventory")
        st.dataframe(_interface_rows(_records(data["network"])), use_container_width=True, hide_index=True)
        for interface in _records(data["network"]):
            ips = _values(interface.get("IPv4Addresses"))
            prefixes = _values(interface.get("PrefixLengths"))
            for ip_address, prefix in zip(ips, prefixes):
                facts = summarize_ipv4(str(ip_address), int(prefix))
                with st.expander(f"{interface.get('InterfaceAlias', 'Interface')}: {ip_address}/{prefix}"):
                    st.json(facts)

    elif page == "TCP Connections":
        st.subheader("TCP connection inventory")
        rows = _tcp_rows(_records(data["tcp"]))
        if rows:
            states = sorted({str(row["State"]) for row in rows})
            selected = st.multiselect("Filter by TCP state", states, default=states)
            filtered = [row for row in rows if row["State"] in selected]
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            st.caption("Process names and service names are collected from local Windows process/service metadata. Missing values can result from access restrictions or processes exiting during collection.")
        else:
            st.info("No TCP entries were returned.")

    elif page == "UDP Endpoints":
        st.subheader("Local UDP endpoints")
        rows = _udp_rows(_records(data["udp"]))
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("UDP endpoints show local bindings. They do not provide TCP-style connection states or prove that a datagram is currently being sent.")

    elif page == "ARP Table":
        st.subheader("Local ARP table")
        st.dataframe(_records(data["arp"]), use_container_width=True, hide_index=True)
        st.caption("ARP maps local IPv4 next-hop addresses to link-layer MAC addresses. It is not an internet-wide device inventory.")

    elif page == "Diagnostics":
        st.subheader("Targeted diagnostics")
        st.warning("These tests contact only the single hostname or IP you enter. Test only systems you own or are authorized to access.")
        with st.form("dns_form"):
            dns_host = st.text_input("DNS hostname", value="example.com")
            dns_submit = st.form_submit_button("Resolve hostname")
        if dns_submit:
            try:
                st.write({"hostname": dns_host, "addresses": resolve_host(dns_host)})
            except Exception as exc:
                st.error(str(exc))
        with st.form("tcp_form"):
            tcp_host = st.text_input("TCP hostname", value="example.com")
            tcp_port = st.number_input("TCP port", min_value=1, max_value=65535, value=443, step=1)
            tcp_submit = st.form_submit_button("Test TCP connection")
        if tcp_submit:
            try:
                result = test_tcp_connection(tcp_host, int(tcp_port))
                if result.success:
                    st.success(f"TCP connection succeeded: {result.host}:{result.port} via {result.remote_ip}")
                else:
                    st.warning(result.message)
            except Exception as exc:
                st.error(str(exc))
        with st.form("ping_form"):
            ping_target = st.text_input("Ping hostname or IP", value="127.0.0.1")
            ping_submit = st.form_submit_button("Run 4-packet ping")
        if ping_submit:
            try:
                success, output = ping_host(ping_target, count=4)
                st.code(output)
                (st.success if success else st.warning)("Ping replies received." if success else "No successful ping replies.")
            except Exception as exc:
                st.error(str(exc))

    elif page == "Investigation Reports":
        st.subheader("Export local investigation snapshot")
        st.warning("Reports may contain private IP addresses, MAC addresses, process names, executable paths and service details. Review and redact them before sharing or publishing.")
        snapshot = build_snapshot(
            network=_records(data["network"]),
            arp=_records(data["arp"]),
            tcp=_records(data["tcp"]),
            udp=_records(data["udp"]),
        )
        json_text = snapshot_to_json(snapshot)
        csv_text = snapshot_to_csv(snapshot)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        col1, col2 = st.columns(2)
        col1.download_button(
            "Download JSON report",
            data=json_text,
            file_name=f"sentinel_x_report_{stamp}.json",
            mime="application/json",
            use_container_width=True,
        )
        col2.download_button(
            "Download CSV report",
            data=csv_text,
            file_name=f"sentinel_x_report_{stamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(f"Snapshot generated at {snapshot['generated_at_utc']}")
        with st.expander("Preview report metadata"):
            st.json({key: snapshot[key] for key in ("application", "version", "generated_at_utc", "computer_name", "platform", "data_scope")})

    st.divider()
    st.caption(f"SENTINEL X v{__version__} · Runs locally on your computer · No telemetry is sent by this app")


if __name__ == "__main__":
    main()
