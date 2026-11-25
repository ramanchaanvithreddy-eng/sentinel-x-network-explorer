# Changelog

## 1.1.0

- Added an optional Streamlit dashboard bound to localhost.
- Added JSON and CSV investigation snapshot downloads.
- Added process name, executable path and Windows service enrichment for TCP/UDP inventory where available.
- Added readable TCP state labels and support for both numeric state values and named Windows states, including `Bound`.
- Prioritized established and listening entries in the limited TCP view.
- Expanded unit tests and added a GitHub Actions workflow for Windows and Ubuntu.
- Added architecture and safety-boundary documentation.

## 1.0.0

- Initial Windows network fundamentals CLI with network inspector, DNS, ping, TCP test, ARP, TCP connection and UDP endpoint modules.
