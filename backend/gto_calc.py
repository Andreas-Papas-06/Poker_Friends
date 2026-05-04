import numpy as np
from poker import Card, new_deck, deal_hand, deal_next_card, get_score

hand = input("Enter Your Hand: ").split()
while len(hand) != 2:
    print("error: hand can only contain 2 cards")
    hand = input("Enter Your Hand: ").split()

board = input("Enter The Board: ").split()
while len(board) < 3 or len(board) > 5:
    print("error: board must contain 3 - 5 cards")
    board = input("Enter The Board: ").split()

pot = int(input("Enter pot size (BB): "))
stack = int(input("Enter your stack (BB): "))
bet = int(input("Enter bet facing you (0 if first to act): "))
pos = input("Enter position (ip/oop): ")

def map_c(c):
    if c == 'A':
        return 14
    elif c =='K':
        return 13
    elif c =='Q':
        return 12
    elif c =='J':
        return 11
    elif c =='T':
        return 10
    else:
        return int(c)

    

hand = [Card(map_c(c[0]), c[1]) for c in hand]
board = [Card(map_c(c[0]), c[1]) for c in board]


def get_equity(hand, board, simulations=10000):
    wins = 0
    ties = 0
    known = [f"{c.rank}{c.suit}" for c in hand+board]

    for i in range(simulations):
        deck = new_deck(known)
        opp_hand = []
        sim_board = board.copy()
        deal_hand(deck, [opp_hand])

        while len(sim_board) < 5:
            deal_next_card(deck, sim_board)

        my_score = get_score(hand+sim_board)
        opp_score = get_score(opp_hand+sim_board)

        if my_score == opp_score:
            ties += 1
        elif my_score > opp_score:
            wins += 1

    equity = (wins + ties * 0.5) / simulations
    return equity


def get_gto_frequencies(equity, pot, stack, facing_bet=0, position='ip'):
    spr = stack / pot

    if facing_bet > 0:
        pot_odds = facing_bet / (pot + facing_bet)
        equity_advantage = equity - pot_odds
        if equity_advantage > 0.20:
            fold = 0.0
            call = 0.5
            raise_ = 0.5
        elif equity_advantage > 0.10:
            fold = 0.05
            call = 0.6
            raise_ = 0.35
        elif equity_advantage > 0.0:
            fold  = 0.15
            call  = 0.70
            raise_ = 0.15
        elif equity_advantage > -0.10:
            fold  = 0.55
            call  = 0.40
            raise_ = 0.05
        else:
            fold  = 0.85
            call  = 0.15
            raise_ = 0.00

        if spr < 1.5:
            call  += raise_
            raise_ = 0.00

        frequencies = {'fold': fold, 'call': call, 'raise': raise_}
    else:
        bet_size = pot * 0.75
        mdf = pot / (pot + bet_size)

        if equity > 0.70:
            bet   = 0.85
            check = 0.15
        elif equity > 0.55:
            bet   = 0.60
            check = 0.40
        elif equity > 0.45:
            bet   = 0.40
            check = 0.60
        elif equity > 0.30:
            bet   = 1 - mdf  
            check = mdf

        else:
            bet   = 0.10
            check = 0.90

        if position == 'oop':
            shift = 0.10
            bet   = max(0, bet - shift)
            check = min(1, check + shift)

        frequencies = {'check': check, 'bet': bet}

    return frequencies


def display_gto(frequencies, equity, pot, facing_bet=0):
    """Prints a clean readable summary of the GTO output"""
    print("\n" + "="*40)
    print("        GTO STRATEGY ADVISOR")
    print("="*40)
    print(f"  Hand Equity   : {equity*100:.1f}%")
    print(f"  Pot Size      : {pot} BB")
    if facing_bet > 0:
        pot_odds = facing_bet / (pot + facing_bet)
        print(f"  Facing Bet    : {facing_bet} BB")
        print(f"  Pot Odds      : {pot_odds*100:.1f}% equity needed")
    print("-"*40)
    print("  GTO Action Frequencies:")
    print('')
    for action, freq in frequencies.items():
        bar = "█" * int(freq * 20)
        print(f"  {action.upper():<8} {freq*100:5.1f}%  {bar}")
        print('')
    print("="*40)



equity = get_equity(hand, board)
frequencies = get_gto_frequencies(equity, pot, stack, bet, pos)
display_gto(frequencies, equity, pot, bet)
