import socket
import argparse
import time
import random

# Network configuration
PLAYER_PORTS = [5001, 5002, 5003, 5004]
HOST = 'localhost'

# Game constants
INITIAL_LIVES = 3  # Reduced for faster testing, change to 12 for full game
NUM_PLAYERS = 4
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

class Player:
    def __init__(self, num):
        self.num = num
        self.lives = INITIAL_LIVES
        self.hand = []
        self.bet = 0
        self.tricks = 0

    def is_alive(self):
        return self.lives > 0

class GameState:
    def __init__(self):
        self.players = [Player(i+1) for i in range(NUM_PLAYERS)]
        self.dealer = 0
        self.round = 0
        self.deck = []

    def next_dealer(self):
        self.dealer = (self.dealer + 1) % NUM_PLAYERS
        while not self.players[self.dealer].is_alive():
            self.dealer = (self.dealer + 1) % NUM_PLAYERS

    def alive_players(self):
        return [p for p in self.players if p.is_alive()]

def setup_network(player_num):
    my_port = PLAYER_PORTS[player_num - 1]
    next_port = PLAYER_PORTS[player_num % NUM_PLAYERS]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, my_port))
    return sock, (HOST, next_port)

def send_message(sock, dest_address, message):
    sock.sendto(message.encode(), dest_address)

def receive_message(sock):
    data, addr = sock.recvfrom(1024)
    return data.decode()

def pass_token(sock, next_address):
    send_message(sock, next_address, "TOKEN")

def create_deck():
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]

def shuffle_deck(deck):
    random.shuffle(deck)

def deal_cards(deck, num_cards):
    return [deck.pop() for _ in range(num_cards)]

def play_card(hand):
    print("Your hand:", ", ".join(hand))
    while True:
        card = input("Choose a card to play: ")
        if card in hand:
            hand.remove(card)
            return card
        print("Invalid card. Try again.")

def get_bet(hand_size):
    while True:
        try:
            bet = int(input(f"Enter your bet (0-{hand_size}): "))
            if 0 <= bet <= hand_size:
                return bet
            print("Invalid bet. Try again.")
        except ValueError:
            print("Please enter a number.")

def initialize_game(sock, player_num, next_address):
    print(f"Player {player_num} entering initialization...")
    if player_num == 1:
        print("Player 1 waiting for all players to connect...")
        while True:
            print("Player 1 waiting to receive message...")
            msg = receive_message(sock)
            print(f"Player 1 received: {msg}")
            if msg == "START":
                print("All players connected. Game starting...")
                break
    else:
        print(f"Player {player_num} waiting for initialization...")
        while True:
            print(f"Player {player_num} waiting to receive message...")
            msg = receive_message(sock)
            print(f"Player {player_num} received: {msg}")
            if msg == f"INIT {player_num - 1}":
                print(f"Player {player_num} connected. Sending ready signal...")
                send_message(sock, next_address, f"INIT {player_num}")
                print(f"Player {player_num} sent: INIT {player_num}")
                if player_num == 4:
                    print("All players connected. Sending START signal...")
                    send_message(sock, next_address, "START")
                    print("Player 4 sent: START")
                break

    if player_num == 4:
        print("Dealer (Player 4) passing initial token...")
        pass_token(sock, next_address)
        print("Player 4 sent: TOKEN")

    print(f"Player {player_num} exiting initialization...")

def main(player_num):
    sock, next_address = setup_network(player_num)
    print(f"Player {player_num} started on port {PLAYER_PORTS[player_num-1]}")

    game_state = GameState()
    game_state.dealer = 3  # Player 4 is the initial dealer

    initialize_game(sock, player_num, next_address)
    print(f"Player {player_num} finished initialization, entering main game loop")

    my_player = game_state.players[player_num - 1]

    while len(game_state.alive_players()) > 1:
        print(f"Player {player_num} waiting for action. Current dealer: Player {game_state.dealer + 1}")  
        if player_num - 1 == game_state.dealer:
            # Dealer's actions
            game_state.round += 1
            num_cards = 13 - (game_state.round - 1) % 13
            game_state.deck = create_deck()
            shuffle_deck(game_state.deck)
            
            for p in game_state.alive_players():
                p.hand = deal_cards(game_state.deck, num_cards)
                send_message(sock, next_address, f"DEAL {p.num} {' '.join(p.hand)}")
            
            # Betting phase
            for _ in range(len(game_state.alive_players())):
                received = receive_message(sock)
                parts = received.split()
                if parts[0] == "BET":
                    player_num, bet = int(parts[1]), int(parts[2])
                    game_state.players[player_num - 1].bet = bet
                send_message(sock, next_address, received)
            
            # Playing phase
            for _ in range(num_cards):
                for _ in range(len(game_state.alive_players())):
                    received = receive_message(sock)
                    parts = received.split()
                    if parts[0] == "PLAY":
                        player_num, card = int(parts[1]), parts[2]
                        # Simple trick resolution (highest card wins)
                        if _ == 0 or card > winning_card:
                            winning_card = card
                            winning_player = player_num
                    send_message(sock, next_address, received)
                game_state.players[winning_player - 1].tricks += 1
            
            # Results
            for p in game_state.alive_players():
                if p.bet != p.tricks:
                    p.lives -= abs(p.bet - p.tricks)
                p.bet = 0
                p.tricks = 0
                send_message(sock, next_address, f"RESULT {p.num} {p.lives}")
            
            game_state.next_dealer()
            pass_token(sock, next_address)

        else:
            # Non-dealer actions
            received = receive_message(sock)
            parts = received.split()
            
            if parts[0] == "DEAL" and int(parts[1]) == player_num:
                my_player.hand = parts[2:]
                my_player.bet = get_bet(len(my_player.hand))
                send_message(sock, next_address, f"BET {player_num} {my_player.bet}")
            elif parts[0] == "PLAY":
                if int(parts[1]) == player_num:
                    card = play_card(my_player.hand)
                    send_message(sock, next_address, f"PLAY {player_num} {card}")
                else:
                    send_message(sock, next_address, received)
            elif parts[0] == "RESULT":
                if int(parts[1]) == player_num:
                    my_player.lives = int(parts[2])
                    print(f"Round ended. You have {my_player.lives} lives left.")
                send_message(sock, next_address, received)
            elif parts[0] == "TOKEN":
                pass_token(sock, next_address)
            else:
                send_message(sock, next_address, received)

    if my_player.is_alive():
        print("Congratulations! You've won the game!")
    else:
        print("Game over. You've run out of lives.")

    sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fodinha game player")
    parser.add_argument("player_num", type=int, choices=range(1, 5), 
                        help="Player number (1-4)")
    args = parser.parse_args()
    
    main(args.player_num)

