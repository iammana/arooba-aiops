"""
Simulation Engine for Arooba-AIOps.
Maintains state for simulated Access Points, Clients, and Network Services.
Supports injecting realistic enterprise Wi-Fi troubleshooting scenarios.
"""

from typing import Dict, List, Optional
from simulator.models import (
    AccessPoint,
    ClientStation,
    ConnectionState,
    NetworkServicesStatus,
    RemediationResult,
)


class SimulatorEngine:
    def __init__(self):
        self.aps: Dict[str, AccessPoint] = {}
        self.clients: Dict[str, ClientStation] = {}
        self.services: NetworkServicesStatus = NetworkServicesStatus()
        self.current_scenario: str = "baseline"
        self.load_scenario("baseline")

    def load_scenario(self, scenario_name: str) -> str:
        """Loads a pre-canned enterprise Wi-Fi scenario."""
        self.current_scenario = scenario_name

        if scenario_name == "baseline":
            self._setup_baseline()
            return "Loaded baseline: Healthy multi-AP campus network."
        elif scenario_name == "sticky_client":
            self._setup_sticky_client()
            return "Loaded scenario: Sticky Client roaming failure in Conference Room B."
        elif scenario_name == "channel_congestion":
            self._setup_channel_congestion()
            return "Loaded scenario: High Co-Channel Interference (CCI) on 2.4 GHz radio."
        elif scenario_name == "dhcp_exhaustion":
            self._setup_dhcp_exhaustion()
            return "Loaded scenario: DHCP lease pool exhaustion on guest/client VLAN."
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
        )
        if troubled_mac in self.aps["ap-conf-b"].connected_clients:
            self.aps["ap-conf-b"].connected_clients.remove(troubled_mac)
        if troubled_mac not in self.aps["ap-lobby"].connected_clients:
            self.aps["ap-lobby"].connected_clients.append(troubled_mac)

    def _setup_channel_congestion(self):
        """Simulates high channel utilization (airtime choke) on AP-ConfRoom-B."""
        self._setup_baseline()
        self.aps["ap-conf-b"].channel_utilization_pct = 91.4
        self.aps["ap-conf-b"].noise_floor_dbm = -78  # High RF noise floor
        # Associated client suffers retries
        client = self.clients["f8:ff:c2:55:00:03"]
        client.tx_retries_pct = 28.5
        client.last_event="HIGH_AIRTIME_UTILIZATION: 91.4% busy airtime on channel 6"

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
        )
        self.aps["ap-conf-b"].connected_clients.append(new_mac)

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

        return RemediationResult(
            success=True,
            action_type="DHCP_REMEDIATION",
            target="VLAN_20_DHCP_SCOPE",
            message="Purged expired DHCP leases and expanded scope. All pending stations received IP addresses.",
            details={"pool_used": 46, "pool_total": self.services.dhcp_pool_total}
        )


# Singleton simulator instance
simulator = SimulatorEngine()
