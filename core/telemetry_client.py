"""
Unified Telemetry Client.
Abstracts whether data is fetched from the local in-memory Simulator
or from a physical Raspberry Pi 5 AP over HTTP.
"""

from typing import List, Dict, Any, Optional
import json

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

from core.config import config
from simulator.engine import simulator
from simulator.models import (
    AccessPoint,
    ClientStation,
    ConnectionState,
    NetworkServicesStatus,
    RemediationResult,
)


class TelemetryClient:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or config.TELEMETRY_SOURCE

    def set_mode(self, mode: str):
        self.mode = mode.lower()

    def get_mode(self) -> str:
        return self.mode

    def _http_get(self, path: str) -> Optional[Any]:
        url = f"{config.EDGE_AP_HOST}{path}"
        if HAS_HTTPX:
            with httpx.Client(timeout=config.EDGE_AP_TIMEOUT_SEC) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        else:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=config.EDGE_AP_TIMEOUT_SEC) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode())
            except Exception:
                pass
        return None

    def _http_post(self, path: str, payload: Dict[str, Any]) -> Optional[Any]:
        url = f"{config.EDGE_AP_HOST}{path}"
        if HAS_HTTPX:
            with httpx.Client(timeout=config.EDGE_AP_TIMEOUT_SEC) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
        else:
            try:
                data = json.dumps(payload).encode()
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=config.EDGE_AP_TIMEOUT_SEC) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode())
            except Exception:
                pass
        return None

    # ---------------- AP Telemetry ----------------

    def get_all_aps(self) -> List[AccessPoint]:
        if self.mode == "hardware":
            try:
                data = self._http_get("/api/v1/telemetry/ap")
                if data:
                    return [
                        AccessPoint(
                            ap_id=data.get("ap_id", "pi5-edge-ap"),
                            name=data.get("name", "RaspberryPi-5-Edge-AP"),
                            model=data.get("model", "Raspberry Pi 5 AP"),
                            location="Physical Edge Testbed",
                            channel_2g=data.get("channel", 36),
                            channel_5g=data.get("channel", 36),
                            channel_utilization_pct=data.get("channel_utilization_pct", 15.0),
                            noise_floor_dbm=data.get("noise_floor_dbm", -95),
                        )
                    ]
            except Exception:
                pass
        return simulator.get_all_aps()

    def get_ap(self, ap_id: str) -> Optional[AccessPoint]:
        aps = self.get_all_aps()
        for ap in aps:
            if ap.ap_id.lower() == ap_id.lower() or ap_id.lower() in ap.name.lower():
                return ap
        return None

    # ---------------- Client Telemetry ----------------

    def get_all_clients(self) -> List[ClientStation]:
        if self.mode == "hardware":
            try:
                raw_list = self._http_get("/api/v1/telemetry/clients")
                if raw_list and isinstance(raw_list, list):
                    results = []
                    for item in raw_list:
                        results.append(
                            ClientStation(
                                mac=item["mac"],
                                ip=item.get("ip"),
                                hostname=item.get("hostname", "Unknown Device"),
                                bssid=item.get("bssid", "wlan0"),
                                ap_name=item.get("ap_name", "RaspberryPi-5-Edge-AP"),
                                band=item.get("band", "5GHz"),
                                rssi_dbm=item["rssi_dbm"],
                                snr_db=item.get("snr_db", 35),
                                tx_bitrate_mbps=item.get("tx_bitrate_mbps", 150.0),
                                rx_bitrate_mbps=item.get("rx_bitrate_mbps", 150.0),
                                tx_retries_pct=float(item.get("tx_retries", 0)),
                                sticky_client_detected=item.get("sticky_client_detected", False),
                                connection_state=ConnectionState.CONNECTED,
                            )
                        )
                    return results
            except Exception:
                pass
        return simulator.get_all_clients()

    def get_client(self, identifier: str) -> Optional[ClientStation]:
        clients = self.get_all_clients()
        identifier = identifier.strip().lower()
        for c in clients:
            if c.mac.lower() == identifier or (c.ip and c.ip == identifier) or identifier in c.hostname.lower():
                return c
        return None

    # ---------------- Network Services ----------------

    def get_network_services(self) -> NetworkServicesStatus:
        return simulator.get_network_services()

    # ---------------- Remediation Actions ----------------

    def deauthenticate_client(self, mac: str, reason: str = "AIOps Triggered Roam") -> RemediationResult:
        if self.mode == "hardware":
            try:
                data = self._http_post("/api/v1/actions/deauthenticate", {"mac": mac, "reason": reason})
                if data:
                    return RemediationResult(
                        success=data.get("success", True),
                        action_type="DEAUTHENTICATE",
                        target=mac,
                        message=data.get("message", "Deauthenticated via hostapd_cli."),
                    )
            except Exception as e:
                return RemediationResult(
                    success=False,
                    action_type="DEAUTHENTICATE",
                    target=mac,
                    message=f"Hardware connection failed: {e}",
                )
        return simulator.deauthenticate_client(mac, reason)

    def change_channel(self, ap_id: str, band: str, target_channel: int) -> RemediationResult:
        if self.mode == "hardware":
            try:
                data = self._http_post("/api/v1/actions/channel", {"channel": target_channel, "band": band})
                if data:
                    return RemediationResult(
                        success=data.get("success", True),
                        action_type="CHANGE_CHANNEL",
                        target=str(target_channel),
                        message=data.get("message", "Switched channel via hostapd_cli."),
                    )
            except Exception as e:
                return RemediationResult(
                    success=False,
                    action_type="CHANGE_CHANNEL",
                    target=str(target_channel),
                    message=f"Hardware connection failed: {e}",
                )
        return simulator.change_channel(ap_id, band, target_channel)

    def adjust_tx_power(self, ap_id: str, band: str, power_dbm: int) -> RemediationResult:
        if self.mode == "hardware":
            try:
                data = self._http_post("/api/v1/actions/tx_power", {"tx_power_dbm": power_dbm})
                if data:
                    return RemediationResult(
                        success=data.get("success", True),
                        action_type="ADJUST_TX_POWER",
                        target=f"{power_dbm} dBm",
                        message=data.get("message", "Adjusted Tx power via iw."),
                    )
            except Exception as e:
                return RemediationResult(
                    success=False,
                    action_type="ADJUST_TX_POWER",
                    target=f"{power_dbm} dBm",
                    message=f"Hardware connection failed: {e}",
                )
        return simulator.adjust_tx_power(ap_id, band, power_dbm)

    def resolve_dhcp_pool(self) -> RemediationResult:
        return simulator.resolve_dhcp_pool()


telemetry_client = TelemetryClient()
