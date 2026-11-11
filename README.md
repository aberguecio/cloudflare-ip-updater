# Multi-domain Cloudflare IP sync

Updates existing home-server A records to the current public IPv4 address.
Python 3's standard library is sufficient; no extra dependencies are required.

Existing `tokens.json` files remain compatible: `email`, `api_token` (legacy
Global API Key), and `zones_id` (array of existing zone IDs). Alternatively use
`bearer_token` with a scoped API token. Credentials stay outside Git.

```json
{
  "bearer_token": "your-scoped-token",
  "zones_id": ["existing-zone-id"]
}
```

Legacy zones retain their selection rule: only A records whose first comment
word is `update` are updated. Whitespace-only comments are ignored. Other record
types are never converted, and PATCH changes only `content`, preserving record
IDs, proxy status, TTL, comments and tags.

`domains.json` adds explicit zone/record names without exposing credentials.
It includes the apex A record `pichan.ga`, even if its comment is empty. The
zone is discovered by exact name; existing zone IDs and opt-in behavior remain.
The credentials need Zone Read and DNS Edit access to that zone. The A record
must already exist; missing records, inaccessible zones and invalid public IPs
fail with a nonzero exit code. Invalid public IPs block all writes; zone failures
are isolated so healthy legacy domains continue updating. The updater does not create
records or change CNAME/AAAA/mail entries. Remove a stale AAAA record only after
separate explicit authorization if the server has no working IPv6 route.

## Install from this repository

On the home server, update the checkout to the reviewed revision and run:

```bash
cd /home/langosta/cloudflare-ip-updater
python3 cloudflare-redirect-rules.py --dry-run
bash install-cron.sh
```

The installer retains unrelated cron jobs, replaces this checkout's old updater
entry, and saves the previous crontab in `.cron-backups/`. It installs the same
ten-minute cadence using `flock` to prevent overlapping runs. Running the
installer twice leaves one managed job. Configuration is always loaded relative
to the script, so running from another working directory is safe.

```bash
python3 -m unittest -v test_updater.py
```

Production coordination: https://github.com/aberguecio/pichanga/issues/16
API reference: https://developers.cloudflare.com/api/resources/dns/subresources/records/
