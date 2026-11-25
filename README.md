# SENTINEL X — Network Fundamentals Explorer

**Version:** 1.1.0  
**Platform:** Windows 10/11  
**Python:** 3.11–3.15 recommended for the optional Streamlit dashboard (the original CLI uses the standard library).

SENTINEL X is a local Windows networking lab that helps learners understand IP configuration, DNS, ICMP, TCP, UDP, ARP, Windows processes and services.

## What's new in v1.1.0

- Readable TCP state labels (for example, `Established`, `Listening`, and `Bound`).
- TCP results prioritize established and listening entries before filling the 100-row display limit.
- TCP state decoding handles both numeric values and friendly Windows enum names.
- TCP and UDP endpoint tables enriched with local process names, executable paths and Windows service names where Windows permits access.
- Optional local Streamlit dashboard with overview metrics, network interfaces, TCP connections, UDP endpoints, ARP entries and targeted diagnostics.
- JSON and CSV investigation report downloads.
- Expanded unit tests for state labels and report serialization.
- The original command-line application remains available.

## Requirements

- Windows 10 or Windows 11 for the Windows-specific collectors.
- Python 3.10+ for the command-line application.
- Python 3.11–3.15 for the optional current Streamlit dashboard. See the [official Streamlit installation guide](https://docs.streamlit.io/get-started/installation/command-line).

## Run the command-line application

Open PowerShell in the extracted project folder:

```powershell
py -3 -m sentinel_x
```

Or double-click `start_sentinel.bat`.

## Run the dashboard

Create and activate a project-specific virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the dashboard:

```powershell
py -3 -m streamlit run dashboard.py --server.address 127.0.0.1
```

Or double-click `start_dashboard.bat` after installing dependencies.

The dashboard is explicitly bound to `127.0.0.1`, so it is intended for local use on this computer rather than access from other devices on the network.

## Run tests

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m compileall -q sentinel_x tests
```

The unit tests cover input validation, subnet calculations, TCP state labels and report serialization. Windows-specific live collectors should also be checked on a Windows machine. GitHub Actions runs the platform-independent tests on Windows and Ubuntu for pushes and pull requests.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module responsibilities, data flow, security boundaries and limitations. Release history is in [`CHANGELOG.md`](CHANGELOG.md).

## Dashboard sections

- **Overview:** interface count, TCP entries, established TCP entries and UDP endpoints.
- **Network Interfaces:** adapters, IPv4 addresses, prefix lengths, gateways and DNS servers.
- **TCP Connections:** endpoints, readable states, process names, PIDs and service names.
- **UDP Endpoints:** local bindings with process and service information.
- **ARP Table:** local IPv4-to-MAC mappings.
- **Diagnostics:** single-target DNS, ping and TCP connectivity tests.
- **Investigation Reports:** download JSON and CSV snapshots.

## Privacy and safety

- This is a local learning and diagnostics tool, not a vulnerability scanner.
- It does not scan IP ranges or enumerate other people's devices.
- Diagnostics test only the single destination entered by the user.
- The dashboard binds to localhost (`127.0.0.1`) by default.
- Reports can contain private IP addresses, MAC addresses, process names, executable paths and Windows service details. Review and redact reports before sharing or publishing them.
- A listening port, UDP binding or unfamiliar remote IP is not automatically malicious.
- Process names and service associations can be unavailable when Windows restricts access or a process exits during collection.
- TCP success proves a TCP connection, not that the application protocol or TLS session is healthy.
- A failed ping does not necessarily mean a host is offline; ICMP may be filtered.

## Project structure

```text
sentinel-x-network-explorer/
├── sentinel_x/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── connections.py
│   ├── diagnostics.py
│   ├── network.py
│   ├── reporting.py
│   └── windows.py
├── tests/
│   └── test_core.py
├── dashboard.py
├── requirements.txt
├── start_sentinel.bat
├── start_dashboard.bat
├── README.md
└── LICENSE
```

## Upgrade an existing v1.0.0 clone

Do not run `git init` again and do not delete the `.git` directory. Extract this release to a temporary folder, copy its project files over your existing local clone (the archive does not contain `.git`), then run:

```powershell
git status
git add .
git commit -m "SENTINEL X v1.1.0: dashboard, process intelligence and CI"
git push
```

Review `git status` before committing. The dashboard report exports can include private IP addresses, MAC addresses, process names and executable paths; inspect and redact reports before sharing. Never place GitHub credentials in source files or chat.

## GitHub Actions

The repository includes `.github/workflows/tests.yml`. It runs the standard-library unit tests and Python compilation checks on Windows and Ubuntu for pushes and pull requests.

## License

MIT License. See `LICENSE`.
