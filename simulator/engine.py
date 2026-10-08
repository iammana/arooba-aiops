"""
Simulation Engine for Arooba-AIOps.
Maintains state for simulated Access Points, Clients, Network Services,
Synthetic UXI Probes, WIDS Security Threats, and Application QoE metrics.
Supports enterprise Wi-Fi troubleshooting and self-healing scenarios.
"""

import datetime
from typing import Dict, List, Optional, Any
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


class SimulatorEngine:
    def __init__(self):
        self.aps: Dict[str, AccessPoint] = {}
        self.clients: Dict[str, ClientStation] = {}
        self.services: NetworkServicesStatus = NetworkServicesStatus()
        self.threats: Dict[str, SecurityThreat] = {}
        self.uxi_reports: List[UxiSensorReport] = []
        self.app_qoe: Dict[str, AppQoEMetrics] = {}
        self.rf_plan_history: List[AirMatchPlan] = []
        self.current_scenario: str = "baseline"
        self.load_scenario("baseline")

    def load_scenario(self, scenario_name: str) -> str:
        """Loads a pre-canned enterprise Wi-Fi scenario."""
        self.current_scenario = scenario_name

        if scenario_name == "baseline":
            self._setup_baseline()
            return "Loaded baseline: Healthy multi-AP campus network with optimal RF plan."
        elif scenario_name == "sticky_client":
            self._setup_sticky_client()
            return "Loaded scenario: Sticky Client roaming failure in Conference Room B."
        elif scenario_name == "channel_congestion":
            self._setup_channel_congestion()
            return "Loaded scenario: High Co-Channel Interference (CCI) on 2.4 GHz radio."
        elif scenario_name == "dhcp_exhaustion":
            self._setup_dhcp_exhaustion()
            return "Loaded scenario: DHCP lease pool exhaustion on guest/client VLAN."
        elif scenario_name == "evil_twin_attack":
            self._setup_evil_twin_attack()
            return "Loaded scenario: Rogue AP / Evil Twin attack broadcasting corporate SSID."
        elif scenario_name == "zoom_audio_jitter":
            self._setup_zoom_audio_jitter()
            return "Loaded scenario: Unified Communications (Zoom) degraded by RF packet retries."
        elif scenario_name == "campus_rf_conflict":
            self._setup_campus_rf_conflict()
            return "Loaded scenario: Campus-wide RF channel conflict requiring AirMatch optimization."
        else:
            self._setup_baseline()
            return f"Unknown scenario '{scenario_name}'. Loaded baseline instead."

    def _setup_baseline(self):
        self.aps = {
            "ap-lobby": AccessPoint(
                ap_id="ap-lobby",
                name="AP-Lobby-Main",
                model="Arooba AP-635 (Wi-Fi 6E)",
                location="Montreal HQ - Ground Lobby",
                bssid_2g="00:0b:86:11:22:01",
                bssid_5g="00:0b:86:11:22:02",
                channel_2g=1,
                channel_5g=36,
                channel_utilization_pct=18.5,
                noise_floor_dbm=-96,
                connected_clients=["a4:83:e7:10:00:01", "3c:22:fb:44:00:02"],
                pos_x=18.0,
                pos_y=75.0,
            ),
            "ap-conf-b": AccessPoint(
                ap_id="ap-conf-b",
                name="AP-ConfRoom-B",
                model="Arooba AP-635 (Wi-Fi 6E)",
                location="Montreal HQ - Floor 2 - Conf Room B",
                bssid_2g="00:0b:86:33:44:01",
                bssid_5g="00:0b:86:33:44:02",
                channel_2g=6,
                channel_5g=149,
                channel_utilization_pct=24.0,
                noise_floor_dbm=-95,
                connected_clients=["f8:ff:c2:55:00:03"],
                pos_x=50.0,
                pos_y=22.0,
            ),
            "ap-eng-floor": AccessPoint(
                ap_id="ap-eng-floor",
                name="AP-Engineering-Lab",
                model="Arooba AP-655 (Wi-Fi 6E High-Density)",
                location="Montreal HQ - Floor 3 - Engineering",
                bssid_2g="00:0b:86:55:66:01",
                bssid_5g="00:0b:86:55:66:02",
                channel_2g=11,
                channel_5g=44,
                channel_utilization_pct=29.2,
                noise_floor_dbm=-94,
                connected_clients=["70:3a:cb:77:00:04", "88:66:5a:88:00:05"],
                pos_x=80.0,
                pos_y=55.0,
            ),
        }

        self.clients = {
            "a4:83:e7:10:00:01": ClientStation(
                mac="a4:83:e7:10:00:01",
                ip="10.20.1.101",
                hostname="MacBookPro-Sales",
                bssid="00:0b:86:11:22:02",
                ap_name="AP-Lobby-Main",
                band="5GHz",
                rssi_dbm=-52,
                snr_db=44,
                tx_bitrate_mbps=866.7,
                rx_bitrate_mbps=866.7,
                tx_retries_pct=1.0,
                connection_state=ConnectionState.CONNECTED,
                pos_x=10.0,
                pos_y=85.0,
            ),
            "3c:22:fb:44:00:02": ClientStation(
                mac="3c:22:fb:44:00:02",
                ip="10.20.1.102",
                hostname="iPhone-15-Guest",
                bssid="00:0b:86:11:22:02",
                band="5GHz",
                ap_name="AP-Lobby-Main",
                rssi_dbm=-58,
                snr_db=38,
                tx_bitrate_mbps=540.0,
                rx_bitrate_mbps=540.0,
                tx_retries_pct=2.1,
                connection_state=ConnectionState.CONNECTED,
                pos_x=26.0,
                pos_y=85.0,
            ),
            "f8:ff:c2:55:00:03": ClientStation(
                mac="f8:ff:c2:55:00:03",
                ip="10.20.1.103",
                hostname="Dell-Latitude-Dev",
                bssid="00:0b:86:33:44:02",
                ap_name="AP-ConfRoom-B",
                band="5GHz",
                rssi_dbm=-48,
                snr_db=47,
                tx_bitrate_mbps=1201.0,
                rx_bitrate_mbps=1201.0,
                tx_retries_pct=0.8,
                connection_state=ConnectionState.CONNECTED,
                pos_x=40.0,
                pos_y=35.0,
            ),
            "70:3a:cb:77:00:04": ClientStation(
                mac="70:3a:cb:77:00:04",
                ip="10.20.1.104",
                hostname="iPad-Pro-Design",
                bssid="00:0b:86:55:66:02",
                ap_name="AP-Engineering-Lab",
                band="5GHz",
                rssi_dbm=-50,
                snr_db=44,
                tx_bitrate_mbps=866.7,
                rx_bitrate_mbps=866.7,
                tx_retries_pct=1.4,
                connection_state=ConnectionState.CONNECTED,
                pos_x=73.0,
                pos_y=35.0,
            ),
            "88:66:5a:88:00:05": ClientStation(
                mac="88:66:5a:88:00:05",
                ip="10.20.1.105",
                hostname="Pixel-8-QA",
                bssid="00:0b:86:55:66:02",
                ap_name="AP-Engineering-Lab",
                band="5GHz",
                rssi_dbm=-55,
                snr_db=39,
                tx_bitrate_mbps=720.0,
                rx_bitrate_mbps=720.0,
                tx_retries_pct=1.9,
                connection_state=ConnectionState.CONNECTED,
                pos_x=85.0,
                pos_y=75.0,
            ),
        }

        self.services = NetworkServicesStatus(
            dhcp_pool_total=254,
            dhcp_pool_used=45,
            dhcp_exhausted=False,
            dns_latency_ms=8.2,
            gateway_reachable=True,
            radius_auth_status="HEALTHY",
        )

        self.threats = {}

        # Default App QoE entries
        self.app_qoe = {
            mac: AppQoEMetrics(
                mac=c.mac,
                hostname=c.hostname,
                zoom_mos_score=4.4,
                zoom_jitter_ms=4.1,
                zoom_packet_loss_pct=0.2,
                zoom_status="EXCELLENT",
                teams_mos_score=4.3,
                teams_jitter_ms=5.0,
                teams_packet_loss_pct=0.3,
                http_ttfb_ms=42.0,
                top_app="Zoom Video Conferencing",
                bandwidth_consumed_mb=145.2,
            )
            for mac, c in self.clients.items()
        }

        # Initial baseline synthetic UXI probe
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.uxi_reports = [
            UxiSensorReport(
                sensor_id="uxi-sensor-01",
                location="Montreal HQ - Floor 2 - Conf Room B",
                target_ssid="Arooba-Corp-Secure",
                target_bssid="00:0b:86:33:44:02",
                target_ap_name="AP-ConfRoom-B",
                timestamp=now_ts,
                overall_sla="PASSED",
                assoc_time_ms=11.8,
                auth_8021x_time_ms=23.4,
                dhcp_dora_time_ms=36.1,
                dns_lookup_time_ms=6.8,
                gateway_rtt_ms=1.8,
                cloud_app_http_ms=29.5,
                dl_throughput_mbps=512.0,
                ul_throughput_mbps=340.0,
            )
        ]

    def _setup_sticky_client(self):
        """Simulates sticky client syndrome: laptop walked to Conf Room B but stuck to distant Lobby AP."""
        self._setup_baseline()
        troubled_mac = "f8:ff:c2:55:00:03"
        self.clients[troubled_mac] = ClientStation(
            mac=troubled_mac,
            ip="10.20.1.103",
            hostname="MacBook-Exec-Zoom",
            bssid="00:0b:86:11:22:01",  # Connected to distant Lobby 2.4GHz!
            ap_name="AP-Lobby-Main",
            band="2.4GHz",
            rssi_dbm=-83,               # Highly degraded signal
            snr_db=11,
            tx_bitrate_mbps=28.0,       # Dropped to low PHY rate
            rx_bitrate_mbps=18.0,
            tx_retries_pct=34.8,        # Severe packet retransmission
            connection_state=ConnectionState.CONNECTED,
            sticky_client_detected=True,
            last_event="ROAM_TIMEOUT: User walked past AP-ConfRoom-B (-46 dBm) without 802.11k/v trigger",
            pos_x=40.0,                 # Physically located in Conf Room B
            pos_y=35.0,
        )
        if troubled_mac in self.aps["ap-conf-b"].connected_clients:
            self.aps["ap-conf-b"].connected_clients.remove(troubled_mac)
        if troubled_mac not in self.aps["ap-lobby"].connected_clients:
            self.aps["ap-lobby"].connected_clients.append(troubled_mac)

        # Degrade Zoom QoE for this client due to poor RF
        self.app_qoe[troubled_mac] = AppQoEMetrics(
            mac=troubled_mac,
            hostname="MacBook-Exec-Zoom",
            zoom_mos_score=2.2,
            zoom_jitter_ms=58.2,
            zoom_packet_loss_pct=14.5,
            zoom_status="CRITICAL",
            teams_mos_score=2.3,
            teams_jitter_ms=54.0,
            teams_packet_loss_pct=13.8,
            http_ttfb_ms=210.0,
            top_app="Zoom Video Conferencing",
            bandwidth_consumed_mb=56.0,
        )

    def _setup_channel_congestion(self):
        """Simulates high channel utilization (airtime choke) on AP-ConfRoom-B."""
        self._setup_baseline()
        self.aps["ap-conf-b"].channel_utilization_pct = 91.4
        self.aps["ap-conf-b"].noise_floor_dbm = -78  # High RF noise floor
        client = self.clients["f8:ff:c2:55:00:03"]
        client.tx_retries_pct = 28.5
        client.last_event = "HIGH_AIRTIME_UTILIZATION: 91.4% busy airtime on channel 6"

        self.app_qoe["f8:ff:c2:55:00:03"] = AppQoEMetrics(
            mac="f8:ff:c2:55:00:03",
            hostname=client.hostname,
            zoom_mos_score=2.6,
            zoom_jitter_ms=44.1,
            zoom_packet_loss_pct=8.9,
            zoom_status="DEGRADED",
            teams_mos_score=2.7,
            teams_jitter_ms=42.0,
            teams_packet_loss_pct=8.1,
            http_ttfb_ms=165.0,
            top_app="Zoom Video Conferencing",
            bandwidth_consumed_mb=92.0,
        )

    def _setup_dhcp_exhaustion(self):
        """Simulates VLAN DHCP exhaustion: Wi-Fi associates fine, but IP cannot be acquired."""
        self._setup_baseline()
        self.services.dhcp_pool_used = 254
        self.services.dhcp_exhausted = True

        new_mac = "ee:11:22:33:44:55"
        self.clients[new_mac] = ClientStation(
            mac=new_mac,
            ip=None,
            hostname="ThinkPad-NewVisitor",
            bssid="00:0b:86:33:44:02",
            ap_name="AP-ConfRoom-B",
            band="5GHz",
            rssi_dbm=-51,
            snr_db=44,
            tx_bitrate_mbps=866.7,
            rx_bitrate_mbps=866.7,
            tx_retries_pct=1.2,
            connection_state=ConnectionState.DHCP_FAILED,
            last_event="DHCP_DISCOVER_TIMEOUT: 4 attempts sent, 0 DHCP_OFFER received from gateway",
            pos_x=54.0,
            pos_y=32.0,
        )
        self.aps["ap-conf-b"].connected_clients.append(new_mac)

        # UXI sensor in Conf Room B also fails DHCP probe
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.uxi_reports.insert(0, UxiSensorReport(
            sensor_id="uxi-sensor-01",
            location="Montreal HQ - Floor 2 - Conf Room B",
            target_ssid="Arooba-Corp-Secure",
            target_bssid="00:0b:86:33:44:02",
            target_ap_name="AP-ConfRoom-B",
            timestamp=now_ts,
            overall_sla="FAILED",
            assoc_time_ms=12.1,
            auth_8021x_time_ms=22.8,
            dhcp_dora_time_ms=8000.0,
            dns_lookup_time_ms=0.0,
            gateway_rtt_ms=0.0,
            cloud_app_http_ms=0.0,
            dl_throughput_mbps=0.0,
            ul_throughput_mbps=0.0,
            failing_phase="DHCP_DORA",
            error_detail="DHCP_DISCOVER_TIMEOUT: No DHCP_OFFER received. Scope is 100% full.",
        ))

    def _setup_evil_twin_attack(self):
        """Simulates Rogue AP / Evil Twin attack: unauthorized AP spoofing corporate SSID."""
        self._setup_baseline()
        rogue_bssid = "de:ad:be:ef:00:99"
        self.threats[rogue_bssid] = SecurityThreat(
            threat_id="threat-wids-001",
            threat_type="EVIL_TWIN_AP",
            severity="CRITICAL",
            ssid="Arooba-Corp-Secure",
            bssid=rogue_bssid,
            channel=6,
            signal_dbm=-44,
            detecting_ap="AP-ConfRoom-B",
            description="Unauthorized BSSID broadcasting corporate SSID without 802.1X certificate validation. Suspected Man-in-the-Middle credential harvester.",
            is_contained=False,
            mitigation_action="Targeted 802.11 Deauth airtime containment recommended.",
        )

    def _setup_zoom_audio_jitter(self):
        """Simulates critical Zoom meeting degradation with audio cutouts and packet drops."""
        self._setup_baseline()
        troubled_mac = "f8:ff:c2:55:00:03"
        client = self.clients[troubled_mac]
        client.tx_retries_pct = 22.4
        client.last_event = "UCC_QUALITY_DEGRADED: High jitter buffer overrun on UDP port 8801"

        self.app_qoe[troubled_mac] = AppQoEMetrics(
            mac=troubled_mac,
            hostname=client.hostname,
            zoom_mos_score=2.1,
            zoom_jitter_ms=64.8,
            zoom_packet_loss_pct=15.2,
            zoom_status="CRITICAL",
            teams_mos_score=2.2,
            teams_jitter_ms=60.1,
            teams_packet_loss_pct=14.0,
            http_ttfb_ms=240.0,
            top_app="Zoom Video Conferencing (Active Call)",
            bandwidth_consumed_mb=85.0,
        )

    def _setup_campus_rf_conflict(self):
        """Simulates all campus APs overlapping on same channels, generating Co-Channel Interference."""
        self._setup_baseline()
        for ap in self.aps.values():
            ap.channel_2g = 6
            ap.channel_5g = 36
            ap.tx_power_2g_dbm = 23  # Max power causing cell spillover
            ap.tx_power_5g_dbm = 23
            ap.channel_utilization_pct = 74.5
            ap.noise_floor_dbm = -82

        for c in self.clients.values():
            c.tx_retries_pct = 19.8

    # ---------------- Telemetry Accessors ----------------

    def get_all_aps(self) -> List[AccessPoint]:
        return list(self.aps.values())

    def get_ap(self, ap_id: str) -> Optional[AccessPoint]:
        return self.aps.get(ap_id)

    def get_all_clients(self) -> List[ClientStation]:
        return list(self.clients.values())

    def get_client(self, identifier: str) -> Optional[ClientStation]:
        identifier = identifier.strip().lower()
        for c in self.clients.values():
            if c.mac.lower() == identifier or (c.ip and c.ip == identifier) or identifier in c.hostname.lower():
                return c
        return None

    def get_network_services(self) -> NetworkServicesStatus:
        return self.services

    # ---------------- Aruba-Competitive Advanced Features ----------------

    def optimize_campus_rf_plan(self) -> AirMatchPlan:
        """
        Algorithmic RF Plan Optimizer (Competes with Aruba AirMatch).
        Uses a graph-coloring interference minimizer to assign non-overlapping
        channels and auto-tune transmit power across all APs in the campus topology.
        """
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Compute pre-optimization Co-Channel Interference (CCI) score
        pre_cci = 0.0
        ap_list = list(self.aps.values())
        for i in range(len(ap_list)):
            for j in range(i + 1, len(ap_list)):
                ap1, ap2 = ap_list[i], ap_list[j]
                if ap1.channel_2g == ap2.channel_2g:
                    pre_cci += 35.0
                if ap1.channel_5g == ap2.channel_5g:
                    pre_cci += 45.0

        # 2. Assign non-overlapping channel pool (Graph Coloring)
        # 2.4 GHz non-overlapping channels: 1, 6, 11
        # 5 GHz clean UNII channels: 36, 44, 149, 157
        channel_2g_pool = [1, 6, 11]
        channel_5g_pool = [36, 149, 44, 157]

        changes: List[Dict[str, Any]] = []
        for idx, ap in enumerate(ap_list):
            new_2g = channel_2g_pool[idx % len(channel_2g_pool)]
            new_5g = channel_5g_pool[idx % len(channel_5g_pool)]
            new_tx_2g = 14  # Balanced power prevents 2.4GHz bleeds
            new_tx_5g = 18

            old_2g, old_5g = ap.channel_2g, ap.channel_5g
            old_tx_2g, old_tx_5g = ap.tx_power_2g_dbm, ap.tx_power_5g_dbm

            ap.channel_2g = new_2g
            ap.channel_5g = new_5g
            ap.tx_power_2g_dbm = new_tx_2g
            ap.tx_power_5g_dbm = new_tx_5g
            ap.channel_utilization_pct = max(16.0, round(ap.channel_utilization_pct * 0.42, 1))
            ap.noise_floor_dbm = -95

            changes.append({
                "ap_id": ap.ap_id,
                "ap_name": ap.name,
                "channel_2g": f"{old_2g} -> {new_2g}",
                "channel_5g": f"{old_5g} -> {new_5g}",
                "tx_power_2g": f"{old_tx_2g} -> {new_tx_2g} dBm",
                "tx_power_5g": f"{old_tx_5g} -> {new_tx_5g} dBm",
                "utilization_pct": f"{ap.channel_utilization_pct}%",
            })

        # Post-CCI is minimized to 0.0 because channels are completely orthogonal
        post_cci = 0.0
        reduction_pct = 100.0 if pre_cci > 0 else 0.0

        plan = AirMatchPlan(
            timestamp=now_ts,
            optimization_metric="Co-Channel & Adjacent Channel Interference",
            pre_cci_score=pre_cci,
            post_cci_score=post_cci,
            interference_reduction_pct=reduction_pct,
            changes=changes,
        )
        self.rf_plan_history.insert(0, plan)

        # Normalize client retries if caused by RF conflict
        for c in self.clients.values():
            if c.tx_retries_pct > 15.0 and not c.sticky_client_detected:
                c.tx_retries_pct = 1.2
                c.last_event = "REMEDIATED: AirMatch RF plan optimized channels and power."

        return plan

    def run_synthetic_uxi_test(self, target_ap_id: Optional[str] = None) -> UxiSensorReport:
        """
        Runs synthetic client journey probe across link phases (Competes with Aruba UXI).
        Tests: Association -> 802.1X -> DHCP DORA -> DNS -> Gateway Ping -> Cloud HTTP -> Throughput.
        """
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_ap = self.aps.get(target_ap_id or "ap-conf-b") or list(self.aps.values())[0]

        # Case 1: DHCP failure
        if self.services.dhcp_exhausted:
            report = UxiSensorReport(
                sensor_id="uxi-sensor-01",
                location="Montreal HQ - Floor 2 - Conf Room B",
                target_ssid="Arooba-Corp-Secure",
                target_bssid=target_ap.bssid_5g,
                target_ap_name=target_ap.name,
                timestamp=now_ts,
                overall_sla="FAILED",
                assoc_time_ms=12.4,
                auth_8021x_time_ms=23.1,
                dhcp_dora_time_ms=8000.0,
                dns_lookup_time_ms=0.0,
                gateway_rtt_ms=0.0,
                cloud_app_http_ms=0.0,
                dl_throughput_mbps=0.0,
                ul_throughput_mbps=0.0,
                failing_phase="DHCP_DORA",
                error_detail="DHCP_DISCOVER_TIMEOUT: VLAN scope is 100% exhausted. 0 IP leases available.",
            )
        # Case 2: Congested AP
        elif target_ap.channel_utilization_pct > 70.0:
            report = UxiSensorReport(
                sensor_id="uxi-sensor-01",
                location="Montreal HQ - Floor 2 - Conf Room B",
                target_ssid="Arooba-Corp-Secure",
                target_bssid=target_ap.bssid_5g,
                target_ap_name=target_ap.name,
                timestamp=now_ts,
                overall_sla="DEGRADED",
                assoc_time_ms=28.5,
                auth_8021x_time_ms=45.2,
                dhcp_dora_time_ms=78.4,
                dns_lookup_time_ms=34.2,
                gateway_rtt_ms=18.5,
                cloud_app_http_ms=142.0,
                dl_throughput_mbps=85.0,
                ul_throughput_mbps=42.0,
                failing_phase="AIRTIME_CONGESTION",
                error_detail=f"High channel utilization ({target_ap.channel_utilization_pct}%). Frame delay exceeds 100ms SLA.",
            )
        # Case 3: Healthy SLA
        else:
            report = UxiSensorReport(
                sensor_id="uxi-sensor-01",
                location="Montreal HQ - Floor 2 - Conf Room B",
                target_ssid="Arooba-Corp-Secure",
                target_bssid=target_ap.bssid_5g,
                target_ap_name=target_ap.name,
                timestamp=now_ts,
                overall_sla="PASSED",
                assoc_time_ms=11.2,
                auth_8021x_time_ms=22.4,
                dhcp_dora_time_ms=34.8,
                dns_lookup_time_ms=6.2,
                gateway_rtt_ms=1.7,
                cloud_app_http_ms=28.6,
                dl_throughput_mbps=520.0,
                ul_throughput_mbps=345.0,
                failing_phase=None,
                error_detail=None,
            )

        self.uxi_reports.insert(0, report)
        return report

    def get_uxi_sensor_status(self) -> UxiSensorReport:
        if not self.uxi_reports:
            return self.run_synthetic_uxi_test()
        return self.uxi_reports[0]

    def scan_wids_security_threats(self) -> List[SecurityThreat]:
        """
        WIDS / WIPS Rogue AP & Threat Scanner (Competes with Aruba RFProtect).
        Scans for rogue BSSIDs, evil twins, and deauth floods.
        """
        return list(self.threats.values())

    def contain_rogue_ap(self, bssid: str) -> RemediationResult:
        """
        WIPS Automated Airtime Containment: sends targeted 802.11 deauth suppression frames
        to block rogue AP association without disrupting neighboring authorized APs.
        """
        threat = self.threats.get(bssid)
        if not threat:
            # Check if matching partial BSSID
            for t in self.threats.values():
                if bssid.lower() in t.bssid.lower():
                    threat = t
                    break

        if not threat:
            return RemediationResult(
                success=False,
                action_type="WIPS_CONTAINMENT",
                target=bssid,
                message=f"Threat BSSID {bssid} not found in active WIDS threat table.",
            )

        threat.is_contained = True
        threat.mitigation_action = "ACTIVE: Transmitting 802.11 deauth containment frames on channel."

        return RemediationResult(
            success=True,
            action_type="WIPS_CONTAINMENT",
            target=threat.bssid,
            message=f"Successfully contained Rogue AP ({threat.ssid} - {threat.bssid}). Airtime containment active.",
            details={"threat_type": threat.threat_type, "bssid": threat.bssid, "detecting_ap": threat.detecting_ap},
        )

    def get_application_qoe(self, identifier: str) -> Optional[AppQoEMetrics]:
        """
        Application Quality of Experience (QoE / UCC) Telemetry (Competes with Aruba AppRF / UCC).
        Returns Mean Opinion Score (MOS), jitter, and packet loss for Zoom & Teams.
        """
        client = self.get_client(identifier)
        if not client:
            return None

        # Return cached or compute dynamically based on RF state
        qoe = self.app_qoe.get(client.mac)
        if not qoe:
            is_degraded = client.tx_retries_pct > 15.0 or client.rssi_dbm < -75
            mos = 2.3 if is_degraded else 4.4
            qoe = AppQoEMetrics(
                mac=client.mac,
                hostname=client.hostname,
                zoom_mos_score=mos,
                zoom_jitter_ms=52.0 if is_degraded else 4.5,
                zoom_packet_loss_pct=12.0 if is_degraded else 0.2,
                zoom_status="CRITICAL" if is_degraded else "EXCELLENT",
                teams_mos_score=mos + 0.1,
                teams_jitter_ms=48.0 if is_degraded else 5.2,
                teams_packet_loss_pct=11.0 if is_degraded else 0.3,
                http_ttfb_ms=195.0 if is_degraded else 42.0,
                top_app="Zoom Video Conferencing",
                bandwidth_consumed_mb=110.0,
            )
            self.app_qoe[client.mac] = qoe
        return qoe

    def get_all_app_qoe(self) -> List[AppQoEMetrics]:
        return [self.get_application_qoe(mac) for mac in self.clients.keys() if self.get_application_qoe(mac)]

    def get_baseline_anomalies(self, ap_id: Optional[str] = None) -> List[TelemetryAnomaly]:
        """
        Telemetry Baseline & Anomaly Detection (Competes with Aruba Central AI Insights).
        Computes Z-scores (Z = (X - mean) / std) across airtime utilization and frame retry rates.
        """
        anomalies: List[TelemetryAnomaly] = []
        aps_to_check = [self.aps[ap_id]] if (ap_id and ap_id in self.aps) else list(self.aps.values())

        # Baseline model for enterprise campus:
        # Expected airtime utilization: mean = 22.0%, std = 7.0%
        # Expected frame retry rate: mean = 2.0%, std = 1.2%
        base_util_mean = 22.0
        base_util_std = 7.0

        for ap in aps_to_check:
            val = ap.channel_utilization_pct
            z_score = round((val - base_util_mean) / base_util_std, 2)
            is_anomaly = abs(z_score) >= 2.5

            if is_anomaly:
                severity = "CRITICAL" if z_score > 4.0 else "WARNING"
                anomalies.append(TelemetryAnomaly(
                    ap_id=ap.ap_id,
                    metric_name="channel_utilization_pct",
                    current_value=val,
                    baseline_mean=base_util_mean,
                    baseline_std=base_util_std,
                    z_score=z_score,
                    is_anomaly=True,
                    severity=severity,
                    recommendation=f"Airtime is {z_score}σ above 7-day baseline ({val}% vs expected {base_util_mean}%). Run AirMatch dynamic channel optimization.",
                ))

        # Check clients for retry rate anomalies
        base_retry_mean = 2.0
        base_retry_std = 1.2
        for c in self.clients.values():
            r_val = c.tx_retries_pct
            r_z = round((r_val - base_retry_mean) / base_retry_std, 2)
            if r_z >= 3.0:
                anomalies.append(TelemetryAnomaly(
                    ap_id=c.ap_name,
                    metric_name=f"client_tx_retries ({c.hostname})",
                    current_value=r_val,
                    baseline_mean=base_retry_mean,
                    baseline_std=base_retry_std,
                    z_score=r_z,
                    is_anomaly=True,
                    severity="CRITICAL" if r_z > 5.0 else "WARNING",
                    recommendation=f"Client retry rate {r_val}% is {r_z}σ above norm. Check for sticky client roaming or CCI.",
                ))

        return anomalies

    # ---------------- Remediation Actions ----------------

    def deauthenticate_client(self, mac: str, reason: str = "AIOps Assisted Roam") -> RemediationResult:
        client = self.get_client(mac)
        if not client:
            return RemediationResult(
                success=False,
                action_type="DEAUTHENTICATE",
                target=mac,
                message=f"Client with MAC {mac} not found in active station table."
            )

        # Simulate assisted roam to the best nearby AP (e.g. AP-ConfRoom-B on 5GHz)
        target_ap = self.aps.get("ap-conf-b")
        if target_ap:
            client.bssid = target_ap.bssid_5g
            client.ap_name = target_ap.name
            client.band = "5GHz"
            client.rssi_dbm = -47
            client.snr_db = 48
            client.tx_bitrate_mbps = 1201.0
            client.rx_bitrate_mbps = 1201.0
            client.tx_retries_pct = 1.1
            client.sticky_client_detected = False
            client.roam_count += 1
            client.last_event = f"REMEDIATED: 802.11v/BSS Transition executed. Reassociated to {target_ap.name}"

            # Restore Zoom QoE if previously degraded
            if client.mac in self.app_qoe:
                qoe = self.app_qoe[client.mac]
                qoe.zoom_mos_score = 4.4
                qoe.zoom_jitter_ms = 4.2
                qoe.zoom_packet_loss_pct = 0.2
                qoe.zoom_status = "EXCELLENT"

        return RemediationResult(
            success=True,
            action_type="DEAUTHENTICATE",
            target=mac,
            message=f"Successfully issued 802.11v BSS Transition frame to {mac}. Reason: {reason}. Client successfully steered to {client.ap_name} (-47 dBm).",
            details={"new_ap": client.ap_name, "new_rssi": client.rssi_dbm, "band": client.band}
        )

    def change_channel(self, ap_id: str, band: str, target_channel: int) -> RemediationResult:
        ap = self.aps.get(ap_id)
        if not ap:
            return RemediationResult(
                success=False,
                action_type="CHANGE_CHANNEL",
                target=ap_id,
                message=f"Access Point {ap_id} not found."
            )

        old_channel = ap.channel_2g if "2" in band else ap.channel_5g
        if "2" in band:
            ap.channel_2g = target_channel
        else:
            ap.channel_5g = target_channel

        # Clear interference on successful channel change
        ap.channel_utilization_pct = 21.5
        ap.noise_floor_dbm = -95

        # Normalize associated clients
        for c in self.clients.values():
            if c.ap_name == ap.name and not c.sticky_client_detected:
                c.tx_retries_pct = 1.2
                c.last_event = f"REMEDIATED: Switched to clean channel {target_channel} on {ap.name}."
                if c.mac in self.app_qoe:
                    self.app_qoe[c.mac].zoom_status = "EXCELLENT"
                    self.app_qoe[c.mac].zoom_mos_score = 4.4

        return RemediationResult(
            success=True,
            action_type="CHANGE_CHANNEL",
            target=ap_id,
            message=f"Switched {ap.name} {band} radio from Channel {old_channel} to Channel {target_channel}. Channel utilization reduced to 21.5%.",
            details={"ap_id": ap_id, "new_channel": target_channel, "new_utilization_pct": 21.5}
        )

    def adjust_tx_power(self, ap_id: str, band: str, power_dbm: int) -> RemediationResult:
        ap = self.aps.get(ap_id)
        if not ap:
            return RemediationResult(
                success=False,
                action_type="ADJUST_TX_POWER",
                target=ap_id,
                message=f"Access Point {ap_id} not found."
            )

        if "2" in band:
            ap.tx_power_2g_dbm = power_dbm
        else:
            ap.tx_power_5g_dbm = power_dbm

        return RemediationResult(
            success=True,
            action_type="ADJUST_TX_POWER",
            target=ap_id,
            message=f"Updated {ap.name} {band} Tx power to {power_dbm} dBm.",
            details={"ap_id": ap_id, "band": band, "power_dbm": power_dbm}
        )

    def resolve_dhcp_pool(self) -> RemediationResult:
        self.services.dhcp_pool_used = 46
        self.services.dhcp_exhausted = False

        # Transition any DHCP_FAILED clients to CONNECTED
        for c in self.clients.values():
            if c.connection_state == ConnectionState.DHCP_FAILED:
                c.connection_state = ConnectionState.CONNECTED
                c.ip = "10.20.1.189"
                c.last_event = "REMEDIATED: DHCP lease assigned 10.20.1.189 after lease purge"

        # Update latest UXI probe
        self.run_synthetic_uxi_test()

        return RemediationResult(
            success=True,
            action_type="DHCP_REMEDIATION",
            target="VLAN_20_DHCP_SCOPE",
            message="Purged expired DHCP leases and expanded scope. All pending stations received IP addresses.",
            details={"pool_used": 46, "pool_total": self.services.dhcp_pool_total}
        )


# Singleton simulator instance
simulator = SimulatorEngine()
