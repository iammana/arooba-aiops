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

    def test_parse_station_dump_signal_avg_fallback(self):
        dump = """
Station 1c:bc:fe:41:70:f0 (on wlan0)
    inactive time:  120 ms
    tx bitrate:     72.2 MBit/s
    signal avg:     -58 dBm
"""
        stations = parse_station_dump(dump)
        self.assertEqual(len(stations), 1)
        self.assertEqual(stations[0]["rssi_dbm"], -58)
        self.assertEqual(stations[0]["signal_avg_dbm"], -58)
        self.assertTrue(stations[0]["rssi_measured"])

    def test_parse_station_dump_bracketed_mimo(self):
        dump = """
Station 1c:bc:fe:41:70:f0 (on wlan0)
    signal:         -52 [-55, -57] dBm
    tx bitrate:     72.2 MBit/s
"""
        stations = parse_station_dump(dump)
        self.assertEqual(len(stations), 1)
        self.assertEqual(stations[0]["rssi_dbm"], -52)
        self.assertTrue(stations[0]["rssi_measured"])

    def test_parse_hostapd_all_sta(self):
        raw = """
1c:bc:fe:41:70:f0
flags=[AUTH][ASSOC][AUTHORIZED][WMM][HT]
signal=-58
rx_rate_info=722
tx_rate_info=722
connected_time=320
b0:ab:c1:cb:c7:c7
flags=[AUTH][ASSOC]
signal=-79
tx_rate_info=60
connected_time=120
"""
        from edge.parsers import parse_hostapd_all_sta
        sta = parse_hostapd_all_sta(raw)
        self.assertIn("1c:bc:fe:41:70:f0", sta)
        self.assertEqual(sta["1c:bc:fe:41:70:f0"]["signal"], -58)
        self.assertEqual(sta["1c:bc:fe:41:70:f0"]["tx_rate_info"], 72.2)
        self.assertEqual(sta["b0:ab:c1:cb:c7:c7"]["signal"], -79)
        self.assertEqual(sta["b0:ab:c1:cb:c7:c7"]["tx_rate_info"], 6.0)

    def test_parse_iw_info(self):
        from edge.parsers import parse_iw_info
        raw_iw = """
Interface wlan0
        ifindex 3
        wdev 0x1
        addr b8:27:eb:11:22:33
        ssid Arooba-AIOps-Lab
        type AP
        wiphy 0
        channel 36 (5180 MHz), width: 80 MHz, center1: 5210 MHz
        txpower 20.00 dBm
"""
        info = parse_iw_info(raw_iw)
        self.assertEqual(info["channel"], 36)
        self.assertEqual(info["frequency_mhz"], 5180)
        self.assertEqual(info["channel_width_mhz"], 80)
        self.assertEqual(info["center_freq1_mhz"], 5210)
        self.assertEqual(info["tx_power_dbm"], 20.0)
        self.assertEqual(info["ssid"], "Arooba-AIOps-Lab")

    def test_parse_proc_net_dev(self):
        from edge.parsers import parse_proc_net_dev
        raw_dev = """
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
  eth0: 1000000    5000    0    0    0     0          0         0  2000000    8000    0    0    0     0       0          0
 wlan0:  145920    1204    1    0    0     0          0         0   854002    2840    0    0    0     0       0          0
"""
        stats = parse_proc_net_dev(raw_dev, "wlan0")
        self.assertEqual(stats["rx_bytes"], 145920)
        self.assertEqual(stats["rx_packets"], 1204)
        self.assertEqual(stats["rx_errs"], 1)
        self.assertEqual(stats["tx_bytes"], 854002)
        self.assertEqual(stats["tx_packets"], 2840)

    def test_parse_station_dump_deep_telemetry(self):
        stations = parse_station_dump(SAMPLE_STATION_DUMP)
        s = stations[0]
        self.assertEqual(s["rx_bytes"], 145920)
        self.assertEqual(s["tx_bytes"], 854002)
        self.assertEqual(s["rx_packets"], 1204)
        self.assertEqual(s["tx_packets"], 2840)
        self.assertEqual(s["inactive_time_ms"], 120)
        self.assertIn("VHT-MCS 9 80MHz", s["tx_bitrate_info"])


if __name__ == "__main__":
    unittest.main()

