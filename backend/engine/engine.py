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
        self.buy_ins = 1
        self.current_bet = 0
        self.total_bet = 0
        self.folded = False
        self.all_in = False
        self.has_acted = False
        self.leaving = False

class PokerGame:
    def __init__(self, players, sb, bb, starting_stack, rebuy, style, blind_increase, display):
        self.players = [Player(player, starting_stack) for player in players]
        self.waiting = []
        self.spectators = []
        self.starting_stack = starting_stack
        self.base_sb = sb
        self.base_bb = bb
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
        self.all_in_runout = False   # set when the board must be run out (all players all-in)
        self.rebuy = rebuy
        self.hand_count = 0
        self.sb = sb
        self.bb = bb
        self.style = style
        self.blind_inc = blind_increase
        self.display = display

    def start_round(self):
        # Build the prospective roster first and only commit once it's valid —
        # a refused start must not drop players or empty the waiting queue.
        # Busted players move to spectators — `leaving` means disconnected only,
        # and setting it here would strand them on the hand after a rebuy.
        busted = [p for p in self.players if p.chips == 0]
        roster = [p for p in self.players if p.chips > 0 and not p.leaving] + self.waiting
        if len(roster) < 2:
            raise ValueError("Not enough players to start")
        for p in busted:
            if p not in self.spectators:
                self.spectators.append(p)
        self.players = roster
        self.waiting = []
        self.phase = GamePhase.PRE_FLOP
        self.dealer = (self.dealer + 1) % len(self.players)
        self.board = []
        self.last_result = []
        self.all_in_runout = False
        self.pot = 0
        self.current_bet = 0
        self.side_pot = False
        self.hand_count += 1
        self.set_blinds()
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

        # Action starts left of the big blind — but only assign it after the
        # blinds are posted, since a player whose blind used their whole stack
        # is now all-in and has no actions. Handing them the turn freezes the
        # hand, because nobody else can act to trigger after_action.
        self.action_turn = (self.dealer + 2) % len(self.players)
        for _ in range(len(self.players)):
            self.action_turn = (self.action_turn + 1) % len(self.players)
            p = self.players[self.action_turn]
            if not p.folded and not p.all_in:
                break
        # No betting possible at all (everyone left is all-in on their blind) —
        # flag it so the socket layer runs the board out.
        if self.betting_round_over():
            self.all_in_runout = True

        

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

        # First live player left of the dealer — folded and all-in players have
        # no legal actions, so landing on one freezes the hand. Bounded scan
        # rather than next_active_player(), which recurses via skip_to_showdown.
        self.action_turn = self.dealer
        for _ in range(len(self.players)):
            self.action_turn = (self.action_turn + 1) % len(self.players)
            p = self.players[self.action_turn]
            if not p.folded and not p.all_in:
                break


    def reset_bets(self):
        self.current_bet = 0
        self.last_raise = self.bb
        for p in self.players:
            p.current_bet = 0
            p.has_acted = False

    def set_blinds(self):
        if self.style == 'T' and self.blind_inc > 0:
            level = (self.hand_count - 1) // self.blind_inc
            self.sb = self.base_sb * 2**level
            self.bb = self.base_bb * 2**level
        else:
            self.sb = self.base_sb
            self.bb = self.base_bb

    def return_extra_chips(self):
        # An uncalled bet returns to whoever posted it even if they later fold —
        # a blind is treated like any other bet. Filtering to unfolded players
        # stranded the excess of, say, a big blind that short all-ins couldn't
        # match, leaving a side-pot layer nobody was eligible to win.
        active = sorted(self.players, key=lambda p: p.current_bet)
        if len(active) < 2:
            return
        if active[-1].current_bet > active[-2].current_bet:
            extra = active[-1].current_bet - active[-2].current_bet
            active[-1].chips += extra
            active[-1].current_bet -= extra
            # total_bet drives build_side_pots — leaving it overstated makes the
            # side pots sum to more than the pot actually holds, creating chips.
            active[-1].total_bet -= extra
            self.current_bet -= extra
            self.pot -= extra

    def betting_round_over(self):
        # If at most one player can still act and they have nothing to call,
        # no further betting is possible — don't hand them an action they can
        # only fold into, which would abandon a side pot with no eligible winner.
        contenders = [p for p in self.players if not p.folded and not p.all_in]
        if len(contenders) <= 1 and all(p.current_bet >= self.current_bet for p in contenders):
            self.round_start_pot = self.pot
            return True
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
            # Each layer is only what's owed *above* the previous level. Using a
            # running total instead drops chips, because lower levels have more
            # contributors than higher ones.
            amount = (bet - last_pot) * len(contributers)
            if amount:
                side_pots.append((amount, players))
            last_pot = bet

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
        if player is None:
            raise ValueError("Invalid player")
        actual = min(amount, player.chips)
        player.chips -= actual
        player.current_bet += actual
        player.total_bet += actual
        self.pot += actual
        if player.chips == 0: player.all_in = True

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
            # if at most one player can still act, no more betting is possible —
            # run the remaining streets out to showdown
            can_act = [p for p in active if not p.all_in]
            if len(can_act) <= 1:
                # no more betting possible — signal the async layer to run the
                # board out street-by-street (with delays). Engine stays synchronous.
                self.all_in_runout = True
            else:
                self.advance_phase()
        else:
            self.next_active_player()

    def player_call(self, player_id):
        player = None
        for p in self.players:
            if p.id == player_id:
                player = p
        if player is None:
            raise ValueError("Invalid player")
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

    def rebuy_error(self, player_id):
        """Why this player can't rebuy right now, or None if they can.

        Single source of truth: player_rebuy raises on it, the serializer
        renders the button from it, so the two can never disagree.
        """
        player = self.player_data.get(player_id)
        if player is None:
            return "Invalid player"
        if not self.rebuy:
            return "Rebuys are off for this table"
        if player.chips > 0:
            return "You still have chips"
        # A seated player is in the current hand — pulling them out mid-hand
        # would strand their chips in the pot. A spectator isn't, so they may
        # rebuy at any time and join the next deal.
        if player in self.players and self.phase not in (GamePhase.WAITING, GamePhase.SHOWDOWN):
            return "Can't rebuy during a hand"
        # Seats they don't already occupy — a busted player still sitting at the
        # table isn't taking a new one.
        if len([p for p in self.players + self.waiting if p is not player]) >= 9:
            return "Table is full"
        return None

    def player_rebuy(self, player_id):
        err = self.rebuy_error(player_id)
        if err:
            raise ValueError(err)
        player = self.player_data[player_id]
        player.buy_ins += 1
        player.chips = self.starting_stack
        self.place_player(player, self.players if self.phase == GamePhase.WAITING else self.waiting)

    def player_join(self, player_id):
        if not (len(self.players) + len(self.waiting) < 9):
            return
        if player_id in self.player_data:
            player = self.player_data[player_id]
            player.leaving = False   
            if player.chips == 0:
                self.place_player(player, self.spectators)  
                return     
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
        for p in self.spectators:
            if p.id == player_id:
                self.spectators.remove(p)
                return
        # Only fold (and advance the action) when a hand is actually live.
        # Between hands there is nothing to fold out of, and calling
        # after_action there resolves a hand that never started.
        in_hand = self.phase not in (GamePhase.WAITING, GamePhase.SHOWDOWN)
        for p in self.players:
            if p.id != player_id:
                continue
            p.leaving = True
            if in_hand and not p.folded:
                p.folded = True
                if self.players[self.action_turn] == p:
                    self.after_action()
            return

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

    def place_player(self, player, target):
        for lst in (self.players, self.waiting, self.spectators):
            if player in lst:
                lst.remove(player)
        if target is not None:
            target.append(player)
            


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

        



