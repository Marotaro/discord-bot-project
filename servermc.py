from mcrcon import MCRcon
from mcstatus import JavaServer
import requests
from ping3 import ping

def com(command):
    with MCRcon('91.197.6.200', password='jFb2udiywF8uumJ', port= 30431, timeout=2) as client:
        response = client.command(command)
    return(response)


def getstatus():
    server = JavaServer.lookup('91.197.6.200:25609')
    status = server.status()
    return (f"The server has {status.players.online} player(s) online and replied in {status.latency} ms")

def getplayers():
    server = JavaServer.lookup('91.197.6.200:25609')
    query = server.query()
    return(f"The server has the following players online: {', '.join(query.players.names)}")

def get_player_uuid(pseudo):
    url = f'https://api.mojang.com/users/profiles/minecraft/{pseudo}?'
    response = requests.get(url)
    return response.json()['id']

def get_player_name(uuid):
    url = f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}'
    response = requests.get(url)
    return response.json()['name']

def get_if_up():
    server = JavaServer.lookup("91.197.6.200:25609")
    latency = server.ping()
    return latency

print(get_if_up())



