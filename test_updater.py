import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("updater", Path(__file__).with_name("cloudflare-redirect-rules.py"))
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def record(name, kind="A", content="192.0.2.1", comment=None):
    return dict(id=name, name=name, type=kind, content=content, comment=comment,
                proxied=True, ttl=300, tags=["production"])


class FakeCloudflare:
    def __init__(self, records, zones=None):
        self.records = records
        self.zones = zones or {"pichan.ga": [dict(id="new", status="active")]}
        self.writes = []

    def list(self, path, **params):
        if path == "/zones":
            return iter(self.zones.get(params["name"], []))
        return iter(self.records[path.split("/")[2]])

    def call(self, path, payload):
        self.writes.append((path, payload))


class UpdateTests(unittest.TestCase):
    def test_preserves_legacy_opt_in_and_updates_explicit_domain_without_comment(self):
        cf = FakeCloudflare({"old": [record("existing.cl", comment="update home"),
                                    record("unrelated.cl"), record("empty.cl", comment="   ")],
                             "new": [record("pichan.ga")]})
        updater.synchronize(cf, ["old"], {"pichan.ga": ["pichan.ga"]}, "198.51.100.5")
        self.assertEqual(cf.writes, [("/zones/old/dns_records/existing.cl", {"content": "198.51.100.5"}),
                                     ("/zones/new/dns_records/pichan.ga", {"content": "198.51.100.5"})])

    def test_other_record_types_and_unselected_subdomains_are_untouched(self):
        cf = FakeCloudflare({"new": [record("pichan.ga"), record("mail.pichan.ga", "MX", comment="update"),
                                    record("v6.pichan.ga", "AAAA", "2001:db8::1", "update"),
                                    record("www.pichan.ga", "CNAME", "pichan.ga", "update")]})
        updater.synchronize(cf, [], {"pichan.ga": ["pichan.ga"]}, "198.51.100.5")
        self.assertEqual(len(cf.writes), 1)

    def test_same_ip_and_dry_run_never_write(self):
        cf = FakeCloudflare({"new": [record("pichan.ga")]})
        updater.synchronize(cf, [], {"pichan.ga": ["pichan.ga"]}, "192.0.2.1")
        updater.synchronize(cf, [], {"pichan.ga": ["pichan.ga"]}, "198.51.100.5", dry_run=True)
        self.assertEqual(cf.writes, [])

    def test_invalid_ip_fails_before_discovery_or_writes(self):
        cf = FakeCloudflare({})
        for ip in ("", "error", "2001:db8::1"):
            with self.assertRaises(ValueError):
                updater.synchronize(cf, [], {}, ip)
        self.assertEqual(cf.writes, [])

    def test_bad_new_zone_does_not_block_healthy_legacy_domains(self):
        for zones, records in (({}, []),
                               ({"pichan.ga": [dict(id="new", status="active")]},
                                [record("pichan.ga", "CNAME", "server.example")])):
            cf = FakeCloudflare({"old": [record("existing.cl", comment="update")], "new": records}, zones)
            if not zones:
                cf.zones = {}
            with self.assertRaises(RuntimeError):
                updater.synchronize(cf, ["old"], {"pichan.ga": ["pichan.ga"]}, "198.51.100.5")
            self.assertEqual(cf.writes, [("/zones/old/dns_records/existing.cl", {"content": "198.51.100.5"})])

    def test_pagination_does_not_drop_records_after_first_page(self):
        cf = updater.Cloudflare(dict(bearer_token="test"))
        with patch.object(cf, "call", side_effect=[
            dict(result=[1], result_info=dict(total_pages=2)),
            dict(result=[2], result_info=dict(total_pages=2))]) as call:
            self.assertEqual(list(cf.list("/zones/example/dns_records")), [1, 2])
            self.assertIn("per_page=50", call.call_args_list[0].args[0])
            self.assertIn("page=2", call.call_args_list[1].args[0])

    def test_new_zone_already_in_legacy_list_is_not_updated_twice(self):
        cf = FakeCloudflare({"new": [record("pichan.ga", comment="update")]})
        updater.synchronize(cf, ["new"], {"pichan.ga": ["pichan.ga"]}, "198.51.100.5")
        self.assertEqual(len(cf.writes), 1)


if __name__ == "__main__":
    unittest.main()
