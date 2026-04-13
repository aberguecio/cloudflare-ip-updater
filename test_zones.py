import requests
import json

with open('tokens.json') as f:
    tokens = json.load(f)

email = tokens['email']
api_token = tokens['api_token']
zones_id = tokens['zones_id']

for zone_id in zones_id:
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}'
    headers = {
        'X-Auth-Key': api_token,
        'X-Auth-Email': email,
        'Content-type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        zone_info = response.json()['result']
        print(f"✓ Zone ID: {zone_id}")
        print(f"  Dominio: {zone_info['name']}")
        print(f"  Estado: {zone_info['status']}")
        print()
    else:
        print(f"✗ Zone ID: {zone_id}")
        print(f"  Error: {response.status_code}")
        print(f"  Mensaje: {response.text}")
        print()
