import http.client
import json

with open('tokens.json') as f:
    tokens = json.load(f)

email = tokens['email']
api_token = tokens['api_token']
zone_id = tokens['zone_id']


conn = http.client.HTTPSConnection("api.cloudflare.com")
headers = {'X-Auth-Key': api_token, 'X-Auth-Email': email, 'Content-type': 'application/json'}

conn.request("GET", f"/client/v4/zones/{zone_id}/dns_records", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))