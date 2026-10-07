# 📡 Arooba-AIOps: Autonomous Wi-Fi Operations Copilot

[![Arooba-AIOps CI](https://github.com/fadi/arooba-aiops/actions/workflows/ci.yml/badge.svg)](https://github.com/fadi/arooba-aiops/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Wi-Fi 6/6E Telemetry](https://img.shields.io/badge/Wi--Fi-802.11ax%20%7C%20802.11v%2Fk-orange.svg)](#)

> **Autonomous Network Operations & Telemetry Agent for Enterprise Wi-Fi.**  
> *Inspired by HPE Aruba Central AIOps, with dual support for Cloud Simulation and Physical Edge APs (Raspberry Pi 5).*

---

## 🌟 Executive Overview

In enterprise wireless networks, Wi-Fi incidents are notoriously ambiguous. A user submits a ticket saying:
> *"The Wi-Fi in Conference Room B is sluggish and Zoom calls keep dropping."*

Diagnosing this manually requires correlating:
1. **Client RF Telemetry:** RSSI signal strength, SNR, PHY bitrate, and 802.11 frame retry rates.
2. **Access Point Airtime:** Channel utilization, co-channel interference (CCI), and RF noise floor.
3. **Roaming & Mobility Events:** Detecting **Sticky Client Syndrome** (stations refusing to roam to a closer AP).
4. **Core Infrastructure Services:** 802.1X/RADIUS authentication, DHCP scope exhaustion, and DNS latency.

**Arooba-AIOps** bridges low-level wireless telemetry and autonomous AI agents. It investigates complaints, systematically executes diagnostic tools, determines the definitive Root Cause Analysis (RCA), and performs closed-loop remediation (e.g. 802.11v BSS Transition steering, dynamic channel switching, or DHCP lease recovery).

---

## 🏗️ Architecture

```mermaid
flowchart TD
    subgraph UI ["User / IT Operations"]
        Ticket["Incident / Natural Language Ticket\n'Zoom dropping in Conf Room B'"]
        Dashboard["Streamlit Interactive Telemetry Dashboard"]
    end

    subgraph AgentCore ["AIOps AI Agent Orchestrator"]
        Orchestrator["Diagnostic Orchestrator & Reasoning Loop"]
        KnowledgeBase["802.11 RF Rules & RCA Engine"]
        Tools["Tool Registry\n(AP Health, Client Journey, Network Services)"]
    end

    subgraph DualMode ["Unified Telemetry Layer"]
        SimMode["Mode A: Multi-AP Enterprise Simulator\n(Lobby, Conf Room, Engineering Lab)"]
        HardwareMode["Mode B: Physical Edge AP (Raspberry Pi 5)\n(hostapd, dnsmasq, Linux iw, hostapd_cli)"]
    end

    Ticket --> Dashboard
    Dashboard --> Orchestrator
    Orchestrator <--> KnowledgeBase
    Orchestrator --> Tools
    Tools <--> DualMode
```

---

## ⚡ Key Highlights

* **Dual-Mode Deployment:**
  * **Simulation Mode:** Pre-loaded multi-AP campus deployment. Instant evaluation on any Mac/PC with **zero hardware**.
  * **Hardware Mode (Raspberry Pi 5):** Turns a Pi 5 into an actual Wi-Fi Access Point broadcasting an SSID, running real Linux `hostapd` / `dnsmasq`, and exposing live kernel 802.11 telemetry (`iw dev wlan0 station dump`).
* **Zero-Dependency Demo Guarantee:** Ships with an intelligent, deterministic rule engine that runs locally with **0 API keys required**, while seamlessly supporting **Google Gemini**, **OpenAI GPT-4o**, and **Anthropic Claude**.
* **Pre-Canned Incident Scenarios:**
  1. **Sticky Client Syndrome:** Client walked across the building but is stubbornly stuck to a distant 2.4 GHz AP at -83 dBm instead of a nearby Wi-Fi 6 AP (-46 dBm).
  2. **Co-Channel Interference (CCI):** Channel utilization surges to 91% due to airtime congestion.
  3. **Silent DHCP Exhaustion:** Wi-Fi link association succeeds, but station is trapped in `DHCP_DISCOVER_TIMEOUT`.
* **Automated Remediation:** Issues 802.11v BSS Transition Management frames, channel switch announcements (CSA), or DHCP pool lease purges.

---

## 🚀 Quickstart (30 Seconds)

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/fadi/arooba-aiops.git
cd arooba-aiops

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Interactive Web Dashboard

```bash
streamlit run ui/dashboard.py
```

Open your browser to `http://localhost:8501`. You can immediately:
* Inspect live AP airtime and client link tables.
* Inject an incident using the sidebar scenario dropdown.
* Run the AI Agent to watch real-time tool calls, RCA generation, and auto-remediation!

---

## 🍓 Raspberry Pi 5 Hardware Setup (Optional)

If you have a Raspberry Pi 5, you can turn it into an authentic Aruba-style Edge AP.

```
                    ┌───────────────────────────────┐
                    │     Raspberry Pi 5 (Edge)     │
                    │                               │
                    │   SSID: Aruba-AIOps-Lab       │
                    │   hostapd (802.11ac / 5GHz)   │
                    │   dnsmasq (192.168.4.1/24)    │
                    │   arooba-edge.service (:8000) │
                    └───────────────▲───────────────┘
                                    │ HTTP Telemetry & Control
                                    ▼
                    ┌───────────────────────────────┐
                    │      Laptop / Workstation     │
                    │                               │
                    │   Arooba-AIOps Copilot UI     │
                    └───────────────────────────────┘
```

### 1. Run Automated Setup on Pi 5 (Raspberry Pi OS Bookworm)

```bash
sudo bash edge/scripts/setup_pi_ap.sh
```

This automated script will:
* Install `hostapd`, `dnsmasq`, and `wireless-tools`.
* Configure static IP `192.168.4.1/24` on `wlan0`.
* Broadcast SSID **`Aruba-AIOps-Lab`** (WPA2 passphrase: `AroobaAiOps2026!`).
* Enable IP forwarding & NAT (routing Wi-Fi traffic out `eth0`).
* Launch the `arooba-edge` FastAPI daemon on port `8000`.

### 2. Connect Your Laptop to the Pi 5

In `ui/dashboard.py` (or your `.env` file), switch the source mode to **Physical Edge (Raspberry Pi 5)**:
```env
TELEMETRY_SOURCE=hardware
EDGE_AP_HOST=http://192.168.4.1:8000
```

Now, connect your smartphone or laptop to `Aruba-AIOps-Lab`. The AI Agent will read your phone's real RSSI, SNR, and PHY bitrate directly from the Pi 5's Broadcom wireless driver!

---

## 🧪 Testing

Run the automated test suite verifying parsers, simulation models, and AI agent diagnostic loops:

```bash
pytest -v tests/
```

---

## 📂 Repository Layout

```text
arooba-aiops/
├── README.md                      # Documentation, architecture, and quickstart
├── LICENSE                        # Apache 2.0 License
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment configuration template
├── .github/workflows/ci.yml       # GitHub Actions CI matrix
│
├── core/                          # AI Agent Core & Telemetry Client
│   ├── config.py                  # Environment config
│   ├── telemetry_client.py        # Unified interface (Simulator vs Hardware)
│   ├── tools.py                   # Diagnostic & Remediation tools
│   ├── prompts.py                 # HPE Aruba Tier-3 engineering prompts
│   └── agent.py                   # Multi-provider agent orchestrator
│
├── simulator/                     # In-Memory Multi-AP Campus Simulator
│   ├── models.py                  # Pydantic data schemas
│   └── engine.py                  # Wi-Fi state & scenario engine
│
├── edge/                          # Raspberry Pi 5 Edge Telemetry Daemon
│   ├── daemon.py                  # FastAPI service for hostapd/iw
│   ├── parsers.py                 # Linux 802.11 output parsers
│   ├── scripts/
│   │   ├── setup_pi_ap.sh         # One-click Pi 5 AP setup
│   │   ├── hostapd.conf.template  # 802.11ac AP configuration
│   │   └── dnsmasq.conf.template  # DHCP/DNS configuration
│   └── systemd/
│       └── arooba-edge.service    # Auto-start systemd service
│
├── ui/                            # Interactive Dashboard
│   └── dashboard.py               # Streamlit application
│
└── tests/                         # Pytest test suite
    ├── test_parsers.py            # Linux Wi-Fi text parsers
    ├── test_simulator.py          # State changes & scenarios
    └── test_agent.py              # Autonomous diagnostic loops
```

---

## 📜 License

Distributed under the [Apache 2.0 License](LICENSE).
