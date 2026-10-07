"""
Unit tests for SimulatorEngine.
Compatible with both pytest and python3 -m unittest.
"""

import unittest
from simulator.engine import SimulatorEngine
from simulator.models import ConnectionState


class TestSimulator(unittest.TestCase):
    def test_simulator_baseline(self):
        sim = SimulatorEngine()
        sim.load_scenario("baseline")
        self.assertEqual(len(sim.get_all_aps()), 3)
        self.assertEqual(len(sim.get_all_clients()), 5)
        services = sim.get_network_services()
        self.assertFalse(services.dhcp_exhausted)

    def test_simulator_sticky_client(self):
        sim = SimulatorEngine()
        sim.load_scenario("sticky_client")
        client = sim.get_client("f8:ff:c2:55:00:03")
        self.assertIsNotNone(client)
        self.assertTrue(client.sticky_client_detected)
        self.assertEqual(client.rssi_dbm, -83)

        # Remediate via deauth / steer
        res = sim.deauthenticate_client("f8:ff:c2:55:00:03")
        self.assertTrue(res.success)
        self.assertFalse(client.sticky_client_detected)
        self.assertEqual(client.rssi_dbm, -47)
        self.assertEqual(client.band, "5GHz")

    def test_simulator_channel_congestion(self):
        sim = SimulatorEngine()
        sim.load_scenario("channel_congestion")
        ap = sim.get_ap("ap-conf-b")
        self.assertIsNotNone(ap)
        self.assertGreater(ap.channel_utilization_pct, 70.0)

        # Remediate via channel change
        res = sim.change_channel("ap-conf-b", "2.4GHz", 1)
        self.assertTrue(res.success)
        self.assertEqual(ap.channel_2g, 1)
        self.assertEqual(ap.channel_utilization_pct, 21.5)

    def test_simulator_dhcp_exhaustion(self):
        sim = SimulatorEngine()
        sim.load_scenario("dhcp_exhaustion")
        services = sim.get_network_services()
        self.assertTrue(services.dhcp_exhausted)

        troubled_client = sim.get_client("ee:11:22:33:44:55")
        self.assertIsNotNone(troubled_client)
        self.assertEqual(troubled_client.connection_state, ConnectionState.DHCP_FAILED)

        # Remediate via DHCP pool resolve
        res = sim.resolve_dhcp_pool()
        self.assertTrue(res.success)
        self.assertFalse(services.dhcp_exhausted)
        self.assertEqual(troubled_client.connection_state, ConnectionState.CONNECTED)
        self.assertIsNotNone(troubled_client.ip)


if __name__ == "__main__":
    unittest.main()
