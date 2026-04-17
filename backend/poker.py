import random
import hand_calculator

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    
    def print(self):
        if self.rank == 14:
            rank = 'A'
        elif self.rank == 13:
            rank = 'K'
        elif self.rank == 12:
            rank = 'Q'
        elif self.rank == 11:
            rank = 'J'
        elif self.rank == 10:
            rank = 'T'
        else:
            rank = self.rank
        print(f"{rank}{self.suit}", end=' ')

def shuffle(deck):
    random.shuffle(deck)

def new_deck():
    deck = []
    for i in range(2, 15):
        for j in range(4):
            if j == 0:
                suit = 'H'
            elif j == 1:
                suit = 'D'
            elif j == 2:
                suit = 'S'
            else:
                suit = 'C'

            card = Card(i, suit)
            deck.append(card)
    shuffle(deck)
    return deck

def deal_hand(deck, players):
    for i in range(len(players)*2):
        players[i//2].append(deck.pop())

def deal_flop(deck, board):
   for i in range(3):
       board.append(deck.pop())

def deal_next_card(deck, board):
   board.append(deck.pop())

def determine_winner(players, board):
    scores = []
    winners = []
    for player in players:
        hand = player + board
        scores.append(hand_calculator.calculate_hand(hand))
    best = 0
    for i, score in enumerate(scores):
        if score > best:
            best = score
            winners = [i]
        elif score == best:
            winners.append(i)
    return winners


players = [[],[],[],[],[]]
board = []
deck = new_deck()
deal_hand(deck, players)
for i, player in enumerate(players):
    print(f"Player {i} Hand: ", end='')
    player[0].print()
    player[1].print()
    print('')
deal_flop(deck, board)
for card in board:
    card.print()
print('')
deal_next_card(deck, board)
for card in board:
    card.print()
print('')
deal_next_card(deck, board)
for card in board:
    card.print()
print('')
winners = determine_winner(players, board)
print(f"Winner(s): ")
for winner in winners:
    print(winner)



