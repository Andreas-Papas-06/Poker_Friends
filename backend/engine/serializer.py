def serialize_game(game, player_id=None) -> dict:
    opts = game.player_options(player_id)
    return {
        "phase": game.phase.name,
        "pot": game.pot,
        "current_bet": game.current_bet,
        "board": [serialize_card(c) for c in game.board],
        "action_turn": game.players[game.action_turn].id if game.players else None,
        "dealer": game.players[game.dealer].id if game.players else None,
        "options": opts["actions"],
        "min_raise": opts["min_raise"],
        "max_raise": opts["max_raise"],
        "waiting": [p.id for p in game.waiting],
        "showdown": game.last_result if game.phase.name == "SHOWDOWN" else None,
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
