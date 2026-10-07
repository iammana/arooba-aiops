"""
Integration tests for AIOps Agent and tool execution loops.
Compatible with both pytest and python3 -m unittest.
"""

import unittest
from simulator.engine import simulator
from core.agent import aiops_agent


class TestAgent(unittest.TestCase):
    def test_agent_sticky_client_investigation(self):
        simulator.load_scenario("sticky_client")
        query = "User on f8:ff:c2:55:00:03 is having severe Zoom drops in Conference Room B."
        result = aiops_agent.run_investigation(query)

        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["trace"]), 4)
        self.assertIn("Root Cause Analysis (RCA)", result["final_report"])
        self.assertIn("Sticky Client", result["final_report"])
        self.assertIsNotNone(result["remediation"])
        self.assertEqual(result["remediation"]["action_type"], "DEAUTHENTICATE")

    def test_agent_channel_congestion_investigation(self):
        simulator.load_scenario("channel_congestion")
        query = "AP-ConfRoom-B is reporting sluggish throughput and high airtime utilization."
        result = aiops_agent.run_investigation(query)

        self.assertTrue(result["success"])
        self.assertIn("Root Cause Analysis (RCA)", result["final_report"])
        self.assertIn("Co-Channel Interference", result["final_report"])
        self.assertIsNotNone(result["remediation"])
        self.assertEqual(result["remediation"]["action_type"], "CHANGE_CHANNEL")

    def test_agent_dhcp_exhaustion_investigation(self):
        simulator.load_scenario("dhcp_exhaustion")
        query = "Clients cannot get an IP address on the guest VLAN."
        result = aiops_agent.run_investigation(query)

        self.assertTrue(result["success"])
        self.assertIn("Root Cause Analysis (RCA)", result["final_report"])
        self.assertIn("DHCP", result["final_report"])
        self.assertIsNotNone(result["remediation"])
        self.assertEqual(result["remediation"]["action_type"], "DHCP_REMEDIATION")


if __name__ == "__main__":
    unittest.main()
