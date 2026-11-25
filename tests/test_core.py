"""Tests for platform-independent SENTINEL X functionality."""

import unittest

from sentinel_x.diagnostics import InputValidationError, validate_host, validate_port
from sentinel_x.network import summarize_ipv4
from sentinel_x.connections import tcp_state_label
from sentinel_x.reporting import build_snapshot, snapshot_to_csv, snapshot_to_json


class HostValidationTests(unittest.TestCase):
    def test_accepts_domain(self):
        self.assertEqual(validate_host("google.com"), "google.com")

    def test_trims_whitespace(self):
        self.assertEqual(validate_host("  127.0.0.1  "), "127.0.0.1")

    def test_rejects_shell_metacharacters(self):
        with self.assertRaises(InputValidationError):
            validate_host("example.com & whoami")

    def test_rejects_empty_host(self):
        with self.assertRaises(InputValidationError):
            validate_host("   ")


class PortValidationTests(unittest.TestCase):
    def test_accepts_valid_port(self):
        self.assertEqual(validate_port("443"), 443)

    def test_rejects_out_of_range_port(self):
        with self.assertRaises(InputValidationError):
            validate_port(65536)

    def test_rejects_non_numeric_port(self):
        with self.assertRaises(InputValidationError):
            validate_port("https")


class SubnetSummaryTests(unittest.TestCase):
    def test_calculates_user_lesson_subnet(self):
        facts = summarize_ipv4("10.0.6.3", 21)
        self.assertEqual(facts["subnet_mask"], "255.255.248.0")
        self.assertEqual(facts["network_address"], "10.0.0.0")
        self.assertEqual(facts["broadcast_address"], "10.0.7.255")
        self.assertEqual(facts["first_usable"], "10.0.0.1")
        self.assertEqual(facts["last_usable"], "10.0.7.254")
        self.assertEqual(facts["total_addresses"], 2048)

    def test_handles_point_to_point_prefix(self):
        facts = summarize_ipv4("192.0.2.10", 31)
        self.assertEqual(facts["first_usable"], "192.0.2.10")
        self.assertEqual(facts["last_usable"], "192.0.2.11")


class TcpStateLabelTests(unittest.TestCase):
    def test_maps_numeric_windows_states(self):
        self.assertEqual(tcp_state_label(2), "Listening")
        self.assertEqual(tcp_state_label(5), "Established")
        self.assertEqual(tcp_state_label(100), "Bound")

    def test_normalizes_string_states(self):
        self.assertEqual(tcp_state_label("SynSent"), "SYN Sent")
        self.assertEqual(tcp_state_label("CloseWait"), "Close Wait")
        self.assertEqual(tcp_state_label("Established"), "Established")

    def test_handles_bound_and_listen_names(self):
        self.assertEqual(tcp_state_label("Bound"), "Bound")
        self.assertEqual(tcp_state_label("Listen"), "Listening")
        self.assertEqual(tcp_state_label("TimeWait"), "Time Wait")

    def test_handles_unknown_or_missing_state(self):
        self.assertEqual(tcp_state_label(None), "Unknown")
        self.assertEqual(tcp_state_label(999), "Unknown (999)")


class ReportingTests(unittest.TestCase):
    def test_snapshot_includes_categories(self):
        snapshot = build_snapshot(network=[], arp=[], tcp=[], udp=[])
        self.assertEqual(snapshot["application"], "SENTINEL X")
        self.assertIn("generated_at_utc", snapshot)
        self.assertEqual(snapshot["tcp_connections"], [])

    def test_json_and_csv_exports(self):
        snapshot = build_snapshot(
            network=[], arp=[{"ip": "10.0.0.1", "mac": "aa-bb-cc-dd-ee-ff"}],
            tcp=[], udp=[]
        )
        json_text = snapshot_to_json(snapshot)
        csv_text = snapshot_to_csv(snapshot)
        self.assertIn('"arp_entries"', json_text)
        self.assertIn("arp_entries", csv_text)
        self.assertIn("10.0.0.1", csv_text)


if __name__ == "__main__":
    unittest.main()
