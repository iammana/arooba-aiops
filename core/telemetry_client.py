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
    UxiSensorReport,
    SecurityThreat,
    AppQoEMetrics,
    AirMatchPlan,
    TelemetryAnomaly,
)


class TelemetryClient:
    def __init__(self, mode: Optional[str] = None):
        self.mode = (mode or config.TELEMETRY_SOURCE).lower()
        self.edge_host = config.EDGE_AP_HOST.rstrip("/")
        self.last_error: Optional[str] = None
        self._health_cache: Optional[Dict[str, Any]] = None
        self._health_cache_time: float = 0.0

    def set_mode(self, mode: str):
        self.mode = mode.lower()

    def get_mode(self) -> str:
        return self.mode

    def set_edge_host(self, host: str):
        if host:
            self.edge_host = host.rstrip("/")
            self._health_cache = None

    def get_edge_host(self) -> str:
        return self.edge_host

    def check_edge_health(self, timeout: float = 2.0, force: bool = False) -> Dict[str, Any]:
        """
        Pings the Pi 5 Edge AP health endpoint (/health).
        Caches result for 3 seconds to avoid blocking Streamlit reruns.
        """
        import time
        now = time.time()
        if not force and self._health_cache and (now - self._health_cache_time < 3.0):
            return self._health_cache

        data = self._http_get("/health", timeout=timeout)
        if data and isinstance(data, dict) and data.get("status") == "online":
            res = {
                "connected": True,
                "host": self.edge_host,
                "data": data,
                "error": None,
            }
        else:
            res = {
                "connected": False,
                "host": self.edge_host,
                "data": None,
                "error": self.last_error or f"Cannot connect to {self.edge_host}",
            }
        self._health_cache = res
        self._health_cache_time = now
        return res

    def _http_get(self, path: str, timeout: Optional[float] = None) -> Optional[Any]:
        url = f"{self.edge_host}{path}"
        timeout_val = timeout or config.EDGE_AP_TIMEOUT_SEC
        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=timeout_val) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        self.last_error = None
                        return resp.json()
                    self.last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
            except httpx.ConnectError:
                self.last_error = f"Connection refused / unreachable host at {url}"
            except httpx.TimeoutException:
                self.last_error = f"Connection timed out ({timeout_val}s) reaching {url}"
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {str(e)}"
        else:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=timeout_val) as resp:
                    if resp.status == 200:
                        self.last_error = None
                        return json.loads(resp.read().decode())
            except urllib.error.URLError as e:
                self.last_error = f"Network error: {e.reason}"
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {str(e)}"
        return None

    def _http_post(self, path: str, payload: Dict[str, Any], timeout: Optional[float] = None) -> Optional[Any]:
        url = f"{self.edge_host}{path}"
        timeout_val = timeout or config.EDGE_AP_TIMEOUT_SEC
        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=timeout_val) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        self.last_error = None
                        return resp.json()
                    self.last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
            except httpx.ConnectError:
                self.last_error = f"Connection refused / unreachable host at {url}"
            except httpx.TimeoutException:
                self.last_error = f"Connection timed out ({timeout_val}s) reaching {url}"
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {str(e)}"
        else:
            try:
                data = json.dumps(payload).encode()
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=timeout_val) as resp:
                    if resp.status == 200:
                        self.last_error = None
                        return json.loads(resp.read().decode())
            except urllib.error.URLError as e:
                self.last_error = f"Network error: {e.reason}"
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {str(e)}"
        return None

    # ---------------- AP Telemetry ----------------

    def get_all_aps(self) -> List[AccessPoint]:
        if self.mode == "hardware":
            data = self._http_get("/api/v1/telemetry/ap")
            if data and isinstance(data, dict):
                sys_health = data.get("system_health", {})
                channel = data.get("channel", 36)
                band_mode = data.get("band_mode", "5GHz Only (Single-Radio AP)" if channel > 14 else "2.4GHz Only (Single-Radio AP)")
                return [
                    AccessPoint(
                        ap_id=data.get("ap_id", "pi5-edge-ap"),
                        name=data.get("name", "RaspberryPi-5-Edge-AP"),
                        model=data.get("model", "Raspberry Pi 5 AP"),
                        location=data.get("location", "Physical Edge Testbed"),
                        channel_2g=channel if channel <= 14 else 0,
                        channel_5g=channel if channel > 14 else 0,
                        channel_width_mhz=data.get("channel_width_mhz", 80),
                        tx_power_actual_dbm=data.get("tx_power_dbm", 20.0),
                        tx_power_2g_dbm=int(data.get("tx_power_dbm", 15)) if channel <= 14 else 0,
                        tx_power_5g_dbm=int(data.get("tx_power_dbm", 20)) if channel > 14 else 0,
                        channel_utilization_pct=data.get("channel_utilization_pct", 4.2),
                        noise_floor_dbm=data.get("noise_floor_dbm", -95),
                        cpu_temp_c=sys_health.get("cpu_temp_c", 48.5),
                        cpu_load_1m=sys_health.get("cpu_load_1m", 0.25),
                        band_mode=band_mode,
                        throughput_mbps=data.get("throughput_mbps", 0.0),
                    )
                ]
            return []
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
                            rx_bytes=item.get("rx_bytes", 0),
                            tx_bytes=item.get("tx_bytes", 0),
                            tx_failed=item.get("tx_failed", 0),
                            inactive_time_ms=item.get("inactive_time_ms", 0),
                            connected_time_sec=item.get("connected_time_sec", 0),
                            bitrate_info=item.get("bitrate_info", ""),
                            signal_chains=item.get("signal_chains", []),
                        )
                    )
                return results
            return []
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
        if self.mode == "hardware":
            data = self._http_get("/api/v1/telemetry/services")
            if data and isinstance(data, dict):
                return NetworkServicesStatus(
                    dhcp_pool_total=data.get("dhcp_pool_total", 191),
                    dhcp_pool_used=data.get("dhcp_pool_used", 0),
                    dhcp_exhausted=data.get("dhcp_exhausted", False),
                    dns_latency_ms=data.get("dns_latency_ms", 3.5),
                    gateway_reachable=data.get("gateway_reachable", True),
                    radius_auth_status=data.get("radius_auth_status", "N/A (WPA2-PSK)"),
                    wan_reachable=data.get("wan_reachable", True),
                    wan_latency_ms=data.get("wan_latency_ms", 12.0),
                    eth0_carrier=data.get("eth0_carrier", True),
                    eth0_speed_mbps=data.get("eth0_speed_mbps", 1000),
                    conntrack_sessions=data.get("conntrack_sessions", 0),
                )
            health = self.check_edge_health(timeout=1.0)
            is_online = health.get("connected", False)
            return NetworkServicesStatus(
                dhcp_pool_total=191,
                dhcp_pool_used=0,
                dhcp_exhausted=False,
                dns_latency_ms=3.5 if is_online else 0.0,
                gateway_reachable=is_online,
                radius_auth_status="N/A (WPA2-PSK)",
                wan_reachable=is_online,
                wan_latency_ms=12.0 if is_online else 0.0,
                eth0_carrier=is_online,
                eth0_speed_mbps=1000 if is_online else 0,
                conntrack_sessions=0,
            )
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
            return RemediationResult(
                success=False,
                action_type="DEAUTHENTICATE",
                target=mac,
                message=f"Hardware connection failed: {self.last_error}",
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
            return RemediationResult(
                success=False,
                action_type="CHANGE_CHANNEL",
                target=str(target_channel),
                message=f"Hardware connection failed: {self.last_error}",
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
            return RemediationResult(
                success=False,
                action_type="ADJUST_TX_POWER",
                target=f"{power_dbm} dBm",
                message=f"Hardware connection failed: {self.last_error}",
            )
        return simulator.adjust_tx_power(ap_id, band, power_dbm)

    def resolve_dhcp_pool(self) -> RemediationResult:
        if self.mode == "hardware":
            try:
                data = self._http_post("/api/v1/actions/dhcp_resolve", {})
                if data:
                    return RemediationResult(
                        success=data.get("success", True),
                        action_type="DHCP_REMEDIATION",
                        target="dnsmasq leases",
                        message=data.get("message", "Flushed DHCP leases and reloaded dnsmasq on Pi 5."),
                    )
            except Exception as e:
                return RemediationResult(
                    success=False,
                    action_type="DHCP_REMEDIATION",
                    target="dnsmasq leases",
                    message=f"Hardware connection failed: {e}",
                )
            return RemediationResult(
                success=False,
                action_type="DHCP_REMEDIATION",
                target="dnsmasq leases",
                message=f"Hardware connection failed: {self.last_error}",
            )
        return simulator.resolve_dhcp_pool()

    # ---------------- Advanced Enterprise Capabilities ----------------

    def optimize_campus_rf_plan(self) -> AirMatchPlan:
        """Runs the AirMatch dynamic RF optimization engine."""
        return simulator.optimize_campus_rf_plan()

    def run_synthetic_uxi_test(self, target_ap_id: Optional[str] = None) -> UxiSensorReport:
        """Runs an autonomous synthetic UXI client journey probe."""
        return simulator.run_synthetic_uxi_test(target_ap_id)

    def get_uxi_sensor_status(self) -> UxiSensorReport:
        """Returns the latest synthetic UXI probe status."""
        return simulator.get_uxi_sensor_status()

    def scan_wids_security_threats(self) -> List[SecurityThreat]:
        """Scans for rogue APs, evil twins, and wireless threats."""
        return simulator.scan_wids_security_threats()

    def contain_rogue_ap(self, bssid: str) -> RemediationResult:
        """Suppresses rogue AP through airtime containment."""
        return simulator.contain_rogue_ap(bssid)

    def get_application_qoe(self, identifier: str) -> Optional[AppQoEMetrics]:
        """Retrieves Layer-7 application quality metrics (Zoom MOS, jitter, packet loss)."""
        return simulator.get_application_qoe(identifier)

    def get_all_app_qoe(self) -> List[AppQoEMetrics]:
        """Retrieves application QoE metrics for all active clients."""
        return simulator.get_all_app_qoe()

    def get_baseline_anomalies(self, ap_id: Optional[str] = None) -> List[TelemetryAnomaly]:
        """Calculates Z-score statistical anomalies against 7-day baselines."""
        return simulator.get_baseline_anomalies(ap_id)


telemetry_client = TelemetryClient()
