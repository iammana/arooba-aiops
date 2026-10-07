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
        st.info("📡 Connecting to Raspberry Pi 5 AP via REST (`wlan0` / `hostapd`)")
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
    st.caption("Arooba Autonomous Network Operations Engine")


# ================= Main Dashboard =================

st.markdown('<div class="main-header">📡 Arooba-AIOps Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous Wi-Fi Assurance, RF Telemetry Analytics & Self-Healing Agent</div>',
    unsafe_allow_html=True,
)

# Fetch Current Telemetry
aps = telemetry_client.get_all_aps()
clients = telemetry_client.get_all_clients()
services = telemetry_client.get_network_services()

# Top Stats Overview
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Managed APs", len(aps), delta="All Online")
with col2:
    st.metric("Connected Stations", len(clients))
with col3:
    avg_util = round(sum(ap.channel_utilization_pct for ap in aps) / max(1, len(aps)), 1)
    st.metric(
        "Avg Channel Utilization",
        f"{avg_util}%",
        delta="-Congested" if avg_util > 50 else "+Optimal",
        delta_color="inverse" if avg_util > 50 else "normal",
    )
with col4:
    dhcp_pct = round((services.dhcp_pool_used / services.dhcp_pool_total) * 100, 1)
    st.metric(
        "DHCP Pool Usage",
        f"{dhcp_pct}%",
        delta="Exhausted" if services.dhcp_exhausted else "Healthy",
        delta_color="inverse" if services.dhcp_exhausted else "normal",
    )

st.divider()

# ================= Tabs: Telemetry Cockpit vs Agent Console =================
tab_cockpit, tab_agent = st.tabs(["📊 Live Telemetry Cockpit", "🤖 Autonomous AI Copilot Console"])

with tab_cockpit:
    st.subheader("Managed Access Point Radios")
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
            st.write(f"- **2.4 GHz:** Channel {ap.channel_2g} ({ap.tx_power_2g_dbm} dBm)")
            st.write(f"- **5 GHz:** Channel {ap.channel_5g} ({ap.tx_power_5g_dbm} dBm)")
            st.write(f"- **Noise Floor:** `{ap.noise_floor_dbm} dBm`")
            st.write(f"- **Clients Associated:** `{len(ap.connected_clients)}`")

    st.divider()

    st.subheader("Connected Client Stations & RF Link Quality")
    client_data = []
    for c in clients:
        status_emoji = "🟢"
        if c.connection_state.value == "DHCP_FAILED":
            status_emoji = "🔴 (DHCP Failure)"
        elif c.sticky_client_detected or c.rssi_dbm < -75:
            status_emoji = "⚠️ (Sticky / Weak Link)"

        client_data.append({
            "Status": status_emoji,
            "Hostname": c.hostname,
            "MAC Address": c.mac,
            "IP Address": c.ip or "0.0.0.0",
            "Associated AP": c.ap_name,
            "Band": c.band,
            "RSSI (dBm)": c.rssi_dbm,
            "SNR (dB)": c.snr_db,
            "PHY Tx (Mbps)": c.tx_bitrate_mbps,
            "Tx Retries (%)": f"{c.tx_retries_pct}%",
            "Last Event": c.last_event,
        })

    df = pd.DataFrame(client_data)
    st.dataframe(df, width="stretch", hide_index=True)


with tab_agent:
    st.subheader("Autonomous Wi-Fi Incident Investigation")
    st.write(
        "Enter a user complaint, support ticket, or alert. The AI agent will inspect RF telemetry, "
        "reconstruct the client journey, diagnose the root cause, and execute autonomous remediation."
    )

    # Prompt suggestions based on current scenario
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
