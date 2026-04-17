from itertools import combinations
from collections import Counter
#hand = [12, 9]
#board = [4, 4, 4, 9, 9]
#types = ['h', 'd', 'c', 's', 'd', 'c', 'c' ]
#cards = hand + board

def is_flush(types, cards):
    c= Counter(types)
    
    for k, v in c.items():
        if v >= 5:
            values = [card for i, card in enumerate(cards) if types[i] == k ]
            straight_flush = int(is_straight(values))
            
            if {14, 13, 12, 11, 10}.issubset(set(values)):
                print("Royal Flush")
                return 1000000
            elif straight_flush: 
                print(f"{(straight_flush - 500000) // 1000} high Straight Flush")
                return  (5 if (straight_flush - 500000) // 1000 == 14 else (straight_flush - 500000) // 1000) + 900000
            else:
                print(f"{max(values)} high flush")
                score = 0
                mult = 1000
                for val in sorted(values, reverse=True)[:5]:
                    score += val*mult
                    mult //= 10
                return 600000 + score
            
    return 0

def is_straight(cards):
    values = sorted(cards)
    # check for wheel
    straight = {values[-1]}
    if {14, 2, 3, 4, 5}.issubset(set(values)):
        return 505000
    count = 1
    for i in range(len(values)-1, -1, -1):
        
        if i == len(values)-1:
            continue
        if values[i] == values[i+1]:
            continue
        if count == 5:
            score = 0
            mult = 1000
            for val in sorted(list(straight), reverse=True):
                score += val*mult
                mult //= 10
            return 500000 + score
        if values[i] == values[i+1] - 1:
            straight.add(values[i])
            count += 1
        else:
            straight.clear()
            straight.add(values[i])
            count = 1
    if count == 5:
        score = 0
        mult = 1000
        for val in sorted(list(straight), reverse=True):
            score += val*mult
            mult //= 10
        return 500000 + score
    else:
        return 0
    
def is_quads_or_full_house(c):
    quads = []
    trips = []
    pairs = []
    for k, v in c.items():
        if v == 4:
            quads.append(k)
        elif v == 3:
            trips.append(k)
        elif v == 2:
            pairs.append(k)

    quads.sort(reverse=True)
    trips.sort(reverse=True)
    pairs.sort(reverse=True)
    if quads:
        quad = quads[0]
        kicker = max([k for k in c if k != quad])
        print(f"Four of a kind {quad}")
        return 800000 + quad * 100 + kicker
    if len(trips) >= 2:
        print(f"{trips[0]}s full of {trips[1]}s")
        return 700000 + trips[0] * 100 + trips[1]
    elif trips and pairs:
        print(f"{trips[0]}s full of {pairs[0]}s")
        return 700000 + trips[0] * 100 + pairs[0]
    return 0

def trips_two_pair(c):
    trips = []
    pairs = []
    singles = []
    for k, v in c.items():
        if v == 3:
            trips.append(k)
        elif v == 2:
            pairs.append(k)
        else:
            singles.append(k)
    trips.sort(reverse=True)
    pairs.sort(reverse=True)
    singles.sort(reverse=True)

    # Trips
    if trips:
        trip = trips[0]
        kickers = sorted([k for k in c if k != trip], reverse=True)[:2]
        print(f"trip {trip}s")
        return 400000 + trip * 1000 + kickers[0] * 50 + kickers[1]

    # Two pair
    if len(pairs) >= 2:
        high, low = pairs[:2]
        kicker = max([k for k in c if k != high and k != low])
        print(f"two pair {high}s and {low}s")
        return 300000 + high * 1000 + low * 50 + kicker

    # One pair
    if pairs:
        pair = pairs[0]
        kickers = sorted([k for k in c if k != pair], reverse=True)[:3]
        print(f"pair of {pair}s")
        score = 0
        mult = 1000
        for val in kickers:
            score += val * mult
            mult //= 10
        return 200000 + pair * 10000 + score
    return 0

def high_card(cards):
    sorted_cards = sorted(cards, reverse=True)
    score = 0
    mult = 1000
    for val in sorted_cards[:5]:
        score += val*mult
        mult //= 10
    return 100000 + score

def calculate_hand(hand):
    cards = []
    types = []
    for card in hand:
        cards.append(card.rank)
        types.append(card.suit)
    c_cards = Counter(cards)
    c_cards = dict(sorted(c_cards.items(), reverse=True))
    score = 0

    # check flushes
    # its ok to check for flush before full house beacuse a player cannot have both
    score = is_flush(types, cards)
    if score:
        return score

    # ckeck full house or quads
    score = is_quads_or_full_house(c_cards)
    if score:
        return score

    #check straight
    score = is_straight(cards)
    if score:
        return score

    #check trips and two pair
    score = trips_two_pair(c_cards)
    if score:
        return score
    
    # high card
    return high_card(cards)

