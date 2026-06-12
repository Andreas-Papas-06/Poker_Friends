def serialize_game(game, player_id=None) -> dict:
    return {
        "phase": game.phase.name,
        "pot": game.pot,
        "current_bet": game.current_bet,
        "board": [serialize_card(c) for c in game.board],
        "action_turn":  game.players[game.action_turn].id if game.players else None,
        "players": [serialize_player(p, reveal=(game.phase.name == "SHOWDOWN" or p.id == player_id)) 
                    for p in game.players],
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