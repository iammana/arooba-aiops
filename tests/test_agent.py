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


    def test_gemini_fallback_without_key(self):
        result = aiops_agent.run_investigation(
            "Test query",
            provider_override="gemini",
            api_key_override="",
        )
        self.assertTrue(result["success"])
        self.assertIn("Fallback: GEMINI_API_KEY not configured", result["provider"])

    def test_gemini_fallback_on_api_error(self):
        from unittest.mock import patch
        with patch("google.generativeai.GenerativeModel", side_effect=RuntimeError("QuotaExceeded")):
            result = aiops_agent.run_investigation(
                "Test query",
                provider_override="gemini",
                api_key_override="fake-test-key",
            )
            self.assertTrue(result["success"])
            self.assertIn("Fallback from Gemini error", result["provider"])
            self.assertIn("QuotaExceeded", result["provider"])

    def test_gemini_mocked_agent_execution(self):
        from unittest.mock import patch, MagicMock

        mock_response = MagicMock()
        mock_response.text = "### 📋 Incident Summary\nResolved by Gemini agent."

        mock_chat = MagicMock()

        def side_effect_send_message(prompt):
            # Simulate Gemini invoking a tool
            for t in captured_tools:
                if getattr(t, "__name__", "") == "list_access_points":
                    t()
            return mock_response

        mock_chat.send_message.side_effect = side_effect_send_message

        mock_model_instance = MagicMock()
        mock_model_instance.start_chat.return_value = mock_chat

        captured_tools = []
        def mock_init(model_name, system_instruction, tools):
            nonlocal captured_tools
            captured_tools = tools
            return mock_model_instance

        with patch("google.generativeai.configure"), patch(
            "google.generativeai.GenerativeModel", side_effect=mock_init
        ):
            result = aiops_agent.run_investigation(
                "Survey campus AP status",
                provider_override="gemini",
                api_key_override="valid-test-key",
                model_override="gemini-1.5-flash",
            )
            self.assertTrue(result["success"])
            self.assertIn("Google Gemini Agent", result["provider"])
            self.assertEqual(len(result["trace"]), 1)
            self.assertEqual(result["trace"][0]["tool"], "list_access_points")
            self.assertIn("Resolved by Gemini agent", result["final_report"])


if __name__ == "__main__":
    unittest.main()

