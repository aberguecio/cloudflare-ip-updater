import requests
import json

# Load credentials and details from tokens.json
with open('tokens.json') as f:
    tokens = json.load(f)

email = tokens['email']
api_token = tokens['api_token']
zone_id = tokens['zone_id']
ruleset_id = tokens['ruleset_id']
rule_id = tokens['rule_id']
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

# Define la solicitud para la API de Cloudflare con el nuevo destino de la regla de redirección
base_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}'
headers = {'X-Auth-Key': api_token, 'X-Auth-Email': email, 'Content-type': 'application/json'}
data = {
    "action": "redirect",
    "action_parameters": {
        "from_value":{
            "target_url": {
                "value": new_destination_ip,
            },
            "status_code": 302
        },
    },
    "expression": "http.host eq \"server.agustin.berguecio.cl\"",
    "description": "Redirección para server.agustin.berguecio.cl",
    "enabled": True
}

# Envía la solicitud PUT para actualizar la regla de redirección
response = requests.patch(base_url, headers=headers, json=data)
if response.status_code == 200:
    print('Regla de redirección actualizada exitosamente.')
else:
    print('Error al actualizar la regla de redirección:', response.text)


update_dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}'
update_data = {
    'type': 'A',
    'name': 'agustin.berguecio.cl',
    'content': new_destination_ip,
    'ttl': 1,  # 1 para 'automatic'
    'proxied': False 
}

response = requests.put(update_dns_url, headers=headers, json=update_data)
if response.status_code == 200:
    print('Registro DNS actualizado exitosamente.')
else:
    print('Error al actualizar el registro DNS:', response.text)

# https://developers.cloudflare.com/api/operations/updateZoneRulesetRule