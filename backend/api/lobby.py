import uuid
from backend.engine.engine import PokerGame

# game_id → { "game": PokerGame, "players": {socket_id: player_id} }
games: dict = {}

def create_game(sb=10, bb=20, starting_stack=1000, rebuy=True, style='C', blind_increase=1) -> str:
    game_id = str(uuid.uuid4())[:8]  # short code users can share
    games[game_id] = {
        "game": PokerGame(players=[], sb=sb, bb=bb, starting_stack=starting_stack, rebuy=rebuy, style=style, blind_increase=blind_increase),
        "players": {}  # socket_sid → player_id
    }
    return game_id

def get_game(game_id: str):
    return games.get(game_id)