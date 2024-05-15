import requests
import json

# Load credentials and details from tokens.json
with open('tokens.json') as f:
    tokens = json.load(f)

email = tokens['email']
api_token = tokens['api_token']
zone_id = tokens['zone_id']
dns_record_name = tokens['dns_record_name']
dns_record_id = tokens['dns_record_id']

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            print('IP pública obtenida exitosamente:', response.text)
            return response.text
        else:
            print('Error al obtener la IP pública:', response.text)
            return None
    except Exception as e:
        print('Error al obtener la IP pública:', str(e))
        return None
    
new_destination_ip = get_public_ip()

update_dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}'
headers = {'X-Auth-Key': api_token, 'X-Auth-Email': email, 'Content-type': 'application/json'}
update_data = {
    'type': 'A',
    'name': dns_record_name,
    'content': new_destination_ip,
    'ttl': 1,  # 1 para 'automatic'
    'proxied': False 
}

response = requests.put(update_dns_url, headers=headers, json=update_data)
if response.status_code == 200:
    print('Registro DNS actualizado exitosamente.')
else:
    print('Error al actualizar el registro DNS:', response.text)

# https://developers.cloudflare.com/api