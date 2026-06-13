from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from backend.api import lobby

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # dev only — lock this down before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)


@app.post('/games')
async def create_game(sb: int = 10, bb: int = 20, starting_stack: int = 1000):
    game_id = lobby.create_game(sb, bb, starting_stack)
    return {"game_id": game_id}

@app.get("/games/{game_id}")
async def get_game_state(game_id: str):
    entry = lobby.get_game(game_id)
    if not entry:
        return {"error": "Game not found"}
    from backend.engine.serializer import serialize_game
    return serialize_game(entry["game"])
