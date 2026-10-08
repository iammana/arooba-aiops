"""
Streamlit Web Dashboard for Arooba-AIOps.
Visualizes real-time Wi-Fi AP telemetry, client health,
interactive scenario injection, and autonomous AI Agent diagnostics.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path so simulator, core, and edge can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from typing import Dict, Any

from simulator.engine import simulator
from core.telemetry_client import telemetry_client
from core.agent import aiops_agent

# Page Configuration
st.set_page_config(
    page_title="Arooba-AIOps | Autonomous Wi-Fi Copilot",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ff8300; /* Accent Orange */
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #888888;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1a1c24;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #ff8300;
    }
    .stButton>button {
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================= Sidebar Controls =================
with st.sidebar:
    st.markdown("## 📡 **Arooba-AIOps**")
    st.caption("Autonomous Network Operations for Enterprise Wi-Fi APs")

    st.divider()

    # Telemetry Source Mode
    st.subheader("🌐 Telemetry Source")
    mode_choice = st.radio(
        "Source Mode",
        options=["Simulated Campus (Virtual APs)", "Physical Edge (Raspberry Pi 5)"],
        index=0 if telemetry_client.get_mode() == "simulated" else 1,
    )

    current_mode = "simulated" if "Simulated" in mode_choice else "hardware"
    telemetry_client.set_mode(current_mode)

    if current_mode == "hardware":
        st.markdown("#### 🍓 **Raspberry Pi 5 Connection**")
        edge_host_input = st.text_input(
            "Edge AP Host URL",
            value=telemetry_client.get_edge_host(),
            help="Edge Daemon REST URL. Default: http://192.168.4.1:8000 when connected to Pi AP, or http://<PI_LAN_IP>:8000 on LAN.",
        )
        if edge_host_input.strip() and edge_host_input.strip() != telemetry_client.get_edge_host():
            telemetry_client.set_edge_host(edge_host_input.strip())
            st.rerun()

        health = telemetry_client.check_edge_health()
        if health["connected"]:
            st.success("🟢 **Edge Node Connected**")
            details = health.get("data", {})
            tools = details.get("linux_tools_available", {})
            st.caption(
                f"**Interface:** `{details.get('interface', 'wlan0')}` | "
                f"**iw:** {'✅' if tools.get('iw') else '❌'} | "
                f"**hostapd_cli:** {'✅' if tools.get('hostapd_cli') else '❌'}"
            )
        else:
            st.error("🔴 **Edge Node Offline / Unreachable**")
            if health.get("error"):
                st.caption(f"**Error:** `{health['error']}`")

            with st.expander("🛠️ Connection Guide & Troubleshooting", expanded=False):
                st.markdown(
                    """
                    **How to connect to the Raspberry Pi 5 AP:**
                    1. **Direct AP Wi-Fi (Recommended):**
                       - Connect your device's Wi-Fi to SSID **`Arooba-AIOps-Lab`**
                       - WPA2 Password: **`AroobaAiOps2026!`**
                       - Default URL: `http://192.168.4.1:8000`
                    2. **Local LAN / Ethernet:**
                       - If the Pi is connected to your router/switch, enter its LAN IP above (e.g. `http://raspberrypi.local:8000` or `http://192.168.x.x:8000`).
                    3. **Check Edge Daemon Service on Pi:**
                       - Verify service: `sudo systemctl status arooba-edge`
                       - Or launch manually on the Pi:
                         ```bash
                         python3 -m uvicorn edge.daemon:app --host 0.0.0.0 --port 8000
                         ```
                    """
                )

        if st.button("🔄 Test / Retry Connection", width="stretch"):
            telemetry_client.check_edge_health(force=True)
            st.rerun()

        st.divider()

        st.subheader("📡 Physical Edge Operations")
        st.info(
            "🧪 **Incident Scenario Injection is disabled in Physical Edge mode.**\n\n"
            "Synthetic scenarios apply only to the multi-AP simulator. In Physical Edge mode, "
            "Arooba-AIOps monitors live physical RF telemetry, real frame retries, and physical client associations directly from the Pi 5's Broadcom Wi-Fi radio (`wlan0`)."
        )
    else:
        st.success("💻 Running Multi-AP In-Memory Simulation")

        st.divider()

        # Pre-canned Scenarios (for quick presentation demos)
        st.subheader("🧪 Inject Incident Scenario")
        scenario = st.selectbox(
            "Select Scenario",
            [
                ("baseline", "✅ Healthy Baseline"),
                ("sticky_client", "⚠️ Sticky Client Roaming Drop"),
                ("channel_congestion", "⚡ Co-Channel Interference (CCI)"),
                ("dhcp_exhaustion", "🚫 DHCP Scope Exhaustion"),
            ],
            format_func=lambda x: x[1],
        )

        if st.button("Apply Scenario", width="stretch", type="secondary"):
            msg = simulator.load_scenario(scenario[0])
            st.toast(msg, icon="🔔")
            st.rerun()

    st.divider()

    # Live Telemetry Stream Polling Controls
    st.subheader("⏱️ Live Telemetry Stream")
    auto_refresh = st.toggle(
        "Auto-Refresh Live Stream",
        value=False,
        help="Continuously poll live RF and client telemetry from the edge AP in the background.",
    )
    poll_seconds = 3
    if auto_refresh:
        poll_seconds = st.selectbox(
            "Polling Interval",
            options=[2, 3, 5, 10],
            index=1,
            format_func=lambda s: f"{s} seconds",
        )

    st.divider()
    st.caption("Arooba Autonomous Network Operations Engine")


# ================= Main Dashboard =================

st.markdown('<div class="main-header">📡 Arooba-AIOps Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous Wi-Fi Assurance, RF Telemetry Analytics & Self-Healing Agent</div>',
    unsafe_allow_html=True,
)

is_hardware = current_mode == "hardware"

# ================= Tabs: Telemetry Cockpit vs Agent Console =================
tab_cockpit, tab_agent = st.tabs(["📊 Live Telemetry Cockpit", "🤖 Autonomous AI Copilot Console"])

with tab_cockpit:
    @st.fragment(run_every=poll_seconds if auto_refresh else None)
    def render_live_telemetry_cockpit():
        import datetime
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        # Fetch Current Telemetry
        is_connected = True
        if is_hardware:
            health = telemetry_client.check_edge_health()
            is_connected = health.get("connected", False)

        aps = telemetry_client.get_all_aps()
        clients = telemetry_client.get_all_clients()
        services = telemetry_client.get_network_services()

        # Live Status Banner & Manual Refresh
        bar_col1, bar_col2 = st.columns([3, 1])
        with bar_col1:
            if auto_refresh:
                st.caption(f"🟢 **Live Telemetry Stream Active** (Auto-polling every {poll_seconds}s) • Last updated: `{now_str}`")
            else:
                st.caption(f"⏸️ **Live Stream Paused** • Last updated: `{now_str}`")
        with bar_col2:
            if st.button("🔄 Refresh Data", key="refresh_cockpit_btn", width="stretch"):
                st.rerun(scope="fragment")

        if is_hardware and not is_connected:
            st.warning(
                f"⚠️ **Raspberry Pi 5 Edge AP is unreachable at `{telemetry_client.get_edge_host()}`.** "
                "Showing disconnected state. Check sidebar settings to verify the Pi 5 Edge URL, ensure `arooba-edge` is running, "
                "or switch to **Simulated Campus** mode."
            )

        # Top Stats Overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if is_hardware and not is_connected:
                st.metric("Managed APs", 0, delta="Edge Offline", delta_color="inverse")
            else:
                st.metric("Managed APs", len(aps), delta="All Online" if len(aps) > 0 else "None")
        with col2:
            st.metric("Connected Stations", len(clients))
        with col3:
            if aps:
                avg_util = round(sum(ap.channel_utilization_pct for ap in aps) / max(1, len(aps)), 1)
                st.metric(
                    "Avg Channel Utilization",
                    f"{avg_util}%",
                    delta="-Congested" if avg_util > 50 else "+Optimal",
                    delta_color="inverse" if avg_util > 50 else "normal",
                )
            else:
                st.metric("Avg Channel Utilization", "N/A")
        with col4:
            if is_hardware and not is_connected:
                st.metric("DHCP Pool Usage", "N/A")
            elif services.dhcp_pool_total > 0:
                dhcp_pct = round((services.dhcp_pool_used / services.dhcp_pool_total) * 100, 1)
                st.metric(
                    "DHCP Pool Usage",
                    f"{dhcp_pct}%",
                    delta="Exhausted" if services.dhcp_exhausted else "Healthy",
                    delta_color="inverse" if services.dhcp_exhausted else "normal",
                )
            else:
                st.metric("DHCP Pool Usage", "N/A")

        st.divider()

        # Upstream Network Assurance SLA & Edge AP Health Bar
        st.subheader("🌐 Upstream Network Assurance SLA & AP Hardware Health")
        sla_col1, sla_col2, sla_col3, sla_col4, sla_col5 = st.columns(5)
        with sla_col1:
            if is_hardware and not is_connected:
                st.metric("Ethernet Uplink (eth0)", "Offline", delta="Edge Unreachable", delta_color="inverse")
            else:
                uplink_ok = services.eth0_carrier
                st.metric(
                    "Ethernet Uplink (eth0)",
                    f"{services.eth0_speed_mbps} Mbps Link" if uplink_ok else "Disconnected",
                    delta="🟢 Uplink Up" if uplink_ok else "🔴 Cable Unplugged",
                    delta_color="normal" if uplink_ok else "inverse",
                )
        with sla_col2:
            if is_hardware and not is_connected:
                st.metric("WAN Internet Latency", "N/A")
            else:
                wan_ms = services.wan_latency_ms
                st.metric(
                    "WAN Internet Latency",
                    f"{wan_ms} ms",
                    delta="🟢 1.1.1.1 RTT (Optimal)" if wan_ms < 30.0 else "⚠️ High WAN Latency",
                    delta_color="normal" if wan_ms < 30.0 else "inverse",
                )
        with sla_col3:
            if is_hardware and not is_connected:
                st.metric("DNS Benchmark", "N/A")
            else:
                dns_ms = services.dns_latency_ms
                st.metric(
                    "DNS Benchmark",
                    f"{dns_ms} ms",
                    delta="🟢 Fast Lookup" if dns_ms < 25.0 else "⚠️ Slow DNS",
                    delta_color="normal" if dns_ms < 25.0 else "inverse",
                )
        with sla_col4:
            if is_hardware and not is_connected:
                st.metric("Active NAT Sessions", "N/A")
            else:
                st.metric(
                    "Active NAT Sessions",
                    f"{services.conntrack_sessions}",
                    delta="conntrack table",
                )
        with sla_col5:
            if aps and aps[0].cpu_temp_c is not None:
                ap_temp = aps[0].cpu_temp_c
                is_hot = ap_temp > 70.0
                st.metric(
                    "AP SoC Temperature",
                    f"{ap_temp}°C",
                    delta="⚠️ Thermal Throttling" if is_hot else f"🟢 Cool (Load: {aps[0].cpu_load_1m})",
                    delta_color="inverse" if is_hot else "normal",
                )
            else:
                st.metric("AP SoC Temperature", "N/A")

        st.divider()

        st.subheader("Managed Access Point Radios")
        if not aps:
            if is_hardware:
                if is_connected:
                    err_detail = f" (Error: `{telemetry_client.last_error}`)" if telemetry_client.last_error else ""
                    st.info(f"📡 No Access Point radio metrics received{err_detail}. Connected client stations and DHCP services are active below.")
                else:
                    st.info("📡 No Access Point telemetry received. Verify that the Raspberry Pi 5 Edge Daemon is reachable.")
            else:
                st.info("No Access Points configured.")
        else:
            ap_cols = st.columns(len(aps))
            for idx, ap in enumerate(aps):
                with ap_cols[idx]:
                    is_congested = ap.channel_utilization_pct > 70.0
                    border_color = "🔴" if is_congested else "🟢"
                    st.markdown(f"#### {border_color} {ap.name}")
                    st.caption(f"**Model:** {ap.model}")
                    st.caption(f"**Location:** {ap.location}")
                    st.metric(
                        "Airtime Utilization",
                        f"{ap.channel_utilization_pct}%",
                        delta="Severe Interference" if is_congested else "Clean Airtime",
                        delta_color="inverse" if is_congested else "normal",
                    )
                    if is_hardware:
                        active_chan = ap.channel_5g if ap.channel_5g > 0 else ap.channel_2g
                        st.write(f"- **Radio & Band:** `{ap.band_mode}`")
                        st.write(f"- **Operating Channel:** Channel {active_chan} ({ap.channel_width_mhz} MHz Width)")
                        st.write(f"- **Actual Tx Power:** `{ap.tx_power_actual_dbm} dBm`")
                        st.write(f"- **Live Throughput:** `{ap.throughput_mbps} Mbps`")
                        st.write(f"- **Noise Floor:** `{ap.noise_floor_dbm} dBm`")
                        st.write(f"- **Clients Associated:** `{len(ap.connected_clients)}`")
                    else:
                        st.write(f"- **2.4 GHz:** Channel {ap.channel_2g} ({ap.tx_power_2g_dbm} dBm)")
                        st.write(f"- **5 GHz:** Channel {ap.channel_5g} ({ap.tx_power_5g_dbm} dBm)")
                        st.write(f"- **Noise Floor:** `{ap.noise_floor_dbm} dBm`")
                        st.write(f"- **Clients Associated:** `{len(ap.connected_clients)}`")

        st.divider()

        st.subheader("Connected Client Stations & RF Link Quality")
        if not clients:
            if is_hardware:
                st.info("No client stations currently associated with the Pi 5 AP (`wlan0`). Connect a smartphone or laptop to **`Arooba-AIOps-Lab`** to observe real RF telemetry.")
            else:
                st.info("No connected client stations.")
        else:
            client_data = []
            for c in clients:
                status_emoji = "🟢"
                if c.connection_state.value == "DHCP_FAILED":
                    status_emoji = "🔴 (DHCP Failure)"
                elif c.sticky_client_detected or c.rssi_dbm < -75:
                    status_emoji = "⚠️ (Sticky / Weak Link)"

                phy_str = f"{c.tx_bitrate_mbps} Mbps"
                if c.bitrate_info:
                    phy_str += f" ({c.bitrate_info})"

                tx_mb = round(c.tx_bytes / (1024 * 1024), 2)
                rx_mb = round(c.rx_bytes / (1024 * 1024), 2)
                traffic_str = f"{tx_mb} MB ↑ / {rx_mb} MB ↓" if (c.tx_bytes > 0 or c.rx_bytes > 0) else "Active"

                heartbeat_str = f"{c.inactive_time_ms} ms" if c.inactive_time_ms > 0 else "Instant"

                client_data.append({
                    "Status": status_emoji,
                    "Hostname": c.hostname,
                    "MAC Address": c.mac,
                    "IP Address": c.ip or "0.0.0.0",
                    "Associated AP": c.ap_name,
                    "Band": c.band,
                    "RSSI (dBm)": c.rssi_dbm,
                    "SNR (dB)": c.snr_db,
                    "PHY Rate / MCS": phy_str,
                    "Tx Retries (%)": f"{c.tx_retries_pct}%",
                    "Traffic Volume": traffic_str,
                    "Heartbeat": heartbeat_str,
                    "Last Event": c.last_event,
                })

            df = pd.DataFrame(client_data)
            st.dataframe(df, width="stretch", hide_index=True)

    render_live_telemetry_cockpit()


with tab_agent:
    st.subheader("Autonomous Wi-Fi Incident Investigation")
    st.write(
        "Enter a user complaint, support ticket, or alert. The AI agent will inspect RF telemetry, "
        "reconstruct the client journey, diagnose the root cause, and execute autonomous remediation."
    )

    agent_clients = telemetry_client.get_all_clients()
    # Prompt suggestions based on mode and scenario
    if is_hardware:
        if agent_clients:
            first_mac = agent_clients[0].mac
            default_prompt = f"Analyze RF link quality, signal strength (RSSI), and frame retry rates for station {first_mac} on RaspberryPi-5-Edge-AP."
        else:
            default_prompt = "Perform an RF health check and survey airtime utilization on RaspberryPi-5-Edge-AP."
    else:
        default_prompt = "Users in Conference Room B are complaining that Zoom calls keep dropping and latency is terrible."
        if simulator.current_scenario == "dhcp_exhaustion":
            default_prompt = "New guests in Conference Room B cannot connect to the Wi-Fi. Devices are stuck acquiring an IP address."
        elif simulator.current_scenario == "channel_congestion":
            default_prompt = "Wi-Fi is running extremely sluggish on AP-ConfRoom-B despite sitting right next to the access point."

    user_ticket = st.text_area("Support Ticket / Diagnostic Query:", value=default_prompt, height=80)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_btn = st.button("🚀 Run AIOps Agent", type="primary", width="stretch")

    if run_btn:
        with st.spinner("Agent is formulating hypotheses and querying telemetry tools..."):
            result = aiops_agent.run_investigation(user_ticket)

        st.success(f"Investigation completed using: **{result['provider']}**")

        # Step-by-Step Tool Trace
        with st.expander("🛠️ View Agent Tool Calls & Reasoning Trace", expanded=True):
            for step in result.get("trace", []):
                st.markdown(
                    f"**Step {step['step']}: Tool `{step['tool']}`** — *{step['result_summary']}*"
                )
                with st.container():
                    st.json(step["data"])

        # Final Report
        st.markdown("---")
        st.markdown(result["final_report"])

        if result.get("remediation"):
            st.toast("⚡ Autonomous Remediation Successfully Applied!", icon="✅")
            st.balloons()
