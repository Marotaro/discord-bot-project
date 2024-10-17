from mcrcon import MCRcon
from mcrcon import MCRconException
from mcstatus import JavaServer
import requests
from config import PASSWORD, AUTHORISATION
import json

def com(command):
    try:
        with MCRcon(f"{get_server_info('ip')}", password=PASSWORD, port= int(get_server_info("port")), timeout=5) as client:
            response = client.command(command)
        return(response)
    except MCRconException as e:
        return f"error: executing command: {str(e)}"


def get_ping():
    server = JavaServer.lookup(f"{get_server_info('ip')}:{get_server_info('port')}")
    return server.ping()

def get_players():
    server = JavaServer.lookup(f"{get_server_info('ip')}:{get_server_info('port')}")
    query = server.query()
    return query.players.names


def get_player_uuid(pseudo):
    url = f'https://api.mojang.com/users/profiles/minecraft/{pseudo}?'
    response = requests.get(url)
    return response.json()['id']

def get_player_name(uuid):
    url = f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}'
    response = requests.get(url)
    return response.json()['name']

def get_ressources():
    url = f"https://rest.minestrator.com/api/v1/server/ressources/{get_server_info('uuid')}"
    headers = {
        'Authorization': f'{AUTHORISATION}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        yolo = response.json()
        return yolo['data'][0]
    else:
        return False
    
def get_content():
    url = f"https://rest.minestrator.com/api/v1/server/content/{get_server_info('uuid')}"
    headers = {
        'Authorization': f'{AUTHORISATION}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        yolo = response.json()
        return yolo['data'][0]
    else:
        return False

def get_if_up():
    ressources = get_ressources()
    try:
        status = ressources.get('status')
        print(status)
        return status
    except:
        return 'error'

def server_action(action):
        url = 'https://rest.minestrator.com/api/v1/server/action'
        headers = {
            'Authorization': f'{AUTHORISATION}'
        }
        params = {
            'hashsupport': f"{get_server_info('uuid')}",
            'action': action  # Actions possibles : start, stop, restart, kill
        }

        response = requests.post(url, headers=headers, data=params)

        if response.status_code == 200:
            yolo = response.json()
            print(yolo)
        else:
            print(f"Erreur lors de la requête: {response.status_code}")

def create_server_info():
    server_info = {
        "uuid": "empty",
        "ip": "empty",
        "port": "empty",
        "rcon_port": "empty"
    }
    with open('server_info.json', 'w') as file:
        json.dump(server_info, file)
        file.close()
        print('Fichier server_info.json créé avec succès.')

def get_server_info(type):
    try:
        with open('server_info.json', 'r') as file:
            data = json.load(file)
            file.close()
        return data[type]
    except:
        create_server_info()
        return 'empty'
    
def change_server_info(type, info):
    for n in range(2):
        try:
            with open('server_info.json', 'r') as file:
                data = json.load(file)
                file.close()
            data[type] = info
            with open('server_info.json', 'w') as file:
                json.dump(data, file)
                file.close()
            print(f'Server {type} changé avec succès.')
        except:
            create_server_info()
