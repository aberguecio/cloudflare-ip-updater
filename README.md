# Multi-Domain Cloudflare IP Sync

This script updates the IP address for all desired domains in Cloudflare with your local IP. When updating, it retains the existing `proxied` or `non-proxied` status for each domain.

To trigger the update, you need to include "update" in the comment message. You can write anything after "update" as only the first word is checked.
![image](https://github.com/user-attachments/assets/01daeb50-5d48-4bf3-b870-b21f7366a4f8)



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
