"""
Data models representing Wi-Fi Access Points, Station Clients,
RF telemetry, and Network Core Services.
Supports both Pydantic (when installed) and Python standard library dataclasses.
"""

from enum import Enum
from typing import List, Optional, Dict, Any

try:
    from pydantic import BaseModel, Field

    class BaseSchema(BaseModel):
        pass

except ImportError:
    from dataclasses import dataclass, field, asdict

    def Field(default=None, default_factory=None, description=""):
        if default_factory is not None:
            return field(default_factory=default_factory)
        return field(default=default)

    class BaseSchema:
        def model_dump(self) -> Dict[str, Any]:
            from dataclasses import asdict
            return asdict(self)


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    ASSOCIATING = "ASSOCIATING"
    AUTHENTICATING = "AUTHENTICATING"
    DHCP_PENDING = "DHCP_PENDING"
    DHCP_FAILED = "DHCP_FAILED"
    DISCONNECTED = "DISCONNECTED"


try:
    from pydantic import BaseModel

    class ClientStation(BaseModel):
        mac: str
        ip: Optional[str] = None
        hostname: str = "Unknown Device"
        bssid: str
        ap_name: str
        band: str = "5GHz"
        rssi_dbm: int
        snr_db: int
        tx_bitrate_mbps: float = 300.0
        rx_bitrate_mbps: float = 300.0
        tx_retries_pct: float = 1.2
        connection_state: ConnectionState = ConnectionState.CONNECTED
        roam_count: int = 0
        sticky_client_detected: bool = False
        last_event: str = "NORMAL_OPERATION"
        # Deep Live RF & Traffic Telemetry
        rx_bytes: int = 0
        tx_bytes: int = 0
        tx_failed: int = 0
        inactive_time_ms: int = 0
        connected_time_sec: int = 0
        bitrate_info: str = ""
        signal_chains: List[int] = []
        # Spatial floorplan coordinates (0.0 to 100.0)
        pos_x: float = 50.0
        pos_y: float = 50.0

    class AccessPoint(BaseModel):
        ap_id: str
        name: str
        model: str = "Arooba AP-635 (Wi-Fi 6E)"
        location: str = "Montreal HQ - Floor 3"
        bssid_2g: str = "00:0b:86:11:22:33"
        bssid_5g: str = "00:0b:86:11:22:34"
        channel_2g: int = 6
        channel_5g: int = 36
        tx_power_2g_dbm: int = 15
        tx_power_5g_dbm: int = 18
        channel_utilization_pct: float = 22.0
        noise_floor_dbm: int = -95
        connected_clients: List[str] = []
        # Live Hardware & Radio Parameters
        channel_width_mhz: int = 80
        tx_power_actual_dbm: float = 20.0
        cpu_temp_c: Optional[float] = 48.5
        cpu_load_1m: Optional[float] = 0.25
        band_mode: str = "Dual-Band 2.4/5GHz"
        throughput_mbps: float = 0.0
        # Spatial floorplan coordinates (0.0 to 100.0)
        pos_x: float = 50.0
        pos_y: float = 50.0

    class NetworkServicesStatus(BaseModel):
        dhcp_pool_total: int = 254
        dhcp_pool_used: int = 45
        dhcp_exhausted: bool = False
        dns_latency_ms: float = 8.2
        gateway_reachable: bool = True
        radius_auth_status: str = "HEALTHY"
        # Live Upstream SLA & Network Assurance
        wan_latency_ms: float = 12.5
        wan_reachable: bool = True
        eth0_carrier: bool = True
        eth0_speed_mbps: int = 1000
        conntrack_sessions: int = 14

    class RemediationResult(BaseModel):
        success: bool
        action_type: str
        target: str
        message: str
        details: Dict[str, Any] = {}

    class UxiSensorReport(BaseModel):
        sensor_id: str = "uxi-sensor-01"
        location: str = "Montreal HQ - Floor 2"
        target_ssid: str = "Arooba-Corp-Secure"
        target_bssid: str = "00:0b:86:33:44:02"
        target_ap_name: str = "AP-ConfRoom-B"
        timestamp: str = ""
        overall_sla: str = "PASSED"  # PASSED, DEGRADED, FAILED
        assoc_time_ms: float = 12.4
        auth_8021x_time_ms: float = 24.6
        dhcp_dora_time_ms: float = 38.2
        dns_lookup_time_ms: float = 7.1
        gateway_rtt_ms: float = 1.9
        cloud_app_http_ms: float = 32.4
        dl_throughput_mbps: float = 485.0
        ul_throughput_mbps: float = 310.0
        failing_phase: Optional[str] = None
        error_detail: Optional[str] = None

    class SecurityThreat(BaseModel):
        threat_id: str
        threat_type: str  # EVIL_TWIN_AP, ROGUE_AP, DEAUTH_FLOOD, UNENCRYPTED_HONEYPOT
        severity: str     # CRITICAL, HIGH, MEDIUM
        ssid: str
        bssid: str
        channel: int
        signal_dbm: int
        detecting_ap: str
        description: str
        is_contained: bool = False
        mitigation_action: str = ""

    class AppQoEMetrics(BaseModel):
        mac: str
        hostname: str
        zoom_mos_score: float = 4.4  # 1.0 (Bad) to 5.0 (Excellent)
        zoom_jitter_ms: float = 4.2
        zoom_packet_loss_pct: float = 0.2
        zoom_status: str = "EXCELLENT"  # EXCELLENT, DEGRADED, CRITICAL
        teams_mos_score: float = 4.3
        teams_jitter_ms: float = 5.1
        teams_packet_loss_pct: float = 0.3
        http_ttfb_ms: float = 45.0
        top_app: str = "Zoom Video Conferencing"
        bandwidth_consumed_mb: float = 124.5

    class AirMatchPlan(BaseModel):
        timestamp: str
        optimization_metric: str = "Co-Channel & Adjacent Channel Interference"
        pre_cci_score: float
        post_cci_score: float
        interference_reduction_pct: float
        changes: List[Dict[str, Any]] = []

    class TelemetryAnomaly(BaseModel):
        ap_id: str
        metric_name: str
        current_value: float
        baseline_mean: float
        baseline_std: float
        z_score: float
        is_anomaly: bool
        severity: str
        recommendation: str

except ImportError:
    from dataclasses import dataclass, field, asdict

    @dataclass
    class ClientStation:
        mac: str
        bssid: str
        ap_name: str
        rssi_dbm: int
        snr_db: int
        ip: Optional[str] = None
        hostname: str = "Unknown Device"
        band: str = "5GHz"
        tx_bitrate_mbps: float = 300.0
        rx_bitrate_mbps: float = 300.0
        tx_retries_pct: float = 1.2
        connection_state: ConnectionState = ConnectionState.CONNECTED
        roam_count: int = 0
        sticky_client_detected: bool = False
        last_event: str = "NORMAL_OPERATION"
        rx_bytes: int = 0
        tx_bytes: int = 0
        tx_failed: int = 0
        inactive_time_ms: int = 0
        connected_time_sec: int = 0
        bitrate_info: str = ""
        signal_chains: List[int] = field(default_factory=list)
        pos_x: float = 50.0
        pos_y: float = 50.0

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class AccessPoint:
        ap_id: str
        name: str
        model: str = "Arooba AP-635 (Wi-Fi 6E)"
        location: str = "Montreal HQ - Floor 3"
        bssid_2g: str = "00:0b:86:11:22:33"
        bssid_5g: str = "00:0b:86:11:22:34"
        channel_2g: int = 6
        channel_5g: int = 36
        tx_power_2g_dbm: int = 15
        tx_power_5g_dbm: int = 18
        channel_utilization_pct: float = 22.0
        noise_floor_dbm: int = -95
        connected_clients: List[str] = field(default_factory=list)
        channel_width_mhz: int = 80
        tx_power_actual_dbm: float = 20.0
        cpu_temp_c: Optional[float] = 48.5
        cpu_load_1m: Optional[float] = 0.25
        band_mode: str = "Dual-Band 2.4/5GHz"
        throughput_mbps: float = 0.0
        pos_x: float = 50.0
        pos_y: float = 50.0

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class NetworkServicesStatus:
        dhcp_pool_total: int = 254
        dhcp_pool_used: int = 45
        dhcp_exhausted: bool = False
        dns_latency_ms: float = 8.2
        gateway_reachable: bool = True
        radius_auth_status: str = "HEALTHY"
        wan_latency_ms: float = 12.5
        wan_reachable: bool = True
        eth0_carrier: bool = True
        eth0_speed_mbps: int = 1000
        conntrack_sessions: int = 14

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class RemediationResult:
        success: bool
        action_type: str
        target: str
        message: str
        details: Dict[str, Any] = field(default_factory=dict)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class UxiSensorReport:
        sensor_id: str = "uxi-sensor-01"
        location: str = "Montreal HQ - Floor 2"
        target_ssid: str = "Arooba-Corp-Secure"
        target_bssid: str = "00:0b:86:33:44:02"
        target_ap_name: str = "AP-ConfRoom-B"
        timestamp: str = ""
        overall_sla: str = "PASSED"
        assoc_time_ms: float = 12.4
        auth_8021x_time_ms: float = 24.6
        dhcp_dora_time_ms: float = 38.2
        dns_lookup_time_ms: float = 7.1
        gateway_rtt_ms: float = 1.9
        cloud_app_http_ms: float = 32.4
        dl_throughput_mbps: float = 485.0
        ul_throughput_mbps: float = 310.0
        failing_phase: Optional[str] = None
        error_detail: Optional[str] = None

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class SecurityThreat:
        threat_id: str
        threat_type: str
        severity: str
        ssid: str
        bssid: str
        channel: int
        signal_dbm: int
        detecting_ap: str
        description: str
        is_contained: bool = False
        mitigation_action: str = ""

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class AppQoEMetrics:
        mac: str
        hostname: str
        zoom_mos_score: float = 4.4
        zoom_jitter_ms: float = 4.2
        zoom_packet_loss_pct: float = 0.2
        zoom_status: str = "EXCELLENT"
        teams_mos_score: float = 4.3
        teams_jitter_ms: float = 5.1
        teams_packet_loss_pct: float = 0.3
        http_ttfb_ms: float = 45.0
        top_app: str = "Zoom Video Conferencing"
        bandwidth_consumed_mb: float = 124.5

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class AirMatchPlan:
        timestamp: str
        pre_cci_score: float
        post_cci_score: float
        interference_reduction_pct: float
        optimization_metric: str = "Co-Channel & Adjacent Channel Interference"
        changes: List[Dict[str, Any]] = field(default_factory=list)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class TelemetryAnomaly:
        ap_id: str
        metric_name: str
        current_value: float
        baseline_mean: float
        baseline_std: float
        z_score: float
        is_anomaly: bool
        severity: str
        recommendation: str

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)
