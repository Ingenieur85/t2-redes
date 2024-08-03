import socket
import sys
import json
import time

PLAYER_COUNT = 4
BASE_PORT = 5000

def get_next_player(player_number):
    return (player_number % PLAYER_COUNT) + 1

def create_message(token, message=""):
    return json.dumps({"token": token, "message": message}).encode('utf-8')

def parse_message(data):
    message = json.loads(data.decode('utf-8'))
    return message["token"], message["message"]

def main(player_number):
    player_number = int(player_number)
    player_port = BASE_PORT + player_number
    next_player_port = BASE_PORT + get_next_player(player_number)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', player_port))

    if player_number == 1:
        token = True
        message = "Hello from player 1"
        sock.sendto(create_message(token, message), ('localhost', next_player_port))
    else:
        token = False

    while True:
        data, addr = sock.recvfrom(1024)
        token, message = parse_message(data)

        if token:
            print(f"Player {player_number} received message: {message}")
            if player_number == 1:
                message = "Hello from player 1"
            elif player_number == 2:
                message = "Hello from player 2"
            elif player_number == 3:
                message = "Hello from player 3"
            elif player_number == 4:
                message = "Hello from player 4"
            sock.sendto(create_message(token, message), ('localhost', next_player_port))
        else:
            sock.sendto(data, ('localhost', next_player_port))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <player_number>")
        sys.exit(1)
    player_number = sys.argv[1]
    main(player_number)