#!/usr/bin/env bash
# Install the repository-managed schedule without changing unrelated jobs.
set -euo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Cron paths cannot safely contain whitespace or percent signs.
[[ "$ROOT" != *[[:space:]%]* ]] || { echo "Unsupported cron path" >&2; exit 1; }
command -v flock >/dev/null
command -v python3 >/dev/null
cron_error="$(mktemp)"
trap 'rm -f "$cron_error"' EXIT
if existing="$(LC_ALL=C crontab -l 2>"$cron_error")"; then
  :
elif [[ "$(cat "$cron_error")" == "no crontab for "* ]]; then
  existing=""
else
  echo "Cannot read crontab; refusing to replace existing jobs" >&2
  exit 1
fi
mkdir -p "$ROOT/.cron-backups"
printf '%s\n' "$existing" > "$ROOT/.cron-backups/crontab-$(date +%Y%m%d-%H%M%S)-$$"
{
  printf '%s\n' "$existing" | awk -v root="$ROOT" '
    index($0, "# cloudflare-ip-updater managed") { next }
    index($0, root "/") && index($0, "cloudflare-redirect-rules.py") { next }
    { print }
  '
  printf '*/10 * * * * cd %s && /usr/bin/flock -n .update.lock /usr/bin/python3 cloudflare-redirect-rules.py >> cloudflare-redirect-rules.log 2>&1 # cloudflare-ip-updater managed\n' "$ROOT"
} | crontab -
echo "Installed ten-minute DNS sync; previous crontab retained in .cron-backups/"
