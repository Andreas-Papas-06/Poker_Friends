def serialize_game(game, player_id=None) -> dict:
    opts = game.player_options(player_id)
    me = game.player_data.get(player_id)
    known = me is not None
    chips = me.chips if known else 0
    seated = known and me in game.players
    queued = known and me in game.waiting
    # A seated player at 0 chips is all-in while the hand runs, and only
    # becomes a spectator once it's over — their seat already says ALL IN.
    in_hand = game.phase.name not in ("WAITING", "SHOWDOWN")
    spectating = known and not queued and (not seated or (chips == 0 and not in_hand))
    # asks the engine, so the button is exactly as permissive as the server
    can_rebuy = game.rebuy_error(player_id) is None
    return {
        "phase": game.phase.name,
        "pot": game.pot,
        "current_bet": game.current_bet,
        "board": [serialize_card(c) for c in game.board],
        "action_turn": game.players[game.action_turn].id if game.action_turn < len(game.players) else None,
        "dealer": game.players[game.dealer].id if game.dealer < len(game.players) else None,
        "options": opts["actions"],
        "min_raise": opts["min_raise"],
        "max_raise": opts["max_raise"],
        "display": game.display,
        "waiting": [p.id for p in game.waiting],
        "showdown": game.last_result if game.phase.name == "SHOWDOWN" else None,
        "rebuy": game.rebuy,
        "starting_stack": game.starting_stack,
        "spectators": [p.id for p in game.spectators],
        "spectating": spectating,
        "can_rebuy": can_rebuy,
        "players": [
            serialize_player(
                p,
                reveal=(p.id == player_id or (game.phase.name == "SHOWDOWN" and not p.folded)),
            )
            for p in game.players
        ],
    }


def serialize_player(player, reveal=False) -> dict:
    return {
        "id": player.id,
        "chips": player.chips,
        "current_bet": player.current_bet,
        "folded": player.folded,
        "all_in": player.all_in,
        "hand": [serialize_card(c) for c in player.hand] if reveal else None,
    }


def serialize_card(card) -> dict:
    return {"rank": card.rank, "suit": card.suit}
