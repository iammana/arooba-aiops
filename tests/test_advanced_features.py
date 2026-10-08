"""
Unit and Integration Tests for Advanced Enterprise Features:
- Aruba AirMatch RF Optimizer
- Synthetic UXI Probe Engine
- WIDS / WIPS Rogue AP Threat Containment
- Application Quality of Experience (QoE / UCC)
- Telemetry Baseline Anomaly Detection
- Visual RF Floorplan Heatmap Generator
"""

import unittest
from simulator.engine import simulator
from core.agent import aiops_agent
from core.tools import (
    run_synthetic_uxi_probe,
    scan_wids_security_threats,
    remediate_contain_rogue_ap,
    remediate_optimize_campus_rf_plan,
    get_application_qoe_telemetry,
    get_baseline_anomalies,
)
from ui.floorplan import generate_floorplan_svg


class TestAdvancedEnterpriseFeatures(unittest.TestCase):

    def setUp(self):
        simulator.load_scenario("baseline")

    def test_airmatch_rf_optimization(self):
        """Tests that AirMatch resolves campus RF channel conflicts and reduces CCI."""
        simulator.load_scenario("campus_rf_conflict")
        # All APs initially share channel 6 and 36
        aps_before = simulator.get_all_aps()
        self.assertEqual(len(set(ap.channel_2g for ap in aps_before)), 1)

        plan = simulator.optimize_campus_rf_plan()
        self.assertGreater(plan.pre_cci_score, 0.0)
        self.assertEqual(plan.post_cci_score, 0.0)
        self.assertEqual(plan.interference_reduction_pct, 100.0)

        # After AirMatch, AP channels must be distributed orthogonally
        aps_after = simulator.get_all_aps()
        channels_2g = [ap.channel_2g for ap in aps_after]
        self.assertIn(1, channels_2g)
        self.assertIn(6, channels_2g)
        self.assertIn(11, channels_2g)

    def test_synthetic_uxi_probe_baseline_and_failure(self):
        """Tests that synthetic UXI probe reports PASSED on healthy baseline and FAILED on DHCP exhaustion."""
        # Baseline check
        report_ok = simulator.run_synthetic_uxi_test()
        self.assertEqual(report_ok.overall_sla, "PASSED")
        self.assertLess(report_ok.dhcp_dora_time_ms, 100.0)
        self.assertGreater(report_ok.dl_throughput_mbps, 100.0)

        # DHCP exhaustion scenario
        simulator.load_scenario("dhcp_exhaustion")
        report_fail = simulator.run_synthetic_uxi_test()
        self.assertEqual(report_fail.overall_sla, "FAILED")
        self.assertEqual(report_fail.failing_phase, "DHCP_DORA")
        self.assertEqual(report_fail.dl_throughput_mbps, 0.0)

    def test_wids_rogue_ap_detection_and_containment(self):
        """Tests WIDS detection of Evil Twin attack and WIPS containment."""
        simulator.load_scenario("evil_twin_attack")
        threats = simulator.scan_wids_security_threats()
        self.assertEqual(len(threats), 1)

        threat = threats[0]
        self.assertEqual(threat.threat_type, "EVIL_TWIN_AP")
        self.assertEqual(threat.severity, "CRITICAL")
        self.assertFalse(threat.is_contained)

        # Trigger containment
        res = simulator.contain_rogue_ap(threat.bssid)
        self.assertTrue(res.success)
        self.assertTrue(threat.is_contained)
        self.assertIn("ACTIVE", threat.mitigation_action)

    def test_application_qoe_zoom_degradation(self):
        """Tests Layer-7 Zoom MOS score degradation and restoration."""
        simulator.load_scenario("zoom_audio_jitter")
        client_mac = "f8:ff:c2:55:00:03"
        qoe = simulator.get_application_qoe(client_mac)
        self.assertIsNotNone(qoe)
        self.assertEqual(qoe.zoom_status, "CRITICAL")
        self.assertLess(qoe.zoom_mos_score, 3.0)
        self.assertGreater(qoe.zoom_packet_loss_pct, 10.0)

    def test_baseline_anomalies_z_score(self):
        """Tests statistical Z-score baseline anomaly detection."""
        simulator.load_scenario("channel_congestion")
        anomalies = simulator.get_baseline_anomalies()
        self.assertGreater(len(anomalies), 0)
        self.assertTrue(any(a.is_anomaly for a in anomalies))
        self.assertTrue(any(a.z_score >= 2.5 for a in anomalies))

    def test_floorplan_svg_rendering(self):
        """Tests that the SVG floorplan generator produces valid, styled SVG with campus zones."""
        simulator.load_scenario("evil_twin_attack")
        aps = simulator.get_all_aps()
        clients = simulator.get_all_clients()
        threats = simulator.scan_wids_security_threats()
        uxi = simulator.get_uxi_sensor_status()

        svg = generate_floorplan_svg(aps, clients, threats, uxi)
        self.assertIn("<svg", svg)
        self.assertIn("ZONE 3: EXECUTIVE CONF ROOM B", svg)
        self.assertIn("ROGUE AP", svg)
        self.assertIn("UXI Probe Sensor", svg)
        self.assertIn("AP-Lobby-Main", svg)

    def test_agent_investigation_evil_twin(self):
        """Tests that the agent autonomously identifies and contains Rogue AP attacks."""
        simulator.load_scenario("evil_twin_attack")
        query = "Security sensor in Conference Room B flagged an unknown AP spoofing our network SSID."
        result = aiops_agent.run_investigation(query, provider_override="mock")

        self.assertTrue(result["success"])
        self.assertIn("Security Incident Summary", result["final_report"])
        self.assertIn("CONTAINED", result["final_report"])
        self.assertIn("remediate_contain_rogue_ap", [t["tool"] for t in result["trace"]])

    def test_agent_investigation_campus_rf_conflict(self):
        """Tests that the agent invokes AirMatch RF optimizer when campus conflict is reported."""
        simulator.load_scenario("campus_rf_conflict")
        query = "Campus-wide channel conflict reported across building floors. Run AirMatch RF plan."
        result = aiops_agent.run_investigation(query, provider_override="mock")

        self.assertTrue(result["success"])
        self.assertIn("remediate_optimize_campus_rf_plan", [t["tool"] for t in result["trace"]])
        self.assertIn("AirMatch", result["final_report"])


if __name__ == "__main__":
    unittest.main()
