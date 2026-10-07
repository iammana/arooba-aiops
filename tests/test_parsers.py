"""
Unit tests for Linux Wi-Fi telemetry parsers.
Compatible with both pytest and python3 -m unittest.
"""

import unittest
from edge.parsers import parse_station_dump, parse_survey_dump, parse_dnsmasq_leases


SAMPLE_STATION_DUMP = """
Station a4:83:e7:2b:11:05 (on wlan0)
    inactive time:  120 ms
    rx bytes:       145920
    rx packets:     1204
    tx bytes:       854002
    tx packets:     2840
    tx retries:     14
    tx failed:      0
    signal:         -52 dBm
    signal avg:     -53 dBm
    tx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
    rx bitrate:     866.7 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 2
    authorized:     yes
    authenticated:  yes
    associated:     yes
"""

SAMPLE_SURVEY_DUMP = """
Survey data from wlan0
    frequency:          5180 MHz
    noise:              -95 dBm
    channel active time: 1000 ms
    channel busy time:  350 ms
    channel receive time: 120 ms
    channel transmit time: 80 ms
"""

SAMPLE_DNSMASQ_LEASES = """
1712000000 a4:83:e7:2b:11:05 192.168.4.55 MacBook-Pro-Fadi 01:a4:83:e7:2b:11:05
1712000000 3c:22:fb:44:00:02 192.168.4.56 iPhone-Guest 01:3c:22:fb:44:00:02
1712000000 70:3a:cb:77:00:03 192.168.4.57 * *
"""


class TestEdgeParsers(unittest.TestCase):
    def test_parse_station_dump(self):
        stations = parse_station_dump(SAMPLE_STATION_DUMP)
        self.assertEqual(len(stations), 1)
        s = stations[0]
        self.assertEqual(s["mac"], "a4:83:e7:2b:11:05")
        self.assertEqual(s["rssi_dbm"], -52)
        self.assertEqual(s["tx_retries"], 14)
        self.assertEqual(s["tx_bitrate_mbps"], 866.7)

    def test_parse_survey_dump(self):
        survey = parse_survey_dump(SAMPLE_SURVEY_DUMP)
        self.assertEqual(survey["frequency_mhz"], 5180)
        self.assertEqual(survey["noise_floor_dbm"], -95)
        self.assertEqual(survey["channel_active_time_ms"], 1000)
        self.assertEqual(survey["channel_busy_time_ms"], 350)
        self.assertEqual(survey["channel_utilization_pct"], 35.0)

    def test_parse_dnsmasq_leases(self):
        leases = parse_dnsmasq_leases(SAMPLE_DNSMASQ_LEASES)
        self.assertIn("a4:83:e7:2b:11:05", leases)
        self.assertEqual(leases["a4:83:e7:2b:11:05"]["ip"], "192.168.4.55")
        self.assertEqual(leases["a4:83:e7:2b:11:05"]["hostname"], "MacBook-Pro-Fadi")
        self.assertEqual(leases["3c:22:fb:44:00:02"]["hostname"], "iPhone-Guest")
        self.assertEqual(leases["70:3a:cb:77:00:03"]["hostname"], "Unknown-Station")


if __name__ == "__main__":
    unittest.main()
