import socket
import argparse
import time

# Network configuration
PLAYER_PORTS = [5001, 5002, 5003, 5004]
HOST = 'localhost'

def setup_network(player_num):
    """Set up the network for the current player."""
    my_port = PLAYER_PORTS[player_num - 1]
    next_port = PLAYER_PORTS[player_num % 4]  # Wrap around to the first player
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, my_port))
    return sock, (HOST, next_port)

def send_message(sock, dest_address, message):
    """Send a message to the next player."""
    sock.sendto(message.encode(), dest_address)

def receive_message(sock):
    """Receive a message from the previous player."""
    data, addr = sock.recvfrom(1024)
    return data.decode()

def pass_token(sock, next_address):
    """Pass the token to the next player."""
    send_message(sock, next_address, "TOKEN")

def main(player_num):
    sock, next_address = setup_network(player_num)
    print(f"Player {player_num} started on port {PLAYER_PORTS[player_num-1]}")

    # Initial token holder
    has_token = (player_num == 1)

    while True:
        if has_token:
            message = input(f"Player {player_num}, enter a message (or 'quit' to exit): ")
            if message.lower() == 'quit':
                break
            send_message(sock, next_address, f"Player {player_num} says: {message}")
            pass_token(sock, next_address)
            has_token = False
        else:
            received = receive_message(sock)
            if received == "TOKEN":
                has_token = True
                print(f"Player {player_num} received the token.")
            else:
                print(f"Received: {received}")

    sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fodinha game player")
    parser.add_argument("player_num", type=int, choices=range(1, 5), 
                        help="Player number (1-4)")
    args = parser.parse_args()
    
    main(args.player_num)