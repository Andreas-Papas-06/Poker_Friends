"""
Two-client end-to-end test for the poker socket layer.

Run the server first (in another terminal):
    python -m backend.api.main

Then run this:
    python test_client.py
"""
import asyncio
import aiohttp
import socketio

BASE = "http://localhost:8000"


def make_client(name):
    """Create a socket client that logs everything it receives."""
    sio = socketio.AsyncClient()

    @sio.on("game_state")
    def on_state(state):
        turn = state.get("action_turn")
        ids = [p["id"] for p in state["players"]]
        # show this client's own hand (only theirs is populated)
        me = next((p for p in state["players"] if p["id"] == name), None)
        hand = me["hand"] if me else None
        print(f"[{name}] state: phase={state['phase']} pot={state['pot']} "
              f"turn={turn} players={ids} my_hand={hand}")

    @sio.on("error")
    def on_error(err):
        print(f"[{name}] ERROR: {err['message']}")

    return sio


async def main():
    # 1. Create a game over REST
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE}/games") as resp:
            game_id = (await resp.json())["game_id"]
    print(f"Created game: {game_id}\n")

    # 2. Connect two clients
    alice = make_client("alice")
    bob = make_client("bob")
    await alice.connect(BASE)
    await bob.connect(BASE)

    # 3. Both join the table
    await alice.emit("join_game", {"game_id": game_id, "player_id": "alice"})
    await asyncio.sleep(0.3)
    await bob.emit("join_game", {"game_id": game_id, "player_id": "bob"})
    await asyncio.sleep(0.3)

    # 4. Alice starts the hand
    print("\n--- starting hand ---")
    await alice.emit("start_game", {"game_id": game_id})
    await asyncio.sleep(0.5)

    # 5. Try an out-of-turn action to prove the guard fires
    print("\n--- bob tries to act (testing turn validation) ---")
    await bob.emit("player_action", {"game_id": game_id, "action": "fold"})
    await asyncio.sleep(0.3)
    await alice.emit("player_action", {"game_id": game_id, "action": "fold"})
    await asyncio.sleep(0.5)

    # 6. Clean up
    await alice.disconnect()
    await bob.disconnect()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
