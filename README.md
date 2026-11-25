# SENTINEL X — Network Fundamentals Explorer

**Version:** 1.0.0  
**Platform:** Windows 10/11  
**Python:** 3.10+ recommended (tested with Python 3.13)

SENTINEL X is a beginner-friendly Windows networking lab. It turns networking fundamentals into practical diagnostics that you can run on your own computer.

## Features

1. **Network Inspector** — active adapters, IPv4 addresses, subnet prefixes, gateways and DNS servers.
2. **DNS Explorer** — resolve a hostname into IPv4 and IPv6 addresses.
3. **Ping Tester** — run a limited ICMP ping test.
4. **TCP Port Tester** — attempt a TCP connection to one specified host and port.
5. **ARP Viewer** — display the local Windows ARP table.
6. **TCP Connection Monitor** — inspect up to 50 local TCP connection entries.
7. **UDP Endpoint Viewer** — inspect up to 50 local UDP endpoints.

The application uses Python's standard library and Windows built-in tools/PowerShell. No third-party Python packages are required.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Windows PowerShell
- Wi-Fi or Ethernet connection for live network tests (some features also work offline)

## Run on Windows

1. Download and extract this repository.
2. Open PowerShell in the extracted `sentinel-x-network-explorer` folder.
3. Check Python:

   ```powershell
   py -3 --version
   ```

4. Start the application:

   ```powershell
   py -3 -m sentinel_x
   ```

   Or double-click `start_sentinel.bat`.

No `pip install` step is needed.

## Publish to your GitHub account

Create a new **empty** GitHub repository (for example, `sentinel-x-network-explorer`) without adding a README, license or `.gitignore` on GitHub. Then open PowerShell in this extracted project folder and run:

```powershell
git init
git add .
git commit -m "Initial release: SENTINEL X Network Fundamentals Explorer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sentinel-x-network-explorer.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Git may open a browser sign-in flow; authenticate through Git Credential Manager. Never paste a GitHub password or personal access token into the project files or chat.

## Run the tests

From the project folder:

```powershell
py -3 -m unittest discover -s tests -v
```

The automated tests cover subnet calculations, hostname validation and TCP port validation. Windows-only live commands should be manually tested on a Windows computer.

## Menu guide

| Menu | What it teaches |
|---|---|
| 1. Network Inspector | Interfaces, IP addressing, subnet masks, gateways and DNS |
| 2. DNS Explorer | Name resolution and IPv4/IPv6 |
| 3. Ping Tester | ICMP Echo Requests/Replies and packet loss |
| 4. TCP Port Tester | TCP connection attempts and destination ports |
| 5. ARP Viewer | Local IPv4-to-MAC mappings |
| 6. TCP Connection Monitor | Local/remote endpoints, TCP states and process IDs |
| 7. UDP Endpoint Viewer | Local UDP addresses and ports |

## Safety and privacy

- This is a local learning and diagnostics tool, not a vulnerability scanner.
- It does not scan network ranges or enumerate other people's devices.
- It does not collect credentials, passwords or browser data.
- It does not send telemetry to the project author.
- DNS, ping and TCP tests generate ordinary network traffic to the specific destination you enter.
- Only test systems and services you own or are authorized to access.
- A failed ping does not necessarily mean a host is offline; networks may filter ICMP.
- A successful TCP port test confirms a TCP connection, not that an application or TLS session is fully healthy.

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
│   └── windows.py
├── tests/
│   └── test_core.py
├── .gitignore
├── README.md
├── requirements.txt
└── start_sentinel.bat
```

## Learning path

This project is designed to grow with your networking knowledge:

- IP addresses and subnetting → Network Inspector
- ICMP and connectivity → Ping Tester
- DNS and address resolution → DNS Explorer
- TCP and ports → TCP Port Tester
- MAC addresses and ARP → ARP Viewer
- TCP states and process IDs → TCP Connection Monitor
- UDP and ports → UDP Endpoint Viewer

## Limitations

The PowerShell-based interface, ARP, TCP and UDP views are Windows-specific. Network details may change when you switch Wi-Fi networks, connect/disconnect a VPN, or enable virtual adapters. The application displays current local information and does not assume a fixed IP address or gateway.

## License

MIT License. See `LICENSE`.
