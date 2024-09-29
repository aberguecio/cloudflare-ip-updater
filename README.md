# Dinamic Cloudflare IP Updater

This script updates the IP address for all desired domains in Cloudflare with your local IP. When updating, it retains the existing `proxied` or `non-proxied` status for each domain.

To trigger the update, you need to include "update" in the comment message. You can write anything after "update" as only the first word is checked.

Consider adding this script to a cron job for periodic execution.

## Tokens

Create a `tokens.json` file with the following structure:

```json
{
    "email": "your_email",
    "api_token": "your_api_token",
    "zone_id": "your_zone_id"
}
```
