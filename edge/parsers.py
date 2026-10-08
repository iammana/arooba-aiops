"""
Linux 802.11 Wi-Fi Telemetry Parsers.
Parses output from `iw dev <interface> station dump`,
`iw dev <interface> survey dump`, and dnsmasq lease tables.
"""

import re
from typing import Dict, List, Optional, Any


def _finalize_station(current: Dict[str, Any]) -> None:
    """Ensures rssi_dbm and signal_avg_dbm fall back to each other if one is available."""
    if current.get("rssi_dbm") is None and current.get("signal_avg_dbm") is not None:
        current["rssi_dbm"] = current["signal_avg_dbm"]
        current["rssi_measured"] = True
    elif current.get("signal_avg_dbm") is None and current.get("rssi_dbm") is not None:
        current["signal_avg_dbm"] = current["rssi_dbm"]
        current["rssi_measured"] = True
    elif current.get("rssi_dbm") is not None:
        current["rssi_measured"] = True
    else:
        current["rssi_measured"] = False


def parse_station_dump(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses output from: `iw dev wlan0 station dump`
    Example format:
    Station a4:83:e7:2b:11:05 (on wlan0)
        inactive time:  120 ms
        rx bytes:       145920
        rx packets:     1204
        tx bytes:       854002
        tx packets:     2840
        tx retries:     14
        tx failed:      0
        signal:         -52 dBm
        signal avg:     -53 dBm
        tx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
        rx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
        authorized:     yes
        authenticated:  yes
        associated:     yes
    """
    stations: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        station_match = re.match(r"^Station\s+([0-9a-fA-F:]{17})", line)
        if station_match:
            if current:
                _finalize_station(current)
                stations.append(current)
            current = {
                "mac": station_match.group(1).lower(),
                "rssi_dbm": None,
                "signal_avg_dbm": None,
                "rssi_measured": False,
                "tx_bitrate_mbps": 0.0,
                "rx_bitrate_mbps": 0.0,
                "tx_bitrate_info": "",
                "tx_retries": 0,
                "tx_failed": 0,
                "rx_bytes": 0,
                "tx_bytes": 0,
                "rx_packets": 0,
                "tx_packets": 0,
                "inactive_time_ms": 0,
                "signal_chains": [],
                "authorized": True,
            }
            continue

        if not current:
            continue

        # Handle 'signal:' with optional MIMO bracketed values: 'signal: -52 [-55, -57] dBm'
        if re.match(r"^signal\s*:", line, re.IGNORECASE):
            m = re.search(r"(-?\d+)", line[line.find(":") + 1:])
            if m:
                current["rssi_dbm"] = int(m.group(1))
            # Extract per-chain MIMO antenna values if present, e.g. [-55, -57]
            m_chains = re.search(r"\[(.*?)\]", line)
            if m_chains:
                chains = []
                for val in m_chains.group(1).split(","):
                    val = val.strip()
                    if val.lstrip("-").isdigit():
                        chains.append(int(val))
                if chains:
                    current["signal_chains"] = chains
        elif re.match(r"^signal\s+avg\s*:", line, re.IGNORECASE):
            m = re.search(r"(-?\d+)", line[line.find(":") + 1:])
            if m:
                current["signal_avg_dbm"] = int(m.group(1))
        elif line.startswith("tx retries:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["tx_retries"] = int(m.group(1))
        elif line.startswith("tx failed:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["tx_failed"] = int(m.group(1))
        elif line.startswith("rx bytes:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["rx_bytes"] = int(m.group(1))
        elif line.startswith("tx bytes:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["tx_bytes"] = int(m.group(1))
        elif line.startswith("rx packets:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["rx_packets"] = int(m.group(1))
        elif line.startswith("tx packets:"):
            m = re.search(r"(\d+)", line)
            if m:
                current["tx_packets"] = int(m.group(1))
        elif line.startswith("tx bitrate:"):
            m = re.search(r"([\d.]+)\s*MBit/s(.*)", line)
            if m:
                current["tx_bitrate_mbps"] = float(m.group(1))
                current["tx_bitrate_info"] = m.group(2).strip()
        elif line.startswith("rx bitrate:"):
            m = re.search(r"([\d.]+)\s*MBit/s", line)
            if m:
                current["rx_bitrate_mbps"] = float(m.group(1))
        elif line.startswith("inactive time:"):
            m = re.search(r"(\d+)\s*ms", line)
            if m:
                current["inactive_time_ms"] = int(m.group(1))

    if current:
        _finalize_station(current)
        stations.append(current)

    return stations


def parse_hostapd_all_sta(raw_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses output from: `hostapd_cli -i <interface> all_sta`
    Returns a dictionary keyed by MAC address with station metrics like signal,
    rates, and connection duration.
    """
    stations: Dict[str, Dict[str, Any]] = {}
    current_mac: Optional[str] = None
    current_data: Dict[str, Any] = {}

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        mac_m = re.match(r"^([0-9a-fA-F:]{17})$", line)
        if mac_m:
            if current_mac:
                stations[current_mac] = current_data
            current_mac = mac_m.group(1).lower()
            current_data = {}
            continue
        if current_mac and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "signal":
                try:
                    current_data["signal"] = int(v)
                except ValueError:
                    pass
            elif k in ("rx_rate_info", "tx_rate_info"):
                try:
                    # In hostapd_cli, rate_info is given in units of 100 kbps (e.g., 722 = 72.2 Mbps)
                    current_data[k] = float(v) / 10.0
                except ValueError:
                    pass
            elif k == "connected_time":
                try:
                    current_data["connected_time_sec"] = int(v)
                except ValueError:
                    pass
            elif k == "flags":
                current_data["flags"] = v

    if current_mac:
        stations[current_mac] = current_data

    return stations


def parse_survey_dump(raw_text: str) -> Dict[str, Any]:
    """
    Parses output from: `iw dev wlan0 survey dump`
    Computes channel active vs channel busy time to calculate airtime utilization.
    """
    active_time = 0
    busy_time = 0
    noise_dbm = -95
    frequency_mhz = 2412

    for line in raw_text.splitlines():
        line = line.strip()
        if "frequency:" in line:
            m = re.search(r"(\d+)\s*MHz", line)
            if m:
                frequency_mhz = int(m.group(1))
        elif "noise:" in line:
            m = re.search(r"(-?\d+)\s*dBm", line)
            if m:
                noise_dbm = int(m.group(1))
        elif "channel active time:" in line:
            m = re.search(r"(\d+)\s*ms", line)
            if m:
                active_time = int(m.group(1))
        elif "channel busy time:" in line:
            m = re.search(r"(\d+)\s*ms", line)
            if m:
                busy_time = int(m.group(1))

    utilization_pct = 0.0
    if active_time > 0:
        utilization_pct = round((busy_time / active_time) * 100.0, 1)

    return {
        "frequency_mhz": frequency_mhz,
        "noise_floor_dbm": noise_dbm,
        "channel_active_time_ms": active_time,
        "channel_busy_time_ms": busy_time,
        "channel_utilization_pct": utilization_pct,
    }


def parse_dnsmasq_leases(raw_text: str) -> Dict[str, Dict[str, str]]:
    """
    Parses `/var/lib/misc/dnsmasq.leases`
    Format: <timestamp> <mac> <ip> <hostname> <client-id>
    """
    leases: Dict[str, Dict[str, str]] = {}
    for line in raw_text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4:
            mac = parts[1].lower()
            leases[mac] = {
                "ip": parts[2],
                "hostname": parts[3] if parts[3] != "*" else "Unknown-Station",
            }
    return leases


def parse_iw_info(raw_text: str) -> Dict[str, Any]:
    """
    Parses output from: `iw dev wlan0 info`
    Extracts real channel, frequency, channel width (e.g. 20/40/80 MHz),
    center frequency, and configured Tx power.
    """
    res: Dict[str, Any] = {
        "channel": 36,
        "frequency_mhz": 5180,
        "channel_width_mhz": 20,
        "center_freq1_mhz": None,
        "tx_power_dbm": 20.0,
        "ssid": "",
        "type": "AP",
    }
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("ssid "):
            res["ssid"] = line[5:].strip()
        elif line.startswith("type "):
            res["type"] = line[5:].strip()
        elif "channel" in line:
            chan_m = re.search(r"channel\s+(\d+)", line)
            if chan_m:
                res["channel"] = int(chan_m.group(1))
            freq_m = re.search(r"\((\d+)\s*MHz\)", line)
            if freq_m:
                res["frequency_mhz"] = int(freq_m.group(1))
            width_m = re.search(r"width:\s*(\d+)\s*MHz", line)
            if width_m:
                res["channel_width_mhz"] = int(width_m.group(1))
            center_m = re.search(r"center1:\s*(\d+)\s*MHz", line)
            if center_m:
                res["center_freq1_mhz"] = int(center_m.group(1))
        elif line.startswith("txpower"):
            pwr_m = re.search(r"([\d.]+)\s*dBm", line)
            if pwr_m:
                res["tx_power_dbm"] = float(pwr_m.group(1))
    return res


def parse_proc_net_dev(raw_text: str, interface: str = "wlan0") -> Dict[str, int]:
    """
    Parses `/proc/net/dev` to extract total bytes, packets, and errors
    for a given network interface.
    """
    for line in raw_text.splitlines():
        if f"{interface}:" in line:
            parts = line.split(":", 1)[1].split()
            if len(parts) >= 16:
                return {
                    "rx_bytes": int(parts[0]),
                    "rx_packets": int(parts[1]),
                    "rx_errs": int(parts[2]),
                    "rx_drop": int(parts[3]),
                    "tx_bytes": int(parts[8]),
                    "tx_packets": int(parts[9]),
                    "tx_errs": int(parts[10]),
                    "tx_drop": int(parts[11]),
                }
    return {
        "rx_bytes": 0, "rx_packets": 0, "rx_errs": 0, "rx_drop": 0,
        "tx_bytes": 0, "tx_packets": 0, "tx_errs": 0, "tx_drop": 0,
    }

