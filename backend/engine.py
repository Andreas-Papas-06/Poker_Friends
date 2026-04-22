from enum import Enum
import poker

class GamePhase(Enum):
    WAITING   = "waiting"
    PRE_FLOP  = "pre_flop"
    FLOP      = "flop"
    TURN      = "turn"
    RIVER     = "river"
    SHOWDOWN  = "showdown"

class Player:
    def __init__(self, id, chips):
        self.hand = []
        self.id = id
        self.chips = chips
        self.current_bet = 0
        self.folded = False
        self.all_in = False
        self.has_acted = False
        self.leaving = False

class PokerGame:
    def __init__(self, players, sb, bb, starting_stack):
        self.players = [Player(player, starting_stack) for player in players]
        self.waiting = []
        self.starting_stack = starting_stack
        self.sb = sb
        self.bb = bb
        self.pot = 0
        self.board = []
        self.deck = []
        self.phase = GamePhase.WAITING
        self.current_bet = 0
        self.action_turn = 0
        self.dealer = 0

    def start_round(self):
        self.phase = GamePhase.PRE_FLOP
        for p in self.players:
            if p.leaving:
                self.players.remove(p)
        self.dealer = (self.dealer + 1) % len(self.players)
        self.players += self.waiting
        self.board = []
        self.pot = 0
        self.current_bet = 0
        self.action_turn = (self.dealer + 3) % len(self.players)  
        for p in self.players:
            p.hand = []
            p.current_bet = 0
            p.folded = False
            p.all_in = False
            p.has_acted = False

        self.deck = poker.new_deck()
        poker.deal_hand(self.deck, [p.hand for p in self.players])
        sb = self.players[(self.dealer + 1) % len(self.players)]
        bb = self.players[(self.dealer + 2) % len(self.players)]
        self.post_blind(sb, self.sb)
        self.post_blind(bb, self.bb)
        self.current_bet = self.bb

        

    def advance_phase(self):
        self.reset_bets()

        if self.phase == GamePhase.PRE_FLOP:
            poker.deal_flop(self.deck, self.board)
            self.phase = GamePhase.FLOP

        elif self.phase == GamePhase.FLOP:
            poker.deal_next_card(self.deck, self.board)
            self.phase = GamePhase.TURN

        elif self.phase == GamePhase.TURN:
            poker.deal_next_card(self.deck, self.board)
            self.phase = GamePhase.RIVER

        elif self.phase == GamePhase.RIVER:
            self.phase = GamePhase.SHOWDOWN
            self.resolve_showdown()
            return

        self.action_turn = (self.dealer + 1) % len(self.players)


    def reset_bets(self):
        self.current_bet = 0
        for p in self.players:
            p.current_bet = 0
            p.has_acted = False

    def betting_round_over(self):
        for p in self.players:
            if p.folded or p.all_in:
                continue
            if not p.has_acted or p.current_bet < self.current_bet:
                return False
        return True
    
    def resolve_showdown(self):
        active = [p for p in self.players if not p.folded]
        hands = [p.hand for p in active]
        winners = poker.determine_winner(hands, self.board)
        winner_players = [active[i] for i in winners]
        self.award_pot(winner_players)

    
    def next_active_player(self):
        for i in range(len(self.players)):
            self.action_turn = (self.action_turn + 1) % len(self.players)
            p = self.players[self.action_turn]
            if not p.folded and not p.all_in:
                return
        self.skip_to_showdown()

    def skip_to_showdown(self):
        while self.phase not in (GamePhase.RIVER, GamePhase.SHOWDOWN):
            self.advance_phase()


    def post_blind(self, player, amount):
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        self.pot += actual

    def player_bet(self, player, amount):
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        
        amount = min(amount, player.chips)
        player.chips -= amount
        player.current_bet += amount
        self.pot += amount

        if player.current_bet > self.current_bet:
            self.current_bet = player.current_bet
            for p in self.players:
                if not p.folded:
                    p.has_acted = False

        if player.chips == 0:
            player.all_in = True

        player.has_acted = True
        self.after_action()

    def after_action(self):
        active = [p for p in self.players if not p.folded]
        if len(active) == 1:
            self.award_pot(active)
            return
        
        if self.betting_round_over():
            self.advance_phase()
        else:
            self.next_active_player()

    def player_call(self, player):
        to_call = self.current_bet - player.current_bet
        self.player_bet(player, to_call) 
        
    def player_fold(self, player):
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        player.folded = True
        player.has_acted = True
        self.after_action()

    def player_check(self, player):
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        if self.current_bet > player.current_bet:
            raise ValueError("Can't check, there's a bet to call")
        player.has_acted = True
        self.after_action()

    def award_pot(self, winners):
        share = self.pot / len(winners)
        for w in winners:
            w.chips += share
        self.phase = GamePhase.SHOWDOWN

    def player_join(self, player_id):
        for p in self.players + self.waiting:
            if p.id == player_id:
                raise ValueError("Player already in game")
        self.waiting.append(Player(player_id, self.starting_stack))

    def player_leave(self, player_id):
        for p in self.waiting:
            if p.id == player_id:
                self.waiting.remove(p)
                return
        for p in self.players:
            if p.id == player_id and p.folded:
                p.leaving = True
            elif p.id == player_id:
                p.folded = True
                p.leaving = True

        



