"""
Unit tests for Unified TelemetryClient and hardware mode fallback handling.
Compatible with both pytest and python3 -m unittest.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.telemetry_client import TelemetryClient
from core.agent import aiops_agent
from simulator.models import ConnectionState


class TestTelemetryClient(unittest.TestCase):
    def setUp(self):
        self.client = TelemetryClient(mode="simulated")

    def test_simulated_mode_defaults(self):
        self.assertEqual(self.client.get_mode(), "simulated")
        aps = self.client.get_all_aps()
        self.assertGreaterEqual(len(aps), 2)
        clients = self.client.get_all_clients()
        self.assertGreaterEqual(len(clients), 3)

    def test_edge_host_configuration(self):
        self.client.set_edge_host("http://192.168.1.150:8000/")
        self.assertEqual(self.client.get_edge_host(), "http://192.168.1.150:8000")

    @patch.object(TelemetryClient, "_http_get")
    def test_hardware_mode_unreachable_returns_empty_and_offline(self, mock_http_get):
        mock_http_get.return_value = None
        self.client.set_mode("hardware")
        self.client.set_edge_host("http://127.0.0.1:59999")  # Unused port
        self.client.last_error = "Connection refused / unreachable host at http://127.0.0.1:59999/health"

        health = self.client.check_edge_health(timeout=0.2, force=True)
        self.assertFalse(health["connected"])
        self.assertIsNotNone(health["error"])

        # When offline, get_all_aps and get_all_clients must NOT fall back to the simulator
        aps = self.client.get_all_aps()
        self.assertEqual(len(aps), 0)

        clients = self.client.get_all_clients()
        self.assertEqual(len(clients), 0)

    @patch.object(TelemetryClient, "_http_get")
    def test_hardware_mode_mocked_success(self, mock_http_get):
        self.client.set_mode("hardware")

        def mock_get_side_effect(path, timeout=None):
            if path == "/health":
                return {
                    "status": "online",
                    "interface": "wlan0",
                    "platform": "Raspberry Pi 5 (Edge Node)",
                    "linux_tools_available": {"iw": True, "hostapd_cli": True},
                }
            elif path == "/api/v1/telemetry/ap":
                return {
                    "ap_id": "pi5-edge-ap",
                    "name": "RaspberryPi-5-Edge-AP",
                    "model": "Raspberry Pi 5 AP",
                    "channel": 36,
                    "channel_utilization_pct": 18.5,
                    "noise_floor_dbm": -92,
                    "channel_width_mhz": 80,
                    "tx_power_dbm": 20.0,
                    "system_health": {"cpu_temp_c": 49.1, "cpu_load_1m": 0.15},
                }
            elif path == "/api/v1/telemetry/clients":
                return [
                    {
                        "mac": "b4:2e:99:11:22:33",
                        "ip": "192.168.4.88",
                        "hostname": "Pixel-8",
                        "bssid": "wlan0",
                        "rssi_dbm": -55,
                        "snr_db": 37,
                        "tx_bitrate_mbps": 433.0,
                        "rx_bitrate_mbps": 433.0,
                        "tx_retries": 2,
                        "sticky_client_detected": False,
                        "rx_bytes": 500000,
                        "tx_bytes": 1200000,
                        "inactive_time_ms": 50,
                        "bitrate_info": "VHT-MCS 9 80MHz",
                    }
                ]
            elif path == "/api/v1/telemetry/services":
                return {
                    "dhcp_pool_total": 191,
                    "dhcp_pool_used": 1,
                    "dhcp_exhausted": False,
                    "dns_latency_ms": 2.1,
                    "gateway_reachable": True,
                    "radius_auth_status": "N/A",
                    "wan_reachable": True,
                    "wan_latency_ms": 11.8,
                    "eth0_carrier": True,
                    "eth0_speed_mbps": 1000,
                    "conntrack_sessions": 25,
                }
            return None

        mock_http_get.side_effect = mock_get_side_effect

        health = self.client.check_edge_health(force=True)
        self.assertTrue(health["connected"])

        aps = self.client.get_all_aps()
        self.assertEqual(len(aps), 1)
        self.assertEqual(aps[0].name, "RaspberryPi-5-Edge-AP")
        self.assertEqual(aps[0].channel_utilization_pct, 18.5)
        self.assertEqual(aps[0].channel_width_mhz, 80)
        self.assertEqual(aps[0].cpu_temp_c, 49.1)

        clients = self.client.get_all_clients()
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0].mac, "b4:2e:99:11:22:33")
        self.assertEqual(clients[0].hostname, "Pixel-8")
        self.assertEqual(clients[0].rx_bytes, 500000)
        self.assertEqual(clients[0].bitrate_info, "VHT-MCS 9 80MHz")
        self.assertEqual(clients[0].connection_state, ConnectionState.CONNECTED)

        services = self.client.get_network_services()
        self.assertEqual(services.dhcp_pool_used, 1)
        self.assertFalse(services.dhcp_exhausted)
        self.assertEqual(services.wan_latency_ms, 11.8)
        self.assertTrue(services.eth0_carrier)
        self.assertEqual(services.conntrack_sessions, 25)

    @patch.object(TelemetryClient, "_http_get")
    def test_agent_investigation_in_offline_hardware_mode(self, mock_http_get):
        mock_http_get.return_value = None
        from core.telemetry_client import telemetry_client
        original_mode = telemetry_client.get_mode()
        original_host = telemetry_client.get_edge_host()

        try:
            telemetry_client.set_mode("hardware")
            telemetry_client.set_edge_host("http://127.0.0.1:59999")
            telemetry_client.last_error = "Connection refused / host unreachable"
            telemetry_client.check_edge_health(timeout=0.1, force=True)

            res = aiops_agent.run_investigation("Check network health", provider_override="mock")
            self.assertFalse(res["success"])
            self.assertIn("Physical Edge Connection Alert", res["final_report"])
            self.assertIn("Raspberry Pi 5", res["final_report"])
        finally:
            telemetry_client.set_mode(original_mode)
            telemetry_client.set_edge_host(original_host)
            telemetry_client.last_error = None
            telemetry_client._health_cache = None
            telemetry_client._health_cache_time = 0.0


if __name__ == "__main__":
    unittest.main()
