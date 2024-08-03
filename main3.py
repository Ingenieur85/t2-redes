import socket
import json
import time

class RingNetwork:
    def __init__(self, player_id, total_players=4):
        self.player_id = player_id
        self.total_players = total_players
        self.port = 5000 + player_id
        self.next_port = 5000 + ((player_id + 1) % total_players)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', self.port))
        self.socket.settimeout(0.1)  # Short timeout for non-blocking receives

    def send(self, message):
        self.socket.sendto(json.dumps(message).encode(), ('localhost', self.next_port))

    def receive(self):
        try:
            data, addr = self.socket.recvfrom(1024)
            return json.loads(data.decode())
        except socket.timeout:
            return None

    def send_and_forward(self, message, origin_id):
        if message['sender'] == origin_id:
            print(f"Message completed full circle: {message}")
            return False
        else:
            print(f"Received and forwarding: {message}")
            self.send(message)
            return True

def setup_and_test_network(player_id, total_players=4):
    network = RingNetwork(player_id, total_players)
    print(f"Player {player_id} initialized on port {network.port}")

    # Wait for all players to join
    all_joined = False
    while not all_joined:
        if player_id == 0:  # First player initiates the join process
            network.send({
                'type': 'JOIN',
                'sender': player_id,
                'joined': [player_id]
            })

        message = network.receive()
        if message and message['type'] == 'JOIN':
            if player_id not in message['joined']:
                message['joined'].append(player_id)
            
            if len(message['joined']) == total_players:
                all_joined = True
                if player_id == 0:
                    print("All players have joined. Starting network test.")
                    time.sleep(1)  # Give other players time to process join completion
                    network.send({
                        'type': 'TEST',
                        'sender': player_id,
                        'content': f"Test message from Player {player_id}"
                    })
            else:
                network.send(message)

    # Test the network
    test_complete = False
    while not test_complete:
        message = network.receive()
        if message and message['type'] == 'TEST':
            test_complete = not network.send_and_forward(message, 0)

    print("Network test completed successfully.")
    return network

def main():
    player_id = int(input("Enter your player ID (0-3): "))
    network = setup_and_test_network(player_id)

    # Here you would typically start the game logic
    print("Network is ready. Game logic would start here.")

if __name__ == "__main__":
    main()