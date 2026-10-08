"""
Diagnostic and Remediation Tools for Arooba-AIOps Agents.
Exposed as function tools for LLM reasoning and the AIOps execution engine.
"""

from typing import Dict, Any, List
from core.telemetry_client import telemetry_client


def list_access_points() -> List[Dict[str, Any]]:
    """
    Returns an inventory of all managed Wi-Fi Access Points,
    their locations, active channels, and airtime utilization percentages.
    """
    aps = telemetry_client.get_all_aps()
    return [
        {
            "ap_id": ap.ap_id,
            "name": ap.name,
            "model": ap.model,
            "location": ap.location,
            "channel_2g": ap.channel_2g,
            "channel_5g": ap.channel_5g,
            "channel_utilization_pct": ap.channel_utilization_pct,
            "noise_floor_dbm": ap.noise_floor_dbm,
            "client_count": len(ap.connected_clients) if ap.connected_clients else 0,
        }
        for ap in aps
    ]


def get_ap_rf_health(ap_id: str) -> Dict[str, Any]:
    """
    Retrieves deep Radio Frequency (RF) health metrics for a specific Access Point.
    Includes channel utilization, background noise floor, transmit power, and connected clients.
    """
    ap = telemetry_client.get_ap(ap_id)
    if not ap:
        return {"error": f"Access Point '{ap_id}' not found."}

    return {
        "ap_id": ap.ap_id,
        "name": ap.name,
        "channel_utilization_pct": ap.channel_utilization_pct,
        "is_congested": ap.channel_utilization_pct > 70.0,
        "noise_floor_dbm": ap.noise_floor_dbm,
        "rf_interference_detected": ap.noise_floor_dbm > -85,
        "channel_2g": ap.channel_2g,
        "channel_5g": ap.channel_5g,
        "channel_width_mhz": ap.channel_width_mhz,
        "tx_power_2g_dbm": ap.tx_power_2g_dbm,
        "tx_power_5g_dbm": ap.tx_power_5g_dbm,
        "tx_power_actual_dbm": ap.tx_power_actual_dbm,
        "band_mode": ap.band_mode,
        "throughput_mbps": ap.throughput_mbps,
        "cpu_temp_c": ap.cpu_temp_c,
        "cpu_load_1m": ap.cpu_load_1m,
        "connected_clients": ap.connected_clients,
    }


def list_connected_clients() -> List[Dict[str, Any]]:
    """
    Returns a summary of all active client stations currently associated to the network,
    including their MAC, IP, hostname, RSSI, SNR, and associated AP.
    """
    clients = telemetry_client.get_all_clients()
    return [
        {
            "mac": c.mac,
            "ip": c.ip or "No IP (Pending DHCP)",
            "hostname": c.hostname,
            "associated_ap": c.ap_name,
            "band": c.band,
            "rssi_dbm": c.rssi_dbm,
            "snr_db": c.snr_db,
            "tx_retries_pct": c.tx_retries_pct,
            "sticky_client": c.sticky_client_detected,
            "connection_state": c.connection_state.value,
        }
        for c in clients
    ]


def get_client_telemetry(identifier: str) -> Dict[str, Any]:
    """
    Deep-dives into a single client station by MAC address, IP address, or hostname.
    Returns full Client Journey metrics: RSSI, SNR, PHY bitrate, retries, roam history,
    sticky client status, and last connection event.
    """
    client = telemetry_client.get_client(identifier)
    if not client:
        return {"error": f"Client matching '{identifier}' not found."}

    # Evaluate RF health thresholds
    rf_health = "POOR" if client.rssi_dbm < -75 else ("FAIR" if client.rssi_dbm < -67 else "EXCELLENT")

    return {
        "mac": client.mac,
        "ip": client.ip,
        "hostname": client.hostname,
        "associated_ap": client.ap_name,
        "associated_bssid": client.bssid,
        "band": client.band,
        "rssi_dbm": client.rssi_dbm,
        "rf_health": rf_health,
        "snr_db": client.snr_db,
        "tx_bitrate_mbps": client.tx_bitrate_mbps,
        "rx_bitrate_mbps": client.rx_bitrate_mbps,
        "bitrate_info": client.bitrate_info,
        "tx_retries_pct": client.tx_retries_pct,
        "tx_failed": client.tx_failed,
        "rx_bytes": client.rx_bytes,
        "tx_bytes": client.tx_bytes,
        "inactive_time_ms": client.inactive_time_ms,
        "connected_time_sec": client.connected_time_sec,
        "signal_chains": client.signal_chains,
        "high_retries": client.tx_retries_pct > 15.0,
        "connection_state": client.connection_state.value,
        "sticky_client_detected": client.sticky_client_detected,
        "roam_count": client.roam_count,
        "last_event": client.last_event,
    }


def check_network_services() -> Dict[str, Any]:
    """
    Checks the status of core network infrastructure services:
    DHCP lease scope utilization, DNS resolution latency, Default Gateway ping, and 802.1X/RADIUS status.
    """
    services = telemetry_client.get_network_services()
    return {
        "dhcp_pool_total": services.dhcp_pool_total,
        "dhcp_pool_used": services.dhcp_pool_used,
        "dhcp_exhausted": services.dhcp_exhausted,
        "dhcp_utilization_pct": round((services.dhcp_pool_used / services.dhcp_pool_total) * 100, 1),
        "dns_latency_ms": services.dns_latency_ms,
        "dns_healthy": services.dns_latency_ms < 50.0,
        "gateway_reachable": services.gateway_reachable,
        "wan_reachable": services.wan_reachable,
        "wan_latency_ms": services.wan_latency_ms,
        "eth0_carrier": services.eth0_carrier,
        "eth0_speed_mbps": services.eth0_speed_mbps,
        "conntrack_sessions": services.conntrack_sessions,
        "radius_auth_status": services.radius_auth_status,
    }


def remediate_deauthenticate_client(mac: str, reason: str = "AIOps Triggered Assisted Roam") -> Dict[str, Any]:
    """
    Issues an 802.11v BSS Transition Management frame or deauthentication frame to steer
    a sticky/degraded client towards a closer, higher-performing Access Point radio.
    """
    res = telemetry_client.deauthenticate_client(mac, reason)
    return res.model_dump()


def remediate_change_channel(ap_id: str, band: str, target_channel: int) -> Dict[str, Any]:
    """
    Executes a dynamic channel change on an Access Point radio to relieve severe
    co-channel interference (CCI) or non-Wi-Fi airtime congestion.
    """
    res = telemetry_client.change_channel(ap_id, band, target_channel)
    return res.model_dump()


def remediate_adjust_tx_power(ap_id: str, band: str, power_dbm: int) -> Dict[str, Any]:
    """
    Adjusts the radio transmit power (Tx Power) on an Access Point to optimize cell size
    and eliminate RF coverage holes.
    """
    res = telemetry_client.adjust_tx_power(ap_id, band, power_dbm)
    return res.model_dump()


def remediate_resolve_dhcp_pool() -> Dict[str, Any]:
    """
    Remediates a DHCP scope exhaustion event by purging stale/expired leases
    and re-enabling dynamic IP allocation on the client VLAN.
    """
    res = telemetry_client.resolve_dhcp_pool()
    return res.model_dump()


# Registry of available tools for LLM agent
TOOL_REGISTRY = {
    "list_access_points": list_access_points,
    "get_ap_rf_health": get_ap_rf_health,
    "list_connected_clients": list_connected_clients,
    "get_client_telemetry": get_client_telemetry,
    "check_network_services": check_network_services,
    "remediate_deauthenticate_client": remediate_deauthenticate_client,
    "remediate_change_channel": remediate_change_channel,
    "remediate_adjust_tx_power": remediate_adjust_tx_power,
    "remediate_resolve_dhcp_pool": remediate_resolve_dhcp_pool,
}
