import requests
import json

# Cargar credenciales y detalles desde tokens.json
with open('tokens.json') as f:
    tokens = json.load(f)

email = tokens['email']
api_token = tokens['api_token']
zone_id = tokens['zone_id']

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

def all_dns_records():
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
    headers = {
        'X-Auth-Key': api_token,
        'X-Auth-Email': email,
        'Content-type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['result']
    else:
        print('Error al obtener los registros DNS:', response.text)
        return None
    
def update_dns_record(dns_record_id, dns_record_name, new_destination_ip, proxied, comment):
    update_dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}'
    headers = {
        'X-Auth-Key': api_token,
        'X-Auth-Email': email,
        'Content-type': 'application/json'
    }
    update_data = {
        'type': 'A',
        'name': dns_record_name,
        'content': new_destination_ip,
        'ttl': 1,  # 1 para 'automatic'
        'proxied': proxied,
        'comment': comment
    }

    response = requests.put(update_dns_url, headers=headers, json=update_data)
    if response.status_code == 200:
        print(f'Registro DNS {dns_record_name} actualizado exitosamente.')
    else:
        print(f'Error al actualizar el registro DNS {dns_record_name}:', response.text)
    

# Obtener la nueva IP pública
new_destination_ip = get_public_ip()

# Obtener todos los registros DNS
dns_records = all_dns_records()
if dns_records is None:
    print('No se pudieron obtener los registros DNS.')
    exit()

# Actualizar DNS 'update'
for dns_record in dns_records:
    if dns_record['comment'] is None:
        print(f'El registro DNS {dns_record["name"]} no tiene comentario.')
        continue
    else:
        comment = dns_record['comment'].split()

    if dns_record['content'] == new_destination_ip:
        print(f'La IP {new_destination_ip} ya está asignada al registro DNS {dns_record["name"]}.')
        continue

    if comment[0] == 'update':
        dns_record_name = dns_record['name']
        dns_record_id = dns_record['id']
        if len(comment) >= 2:
            proxied = comment[1] == "proxied"
        else:
            proxied = False

        update_dns_record(dns_record_id, dns_record_name, new_destination_ip, proxied, dns_record['comment'])


# https://developers.cloudflare.com/api