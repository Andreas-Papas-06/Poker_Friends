from backend.api.api import sio
from backend.api import lobby
from backend.engine.serializer import serialize_game

# Broadcast state function
async def broadcast_state(game_id: str, game):
    entry = lobby.get_game(game_id)
    for sid, player_id in entry["players"].items():
        state = serialize_game(game, player_id=player_id)
        await sio.emit("game_state", state, to=sid)

@sio.event
async def join_game(sid, data):
    game_id = data['game_id']
    player_id = data['player_id']
    entry = lobby.get_game(game_id)
    if not entry:
        await sio.emit("error", {"message": "Game not found"}, to=sid)
        return
    entry["players"][sid] = player_id
    try:
        entry["game"].player_join(player_id)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, to=sid)
        return
    await sio.enter_room(sid, game_id)
    await broadcast_state(game_id, entry["game"])

@sio.event
async def leave_game(sid, data):
    game_id = data['game_id']
    entry = lobby.get_game(game_id)
    if not entry or sid not in entry["players"]:
        await sio.emit("error", {"message": "Not in this game"}, to=sid)
        return
    player_id = entry["players"].pop(sid)   # derive from sid AND remove the mapping
    try:
        entry["game"].player_leave(player_id)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, to=sid)
        return
    await sio.leave_room(sid, game_id)      # leave, not enter
    await broadcast_state(game_id, entry["game"])

@sio.event
async def start_game(sid, data):
    game_id = data['game_id']
    entry = lobby.get_game(game_id)
    if not entry or sid not in entry["players"]:
        await sio.emit("error", {"message": "Not in this game"}, to=sid)
        return
    try:
        entry['game'].start_round()
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, to=sid)
        return
    await broadcast_state(game_id, entry["game"])

@sio.event
async def player_action(sid, data):
    game_id = data['game_id']
    action = data['action']
    amount = data.get("amount", 0)
    entry = lobby.get_game(game_id)
    if not entry or sid not in entry["players"]:
        await sio.emit("error", {"message": "Not in this game"}, to=sid)
        return
    game = entry["game"]
    player_id = entry["players"][sid]

    try:
        match action:
            case 'fold':
                game.player_fold(player_id)
            case 'check':
                game.player_check(player_id)
            case 'call':
                game.player_call(player_id)
            case 'bet' | 'raise':
                game.player_bet(player_id, amount)
    except ValueError as e:
        await sio.emit("error", {"message": str(e)}, to=sid)
        return

    await broadcast_state(game_id, entry["game"])

@sio.event
async def disconnect(sid):
    # Find which game this socket was in and remove the player
    for game_id, entry in lobby.games.items():
        if sid in entry["players"]:
            player_id = entry["players"].pop(sid)
            try:
                entry["game"].player_leave(player_id)
            except Exception:
                pass
            await broadcast_state(game_id, entry["game"])
            break