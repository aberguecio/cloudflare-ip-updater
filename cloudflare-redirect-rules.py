#!/usr/bin/env python3
"""Update legacy opt-in A records and explicitly configured home-server domains."""
import ipaddress
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
API = "https://api.cloudflare.com/client/v4"


def request_json(url, headers=None, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers=headers or {},
                      method="GET" if payload is None else "PATCH")
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        # Do not log the response body or credentials.
        raise RuntimeError(f"HTTP {error.code} from {request.host}") from None


class Cloudflare:
    def __init__(self, credentials):
        if credentials.get("bearer_token"):
            self.headers = {"Authorization": "Bearer " + credentials["bearer_token"]}
        else:
            self.headers = {"X-Auth-Key": credentials["api_token"],
                            "X-Auth-Email": credentials["email"]}
        self.headers["Content-Type"] = "application/json"

    def call(self, path, payload=None):
        result = request_json(API + path, self.headers, payload)
        if not result.get("success"):
            raise RuntimeError("Cloudflare rejected " + path.split("?")[0])
        return result

    def list(self, path, **params):
        page = 1
        while True:
            result = self.call(path + "?" + urlencode({**params, "page": page, "per_page": 50}))
            yield from result["result"]
            if page >= result.get("result_info", {}).get("total_pages", 1):
                break
            page += 1


def synchronize(client, legacy_ids, domains, public_ip, dry_run=False):
    # Validate before making any DNS writes; an unavailable IP service is fatal.
    public_ip = str(ipaddress.IPv4Address(public_ip.strip()))
    zones = {zone_id: set() for zone_id in legacy_ids}
    errors = []
    for domain, names in domains.items():
        try:
            matches = list(client.list("/zones", name=domain))
            if len(matches) != 1 or matches[0]["status"] != "active":
                raise RuntimeError("Expected one accessible active zone for " + domain)
            zones.setdefault(matches[0]["id"], set()).update(names)
        except (RuntimeError, OSError, ValueError) as error:
            errors.append(str(error))

    changes = []
    for zone_id, required_names in zones.items():
        try:
            found = set()
            zone_changes = []
            for record in client.list(f"/zones/{zone_id}/dns_records"):
                # Never turn CNAME, AAAA, mail or verification records into A records.
                if record["type"] != "A":
                    continue
                name = record["name"]
                explicit = name in required_names
                words = (record.get("comment") or "").split()
                legacy = zone_id in legacy_ids and bool(words) and words[0] == "update"
                if explicit:
                    found.add(name)
                if (explicit or legacy) and record["content"] != public_ip:
                    zone_changes.append((zone_id, record))
            missing = required_names - found
            if missing:
                raise RuntimeError("No existing A record for: " + ", ".join(sorted(missing)))
            changes.extend(zone_changes)
        except (RuntimeError, OSError, ValueError) as error:
            errors.append(str(error))

    # Each zone is validated before its writes. Healthy legacy domains still
    # update when another zone is unavailable; report partial failure afterward.
    for zone_id, record in changes:
        print(("Would update " if dry_run else "Updating ") + record["name"])
        if not dry_run:
            try:
                client.call(f'/zones/{zone_id}/dns_records/{record["id"]}', {"content": public_ip})
            except (RuntimeError, OSError, ValueError) as error:
                errors.append(str(error))
    if errors:
        raise RuntimeError("; ".join(errors))
    print(f"DNS sync complete: {len(changes)} changed record(s), dry_run={dry_run}")
    return len(changes)


def main():
    if any(arg != "--dry-run" for arg in sys.argv[1:]):
        raise ValueError("Usage: cloudflare-redirect-rules.py [--dry-run]")
    credentials = json.loads((ROOT / "tokens.json").read_text())
    domains = json.loads((ROOT / "domains.json").read_text())
    with urlopen("https://api.ipify.org", timeout=30) as response:
        public_ip = response.read().decode("ascii").strip()
    synchronize(Cloudflare(credentials), credentials.get("zones_id", []), domains,
                public_ip, dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"DNS sync failed: {error}", file=sys.stderr)
        sys.exit(1)
