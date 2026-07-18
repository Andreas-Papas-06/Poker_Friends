from enum import Enum
from backend.engine import poker

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
        self.total_bet = 0
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
        self.last_raise = 0
        self.action_turn = 0
        self.dealer = 0
        self.side_pot = False
        self.side_pots = {}
        self.round_start_pot = 0
        self.player_data = {}
        self.last_result = []   # [{player_id, amount}] winners of the last completed hand

    def start_round(self):
        self.players += self.waiting
        self.waiting = []
        if len(self.players) < 2:
            raise ValueError("Not enough players to start")
        self.phase = GamePhase.PRE_FLOP
        self.players = [p for p in self.players if not p.leaving]
        self.dealer = (self.dealer + 1) % len(self.players)
        self.board = []
        self.last_result = []
        self.pot = 0
        self.current_bet = 0
        self.side_pot = False
        self.action_turn = (self.dealer + 3) % len(self.players)  
        for p in self.players:
            p.hand = []
            p.current_bet = 0
            p.total_bet = 0
            p.folded = False
            p.all_in = False
            p.has_acted = False

        self.deck = poker.new_deck()
        poker.deal_hand(self.deck, [p.hand for p in self.players])
        sb = self.players[(self.dealer + 1) % len(self.players)]
        bb = self.players[(self.dealer + 2) % len(self.players)]
        self.post_blind(sb.id, self.sb)
        self.post_blind(bb.id, self.bb)
        self.current_bet = self.bb
        self.last_raise = self.bb

        

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
        self.last_raise = self.bb
        for p in self.players:
            p.current_bet = 0
            p.has_acted = False

    def return_extra_chips(self):
        active = [p for p in self.players if not p.folded]
        if len(active) < 2:
            return
        active.sort(key=lambda p: p.current_bet)
        if active[-1].current_bet > active[-2].current_bet:
            extra = active[-1].current_bet - active[-2].current_bet
            active[-1].chips += extra
            active[-1].current_bet -= extra
            self.current_bet -= extra
            self.pot -= extra

    def betting_round_over(self):
        for p in self.players:
            if p.folded or p.all_in:
                continue
            if not p.has_acted or p.current_bet < self.current_bet:
                return False
        self.round_start_pot = self.pot
        return True
    
    def build_side_pots(self):
        all_in = [p for p in self.players if p.total_bet > 0]
        side_pots = []
        current_bets = list(set([p.total_bet for p in all_in]))
        current_bets.sort()
        last_pot = 0

        for bet in current_bets:
            contributers = [p for p in all_in if p.total_bet >= bet]
            players = [p for p in contributers if not p.folded]
            pot = bet * len(contributers)
            side_pots.append((pot - last_pot, players))
            last_pot = pot

        return side_pots
    
    def resolve_showdown(self):
        if self.side_pot:
            self.side_pots = self.build_side_pots()
            for pot, players in self.side_pots:
                hands = [p.hand for p in players]
                winners = poker.determine_winner(hands, self.board)
                winner_players = [players[i] for i in winners]
                self.award_pot(winner_players, pot)
        else:
            active = [p for p in self.players if not p.folded]
            hands = [p.hand for p in active]
            winners = poker.determine_winner(hands, self.board)
            winner_players = [active[i] for i in winners]
            self.award_pot(winner_players)

        self.phase = GamePhase.SHOWDOWN

    
    def next_active_player(self):
        for i in range(len(self.players)):
            self.action_turn = (self.action_turn + 1) % len(self.players)
            p = self.players[self.action_turn]
            if not p.folded and not p.all_in:
                return
        self.skip_to_showdown()

    def skip_to_showdown(self):
        while self.phase != GamePhase.SHOWDOWN:
            self.advance_phase()


    def post_blind(self, player_id, amount):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        player.total_bet += actual
        self.pot += actual

    def player_bet(self, player_id, amount):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        
        amount = min(amount, player.chips)
        player.chips -= amount
        player.current_bet += amount
        player.total_bet += amount
        self.pot += amount

        if player.chips == 0:
            player.all_in = True

        if player.current_bet > self.current_bet:
            self.last_raise = player.current_bet - self.current_bet
            self.current_bet = player.current_bet
            for p in self.players:
                if not p.folded and not p.all_in:
                    p.has_acted = False

        if player.chips == 0 and amount < self.current_bet:
            self.side_pot = True
            
        player.has_acted = True
        self.after_action()

    def after_action(self):
        active = [p for p in self.players if not p.folded]
        if len(active) <= 1:
            if active:
                self.award_pot(active)
            self.phase = GamePhase.SHOWDOWN
            return
        
        if self.betting_round_over():
            self.return_extra_chips()
            self.advance_phase()
        else:
            self.next_active_player()

    def player_call(self, player_id):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        to_call = self.current_bet - player.current_bet
        self.player_bet(player_id, to_call) 
        
    def player_fold(self, player_id):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        player.folded = True
        player.has_acted = True
        self.after_action()

    def player_check(self, player_id):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        if player is None or player.folded:
            raise ValueError("Invalid player")
        if self.players[self.action_turn] != player:
            raise ValueError("Not your turn")
        if self.current_bet > player.current_bet:
            raise ValueError("Can't check, there's a bet to call")
        player.has_acted = True
        self.after_action()

    def award_pot(self, winners, amount=0):
        if not amount:
            amount = self.pot
        self.pot -= amount
        share = amount // len(winners)
        remainder = amount % len(winners)
        winners[0].chips += remainder
        for w in winners:
            w.chips += share
            won = share + (remainder if w is winners[0] else 0)
            self.last_result.append({"player_id": w.id, "amount": won})

    def player_join(self, player_id):
        if not (len(self.players) + len(self.waiting) < 9):
            return
        if player_id in self.player_data:
            player = self.player_data[player_id]
            player.leaving = False          
            if player not in self.players and player not in self.waiting:
                if self.phase == GamePhase.WAITING:
                    self.players.append(player)
                else:
                    self.waiting.append(player)
            return
        # new player
        player = Player(player_id, self.starting_stack)
        self.player_data[player_id] = player
        if self.phase == GamePhase.WAITING:
            self.players.append(player)
        else:
            self.waiting.append(player)   

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
                if self.players[self.action_turn] == p:
                    self.after_action()

    def player_options(self, player_id):
        for p in self.players:
            if p.id == player_id:
                if p.folded or p.all_in:
                    return {"actions": [], "min_raise": 0, "max_raise": 0}
                to_call = self.current_bet - p.current_bet
                min_raise = self.current_bet + self.last_raise
                opponents = [pl for pl in self.players if pl.id != player_id and not pl.folded]
                opp_cap = max((pl.current_bet + pl.chips for pl in opponents), default=p.current_bet + p.chips)
                max_raise = min(p.current_bet + p.chips, opp_cap)
                options = ['fold']
                if to_call == 0:
                    options.append('check')
                else:
                    options.append('call')
                if p.chips > to_call:
                    options.append('raise')
                return {"actions": options, "min_raise": min_raise, "max_raise": max_raise}
        return {"actions": [], "min_raise": 0, "max_raise": 0}
            


# =============================================================================
# PokerGame Module — Function Index
# =============================================================================
#
# Player.__init__(self, id, chips)
#   Initializes a player with a given ID and chip count. Sets up hand, betting,
#   and status fields to their default values.
#
# PokerGame.__init__(self, players, sb, bb, starting_stack)
#   Initializes the game with a list of player IDs, blind sizes, and starting
#   stack. Sets up the deck, pot, board, and game phase.
#
# PokerGame.start_round(self)
#   Begins a new round by dealing hands, posting blinds, and resetting player
#   state. Rotates the dealer and merges any waiting players into the game.
#
# PokerGame.advance_phase(self)
#   Moves the game to the next street (Flop → Turn → River → Showdown),
#   dealing the appropriate community cards. Resets bets and repositions action.
#
# PokerGame.reset_bets(self)
#   Clears all current bets and acted flags for every player. Also resets the
#   table-level current bet to zero.
#
# PokerGame.return_extra_chips(self)
#   Refunds any unmatched chips to the player who over-bet relative to the
#   next-highest bet. Used when a player is all-in for less than the full bet.
#
# PokerGame.betting_round_over(self)
#   Checks whether all active (non-folded, non-all-in) players have acted and
#   matched the current bet. Returns True if the betting round is complete.
#
# PokerGame.build_side_pots(self)
#   Constructs a list of side pots when one or more players are all-in.
#   Each pot is paired with the subset of players eligible to win it.
#
# PokerGame.resolve_showdown(self)
#   Evaluates hands at showdown and awards the pot(s) to the winner(s).
#   Handles both standard pots and side pots from all-in situations.
#
# PokerGame.next_active_player(self)
#   Advances action_turn to the next player who has not folded or gone all-in.
#   If no such player exists, skips directly to showdown.
#
# PokerGame.skip_to_showdown(self)
#   Repeatedly advances the phase until showdown is reached. Used when no
#   further betting action is possible.
#
# PokerGame.post_blind(self, player, amount)
#   Deducts the blind amount from a player's stack and adds it to the pot.
#   Caps the blind at the player's remaining chips.
#
# PokerGame.player_bet(self, player, amount)
#   Processes a bet or raise action, updating the player's chips and the pot.
#   Detects all-in situations and triggers side pot logic if necessary.
#
# PokerGame.after_action(self)
#   Called after any player action to check if the hand or betting round is
#   over, and either awards the pot, advances the phase, or moves action along.
#
# PokerGame.player_call(self, player)
#   Calls the current bet by computing the difference owed and delegating to
#   player_bet.
#
# PokerGame.player_fold(self, player)
#   Marks the player as folded and triggers after_action. Validates that it is
#   the player's turn.
#
# PokerGame.player_check(self, player)
#   Allows a player to check if no bet is owed. Raises an error if there is an
#   outstanding bet that must be called or folded to.
#
# PokerGame.award_pot(self, winners, amount=0)
#   Distributes the pot (or a specified amount) evenly among winners. Any
#   indivisible remainder goes to the first winner in the list.
#
# PokerGame.player_join(self, player_id)
#   Adds a new player to the waiting list to join at the start of the next
#   round. Raises an error if the player is already in the game.
#
# PokerGame.player_leave(self, player_id)
#   Handles a player's departure gracefully. Removes waiting players
#   immediately; marks active players to fold and leave after their turn.
#
# PokerGame.player_options(self, player_id)
#   Returns the list of valid actions (fold, check, call, raise) available to
#   a given player based on the current bet and their chip count.
#
# =============================================================================

        



